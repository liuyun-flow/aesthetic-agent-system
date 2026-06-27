# Eval strategy — minimal critic sanity-check, not a gold standard

**Decision (2026-06-26).** We are *not* building a developer-owned "gold standard"
aesthetic corpus. Aesthetic taste is per-user; a universal gold set forces
mislabels (real proof: competent HIPPEAS packaging / a Femme editorial site got
labeled "bad" only because there was no universal bad to measure against).

Two different things were both called "the library." They do opposite jobs:

| | **Critic sanity-check** (this dir) | **Personal library** (product) |
|---|---|---|
| Whose taste | nobody's — it's a *ruler* | each user's own |
| Job | "is the DeepSeek critic broken / did it regress?" | "train *my* eye against *my* standard" |
| Audience | developers, internal | the user — it's the product |
| Per-user? | no | **yes** |

## What we keep — a tiny internal sanity-check

A handful of **clean, real fundamentals contrasts** whose only job is to catch a
broken or regressed critic. "Better" must win on *craft* (hierarchy, alignment,
contrast, spacing, legibility), holding style constant — never on taste.

- Current clean pairs: **`gold_src/pairs/Business Card`** (bad side is genuinely
  broken: skewed text, gibberish copy) and **`Banner`** (good side has clearly
  stronger hierarchy). These are the seed of the sanity-check.
- Parked in `gold_src/pairs/_flagged/`: Dashboard, Mobile UI, Packaging, Poster —
  their "bad" side is competent-but-different-style (taste, not craft). Not deleted;
  either drop or swap the bad side for a genuinely botched real example.
- The synthetic `gold/*.jsonl` stays as a no-key smoke test until the real pairs
  are Vision-described into the harness.

This imposes nothing on users — they never see it.

### Status + first finding (2026-06-27)

The 2 clean pairs are now Vision-described into `gold/pairs.jsonl` and synthetic
items are retired (`gold/items.jsonl` emptied). First run: **win-rate 0.0** — the
critic rated the *gibberish* handyman card (5.0) above the clean logo (4.0).

Root cause is the architecture, not (necessarily) the critic: it scores the
**Vision description**, and GPT-4o-mini writes charitable text — it called the
broken card "clearly shows info, enhances readability, professional," laundering
out the skew/gibberish the pair hinges on. Therefore:
- This is **not** proof the critic is broken — the signal never reached it.
- A describe→critique eval **cannot validate visual fundamentals**; the vision
  layer is itself a lossy, charitable judge.
- **Production shares this blind spot** (same image→describe→critique flow), so
  the live critic can't catch visually-bad-but-charitably-described work.
- Validating visual judgment needs **vision-direct scoring (R-4)**, not text.

## What we drop

The ambition of a large developer-built gold corpus. That was the wrong model.

## What the per-user library becomes (the real build)

Users build their own sample library; the system trains their eye against *their*
standard. This is the product direction, and it reuses machinery we already have:

- **Reference cases** (`reference_service`, `reference_comparator`) — already
  "users add their own examples."
- **Profile agent** + judgment-gap — the per-user calibration primitives.
- Matches the existing **V3.0 闭环 plan**: personal seed library + grounding the
  critic in the user's own examples.

## How the current assets map

| Asset | New role |
|---|---|
| 42 real screenshots in `gold_src/items` | seed / demo content for the personal library (you are user #1) |
| `_illustrations/` | out of scope for design critique; kept for a possible illustration track |
| `label_gold.py` | the **user ingestion pipeline**: drop images → Vision describes → *user* labels to their taste |
| `Business Card` + `Banner` pairs | the internal critic sanity-check |
| `_flagged/` pairs | rework or drop |

## Open / next

1. Needs `OPENAI_API_KEY` live to run `label_gold describe` (auto-tags
   design-vs-illustration + generates descriptions in one pass).
2. Once described, wire the 2 clean pairs into `run_eval` as the sanity-check and
   retire the synthetic `gold/*.jsonl`.
3. Broader doc sync: `docs/SESSION_HANDOFF.md` M-1 line + ROADMAP framing change
   from "eval harness is the backbone / real gold" to this pivot.
