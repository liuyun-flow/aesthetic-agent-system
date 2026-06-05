"""Prompt Generator agent — produces copyable prompts for image generation tools."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import GeneratedPrompt


PROMPT_GEN_SYSTEM = (
    "You are a design-to-prompt translator. Given design analysis results, "
    "you generate copyable prompts for image generation tools (Midjourney, "
    "DALL-E, Stable Diffusion, Chinese design agents) and for human designers.\n\n"
    "Always respond with valid JSON only — no markdown, no extra text."
)

PROMPT_GEN_USER = """Generate copyable prompts based on the following context.

Work description:
{work_description}

Image description:
{image_description}

User self-assessment:
{user_judgment}

AI critique result:
{critique_result}

Iteration directions:
{iterate_result}

Selected direction:
{selected_direction}

Reference comparison:
{reference_comparison}

Target tool: {target_tool}

Return a JSON object with exactly these keys:
- chinese_prompt: string — suitable for Chinese design agents / image tools. Include specific style, color, composition, material, mood details. Keep under 300 chars if possible but be specific.
- english_prompt: string — suitable for Midjourney / DALL-E / Stable Diffusion. Include style keywords, lighting, composition, aspect ratio hints.
- negative_prompt: string — what to AVOID: cheap clipart, excessive promotions, font chaos, low-quality textures, cluttered layout, neon overload, etc. Be specific based on the actual work's weaknesses.
- design_notes: array of strings — 3-5 actionable notes for a human designer, based on the critique and iteration analysis
- copywriting_prompt: string — if the design includes titles/taglines, suggest copy direction. If none, return empty string.
- usage_tips: array of strings — 2-3 tips on how to use these prompts effectively

Be specific, actionable, and grounded in the provided context."""  # noqa: E501


def _parse_json_response(raw: str) -> dict[str, Any]:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class PromptGeneratorAgent:
    """Generates copyable design prompts from analysis results."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(
        self,
        work_description: str,
        image_description: str | None = None,
        user_judgment: dict[str, Any] | None = None,
        critique_result: dict[str, Any] | None = None,
        iterate_result: dict[str, Any] | None = None,
        selected_direction: str | None = None,
        reference_comparison: dict[str, Any] | None = None,
        target_tool: str = "general",
    ) -> GeneratedPrompt:
        messages = [
            {"role": "system", "content": PROMPT_GEN_SYSTEM},
            {
                "role": "user",
                "content": PROMPT_GEN_USER.format(
                    work_description=work_description,
                    image_description=image_description or "not provided",
                    user_judgment=json.dumps(user_judgment, ensure_ascii=False, indent=2) if user_judgment else "not provided",
                    critique_result=json.dumps(critique_result, ensure_ascii=False, indent=2) if critique_result else "not provided",
                    iterate_result=json.dumps(iterate_result, ensure_ascii=False, indent=2) if iterate_result else "not provided",
                    selected_direction=selected_direction or "not specified",
                    reference_comparison=json.dumps(reference_comparison, ensure_ascii=False, indent=2) if reference_comparison else "not provided",
                    target_tool=target_tool,
                ),
            },
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)
        return GeneratedPrompt.model_validate(data)
