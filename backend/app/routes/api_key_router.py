from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config.settings import settings
from app.utils.api_keys import generate_api_key

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

