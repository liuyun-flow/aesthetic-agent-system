"""DeepSeek API client using OpenAI-compatible pattern."""

import os

from dotenv import load_dotenv
from openai import OpenAI

from app.settings.config_store import get_value

load_dotenv()

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
REASONING_MODEL = "deepseek-v4-pro"
PLACEHOLDER_API_KEYS = {"", "replace-me", "your_deepseek_api_key_here"}
# Reasoning calls can legitimately take a while, but a hung connection
# must not hang the request forever.
DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_MAX_RETRIES = 1


def _get_timeout() -> float:
    raw = (
        get_value("deepseek", "timeout_seconds", env_var="DEEPSEEK_TIMEOUT_SECONDS")
        or ""
    )
    try:
        value = float(raw)
        return value if value > 0 else DEFAULT_TIMEOUT_SECONDS
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS


def get_deepseek_client(api_key: str | None = None) -> OpenAI:
    """Create an OpenAI-compatible client pointed at DeepSeek API."""
    key = (
        api_key
        or get_value("deepseek", "api_key", env_var="DEEPSEEK_API_KEY")
        or ""
    ).strip()
    if not key or key in PLACEHOLDER_API_KEYS:
        raise ValueError(
            "DEEPSEEK_API_KEY is not set. "
            "Set it in your .env file or pass it directly."
        )

    base_url = (
        get_value("deepseek", "base_url", env_var="DEEPSEEK_BASE_URL")
        or DEFAULT_BASE_URL
    )
    return OpenAI(
        api_key=key,
        base_url=base_url,
        timeout=_get_timeout(),
        max_retries=DEFAULT_MAX_RETRIES,
    )


def get_default_model() -> str:
    return (
        get_value("deepseek", "default_model", env_var="DEEPSEEK_DEFAULT_MODEL")
        or DEFAULT_MODEL
    )


def get_reasoning_model() -> str:
    return (
        get_value("deepseek", "reasoning_model", env_var="DEEPSEEK_REASONING_MODEL")
        or REASONING_MODEL
    )
