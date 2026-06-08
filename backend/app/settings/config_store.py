"""Persistent BYOK config store backed by data/config/app_config.json.

Priority chain: JSON file > environment variable > hardcoded default.
"""

import json
import os
import time
from pathlib import Path
from copy import deepcopy

# ── Path resolution ────────────────────────────────────────────────────
_DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "data"),
    )
)
CONFIG_DIR = _DATA_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "app_config.json"

# Default values for the config file skeleton — ALL empty so that .env
# values are never shadowed by hard-coded defaults on fresh installs.
# The real defaults live in get_value()'s ``default`` kwarg and in the
# ``or`` fallbacks used by callers (get_masked_status, deepseek_client, etc.).
DEFAULT_CONFIG: dict[str, dict[str, str]] = {
    "deepseek": {
        "api_key": "",
        "base_url": "",
        "default_model": "",
        "reasoning_model": "",
    },
    "vision": {
        "provider": "",
        "openai_api_key": "",
        "openai_vision_model": "",
    },
}

PLACEHOLDER_CONFIG_VALUES = {
    "",
    "replace-me",
    "your_deepseek_api_key_here",
    "your_openai_api_key_here",
    "your_anthropic_api_key_here",
    "your_gemini_api_key_here",
    "replace-with-your-key",
}

# Sentinel written by clear_key() so that get_value() knows the user
# explicitly cleared the field and .env fallback should NOT be used.
_CLEARED_SENTINEL = "\x00CLEARED"

# ── TTL cache ──────────────────────────────────────────────────────────
_cache: dict | None = None
_cache_ts: float = 0.0
_CACHE_TTL: float = 1.0  # seconds


def _invalidate_cache() -> None:
    """Force next get_config() to re-read from disk."""
    global _cache, _cache_ts
    _cache = None
    _cache_ts = 0.0


def _ensure_config_exists() -> None:
    """Create config directory and default config file if missing."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _read_config() -> dict:
    """Read config from disk. Returns defaults if file is missing or corrupt."""
    _ensure_config_exists()
    try:
        raw = CONFIG_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except (json.JSONDecodeError, FileNotFoundError):
        return deepcopy(DEFAULT_CONFIG)


def write_config(data: dict) -> None:
    """Atomically write config to disk (temp file + rename).

    Public alias for ``_write_config`` — use this when you need to clear
    values by writing empty strings (``set_config`` skips empty values).

    Cache is invalidated **before** any I/O to prevent a narrow window
    where a concurrent reader could see stale cached data while the
    disk write is in progress (GIL is released during file operations).
    """
    _invalidate_cache()
    _ensure_config_exists()
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        tmp.replace(CONFIG_FILE)
    except OSError:
        # On Windows, replace can fail if the file is locked.
        # Fall back to direct write.
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    _invalidate_cache()


# Keep private alias for internal use (set_config, clear_key)
_write_config = write_config


# ── Public API ─────────────────────────────────────────────────────────

def get_config() -> dict:
    """Return current config dict (cached for 1 second)."""
    global _cache, _cache_ts
    now = time.time()
    if _cache is not None and (now - _cache_ts) < _CACHE_TTL:
        return _cache
    _cache = _read_config()
    _cache_ts = now
    return _cache


def get_value(
    section: str,
    key: str,
    env_var: str | None = None,
    default: str = "",
) -> str:
    """Return a config value following the priority chain:

    app_config.json > environment variable > hardcoded default

    If the user explicitly cleared the key via ``clear_key()`` the JSON
    value will be the ``_CLEARED_SENTINEL`` — in that case we return ""
    immediately, skipping the env fallback.
    """
    config = get_config()
    val = config.get(section, {}).get(key, "")
    if val == _CLEARED_SENTINEL:
        return ""  # user explicitly cleared — suppress env fallback
    if val:
        return val
    if env_var:
        env_val = os.getenv(env_var, "")
        if env_val:
            return env_val
    return default


def set_config(section: str, data: dict[str, str]) -> None:
    """Merge data into the specified config section.

    Empty string values are skipped — they do not overwrite existing keys.
    """
    config = get_config()
    if section not in config:
        config[section] = {}
    for key, value in data.items():
        if value:  # skip empty — don't overwrite
            config[section][key] = value
    _write_config(config)


def clear_key(section: str, key: str) -> None:
    """Set a key to the CLEARED sentinel so that get_value() returns ""
    even when an environment variable would otherwise provide a fallback.

    The sentinel (``\\x00CLEARED``) is never a valid API key / URL / model
    name, so it cannot collide with a real value.
    """
    config = get_config()
    if section not in config:
        config[section] = {}
    config[section][key] = _CLEARED_SENTINEL
    _write_config(config)


def is_configured_value(value: str) -> bool:
    """Return whether a secret/config value is present and not a placeholder."""
    return bool(value) and value.strip() not in PLACEHOLDER_CONFIG_VALUES


def get_vision_provider() -> str:
    """Return the effective Vision provider using config > env > default."""
    return (
        get_value("vision", "provider", env_var="VISION_PROVIDER")
        or "placeholder"
    ).strip().lower()


def get_vision_missing_keys(provider: str | None = None) -> list[str]:
    """Return missing config keys for the current/effective Vision provider."""
    provider = (provider or get_vision_provider()).strip().lower()
    if provider in ("placeholder", "manual"):
        return []

    required_values: dict[str, dict[str, str]] = {
        "openai": {
            "OPENAI_API_KEY": get_value(
                "vision",
                "openai_api_key",
                env_var="OPENAI_API_KEY",
            ),
        },
        "claude": {
            "ANTHROPIC_API_KEY": get_value(
                "vision",
                "anthropic_api_key",
                env_var="ANTHROPIC_API_KEY",
            ),
        },
        "gemini": {
            "GEMINI_API_KEY": get_value(
                "vision",
                "gemini_api_key",
                env_var="GEMINI_API_KEY",
            ),
        },
    }

    required = required_values.get(provider)
    if required is None:
        return ["VISION_PROVIDER"]
    return [name for name, value in required.items() if not is_configured_value(value)]


def is_vision_configured(provider: str | None = None) -> bool:
    """Return whether the current/effective Vision provider is usable."""
    return not get_vision_missing_keys(provider)


def mask_key(value: str) -> str:
    """Mask an API key for display.  Examples:

    * ``""`` → ``""``
    * ``"abcd"`` → ``"****"``
    * ``"sk-a1b2c3d4e5f6"`` → ``"sk-a***e5f6"``
    """
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def get_masked_status() -> dict:
    """Return config status dict with API keys masked for display.

    Intended for the ``GET /settings`` response.

    Uses ``get_value()`` for fields that may be empty in the JSON file
    but set via environment variables — this ensures the full priority
    chain (config > env > default) is applied, not just the raw file
    content.
    """
    provider = get_vision_provider()
    openai_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY")

    return {
        "deepseek": {
            "is_configured": is_configured_value(
                get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY")
            ),
            "api_key_masked": mask_key(
                get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY")
            ),
            "base_url": (
                get_value("deepseek", "base_url", env_var="DEEPSEEK_BASE_URL")
                or "https://api.deepseek.com"
            ),
            "default_model": (
                get_value("deepseek", "default_model", env_var="DEEPSEEK_DEFAULT_MODEL")
                or "deepseek-v4-flash"
            ),
            "reasoning_model": (
                get_value("deepseek", "reasoning_model", env_var="DEEPSEEK_REASONING_MODEL")
                or "deepseek-v4-pro"
            ),
        },
        "vision": {
            "provider": provider,
            "is_configured": is_vision_configured(provider),
            "openai_api_key_masked": mask_key(openai_key),
            "openai_vision_model": (
                get_value("vision", "openai_vision_model", env_var="OPENAI_VISION_MODEL")
                or "gpt-4o-mini"
            ),
        },
    }
