"""
Request-scoped caller context — the BYOK Gemini key for the current request.

WHY A CONTEXTVAR AND NOT A PARAMETER:
The key has to reach ``create_genai_client`` at the bottom of the stack, and
the path there runs Route -> Service -> Client through 11 services that each
hold a ``VertexAIClient`` obtained from a process-lifetime singleton. Threading
a credential through every one of those signatures would be a very large diff
whose only job is transport, and any call site missed would silently fall back
to the server's own key -- i.e. bill the operator for a user's request and look
like it worked. A ContextVar is set once per request and read at exactly one
choke point, so "missed a call site" is not a reachable state.

ContextVars propagate into tasks spawned from the request (``asyncio.gather``,
``to_thread``) because both copy the current context at spawn time, which is
what the RAG pipeline's concurrent fan-out needs. They do NOT propagate back
out, which is why the value is set on the way in and never mutated below.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass

# The Google AI Studio key supplied by the caller for THIS request.
# None means "no caller key" — the client factory then falls back to the
# server's own credential, which is how local development and the eval
# harness keep working unchanged.
_byok_api_key: ContextVar[str | None] = ContextVar("byok_api_key", default=None)


def set_byok_key(key: str | None) -> Token[str | None]:
    """Bind a caller-supplied Gemini key to the current request context."""
    return _byok_api_key.set(key)


def get_byok_key() -> str | None:
    """The caller's Gemini key for this request, or None if they sent none."""
    return _byok_api_key.get()


def reset_byok_key(token: Token[str | None]) -> None:
    """Restore the previous value — always paired with set_byok_key in a finally."""
    _byok_api_key.reset(token)


# ── Per-caller model choice ──────────────────────────────────
# Which model serves a tier is a PERSONAL setting under bring-your-own-key,
# not a deployment-wide one. Each caller pays with their own key, against
# their own quota, and their key exposes its own list of models — we measured
# one free key where the 2.5 family 404s entirely. A single global setting
# would therefore let one user who hit a rate limit switch everybody onto a
# model that some of them cannot even call.
#
# Carried per request for the same reason as the API key: the choice belongs
# to whoever is paying for the call.


@dataclass(frozen=True)
class ModelChoice:
    """A caller's chosen model per tier. None means 'use the server default'."""

    strong: str | None = None
    cheap: str | None = None

    def for_tier(self, tier: str) -> str | None:
        return self.strong if tier == "strong" else self.cheap

    @property
    def is_empty(self) -> bool:
        return not self.strong and not self.cheap


_model_choice: ContextVar[ModelChoice] = ContextVar(
    "model_choice", default=ModelChoice()
)


def set_model_choice(choice: ModelChoice) -> Token[ModelChoice]:
    """Bind a caller's model selection to the current request context."""
    return _model_choice.set(choice)


def get_model_choice() -> ModelChoice:
    """The caller's model selection, or an empty one if they sent none."""
    return _model_choice.get()


def reset_model_choice(token: Token[ModelChoice]) -> None:
    """Restore the previous value — always paired with set_model_choice."""
    _model_choice.reset(token)
