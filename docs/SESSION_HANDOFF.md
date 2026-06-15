# Session Handoff — 2026-06-15

> Per-version delivery detail lives in [CHANGELOG.md](CHANGELOG.md). This handoff
> is the current map, the lessons learned, and what to do next.

## Current state — shipped through V2.6.0

Released lineage (newest first): **V2.6.0** UI 高级化改版 · V2.5.0 信心（CI/缓存/遥测/前端测试/E2E/on-release 评测）· V2.4.x 信任度量 · V2.3.0 一键收藏+描述补全 · V2.2.x 体验+Agent 内核.

Where the key systems live:
- **Aesthetic core**: `backend/app/agents/design_knowledge.py` (rubric + signifiers + `PROMPT_VERSION`); injected into analyzer/critic/iterator/reference_comparator. Critic runs on the reasoning model.
- **Measurement**: critique stores 8 dim scores → `training_records.ai_dimension_scores/ai_overall_score`; `assessment.compute_dimension_scores` aggregates, **falls back to keyword method** when no stored scores (keeps old data/no-key working). Dimension scores measure *work quality*, not *judgment ability* (labeled honestly in UI).
- **Eval harness** (the backbone): `backend/evals/` — `run_eval.py` (pair win-rate + Spearman + `--check` gate), gold = **synthetic scaffold awaiting real samples**. Runs on-release only via `.github/workflows/evals.yml` (needs repo secret `DEEPSEEK_API_KEY`).
- **Reliability**: CI (`.github/workflows/ci.yml`) runs backend pytest + Vitest + build + E2E on push/PR. Vision-description cache (`?refresh=true`); LLM telemetry (`llm_usage` + transparent `wrap_client` + `/system/usage` + settings panel).
- **Design system** (V2.6): tokens in `frontend/tailwind.config.ts` + `frontend/src/app/globals.css` (paper/ink/accent, Fraunces display, soft/card shadows, xl2 radius). **Future UI work must use these tokens, not generic Tailwind colors.**
- Tests: 247 backend (mocked) + frontend Vitest(5) + Playwright E2E smoke.

## Lessons learned (this multi-version build)

**Process**
- **Release ritual is fixed** — see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md): bump version in `main.py` + `data_io.py` (EXPORT_VERSION) + `test_api.py`/`test_preflight.py` asserts; sync docs; commit; `git tag vX.Y.Z`; `gh release create` (route through the live proxy port). Miss any of the 4 version sites and tests fail.
- **Verify, never assume** — run the Python311 pytest + Vitest/build before claiming done. Several "it passed" beliefs were only true after a real run.
- **Migrations are additive + idempotent** (`_migrate_vX_Y`: `ALTER ADD COLUMN` in try/except, `create_all` for new tables). Tests build schema fresh so migrations aren't exercised by pytest — verify the ALTER separately if risky.
- **Keep a backward-compat path** when changing core logic (e.g. assessment keyword fallback) — that's what kept old tests green through the V2.4 measurement change.
- **Paid evals never gate PRs** (cost + non-determinism); mocked tests gate PRs, real evals run on-release.

**Environment (Windows dev box)** — fuller list in agent memory `dev-environment.md`
- **Stale lingering server burned a design review**: screenshots showed an old indigo button because Playwright `reuseExistingServer:true` reused a server running pre-change code. For visual review: kill ports 3000/8000, `rm -rf frontend/.next`, fresh build, *then* screenshot.
- **Vitest config must be `.mts`** — `@vitejs/plugin-react` is ESM-only; we dropped it and use esbuild's automatic JSX instead.
- **CJK web fonts are heavy/risky in next/font** — used Fraunces (Latin display) + system CJK stack rather than downloading a Chinese serif.

**Design**
- The premium look came from **restraint** — warm neutral ground + one accent + good type + whitespace — i.e. the same signifiers `design_knowledge.py` teaches. A scripted sed remap across files is efficient, but handle semantic colors (red/green/amber) separately and sweep stragglers.

**Product**
- **Honest framing matters**: V2.4.1 relabeled the dimension dashboard (work-quality ≠ judgment-ability). Don't let the UI overclaim what it measures.
- **Version numbers got reprioritized** (2026-06-15): Confidence moved V2.6→**V2.5**; close-the-loop moved V2.5→**~V3.0**. Plans renamed accordingly.

## Known issues
1. 开发者受限网络下 push 需本机代理（端口浮动，不入仓库）；最终用户部署无需代理
2. on-release 评测台金标准仍为合成脚手架；真实校准需加 secret + 替换真实样本（= M-1）
3. POST /settings/test-vision 只做文本 chat smoke test
4. 语义搜索为暴力余弦相似度（案例 <1000 够用）；导出不含 embeddings；导入仅合并不去重
5. 误判检测基于关键词规则（非 LLM）
6. preflight 返回本地绝对路径可能暴露用户名
7. 前端 `NEXT_PUBLIC_API_BASE_URL` 为 build-time（自定义部署需 rebuild，V2.7 修）
8. Apple Silicon Mac 未经真实机器测试；缺 `scripts/package-release`

## Next steps (pick a direction)
- **M-1 (do first, needs key)**: add repo secret `DEEPSEEK_API_KEY` + replace `backend/evals/gold/*.jsonl` with real consensus strong/weak samples → run `python -m evals.run_eval --repeat 3 --check` for a real baseline.
- **V2.7 触达**: runtime-configurable API base URL (Next.js rewrite, fixes #7); desktop packaging (Tauri/Electron — Python backend packaging is the big lift) or hosted demo. **The real barrier is the API-key wall, not packaging.**
- **~V3.0 闭环** ([V3.0_PLAN.md](V3.0_PLAN.md)): seed library (text-only seeds) + top-N grounding (**changes scores → run the harness around it**) + structured curriculum.
- Also open: R-4 vision-direct calibration (key); R-6 runtime API URL (touches ~6 components).
