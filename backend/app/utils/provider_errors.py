"""
Classify upstream model-provider failures into something a user can act on.

WHY: quota exhaustion and provider overload are EXPECTED operating conditions,
not internal errors. Left unclassified they reach the caller as a bare HTTP 500
("An unexpected error occurred") — which tells the user nothing, tells the
operator nothing, and looks like a defect in this app rather than a limit that
resets. On the free tier one chat turn makes 6-12 model calls against a
20-per-day-per-model cap, so this is reachable in about two conversations.

The classification is string-based on purpose: the google-genai SDK raises
several exception types across the Vertex and Developer-API backends, and
pinning this to its private error hierarchy would break on an SDK bump for no
gain. The same reasoning already applies in vertex_ai_client._is_transient.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ProviderErrorKind(str, Enum):
    """What went wrong upstream, from the caller's point of view."""

    QUOTA_EXHAUSTED = "quota_exhausted"      # billing/limit — waiting helps
    PROVIDER_UNAVAILABLE = "provider_unavailable"  # overload — retrying helps
    INVALID_KEY = "invalid_key"              # the caller's own key — only they can fix it
    UNKNOWN = "unknown"                      # a real bug — surface as 500


@dataclass(frozen=True)
class ProviderError:
    kind: ProviderErrorKind
    status_code: int
    error_code: str
    message_ka: str
    retry_after_s: int | None = None

    @property
    def is_provider_fault(self) -> bool:
        return self.kind is not ProviderErrorKind.UNKNOWN


# User-facing copy. Georgian, because the app is Georgian — an English string
# here lands verbatim in the conversation as a chat bubble.
_QUOTA_KA = (
    "AI სერვისის დღიური ლიმიტი ამოიწურა. გთხოვთ, სცადოთ მოგვიანებით."
)
_UNAVAILABLE_KA = (
    "AI სერვისი დროებით გადატვირთულია. გთხოვთ, სცადოთ რამდენიმე წამში."
)
_UNKNOWN_KA = "დაფიქსირდა შეცდომა. გთხოვთ, სცადოთ თავიდან."
# Under bring-your-own-key the credential belongs to the USER, so a rejected
# key is not an outage and waiting will not fix it — the message has to say
# what they must do. Left unclassified this arrives as "an error occurred",
# and the user has no way to learn that their key expired.
_INVALID_KEY_KA = (
    "თქვენი Google-ის გასაღები არ მუშაობს. გთხოვთ, შეამოწმოთ ან დაამატოთ ახალი "
    "გასაღები პარამეტრებში."
)

# Quota and overload BOTH surface as 429 on the Gemini Developer API, so the
# status code alone cannot separate them — "exceeded your current quota"
# distinguishes a spent daily bucket from ordinary rate limiting.
_QUOTA_MARKERS = (
    "RESOURCE_EXHAUSTED",
    "exceeded your current quota",
    "quota exceeded",
    "billing",
)
_UNAVAILABLE_MARKERS = (
    "503",
    "UNAVAILABLE",
    "high demand",
    "overloaded",
    "500",
    "INTERNAL",
    "DEADLINE_EXCEEDED",
)

_INVALID_KEY_MARKERS = (
    "API_KEY_INVALID",
    "API key not valid",
    "API key expired",
    "UNAUTHENTICATED",
    "PERMISSION_DENIED",
    "SERVICE_DISABLED",
    "has not been used in project",
)

_RETRY_AFTER_RE = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)")
_RETRY_IN_RE = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


def _retry_after(text: str) -> int | None:
    """The provider tells us how long to wait; pass it on rather than guess."""
    for rx in (_RETRY_AFTER_RE, _RETRY_IN_RE):
        m = rx.search(text)
        if m:
            try:
                return max(1, int(float(m.group(1))))
            except ValueError:
                continue
    return None


def classify(exc: BaseException) -> ProviderError:
    """Map an exception onto a user-facing provider error.

    Returns kind=UNKNOWN for anything that is not recognisably the provider's
    fault — those must keep surfacing as 500s, because turning a genuine bug
    into a soothing "try again later" is how defects get shipped.
    """
    text = f"{type(exc).__name__}: {exc}"

    # Checked before quota: a disabled-API error carries PERMISSION_DENIED and
    # some quota-ish wording, and telling the user to "try later" when their
    # key will never work is the worse of the two mistakes.
    if any(m in text for m in _INVALID_KEY_MARKERS):
        return ProviderError(
            kind=ProviderErrorKind.INVALID_KEY,
            # 401, not 503: the request cannot succeed as sent, and the client
            # keys its "re-prompt for a key" flow off this status.
            status_code=401,
            error_code="byok_key_invalid",
            message_ka=_INVALID_KEY_KA,
        )

    if any(m in text for m in _QUOTA_MARKERS):
        return ProviderError(
            kind=ProviderErrorKind.QUOTA_EXHAUSTED,
            # 503, not 429: 429 means THIS CLIENT sent too many requests, and
            # the user did not — the server's own upstream budget is spent.
            status_code=503,
            error_code="ai_quota_exhausted",
            message_ka=_QUOTA_KA,
            retry_after_s=_retry_after(text),
        )

    if any(m in text for m in _UNAVAILABLE_MARKERS):
        return ProviderError(
            kind=ProviderErrorKind.PROVIDER_UNAVAILABLE,
            status_code=503,
            error_code="ai_unavailable",
            message_ka=_UNAVAILABLE_KA,
            retry_after_s=_retry_after(text),
        )

    return ProviderError(
        kind=ProviderErrorKind.UNKNOWN,
        status_code=500,
        error_code="internal_server_error",
        message_ka=_UNKNOWN_KA,
    )
