"""
Model router — read the effective tier models, and change them at runtime.

GET  /api/v1/models   any authenticated caller — the UI shows what is running
PUT  /api/v1/models   admin only — changing a model changes cost and answer
                      quality for EVERY user, so it is not a personal setting
DELETE /api/v1/models admin only — drop overrides, back to the environment
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.model_config_service import get_model_config_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])

_ADMIN_TIERS = {"ADMIN", "SUPERADMIN"}

# Filtering is two-part, because neither half is sufficient alone.
#
# 1. supportedGenerationMethods CANNOT distinguish a chat model: lyria-3
#    (music) and deep-research both advertise generateContent. What DOES
#    separate them is `createCachedContent` — the general-purpose Gemini chat
#    models carry it, the single-purpose ones do not.
# 2. A few families pass that test but are structurally not text chat
#    (robotics, image generation), so they are excluded by name.
#
# Deliberately NOT an allow-list: that would need a code change every time the
# provider ships a model, which is the exact friction this screen removes. The
# cost of the looser rule is an occasional odd entry in the list, and the PUT
# smoke-tests the choice before committing it anyway.
_REQUIRED_METHOD = "createCachedContent"
_EXCLUDED_MARKERS = (
    "embedding", "-tts", "-image", "imagen", "veo", "-video",
    "aqa", "learnlm", "gemma", "robotics", "nano-banana", "lyria",
)


class ModelSelection(BaseModel):
    strong: str | None = Field(default=None, description="Model for high-stakes generation")
    cheap: str | None = Field(default=None, description="Model for planning, rerank, verification")


def _is_admin(request: Request) -> bool:
    user = getattr(request.state, "user", None) or {}
    return str(user.get("tier", "")).upper() in _ADMIN_TIERS


def _forbidden() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": "forbidden",
            "message": "მოდელის შეცვლა მხოლოდ ადმინისტრატორს შეუძლია.",
        },
    )


async def _available_models() -> list[str]:
    """Text-generation models the configured provider actually offers.

    Asked of the provider rather than hardcoded: a static list goes stale the
    week a new model ships, and the whole point of this screen is trying new
    models without a deploy. A provider outage yields an empty list, and the
    UI still shows the current selection — degraded, not broken.
    """
    from app.integrations.vertex_ai_client import create_genai_client

    try:
        client = create_genai_client()
        names: list[str] = []
        async for m in await client.aio.models.list():
            name = (m.name or "").removeprefix("models/")
            if not name or any(x in name for x in _EXCLUDED_MARKERS):
                continue
            actions = getattr(m, "supported_actions", None) or []
            # Absence of the field is not exclusion — Vertex omits it entirely,
            # and hiding every model on that backend would be worse than
            # showing a few extra on this one.
            if actions and _REQUIRED_METHOD not in actions:
                continue
            names.append(name)
        return sorted(set(names))
    except Exception as e:  # noqa: BLE001
        logger.warning("model_list_failed", error=str(e)[:200])
        return []


async def _smoke_test(model: str) -> tuple[bool, str]:
    """Ask the model to say one word. Returns (usable, reason-if-not).

    Thinking is disabled and the budget is generous: a thinking model with a
    tight budget returns empty text and would look "unusable" when it is
    merely mis-configured — the guardrail bug, repeated as a false negative.
    """
    from app.integrations.vertex_ai_client import get_vertex_ai_client

    try:
        text = await get_vertex_ai_client().generate(
            prompt="Reply with the single word: OK",
            temperature=0.0,
            max_output_tokens=256,
            thinking_budget=0,
            model_name=model,
        )
    except Exception as e:  # noqa: BLE001
        from app.utils.provider_errors import classify

        return False, classify(e).message_ka
    if not text or not text.strip():
        return False, "პასუხი ცარიელია"
    return True, ""


def _payload(current: dict, available: list[str], can_edit: bool) -> dict:
    return {
        "strong": {"model": current["strong"].model, "source": current["strong"].source},
        "cheap": {"model": current["cheap"].model, "source": current["cheap"].source},
        "available": available,
        "can_edit": can_edit,
    }


@router.get("")
async def get_models(request: Request):
    """Current tier selection, plus what else could be chosen."""
    svc = get_model_config_service()
    return _payload(await svc.current(), await _available_models(), _is_admin(request))


@router.put("")
async def set_models(request: Request, body: ModelSelection):
    if not _is_admin(request):
        return _forbidden()
    if not body.strong and not body.cheap:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": "მოდელი მითითებული არ არის."},
        )

    # Validate against what the provider offers, so a typo becomes a 400 here
    # rather than a 404 from the provider on the user's next legal question.
    available = await _available_models()
    if available:
        unknown = [m for m in (body.strong, body.cheap) if m and m not in available]
        if unknown:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "unknown_model",
                    "message": f"უცნობი მოდელი: {', '.join(unknown)}",
                },
            )

    # A bad choice here breaks EVERY user's next question, so prove the model
    # answers before committing it. One ~10-token call turns "the app is down
    # and nobody knows why" into a 400 on the screen that caused it.
    for candidate in filter(None, (body.strong, body.cheap)):
        ok, detail = await _smoke_test(candidate)
        if not ok:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "model_unusable",
                    "message": f"მოდელი {candidate} ვერ გამოიყენება: {detail}",
                },
            )

    svc = get_model_config_service()
    current = await svc.set_models(strong=body.strong, cheap=body.cheap)
    logger.info(
        "model_config_changed",
        by=(getattr(request.state, "user", None) or {}).get("uid"),
        strong=current["strong"].model,
        cheap=current["cheap"].model,
    )
    return _payload(current, available, True)


@router.delete("")
async def reset_models(request: Request):
    if not _is_admin(request):
        return _forbidden()
    svc = get_model_config_service()
    current = await svc.reset()
    return _payload(current, await _available_models(), True)
