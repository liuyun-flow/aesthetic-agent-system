"""OpenAI Vision adapter — calls GPT-4o to generate structured image descriptions.

Requires ``OPENAI_API_KEY`` in your ``.env`` file.
Set ``VISION_PROVIDER=openai`` to activate.
"""

import base64
import os
from pathlib import Path

from openai import OpenAI

from app.schemas.responses import VisionDescription
from app.vision.base import VisionAdapter

OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

VISION_SYSTEM_PROMPT = (
    "You are a professional visual analyst. Describe the image in detail, "
    "focusing on aesthetic qualities relevant to design critique. "
    "Always respond with valid JSON only — no markdown, no extra text."
)

VISION_USER_PROMPT = """Analyze this image and return a JSON object with exactly these keys:

- summary: string — 2-3 sentence overall description of the image
- colors: array of strings — dominant and accent colors (e.g. ["navy blue", "warm gray", "gold"])
- composition: string — layout, balance, focal points, use of negative space, visual hierarchy
- typography: string or null — any visible text, font styles, hierarchy. Return null if no text is visible. For images with text, describe the font style (serif/sans-serif), weight, size hierarchy, and how typography contributes to or detracts from the overall design.
- materials: array of strings — visible or implied materials and textures (e.g. ["frosted glass", "matte paper", "brushed metal"])
- subjects: array of strings — main objects/people in the image
- background: string or null — description of the background
- style_keywords: array of strings — 3-8 keywords capturing the visual style (e.g. ["minimalist", "corporate", "warm", "Scandinavian"])
- potential_issues: array of strings — 2-5 things that might make this feel cheap, amateur, or aesthetically weak (e.g. "low contrast", "cluttered composition", "inconsistent spacing"). Be honest and specific.
- suggested_prompt_text: string — a concise paragraph that captures all key visual details, suitable for feeding into a design analysis AI. Include colors, composition, materials, style, and mood. Keep under 400 characters if possible.

Be specific, concrete, and design-focused. Name actual colors, materials, and composition patterns."""  # noqa: E501


def _encode_image(image_path: str) -> str:
    """Read an image file and return a base64 data URI."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    suffix = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/png")

    # Check file size — warn if very large
    size = path.stat().st_size
    if size > 20 * 1024 * 1024:  # 20 MB
        raise ValueError(f"Image too large for vision API: {size} bytes (max 20 MB)")

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


class OpenAIVisionAdapter(VisionAdapter):
    """Calls OpenAI GPT-4o to describe images."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
                _placeholder_keys = {"", "your_openai_api_key_here", "replace-with-your-key"}
        if not key or key in _placeholder_keys:
            raise ValueError(
                "未配置 OPENAI_API_KEY，请配置后再使用自动图片描述，或改用手动图片描述。"
            )
        self.client = OpenAI(api_key=key)
        self.model = model or OPENAI_VISION_MODEL

    def describe_image(self, image_path: str, hint: str | None = None) -> str:
        desc = self.describe_image_structured(image_path)
        return desc.suggested_prompt_text

    def describe_image_structured(self, image_path: str) -> VisionDescription:
        data_uri = _encode_image(image_path)

        messages = [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )

        raw = completion.choices[0].message.content or "{}"

        # Parse JSON response (may be wrapped in ```json)
        import json as _json
        import re
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)

        data = _json.loads(raw)
        return VisionDescription.model_validate(data)
