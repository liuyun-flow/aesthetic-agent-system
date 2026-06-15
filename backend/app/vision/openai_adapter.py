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

OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")

VISION_SYSTEM_PROMPT = (
    "你是一名专业的视觉分析师。请用简体中文详细描述图片，"
    "聚焦于与设计评审相关的美学品质。"
    "始终只返回合法 JSON，不要加 markdown，不要加额外文字。"
    "所有字段值必须使用简体中文。"
)

VISION_USER_PROMPT = """请分析这张图片，返回一个 JSON 对象，包含以下字段。所有字段值必须使用简体中文。

- summary: 字符串 — 2-3 句话概括图片内容
- colors: 字符串数组 — 主色和辅助色（例如 ["深炭黑", "橙色", "米白色"]）
- composition: 字符串 — 布局、平衡、视觉焦点、负空间运用、视觉层次
- typography: 字符串或 null — 可见的文字内容、字体风格、字重、大小层次。如果没有文字则返回 null。如果有文字，描述字体风格（衬线/无衬线）、粗细、大小层级，以及排版对整体设计的影响
- materials: 字符串数组 — 可见或隐含的材质和纹理（例如 ["颗粒纹理", "磨砂纸", "拉丝金属"]）
- subjects: 字符串数组 — 图片中的主要物体/人物/内容
- background: 字符串或 null — 背景描述
- style_keywords: 字符串数组 — 3-8 个捕捉视觉风格的关键词（例如 ["极简", "企业", "温暖", "北欧"]）
- potential_issues: 字符串数组 — 2-5 个可能让画面显得廉价、业余或审美薄弱的问题（例如 "对比度低", "构图杂乱", "间距不一致"）。请诚实且具体。
- design_category: 字符串或 null — 设计品类推测（例如 "电商主图", "直播封面", "海报", "App 界面", "品牌 logo", "包装"）
- target_audience_guess: 字符串或 null — 根据视觉线索推测的目标人群（例如 "年轻女性", "考研学生", "高端商务人士"）。这是推测，不是事实。
- price_band_guess: 字符串或 null — 根据视觉调性推测的价格带/定位（例如 "平价促销", "中端", "高端轻奢"）。这是推测，不是事实。
- use_case: 字符串或 null — 使用场景推测（例如 "电商详情页", "社交媒体推广", "线下展示"）
- suggested_prompt_text: 字符串 — 一段精炼的中文描述，包含所有关键视觉细节，适合交给 DeepSeek 做进一步的审美分析。包含颜色、构图、材质、风格和氛围。尽量控制在 400 字以内。

请具体、扎实、以设计为导向。说出实际的颜色名称、材质和构图模式。
对于 design_category / target_audience_guess / price_band_guess / use_case，仅根据画面可见线索推测；信息不足时返回 null，不要编造。"""  # noqa: E501


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
        if api_key is not None:
            key = api_key.strip()
        else:
            key = os.getenv("OPENAI_API_KEY", "").strip()
        _placeholder_keys = {"", "replace-me", "your_openai_api_key_here", "replace-with-your-key"}
        if not key or key in _placeholder_keys:
            raise ValueError(
                "未配置 OPENAI_API_KEY，请配置后再使用自动图片描述，或改用手动图片描述。"
            )
        from app.llm.tracked_client import wrap_client
        self.client = wrap_client(OpenAI(api_key=key), provider="openai-vision")
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
