"""FastAPI router for settings management — BYOK config, test connections."""

import tempfile
from pathlib import Path

from fastapi import APIRouter

from app.settings.config_store import (
    clear_key,
    get_masked_status,
    get_value,
    mask_key,
    set_config,
)
from app.settings.schemas import (
    ClearKeyRequest,
    SettingsSaveRequest,
    SettingsStatusResponse,
    TestConnectionResponse,
)
from app.vision.openai_adapter import OpenAIVisionAdapter

router = APIRouter(prefix="/settings", tags=["settings"])

PLACEHOLDER_KEYS = {
    "", "replace-me", "your_deepseek_api_key_here",
    "your_openai_api_key_here", "replace-with-your-key",
}


def _is_configured(val: str) -> bool:
    return bool(val) and val not in PLACEHOLDER_KEYS


_VISION_TEST_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6360000002000100ffff0300000600"
    "0557bfab0000000049454e44ae426082"
)


def _test_openai_vision_adapter(api_key: str, model: str) -> None:
    """Exercise the same image adapter path used by the workbench."""
    adapter = OpenAIVisionAdapter(api_key=api_key, model=model)
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(_VISION_TEST_PNG)
            tmp_path = tmp.name
        adapter.describe_image_structured(tmp_path)
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


# ── GET /settings ──────────────────────────────────────────────────────

@router.get("", response_model=SettingsStatusResponse)
def get_settings() -> SettingsStatusResponse:
    """Return current config status with API keys masked."""
    status = get_masked_status()
    return SettingsStatusResponse(**status)


# ── POST /settings ─────────────────────────────────────────────────────

@router.post("", status_code=200)
def save_settings(body: SettingsSaveRequest) -> dict:
    """Save config.  Empty string fields are skipped — they do NOT overwrite
    existing values.  Use ``POST /settings/clear-key`` to explicitly clear a key.
    """
    # DeepSeek section
    ds_updates: dict[str, str] = {}
    if body.deepseek_api_key:
        ds_updates["api_key"] = body.deepseek_api_key
    if body.deepseek_base_url:
        ds_updates["base_url"] = body.deepseek_base_url
    if body.deepseek_default_model:
        ds_updates["default_model"] = body.deepseek_default_model
    if body.deepseek_reasoning_model:
        ds_updates["reasoning_model"] = body.deepseek_reasoning_model
    if ds_updates:
        set_config("deepseek", ds_updates)

    # Vision section
    vs_updates: dict[str, str] = {}
    if body.vision_provider:
        vs_updates["provider"] = body.vision_provider
    if body.openai_api_key:
        vs_updates["openai_api_key"] = body.openai_api_key
    if body.openai_vision_model:
        vs_updates["openai_vision_model"] = body.openai_vision_model
    if vs_updates:
        set_config("vision", vs_updates)

    return {"status": "ok"}


# ── POST /settings/clear-key ───────────────────────────────────────────

KEY_MAP = {
    "deepseek": ("deepseek", "api_key"),
    "openai": ("vision", "openai_api_key"),
}


@router.post("/clear-key", status_code=200)
def clear_settings_key(body: ClearKeyRequest) -> dict:
    """Clear the API key for the specified provider.

    ``key_type`` must be ``"deepseek"`` or ``"openai"``.
    """
    section, key = KEY_MAP[body.key_type]
    clear_key(section, key)
    return {"status": "ok", "key_type": body.key_type, "cleared": True}


# ── POST /settings/test-deepseek ───────────────────────────────────────

def _make_client(api_key: str, base_url: str):
    """Create an OpenAI-compatible client for connectivity testing."""
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url)


@router.post("/test-deepseek", response_model=TestConnectionResponse)
def test_deepseek_connection() -> TestConnectionResponse:
    """Test the current DeepSeek API key with a minimal chat request."""
    api_key = get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY")
    if not _is_configured(api_key):
        return TestConnectionResponse(
            success=False,
            message="未配置 DeepSeek API Key，请先保存 API Key。",
        )

    base_url = (
        get_value("deepseek", "base_url", env_var="DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com"
    )
    model = (
        get_value("deepseek", "default_model", env_var="DEEPSEEK_DEFAULT_MODEL")
        or "deepseek-v4-flash"
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in Chinese"}],
            max_tokens=20,
            timeout=15,
        )
        content = resp.choices[0].message.content or ""
        return TestConnectionResponse(
            success=True,
            message=f"连接成功：DeepSeek 返回「{content.strip()}」",
            model_used=model,
        )
    except Exception:
        return TestConnectionResponse(
            success=False,
            message="连接失败：请检查 API Key 和网络连接是否正常。",
            model_used=model,
        )


# ── POST /settings/test-vision ─────────────────────────────────────────

@router.post("/test-vision", response_model=TestConnectionResponse)
def test_vision_connection() -> TestConnectionResponse:
    """Test the current Vision provider configuration.

    * ``placeholder`` / ``manual`` — returns success immediately (no real API).
    * ``openai`` — calls the real image adapter with a tiny test image.
    """
    provider = (
        get_value("vision", "provider", env_var="VISION_PROVIDER")
        or "placeholder"
    ).strip().lower()

    if provider in ("placeholder", "manual"):
        return TestConnectionResponse(
            success=True,
            message=f"当前 Vision 提供者为 {provider}，无需测试外部连接。如需真实图片识别，请切换为 openai 并配置 API Key。",
        )

    if provider == "openai":
        api_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY")
        if not _is_configured(api_key):
            return TestConnectionResponse(
                success=False,
                message="未配置 OpenAI API Key，请先保存 API Key。",
            )
        model = (
            get_value("vision", "openai_vision_model", env_var="OPENAI_VISION_MODEL")
            or "gpt-4o-mini"
        )
        try:
            _test_openai_vision_adapter(api_key, model)
            return TestConnectionResponse(
                success=True,
                message="OpenAI Vision 图片识别测试成功。",
                model_used=model,
            )
        except Exception:
            return TestConnectionResponse(
                success=False,
                message="Vision 测试失败：请检查 OpenAI API Key、模型是否支持图片输入，以及网络连接是否正常。",
                model_used=model,
            )

    return TestConnectionResponse(
        success=False,
        message=f"不支持的 Vision 提供者：{provider}",
    )
