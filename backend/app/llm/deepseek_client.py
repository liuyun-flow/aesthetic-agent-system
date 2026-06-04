"""DeepSeek API client using OpenAI-compatible pattern."""

import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEFAULT_MODEL = os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-v4-flash")
REASONING_MODEL = os.getenv("DEEPSEEK_REASONING_MODEL", "deepseek-v4-pro")


def get_deepseek_client(api_key: Optional[str] = None) -> OpenAI:
    """Create an OpenAI-compatible client pointed at DeepSeek API."""
    key = api_key or DEEPSEEK_API_KEY
    if not key:
        raise ValueError(
            "DEEPSEEK_API_KEY is not set. "
            "Set it in your .env file or pass it directly."
        )
    return OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL)


def get_default_model() -> str:
    return DEFAULT_MODEL


def get_reasoning_model() -> str:
    return REASONING_MODEL
