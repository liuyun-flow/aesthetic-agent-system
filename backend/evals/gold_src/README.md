# Source screenshots — drop zone

Design screenshots go here. `label_gold.py` reads them, generates objective
descriptions via the **production Vision adapter**, and emits label skeletons to
fill in by hand. Images themselves are **not committed** (copyright + size).

> This drop zone serves two purposes (see [../STRATEGY.md](../STRATEGY.md)):
> (1) building the small internal **critic sanity-check**, and (2) ingesting a
> **user's personal library**, where the *user* labels to their own taste. It is
> **not** a developer-imposed gold standard.

## Where to put what

```
gold_src/
  items/    30 standalone designs you can judge high / medium / low on sight
  pairs/    same-category twins, named with a shared prefix (see below)
```

### items/ — any filename
One design per image. The filename stem becomes the gold `id`, so name them
something stable like `landing_hi_01.png`, `portfolio_lo_03.png` (the `hi/lo`
in the name is just for *your* convenience — the actual label comes from the
skeleton you fill in, not the filename).

### pairs/ — shared prefix groups two images
Name the two sides of a pair with the **same prefix** plus a side suffix:

```
typo_1_good.png   typo_1_bad.png      # _good = the better one
color_2_good.png  color_2_bad.png
layout_3_a.png    layout_3_b.png      # _a/_b = "better" left blank for you to decide
```

- Prefix before the side suffix = the pair group (`typo_1`, `color_2`, …).
- Side suffix `_good`/`_bad` pre-fills `better` (good = better). `_a`/`_b` leaves
  it blank so you decide in the skeleton.
- Dimension is inferred from the prefix word: `typo*`→typography, `color*`→color,
  `layout*`→layout, `hier*`→hierarchy, `space*`→spacing, anything else→overall.

## Then run (from `backend/`)

```bash
# 1. verify folder layout + pairing, NO API calls, NO cost:
python -m evals.label_gold describe --dry-run

# 2. generate descriptions (needs VISION_PROVIDER=openai + OPENAI_API_KEY):
python -m evals.label_gold describe

# -> writes gold_src/items.skeleton.jsonl + gold_src/pairs.skeleton.jsonl
# 3. open those two files, fill the blank "label" / "better" fields by hand
# 4. promote the filled skeletons into the real gold set:
python -m evals.label_gold promote
```

See `../M1_PLAN.md` for the full plan, sizing, and the baseline run.
