"""Tests for V1.7 settings endpoints and config store."""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import config_store as cs

# Re-use the in-memory DB and mock agent overrides from test_api.py
from app.tests.test_api import (
    TestSessionLocal,
    override_get_db,
    MockAnalyzerAgent,
    MockCriticAgent,
    MockIteratorAgent,
    MockProfileAgent,
    MockComparatorAgent,
    MockReferenceComparatorAgent,
    MockPromptGeneratorAgent,
    MockWeeklyReviewAgent,
)

from app.db.database import Base, get_db
from app.main import (
    get_analyzer, get_critic, get_iterator,
    get_profile_agent, get_comparator,
    get_reference_comparator, get_prompt_generator,
    get_weekly_reviewer, get_vision_adapter,
)
from app.vision.manual_adapter import ManualAdapter


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_test_db():
    """Create in-memory tables for each test."""
    from app.tests.test_api import test_engine
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Point config_store to a temp directory for isolation."""
    config_dir = tmp_path / "data" / "config"
    config_dir.mkdir(parents=True)

    orig_dir = cs.CONFIG_DIR
    orig_file = cs.CONFIG_FILE
    cs.CONFIG_DIR = config_dir
    cs.CONFIG_FILE = config_dir / "app_config.json"
    cs._invalidate_cache()
    yield config_dir
    cs.CONFIG_DIR = orig_dir
    cs.CONFIG_FILE = orig_file
    cs._invalidate_cache()


@pytest.fixture
def settings_client(temp_config_dir, setup_test_db, monkeypatch):
    """TestClient with clean config + mocked agents, no proxy env."""
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)

    from app.tests.test_api import test_engine
    def _override_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_analyzer] = lambda: MockAnalyzerAgent()
    app.dependency_overrides[get_critic] = lambda: MockCriticAgent()
    app.dependency_overrides[get_iterator] = lambda: MockIteratorAgent()
    app.dependency_overrides[get_profile_agent] = lambda: MockProfileAgent()
    app.dependency_overrides[get_comparator] = lambda: MockComparatorAgent()
    app.dependency_overrides[get_reference_comparator] = lambda: MockReferenceComparatorAgent()
    app.dependency_overrides[get_prompt_generator] = lambda: MockPromptGeneratorAgent()
    app.dependency_overrides[get_weekly_reviewer] = lambda: MockWeeklyReviewAgent()
    app.dependency_overrides[get_vision_adapter] = lambda: ManualAdapter()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Helper ─────────────────────────────────────────────────────────────

def _save(settings_client, ds_api_key="", vision_provider="", openai_key=""):
    """Convenience: save settings with optional fields."""
    body: dict = {}
    if ds_api_key:
        body["deepseek_api_key"] = ds_api_key
    if vision_provider:
        body["vision_provider"] = vision_provider
    if openai_key:
        body["openai_api_key"] = openai_key
    if not body:
        return
    return settings_client.post("/settings", json=body)


# ── Test: GET /settings ────────────────────────────────────────────────

class TestGetSettings:
    def test_returns_defaults_when_no_config(self, settings_client, monkeypatch):
        # Clear env vars so we test true defaults (not .env fallback)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
        monkeypatch.delenv("DEEPSEEK_DEFAULT_MODEL", raising=False)
        monkeypatch.delenv("DEEPSEEK_REASONING_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
        monkeypatch.delenv("VISION_PROVIDER", raising=False)
        cs._invalidate_cache()

        resp = settings_client.get("/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deepseek"]["is_configured"] is False
        assert data["deepseek"]["base_url"] == "https://api.deepseek.com"
        assert data["deepseek"]["default_model"] == "deepseek-v4-flash"
        assert data["deepseek"]["reasoning_model"] == "deepseek-v4-pro"
        assert data["vision"]["provider"] == "placeholder"
        assert data["vision"]["is_configured"] is True

    def test_does_not_expose_raw_api_keys(self, settings_client):
        _save(settings_client, ds_api_key="sk-top-secret-12345678")
        resp = settings_client.get("/settings")
        data = resp.json()
        body = json.dumps(data)
        assert "sk-top-secret-12345678" not in body
        assert "sk-top-secret" not in body
        # Should show masked version
        assert data["deepseek"]["api_key_masked"] != ""

    def test_masked_key_format(self, settings_client):
        _save(settings_client, ds_api_key="sk-short")
        resp = settings_client.get("/settings")
        assert resp.json()["deepseek"]["api_key_masked"] == "********"

        _save(settings_client, ds_api_key="sk-longtestkey12345678")
        resp = settings_client.get("/settings")
        masked = resp.json()["deepseek"]["api_key_masked"]
        assert masked.startswith("sk-l")
        assert masked.endswith("5678")
        assert "*" in masked


# ── Test: POST /settings ───────────────────────────────────────────────

class TestSaveSettings:
    def test_saves_deepseek_key(self, settings_client, temp_config_dir):
        resp = _save(settings_client, ds_api_key="sk-my-key")
        assert resp.status_code == 200

        # Verify on disk
        raw = json.loads((temp_config_dir / "app_config.json").read_text())
        assert raw["deepseek"]["api_key"] == "sk-my-key"

        # Verify via GET
        status = settings_client.get("/settings").json()
        assert status["deepseek"]["is_configured"] is True

    def test_empty_key_does_not_overwrite(self, settings_client):
        _save(settings_client, ds_api_key="sk-original")
        # Try to save with empty — should preserve original
        resp = settings_client.post("/settings", json={"deepseek_api_key": ""})
        assert resp.status_code == 200
        config = cs.get_config()
        assert config["deepseek"]["api_key"] == "sk-original"

    def test_partial_save_only_updates_given_section(self, settings_client, monkeypatch):
        # Ensure env doesn't provide vision key as fallback
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("VISION_PROVIDER", raising=False)
        cs._invalidate_cache()

        _save(settings_client, ds_api_key="sk-ds")
        status = settings_client.get("/settings").json()
        assert status["deepseek"]["is_configured"] is True
        # Vision should still be the default placeholder provider.
        assert status["vision"]["provider"] == "placeholder"
        assert status["vision"]["is_configured"] is True
        assert status["vision"]["openai_api_key_masked"] == ""

    def test_saves_vision_provider_and_key(self, settings_client):
        resp = settings_client.post("/settings", json={
            "vision_provider": "openai",
            "openai_api_key": "sk-vision-key",
        })
        assert resp.status_code == 200
        status = settings_client.get("/settings").json()
        assert status["vision"]["provider"] == "openai"
        assert status["vision"]["is_configured"] is True

    def test_openai_key_is_masked_in_response(self, settings_client):
        _save(settings_client, vision_provider="openai", openai_key="sk-openai-secret-1234")
        resp = settings_client.get("/settings")
        body = json.dumps(resp.json())
        assert "sk-openai-secret-1234" not in body


# ── Test: POST /settings/clear-key ─────────────────────────────────────

class TestClearKey:
    def test_clears_deepseek_key(self, settings_client, monkeypatch):
        # Ensure env doesn't provide a fallback after clearing
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        cs._invalidate_cache()

        _save(settings_client, ds_api_key="sk-will-clear")
        resp = settings_client.post("/settings/clear-key", json={"key_type": "deepseek"})
        assert resp.status_code == 200
        status = settings_client.get("/settings").json()
        assert status["deepseek"]["is_configured"] is False

    def test_clears_openai_key(self, settings_client, monkeypatch):
        # Ensure env doesn't provide a fallback after clearing
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        cs._invalidate_cache()

        _save(settings_client, vision_provider="openai", openai_key="sk-clear-me")
        resp = settings_client.post("/settings/clear-key", json={"key_type": "openai"})
        assert resp.status_code == 200
        status = settings_client.get("/settings").json()
        assert status["vision"]["is_configured"] is False

    def test_cleared_openai_key_suppresses_env_fallback(self, settings_client, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-fallback")

        _save(settings_client, vision_provider="openai", openai_key="sk-clear-me")
        resp = settings_client.post("/settings/clear-key", json={"key_type": "openai"})
        assert resp.status_code == 200

        settings_status = settings_client.get("/settings").json()
        assert settings_status["vision"]["is_configured"] is False

        vision_status = settings_client.get("/vision/status").json()
        assert vision_status["vision_provider"] == "openai"
        assert vision_status["is_configured"] is False
        assert "OPENAI_API_KEY" in vision_status["missing_keys"]


# ── Test: POST /settings/test-deepseek ─────────────────────────────────

class TestTestDeepSeek:
    def test_returns_failure_when_unconfigured(self, settings_client, monkeypatch):
        # Clear both config AND env so it's truly unconfigured
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # Clear any env-set key in config
        cs.set_config("deepseek", {"api_key": ""})
        cs._invalidate_cache()

        resp = settings_client.post("/settings/test-deepseek")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "未配置" in data["message"] or "API Key" in data["message"]

    def test_returns_structured_result_with_fake_key(self, settings_client, monkeypatch):
        # Ensure env doesn't provide a real key
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        _save(settings_client, ds_api_key="sk-fake-test-key-not-real")
        resp = settings_client.post("/settings/test-deepseek")
        assert resp.status_code == 200
        data = resp.json()
        # Should fail (fake key) but NOT 500
        assert "success" in data
        assert "model_used" in data


# ── Test: POST /settings/test-vision ───────────────────────────────────

class TestTestVision:
    def test_vision_test_image_is_valid_png(self):
        from app.settings.routes import _make_vision_test_png

        png = _make_vision_test_png()
        width = int.from_bytes(png[16:20], "big")
        height = int.from_bytes(png[20:24], "big")

        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        assert width == 64
        assert height == 64
        assert b"IDAT" in png

    def test_placeholder_returns_success_with_note(self, settings_client, monkeypatch):
        # Ensure provider=placeholder and no OpenAI key in env/config
        monkeypatch.setenv("VISION_PROVIDER", "placeholder")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from app.settings import config_store as cs
        # Clear config to empty (not CLEARED sentinel) so env fallback works
        config = cs.get_config()
        config["vision"]["provider"] = ""
        config["vision"]["openai_api_key"] = ""
        cs.write_config(config)

        resp = settings_client.post("/settings/test-vision")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "placeholder" in data["message"].lower()

    def test_openai_without_key_returns_failure(self, settings_client, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _save(settings_client, vision_provider="openai")
        cs._invalidate_cache()
        resp = settings_client.post("/settings/test-vision")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "未配置" in data["message"] or "API Key" in data["message"]

    def test_openai_test_uses_vision_adapter_path(self, settings_client, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
        from app.settings import routes as settings_routes

        called: dict[str, str] = {}

        def fake_vision_test(api_key: str, model: str) -> None:
            called["api_key"] = api_key
            called["model"] = model

        monkeypatch.setattr(settings_routes, "_test_openai_vision_adapter", fake_vision_test)
        _save(settings_client, vision_provider="openai", openai_key="sk-vision-key")

        resp = settings_client.post("/settings/test-vision")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["model_used"] == "gpt-4o-mini"
        assert called == {"api_key": "sk-vision-key", "model": "gpt-4o-mini"}

    def test_openai_test_does_not_expose_raw_exception(self, settings_client, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_VISION_MODEL", raising=False)
        from app.settings import routes as settings_routes

        def fake_vision_test(api_key: str, model: str) -> None:
            raise RuntimeError("raw provider error with sk-secret")

        monkeypatch.setattr(settings_routes, "_test_openai_vision_adapter", fake_vision_test)
        _save(settings_client, vision_provider="openai", openai_key="sk-vision-key")

        resp = settings_client.post("/settings/test-vision")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "sk-secret" not in data["message"]


# ── Test: /model/status uses config_store ──────────────────────────────

class TestModelStatusUsesConfig:
    def test_reads_from_config(self, settings_client, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_DEFAULT_MODEL", raising=False)

        _save(settings_client, ds_api_key="sk-from-config")
        # Also set model in config
        settings_client.post("/settings", json={
            "deepseek_default_model": "deepseek-custom-model",
        })

        cs._invalidate_cache()
        resp = settings_client.get("/model/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_configured"] is True
        assert data["default_model"] == "deepseek-custom-model"

    def test_falls_back_to_default_when_no_config_or_env(self):
        """When config and env are both empty, returns the provided default."""
        cs.set_config("deepseek", {"default_model": ""})
        cs._invalidate_cache()

        val = cs.get_value("deepseek", "default_model", env_var="NONEXISTENT_ENV_VAR_ZZZ", default="deepseek-v4-flash")
        assert val == "deepseek-v4-flash"


# ── Test: /vision/status uses config_store ─────────────────────────────

class TestVisionStatusUsesConfig:
    def test_settings_and_vision_status_match_for_placeholder(self, settings_client, monkeypatch):
        monkeypatch.delenv("VISION_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        config = cs.get_config()
        config["vision"]["provider"] = ""
        config["vision"]["openai_api_key"] = ""
        cs.write_config(config)

        settings_status = settings_client.get("/settings").json()
        vision_status = settings_client.get("/vision/status").json()

        assert settings_status["vision"]["provider"] == "placeholder"
        assert settings_status["vision"]["is_configured"] is True
        assert vision_status["vision_provider"] == "placeholder"
        assert vision_status["is_configured"] is True

    def test_settings_and_vision_status_match_for_openai_missing_key(self, settings_client, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        _save(settings_client, vision_provider="openai")

        settings_status = settings_client.get("/settings").json()
        vision_status = settings_client.get("/vision/status").json()

        assert settings_status["vision"]["provider"] == "openai"
        assert settings_status["vision"]["is_configured"] is False
        assert vision_status["vision_provider"] == "openai"
        assert vision_status["is_configured"] is False

    def test_reads_from_config(self, settings_client, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        _save(settings_client, vision_provider="openai", openai_key="sk-vs-from-config")

        resp = settings_client.get("/vision/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vision_provider"] == "openai"
        assert data["is_configured"] is True


# ── Test: existing endpoints unaffected ────────────────────────────────

class TestExistingEndpointsUnaffected:
    def test_analyze_still_works(self, settings_client):
        resp = settings_client.post(
            "/analyze",
            json={"work_description": "A blue button on white with Helvetica text."},
        )
        assert resp.status_code == 200
        assert "color" in resp.json()

    def test_critique_still_works(self, settings_client):
        resp = settings_client.post(
            "/critique",
            json={"work_description": "A neon poster with five different fonts."},
        )
        assert resp.status_code == 200
        assert "total_score" in resp.json()

    def test_iterate_still_works(self, settings_client):
        resp = settings_client.post(
            "/iterate",
            json={"work_description": "A dashboard with charts and a sidebar."},
        )
        assert resp.status_code == 200
        assert "directions" in resp.json()

    def test_health_still_works(self, settings_client):
        resp = settings_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Test: config persistence ────────────────────────────────────────────

class TestConfigPersistence:
    def test_config_survives_reset(self, settings_client, temp_config_dir):
        _save(settings_client, ds_api_key="sk-survivor")
        # Invalidate and re-read
        cs._invalidate_cache()
        config = cs.get_config()
        assert config["deepseek"]["api_key"] == "sk-survivor"

    def test_get_value_priority_json_over_default(self, settings_client):
        """JSON config takes priority over hardcoded default."""
        # Clear config value
        cs.set_config("deepseek", {"default_model": ""})
        cs._invalidate_cache()

        # With nothing set, should get hardcoded default
        val = cs.get_value("deepseek", "default_model", default="deepseek-v4-flash")
        assert val == "deepseek-v4-flash"

        # Save to config — should take priority over default
        settings_client.post("/settings", json={"deepseek_default_model": "json-priority-model"})
        cs._invalidate_cache()
        val = cs.get_value("deepseek", "default_model", default="deepseek-v4-flash")
        assert val == "json-priority-model"
