"""
Tests for bring-your-own-key and the no-login access mode.

The property that matters most here is ISOLATION: whatever else breaks, one
caller's Google key must never be used to serve another caller's request. That
failure is silent — answers still come back, correct and on time — and the only
symptom is somebody else's quota draining. Several tests below exist purely to
keep that from regressing.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.config.request_context import get_byok_key, reset_byok_key, set_byok_key

# A syntactically valid Google AI Studio key shape: "AIza" + 35 chars.
KEY_A = "AIza" + "A" * 35
KEY_B = "AIza" + "B" * 35

# A real, registered AI route — not a made-up path. The middleware rejects
# before routing, so a typo'd path would make these tests pass for the wrong
# reason and stop noticing if the gate ever moved behind the router.
CHAT_PATH = "/api/v1/chat/11111111-1111-1111-1111-111111111111/send"


@pytest.fixture
def clean_context():
    """Guarantee no key leaks between tests via the module-level ContextVar."""
    token = set_byok_key(None)
    yield
    reset_byok_key(token)


# ── Client resolution ────────────────────────────────────────

class TestClientResolution:
    """create_genai_client must bill whoever actually made the request."""

    def _fresh_factory(self):
        # The cache is reset around every test by an autouse fixture in
        # conftest, so this only needs to hand back the module.
        from app.integrations import vertex_ai_client

        return vertex_ai_client

    def test_caller_key_is_used(self, clean_context):
        mod = self._fresh_factory()
        set_byok_key(KEY_A)
        with patch.object(mod.genai, "Client") as ctor:
            mod.create_genai_client()
        ctor.assert_called_once_with(api_key=KEY_A)

    def test_two_callers_get_two_clients(self, clean_context):
        """The regression that would silently bill user A for user B's chats."""
        mod = self._fresh_factory()
        with patch.object(mod.genai, "Client", side_effect=lambda **kw: MagicMock(**kw)) as ctor:
            set_byok_key(KEY_A)
            mod.create_genai_client()
            set_byok_key(KEY_B)
            mod.create_genai_client()

        used = [c.kwargs.get("api_key") for c in ctor.call_args_list]
        assert used == [KEY_A, KEY_B]

    def test_same_key_reuses_one_client(self, clean_context):
        """Repeat calls must not open a fresh connection pool every time."""
        mod = self._fresh_factory()
        set_byok_key(KEY_A)
        with patch.object(mod.genai, "Client", side_effect=lambda **kw: MagicMock(**kw)) as ctor:
            first = mod.create_genai_client()
            second = mod.create_genai_client()
        assert first is second
        assert ctor.call_count == 1

    def test_falls_back_to_server_key(self, clean_context):
        """No caller key → the operator's own key, exactly as before BYOK."""
        mod = self._fresh_factory()
        with patch.object(mod, "settings") as st:
            st.gemini_api_key = "AIza" + "S" * 35
            with patch.object(mod.genai, "Client") as ctor:
                mod.create_genai_client()
        ctor.assert_called_once_with(api_key="AIza" + "S" * 35)

    def test_falls_back_to_vertex(self, clean_context):
        """No key anywhere → Vertex with ADC, the original behaviour."""
        mod = self._fresh_factory()
        with patch.object(mod, "settings") as st:
            st.gemini_api_key = ""
            st.google_cloud_project = "proj"
            st.google_cloud_location = "global"
            with patch.object(mod.genai, "Client") as ctor:
                mod.create_genai_client()
        ctor.assert_called_once_with(vertexai=True, project="proj", location="global")


class TestClientsAreNotPinned:
    """The singletons must resolve per request, not memoise the first caller."""

    def test_generation_client_not_pinned(self, clean_context):
        from app.integrations.vertex_ai_client import VertexAIClient

        client = VertexAIClient()
        with patch("app.integrations.vertex_ai_client.create_genai_client") as factory:
            factory.side_effect = ["first", "second"]
            assert client._get_client() == "first"
            assert client._get_client() == "second"

    def test_embedding_client_not_pinned(self, clean_context):
        from app.integrations.vertex_embedding_client import VertexEmbeddingClient

        client = VertexEmbeddingClient()
        with patch("app.integrations.vertex_embedding_client.create_genai_client") as factory:
            factory.side_effect = ["first", "second"]
            assert client._get_client() == "first"
            assert client._get_client() == "second"


# ── Key shape validation ─────────────────────────────────────

class TestKeyShape:
    def test_accepts_google_key(self):
        from app.middleware.byok_middleware import looks_like_google_key

        assert looks_like_google_key(KEY_A)

    @pytest.mark.parametrize("bad", [
        "sk_0000000000000000000000000000dead",  # a legacy access key
        "",
        "AIza",
        "AIza" + "A" * 34,                       # one char short
        "AIza" + "A" * 36,                       # one char long
        "BIza" + "A" * 35,                       # wrong prefix
        "AIza" + "A" * 30 + " " + "A" * 4,       # pasted with whitespace
    ])
    def test_rejects_everything_else(self, bad):
        from app.middleware.byok_middleware import looks_like_google_key

        assert not looks_like_google_key(bad)


# ── Middleware gating ────────────────────────────────────────

class TestByokGating:
    """Which paths demand a key, and what a caller without one is told."""

    def _client(self, **overrides):
        from fastapi.testclient import TestClient

        from app.middleware import byok_middleware

        for k, v in overrides.items():
            setattr(byok_middleware.settings, k, v)
        from app.main import create_app

        return TestClient(create_app())

    @pytest.fixture(autouse=True)
    def _restore(self):
        from app.middleware import byok_middleware

        before = (byok_middleware.settings.byok_required, byok_middleware.settings.byok_key_header)
        yield
        byok_middleware.settings.byok_required, byok_middleware.settings.byok_key_header = before

    def test_health_needs_no_key(self):
        client = self._client(byok_required=True, byok_key_header="X-API-Key")
        assert client.get("/api/v1/health").status_code == 200

    def test_ai_route_without_key_is_rejected(self):
        client = self._client(byok_required=True, byok_key_header="X-API-Key")
        r = client.post(CHAT_PATH, json={"message": "hi"})
        assert r.status_code == 401
        assert r.json()["error"] == "byok_key_required"

    def test_legacy_key_gets_a_specific_message(self):
        """An sk_ key must not produce a vague 401 — say what to paste."""
        client = self._client(byok_required=True, byok_key_header="X-API-Key")
        r = client.post(
            CHAT_PATH,
            json={"message": "hi"},
            headers={"X-API-Key": "sk_0000000000000000000000000000dead"},
        )
        assert r.status_code == 401
        assert r.json()["error"] == "byok_key_invalid"

    def test_disabled_byok_passes_everything_through(self):
        """With BYOK off the header is a legacy access key, not a credential."""
        client = self._client(byok_required=False)
        r = client.post(
            CHAT_PATH,
            json={"message": "hi"},
            headers={"X-API-Key": "sk_whatever"},
        )
        assert r.json().get("error") != "byok_key_invalid"


# ── Anonymous identity ───────────────────────────────────────

class TestAnonymousIdentity:
    def test_device_id_is_stable(self):
        from app.utils.anonymous_identity import anonymous_uid

        assert anonymous_uid("device-xyz", "1.2.3.4") == anonymous_uid("device-xyz", "9.9.9.9")

    def test_different_devices_are_different_users(self):
        from app.utils.anonymous_identity import anonymous_uid

        assert anonymous_uid("device-a", None) != anonymous_uid("device-b", None)

    def test_ip_fallback_when_no_device_id(self):
        from app.utils.anonymous_identity import ANON_UID_PREFIX, anonymous_uid

        uid = anonymous_uid(None, "203.0.113.7")
        assert uid.startswith(f"{ANON_UID_PREFIX}ip-")
        assert anonymous_uid(None, "203.0.113.7") == uid

    def test_ip_is_not_stored_in_the_clear(self):
        """The uid ends up in the database; a raw IP there is personal data."""
        from app.utils.anonymous_identity import anonymous_uid

        assert "203.0.113.7" not in anonymous_uid(None, "203.0.113.7")

    def test_long_device_id_fits_the_column(self):
        from app.utils.anonymous_identity import anonymous_uid

        assert len(anonymous_uid("x" * 500, None)) <= 128


# ── Provider error classification ────────────────────────────

class TestInvalidKeyClassification:
    """A rejected user key must not surface as "an unexpected error"."""

    @pytest.mark.parametrize("message", [
        "400 INVALID_ARGUMENT. API key not valid. Please pass a valid API key.",
        "403 PERMISSION_DENIED: API_KEY_INVALID",
        "SERVICE_DISABLED: Generative Language API has not been used in project 123 before",
    ])
    def test_classified_as_invalid_key(self, message):
        from app.utils.provider_errors import ProviderErrorKind, classify

        err = classify(RuntimeError(message))
        assert err.kind is ProviderErrorKind.INVALID_KEY
        assert err.status_code == 401
        assert err.error_code == "byok_key_invalid"

    def test_quota_still_classified_as_quota(self):
        """The new branch must not swallow the case that already worked."""
        from app.utils.provider_errors import ProviderErrorKind, classify

        err = classify(RuntimeError("429 RESOURCE_EXHAUSTED: exceeded your current quota"))
        assert err.kind is ProviderErrorKind.QUOTA_EXHAUSTED


def test_chat_path_used_by_these_tests_is_real():
    """Guard against the gating tests above passing on a nonexistent route."""
    from app.main import create_app

    assert "/api/v1/chat/{conversation_id}/send" in create_app().openapi()["paths"]


# ── Credential redaction in logs ─────────────────────────────

class TestLogRedaction:
    """A user's Google key must never reach the logs.

    It travels in the WebSocket URL, and uvicorn's access logger writes full
    request lines — so without redaction every chat connection would leave a
    live, billable third-party credential in the container logs.
    """

    def test_query_string_key_is_redacted(self):
        from app.utils.logger import redact_secrets

        line = f'GET /api/v1/chat/abc/ws?api_key={KEY_A}&device_id=x HTTP/1.1" 200'
        out = redact_secrets(line)
        assert KEY_A not in out
        assert "device_id=x" in out  # only the secret is removed

    def test_bare_key_anywhere_is_redacted(self):
        from app.utils.logger import redact_secrets

        assert KEY_A not in redact_secrets(f"provider rejected {KEY_A} today")

    def test_ordinary_lines_are_untouched(self):
        from app.utils.logger import redact_secrets

        line = "GET /api/v1/health HTTP/1.1 200"
        assert redact_secrets(line) == line

    def test_filter_scrubs_the_record(self):
        import logging

        from app.utils.logger import _RedactingFilter

        record = logging.LogRecord(
            name="uvicorn.access", level=logging.INFO, pathname=__file__, lineno=1,
            msg="connection open ?api_key=%s", args=(KEY_A,), exc_info=None,
        )
        assert _RedactingFilter().filter(record) is True
        assert KEY_A not in record.getMessage()


# ── Per-caller model choice ──────────────────────────────────

class TestPersonalModelChoice:
    """Which model serves a tier is personal, because the caller pays for it.

    The failure this guards against is one user hitting a rate limit, switching
    model, and moving every other user onto it — including users whose key
    cannot call it at all.
    """

    @pytest.fixture
    def clean_choice(self):
        from app.config.request_context import ModelChoice, reset_model_choice, set_model_choice

        token = set_model_choice(ModelChoice())
        yield
        reset_model_choice(token)

    async def _resolve(self, tier):
        from app.services.model_config_service import ModelConfigService

        svc = ModelConfigService()
        # No Redis in tests; _overrides swallows the failure and yields {},
        # which is exactly the "no admin default set" case.
        return await svc.resolve(tier)

    async def test_choice_beats_env(self, clean_choice):
        from app.config.request_context import ModelChoice, set_model_choice

        set_model_choice(ModelChoice(strong="gemini-flash-lite-latest"))
        resolved = await self._resolve("strong")
        assert resolved.model == "gemini-flash-lite-latest"
        assert resolved.source == "personal"

    async def test_untouched_tier_falls_through(self, clean_choice):
        from app.config.request_context import ModelChoice, set_model_choice

        set_model_choice(ModelChoice(strong="gemini-flash-lite-latest"))
        assert (await self._resolve("cheap")).source != "personal"

    async def test_no_choice_uses_deployment_value(self, clean_choice):
        assert (await self._resolve("strong")).source in ("env", "override")

    async def test_two_callers_do_not_collide(self, clean_choice):
        """The whole point: one user's switch must not reach another user."""
        from app.config.request_context import ModelChoice, set_model_choice

        set_model_choice(ModelChoice(strong="model-a"))
        first = (await self._resolve("strong")).model
        set_model_choice(ModelChoice(strong="model-b"))
        second = (await self._resolve("strong")).model
        assert (first, second) == ("model-a", "model-b")


class TestModelChoiceExtraction:
    """Reading the selection off the wire — headers on HTTP, query on WS."""

    def _scope(self, kind="http", headers=None, query=b""):
        return {
            "type": kind,
            "path": "/api/v1/chat/x/send",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "query_string": query,
        }

    def test_reads_http_headers(self):
        from app.middleware.byok_middleware import extract_model_choice

        c = extract_model_choice(self._scope(headers={"X-Model-Strong": "m-strong",
                                                      "X-Model-Cheap": "m-cheap"}))
        assert (c.strong, c.cheap) == ("m-strong", "m-cheap")

    def test_reads_websocket_query(self):
        """Browsers cannot set headers on a WebSocket handshake."""
        from app.middleware.byok_middleware import extract_model_choice

        c = extract_model_choice(self._scope("websocket", query=b"model_strong=m1&model_cheap=m2"))
        assert (c.strong, c.cheap) == ("m1", "m2")

    def test_absent_means_empty(self):
        from app.middleware.byok_middleware import extract_model_choice

        assert extract_model_choice(self._scope()).is_empty

    @pytest.mark.parametrize("junk", ["", "   ", "has space", "ünicode"])
    def test_rejects_malformed(self, junk):
        from app.middleware.byok_middleware import extract_model_choice

        assert extract_model_choice(self._scope(headers={"X-Model-Strong": junk})).strong is None

    def test_truncates_absurd_length(self):
        from app.middleware.byok_middleware import extract_model_choice

        c = extract_model_choice(self._scope(headers={"X-Model-Strong": "m" * 5000}))
        assert c.strong is not None and len(c.strong) <= 100
