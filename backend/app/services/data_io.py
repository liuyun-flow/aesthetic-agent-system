"""V1.8: Data export / import service — backup, migration, and data portability."""

import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ReferenceCase, TrainingRecord, UploadedImage
from app.settings.config_store import get_config, mask_key


EXPORT_VERSION = "v1.8.1"


# ── Export ────────────────────────────────────────────────────────────────

def _serialize_record(r: TrainingRecord) -> dict[str, Any]:
    return {
        "id": r.id,
        "record_type": r.record_type,
        "work_description": r.work_description,
        "result_json": r.result_json,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "user_score": r.user_score,
        "user_strengths": r.user_strengths,
        "user_weaknesses": r.user_weaknesses,
        "user_priority_fixes": r.user_priority_fixes,
        "user_target_audience": r.user_target_audience,
        "user_price_band": r.user_price_band,
        "ai_score": r.ai_score,
        "ai_main_problems": r.ai_main_problems,
        "ai_priority_fixes": r.ai_priority_fixes,
        "judgment_gap_summary": r.judgment_gap_summary,
        "training_focus_tags": r.training_focus_tags,
        "selected_direction": r.selected_direction,
        "prompt_result": r.prompt_result,
    }


def _serialize_image(img: UploadedImage) -> dict[str, Any]:
    return {
        "id": img.id,
        "original_filename": img.original_filename,
        "stored_filename": img.stored_filename,
        "content_type": img.content_type,
        "size_bytes": img.size_bytes,
        "created_at": img.created_at.isoformat() if img.created_at else None,
        "ai_description": img.ai_description,
        "vision_provider": img.vision_provider,
        "vision_description_json": img.vision_description_json,
        "described_at": img.described_at.isoformat() if img.described_at else None,
    }


def _serialize_case(c: ReferenceCase) -> dict[str, Any]:
    return {
        "id": c.id,
        "title": c.title,
        "category": c.category,
        "aesthetic_level": c.aesthetic_level,
        "style_tags": c.style_tags,
        "target_audience": c.target_audience,
        "price_band": c.price_band,
        "image_id": c.image_id,
        "image_description": c.image_description,
        "ai_description": c.ai_description,
        "notes": c.notes,
        "score": c.score,
        "premium_sources": c.premium_sources,
        "cheapness_sources": c.cheapness_sources,
        "learn_from_this": c.learn_from_this,
        "avoid_copying": c.avoid_copying,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _config_summary() -> dict[str, Any]:
    """Return a safe config summary — provider/model names only, no API keys."""
    config = get_config()
    summary: dict[str, Any] = {}
    for section in ("deepseek", "vision", "setup"):
        sec = config.get(section, {})
        safe: dict[str, str] = {}
        for k, v in sec.items():
            if "key" in k.lower() or "secret" in k.lower():
                safe[k] = mask_key(v) if v else ""
            else:
                safe[k] = v
        summary[section] = safe
    return summary


def export_data(db: Session, upload_dir: Path) -> bytes:
    """Generate a zip backup containing all training data and uploaded images.

    Returns the raw bytes of the zip file.  No API keys are included.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # ── Manifest ─────────────────────────────────────────────────
        manifest = {
            "version": EXPORT_VERSION,
            "exported_at": datetime.utcnow().isoformat(),
            "counts": {},
        }

        # ── Reference cases ──────────────────────────────────────────
        cases = db.query(ReferenceCase).order_by(ReferenceCase.id).all()
        cases_data = [_serialize_case(c) for c in cases]
        zf.writestr("reference_cases.json", json.dumps(cases_data, ensure_ascii=False, indent=2))
        manifest["counts"]["reference_cases"] = len(cases_data)

        # ── Sessions ─────────────────────────────────────────────────
        records = db.query(TrainingRecord).order_by(TrainingRecord.id).all()
        records_data = [_serialize_record(r) for r in records]
        zf.writestr("sessions.json", json.dumps(records_data, ensure_ascii=False, indent=2))
        manifest["counts"]["sessions"] = len(records_data)

        # ── Prompts (sessions with prompt_result) ────────────────────
        prompts_data = [
            r for r in records_data
            if r.get("selected_direction") and r.get("prompt_result")
        ]
        if prompts_data:
            zf.writestr("prompts.json", json.dumps(prompts_data, ensure_ascii=False, indent=2))
            manifest["counts"]["prompts"] = len(prompts_data)

        # ── Uploaded images metadata ─────────────────────────────────
        images = db.query(UploadedImage).order_by(UploadedImage.id).all()
        images_data = [_serialize_image(img) for img in images]
        zf.writestr("uploaded_images.json", json.dumps(images_data, ensure_ascii=False, indent=2))
        manifest["counts"]["uploaded_images"] = len(images_data)

        # ── Config summary (no keys) ─────────────────────────────────
        zf.writestr("config_summary.json", json.dumps(_config_summary(), ensure_ascii=False, indent=2))

        # ── Image files ──────────────────────────────────────────────
        copied = 0
        for img in images:
            path = Path(img.file_path)
            if path.exists() and path.is_file():
                arcname = f"uploads/{img.stored_filename}"
                if arcname not in zf.namelist():
                    zf.write(path, arcname)
                    copied += 1
        manifest["counts"]["images_copied"] = copied

        # ── Manifest (write once at the end with all counts) ─────────
        zf.writestr("export_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    buf.seek(0)
    return buf.getvalue()


# ── Import ────────────────────────────────────────────────────────────────

class ImportResult:
    def __init__(self):
        self.reference_cases_imported = 0
        self.sessions_imported = 0
        self.images_imported = 0
        self.skipped_items = 0
        self.warnings: list[str] = []
        # ID remapping: old_id → new_id for both images and cases
        self._image_id_map: dict[int, int] = {}
        self._case_id_map: dict[int, int] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_cases_imported": self.reference_cases_imported,
            "sessions_imported": self.sessions_imported,
            "images_imported": self.images_imported,
            "skipped_items": self.skipped_items,
            "warnings": self.warnings,
        }


def _safe_path_component(name: str) -> bool:
    """Reject path traversal in zip entry names."""
    return not name.startswith("/") and not name.startswith("\\") and ".." not in name


def import_data(
    db: Session,
    zip_bytes: bytes,
    upload_dir: Path,
) -> ImportResult:
    """Import data from a V1.8 export zip.  Merge-only — never overwrites.

    Validates zip structure, prevents zip slip, remaps IDs,
    and produces an ImportResult with counts and warnings.
    """
    result = ImportResult()

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        # ── Validate structure ───────────────────────────────────────
        names = set(zf.namelist())
        if "export_manifest.json" not in names:
            result.warnings.append("缺少 export_manifest.json，尝试继续导入")
        for name in names:
            if not _safe_path_component(name):
                raise ValueError(f"不安全的 zip 路径: {name}")

        # ── Parse manifest ───────────────────────────────────────────
        manifest: dict = {}
        if "export_manifest.json" in names:
            manifest = json.loads(zf.read("export_manifest.json"))
            version = manifest.get("version", "")
            if not version.startswith("v1."):
                result.warnings.append(f"导出包版本 {version} 可能不兼容，当前版本 {EXPORT_VERSION}")

        # ── Step 1: Import images ────────────────────────────────────
        if "uploaded_images.json" in names:
            images_data = json.loads(zf.read("uploaded_images.json"))
            result = _import_images(zf, images_data, upload_dir, db, result)

        # ── Step 2: Import reference cases (with remapped image_ids) ─
        if "reference_cases.json" in names:
            cases_data = json.loads(zf.read("reference_cases.json"))
            result = _import_cases(cases_data, db, result)

        # ── Step 3: Import sessions ──────────────────────────────────
        if "sessions.json" in names:
            sessions_data = json.loads(zf.read("sessions.json"))
            result = _import_sessions(sessions_data, db, result)

    return result


def _import_images(
    zf: zipfile.ZipFile,
    images_data: list[dict],
    upload_dir: Path,
    db: Session,
    result: ImportResult,
) -> ImportResult:
    upload_dir.mkdir(parents=True, exist_ok=True)

    for img_meta in images_data:
        old_id = img_meta.get("id", 0)
        stored_filename = img_meta.get("stored_filename", "")
        zip_path = f"uploads/{stored_filename}"

        # Copy image file from zip
        if zip_path in zf.namelist() and _safe_path_component(zip_path):
            dest = upload_dir / stored_filename
            if not dest.exists():
                try:
                    with zf.open(zip_path) as src:
                        with open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                except Exception as e:
                    result.warnings.append(f"无法导入图片 {stored_filename}: {e}")
                    result.skipped_items += 1
                    continue

        # Persist metadata (use new id)
        existing = db.query(UploadedImage).filter(
            UploadedImage.stored_filename == stored_filename
        ).first()
        if existing:
            result._image_id_map[old_id] = existing.id
            result.skipped_items += 1
            result.warnings.append(f"图片 {stored_filename} 已存在，跳过")
            continue

        try:
            img = UploadedImage(
                original_filename=img_meta.get("original_filename", stored_filename),
                stored_filename=stored_filename,
                file_path=str((upload_dir / stored_filename).resolve()),
                content_type=img_meta.get("content_type", "application/octet-stream"),
                size_bytes=img_meta.get("size_bytes", 0),
                ai_description=img_meta.get("ai_description"),
                vision_provider=img_meta.get("vision_provider"),
                vision_description_json=img_meta.get("vision_description_json"),
            )
            db.add(img)
            db.commit()
            db.refresh(img)
            result._image_id_map[old_id] = img.id
            result.images_imported += 1
        except Exception as e:
            db.rollback()
            result.warnings.append(f"图片元数据导入失败 {stored_filename}: {e}")
            result.skipped_items += 1

    return result


def _import_cases(
    cases_data: list[dict],
    db: Session,
    result: ImportResult,
) -> ImportResult:
    for case_meta in cases_data:
        old_id = case_meta.get("id", 0)

        # Remap image_id
        old_image_id = case_meta.get("image_id")
        new_image_id = None
        if old_image_id is not None and old_image_id in result._image_id_map:
            new_image_id = result._image_id_map[old_image_id]

        try:
            case = ReferenceCase(
                title=case_meta.get("title", "Imported Case"),
                category=case_meta.get("category"),
                aesthetic_level=case_meta.get("aesthetic_level", "unknown"),
                style_tags=case_meta.get("style_tags"),
                target_audience=case_meta.get("target_audience"),
                price_band=case_meta.get("price_band"),
                image_id=new_image_id,
                image_description=case_meta.get("image_description"),
                ai_description=case_meta.get("ai_description"),
                notes=case_meta.get("notes"),
                score=case_meta.get("score"),
                premium_sources=case_meta.get("premium_sources"),
                cheapness_sources=case_meta.get("cheapness_sources"),
                learn_from_this=case_meta.get("learn_from_this"),
                avoid_copying=case_meta.get("avoid_copying"),
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            result._case_id_map[old_id] = case.id
            result.reference_cases_imported += 1
        except Exception as e:
            db.rollback()
            result.warnings.append(f"案例导入失败 '{case_meta.get('title', '?')}': {e}")
            result.skipped_items += 1

    return result


def _import_sessions(
    sessions_data: list[dict],
    db: Session,
    result: ImportResult,
) -> ImportResult:
    for rec_meta in sessions_data:
        try:
            record = TrainingRecord(
                record_type=rec_meta.get("record_type", "analyze"),
                work_description=rec_meta.get("work_description", ""),
                result_json=rec_meta.get("result_json"),
                user_score=rec_meta.get("user_score"),
                user_strengths=rec_meta.get("user_strengths"),
                user_weaknesses=rec_meta.get("user_weaknesses"),
                user_priority_fixes=rec_meta.get("user_priority_fixes"),
                user_target_audience=rec_meta.get("user_target_audience"),
                user_price_band=rec_meta.get("user_price_band"),
                ai_score=rec_meta.get("ai_score"),
                ai_main_problems=rec_meta.get("ai_main_problems"),
                ai_priority_fixes=rec_meta.get("ai_priority_fixes"),
                judgment_gap_summary=rec_meta.get("judgment_gap_summary"),
                training_focus_tags=rec_meta.get("training_focus_tags"),
                selected_direction=rec_meta.get("selected_direction"),
                prompt_result=rec_meta.get("prompt_result"),
            )
            db.add(record)
            db.commit()
            result.sessions_imported += 1
        except Exception as e:
            db.rollback()
            result.warnings.append(f"训练记录导入失败: {e}")
            result.skipped_items += 1

    return result
