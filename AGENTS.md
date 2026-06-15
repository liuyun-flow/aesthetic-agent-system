# AGENTS.md — Coding Agent Instructions

## Project
AI 审美训练本地工具。用户上传设计作品 → AI 分析审美质量 → 用户自评对比 → 参考案例库 → 训练复盘。

## File Structure
```
aesthetic-agent-system/
├── backend/
│   ├── app/
│   │   ├── agents/     # Analyzer, Critic, Iterator, Comparator, Profile, PromptGenerator, ReferenceComparator, WeeklyReview
│   │   ├── vision/     # VisionAdapter (base, placeholder, manual, openai)
│   │   ├── db/         # models, database, migrations
│   │   ├── schemas/    # requests.py, responses.py
│   │   └── services/   # session_service, reference_service
│   └── data/uploads/   # 上传图片 (git-ignored)
├── frontend/
│   └── src/
│       ├── app/        # page.tsx, layout.tsx
│       ├── components/ # TaskForm, ResultCard, SessionList, ReferencePanel, TrainingPanel
│       ├── i18n/       # zh.ts, en.ts, index.tsx
│       └── lib/        # formatters.ts
├── scripts/            # start.sh, stop.sh, start.bat, start_all.sh, kill_port.sh, check-env.py
├── AI_CONTEXT.md       # 跨平台工程规范
└── docs/
```

## Development Rules
- Python 3.11+, TypeScript strict
- Backend: 127.0.0.1 (not localhost) for all internal calls
- Frontend: Chinese UI only; i18n keys sync en.ts ⇔ zh.ts
- Tests: 247 pytest (mock agents, no API key needed) + frontend Vitest component tests + Playwright E2E smoke
- CI: GitHub Actions (`.github/workflows/ci.yml`) runs backend pytest + frontend Vitest + build on push/PR — keep green
- DB: SQLite, auto-migration on startup, delete aesthetic.db to reset
- Dev proxy (push/release only; never in repo, end users need none): git uses the
  global proxy config. The port floats with the proxy client — pin it to a fixed
  port to avoid breakage. `gh` obeys `HTTP_PROXY`/`HTTPS_PROXY`; if the env port is
  stale, override per command, e.g. `HTTPS_PROXY=http://127.0.0.1:<live-port> gh ...`

## DO NOT
- Expose API keys to frontend or logs
- Use `taskkill //IM python.exe` (use `scripts/kill_port.sh`)
- Let placeholder impersonate real vision
- Break session detail modal (history click → popup)
- Break V1.1 user judgment / comparator flow
- Commit .env or real keys

## Test Commands
```bash
cd backend && pytest app/tests/ -q     # 242 mocked, no key (use Python311 interp locally)
cd frontend && npm run test            # Vitest component tests
cd frontend && npm run build           # must pass
```

## PR Checklist
- [ ] CI green (backend pytest + frontend Vitest + build)
- [ ] Backend tests pass; Frontend Vitest + `npm run build` pass
- [ ] Chinese UI not broken
- [ ] Session detail modal works
- [ ] analyze / critique / iterate not broken
- [ ] No API keys in code or commits
- [ ] .env.example uses safe placeholders
