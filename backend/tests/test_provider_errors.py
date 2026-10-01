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
