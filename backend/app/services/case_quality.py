"""V1.9: Case quality management — completeness scoring, training readiness, audit, duplicate detection."""

import re
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ReferenceCase


# ── Field weight configuration ──────────────────────────────────────────

# Each field contributes a maximum of `weight` points toward the 100-point score.
# A field is "present" if its value is a non-empty, non-placeholder string (or a
# non-None integer for numeric fields).
_FIELD_WEIGHTS: list[tuple[str, int]] = [
    ("image_id", 15),
    ("description", 15),       # image_description OR ai_description
    ("aesthetic_level", 10),
    ("category", 8),
    ("price_band", 8),
    ("style_tags", 8),
    ("target_audience", 8),
    ("premium_sources", 7),
    ("cheapness_sources", 7),
    ("learn_from_this", 7),
    ("avoid_copying", 3),
    ("notes", 2),
    ("score", 2),               # numeric; present if not None
]

# Chinese labels for each field (used in missing-fields lists and audit output)
_FIELD_LABELS: dict[str, str] = {
    "image_id": "案例图片",
    "description": "图片描述",
    "aesthetic_level": "审美等级",
    "category": "品类",
    "price_band": "价格档位",
    "style_tags": "风格标签",
    "target_audience": "目标用户",
    "premium_sources": "高级感来源",
    "cheapness_sources": "廉价感来源",
    "learn_from_this": "值得学习",
    "avoid_copying": "不能误学",
    "notes": "备注",
    "score": "评分",
}

# Fields that are "required" for training readiness (beyond the 75-point threshold)
_TRAINING_REQUIRED_FIELDS = [
    "image_id",
    "description",
    "aesthetic_level",
    "premium_sources",
    "learn_from_this",
]


# ── Helpers ─────────────────────────────────────────────────────────────

def _is_present(value: Any) -> bool:
    """Return True if *value* looks like meaningful user-provided content."""
    if value is None:
        return False
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        # Reject known placeholder values
        if stripped.lower() in {"unknown", "none", "n/a", "-", "—", "暂无", "无"}:
            return False
        return True
    return False


def _has_description(case: ReferenceCase) -> bool:
    """A case has a description when image_description OR ai_description is present."""
    return _is_present(case.image_description) or _is_present(case.ai_description)


# ── Completeness Score ──────────────────────────────────────────────────

def compute_completeness_score(case: ReferenceCase) -> int:
    """Compute a 0-100 completeness score for *case*.

    The score is the sum of weights for each present field.  Fields are
    evaluated from the ORM object — no database round-trip.
    """
    score = 0
    for field_name, weight in _FIELD_WEIGHTS:
        if field_name == "description":
            if _has_description(case):
                score += weight
        elif field_name == "image_id":
            if case.image_id is not None:
                score += weight
        elif field_name == "score":
            if case.score is not None:
                score += weight
        elif field_name == "aesthetic_level":
            val = (case.aesthetic_level or "").strip().lower()
            if val and val != "unknown":
                score += weight
        else:
            val = getattr(case, field_name, None)
            if _is_present(val):
                score += weight
    return score


# ── Training Readiness ──────────────────────────────────────────────────

def is_training_ready(case: ReferenceCase) -> bool:
    """Return True when *case* meets the minimum bar for training use.

    Requirements (all must pass):
    1. completeness_score >= 75
    2. Has an image (image_id is not None)
    3. Has a meaningful aesthetic_level (not unknown / None)
    4. Has an image description or AI description
    5. Has learn_from_this OR premium_sources
    """
    if compute_completeness_score(case) < 75:
        return False
    if case.image_id is None:
        return False
    level = (case.aesthetic_level or "").strip().lower()
    if not level or level == "unknown":
        return False
    if not _has_description(case):
        return False
    if not _is_present(case.learn_from_this) and not _is_present(case.premium_sources):
        return False
    return True


# ── Missing Fields ──────────────────────────────────────────────────────

def get_missing_fields(case: ReferenceCase) -> list[str]:
    """Return a list of Chinese field labels for fields absent from *case*."""
    missing: list[str] = []
    for field_name, _weight in _FIELD_WEIGHTS:
        if field_name == "description":
            if not _has_description(case):
                missing.append(_FIELD_LABELS["description"])
        elif field_name == "image_id":
            if case.image_id is None:
                missing.append(_FIELD_LABELS["image_id"])
        elif field_name == "score":
            if case.score is None:
                missing.append(_FIELD_LABELS["score"])
        elif field_name == "aesthetic_level":
            val = (case.aesthetic_level or "").strip().lower()
            if not val or val == "unknown":
                missing.append(_FIELD_LABELS["aesthetic_level"])
        else:
            val = getattr(case, field_name, None)
            if not _is_present(val):
                missing.append(_FIELD_LABELS.get(field_name, field_name))
    return missing


# ── Duplicate Detection ─────────────────────────────────────────────────

def _tokenize_title(title: str) -> set[str]:
    """Tokenize a title for similarity comparison."""
    # Split on whitespace and common punctuation, lowercase
    tokens = re.split(r"[，,。\s\-—/|、：:（）()「」\[\]{}]+", title.lower())
    # Filter out very short tokens and stopwords
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "of", "in", "on",
        "and", "or", "not", "to", "for", "with", "as", "at", "by", "be",
        "this", "that", "it", "from", "but", "no", "yes", "my", "our",
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "们", "那", "什么", "怎么", "如何", "为什么", "哪", "吗", "吧", "呢",
    }
    return {t for t in tokens if len(t) >= 2 and t not in stopwords}


def _title_similarity(a: str, b: str) -> float:
    """Jaccard-like token overlap similarity in [0, 1]."""
    ta = _tokenize_title(a)
    tb = _tokenize_title(b)
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    union = ta | tb
    return len(intersection) / len(union) if union else 0.0


def _find_duplicate_groups_by_title(cases: list[ReferenceCase]) -> list[list[ReferenceCase]]:
    """Group cases whose title token overlap is >= 0.7.

    Uses a simple Union-Find to merge overlapping pairs into groups.
    """
    n = len(cases)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            if _title_similarity(cases[i].title, cases[j].title) >= 0.7:
                union(i, j)

    groups: dict[int, list[ReferenceCase]] = {}
    for idx, case in enumerate(cases):
        root = find(idx)
        groups.setdefault(root, []).append(case)

    # Return only groups of size >= 2
    return [g for g in groups.values() if len(g) >= 2]


def find_possible_duplicates(db: Session) -> list[dict[str, Any]]:
    """Return possible duplicate groups.

    Tier 1 — title token overlap (always available).
    Tier 2 — embedding cosine similarity (if embeddings are configured).
    """
    cases = db.query(ReferenceCase).order_by(ReferenceCase.id).all()
    if len(cases) < 2:
        return []

    # ── Tier 1: Title similarity ────────────────────────────────────
    title_groups = _find_duplicate_groups_by_title(cases)

    result: list[dict[str, Any]] = []
    for group in title_groups:
        result.append({
            "method": "title_similarity",
            "cases": [
                {
                    "id": c.id,
                    "title": c.title,
                    "aesthetic_level": c.aesthetic_level,
                    "completeness_score": compute_completeness_score(c),
                }
                for c in group
            ],
        })

    # ── Tier 2: Embedding similarity (if available) ─────────────────
    try:
        from app.services.embeddings import is_embedding_configured, search_semantic as _sem_search

        if is_embedding_configured():
            # Only search for duplicates among cases with descriptions
            cases_with_desc = [c for c in cases if _has_description(c)]
            already_in_title_groups = set()
            for g in title_groups:
                for c in g:
                    already_in_title_groups.add(c.id)

            for case in cases_with_desc:
                if case.id in already_in_title_groups:
                    continue
                desc = case.image_description or case.ai_description or ""
                if not desc.strip():
                    continue
                try:
                    sem = _sem_search(
                        db,
                        query=desc[:300],
                        top_k=5,
                        filters={},
                    )
                    for r in sem.get("results", []):
                        if r["case_id"] != case.id and r.get("similarity", 0) >= 0.90:
                            matched = db.query(ReferenceCase).filter(
                                ReferenceCase.id == r["case_id"]
                            ).first()
                            if matched and matched.id not in already_in_title_groups:
                                result.append({
                                    "method": "embedding_similarity",
                                    "cases": [
                                        {
                                            "id": case.id,
                                            "title": case.title,
                                            "aesthetic_level": case.aesthetic_level,
                                            "completeness_score": compute_completeness_score(case),
                                        },
                                        {
                                            "id": matched.id,
                                            "title": matched.title,
                                            "aesthetic_level": matched.aesthetic_level,
                                            "completeness_score": compute_completeness_score(matched),
                                        },
                                    ],
                                })
                                already_in_title_groups.add(case.id)
                                already_in_title_groups.add(matched.id)
                                break
                except Exception:
                    # Silently skip — embedding errors shouldn't block audit
                    pass
    except ImportError:
        pass

    return result


# ── Audit Report ────────────────────────────────────────────────────────

def _case_summary(case: ReferenceCase) -> dict[str, Any]:
    return {
        "id": case.id,
        "title": case.title,
        "aesthetic_level": case.aesthetic_level,
        "completeness_score": compute_completeness_score(case),
        "missing_fields": get_missing_fields(case),
    }


def audit_cases(db: Session) -> dict[str, Any]:
    """Run a full quality audit on all reference cases.

    Returns a dict matching the V1.9 CaseAuditResponse schema.
    """
    cases = db.query(ReferenceCase).order_by(ReferenceCase.id).all()

    total = len(cases)
    training_ready = [c for c in cases if is_training_ready(c)]
    incomplete = total - len(training_ready)

    # Average completeness
    avg = (
        sum(compute_completeness_score(c) for c in cases) / total
        if total > 0
        else 0.0
    )

    # ── Categorise issues ────────────────────────────────────────────
    missing_image: list[dict[str, Any]] = []
    missing_description: list[dict[str, Any]] = []
    missing_aesthetic_level: list[dict[str, Any]] = []
    missing_price_band: list[dict[str, Any]] = []
    missing_premium_sources: list[dict[str, Any]] = []
    missing_cheapness_sources: list[dict[str, Any]] = []
    missing_learning_notes: list[dict[str, Any]] = []

    for case in cases:
        s = _case_summary(case)

        if case.image_id is None:
            missing_image.append(s)
        if not _has_description(case):
            missing_description.append(s)
        level = (case.aesthetic_level or "").strip().lower()
        if not level or level == "unknown":
            missing_aesthetic_level.append(s)
        if not _is_present(case.price_band):
            missing_price_band.append(s)
        if not _is_present(case.premium_sources):
            missing_premium_sources.append(s)
        if not _is_present(case.cheapness_sources):
            missing_cheapness_sources.append(s)
        if not _is_present(case.learn_from_this) and not _is_present(case.avoid_copying):
            missing_learning_notes.append(s)

    # ── Recommendations ──────────────────────────────────────────────
    recommendations: list[str] = []
    if missing_image:
        recommendations.append(
            f"有 {len(missing_image)} 个案例缺少图片，建议上传案例图片以提升训练效果。"
        )
    if missing_description:
        recommendations.append(
            f"有 {len(missing_description)} 个案例缺少图片描述，建议使用自动描述功能生成。"
        )
    if missing_aesthetic_level:
        recommendations.append(
            f"有 {len(missing_aesthetic_level)} 个案例未设置审美等级，建议标注为 high / medium / low。"
        )
    if missing_price_band:
        recommendations.append(
            f"有 {len(missing_price_band)} 个案例缺少价格档位信息，补充后可更精准地对比分析。"
        )
    if missing_premium_sources:
        recommendations.append(
            f"有 {len(missing_premium_sources)} 个案例缺少「高级感来源」，这是训练质量的关键字段。"
        )
    if missing_cheapness_sources:
        recommendations.append(
            f"有 {len(missing_cheapness_sources)} 个案例缺少「廉价感来源」，补充后有助于全面评估。"
        )
    if missing_learning_notes:
        recommendations.append(
            f"有 {len(missing_learning_notes)} 个案例缺少「值得学习」或「不能误学」备注。"
        )
    if not recommendations and total > 0:
        recommendations.append("所有案例数据完整，案例库质量良好。")

    # ── Duplicates ───────────────────────────────────────────────────
    duplicates = find_possible_duplicates(db)

    return {
        "total_cases": total,
        "training_ready_count": len(training_ready),
        "incomplete_count": incomplete,
        "average_completeness": round(avg, 1),
        "missing_image": missing_image,
        "missing_description": missing_description,
        "missing_aesthetic_level": missing_aesthetic_level,
        "missing_price_band": missing_price_band,
        "missing_premium_sources": missing_premium_sources,
        "missing_cheapness_sources": missing_cheapness_sources,
        "missing_learning_notes": missing_learning_notes,
        "possible_duplicates": duplicates,
        "recommendations": recommendations,
    }
