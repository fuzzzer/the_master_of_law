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
    EMPTY_ANSWER = "empty_answer"            # the model wrote nothing — retrying or another model helps
    MODEL_UNAVAILABLE = "model_unavailable"  # this key can never call this model — only another model helps
    UNKNOWN = "unknown"                      # a real bug — surface as 500


class EmptyModelAnswerError(Exception):
    """The model finished its turn without writing any answer text.

    Raised rather than returned as "": a blank reply delivered as a finished
    answer is a failure that pretends to be success.
    """


@dataclass(frozen=True)
class ProviderError:
    kind: ProviderErrorKind
    status_code: int
    error_code: str
    message_ka: str
    retry_after_s: int | None = None
    # Which of Google's buckets broke — "day" or "minute" — and their ids and
    # limit, so a log line names them even when the raw body is cut short.
    quota_period: str | None = None
    quota_ids: tuple[str, ...] = ()
    quota_value: int | None = None

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
# A spent DAILY bucket does not come back in seconds — Google's delay is the
# rest of the day — so the only useful advice is the way out right now.
_QUOTA_DAILY_KA = (
    "ამ მოდელის დღიური უფასო ლიმიტი თქვენს Google-ის გასაღებზე ამოიწურა. "
    "აირჩიეთ სხვა მოდელი ან შეცვალეთ გასაღები პარამეტრებში."
)


def _quota_message(retry_after_s: int | None) -> str:
    wait = (
        _QUOTA_WAIT_KA.format(seconds=retry_after_s)
        if retry_after_s else _QUOTA_WAIT_UNKNOWN_KA
    )
    return _QUOTA_KA.format(wait=wait)
_UNAVAILABLE_KA = (
    "AI სერვისი დროებით გადატვირთულია. გთხოვთ, სცადოთ რამდენიმე წამში."
)
_UNKNOWN_KA = "დაფიქსირდა შეცდომა. გთხოვთ, სცადოთ თავიდან."
# A free limit of ZERO (Pro models on a free key) or a model retired for new
# users: no wait and no retry will make it work, so say so.
_MODEL_UNAVAILABLE_KA = (
    "ეს მოდელი თქვენი Google-ის გასაღებით მიუწვდომელია. აირჩიეთ სხვა მოდელი "
    "პარამეტრებში."
)
_EMPTY_ANSWER_KA = (
    "მოდელმა პასუხი ვერ დაწერა. გთხოვთ, სცადოთ თავიდან ან აირჩიოთ სხვა მოდელი."
)
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

_LIMIT_RE = re.compile(r"limit:\s*(\d+)")
_RETIRED_MODEL_MARKERS = ("no longer available", "is not found for API version")
_QUOTA_ID_RE = re.compile(r"quotaId['\"]?\s*[:=]\s*['\"]([\w.-]+)")
_QUOTA_VALUE_RE = re.compile(r"quotaValue['\"]?\s*[:=]\s*['\"]?(\d+)")
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


def _quota_period(quota_ids: tuple[str, ...]) -> str | None:
    """A broken day bucket outranks a minute one: waiting a minute cannot
    help while the day's allowance is spent."""
    if any("PerDay" in q for q in quota_ids):
        return "day"
    if any("PerMinute" in q for q in quota_ids):
        return "minute"
    return None


def classify(exc: BaseException) -> ProviderError:
    """Map an exception onto a user-facing provider error.

    Returns kind=UNKNOWN for anything that is not recognisably the provider's
    fault — those must keep surfacing as 500s, because turning a genuine bug
    into a soothing "try again later" is how defects get shipped.
    """
    if isinstance(exc, EmptyModelAnswerError):
        return ProviderError(
            kind=ProviderErrorKind.EMPTY_ANSWER,
            status_code=502,
            error_code="ai_empty_answer",
            message_ka=_EMPTY_ANSWER_KA,
        )

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

    limits = _LIMIT_RE.findall(text)
    zero_free_limit = bool(limits) and all(v == "0" for v in limits)
    if zero_free_limit or ("NOT_FOUND" in text and any(m in text for m in _RETIRED_MODEL_MARKERS)):
        return ProviderError(
            kind=ProviderErrorKind.MODEL_UNAVAILABLE,
            status_code=400,
            error_code="ai_model_unavailable",
            message_ka=_MODEL_UNAVAILABLE_KA,
        )

    if any(m in text for m in _QUOTA_MARKERS):
        quota_ids = tuple(dict.fromkeys(_QUOTA_ID_RE.findall(text)))
        period = _quota_period(quota_ids)
        values = [int(v) for v in _QUOTA_VALUE_RE.findall(text)]
        retry_after_s = None if period == "day" else _retry_after(text)
        return ProviderError(
            kind=ProviderErrorKind.QUOTA_EXHAUSTED,
            # 503, not 429: 429 means THIS CLIENT sent too many requests, and
            # the user did not — the server's own upstream budget is spent.
            status_code=503,
            error_code="ai_quota_exhausted",
            message_ka=_QUOTA_DAILY_KA if period == "day" else _quota_message(retry_after_s),
            retry_after_s=retry_after_s,
            quota_period=period,
            quota_ids=quota_ids,
            quota_value=min(values) if values else None,
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
