"""Critic agent — scores a work across aesthetic dimensions."""

import json
import re
from typing import Any

from openai import OpenAI

from app.agents.design_knowledge import (
    DESIGN_KNOWLEDGE,
    EVIDENCE_RULES,
    SCORING_RUBRIC,
)
from app.schemas.responses import CritiqueResponse


CRITIC_SYSTEM_PROMPT = (
    "You are a strict design critic trained on the knowledge base below. "
    "Your scores follow the calibrated rubric exactly — a 7 from you means "
    "professional grade, not \"pretty good\". Inflated scores destroy the "
    "trainee's calibration.\n\n"
    f"{DESIGN_KNOWLEDGE}\n"
    f"{SCORING_RUBRIC}\n"
    f"{EVIDENCE_RULES}\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

CRITIC_USER_PROMPT_TEMPLATE = """Critique the following visual work description.
First infer the work's commercial intent, then score each dimension 1-10 using the
rubric anchors: start from the 5-6 band and move only on cited evidence.

Work description:
{work_description}
{image_block}
Return a JSON object with exactly these keys:
- total_score: number (1-10; NOT a plain average — fatal issues in hierarchy or
  readability drag the total toward the weakest dimension)
- dimensions: object with number scores (1-10) for each key: color, composition, typography, material, emotion, brand_sense, price_perception (价格感：视觉传达的价格档次与意图是否匹配), commercial_fit (商业适配：是否服务于商业目标/转化/目标受众)
- main_issues: array of strings (top 3-5 problems; each names the element, the violated
  principle, and the consequence)
- cheapness_sources: array of strings (specific cheapness signifiers present in this work)
- priority_fixes: array of strings (ordered by impact; each one concrete enough to act on today)

Rules:
- Each score must be between 1 and 10. Apply the anti-inflation rules strictly.
- If the description lacks information for a dimension, score it conservatively (≤5)
  and add a main_issue naming the missing information. Never invent details.
- Write all string values IN CHINESE (中文)."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class CriticAgent:
    """Produces a scored critique with identified issues and priority fixes."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> CritiqueResponse:
        image_block = ""
        if image_description:
            image_block = f"\nAttached image description:\n{image_description}\n"

        messages = [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": CRITIC_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description,
                    image_block=image_block,
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)

        return CritiqueResponse.model_validate(data)


class VisionCriticAgent:
    """V2.4 (optional): critic that scores the image *directly* via a multimodal
    model, bypassing the image→text bottleneck.

    Used only when SCORING_VISION_DIRECT is enabled and a vision key is set.
    Reuses the same system prompt + rubric as the text critic so scores stay
    comparable. The caller is responsible for falling back to the text critic
    on any failure.
    """

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        key = (api_key or "").strip()
        if not key:
            raise ValueError("Vision-direct scoring requires an OpenAI vision key.")
        self.client = OpenAI(api_key=key)
        self.model = model or "gpt-4o-mini"

    def run(self, work_description: str, image_path: str) -> CritiqueResponse:
        from app.vision.openai_adapter import _encode_image

        data_uri = _encode_image(image_path)
        user_text = CRITIC_USER_PROMPT_TEMPLATE.format(
            work_description=work_description,
            image_block="\n（请直接观察所附图片进行评分，不要只依赖文字描述。）\n",
        )
        messages = [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
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

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)
        return CritiqueResponse.model_validate(data)
