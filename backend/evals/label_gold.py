"""Screenshot -> description -> label pipeline.

Two uses (see STRATEGY.md — we no longer build a developer "gold standard"):
  1. Build the small internal **critic sanity-check** pairs.
  2. Ingest a **user's personal library** — drop images, the Vision adapter
     describes them, and the user labels to *their own* taste.

Bridges the human-labeling workflow into the eval harness (`run_eval.py`):

  1. You drop real design screenshots into ``evals/gold_src/{items,pairs}/``.
  2. ``describe`` runs each image through the **production Vision adapter**
     (same code path the app uses) and emits ``*.skeleton.jsonl`` files whose
     ``work_description`` is filled but whose ``label`` / ``better`` are blank.
  3. You fill the blank labels by hand — judging the *image*, not the text.
  4. ``promote`` validates the filled skeletons (reusing run_eval's validators)
     and writes them into ``gold/items.jsonl`` + ``gold/pairs.jsonl``.

Why Vision-generated descriptions: the critic must infer quality from *neutral*
facts (colors, spacing, type) rather than from rubric vocabulary baked into the
text. Using ``suggested_prompt_text`` — the exact field the critic scores in
production — keeps the gold faithful to the real pipeline and free of evaluative
leakage. (Spot-check the output anyway for stray quality adjectives.)

Usage (run from the ``backend/`` directory):

    # Verify folder layout + pairing — no API calls, no cost:
    python -m evals.label_gold describe --dry-run

    # Generate descriptions (needs VISION_PROVIDER=openai + OPENAI_API_KEY):
    python -m evals.label_gold describe
    python -m evals.label_gold describe --limit 5     # cheap first batch
    python -m evals.label_gold describe --refresh      # ignore cache, re-describe

    # After filling label/better in the skeletons, merge into the gold set:
    python -m evals.label_gold promote
    python -m evals.label_gold promote --dry-run       # validate only, don't write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ── Path bootstrap so `import app.*` works however this is invoked ──────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_EVALS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _EVALS_DIR / "gold_src"
_ITEMS_SRC = _SRC_DIR / "items"
_PAIRS_SRC = _SRC_DIR / "pairs"
_GOLD_DIR = _EVALS_DIR / "gold"
_CACHE_FILE = _SRC_DIR / ".describe_cache.json"

_ITEMS_SKELETON = _SRC_DIR / "items.skeleton.jsonl"
_PAIRS_SKELETON = _SRC_DIR / "pairs.skeleton.jsonl"

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_SIDE_SUFFIXES = ("_good", "_bad", "_a", "_b")

# Map a pair prefix's leading word to a scoring dimension.
_DIM_PREFIXES = {
    "typo": "typography",
    "type": "typography",
    "color": "color",
    "colour": "color",
    "layout": "layout",
    "grid": "layout",
    "hier": "hierarchy",
    "space": "spacing",
    "spacing": "spacing",
}


# ── Vision adapter (mirrors app.main.get_vision_adapter without booting FastAPI) ──

def _build_vision_adapter(allow_placeholder: bool):
    """Return the configured Vision adapter — same priority as the app.

    Refuses the placeholder provider unless explicitly allowed, since placeholder
    descriptions are fixed mock text that would silently poison the gold set.
    """
    from app.settings.config_store import get_value
    from app.vision.manual_adapter import ManualAdapter
    from app.vision.openai_adapter import OpenAIVisionAdapter
    from app.vision.placeholder_adapter import PlaceholderAdapter

    provider = (
        get_value("vision", "provider", env_var="VISION_PROVIDER") or "placeholder"
    ).strip().lower()

    if provider == "openai":
        api_key = get_value("vision", "openai_api_key", env_var="OPENAI_API_KEY")
        model = get_value("vision", "openai_vision_model", env_var="OPENAI_VISION_MODEL")
        return OpenAIVisionAdapter(api_key=api_key, model=model), provider, (model or "gpt-4o-mini")

    if provider == "manual":
        # Manual adapter just echoes a hint — useless for unattended gold building.
        raise SystemExit(
            "VISION_PROVIDER=manual cannot auto-describe images. "
            "Set VISION_PROVIDER=openai (+ OPENAI_API_KEY) to build gold."
        )

    if not allow_placeholder:
        raise SystemExit(
            "VISION_PROVIDER is 'placeholder' — descriptions would be fixed mock "
            "text and would poison the gold set. Set VISION_PROVIDER=openai (+ "
            "OPENAI_API_KEY), or pass --allow-placeholder only to test the pipeline."
        )
    return PlaceholderAdapter(), provider, "placeholder"


# ── Cache (avoid re-paying for images already described) ────────────────────

def _load_cache() -> dict:
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _cache_key(path: Path, provider: str, model: str) -> str:
    return f"{path.name}:{path.stat().st_mtime_ns}:{provider}:{model}"


# ── Image discovery ─────────────────────────────────────────────────────────

def _list_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in _IMAGE_EXTS)


def _pair_group(stem: str) -> tuple[str, str | None]:
    """Split a pair filename stem into (group_prefix, side).

    'typo_1_good' -> ('typo_1', 'good');  'layout_3_a' -> ('layout_3', 'a').
    A stem without a recognized side suffix is its own group with side None.
    """
    for suf in _SIDE_SUFFIXES:
        if stem.endswith(suf):
            return stem[: -len(suf)], suf.lstrip("_")
    return stem, None


def _infer_dim(prefix: str) -> str:
    head = prefix.lower().split("_", 1)[0]
    for key, dim in _DIM_PREFIXES.items():
        if head.startswith(key):
            return dim
    return "overall"


# ── describe: screenshots -> skeleton jsonl ─────────────────────────────────

def _describe_image(adapter, path: Path, cache: dict, provider: str, model: str,
                    refresh: bool) -> str:
    key = _cache_key(path, provider, model)
    if not refresh and key in cache:
        return cache[key]
    desc = adapter.describe_image_structured(str(path))
    text = (desc.suggested_prompt_text or desc.summary or "").strip()
    cache[key] = text
    return text


def cmd_describe(limit: int | None, dry_run: bool, refresh: bool,
                 allow_placeholder: bool) -> int:
    items = _list_images(_ITEMS_SRC)
    pair_imgs = _list_images(_PAIRS_SRC)

    # Group pair images by shared prefix.
    groups: dict[str, dict[str, Path]] = {}
    for p in pair_imgs:
        prefix, side = _pair_group(p.stem)
        groups.setdefault(prefix, {})[side or p.stem] = p

    print(f"Found {len(items)} item image(s) in {_ITEMS_SRC}")
    print(f"Found {len(pair_imgs)} pair image(s) in {len(groups)} group(s) in {_PAIRS_SRC}")

    # Report malformed pair groups up front.
    bad_groups = {k: v for k, v in groups.items() if len(v) != 2}
    if bad_groups:
        print("\n! These pair groups do not have exactly 2 images (skipped):")
        for k, v in bad_groups.items():
            print(f"    {k}: {sorted(p.name for p in v.values())}")

    if dry_run:
        print("\n-- dry run: pairing preview (no model called) --")
        for prefix, sides in sorted(groups.items()):
            if len(sides) != 2:
                continue
            print(f"  pair '{prefix}' (dim={_infer_dim(prefix)}): {sorted(sides.keys())}")
        if not items and not groups:
            print("  (nothing to describe - drop images into gold_src/ first)")
        return 0

    if not items and not groups:
        print("Nothing to describe. Drop images into gold_src/items|pairs first.")
        return 1

    adapter, provider, model = _build_vision_adapter(allow_placeholder)
    cache = _load_cache()
    print(f"\nDescribing with provider={provider}, model={model} "
          f"{'(cache ignored)' if refresh else '(reusing cache where possible)'} ...\n")

    described = 0

    # ── Items ──────────────────────────────────────────────────────────
    item_rows: list[dict] = []
    for p in items:
        if limit is not None and described >= limit:
            break
        try:
            text = _describe_image(adapter, p, cache, provider, model, refresh)
        except Exception as exc:
            print(f"  ! {p.name}: {exc}")
            continue
        described += 1
        item_rows.append({"id": p.stem, "label": "", "work_description": text, "note": ""})
        print(f"  item  {p.name}  ->  {text[:50]}...")

    # ── Pairs ──────────────────────────────────────────────────────────
    pair_rows: list[dict] = []
    for prefix in sorted(groups):
        sides = groups[prefix]
        if len(sides) != 2:
            continue
        if limit is not None and described >= limit:
            break
        # Resolve which file is 'a' and which is 'b', and any better hint.
        if "good" in sides and "bad" in sides:
            a_path, b_path, better = sides["good"], sides["bad"], "a"
        elif "a" in sides and "b" in sides:
            a_path, b_path, better = sides["a"], sides["b"], ""
        else:
            ordered = [sides[k] for k in sorted(sides)]
            a_path, b_path, better = ordered[0], ordered[1], ""
        try:
            a_text = _describe_image(adapter, a_path, cache, provider, model, refresh)
            b_text = _describe_image(adapter, b_path, cache, provider, model, refresh)
        except Exception as exc:
            print(f"  ! pair {prefix}: {exc}")
            continue
        described += 2
        pair_rows.append({
            "id": f"pair-{prefix}", "dim": _infer_dim(prefix),
            "better": better, "a": a_text, "b": b_text, "note": "",
        })
        hint = f"better={better}" if better else "better=? (fill in)"
        print(f"  pair  {prefix}  ({_infer_dim(prefix)}, {hint})")

    _save_cache(cache)

    if item_rows:
        _write_jsonl(_ITEMS_SKELETON, item_rows)
        print(f"\nWrote {len(item_rows)} item rows -> {_ITEMS_SKELETON}")
    if pair_rows:
        _write_jsonl(_PAIRS_SKELETON, pair_rows)
        print(f"Wrote {len(pair_rows)} pair rows -> {_PAIRS_SKELETON}")

    blank_items = sum(1 for r in item_rows if not r["label"])
    blank_pairs = sum(1 for r in pair_rows if not r["better"])
    print("\nNext: open the skeleton file(s) and fill the blank fields by hand -")
    print(f"  {blank_items} item 'label' (high|medium|low), "
          f"{blank_pairs} pair 'better' (a|b).")
    print("Judge the IMAGE, not the text. Then run: python -m evals.label_gold promote")
    return 0


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── promote: filled skeleton -> gold/ ───────────────────────────────────────

def cmd_promote(dry_run: bool) -> int:
    from evals.run_eval import _validate_items, _validate_pairs

    if not _ITEMS_SKELETON.exists() and not _PAIRS_SKELETON.exists():
        print("No skeleton files found. Run `label_gold describe` first.")
        return 1

    items = _read_jsonl(_ITEMS_SKELETON)
    pairs = _read_jsonl(_PAIRS_SKELETON)

    # Surface blanks with a friendlier message than the schema validator.
    errs: list[str] = []
    for r in items:
        if not str(r.get("label", "")).strip():
            errs.append(f"item {r.get('id')}: 'label' is still blank - fill high|medium|low")
    for r in pairs:
        if not str(r.get("better", "")).strip():
            errs.append(f"pair {r.get('id')}: 'better' is still blank - fill a|b")
    errs += _validate_items(items) + _validate_pairs(pairs)

    if errs:
        print("Promote BLOCKED - fix these in the skeleton file(s):")
        for e in errs:
            print(f"  - {e}")
        return 1

    print(f"Validated: {len(items)} items, {len(pairs)} pairs - all labeled.")
    if dry_run:
        print("Dry run - gold files not written.")
        return 0

    _GOLD_DIR.mkdir(parents=True, exist_ok=True)
    _backup_then_write(_GOLD_DIR / "items.jsonl", items)
    _backup_then_write(_GOLD_DIR / "pairs.jsonl", pairs)
    print(f"\nPromoted into {_GOLD_DIR}/ (previous gold backed up to *.bak).")
    print("Verify, then run the baseline:")
    print("  python -m evals.run_eval --dry-run        # validate")
    print("  python -m evals.run_eval --repeat 3       # real baseline (needs DEEPSEEK key)")
    return 0


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _backup_then_write(path: Path, rows: list[dict]) -> None:
    if path.exists():
        path.with_suffix(path.suffix + ".bak").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    _write_jsonl(path, rows)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Build the eval gold set from real screenshots")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("describe", help="Describe screenshots -> label skeletons")
    d.add_argument("--limit", type=int, default=None, help="Describe at most N images (cheap batch)")
    d.add_argument("--dry-run", action="store_true", help="Show pairing only; call no model")
    d.add_argument("--refresh", action="store_true", help="Ignore cache and re-describe")
    d.add_argument("--allow-placeholder", action="store_true",
                   help="Permit the placeholder provider (pipeline testing only — poisons gold)")

    p = sub.add_parser("promote", help="Validate filled skeletons -> gold/")
    p.add_argument("--dry-run", action="store_true", help="Validate only; do not write gold files")

    args = ap.parse_args()
    if args.cmd == "describe":
        return cmd_describe(args.limit, args.dry_run, args.refresh, args.allow_placeholder)
    if args.cmd == "promote":
        return cmd_promote(args.dry_run)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
