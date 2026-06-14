"""V2.0.1: Training effectiveness assessment — rule-based analytics over TrainingRecords.

No LLM calls. All computations are deterministic and work on any historical data.

Key design notes:
- Score gap trend: diff = avg_gap_last_7 - avg_gap_prev_7.  diff < -3 => improving,
  diff > +3 => worsening, otherwise stable.  Threshold of ±3 chosen because a
  typical score gap is 5-30 points; a ±3 shift represents a meaningful change.
- Dimension trend: delta = recent_problem_rate - overall_problem_rate.
  delta > +0.05 => worsening (more problems recently), delta < -0.05 => improving.
  The ±5 pp threshold avoids flagging noise as trend changes.
- Insufficient data: fewer than 5 sessions with both user_score AND ai_score.
"""

import json
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import TrainingRecord

# ── Constants ──────────────────────────────────────────────────────────

INSUFFICIENT_DATA_THRESHOLD = 5
MAX_RECORDS = 3000

# 7 aesthetic judgment dimensions
DIMENSIONS = [
    {
        "key": "typography_judgment",
        "name": "字体判断",
        "keywords": ["字体", "排版", "typography", "字重", "字号", "行距", "字距"],
        "score_label": "对字体选择、字重层次、排版节奏的判断准确度",
    },
    {
        "key": "color_judgment",
        "name": "色彩判断",
        "keywords": ["色彩", "颜色", "配色", "color", "色调", "饱和度"],
        "score_label": "对色彩搭配、对比度、品牌色使用的判断准确度",
    },
    {
        "key": "composition_judgment",
        "name": "构图与留白",
        "keywords": ["构图", "留白", "布局", "composition", "空间", "间距", "负空间"],
        "score_label": "对信息布局、空间分配、视觉层级的判断准确度",
    },
    {
        "key": "texture_material_judgment",
        "name": "材质与质感",
        "keywords": ["材质", "质感", "阴影", "material", "纹理", "深度", "立体"],
        "score_label": "对材质表达、光影质感、层次深度的判断准确度",
    },
    {
        "key": "price_band_judgment",
        "name": "价格感判断",
        "keywords": ["价格", "档次", "price", "高端", "廉价", "定位", "溢价"],
        "score_label": "对作品价格档次、市场定位的判断准确度",
    },
    {
        "key": "commercial_fit_judgment",
        "name": "商业适配判断",
        "keywords": ["商业", "转化", "commercial", "转化率", "点击率", "留存", "场景适配"],
        "score_label": "对作品商业场景适配、转化效果的判断准确度",
    },
    {
        "key": "iteration_judgment",
        "name": "迭代方向判断",
        "keywords": ["迭代", "方向", "改进", "迭代方向", "优化方向", "下一步"],
        "score_label": "对设计改进方向的判断准确性",
    },
]

# Mistake pattern rules: (type, keywords, severity, explanation, suggestion)
MISTAKE_RULES = [
    {
        "type": "高估高级感",
        "keywords": ["高级感", "premium", "精致", "品质"],
        "severity": "medium",
        "explanation": "你倾向于给作品打较高分，但 AI 认为在细节执行上还有差距。",
        "suggestion": "练习拆解「高级感」的具体来源：是字体、间距、材质还是配色？",
    },
    {
        "type": "低估字体问题",
        "keywords": ["字体", "typography", "排版", "字重", "字号"],
        "severity": "high",
        "explanation": "字体层次、字重对比、行距等问题反复出现但未被你注意到。",
        "suggestion": "每次训练时专门评估字体：有几级层次？字重对比够吗？行距舒适吗？",
    },
    {
        "type": "忽略信息层级",
        "keywords": ["层级", "层次", "hierarchy", "主次", "信息"],
        "severity": "high",
        "explanation": "你对页面信息层级不够敏感，AI 多次指出主次信息区分不足。",
        "suggestion": "训练时先问：用户第一眼看到什么？第二眼呢？信息路径清晰吗？",
    },
    {
        "type": "忽略目标用户",
        "keywords": ["用户", "受众", "audience", "目标人群", "画像"],
        "severity": "medium",
        "explanation": "你较少从目标用户视角评估，更多从个人偏好出发。",
        "suggestion": "每次评估先定义目标用户画像，再从他们的视角判断好坏。",
    },
    {
        "type": "忽略价格带",
        "keywords": ["价格", "档次", "price", "定位", "溢价"],
        "severity": "medium",
        "explanation": "你较少从价格定位角度评估作品，但这是商业设计的关键维度。",
        "suggestion": "问自己：这个作品卖多少钱？目标受众愿意为这个设计付溢价吗？",
    },
    {
        "type": "过度关注颜色",
        "keywords": ["颜色", "色彩", "配色", "color"],
        "severity": "low",
        "explanation": "你的判断过度集中于颜色维度，可能忽略了构图、字体、商业等维度。",
        "suggestion": "有意识地在自评时先排除颜色，先评构图和字体，最后再看颜色。",
    },
    {
        "type": "忽略构图与留白",
        "keywords": ["构图", "留白", "布局", "空间", "composition"],
        "severity": "medium",
        "explanation": "你对空间分配和留白质量不够关注，但这是区分中高级设计的关键。",
        "suggestion": "数一数：页面有几个视觉块？块之间距离一致吗？有足够的呼吸空间吗？",
    },
    {
        "type": "忽略商业转化",
        "keywords": ["商业", "转化", "commercial", "效率", "点击", "转化率"],
        "severity": "medium",
        "explanation": "你较少评估设计对商业目标的贡献（转化、点击、留存）。",
        "suggestion": "为每个作品定义一个核心商业目标，然后判断设计是否支持这个目标。",
    },
    {
        "type": "迭代方向选择不稳定",
        "keywords": [],
        "severity": "medium",
        "explanation": "你的迭代方向选择可能不够聚焦，在不同训练中方向变化较大。",
        "suggestion": "连续 3 次训练选择同一个迭代方向，直到明显改善后再切换。",
    },
    {
        "type": "描述过于抽象",
        "keywords": [],
        "severity": "low",
        "explanation": "你的作品描述或自评较抽象，缺少具体可执行的判断语言。",
        "suggestion": "使用「因为…所以…」句式，给出具体证据支撑每个判断。",
    },
]


# ── Helpers ─────────────────────────────────────────────────────────────

def _text_matches(text: str | None, keywords: list[str]) -> bool:
    """Return True if *text* contains any of *keywords* (case-insensitive)."""
    if not text:
        return False
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def _count_keyword_hits(text: str | None, keywords: list[str]) -> int:
    """Count how many keywords appear in *text*."""
    if not text:
        return 0
    lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in lower)


def _collect_searchable_text(record: TrainingRecord) -> str:
    """Concatenate all searchable text fields from a training record."""
    parts: list[str] = []
    for field in (
        "judgment_gap_summary", "training_focus_tags", "user_weaknesses",
        "user_priority_fixes", "ai_main_problems", "ai_priority_fixes",
        "training_theme", "user_lesson", "next_focus",
    ):
        val = getattr(record, field, None)
        if val:
            parts.append(str(val))
    return " ".join(parts)


def _has_sufficient_data(records: list[TrainingRecord]) -> bool:
    """At least INSUFFICIENT_DATA_THRESHOLD records with both scores."""
    scored = [r for r in records if r.user_score is not None and r.ai_score is not None]
    return len(scored) >= INSUFFICIENT_DATA_THRESHOLD


def _records_with_scores(records: list[TrainingRecord]) -> list[TrainingRecord]:
    return [r for r in records if r.user_score is not None and r.ai_score is not None]


# ── Overview ────────────────────────────────────────────────────────────

def compute_overview(db: Session) -> dict[str, Any]:
    """Return a training effectiveness overview."""
    from app.services.session_service import get_all_records

    all_records = get_all_records(db, limit=MAX_RECORDS)
    total = len(all_records)
    completed = sum(1 for r in all_records if r.completed == 1)

    today = date.today()
    last_7 = today - timedelta(days=7)
    last_30 = today - timedelta(days=30)
    before_7 = today - timedelta(days=14)

    records_7 = [r for r in all_records if r.created_at and r.created_at.date() >= last_7]
    records_30 = [r for r in all_records if r.created_at and r.created_at.date() >= last_30]
    records_prev_7 = [
        r for r in all_records
        if r.created_at and before_7 <= r.created_at.date() < last_7
    ]

    scored = _records_with_scores(all_records)
    scored_7 = _records_with_scores(records_7)
    scored_30 = _records_with_scores(records_30)
    scored_prev_7 = _records_with_scores(records_prev_7)

    def _avg_gap(recs: list[TrainingRecord]) -> float | None:
        if not recs:
            return None
        gaps = [abs((r.user_score or 0) - (r.ai_score or 0)) for r in recs]
        return round(sum(gaps) / len(gaps), 1)

    def _avg(recs: list[TrainingRecord], attr: str) -> float | None:
        vals = [getattr(r, attr) for r in recs if getattr(r, attr) is not None]
        if not vals:
            return None
        return round(sum(vals) / len(vals), 1)

    avg_gap_all = _avg_gap(scored)
    avg_gap_7 = _avg_gap(scored_7)
    avg_gap_30 = _avg_gap(scored_30)
    avg_gap_prev_7 = _avg_gap(scored_prev_7)

    # Trend: compare last 7 days gap vs previous 7 days gap
    if not _has_sufficient_data(all_records):
        trend = "insufficient_data"
    elif avg_gap_7 is not None and avg_gap_prev_7 is not None:
        diff = avg_gap_7 - avg_gap_prev_7
        if diff < -3:
            trend = "improving"
        elif diff > 3:
            trend = "worsening"
        else:
            trend = "stable"
    else:
        trend = "stable"

    if not _has_sufficient_data(all_records):
        summary = "训练数据不足，建议先完成至少 5 次训练（包含自评和 AI 评分），再回来查看评估结果。"
        next_focus: list[str] = []
    elif trend == "improving":
        summary = "你的判断准确度在逐步提升！继续保持当前的训练节奏，重点关注接下来的维度建议。"
        next_focus = ["继续当前频率训练", "挑战更高难度的案例"]
    elif trend == "worsening":
        summary = "你的判断差距在扩大，可能训练量减少或题材变化导致的。建议回顾历史强项，回到熟悉的领域巩固基础。"
        next_focus = ["增加训练频率", "回顾早期成功案例", "降低难度，从明确的高低案例对比开始"]
    else:
        summary = "你的判断差距保持稳定。进入高原期是正常的，建议通过针对性训练突破。"
        next_focus = ["针对性训练弱点维度", "增加案例库中高/低对比案例"]

    return {
        "total_sessions": total,
        "valid_scored_sessions": len(scored),
        "completed_sessions": completed,
        "sessions_last_7_days": len(records_7),
        "sessions_last_30_days": len(records_30),
        "average_user_score": _avg(scored, "user_score"),
        "average_ai_score": _avg(scored, "ai_score"),
        "average_score_gap": avg_gap_all,
        "average_score_gap_last_7": avg_gap_7,
        "average_score_gap_last_30": avg_gap_30,
        "score_gap_trend": trend,
        "summary": summary,
        "next_focus": next_focus,
    }


# ── Mistake Patterns ────────────────────────────────────────────────────

def compute_mistake_patterns(db: Session) -> list[dict[str, Any]]:
    """Analyze training records for common mistake patterns using keyword rules."""
    from app.services.session_service import get_all_records

    all_records = get_all_records(db, limit=MAX_RECORDS)
    if not _has_sufficient_data(all_records):
        return []

    results: list[dict[str, Any]] = []
    evidence_map: dict[int, list[int]] = {}  # rule_index -> [session_ids]

    # Check each rule against all records
    for idx, rule in enumerate(MISTAKE_RULES):
        evidence_map[idx] = []
        for r in all_records:
            text = _collect_searchable_text(r)

            if rule["keywords"]:
                if _text_matches(text, rule["keywords"]):
                    evidence_map[idx].append(r.id or 0)
            else:
                # Special rules without keywords
                if rule["type"] == "迭代方向选择不稳定":
                    # Check if selected_direction varies a lot across sessions
                    pass  # Handle below
                elif rule["type"] == "描述过于抽象":
                    wd = r.work_description or ""
                    if len(wd) < 30:
                        evidence_map[idx].append(r.id or 0)

    # Special: iteration instability
    iterate_records = [r for r in all_records if r.record_type == "iterate" and r.selected_direction]
    if len(iterate_records) >= 3:
        dirs = set()
        for r in iterate_records:
            try:
                d = json.loads(r.selected_direction or "{}")
                if isinstance(d, dict):
                    dirs.add(d.get("id", "") or d.get("title", ""))
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        # If more than 3 different directions in <10 iterate sessions, flag as unstable
        if len(dirs) >= 3 and len(iterate_records) <= 10:
            unstable_idx = None
            for i, rule in enumerate(MISTAKE_RULES):
                if rule["type"] == "迭代方向选择不稳定":
                    unstable_idx = i
                    break
            if unstable_idx is not None:
                evidence_map[unstable_idx] = [r.id or 0 for r in iterate_records if r.id]

    # Special: description too abstract
    abstract_idx = None
    for i, rule in enumerate(MISTAKE_RULES):
        if rule["type"] == "描述过于抽象":
            abstract_idx = i
            break
    if abstract_idx is not None:
        abstract_records = [r for r in all_records if r.work_description and len(r.work_description.strip()) < 30]
        if abstract_records:
            evidence_map[abstract_idx] = [r.id or 0 for r in abstract_records]

    # Build result
    for idx, rule in enumerate(MISTAKE_RULES):
        evidence = evidence_map.get(idx, [])
        if not evidence:
            continue
        results.append({
            "mistake_type": rule["type"],
            "count": len(evidence),
            "severity": rule["severity"],
            "evidence_sessions": evidence[:5],  # top 5
            "explanation": rule["explanation"],
            "training_suggestion": rule["suggestion"],
        })

    # Sort by count descending, then by severity
    sev_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: (-x["count"], sev_order.get(x["severity"], 2)))

    return results[:10]


# ── Dimension Assessment ────────────────────────────────────────────────

# V2.4: work-quality dimensions, aggregated from stored critic scores
# (critic 6 dims + 2 commercial dims). Replaces keyword-frequency guessing
# when real per-dimension scores exist on records.
WORK_DIMENSIONS = [
    {"key": "color", "name": "色彩"},
    {"key": "composition", "name": "构图与留白"},
    {"key": "typography", "name": "字体"},
    {"key": "material", "name": "材质与质感"},
    {"key": "emotion", "name": "情绪表达"},
    {"key": "brand_sense", "name": "品牌感"},
    {"key": "price_perception", "name": "价格感"},
    {"key": "commercial_fit", "name": "商业适配"},
]

MIN_DIM_SAMPLES = 3  # per-dimension scores required before we report a dimension


def _parse_dim_scores(record: TrainingRecord) -> dict[str, Any]:
    """Return a record's stored ai_dimension_scores dict, or {} if absent."""
    raw = getattr(record, "ai_dimension_scores", None)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):  # tolerate JSON-as-text
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def compute_dimension_scores(db: Session) -> list[dict[str, Any]]:
    """Per-dimension assessment.

    V2.4: when stored AI dimension scores exist (critique records since V2.4),
    aggregate those *real* scores. Otherwise fall back to the legacy keyword
    heuristic so older data and no-key installs keep working unchanged.
    """
    from app.services.session_service import get_all_records

    all_records = get_all_records(db, limit=MAX_RECORDS)
    dim_records = [r for r in all_records if _parse_dim_scores(r)]
    if dim_records:
        return _aggregate_dimension_scores(dim_records)
    return _keyword_dimension_scores(db)


def _aggregate_dimension_scores(dim_records: list[TrainingRecord]) -> list[dict[str, Any]]:
    """Aggregate stored 0-100 AI dimension scores into per-dimension assessments."""
    today = date.today()
    last_7 = today - timedelta(days=7)

    results: list[dict[str, Any]] = []
    for dim in WORK_DIMENSIONS:
        vals: list[float] = []
        recent: list[float] = []
        for r in dim_records:
            v = _parse_dim_scores(r).get(dim["key"])
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            vals.append(fv)
            if r.created_at and r.created_at.date() >= last_7:
                recent.append(fv)

        if len(vals) < MIN_DIM_SAMPLES:
            results.append({
                "dimension_key": dim["key"],
                "dimension_name": dim["name"],
                "score": 50,
                "level": "medium",
                "trend": "insufficient_data",
                "evidence": f"「{dim['name']}」暂无足够评分数据（需至少 {MIN_DIM_SAMPLES} 次评分训练）。",
                "suggestion": "多做几次「评分」(critique) 训练以积累该维度数据。",
            })
            continue

        score = max(0, min(100, round(sum(vals) / len(vals))))
        level = "strong" if score >= 70 else "medium" if score >= 45 else "weak"

        if len(recent) >= 2:
            delta = (sum(recent) / len(recent)) - (sum(vals) / len(vals))
            trend = "improving" if delta > 5 else "worsening" if delta < -5 else "stable"
        else:
            trend = "stable"

        evidence = f"基于 {len(vals)} 次评分，「{dim['name']}」作品平均得分 {score}/100。"
        if level == "weak":
            suggestion = f"「{dim['name']}」是当前最弱维度，建议作为近期重点训练方向。"
        elif level == "medium":
            suggestion = f"「{dim['name']}」处于中等水平，针对性练习可提升到优秀。"
        else:
            suggestion = f"「{dim['name']}」是强项，保持并在训练中验证巩固。"

        results.append({
            "dimension_key": dim["key"],
            "dimension_name": dim["name"],
            "score": score,
            "level": level,
            "trend": trend,
            "evidence": evidence,
            "suggestion": suggestion,
        })
    return results


def _keyword_dimension_scores(db: Session) -> list[dict[str, Any]]:
    """Legacy keyword-frequency dimension scoring (V2.0).

    Fallback used when no stored AI dimension scores exist (older data,
    no-key installs). Kept intact so existing behavior is unchanged.
    """
    from app.services.session_service import get_all_records

    all_records = get_all_records(db, limit=MAX_RECORDS)
    if not _has_sufficient_data(all_records):
        return [
            {
                "dimension_key": d["key"],
                "dimension_name": d["name"],
                "score": 50,
                "level": "medium",
                "trend": "insufficient_data",
                "evidence": "训练数据不足，建议完成至少 5 次带评分的训练。",
                "suggestion": "先完成基础训练，系统将自动评估各项审美能力。",
            }
            for d in DIMENSIONS
        ]

    results: list[dict[str, Any]] = []
    scored = _records_with_scores(all_records)

    today = date.today()
    last_7 = today - timedelta(days=7)
    scored_7 = [r for r in scored if r.created_at and r.created_at.date() >= last_7]

    for dim in DIMENSIONS:
        # Count how often this dimension appears as a problem in focus tags / problems
        problem_count = 0
        total_checks = 0
        recent_problem_count = 0
        recent_checks = 0

        for r in scored:
            text = _collect_searchable_text(r)
            total_checks += 1
            hits = _count_keyword_hits(text, dim["keywords"])
            if hits > 0:
                problem_count += 1

        for r in scored_7:
            text = _collect_searchable_text(r)
            recent_checks += 1
            hits = _count_keyword_hits(text, dim["keywords"])
            if hits > 0:
                recent_problem_count += 1

        # Score: fewer problems = higher score
        # Base starting point: no problems → 100; every record has problem → 30
        if total_checks > 0:
            problem_rate = problem_count / total_checks
            # Scale: 0% problems = 100, 100% problems = 30
            score = max(30, min(100, round(100 - problem_rate * 70)))
        else:
            score = 50

        # Level
        if score >= 70:
            level = "strong"
        elif score >= 45:
            level = "medium"
        else:
            level = "weak"

        # Trend
        if not _has_sufficient_data(all_records):
            trend = "insufficient_data"
        elif recent_checks > 0 and total_checks > 0:
            recent_rate = recent_problem_count / recent_checks if recent_checks > 0 else 0
            overall_rate = problem_count / total_checks
            delta = recent_rate - overall_rate
            if delta > 0.05:
                trend = "worsening"
            elif delta < -0.05:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Evidence
        if problem_count == 0:
            evidence = f"在所有 {total_checks} 次训练中未发现「{dim['name']}」相关问题。"
        else:
            evidence = f"在 {problem_count}/{total_checks} 次训练中出现了「{dim['name']}」相关误判。"

        # Suggestion
        if level == "weak":
            suggestion = f"「{dim['name']}」是你的薄弱维度，建议作为近期重点训练方向。{dim['score_label']}"
        elif level == "medium":
            suggestion = f"「{dim['name']}」处于中等水平，继续有针对性的练习可以提升到优秀。"
        else:
            suggestion = f"「{dim['name']}」是你的强项，保持当前水平即可。可以在训练中有意识地验证和巩固。"

        results.append({
            "dimension_key": dim["key"],
            "dimension_name": dim["name"],
            "score": score,
            "level": level,
            "trend": trend,
            "evidence": evidence,
            "suggestion": suggestion,
        })

    return results


# ── Report ──────────────────────────────────────────────────────────────

def compute_report(db: Session, days: int = 7) -> dict[str, Any]:
    """Generate a period review report."""
    overview = compute_overview(db)
    mistakes = compute_mistake_patterns(db)
    dimensions = compute_dimension_scores(db)

    from app.services.session_service import get_all_records

    all_records = get_all_records(db, limit=MAX_RECORDS)
    cutoff = date.today() - timedelta(days=days)
    period_records = [r for r in all_records if r.created_at and r.created_at.date() >= cutoff]
    period_scored = _records_with_scores(period_records)

    gap_vals = [abs((r.user_score or 0) - (r.ai_score or 0)) for r in period_scored]
    avg_gap = round(sum(gap_vals) / len(gap_vals), 1) if gap_vals else None

    # Sort dimensions by score
    sorted_dims = sorted(dimensions, key=lambda d: d["score"])
    weakest = sorted_dims[:3]
    strongest = sorted_dims[-3:][::-1]

    # Generate progress summary
    if len(period_scored) < INSUFFICIENT_DATA_THRESHOLD:
        progress = f"最近 {days} 天内训练数据不足（仅 {len(period_scored)} 次有效训练），无法生成可靠的进度评估。建议增加训练频率。"
    elif overview["score_gap_trend"] == "improving":
        progress = f"最近 {days} 天你的判断准确度在提升，平均判断差距为 {avg_gap} 分。继续保持当前训练节奏。"
    elif overview["score_gap_trend"] == "worsening":
        progress = f"最近 {days} 天你的判断差距有所扩大（平均 {avg_gap} 分），建议回顾早期训练记录，重点关注下文建议的薄弱维度。"
    else:
        progress = f"最近 {days} 天你的判断水平保持稳定（平均差距 {avg_gap} 分）。进入高原期后，建议通过针对性训练突破。"

    # Training plan: based on weakest dimensions + top mistakes
    plan: list[str] = []
    for d in weakest:
        plan.append(f"重点训练「{d['dimension_name']}」：{d['suggestion']}")
    for m in mistakes[:3]:
        plan.append(f"注意纠正「{m['mistake_type']}」：{m['training_suggestion']}")

    # Recommended themes: based on weakest dimensions
    theme_map = {
        "typography_judgment": "字体与排版专项训练",
        "color_judgment": "色彩搭配与品牌色专项",
        "composition_judgment": "构图与留白精练",
        "texture_material_judgment": "材质质感表达训练",
        "price_band_judgment": "价格感与市场定位判断",
        "commercial_fit_judgment": "商业转化与用户体验训练",
        "iteration_judgment": "迭代方向选择训练",
    }
    themes = [theme_map.get(d["dimension_key"], d["dimension_name"]) for d in weakest[:3]]

    return {
        "period_days": days,
        "training_count": len(period_records),
        "score_gap_summary": (
            f"近 {days} 天平均判断差距："
            f"{avg_gap} 分（{overview['score_gap_trend']}）"
            if avg_gap is not None
            else f"近 {days} 天无有效评分数据"
        ),
        "top_mistakes": mistakes[:5],
        "strongest_dimensions": strongest,
        "weakest_dimensions": weakest,
        "progress_summary": progress,
        "next_training_plan": plan[:5],
        "recommended_themes": themes,
    }
