#!/usr/bin/env python3
"""Check that the .env file and settings-page config are properly configured.

Reads both ``backend/.env`` and ``backend/data/config/app_config.json``
so that settings saved via the web UI are also recognized.
"""

import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"

ENV_FILE = BACKEND_DIR / ".env"
EXAMPLE_FILE = BACKEND_DIR / ".env.example"
CONFIG_FILE = BACKEND_DIR / "data" / "config" / "app_config.json"

PLACEHOLDER_KEYS = {"", "replace-me", "your_deepseek_api_key_here",
                    "your_openai_api_key_here", "replace-with-your-key"}


def _mask(v: str) -> str:
    if not v:
        return "(empty)"
    if len(v) <= 8:
        return "*" * len(v)
    return v[:4] + "*" * (len(v) - 8) + v[-4:]


def _load_env() -> dict:
    if not ENV_FILE.exists():
        return {}
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _effective(env: dict, config: dict, section: str, key: str, env_key: str | None = None) -> str:
    """Return the effective value: config > .env > empty."""
    cv = config.get(section, {}).get(key, "")
    if cv == "\x00CLEARED":
        return ""
    if cv:
        return cv
    return env.get(env_key or key, "")


def main() -> int:
    errors = 0

    print("=== Environment & Config Check ===\n")

    # ── .env file ─────────────────────────────────────────────────────
    if not ENV_FILE.exists():
        print(f"[ERROR] {ENV_FILE} not found. Copy {EXAMPLE_FILE} to {ENV_FILE} and edit it.")
        return 1
    print(f"[OK] {ENV_FILE} exists")

    env = _load_env()
    config = _load_config()
    if config:
        print(f"[OK] Settings-page config found ({CONFIG_FILE})")
    else:
        print("[INFO] No settings-page config yet (only .env will be used)")

    # ── DeepSeek API Key ──────────────────────────────────────────────
    ds_key = _effective(env, config, "deepseek", "api_key", env_key="DEEPSEEK_API_KEY")
    ds_source = "config" if config.get("deepseek", {}).get("api_key", "") not in ("", "\x00CLEARED") else "env"
    if ds_key in PLACEHOLDER_KEYS or not ds_key:
        print("[ERROR] DeepSeek API Key is not set. Set it in backend/.env or via the Settings page.")
        errors += 1
    else:
        print(f"[OK] DEEPSEEK_API_KEY configured from {ds_source} ({_mask(ds_key)})")

    # ── DeepSeek model / base URL ─────────────────────────────────────
    ds_base = _effective(env, config, "deepseek", "base_url", env_key="DEEPSEEK_BASE_URL")
    if ds_base:
        print(f"[OK] DeepSeek base_url={ds_base}")
    else:
        print("[INFO] DeepSeek base_url not set (default: https://api.deepseek.com)")

    ds_model = _effective(env, config, "deepseek", "default_model", env_key="DEEPSEEK_DEFAULT_MODEL")
    if ds_model:
        print(f"[INFO] DeepSeek default_model={ds_model}")
    else:
        print("[INFO] DeepSeek default_model not set (default: deepseek-v4-flash)")

    ds_reason = _effective(env, config, "deepseek", "reasoning_model", env_key="DEEPSEEK_REASONING_MODEL")
    if ds_reason:
        print(f"[INFO] DeepSeek reasoning_model={ds_reason}")

    # ── Vision ────────────────────────────────────────────────────────
    vs_provider = _effective(env, config, "vision", "provider", env_key="VISION_PROVIDER")
    if not vs_provider:
        vs_provider = "placeholder"
    vs_source = "config" if config.get("vision", {}).get("provider", "") not in ("", "\x00CLEARED") else "env"
    print(f"[INFO] VISION_PROVIDER={vs_provider} (from {vs_source})")

    if vs_provider == "openai":
        vs_key = _effective(env, config, "vision", "openai_api_key", env_key="OPENAI_API_KEY")
        vs_key_source = "config" if config.get("vision", {}).get("openai_api_key", "") not in ("", "\x00CLEARED") else "env"
        if vs_key in PLACEHOLDER_KEYS or not vs_key:
            print("[ERROR] VISION_PROVIDER=openai but OPENAI_API_KEY is not set.")
            errors += 1
        else:
            print(f"[OK] OPENAI_API_KEY configured from {vs_key_source} ({_mask(vs_key)})")
    elif vs_provider == "placeholder":
        print("[WARN] Using placeholder vision — images will not be analyzed by a real vision model.")

    vs_model = _effective(env, config, "vision", "openai_vision_model", env_key="OPENAI_VISION_MODEL")
    if vs_model:
        print(f"[INFO] Vision model={vs_model}")

    # ── Data dirs ─────────────────────────────────────────────────────
    for subdir in ["database", "uploads"]:
        d = BACKEND_DIR / "data" / subdir
        if d.exists():
            print(f"[OK] data/{subdir}/ exists")
        else:
            print(f"[WARN] data/{subdir}/ does not exist (will be created on startup)")

    # ── Database ──────────────────────────────────────────────────────
    db_url = env.get("DATABASE_URL", "")
    if db_url == "sqlite:///./aesthetic.db":
        print("[WARN] DATABASE_URL=sqlite:///./aesthetic.db is the old default.")
        print("       Under Docker this path is NOT volume-protected — data may be lost on 'docker compose down'.")
        print("       Recommended: DATABASE_URL=sqlite:///./data/database/aesthetic.db")

    db_path = BACKEND_DIR / "data" / "database" / "aesthetic.db"
    old_db = BACKEND_DIR / "aesthetic.db"
    if old_db.exists() and not db_path.exists():
        print(f"[WARN] Found database at old location: {old_db}")
        print(f"       Move it to the Docker-persistent path: {db_path}")

    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        print(f"[OK] Database exists ({size_kb:.0f} KB)")
    else:
        print("[INFO] No database yet (will be created on first startup)")

    print()
    if errors:
        print(f"[FAIL] {errors} error(s) found. Fix them before starting.")
    else:
        print("[PASS] Configuration looks good.")
    return errors


if __name__ == "__main__":
    sys.exit(main())
