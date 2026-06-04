"""API endpoint tests — uses mocked agents and in-memory SQLite."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.agents.critic import CriticAgent
from app.db.database import Base, get_db
from app.llm.deepseek_client import (
    get_deepseek_client,
    get_default_model,
    get_reasoning_model,
)
from app.main import app
from app.main import (
    get_analyzer,
    get_critic,
    get_iterator,
    get_profile_agent,
)
from app.schemas.responses import (
    AnalyzeResponse,
    CritiqueResponse,
    DimensionScores,
    IterateResponse,
    IterationDirection,
    ProfileResponse,
)
from app.services import session_service

# ── Test database ────────────────────────────────────────────────────

# StaticPool is required for SQLite :memory: so all connections share
# the same in-memory database.
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def make_chat_client(content: str) -> SimpleNamespace:
    """Return a minimal fake OpenAI-compatible client."""
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: completion)
        )
    )


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Mock agent responses ─────────────────────────────────────────────

MOCK_ANALYZE_RESULT = AnalyzeResponse(
    color="The palette uses a restrained monochrome scheme with high contrast.",
    composition="Centered layout with strong focal point and generous negative space.",
    typography="Clean sans-serif with consistent hierarchy across three weights.",
    material="Flat design with subtle shadow depth on interactive elements.",
    emotion="Calm, professional, and trustworthy — evokes a premium SaaS feel.",
    brand_sense="Modern, minimal, and credible. Reads as a mid-to-high-end brand.",
    premium_sources="Consistent spacing, restrained color palette, quality typography.",
    cheapness_sources="Stock-style iconography could undermine the otherwise premium feel.",
    improvement_suggestions="Replace generic icons with custom illustrations; add micro-interactions.",
)

MOCK_CRITIQUE_RESULT = CritiqueResponse(
    total_score=7.2,
    dimensions=DimensionScores(
        color=8.0,
        composition=7.5,
        typography=6.0,
        material=7.0,
        emotion=7.5,
        brand_sense=7.0,
    ),
    main_issues=[
        "Typography lacks hierarchy between headings and body text.",
        "Color contrast is insufficient on secondary buttons.",
        "Overuse of drop shadows creates a dated feel.",
    ],
    cheapness_sources=[
        "Generic stock photography lowers perceived quality.",
        "Inconsistent border-radius values across cards.",
    ],
    priority_fixes=[
        "Establish a clear typographic scale with at least 3 distinct levels.",
        "Increase contrast ratio on secondary CTAs to meet WCAG AA.",
        "Replace stock photos with custom imagery or illustrations.",
    ],
)

MOCK_ITERATE_RESULT = IterateResponse(
    directions=[
        IterationDirection(
            title="Brutalist Raw",
            description="Strip away all decoration. Use raw typography, hard edges, and black/white only. Embrace the unpolished aesthetic.",
            expected_impact="Would create striking distinctiveness and strong brand personality for an edgy audience.",
        ),
        IterationDirection(
            title="Warm Organic",
            description="Introduce warm earth tones, rounded corners, hand-drawn illustrations, and a friendly voice.",
            expected_impact="Would increase approachability and emotional connection for lifestyle/wellness contexts.",
        ),
        IterationDirection(
            title="Data-Driven Precision",
            description="Add data visualizations, metric cards, progress indicators. Emphasize precision and performance.",
            expected_impact="Would build trust for B2B/SaaS audiences who value transparency and measurable results.",
        ),
        IterationDirection(
            title="Immersive Narrative",
            description="Use full-bleed imagery, scroll-triggered animations, and story-driven copy to create a journey.",
            expected_impact="Would increase engagement time and emotional investment for brand-story contexts.",
        ),
    ],
)

MOCK_PROFILE_RESULT = ProfileResponse(
    preferences="You gravitate toward minimalist layouts with restrained color palettes and clean typography. Sans-serif fonts dominate your work.",
    common_mistakes="Typography hierarchy is a recurring weakness — headings and body text blend together. Secondary button contrast often falls below accessibility thresholds.",
    next_week_focus="1) Practice typographic scale exercises (3+ levels per layout). 2) Audit all CTAs for WCAG AA contrast. 3) Experiment with custom iconography instead of stock sets.",
    total_sessions=12,
)


# ── Mock agents (classes that match the real agent interface) ────────

class MockAnalyzerAgent:
    def run(self, work_description: str) -> AnalyzeResponse:
        return MOCK_ANALYZE_RESULT


class MockCriticAgent:
    def run(self, work_description: str) -> CritiqueResponse:
        return MOCK_CRITIQUE_RESULT


class MockIteratorAgent:
    def run(self, work_description: str) -> IterateResponse:
        return MOCK_ITERATE_RESULT


class MockProfileAgent:
    def run(self, history, total_sessions: int) -> ProfileResponse:
        return ProfileResponse(
            preferences=MOCK_PROFILE_RESULT.preferences,
            common_mistakes=MOCK_PROFILE_RESULT.common_mistakes,
            next_week_focus=MOCK_PROFILE_RESULT.next_week_focus,
            total_sessions=total_sessions,
        )


class FailingAnalyzerAgent:
    def run(self, work_description: str) -> AnalyzeResponse:
        raise RuntimeError("secret-token-value should not be exposed")


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_test_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(setup_test_db):
    """Return a TestClient with overridden dependencies.

    Explicitly depends on setup_test_db so tables exist before the app starts.
    """
    # Override the database dependency to use the test engine
    app.dependency_overrides[get_db] = override_get_db
    # Override agent dependencies with mocks (no API key needed)
    app.dependency_overrides[get_analyzer] = lambda: MockAnalyzerAgent()
    app.dependency_overrides[get_critic] = lambda: MockCriticAgent()
    app.dependency_overrides[get_iterator] = lambda: MockIteratorAgent()
    app.dependency_overrides[get_profile_agent] = lambda: MockProfileAgent()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Tests: /analyze ──────────────────────────────────────────────────

class TestAnalyzeEndpoint:
    def test_returns_200_and_valid_structure(self, client):
        resp = client.post(
            "/analyze",
            json={"work_description": "A simple blue button on a white page with Helvetica text."},
        )
        assert resp.status_code == 200
        data = resp.json()
        for key in (
            "color",
            "composition",
            "typography",
            "material",
            "emotion",
            "brand_sense",
            "premium_sources",
            "cheapness_sources",
            "improvement_suggestions",
        ):
            assert key in data
            assert isinstance(data[key], str)
            assert len(data[key]) > 0

    def test_saves_record_to_database(self, client):
        desc = "A dark mode dashboard with neon accents and monospace fonts."
        resp = client.post("/analyze", json={"work_description": desc})
        assert resp.status_code == 200

        # Verify via /sessions
        sessions_resp = client.get("/sessions")
        assert sessions_resp.status_code == 200
        sessions_data = sessions_resp.json()
        assert sessions_data["total"] >= 1
        records = sessions_data["sessions"]
        analyze_records = [r for r in records if r["record_type"] == "analyze"]
        assert len(analyze_records) >= 1
        assert analyze_records[0]["work_description"] == desc

    def test_rejects_short_description(self, client):
        resp = client.post("/analyze", json={"work_description": "short"})
        assert resp.status_code == 422

    def test_rejects_empty_description(self, client):
        resp = client.post("/analyze", json={"work_description": ""})
        assert resp.status_code == 422

    def test_rejects_missing_field(self, client):
        resp = client.post("/analyze", json={})
        assert resp.status_code == 422


# ── Tests: /critique ─────────────────────────────────────────────────

class TestCritiqueEndpoint:
    def test_returns_200_and_valid_structure(self, client):
        resp = client.post(
            "/critique",
            json={"work_description": "A neon green text on yellow background poster with clip art."},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "total_score" in data
        assert 1 <= data["total_score"] <= 10

        dims = data["dimensions"]
        for dim in ("color", "composition", "typography", "material", "emotion", "brand_sense"):
            assert dim in dims
            assert 1 <= dims[dim] <= 10

        assert isinstance(data["main_issues"], list)
        assert isinstance(data["cheapness_sources"], list)
        assert isinstance(data["priority_fixes"], list)
        assert len(data["main_issues"]) > 0
        assert len(data["priority_fixes"]) > 0

    def test_saves_record_to_database(self, client):
        desc = "A poster with 5 different fonts and clashing colors."
        resp = client.post("/critique", json={"work_description": desc})
        assert resp.status_code == 200

        sessions_resp = client.get("/sessions?record_type=critique")
        assert sessions_resp.status_code == 200
        data = sessions_resp.json()
        assert data["total"] >= 1

    def test_rejects_invalid_description(self, client):
        resp = client.post("/critique", json={"work_description": "ab"})
        assert resp.status_code == 422


class TestCriticAgent:
    def test_returns_structured_critique_response(self):
        raw = """
        {
          "total_score": 7.5,
          "dimensions": {
            "color": 8,
            "composition": 7,
            "typography": 7,
            "material": 8,
            "emotion": 7,
            "brand_sense": 8
          },
          "main_issues": ["The hierarchy needs more contrast."],
          "cheapness_sources": [],
          "priority_fixes": ["Increase title/body size contrast."]
        }
        """
        agent = CriticAgent(client=make_chat_client(raw), model="test-model")

        result = agent.run("A clean landing page with restrained palette and simple layout.")

        assert isinstance(result, CritiqueResponse)
        assert result.total_score == 7.5
        assert result.dimensions.color == 8

    def test_rejects_incomplete_structured_json(self):
        raw = """
        {
          "total_score": 7.5,
          "main_issues": ["The hierarchy needs more contrast."],
          "cheapness_sources": [],
          "priority_fixes": ["Increase title/body size contrast."]
        }
        """
        agent = CriticAgent(client=make_chat_client(raw), model="test-model")

        with pytest.raises(ValidationError):
            agent.run("A clean landing page with restrained palette and simple layout.")


# ── Tests: /iterate ──────────────────────────────────────────────────

class TestIterateEndpoint:
    def test_returns_200_and_valid_structure(self, client):
        resp = client.post(
            "/iterate",
            json={"work_description": "An e-commerce product card with rounded corners and a shadow."},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "directions" in data
        assert 1 <= len(data["directions"]) <= 5

        for direction in data["directions"]:
            assert "title" in direction
            assert "description" in direction
            assert "expected_impact" in direction
            assert len(direction["title"]) > 0
            assert len(direction["description"]) > 0

    def test_saves_record_to_database(self, client):
        desc = "A product card with shadow, rounded corners, and red price tag."
        resp = client.post("/iterate", json={"work_description": desc})
        assert resp.status_code == 200

        sessions_resp = client.get("/sessions?record_type=iterate")
        assert sessions_resp.status_code == 200
        data = sessions_resp.json()
        assert data["total"] >= 1

    def test_rejects_short_description(self, client):
        resp = client.post("/iterate", json={"work_description": "x" * 5})
        assert resp.status_code == 422


# ── Tests: /profile ──────────────────────────────────────────────────

class TestProfileEndpoint:
    def test_returns_200_and_valid_structure(self, client):
        # Seed some records first so profile has data to work with
        for i in range(3):
            client.post(
                "/analyze",
                json={"work_description": f"Test work description number {i} with enough length."},
            )

        resp = client.get("/profile")
        assert resp.status_code == 200
        data = resp.json()

        for key in ("preferences", "common_mistakes", "next_week_focus"):
            assert key in data
            assert isinstance(data[key], str)
            assert len(data[key]) > 0

        assert "total_sessions" in data
        assert data["total_sessions"] == 3

    def test_returns_sensible_response_with_no_records(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0

    def test_total_sessions_matches_record_count(self, client):
        # Create exactly 5 records
        for i in range(5):
            client.post(
                "/analyze",
                json={"work_description": f"Profile test work number {i} with enough text."},
            )

        resp = client.get("/profile")
        assert resp.status_code == 200
        assert resp.json()["total_sessions"] == 5


# ── Tests: /sessions ─────────────────────────────────────────────────

class TestSessionsEndpoint:
    def test_returns_empty_list_initially(self, client):
        resp = client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    def test_returns_all_records(self, client):
        client.post("/analyze", json={"work_description": "First test work with enough length."})
        client.post("/critique", json={"work_description": "Second test critique item here."})
        client.post("/iterate", json={"work_description": "Third test iteration input data."})

        resp = client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["sessions"]) == 3

        types = {r["record_type"] for r in data["sessions"]}
        assert types == {"analyze", "critique", "iterate"}

    def test_filters_by_record_type(self, client):
        client.post("/analyze", json={"work_description": "Filter test analyze work description."})
        client.post("/analyze", json={"work_description": "Second analyze for filter testing."})
        client.post("/critique", json={"work_description": "Critique entry for filter testing."})

        resp = client.get("/sessions?record_type=analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for r in data["sessions"]:
            assert r["record_type"] == "analyze"

    def test_respects_limit(self, client):
        for i in range(10):
            client.post(
                "/analyze",
                json={"work_description": f"Limit test work description number {i}."},
            )

        resp = client.get("/sessions?limit=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 3
        assert data["total"] == 3

    def test_rejects_unknown_record_type(self, client):
        resp = client.get("/sessions?record_type=unknown")
        assert resp.status_code == 422

    def test_rejects_limit_outside_allowed_range(self, client):
        too_small = client.get("/sessions?limit=0")
        too_large = client.get("/sessions?limit=201")

        assert too_small.status_code == 422
        assert too_large.status_code == 422

    def test_session_record_has_required_fields(self, client):
        client.post("/analyze", json={"work_description": "Field check test work description."})

        resp = client.get("/sessions")
        assert resp.status_code == 200
        record = resp.json()["sessions"][0]

        assert "id" in record
        assert "record_type" in record
        assert "work_description" in record
        assert "created_at" in record


# ── Tests: /health ───────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestDeepSeekClient:
    def test_rejects_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        with pytest.raises(ValueError):
            get_deepseek_client()

    def test_rejects_placeholder_api_key(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "your_deepseek_api_key_here")

        with pytest.raises(ValueError):
            get_deepseek_client()

    def test_reads_model_names_at_call_time(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_DEFAULT_MODEL", "custom-default-model")
        monkeypatch.setenv("DEEPSEEK_REASONING_MODEL", "custom-reasoning-model")

        assert get_default_model() == "custom-default-model"
        assert get_reasoning_model() == "custom-reasoning-model"


# ── Tests: Cross-cutting ────────────────────────────────────────────

class TestCrossCutting:
    def test_records_persist_across_requests(self, client):
        """Verify that multiple requests all save and are retrievable."""
        client.post("/analyze", json={"work_description": "Cross-cut test one with enough text."})
        client.post("/critique", json={"work_description": "Cross-cut test two with enough text."})

        sessions_resp = client.get("/sessions")
        assert sessions_resp.status_code == 200
        assert sessions_resp.json()["total"] == 2

        # Add one more
        client.post("/iterate", json={"work_description": "Cross-cut test three with enough text."})

        sessions_resp = client.get("/sessions")
        assert sessions_resp.status_code == 200
        assert sessions_resp.json()["total"] == 3

    def test_different_record_types_independent(self, client):
        """Verify each endpoint saves the correct type."""
        client.post("/analyze", json={"work_description": "Type independence test for analyze."})
        client.post("/critique", json={"work_description": "Type independence test for critique."})

        for rtype in ("analyze", "critique"):
            resp = client.get(f"/sessions?record_type={rtype}")
            assert resp.json()["total"] == 1
            assert resp.json()["sessions"][0]["record_type"] == rtype

    def test_llm_error_response_does_not_leak_exception_details(self, client):
        app.dependency_overrides[get_analyzer] = lambda: FailingAnalyzerAgent()

        resp = client.post(
            "/analyze",
            json={"work_description": "A valid description that triggers a mocked failure."},
        )

        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail == "LLM analysis failed. Please try again later."
        assert "secret-token-value" not in detail

    def test_profile_history_includes_saved_result_json(self, client):
        resp = client.post(
            "/critique",
            json={"work_description": "A poster with weak hierarchy and uneven spacing."},
        )
        assert resp.status_code == 200

        db = TestSessionLocal()
        try:
            history = session_service.get_history_for_profile(db)
        finally:
            db.close()

        assert history[0]["type"] == "critique"
        assert history[0]["result"]["total_score"] == MOCK_CRITIQUE_RESULT.total_score
