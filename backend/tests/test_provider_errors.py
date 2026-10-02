"""
Tests for provider_errors — upstream limits must not read as our defects.

The bug these pin: a Gemini 429 propagated through the error middleware as a
bare HTTP 500 "An unexpected error occurred". On the free tier one chat turn
makes 6-12 model calls against a 20-per-day-per-model cap, so a user reached
that in about two conversations and was told the app was broken.
"""

import sys

sys.path.insert(0, ".")

import pytest

from app.utils.provider_errors import ProviderErrorKind, classify

# The verbatim shape the google-genai SDK raises, trimmed. Kept real rather
# than synthesised so a change in provider wording fails here loudly.
QUOTA_429 = (
    "ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': "
    "'You exceeded your current quota, please check your plan and billing "
    "details. * Quota exceeded for metric: "
    "generativelanguage.googleapis.com/generate_content_free_tier_requests, "
    "limit: 20, model: gemini-3.7-flash. Please retry in 25.247316003s.', "
    "'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': "
    "'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '25s'}]}}"
)
OVERLOAD_503 = (
    "ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This "
    "model is currently experiencing high demand. Spikes in demand are usually "
    "temporary. Please try again later.', 'status': 'UNAVAILABLE'}}"
)


class TestClassification:
    def test_quota_exhaustion_is_not_an_internal_error(self):
        p = classify(RuntimeError(QUOTA_429))
        assert p.kind is ProviderErrorKind.QUOTA_EXHAUSTED
        assert p.status_code == 503, "503, not 500 — nothing in this app is broken"
        assert p.is_provider_fault

    def test_quota_exhaustion_is_not_reported_as_429_either(self):
        """429 means THIS CLIENT sent too many requests. The user did not —
        the server's own upstream budget is spent, which is a 503."""
        assert classify(RuntimeError(QUOTA_429)).status_code != 429

    def test_provider_overload_is_separated_from_quota(self):
        p = classify(RuntimeError(OVERLOAD_503))
        assert p.kind is ProviderErrorKind.PROVIDER_UNAVAILABLE
        assert p.error_code == "ai_unavailable"

    def test_the_providers_own_retry_delay_is_passed_through(self):
        assert classify(RuntimeError(QUOTA_429)).retry_after_s == 25

    def test_a_real_bug_still_surfaces_as_500(self):
        """Dressing a genuine defect up as 'try again later' is how bugs ship."""
        p = classify(TypeError("NoneType object is not subscriptable"))
        assert p.kind is ProviderErrorKind.UNKNOWN
        assert p.status_code == 500
        assert not p.is_provider_fault

    @pytest.mark.parametrize("text", [QUOTA_429, OVERLOAD_503, "boom"])
    def test_every_message_is_georgian(self, text):
        """These strings are rendered verbatim as chat bubbles in a
        Georgian-only app — an English one lands in the conversation."""
        msg = classify(RuntimeError(text)).message_ka
        assert msg and any("Ⴀ" <= ch <= "ჿ" for ch in msg), msg
        latin_names = msg.replace("AI", "").replace("Google", "")
        assert not any(ch.isascii() and ch.isalpha() for ch in latin_names)

    def test_a_spent_quota_says_whose_limit_and_how_long_to_wait(self):
        """The reader has to learn it is their own free Google key, how long
        Google asked them to wait, and that another key is a way out now."""
        msg = classify(RuntimeError(QUOTA_429)).message_ka
        assert "Google-ის გასაღების უფასო ლიმიტი" in msg
        assert "25 წამში" in msg
        assert "შეცვალეთ გასაღები" in msg


class TestRetry:
    @pytest.mark.asyncio
    async def test_a_spent_quota_is_not_retried(self):
        """A retry a second later is refused too, and counts against the same
        per-minute limit the final answer still needs."""
        from app.integrations.vertex_ai_client import with_retry

        calls = 0

        async def spent():
            nonlocal calls
            calls += 1
            raise RuntimeError(QUOTA_429)

        with pytest.raises(RuntimeError):
            await with_retry(spent, what="test")
        assert calls == 1


class TestMiddlewareIntegration:
    @pytest.mark.asyncio
    async def test_middleware_maps_a_provider_429_to_503(self):
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from app.middleware.error_handler_middleware import ErrorHandlerMiddleware

        async def boom(_request):
            raise RuntimeError(QUOTA_429)

        app = Starlette(routes=[Route("/boom", boom)])
        app.add_middleware(ErrorHandlerMiddleware)

        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get("/boom")

        assert r.status_code == 503
        assert r.json()["error"] == "ai_quota_exhausted"
        assert r.headers.get("Retry-After") == "25"

    @pytest.mark.asyncio
    async def test_middleware_still_500s_a_genuine_bug(self):
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from app.middleware.error_handler_middleware import ErrorHandlerMiddleware

        async def boom(_request):
            raise KeyError("case_file_id")

        app = Starlette(routes=[Route("/boom", boom)])
        app.add_middleware(ErrorHandlerMiddleware)

        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get("/boom")

        assert r.status_code == 500
        assert r.json()["error"] == "internal_server_error"


class TestEmptyAnswer:
    """An empty model answer is reported, never delivered as a blank reply."""

    def test_an_empty_answer_says_so_in_georgian(self):
        from app.utils.provider_errors import EmptyModelAnswerError

        p = classify(EmptyModelAnswerError())
        assert p.kind is ProviderErrorKind.EMPTY_ANSWER
        assert p.error_code == "ai_empty_answer"
        assert p.is_provider_fault
        assert "პასუხი" in p.message_ka


# Real, 2026-10-02, a free key calling a model whose free quota is 0. Google
# lists every bucket the call broke; the day ones decide what the user is told.
DAILY_429 = (
    "ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded "
    "your current quota, please check your plan and billing details. \\n* Quota exceeded for "
    "metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, "
    "model: gemini-2.5-pro\\nPlease retry in 14h54m20.958164783s.', 'status': "
    "'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.QuotaFailure', "
    "'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_input_token_count', "
    "'quotaId': 'GenerateContentInputTokensPerModelPerDay-FreeTier', 'quotaDimensions': {'location': "
    "'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': "
    "'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': "
    "'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': "
    "'global', 'model': 'gemini-2.5-pro'}}, {'quotaMetric': "
    "'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': "
    "'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'quotaDimensions': {'model': "
    "'gemini-2.5-pro', 'location': 'global'}, 'quotaValue': '20'}]}, {'@type': "
    "'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '53660s'}]}}"
)
# The per-minute shape: same body, only a minute bucket broken.
MINUTE_429 = (
    "ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded "
    "your current quota. Please retry in 41.2s.', 'status': 'RESOURCE_EXHAUSTED', 'details': "
    "[{'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': "
    "'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': "
    "'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'location': "
    "'global', 'model': 'gemini-3.7-flash'}, 'quotaValue': '5'}]}, {'@type': "
    "'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '41s'}]}}"
)


class TestDailyVersusPerMinute:
    """Production, 2026-10-01: a spent DAILY bucket was reported as "try
    again in 41 seconds" — the user waited and failed again. And when
    Google's delay is the rest of the day, it read "try in 53660 seconds"."""

    def test_a_spent_daily_limit_says_so_and_offers_the_way_out(self):
        p = classify(RuntimeError(DAILY_429))
        assert p.kind is ProviderErrorKind.QUOTA_EXHAUSTED
        assert p.quota_period == "day"
        assert "დღიური" in p.message_ka
        assert "სხვა მოდელი" in p.message_ka and "შეცვალეთ გასაღები" in p.message_ka
        assert "წამში" not in p.message_ka, "waiting seconds will not help"
        assert p.retry_after_s is None

    def test_a_spent_minute_limit_says_how_many_seconds(self):
        p = classify(RuntimeError(MINUTE_429))
        assert p.quota_period == "minute"
        assert "41 წამში" in p.message_ka
        assert "დღიური" not in p.message_ka

    def test_the_broken_buckets_are_named_for_the_log(self):
        """Production log lines are cut at a few hundred characters, which
        drops exactly this part of Google's body."""
        p = classify(RuntimeError(DAILY_429))
        assert "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in p.quota_ids
        assert p.quota_value == 20

    @pytest.mark.parametrize("text", [DAILY_429, MINUTE_429])
    def test_both_stay_georgian(self, text):
        msg = classify(RuntimeError(text)).message_ka
        latin_names = msg.replace("AI", "").replace("Google", "")
        assert not any(ch.isascii() and ch.isalpha() for ch in latin_names), msg
