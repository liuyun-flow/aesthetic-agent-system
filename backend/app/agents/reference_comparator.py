"""Reference Comparator agent — compares user work against curated reference cases."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import CompareWithReferencesResponse


COMPARATOR_SYSTEM_PROMPT = (
    "You are a senior design educator who compares student work against "
    "a curated reference library. Your job is to be specific, honest, and "
    "actionable — never vague. Point to concrete differences in typography, "
    "color, composition, spacing, material feel, commercial positioning, "
    "and audience fit.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

COMPARATOR_USER_PROMPT_TEMPLATE = """Compare the user's work against the provided reference cases.

User's work description:
{user_work_description}

User's image description:
{image_description}

User's self-assessment:
{user_judgment}

Reference cases for comparison:
{reference_cases_json}

Based on this comparison, return a JSON object with exactly these keys:

- overall_level_estimate: string — "high", "medium", or "low". Where does the user's work most likely sit?
- closest_reference_level: string — which reference level is it closest to?
- stronger_than_low_cases: array of strings — what does the user's work do better than the low references? Be specific.
- weaker_than_high_cases: array of strings — what specific gaps exist vs. high references? Point to concrete differences: fonts, colors, spacing, material feel, commercial fit, etc.
- key_gaps: array of strings — the 3-5 most important gaps the user should address
- priority_fixes: array of strings — if the user only fixes 3 things, what should they be? Ordered by impact.
- reference_cases_used: array of integers — the IDs of the reference cases you used
- training_takeaway: string — one encouraging paragraph summarizing what the user learned from this comparison
- next_practice: array of strings — 3-5 specific exercises the user should do next

Rules:
- Be brutally specific. Never say "more premium" — say exactly what makes it premium.
- Ground every gap in the actual reference cases provided.
- If the user's self-assessment is inaccurate, mention it in the gaps.
- If no reference cases are provided, return empty lists with a helpful training_takeaway suggesting they add some reference cases first."""  # noqa: E501


def _parse_json_response(raw: str) -> dict[str, Any]:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class ReferenceComparatorAgent:
    """Compares user work against a curated reference case library."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        user_work_description: str,
        reference_cases: list[dict[str, Any]],
        image_description: str | None = None,
        user_judgment: dict[str, Any] | None = None,
    ) -> CompareWithReferencesResponse:
        """Generate a comparison between user work and reference cases.

        If reference_cases is empty, returns a friendly prompt to add cases.
        """
        if not reference_cases:
            return CompareWithReferencesResponse(
                overall_level_estimate="unknown",
                closest_reference_level="unknown",
                training_takeaway=(
                    "No reference cases are available yet. "
                    "Add some high, medium, and low examples to your reference "
                    "library to enable comparison training."
                ),
                next_practice=["Add 3-5 reference cases with different aesthetic levels."],
            )

        cases_json = json.dumps(reference_cases, ensure_ascii=False, indent=2, default=str)
        judgment_json = json.dumps(user_judgment, ensure_ascii=False, indent=2) if user_judgment else "not provided"

        messages = [
            {"role": "system", "content": COMPARATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": COMPARATOR_USER_PROMPT_TEMPLATE.format(
                    user_work_description=user_work_description,
                    image_description=image_description or "not provided",
                    user_judgment=judgment_json,
                    reference_cases_json=cases_json,
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

        return CompareWithReferencesResponse.model_validate(data)
