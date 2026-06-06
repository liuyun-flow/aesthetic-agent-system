"""Weekly Review agent — summarizes a week of aesthetic training."""

import json
import re
from typing import Any

from openai import OpenAI

from app.schemas.responses import WeeklyReviewResponse


WEEKLY_SYSTEM_PROMPT = (
    "你是一位资深设计教练。请基于用户过去一周的审美训练记录，"
    "生成一份具体的每周复盘报告。必须使用简体中文。"
    "始终只返回合法 JSON，不要加 markdown，不要加额外文字。"
)

WEEKLY_USER_PROMPT = """请根据以下训练记录，生成每周复盘。

本周训练记录（JSON 数组）：
{history_json}

返回一个 JSON 对象，包含以下字段（全部使用简体中文）：

- summary: 字符串 — 2-3 句话总结本周训练情况
- common_misjudgments: 字符串 — 用户反复误判的问题是什么？例如：用户总是高估自己的色彩搭配，或总是忽略字体层级。必须具体，不能泛泛而谈。
- progress_points: 字符串 — 用户本周进步的地方是什么？即使只有一点点，也要指出来。
- recurring_issues: 字符串 — 反复出现的问题是什么？例如：连续 3 次都没注意到留白不足，或每次都只关注表面美感而忽略商业适配。
- next_week_theme: 字符串 — 建议下周训练的 1 个主题，从以下选择：字体与排版、色彩与高级感、构图与留白、材质与质感、价格带判断、商业适配与目标用户
- next_week_tasks: 字符串数组 — 5 个具体的、可执行的下周训练任务。每个任务应该明确、单一、可衡量。

规则：
- 必须诚实、直接、具体
- 不要空泛鼓励
- 必须指出用户反复误判的问题
- 如果训练记录不足（少于 3 条），请在 summary 中说明数据不足，但仍然给出 next_week_tasks 建议
- 所有输出使用简体中文"""  # noqa: E501


def _parse_json_response(raw: str) -> dict[str, Any]:
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return json.loads(raw)


class WeeklyReviewAgent:
    """Generates a weekly training review from recent session history."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self.client = client
        self.model = model

    def run(self, history: list[dict[str, Any]]) -> WeeklyReviewResponse:
        if len(history) < 3:
            return WeeklyReviewResponse(
                summary="本周训练记录不足（少于 3 条），无法生成完整的复盘报告。请完成至少 3 次训练后再来查看。",
                common_misjudgments="数据不足，暂无分析。",
                progress_points="数据不足，暂无分析。",
                recurring_issues="数据不足，暂无分析。",
                next_week_theme="色彩与高级感",
                next_week_tasks=[
                    "上传一个作品并先自评色彩",
                    "指出你认为最影响高级感的颜色问题",
                    "和一个 high 案例对比色彩运用",
                    "生成修改提示词",
                    "记录今天学到的一条色彩规则",
                ],
            )

        history_json = json.dumps(history, ensure_ascii=False, indent=2, default=str)

        messages = [
            {"role": "system", "content": WEEKLY_SYSTEM_PROMPT},
            {"role": "user", "content": WEEKLY_USER_PROMPT.format(history_json=history_json)},
        ]

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
        )

        raw = completion.choices[0].message.content or ""
        data = _parse_json_response(raw)
        return WeeklyReviewResponse.model_validate(data)
