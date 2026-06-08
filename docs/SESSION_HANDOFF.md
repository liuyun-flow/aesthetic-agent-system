# Session Handoff — 2026-06-08

## Last Completed
- **V1.7.1: Setup Wizard + Help Center** — 首次使用向导 / 帮助中心 / 配置状态条 / 系统状态端点

## Commit Timeline (this session)
```
(not yet committed) V1.7.1: Setup wizard, help center, config status bar, system status endpoint
c51071c docs: update PROJECT_STATUS and SESSION_HANDOFF for V1.7 hardening and vision fix
4ac7ee8 fix: improve vision smoke test and error messages
f290ac7 fix: harden local BYOK settings
```

## Key Deliverables — V1.7.1

### Setup Wizard (`/setup`)
- 5-step wizard: welcome → configure → test → first training → done
- Skips on re-visit, completion saved to backend config
- Chinese-first, English available via lang toggle

### Help Center (`/help`)
- Quick start, config guide, training guide, reference library, iteration/prompts, history, backup
- 8 FAQ items with collapsible answers
- Links to setup wizard and settings

### Config Status Bar (Homepage)
- Shows DeepSeek / Vision / Database / Uploads status
- Green/red badges, links to settings/help when unconfigured
- Fetches from `GET /system/status`

### Backend: `/system/status`
- Combined health + model + vision + database connectivity (`SELECT 1`) + uploads writability
- No API key exposure, only boolean flags

### Backend: `/setup/status` + `/setup/complete`
- GET returns `{setup_completed: bool}`
- POST marks wizard done (idempotent), stored in `app_config.json`

### Files Changed
- `backend/app/main.py` — +3 endpoints, version→1.7.1
- `backend/app/settings/config_store.py` — +setup section in DEFAULT_CONFIG
- `backend/app/tests/test_api.py` — +15 tests (TestSystemStatus + TestSetupEndpoints)
- `frontend/src/app/setup/page.tsx` — **new**
- `frontend/src/app/help/page.tsx` — **new**
- `frontend/src/app/layout.tsx` — +Help nav tab
- `frontend/src/app/page.tsx` — +ConfigStatusBar component
- `frontend/src/i18n/zh.ts` — +status/setup/help keys
- `frontend/src/i18n/en.ts` — +status/setup/help keys
- `README.md` — updated
- `PROJECT_STATUS.md` — updated

## Test Results
- **137 passed** (121 original + 16 new V1.7.1)
- Frontend build: ✅ (5 routes: /, /settings, /help, /setup, /_not-found)
- Docker compose config: ✅ valid

## Git Status
- Working tree: **dirty** (V1.7.1 changes not committed)
- Remote: up to date (V1.7 pushed earlier this session)

## Known Issues (carried forward)
1. GitHub push requires proxy at 127.0.0.1:7891
2. Git Bash curl can't reach 127.0.0.1 services
3. Docker not tested locally (not in PATH)
4. HTTP_PROXY env var may cause local connection failures
5. `backend/.env` DATABASE_URL still points to `./aesthetic.db` — do NOT change without migration
6. Frontend `NEXT_PUBLIC_API_BASE_URL` is build-time env
7. POST /settings/test-vision only does text chat test

## Next Session First Steps
1. Commit V1.7.1 changes: `git add -A && git commit -m "V1.7.1: Setup wizard, help center, config status bar"`
2. Push to GitHub (start proxy first)
3. Start services: `bash scripts/start_all.sh --open-browser`
4. Smoke test: verify /setup wizard completes, /help loads, status bar shows on homepage
5. V1.8: Semantic search (prerequisite: ≥50 reference cases)
