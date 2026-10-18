from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config.request_context import get_byok_key
from app.config.settings import settings
from app.utils.api_keys import generate_api_key
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/api-keys",
    tags=["API Keys (Temporary)"],
)

class ApiKeyResponse(BaseModel):
    api_key: str

def verify_admin_key(x_admin_key: str = Header(..., description="Admin API Key")):
    if settings.app_env != "development" or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return x_admin_key

@router.get("/check")
async def check_admin_key(x_admin_key: str = Header(..., description="Admin API Key")):
    """Check if the provided admin key is valid."""
    if settings.app_env != "development" or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return {"status": "ok"}

@router.post("", response_model=ApiKeyResponse, dependencies=[Depends(verify_admin_key)])
async def create_api_key():
    """Generate a new temporary user API key."""
    new_key = generate_api_key()
    return ApiKeyResponse(api_key=new_key)



class KeyValidationResponse(BaseModel):
    valid: bool
    models_available: int


@router.get("/validate", response_model=KeyValidationResponse)
async def validate_caller_key():
    """Check that the caller's Google key actually works, before they rely on it.

    WHY A LIVE CALL AND NOT JUST A FORMAT CHECK: a well-formed key can still
    be revoked, restricted to the wrong API, or belong to a project with the
    Generative Language API disabled. Every one of those looks identical to a
    good key until the first real request fails — by which point the user has
    typed a legal question and is watching a spinner. Listing models costs no
    tokens and no quota, so the check is free to run at paste time.
    """
    key = get_byok_key()
    if not key:
        return JSONResponse(
            status_code=401,
            content={
                "error": "byok_key_required",
                "message": "გასაღები არ არის მითითებული.",
                "message_en": "No API key supplied.",
            },
        )

    from app.integrations.vertex_ai_client import create_genai_client

    try:
        client = create_genai_client()
        count = 0
        async for _ in await client.aio.models.list():
            count += 1
    except Exception as e:  # noqa: BLE001
        from app.utils.provider_errors import classify

        err = classify(e)
        # An unrecognised failure here is far more likely a bad key than a bug
        # in this app: the only thing that varies between callers is the key.
        if not err.is_provider_fault:
            logger.info("byok_key_rejected", error=str(e)[:200])
            return JSONResponse(
                status_code=401,
                content={
                    "error": "byok_key_invalid",
                    "message": "გასაღები არ მუშაობს. შეამოწმეთ, რომ სწორად დააკოპირეთ "
                               "და რომ Generative Language API ჩართულია.",
                    "message_en": "The key was rejected by Google. Check it was copied "
                                  "correctly and that the Generative Language API is enabled.",
                },
            )
        return JSONResponse(
            status_code=err.status_code,
            content={"error": err.error_code, "message": err.message_ka},
        )

    return KeyValidationResponse(valid=True, models_available=count)
