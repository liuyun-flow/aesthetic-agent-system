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
- dimensions: object with number scores for each key: color, composition, typography, material, emotion, brand_sense
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
