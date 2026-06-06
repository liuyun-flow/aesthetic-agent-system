#!/usr/bin/env python3
"""Check that the .env file is properly configured."""

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"

ENV_FILE = BACKEND_DIR / ".env"
EXAMPLE_FILE = BACKEND_DIR / ".env.example"

def main() -> int:
    errors = 0

    print("=== Environment Check ===\n")

    # Check .env exists
    if not ENV_FILE.exists():
        print(f"[ERROR] {ENV_FILE} not found. Copy {EXAMPLE_FILE} to {ENV_FILE} and edit it.")
        return 1
    print(f"[OK] {ENV_FILE} exists")

    # Load env vars
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

    # Check DeepSeek
    dsk = env.get("DEEPSEEK_API_KEY", "")
    placeholder_keys = {"", "replace-me", "your_deepseek_api_key_here"}
    if dsk in placeholder_keys:
        print("[ERROR] DEEPSEEK_API_KEY is not set. Edit backend/.env and add your DeepSeek API key.")
        errors += 1
    else:
        print(f"[OK] DEEPSEEK_API_KEY configured (starts with {dsk[:8]}...)")

    # Check Vision
    provider = env.get("VISION_PROVIDER", "placeholder")
    print(f"[INFO] VISION_PROVIDER={provider}")
    if provider == "openai":
        oai = env.get("OPENAI_API_KEY", "")
        if oai in placeholder_keys:
            print("[ERROR] VISION_PROVIDER=openai but OPENAI_API_KEY is not set.")
            errors += 1
        else:
            print(f"[OK] OPENAI_API_KEY configured (starts with {oai[:8]}...)")
    elif provider == "placeholder":
        print("[WARN] Using placeholder vision — images will not be analyzed by a real vision model.")

    # Check data dirs
    for subdir in ["database", "uploads"]:
        d = BACKEND_DIR / "data" / subdir
        if d.exists():
            print(f"[OK] data/{subdir}/ exists")
        else:
            print(f"[WARN] data/{subdir}/ does not exist (will be created on startup)")

    # Check database
    db_path = BACKEND_DIR / "data" / "database" / "aesthetic.db"
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
