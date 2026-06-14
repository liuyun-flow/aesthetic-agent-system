"""Eval / calibration harness for the critic's aesthetic scoring.

Answers one question: *is the critic's score trustworthy?* — by checking it
against a human-labeled gold set, and recording the prompt version so scoring
regressions are traceable.

This is the "ruler" the rest of V2.4 (and V2.5 grounding) leans on. Build it
first; judge later changes with data, not vibes.

Usage (run from the backend/ directory):

    # Validate the gold files without calling any model (no API key needed):
    python -m evals.run_eval --dry-run

    # Full run — scores each gold item with the critic (needs DEEPSEEK key):
    python -m evals.run_eval
    python -m evals.run_eval --limit 3      # cheap smoke run

Gold formats (JSONL, one object per line):

  gold/items.jsonl   {"id","label":"high|medium|low","work_description","note"}
  gold/pairs.jsonl   {"id","dim","better":"a|b","a":<desc>,"b":<desc>,"note"}

Metrics:
  - items: Spearman rank correlation between critic score and label rank,
           per-bucket means, and a high>medium>low monotonicity check.
  - pairs: win-rate — fraction where the critic scores the gold-"better"
           description higher.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Path bootstrap so `import app.*` works however this is invoked ──────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_GOLD_DIR = Path(__file__).resolve().parent / "gold"
_REPORTS_DIR = Path(__file__).resolve().parent / "reports"

_LABEL_RANK = {"low": 1, "medium": 2, "high": 3}

# Suggested thresholds (advisory, not a hard gate). Surfaced in RELEASE_CHECKLIST.
PAIR_WIN_RATE_THRESHOLD = 0.75
ITEM_SPEARMAN_THRESHOLD = 0.5


# ── Gold loading + validation ──────────────────────────────────────────────

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Gold file not found: {path}")
    rows: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} line {i}: invalid JSON — {exc}") from exc
    return rows


def _validate_items(items: list[dict]) -> list[str]:
    errs: list[str] = []
    for r in items:
        rid = r.get("id", "<no-id>")
        if r.get("label") not in _LABEL_RANK:
            errs.append(f"item {rid}: label must be high/medium/low, got {r.get('label')!r}")
        if not str(r.get("work_description", "")).strip():
            errs.append(f"item {rid}: empty work_description")
    return errs


def _validate_pairs(pairs: list[dict]) -> list[str]:
    errs: list[str] = []
    for r in pairs:
        rid = r.get("id", "<no-id>")
        if r.get("better") not in ("a", "b"):
            errs.append(f"pair {rid}: 'better' must be 'a' or 'b', got {r.get('better')!r}")
        if not str(r.get("a", "")).strip() or not str(r.get("b", "")).strip():
            errs.append(f"pair {rid}: 'a' and 'b' must both be non-empty descriptions")
    return errs


# ── Stats (no scipy — keep deps minimal) ───────────────────────────────────

def _fractional_ranks(values: list[float]) -> list[float]:
    """Average-rank for ties, 1-based."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return _pearson(_fractional_ranks(xs), _fractional_ranks(ys))


# ── Critic scoring ─────────────────────────────────────────────────────────

def _build_critic():
    """Lazily build a critic on the reasoning model. Raises on missing key."""
    from app.agents.critic import CriticAgent
    from app.llm.deepseek_client import get_deepseek_client, get_reasoning_model

    client = get_deepseek_client()  # raises ValueError if no key
    return CriticAgent(client=client, model=get_reasoning_model()), get_reasoning_model()


def _score(critic, description: str) -> float:
    """Return the critic's total_score (1-10) for a description."""
    result = critic.run(description)
    return float(result.total_score)


# ── Eval run ───────────────────────────────────────────────────────────────

def run(dry_run: bool = False, limit: int | None = None) -> int:
    items = _load_jsonl(_GOLD_DIR / "items.jsonl")
    pairs = _load_jsonl(_GOLD_DIR / "pairs.jsonl")

    errs = _validate_items(items) + _validate_pairs(pairs)
    if errs:
        print("Gold validation FAILED:")
        for e in errs:
            print(f"  - {e}")
        return 1

    print(f"Gold OK: {len(items)} items, {len(pairs)} pairs.")

    if dry_run:
        by_label: dict[str, int] = {}
        for r in items:
            by_label[r["label"]] = by_label.get(r["label"], 0) + 1
        print(f"  item label distribution: {by_label}")
        print("Dry run - no model called.")
        return 0

    if limit is not None:
        items = items[:limit]
        pairs = pairs[:limit]

    from app.agents.design_knowledge import PROMPT_VERSION

    try:
        critic, model = _build_critic()
    except ValueError as exc:
        print(f"\nCannot run scoring: {exc}")
        print("Configure a DeepSeek key (settings page or DEEPSEEK_API_KEY), "
              "or use --dry-run to validate gold only.")
        return 1

    print(f"Scoring with model={model}, prompt_version={PROMPT_VERSION} …\n")

    # Score each unique description once (descriptions may repeat across sets).
    score_cache: dict[str, float] = {}

    def cached_score(desc: str) -> float | None:
        if desc not in score_cache:
            try:
                score_cache[desc] = _score(critic, desc)
            except Exception as exc:  # one bad call must not kill the run
                print(f"  ! scoring error: {exc}")
                return None
        return score_cache[desc]

    # ── Items ──────────────────────────────────────────────────────────
    item_detail = []
    crit_scores: list[float] = []
    label_ranks: list[float] = []
    bucket: dict[str, list[float]] = {"high": [], "medium": [], "low": []}
    for r in items:
        s = cached_score(r["work_description"])
        if s is None:
            continue
        crit_scores.append(s)
        label_ranks.append(float(_LABEL_RANK[r["label"]]))
        bucket[r["label"]].append(s)
        item_detail.append({"id": r["id"], "label": r["label"], "critic_score": s})
        print(f"  [{r['label']:>6}] {s:>4.1f}  {r['id']}")

    spearman = _spearman(crit_scores, label_ranks)
    bucket_means = {k: (round(sum(v) / len(v), 2) if v else None) for k, v in bucket.items()}
    monotonic = (
        bucket_means["high"] is not None
        and bucket_means["medium"] is not None
        and bucket_means["low"] is not None
        and bucket_means["high"] > bucket_means["medium"] > bucket_means["low"]
    )

    # ── Pairs ──────────────────────────────────────────────────────────
    pair_detail = []
    correct = 0
    counted = 0
    for r in pairs:
        sa = cached_score(r["a"])
        sb = cached_score(r["b"])
        if sa is None or sb is None:
            continue
        counted += 1
        predicted = "a" if sa > sb else "b" if sb > sa else "tie"
        ok = predicted == r["better"]
        correct += 1 if ok else 0
        pair_detail.append({
            "id": r["id"], "dim": r.get("dim", "overall"),
            "score_a": sa, "score_b": sb, "gold": r["better"],
            "predicted": predicted, "correct": ok,
        })
        print(f"  pair {r['id']}: a={sa:.1f} b={sb:.1f} gold={r['better']} "
              f"pred={predicted} {'ok' if ok else 'X'}")

    win_rate = round(correct / counted, 3) if counted else None

    # ── Report ─────────────────────────────────────────────────────────
    report = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": {
            "n": len(item_detail),
            "spearman": round(spearman, 3) if spearman is not None else None,
            "bucket_means": bucket_means,
            "monotonic_high_gt_medium_gt_low": monotonic,
            "detail": item_detail,
        },
        "pairs": {
            "n": counted,
            "win_rate": win_rate,
            "detail": pair_detail,
        },
    }

    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = _REPORTS_DIR / f"report-{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── Summary ────────────────────────────────────────────────────────
    print("\n-- Summary --")
    print(f"prompt_version : {PROMPT_VERSION}   model: {model}")
    print(f"items          : n={len(item_detail)}  spearman={report['items']['spearman']}  "
          f"monotonic={monotonic}  means={bucket_means}")
    print(f"pairs          : n={counted}  win_rate={win_rate}")
    if win_rate is not None:
        print(f"  pair win-rate {'PASS' if win_rate >= PAIR_WIN_RATE_THRESHOLD else 'WARN'} "
              f"(threshold {PAIR_WIN_RATE_THRESHOLD})")
    if spearman is not None:
        print(f"  item spearman {'PASS' if spearman >= ITEM_SPEARMAN_THRESHOLD else 'WARN'} "
              f"(threshold {ITEM_SPEARMAN_THRESHOLD})")
    print(f"report written : {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Critic scoring eval / calibration harness")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate gold files only; do not call any model")
    ap.add_argument("--limit", type=int, default=None,
                    help="Score only the first N items and pairs (cheap smoke run)")
    args = ap.parse_args()
    return run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
