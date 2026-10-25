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

import anthropic

from app.integrations.claude_client import ClaudeKeyMissingError, ClaudeRefusalError


class ProviderErrorKind(str, Enum):
    """What went wrong upstream, from the caller's point of view."""

    QUOTA_EXHAUSTED = "quota_exhausted"      # billing/limit — waiting helps
    PROVIDER_UNAVAILABLE = "provider_unavailable"  # overload — retrying helps
    INVALID_KEY = "invalid_key"              # the caller's own key — only they can fix it
    CONTEXT_TOO_LONG = "context_too_long"    # prompt over the model's window — shorten it
    MODEL_REFUSED = "model_refused"          # the model declined — rephrase or switch model
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
# Under bring-your-own-key a spent bucket is the free limit of the user's own
# Google key, per MODEL — so besides waiting, another model or another key is
# a way out right now. Say all three, and how long the wait is when Google
# told us.
_QUOTA_KA = (
    "თქვენი Google-ის გასაღების უფასო ლიმიტი ამოიწურა. {wait} აირჩიეთ სხვა "
    "მოდელი ან შეცვალეთ გასაღები პარამეტრებში."
)
_QUOTA_WAIT_KA = "სცადეთ {seconds} წამში,"
_QUOTA_WAIT_UNKNOWN_KA = "სცადეთ მოგვიანებით,"


def _wait_phrase(retry_after_s: int | None) -> str:
    return (
        _QUOTA_WAIT_KA.format(seconds=retry_after_s)
        if retry_after_s else _QUOTA_WAIT_UNKNOWN_KA
    )


def _quota_message(retry_after_s: int | None) -> str:
    return _QUOTA_KA.format(wait=_wait_phrase(retry_after_s))
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

# Claude is reached with the caller's own ANTHROPIC key, so its messages name
# that key — telling a Claude user to fix their Google key sends them to the
# wrong settings field.
_ANTHROPIC_KEY_MISSING_KA = (
    "Claude-ის მოდელისთვის საჭიროა Anthropic-ის გასაღები. დაამატეთ იგი "
    "პარამეტრებში ან აირჩიეთ Gemini-ს მოდელი."
)
_ANTHROPIC_INVALID_KEY_KA = (
    "თქვენი Anthropic-ის გასაღები არ მუშაობს. გთხოვთ, შეამოწმოთ ან დაამატოთ "
    "ახალი გასაღები პარამეტრებში."
)
_ANTHROPIC_QUOTA_KA = (
    "თქვენი Anthropic-ის გასაღების ლიმიტი ამოიწურა. {wait} აირჩიეთ სხვა "
    "მოდელი ან შეცვალეთ გასაღები პარამეტრებში."
)
_CONTEXT_TOO_LONG_KA = (
    "საუბარი მოდელისთვის ზედმეტად გრძელი გახდა. დაიწყეთ ახალი საუბარი ან "
    "შეამოკლეთ შეკითხვა."
)
_REFUSED_KA = (
    "მოდელმა ამ შეკითხვაზე პასუხი არ გასცა. ჩამოაყალიბეთ იგი სხვაგვარად ან "
    "აირჩიეთ სხვა მოდელი."
)
_ANTHROPIC_BILLING_MARKER = "credit balance"
_ANTHROPIC_TOO_LONG_MARKER = "prompt is too long"

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


def _header_retry_after(exc: anthropic.APIStatusError) -> int | None:
    try:
        return max(1, int(float(exc.response.headers.get("retry-after", ""))))
    except ValueError:
        return None


def _classify_claude(exc: BaseException) -> ProviderError | None:
    """Typed mapping for Claude failures; None when exc is not from Claude.

    Typed rather than string-matched: the Anthropic SDK has one stable
    exception per status, and its messages would trip the Gemini markers
    below (an overload message mentions neither 503 nor UNAVAILABLE).
    """
    if isinstance(exc, ClaudeKeyMissingError):
        return ProviderError(
            kind=ProviderErrorKind.INVALID_KEY,
            status_code=401,
            error_code="anthropic_key_required",
            message_ka=_ANTHROPIC_KEY_MISSING_KA,
        )
    if isinstance(exc, ClaudeRefusalError):
        return ProviderError(
            kind=ProviderErrorKind.MODEL_REFUSED,
            status_code=422,
            error_code="ai_refused",
            message_ka=_REFUSED_KA,
        )
    if isinstance(exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return ProviderError(
            kind=ProviderErrorKind.INVALID_KEY,
            status_code=401,
            error_code="anthropic_key_invalid",
            message_ka=_ANTHROPIC_INVALID_KEY_KA,
        )
    if isinstance(exc, anthropic.RateLimitError):
        retry_after_s = _header_retry_after(exc)
        return ProviderError(
            kind=ProviderErrorKind.QUOTA_EXHAUSTED,
            status_code=503,
            error_code="ai_quota_exhausted",
            message_ka=_ANTHROPIC_QUOTA_KA.format(wait=_wait_phrase(retry_after_s)),
            retry_after_s=retry_after_s,
        )
    if isinstance(exc, anthropic.RequestTooLargeError) or (
        isinstance(exc, anthropic.BadRequestError)
        and _ANTHROPIC_TOO_LONG_MARKER in str(exc)
    ):
        return ProviderError(
            kind=ProviderErrorKind.CONTEXT_TOO_LONG,
            status_code=400,
            error_code="ai_context_too_long",
            message_ka=_CONTEXT_TOO_LONG_KA,
        )
    if isinstance(exc, anthropic.BadRequestError) and _ANTHROPIC_BILLING_MARKER in str(exc):
        return ProviderError(
            kind=ProviderErrorKind.QUOTA_EXHAUSTED,
            status_code=503,
            error_code="ai_quota_exhausted",
            message_ka=_ANTHROPIC_QUOTA_KA.format(wait=_QUOTA_WAIT_UNKNOWN_KA),
        )
    # Overload (529), other 5xx, timeouts and dropped connections.
    if isinstance(exc, anthropic.APIConnectionError):
        return ProviderError(
            kind=ProviderErrorKind.PROVIDER_UNAVAILABLE,
            status_code=503,
            error_code="ai_unavailable",
            message_ka=_UNAVAILABLE_KA,
        )
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
        return ProviderError(
            kind=ProviderErrorKind.PROVIDER_UNAVAILABLE,
            status_code=503,
            error_code="ai_unavailable",
            message_ka=_UNAVAILABLE_KA,
            retry_after_s=_header_retry_after(exc),
        )
    if isinstance(exc, anthropic.AnthropicError):
        return ProviderError(
            kind=ProviderErrorKind.UNKNOWN,
            status_code=500,
            error_code="internal_server_error",
            message_ka=_UNKNOWN_KA,
        )
    return None


def classify(exc: BaseException) -> ProviderError:
    """Map an exception onto a user-facing provider error.

    Returns kind=UNKNOWN for anything that is not recognisably the provider's
    fault — those must keep surfacing as 500s, because turning a genuine bug
    into a soothing "try again later" is how defects get shipped.
    """
    claude_error = _classify_claude(exc)
    if claude_error is not None:
        return claude_error

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
        retry_after_s = _retry_after(text)
        return ProviderError(
            kind=ProviderErrorKind.QUOTA_EXHAUSTED,
            # 503, not 429: 429 means THIS CLIENT sent too many requests, and
            # the user did not — the server's own upstream budget is spent.
            status_code=503,
            error_code="ai_quota_exhausted",
            message_ka=_quota_message(retry_after_s),
            retry_after_s=retry_after_s,
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
