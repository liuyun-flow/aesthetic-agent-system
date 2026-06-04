\# Aesthetic Agent System



\## Project goal



Build a developer-version AI agent system that helps the user improve aesthetic judgment.



The system should not simply generate pretty outputs. It should train the user to:

1\. analyze visual work,

2\. compare high vs low aesthetic quality,

3\. critique their own work,

4\. iterate visual direction,

5\. build a long-term aesthetic profile.



\## Runtime model provider



Use DeepSeek API as the primary LLM provider.



Use an OpenAI-compatible client pattern where possible:

\- Base URL: https://api.deepseek.com

\- API key from environment variable: DEEPSEEK\_API\_KEY

\- Default model: deepseek-v4-flash

\- Reasoning / higher-quality model: deepseek-v4-pro



Never hardcode API keys.



\## Initial MVP scope



Backend only. Use FastAPI + SQLite.



Required endpoints:

\- POST /analyze

\- POST /critique

\- POST /iterate

\- GET /profile

\- GET /sessions



Required agents:

\- AnalyzerAgent

\- CriticAgent

\- IteratorAgent

\- ProfileAgent

\- OrchestratorAgent



\## Code standards



\- Python 3.11+

\- Use type hints.

\- Use Pydantic schemas.

\- Keep modules small.

\- Add tests for API endpoints.

\- Add README instructions.

\- Do not introduce heavy dependencies unless necessary.

\- Do not build frontend until backend MVP works.



\## Safety and security



\- Do not commit .env.

\- Do not log raw API keys.

\- Validate user input.

\- Keep all external service credentials in environment variables.

\- Add .env.example.

\- Add clear setup instructions.



\## Commands



Backend setup:

```bash

cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

