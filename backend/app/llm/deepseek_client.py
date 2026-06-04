"""DeepSeek API client using OpenAI-compatible pattern."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
REASONING_MODEL = "deepseek-v4-pro"
PLACEHOLDER_API_KEYS = {"your_deepseek_api_key_here"}


def get_deepseek_client(api_key: str | None = None) -> OpenAI:
    """Create an OpenAI-compatible client pointed at DeepSeek API."""
    key = (api_key or os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not key or key in PLACEHOLDER_API_KEYS:
        raise ValueError(
            "DEEPSEEK_API_KEY is not set. "
            "Set it in your .env file or pass it directly."
        )

    base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=key, base_url=base_url)


def get_default_model() -> str:
    return os.getenv("DEEPSEEK_DEFAULT_MODEL", DEFAULT_MODEL)


def get_reasoning_model() -> str:
    return os.getenv("DEEPSEEK_REASONING_MODEL", REASONING_MODEL)
