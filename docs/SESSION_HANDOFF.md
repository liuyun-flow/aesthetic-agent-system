# Session Handoff — 2026-06-09

## Last Completed
- **V1.8.1: Stability fixes, regression tests, pre-release cleanup**

## V1.8.1 Changes
- Version bumped to v1.8.1 across all files (main.py, export manifest, health, system/status)
- `.gitignore` added `*.zip` to prevent backup files from being committed
- Full regression: 158 tests passed, frontend build passed
- Export zip verified: correct structure, no API key exposure, images included
- Docker compose config passed, mount points verified
- All docs synced (README, PROJECT_STATUS, ROADMAP, SESSION_HANDOFF)

## V1.8 (previous session)
- Data export/import: zip backup with manifest, cases, sessions, prompts, images, config summary (no keys)
- Semantic search over reference cases using OpenAI text-embedding-3-small
- ReferenceCaseEmbedding model + reindex + cosine similarity search
- Frontend: data management section in settings, semantic search UI in reference panel
- Compare-with-references semantic fallback
- 158 tests total

## Git Status
- Working tree: **dirty** (V1.8.1 changes not committed)

## Known Issues
1. GitHub push requires proxy at 127.0.0.1:7891
2. Git Bash curl can't reach 127.0.0.1 services
3. Docker compose up smoke test passed
4. HTTP_PROXY env var may cause local connection failures
5. `backend/.env` DATABASE_URL still points to `./aesthetic.db` — do NOT change without migration
6. Frontend `NEXT_PUBLIC_API_BASE_URL` is build-time env
7. Semantic search requires OPENAI_API_KEY (reuses Vision key) — graceful degradation when missing
8. Embedding search is brute-force cosine similarity — fine for <1000 cases, may need optimization later
9. Export does not include embeddings (user must reindex after import)

## Next Session First Steps
1. Commit V1.8.1: `git add -A && git commit -m "V1.8.1: Stability fixes, regression tests, pre-release cleanup"`
2. Push to GitHub
3. Quick smoke test: docker compose up --build, verify /health→v1.8.1, frontend→200
4. V1.9: Case quality management (duplicate detection, field integrity checks, level distribution stats)
