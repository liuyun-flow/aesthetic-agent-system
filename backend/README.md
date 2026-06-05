# Aesthetic Training Agent System - Backend MVP

Backend-only MVP for AI-assisted aesthetic judgment training.

Stack: FastAPI, SQLite, SQLAlchemy, Pydantic v2, and the DeepSeek API through an OpenAI-compatible client.

## Requirements

- Python 3.11 or newer
- A DeepSeek API key for live `/analyze`, `/critique`, `/iterate`, and `/profile` calls

Tests use mocked agents and do not require an API key.

## Quickstart

### macOS / Linux

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Edit `.env` and set `DEEPSEEK_API_KEY` before calling the LLM endpoints.

API docs: http://127.0.0.1:8000/docs

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | none | Required for live LLM calls. Never commit this value. |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API endpoint. |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-v4-flash` | Default model for analyze, critique, and iterate calls. |
| `DEEPSEEK_REASONING_MODEL` | `deepseek-v4-pro` | Higher-quality model for profile generation. |
| `DATABASE_URL` | `sqlite:///./aesthetic.db` | SQLite database path. |

`.env` is ignored by git. Keep real credentials in `.env` or environment variables only.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze` | Multi-dimensional aesthetic analysis. |
| `POST` | `/critique` | Structured scored critique with issues and fixes. |
| `POST` | `/iterate` | 3-5 alternative design directions. |
| `POST` | `/upload` | Upload an image (jpg, png, webp). Stores on disk, returns metadata. |
| `GET` | `/profile` | User aesthetic profile summary from saved sessions. |
| `GET` | `/sessions` | Recent training records. Supports `record_type` and `limit`. |
| `GET` | `/health` | Health check. |

`/sessions` accepts `record_type=analyze`, `record_type=critique`, or `record_type=iterate`. `limit` must be between 1 and 200.

`/analyze` also accepts optional `image_id` (from `/upload`) and `image_description`:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "work_description": "A landing page with a hero section.",
    "image_id": 1,
    "image_description": "White background, navy header, three cards with icons."
  }'
```

When `image_id` is provided without `image_description`, the endpoint returns 400 because the default ManualAdapter requires a human-written description. Once a real vision model adapter is plugged in, `image_description` becomes optional.

## Example Requests

### Analyze

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"work_description": "A minimalist landing page with white background, Inter font, a single blue CTA button, and generous whitespace."}'
```

### Critique

```bash
curl -X POST http://127.0.0.1:8000/critique \
  -H "Content-Type: application/json" \
  -d '{"work_description": "A poster with neon green text on a yellow background, five different fonts, and a busy collage of clip art."}'
```

Expected response shape:

```json
{
  "total_score": 7.2,
  "dimensions": {
    "color": 8.0,
    "composition": 7.5,
    "typography": 6.0,
    "material": 7.0,
    "emotion": 7.5,
    "brand_sense": 7.0
  },
  "main_issues": ["Typography lacks hierarchy."],
  "cheapness_sources": ["Generic stock photography lowers perceived quality."],
  "priority_fixes": ["Establish a clear typographic scale."]
}
```

### Iterate

```bash
curl -X POST http://127.0.0.1:8000/iterate \
  -H "Content-Type: application/json" \
  -d '{"work_description": "An e-commerce product card with a shadow effect, rounded corners, and a price tag in red."}'
```

### Upload

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@photo.jpg"
```

Response:

```json
{
  "image_id": 1,
  "filename": "a1b2c3d4e5f6.jpg",
  "created_at": "2026-06-04T12:00:00.000000"
}
```

Supported formats: `jpg`, `jpeg`, `png`, `webp`. Max file size: 10 MiB.  
Files are stored in `backend/data/uploads/` with UUID-based names to avoid collisions.

## Running Tests

```bash
cd backend
py -3.11 -m pytest app/tests/test_api.py -v
```

On macOS or Linux, use `python -m pytest app/tests/test_api.py -v` after activating the virtual environment.

## Architecture

```text
backend/
  app/
    main.py               # FastAPI app, endpoints, dependency wiring
    llm/
      deepseek_client.py  # OpenAI-compatible client for DeepSeek
    agents/
      analyzer.py         # Multi-dimensional aesthetic decomposition
      critic.py           # Scored critique with issues and fixes
      iterator.py         # Divergent design direction generator
      profile.py          # Training history to user profile
      orchestrator.py     # Agent container for future compound workflows
    vision/
      base.py             # VisionAdapter abstract protocol
      manual_adapter.py   # Manual (user-provided) image description
    db/
      database.py         # SQLAlchemy engine and session
      models.py           # TrainingRecord + UploadedImage ORM models
    schemas/
      requests.py         # Pydantic request models
      responses.py        # Pydantic response models
    services/
      session_service.py  # Record persistence and retrieval
    tests/
      test_api.py         # API and agent tests with mocked LLM calls
  data/uploads/           # Uploaded images (git-ignored)
  requirements.txt
  .env.example
  README.md
```

## Vision Adapters

Image understanding is handled by a **pluggable adapter** system. The MVP ships with `ManualAdapter` (user writes the description), leaving a clear extension point for real vision models.

To add a new vision backend:

1. Subclass `VisionAdapter` in `app/vision/`
2. Implement `describe_image(image_path, hint)` → `str`
3. Update `get_vision_adapter()` in `app/main.py` to return your adapter

Planned future adapters:

- `OpenAIVisionAdapter` — calls GPT-4o / GPT-4V
- `ClaudeVisionAdapter` — calls Claude Vision
- `OllamaVisionAdapter` — local vision model via Ollama

## Notes

- The backend creates SQLite tables on startup.
- Saved session records include the request description and structured result JSON.
- LLM errors return safe API errors and do not expose raw exception details.
- If `.env` still contains `your_deepseek_api_key_here`, startup calls that need DeepSeek will fail until you replace it.
