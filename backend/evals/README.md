# Eval / Calibration Harness (dev-only)

> **Strategy note (2026-06-26):** this is a **minimal internal critic
> sanity-check**, not a developer "gold standard." Aesthetic taste is per-user;
> the eval only checks "is the critic broken / did it regress" on a few *clean,
> real fundamentals contrasts.* See [STRATEGY.md](STRATEGY.md). The per-user
> sample library is a separate, product-facing thing.

Answers one question: **is the critic's aesthetic score trustworthy?** — by
checking it against a small human-labeled set, and pinning the prompt version so
scoring regressions are traceable.

This is the "ruler" the rest of V2.4 (and V2.5 grounding) leans on. It is **not**
part of the runtime app, is excluded from the Docker image, and is **not** run by
pytest (it is paid + non-deterministic). Run it manually / nightly / before a
release — never as a PR gate.

## Run

From the `backend/` directory:

```bash
# Validate the gold files — no API key needed:
python -m evals.run_eval --dry-run

# Full run — scores each gold item with the critic (needs a DeepSeek key):
python -m evals.run_eval

# Cheap smoke run (first N items + pairs):
python -m evals.run_eval --limit 3
```

> On this machine, use the Python 3.11 interpreter that has the deps:
> `C:/Users/Dream/AppData/Local/Programs/Python/Python311/python.exe -m evals.run_eval --dry-run`

Reports are written to `evals/reports/report-<timestamp>.json`.

## Gold set (`gold/`)

The committed gold set is **synthetic scaffolding** (text-only descriptions, to
avoid copyright). Swap in real "consensus strong / weak" samples over time —
keep them text-only or permissively licensed.

- `gold/items.jsonl` — one object per line:
  `{"id", "label": "high|medium|low", "work_description", "note"}`
- `gold/pairs.jsonl` — one object per line:
  `{"id", "dim", "better": "a|b", "a": <desc>, "b": <desc>, "note"}`

Prefer **pairwise** labels (which of two is better) over absolute scores —
humans are unreliable at absolute aesthetic scores but reliable at relative
ordering.

## Metrics

- **items** — Spearman rank correlation between the critic's score and the
  label rank (high=3/medium=2/low=1), per-bucket means, and a
  high>medium>low monotonicity check.
- **pairs** — win-rate: fraction of pairs where the critic scores the
  gold-"better" description higher.

Advisory thresholds (in `run_eval.py`): pair win-rate ≥ 0.75, item
Spearman ≥ 0.5. Surfaced as a pre-release check, not a hard gate.

## Prompt versioning

Every run records `PROMPT_VERSION` (from `app/agents/design_knowledge.py`) and
the model name in the report. Bump `PROMPT_VERSION` whenever the knowledge base
or any scoring prompt changes, then re-run to catch regressions across versions.
