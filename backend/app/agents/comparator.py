"""Comparator agent — contrasts user self-assessment against AI evaluation."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import JudgmentGap


COMPARATOR_SYSTEM_PROMPT = (
    "You are a design coach who compares a student's self-assessment "
    "against a professional AI evaluation. Your goal is to help the "
    "student identify blind spots — both aesthetic and commercial — "
    "so they can improve their design judgment.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

COMPARATOR_USER_PROMPT_TEMPLATE = """Compare the user's self-assessment against the AI evaluation.

Work description:
{work_description}

User self-assessment:
- Score (0-100): {user_score}
- Strengths: {user_strengths}
- Weaknesses: {user_weaknesses}
- Priority fixes: {user_priority_fixes}
- Target audience: {user_target_audience}
- Price band: {user_price_band}

AI evaluation:
{ai_evaluation_json}

Return a JSON object with exactly these keys:
- accurate_judgments: list of strings (what the user correctly identified)
- missed_issues: list of strings (problems the AI caught but the user missed)
- misjudgments: list of strings (things the user thought were problems but aren't, or things the user praised that the AI flagged)
- commercial_blind_spots: list of strings (commercial/business aspects the user overlooked — target audience, pricing tier, market fit)
- aesthetic_blind_spots: list of strings (visual/aesthetic aspects the user overlooked — color, composition, typography, material, etc.)
- next_training_focus: list of strings (specific skills/exercises the user should practice next)
- short_summary: string (2-3 sentence summary of the gap, encouraging tone)

Be constructive and specific. Ground every observation in the provided data."""


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from an LLM response that may contain markdown fences."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class ComparatorAgent:
    """Compares user self-assessment against AI evaluation results."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        work_description: str,
        user_judgment: dict[str, Any],
        ai_result: dict[str, Any],
    ) -> JudgmentGap:
        """Generate a judgment gap analysis.

        Args:
            work_description: The original work description.
            user_judgment: Dict with score, strengths, weaknesses, etc.
            ai_result: Dict of the AI evaluation (analyze/critique response).
        """
        user_score = user_judgment.get("score") or "not provided"
        user_strengths = json.dumps(user_judgment.get("strengths") or [])
        user_weaknesses = json.dumps(user_judgment.get("weaknesses") or [])
        user_priority_fixes = json.dumps(user_judgment.get("priority_fixes") or [])
        user_target = user_judgment.get("target_audience") or "not provided"
        user_price = user_judgment.get("price_band") or "not provided"
        ai_json = json.dumps(ai_result, ensure_ascii=False, indent=2)

        messages = [
            {"role": "system", "content": COMPARATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": COMPARATOR_USER_PROMPT_TEMPLATE.format(
                    work_description=work_description,
                    user_score=user_score,
                    user_strengths=user_strengths,
                    user_weaknesses=user_weaknesses,
                    user_priority_fixes=user_priority_fixes,
                    user_target_audience=user_target,
                    user_price_band=user_price,
                    ai_evaluation_json=ai_json,
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)

        return JudgmentGap.model_validate(data)
