# Aesthetic Training Agent System — Backend MVP

AI-assisted aesthetic judgment training system.  
Backend only (FastAPI + SQLite + DeepSeek API).

## Quickstart

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env with your DeepSeek API key
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | **Required.** Your DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API endpoint |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | Fast model for standard calls |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | High-quality model for profile |
| `DATABASE_URL` | `sqlite:///./aesthetic.db` | SQLite database path |

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze` | Multi-dimensional aesthetic analysis |
| `POST` | `/critique` | Scored critique with issues & fixes |
| `POST` | `/iterate` | 3-5 alternative design directions |
| `GET` | `/profile` | User aesthetic profile summary |
| `GET` | `/sessions` | Recent training records |
| `GET` | `/health` | Health check |

### Example: Analyze

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"work_description": "A minimalist landing page with white background, Inter font, single blue CTA button, and generous whitespace."}'
```

### Example: Critique

```bash
curl -X POST http://127.0.0.1:8000/critique \
  -H "Content-Type: application/json" \
  -d '{"work_description": "A poster with neon green text on a yellow background, 5 different fonts, and a busy collage of clip art."}'
```

### Example: Iterate

```bash
curl -X POST http://127.0.0.1:8000/iterate \
  -H "Content-Type: application/json" \
  -d '{"work_description": "An e-commerce product card with a shadow effect, rounded corners, and a price tag in red."}'
```

## Architecture

```
backend/
  app/
    main.py              # FastAPI app, endpoints, DI wiring
    llm/
      deepseek_client.py  # OpenAI-compatible client for DeepSeek
    agents/
      analyzer.py         # Multi-dimensional aesthetic decomposition
      critic.py           # Scored critique with issues & fixes
      iterator.py         # Divergent design direction generator
      profile.py          # Training history → user profile
      orchestrator.py     # Agent container (future: compound workflows)
    db/
      database.py         # SQLAlchemy engine & session
      models.py           # ORM models (TrainingRecord)
    schemas/
      requests.py         # Pydantic request models
      responses.py        # Pydantic response models
    services/
      session_service.py  # Record persistence & retrieval
    tests/
      test_api.py         # API endpoint tests (mocked agents)
  requirements.txt
  .env.example
  README.md
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest app/tests/test_api.py -v
```

Tests use mocked agents — no API key required.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 + SQLite
- Pydantic v2
- DeepSeek API (OpenAI-compatible client)
