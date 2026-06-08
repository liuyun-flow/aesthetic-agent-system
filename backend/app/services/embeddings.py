"""V1.8: Embedding generation and semantic search for reference cases."""

import hashlib
import json
import math
import os
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ReferenceCase, ReferenceCaseEmbedding
from app.settings.config_store import get_value


# ── Config ────────────────────────────────────────────────────────────────

def get_embedding_provider() -> str:
    """Return the configured embedding provider or 'disabled'."""
    return (
        get_value("embedding", "provider", env_var="EMBEDDING_PROVIDER")
        or "disabled"
    ).strip().lower()


def get_embedding_model() -> str:
    return (
        get_value("embedding", "openai_model", env_var="OPENAI_EMBEDDING_MODEL")
        or "text-embedding-3-small"
    ).strip()


def is_embedding_configured() -> bool:
    provider = get_embedding_provider()
    if provider != "openai":
        return False
    key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY")
    return bool(key and key.strip() and key.strip() not in ("", "replace-me", "replace-with-your-key"))


# ── Source text builder ───────────────────────────────────────────────────

def build_source_text(case: ReferenceCase) -> str:
    """Concatenate all searchable fields from a reference case."""
    parts = [
        case.title or "",
        case.category or "",
        case.aesthetic_level or "",
        case.price_band or "",
        case.style_tags or "",
        case.target_audience or "",
        case.image_description or "",
        case.ai_description or "",
        case.premium_sources or "",
        case.cheapness_sources or "",
        case.learn_from_this or "",
        case.avoid_copying or "",
        case.notes or "",
    ]
    return " ".join(p for p in parts if p)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Embedding API call ────────────────────────────────────────────────────

def _call_openai_embedding(text: str, api_key: str, model: str) -> list[float]:
    """Call OpenAI embeddings API and return the embedding vector."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding


# ── Cosine similarity ─────────────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── Reindex ───────────────────────────────────────────────────────────────

def reindex_all_cases(db: Session) -> dict[str, Any]:
    """Generate or update embeddings for all reference cases.

    Skips cases whose source text hasn't changed (by hash).
    Returns counts: indexed, skipped, failed, warnings.
    """
    if not is_embedding_configured():
        return {
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
            "warnings": ["未配置 Embedding 模型（EMBEDDING_PROVIDER 未设为 openai 或缺少 OPENAI_API_KEY）"],
        }

    provider = get_embedding_provider()
    model = get_embedding_model()
    api_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY") or ""

    cases = db.query(ReferenceCase).all()
    indexed = 0
    skipped = 0
    failed = 0
    warnings: list[str] = []

    for case in cases:
        source = build_source_text(case)
        text_hash = _hash_text(source)

        # Check if existing embedding is still fresh
        existing = (
            db.query(ReferenceCaseEmbedding)
            .filter(ReferenceCaseEmbedding.reference_case_id == case.id)
            .first()
        )
        if existing and existing.source_text_hash == text_hash:
            skipped += 1
            continue

        try:
            vec = _call_openai_embedding(source, api_key, model)
            if existing:
                existing.embedding_json = json.dumps(vec)
                existing.source_text_hash = text_hash
                existing.embedding_model = model
                existing.embedding_provider = provider
            else:
                emb = ReferenceCaseEmbedding(
                    reference_case_id=case.id,
                    embedding_provider=provider,
                    embedding_model=model,
                    embedding_json=json.dumps(vec),
                    source_text_hash=text_hash,
                )
                db.add(emb)
            db.commit()
            indexed += 1
        except Exception as e:
            db.rollback()
            failed += 1
            warnings.append(f"案例 {case.id} ({case.title}) embedding 失败: {e}")

    return {
        "indexed": indexed,
        "skipped": skipped,
        "failed": failed,
        "warnings": warnings,
    }


# ── Semantic search ───────────────────────────────────────────────────────

def search_semantic(
    db: Session,
    query: str,
    top_k: int = 10,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Search reference cases by semantic similarity.

    Generates a query embedding, computes cosine similarity against all
    indexed cases, applies optional filters, and returns top_k results.
    """
    if not is_embedding_configured():
        return {
            "results": [],
            "message": "未配置语义搜索模型（EMBEDDING_PROVIDER 未设为 openai 或缺少 OPENAI_API_KEY）。当前只能使用普通筛选。",
            "total_indexed": 0,
        }

    provider = get_embedding_provider()
    model = get_embedding_model()
    api_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY") or ""

    # Check if any embeddings exist
    total = db.query(ReferenceCaseEmbedding).count()
    if total == 0:
        return {
            "results": [],
            "message": "尚未建立语义索引，请先点击「重建语义索引」按钮。",
            "total_indexed": 0,
        }

    # Generate query embedding
    try:
        query_vec = _call_openai_embedding(query, api_key, model)
    except Exception as e:
        return {
            "results": [],
            "message": f"查询 Embedding 生成失败: {e}",
            "total_indexed": total,
        }

    # Load all embeddings and compute similarity
    embeddings = db.query(ReferenceCaseEmbedding).all()
    scored: list[tuple[ReferenceCaseEmbedding, float]] = []
    for emb in embeddings:
        case = db.query(ReferenceCase).filter(ReferenceCase.id == emb.reference_case_id).first()
        if case is None:
            continue

        # Apply filters
        if filters:
            if "category" in filters and filters["category"] and case.category != filters["category"]:
                continue
            if "aesthetic_level" in filters and filters["aesthetic_level"] and case.aesthetic_level != filters["aesthetic_level"]:
                continue
            if "price_band" in filters and filters["price_band"] and case.price_band != filters["price_band"]:
                continue

        try:
            vec = json.loads(emb.embedding_json)
        except json.JSONDecodeError:
            continue
        sim = cosine_similarity(query_vec, vec)
        scored.append((emb, sim))

    # Sort by similarity descending, take top_k
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    results = []
    for emb, sim in top:
        case = db.query(ReferenceCase).filter(ReferenceCase.id == emb.reference_case_id).first()
        if case is None:
            continue
        # Build image URL
        image_url = None
        if case.image_id:
            from app.services.session_service import get_image_by_id
            img = get_image_by_id(db, case.image_id)
            if img:
                image_url = f"/uploads/{img.stored_filename}"

        results.append({
            "case_id": case.id,
            "title": case.title,
            "score": case.score,
            "similarity": round(sim, 4),
            "aesthetic_level": case.aesthetic_level,
            "category": case.category,
            "price_band": case.price_band,
            "image_url": image_url,
            "image_description": case.image_description or case.ai_description,
            "reason": _similarity_reason(sim),
        })

    return {
        "results": results,
        "message": None,
        "total_indexed": total,
    }


def _similarity_reason(sim: float) -> str:
    if sim >= 0.85:
        return "高度匹配"
    elif sim >= 0.70:
        return "较匹配"
    elif sim >= 0.50:
        return "部分匹配"
    else:
        return "低度匹配"
