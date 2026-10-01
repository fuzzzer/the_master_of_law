"""
Model router — read the effective tier models, and change them at runtime.

GET    /api/v1/models          what is serving THIS caller, plus what their
                               key could be switched to
PUT    /api/v1/models          any caller — validate and smoke-test a model,
                               then hand it back for the client to store and
                               send on later requests. Personal: it changes
                               nothing for anybody else.
DELETE /api/v1/models          any caller — clear their personal choice

PUT    /api/v1/models/default  admin only — the deployment-wide default, for
                               callers who have expressed no preference
DELETE /api/v1/models/default  admin only — drop it, back to the environment

WHY PERSONAL RATHER THAN GLOBAL: under bring-your-own-key each caller pays
with their own key, against their own quota, and their key exposes its own
model list — a measured free key 404s the whole 2.5 family. The reason a user
changes model is usually that they personally ran out of one, and making that
switch global would drag every other user onto it, including the ones whose
key cannot call it. The server therefore stores nothing per user: the choice
travels on the request, exactly like the key that pays for it.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.model_config_service import TierModel, get_model_config_service
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


def _payload(current: dict, available: list[str], can_edit: bool = True) -> dict:
    return {
        # can_edit stays true for everyone: choosing your own model is a
        # personal setting now, so there is nobody to withhold it from.
        "strong": {"model": current["strong"].model, "source": current["strong"].source},
        "cheap": {"model": current["cheap"].model, "source": current["cheap"].source},
        "available": available,
        "can_edit": can_edit,
    }


async def _validate_choice(body: "ModelSelection") -> JSONResponse | None:
    """Reject a selection the caller's own key cannot actually run.

    Both checks use the CALLER's credential — the available list and the smoke
    test are asked of their key, not the server's — so "usable" means usable
    for them. Returns None when the selection is good.
    """
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

    # Prove the model answers before the client commits to it. One ~10-token
    # call turns "every question fails and I do not know why" into a message
    # on the screen that caused it.
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
    return None


@router.get("")
async def get_models(request: Request):
    """What is serving THIS caller, plus what their own key could be switched to.

    can_edit is true for everyone: the selection is personal now, so there is
    nobody to withhold it from. It was _is_admin here while the setting was
    global, which in a deployment with no accounts made the picker read-only
    for every single user — including the one who had just run out of quota
    and needed it most.
    """
    svc = get_model_config_service()
    return _payload(await svc.current(), await _available_models(), can_edit=True)


@router.put("")
async def choose_models(request: Request, body: ModelSelection):
    """Validate a personal model choice and hand it back to the client to keep.

    Deliberately writes nothing on the server. The choice is returned so the
    client can store it and send it on subsequent requests, which keeps it
    scoped to one user without the backend having to hold per-user state for
    a deployment that has no accounts.
    """
    if not body.strong and not body.cheap:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": "მოდელი მითითებული არ არის."},
        )

    rejection = await _validate_choice(body)
    if rejection is not None:
        return rejection

    svc = get_model_config_service()
    current = dict(await svc.current())
    # Overlay the accepted choice so the response describes the world the
    # client is about to create by storing it — echoing the pre-change value
    # reads as "it did not work".
    for tier, chosen in (("strong", body.strong), ("cheap", body.cheap)):
        if chosen:
            current[tier] = TierModel(tier=tier, model=chosen, source="personal")

    logger.info(
        "model_choice_accepted",
        uid=(getattr(request.state, "user", None) or {}).get("uid"),
        strong=body.strong,
        cheap=body.cheap,
    )
    return _payload(current, await _available_models())


@router.delete("")
async def clear_choice(request: Request):
    """Fall back to the deployment default. The client drops what it stored."""
    svc = get_model_config_service()
    # Resolved with the caller's choice deliberately ignored, so the response
    # shows what they will actually get once the client stops sending it.
    from app.config.request_context import ModelChoice, reset_model_choice, set_model_choice

    token = set_model_choice(ModelChoice())
    try:
        current = await svc.current()
        available = await _available_models()
    finally:
        reset_model_choice(token)
    return _payload(current, available)


@router.put("/default")
async def set_default_models(request: Request, body: ModelSelection):
    """The deployment-wide default, for callers with no preference of their own."""
    if not _is_admin(request):
        return _forbidden()
    if not body.strong and not body.cheap:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": "მოდელი მითითებული არ არის."},
        )

    rejection = await _validate_choice(body)
    if rejection is not None:
        return rejection

    svc = get_model_config_service()
    current = await svc.set_models(strong=body.strong, cheap=body.cheap)
    logger.info(
        "model_default_changed",
        by=(getattr(request.state, "user", None) or {}).get("uid"),
        strong=current["strong"].model,
        cheap=current["cheap"].model,
    )
    return _payload(current, await _available_models())


@router.delete("/default")
async def reset_default_models(request: Request):
    if not _is_admin(request):
        return _forbidden()
    svc = get_model_config_service()
    current = await svc.reset()
    return _payload(current, await _available_models())
