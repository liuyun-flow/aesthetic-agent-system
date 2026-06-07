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

DEFAULT_CONFIG: dict[str, dict[str, str]] = {
    "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "reasoning_model": "deepseek-v4-pro",
    },
    "vision": {
        "provider": "placeholder",
        "openai_api_key": "",
        "openai_vision_model": "gpt-4o-mini",
    },
}

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
    """
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
    """
    config = get_config()
    val = config.get(section, {}).get(key, "")
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
    """Set a key to empty string, falling back to env/default on next read."""
    config = get_config()
    if section in config and key in config[section]:
        config[section][key] = ""
    _write_config(config)


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
    """
    config = get_config()
    ds = config.get("deepseek", {})
    vs = config.get("vision", {})

    dskey = ds.get("api_key", "")
    oaikey = vs.get("openai_api_key", "")
    placeholder_keys = {"", "replace-me", "your_deepseek_api_key_here",
                        "your_openai_api_key_here", "replace-with-your-key"}

    def _ok(v: str) -> bool:
        return bool(v) and v not in placeholder_keys

    return {
        "deepseek": {
            "is_configured": _ok(dskey),
            "api_key_masked": mask_key(dskey),
            "base_url": ds.get("base_url", "https://api.deepseek.com"),
            "default_model": ds.get("default_model", "deepseek-v4-flash"),
            "reasoning_model": ds.get("reasoning_model", "deepseek-v4-pro"),
        },
        "vision": {
            "provider": vs.get("provider", "placeholder"),
            "is_configured": _ok(oaikey),
            "openai_api_key_masked": mask_key(oaikey),
            "openai_vision_model": vs.get("openai_vision_model", "gpt-4o-mini"),
        },
    }
