"""API endpoint tests — uses mocked agents and in-memory SQLite."""

import io
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
    get_comparator,
    get_critic,
    get_iterator,
    get_profile_agent,
    get_vision_adapter,
)
from app.vision.manual_adapter import ManualAdapter
from app.schemas.responses import (
    AnalyzeResponse,
    CritiqueResponse,
    DimensionScores,
    IterateResponse,
    IterationDirection,
    JudgmentGap,
    ProfileResponse,
    VisionDescription,
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
    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> AnalyzeResponse:
        return MOCK_ANALYZE_RESULT


class MockCriticAgent:
    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> CritiqueResponse:
        return MOCK_CRITIQUE_RESULT
class MockIteratorAgent:
    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> IterateResponse:
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
    def run(
        self,
        work_description: str,
        image_description: str | None = None,
    ) -> AnalyzeResponse:
        raise RuntimeError("secret-token-value should not be exposed")


MOCK_JUDGMENT_GAP = JudgmentGap(
    accurate_judgments=["User correctly noted the typography issue."],
    missed_issues=["User missed the poor color contrast.", "User missed the layout imbalance."],
    misjudgments=["User thought the shadow was too heavy, but AI found it appropriate."],
    commercial_blind_spots=["User did not consider the price band or target audience."],
    aesthetic_blind_spots=["User overlooked the lack of visual hierarchy."],
    next_training_focus=["Practice color contrast audits.", "Define target audience before designing."],
    short_summary="You have a good eye for typography but tend to overlook commercial context. Focus on audience-first design thinking next week.",
)


class MockComparatorAgent:
    def run(self, work_description, user_judgment, ai_result) -> JudgmentGap:
        return MOCK_JUDGMENT_GAP


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
    app.dependency_overrides[get_vision_adapter] = lambda: ManualAdapter()
    app.dependency_overrides[get_comparator] = lambda: MockComparatorAgent()

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


# ── Tests: /upload ───────────────────────────────────────────────────

class TestUploadEndpoint:
    def test_uploads_valid_jpg(self, client):
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        resp = client.post(
            "/upload",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "image_id" in data
        assert data["image_id"] > 0
        assert data["filename"].endswith(".jpg")
        assert "created_at" in data

    def test_uploads_valid_png(self, client):
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        resp = client.post(
            "/upload",
            files={"file": ("photo.png", fake_image, "image/png")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"].endswith(".png")

    def test_uploads_valid_webp(self, client):
        fake_image = io.BytesIO(b"RIFF\x00\x00\x00\x00WEBPVP8L" + b"\x00" * 16)
        resp = client.post(
            "/upload",
            files={"file": ("graphic.webp", fake_image, "image/webp")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"].endswith(".webp")

    def test_rejects_unsupported_extension(self, client):
        fake_image = io.BytesIO(b"not-an-image")
        resp = client.post(
            "/upload",
            files={"file": ("document.pdf", fake_image, "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_rejects_unsupported_content_type(self, client):
        fake_image = io.BytesIO(b"garbage")
        resp = client.post(
            "/upload",
            files={"file": ("fake.jpg", fake_image, "text/html")},
        )
        assert resp.status_code == 400

    def test_rejects_empty_filename(self, client):
        fake_image = io.BytesIO(b"")
        resp = client.post(
            "/upload",
            files={"file": ("", fake_image, "image/jpeg")},
        )
        # FastAPI rejects missing/empty filenames at the framework level
        assert resp.status_code in (400, 422)

    def test_rejects_file_too_large(self, client, monkeypatch):
        # Lower the size limit temporarily for a fast test
        monkeypatch.setattr("app.main._MAX_FILE_SIZE", 10)
        fake_image = io.BytesIO(b"x" * 100)
        resp = client.post(
            "/upload",
            files={"file": ("big.jpg", fake_image, "image/jpeg")},
        )
        assert resp.status_code == 413

    def test_missing_file_field(self, client):
        resp = client.post("/upload")
        assert resp.status_code == 422

    def test_generates_unique_filenames(self, client):
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        names = set()
        for _ in range(3):
            resp = client.post(
                "/upload",
                files={"file": ("img.png", fake_image, "image/png")},
            )
            assert resp.status_code == 201
            names.add(resp.json()["filename"])
        # All three should have unique UUID-based names
        assert len(names) == 3


# ── Tests: Vision adapter & /analyze with image ──────────────────────

class TestManualAdapter:
    def test_returns_hint_verbatim(self):
        adapter = ManualAdapter()
        result = adapter.describe_image(
            "/fake/path.jpg",
            hint="A blue button on a white page.",
        )
        assert result == "A blue button on a white page."

    def test_raises_without_hint(self):
        adapter = ManualAdapter()
        with pytest.raises(ValueError, match="image_description"):
            adapter.describe_image("/fake/path.jpg")


class TestAnalyzeWithImage:
    def test_analyze_with_image_id_and_description(self, client):
        # Upload an image first
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("design.png", fake_img, "image/png")},
        )
        assert upload_resp.status_code == 201
        image_id = upload_resp.json()["image_id"]

        # Analyze with image
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A landing page with a hero section and three cards.",
                "image_id": image_id,
                "image_description": "White background, navy header, three feature cards with icons.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "color" in data
        assert "composition" in data

    def test_analyze_with_image_id_missing_description(self, client):
        # Upload an image
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("photo.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        # Analyze with image_id but no image_description → ManualAdapter raises
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A landing page with a hero section.",
                "image_id": image_id,
            },
        )
        assert resp.status_code == 400

    def test_analyze_with_invalid_image_id(self, client):
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A landing page with a hero section.",
                "image_id": 99999,
                "image_description": "Some description.",
            },
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_analyze_without_image_still_works(self, client):
        """Backward compatibility: no image_id → pure text analysis."""
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A minimalist page with a single CTA button."
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "color" in data


class TestVisionAdapterProtocol:
    def test_cannot_instantiate_abstract(self):
        from app.vision.base import VisionAdapter

        with pytest.raises(TypeError):
            VisionAdapter()  # type: ignore[abstract]

    def test_manual_adapter_is_a_vision_adapter(self):
        from app.vision.base import VisionAdapter

        assert isinstance(ManualAdapter(), VisionAdapter)


# ── V1.1: User judgment & comparator ────────────────────────────────

class TestUserJudgmentFlow:
    """Test the training loop: user_judgment → AI → comparator → gap."""

    def test_critique_with_user_judgment_returns_gap(self, client):
        resp = client.post(
            "/critique",
            json={
                "work_description": "A poster with mismatched fonts and neon colors.",
                "user_judgment": {
                    "score": 60,
                    "strengths": ["Bold color choice"],
                    "weaknesses": ["Too many fonts"],
                    "priority_fixes": ["Reduce to 2 fonts"],
                    "target_audience": "Young adults",
                    "price_band": "Budget",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should still have regular critique fields
        assert "total_score" in data
        assert "dimensions" in data
        # Should also have judgment gap
        assert data.get("judgment_gap") is not None
        gap = data["judgment_gap"]
        assert "accurate_judgments" in gap
        assert "missed_issues" in gap
        assert "short_summary" in gap
        assert len(gap["short_summary"]) > 0

    def test_analyze_with_user_judgment_returns_gap(self, client):
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A minimal blue button on a white page with Helvetica.",
                "user_judgment": {
                    "score": 75,
                    "strengths": ["Clean layout"],
                    "weaknesses": ["Generic color"],
                    "priority_fixes": ["Add a distinctive accent"],
                    "target_audience": "SaaS users",
                    "price_band": "Mid-market",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("judgment_gap") is not None
        gap = data["judgment_gap"]
        assert "commercial_blind_spots" in gap
        assert "aesthetic_blind_spots" in gap
        assert "next_training_focus" in gap

    def test_iterate_with_user_judgment_returns_gap(self, client):
        resp = client.post(
            "/iterate",
            json={
                "work_description": "An e-commerce card with rounded corners and shadow.",
                "user_judgment": {
                    "score": 80,
                    "strengths": ["Good shadow depth"],
                    "weaknesses": ["Rounded corners might feel dated"],
                    "priority_fixes": ["Try sharper corners"],
                    "target_audience": "Online shoppers",
                    "price_band": "Mid-market",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "directions" in data
        assert data.get("judgment_gap") is not None

    def test_no_user_judgment_still_works(self, client):
        """Backward compatibility: no user_judgment → no gap, same result."""
        resp = client.post(
            "/critique",
            json={
                "work_description": "A neon green poster with five fonts."
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_score" in data
        # judgment_gap should be None (omitted from JSON or null)
        assert data.get("judgment_gap") is None


class TestUserJudgmentSessionPersistence:
    def test_session_includes_judgment_fields(self, client):
        client.post(
            "/critique",
            json={
                "work_description": "Session persistence test work description.",
                "user_judgment": {
                    "score": 55,
                    "strengths": ["Good contrast"],
                    "weaknesses": ["Bad font pairing"],
                    "priority_fixes": ["Change fonts"],
                    "target_audience": "Designers",
                    "price_band": "Premium",
                },
            },
        )

        resp = client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        latest = data["sessions"][0]
        assert latest["user_score"] == 55
        assert latest["ai_score"] is not None
        assert latest.get("judgment_gap_summary") is not None
        assert len(latest["judgment_gap_summary"]) > 0

    def test_session_judgment_fields_null_without_user_judgment(self, client):
        client.post(
            "/critique",
            json={
                "work_description": "No judgment test work description here."
            },
        )

        resp = client.get("/sessions")
        data = resp.json()
        latest = data["sessions"][0]
        assert latest["user_score"] is None
        assert latest["judgment_gap_summary"] is None

    def test_profile_includes_judgment_history(self, client):
        # Submit a few records with user_judgment
        for i in range(3):
            client.post(
                "/critique",
                json={
                    "work_description": f"Profile test work number {i} with enough text.",
                    "user_judgment": {
                        "score": 40 + i * 10,
                        "strengths": [f"Strength {i}"],
                        "weaknesses": [f"Weakness {i}"],
                        "priority_fixes": [f"Fix {i}"],
                        "target_audience": "Test",
                        "price_band": "Test",
                    },
                },
            )

        resp = client.get("/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 3
        # Profile should still return sensible text
        assert len(data["preferences"]) > 0
        assert len(data["common_mistakes"]) > 0


# ── V1.3: Image describe endpoint & Vision Adapter ──────────────────

class TestImageDescribeEndpoint:
    def test_describe_existing_image_returns_structured(self, client):
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("photo.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        resp = client.post(f"/images/{image_id}/describe")
        assert resp.status_code == 200
        data = resp.json()
        assert data["image_id"] == image_id
        desc = data["description"]
        assert "summary" in desc
        assert len(desc["summary"]) > 0
        assert "colors" in desc
        assert "suggested_prompt_text" in desc
        assert "style_keywords" in desc

    def test_describe_nonexistent_image_returns_404(self, client):
        resp = client.post("/images/99999/describe")
        assert resp.status_code == 404

    def test_describe_persists_on_image_record(self, client):
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("img.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        client.post(f"/images/{image_id}/describe")

        # Verify image record was updated via a second describe
        resp2 = client.post(f"/images/{image_id}/describe")
        assert resp2.status_code == 200


class TestPlaceholderAdapter:
    def test_returns_mock_description(self):
        from app.vision.placeholder_adapter import PlaceholderAdapter
        adapter = PlaceholderAdapter()
        desc = adapter.describe_image_structured("/fake/path.jpg")
        assert isinstance(desc, VisionDescription)
        assert len(desc.summary) > 0
        assert len(desc.colors) > 0
        assert len(desc.style_keywords) > 0
        assert len(desc.suggested_prompt_text) > 0

    def test_plain_describe_returns_string(self):
        from app.vision.placeholder_adapter import PlaceholderAdapter
        adapter = PlaceholderAdapter()
        text = adapter.describe_image("/fake/path.jpg")
        assert isinstance(text, str)
        assert len(text) > 0


class TestV13BackwardCompat:
    def test_analyze_still_works_with_placeholder_adapter(self, client):
        """Override with PlaceholderAdapter — old endpoints must still work."""
        from app.vision.placeholder_adapter import PlaceholderAdapter
        app.dependency_overrides[get_vision_adapter] = lambda: PlaceholderAdapter()

        resp = client.post(
            "/analyze",
            json={"work_description": "A simple blue button on a white page."},
        )
        assert resp.status_code == 200

    def test_critique_still_works_with_placeholder_adapter(self, client):
        from app.vision.placeholder_adapter import PlaceholderAdapter
        app.dependency_overrides[get_vision_adapter] = lambda: PlaceholderAdapter()

        resp = client.post(
            "/critique",
            json={"work_description": "A neon green poster with five fonts."},
        )
        assert resp.status_code == 200

    def test_iterate_still_works_with_placeholder_adapter(self, client):
        from app.vision.placeholder_adapter import PlaceholderAdapter
        app.dependency_overrides[get_vision_adapter] = lambda: PlaceholderAdapter()

        resp = client.post(
            "/iterate",
            json={"work_description": "An e-commerce card with shadow and rounded corners."},
        )
        assert resp.status_code == 200


# ── V1.4: Reference cases ───────────────────────────────────────────

class TestReferenceCases:
    def test_create_reference_case(self, client):
        resp = client.post(
            "/reference-cases",
            json={
                "title": "Premium SaaS Landing Page",
                "category": "web",
                "aesthetic_level": "high",
                "style_tags": "minimalist, professional, blue",
                "target_audience": "SaaS buyers",
                "price_band": "premium",
                "score": 85,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Premium SaaS Landing Page"
        assert data["aesthetic_level"] == "high"
        assert data["id"] > 0

    def test_list_reference_cases(self, client):
        for i in range(3):
            client.post(
                "/reference-cases",
                json={
                    "title": f"Case {i}",
                    "aesthetic_level": ["high", "medium", "low"][i],
                },
            )
        resp = client.get("/reference-cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3

    def test_filter_by_aesthetic_level(self, client):
        client.post("/reference-cases", json={"title": "High case", "aesthetic_level": "high"})
        client.post("/reference-cases", json={"title": "Low case", "aesthetic_level": "low"})

        resp = client.get("/reference-cases?aesthetic_level=high")
        data = resp.json()
        for c in data["cases"]:
            assert c["aesthetic_level"] == "high"

    def test_get_single_case(self, client):
        created = client.post(
            "/reference-cases",
            json={"title": "Single Case", "aesthetic_level": "medium"},
        )
        case_id = created.json()["id"]

        resp = client.get(f"/reference-cases/{case_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Single Case"

    def test_get_nonexistent_case_404(self, client):
        resp = client.get("/reference-cases/99999")
        assert resp.status_code == 404

    def test_delete_reference_case(self, client):
        created = client.post(
            "/reference-cases",
            json={"title": "To Delete", "aesthetic_level": "low"},
        )
        case_id = created.json()["id"]

        resp = client.delete(f"/reference-cases/{case_id}")
        assert resp.status_code == 204

        resp2 = client.get(f"/reference-cases/{case_id}")
        assert resp2.status_code == 404

    def test_delete_nonexistent_case_404(self, client):
        resp = client.delete("/reference-cases/99999")
        assert resp.status_code == 404


class TestCompareWithReferences:
    def test_compare_no_cases_returns_friendly_message(self, client):
        resp = client.post(
            "/compare-with-references",
            json={
                "user_work_description": "A blue button on a white page.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "No reference cases" in data["training_takeaway"]

    def test_compare_with_cases_returns_structured(self, client):
        # Create a few reference cases
        for level in ["high", "medium", "low"]:
            client.post(
                "/reference-cases",
                json={
                    "title": f"{level.capitalize()} reference",
                    "aesthetic_level": level,
                },
            )

        resp = client.post(
            "/compare-with-references",
            json={
                "user_work_description": "A simple landing page with blue accents.",
                "user_judgment": {
                    "score": 60,
                    "strengths": ["Clean"],
                    "weaknesses": ["Boring"],
                    "priority_fixes": ["Add color"],
                    "target_audience": "Everyone",
                    "price_band": "Mid",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_level_estimate" in data
        assert "key_gaps" in data
        assert "priority_fixes" in data
        assert "training_takeaway" in data
        assert len(data["training_takeaway"]) > 0

    def test_existing_endpoints_still_work(self, client):
        """V1.4 must not break V1.0-V1.3 endpoints."""
        resp = client.post(
            "/analyze",
            json={"work_description": "A simple blue button on white page with Helvetica."},
        )
        assert resp.status_code == 200

        resp2 = client.post(
            "/critique",
            json={"work_description": "A neon poster with five different fonts."},
        )
        assert resp2.status_code == 200


# ── V1.4.1: Generate prompt ─────────────────────────────────────────

class TestPromptGeneration:
    def test_generate_prompt_returns_structured(self, client):
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A minimal blue button on a white page with Helvetica.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "chinese_prompt" in data
        assert "english_prompt" in data
        assert "negative_prompt" in data
        assert "design_notes" in data
        assert isinstance(data["design_notes"], list)
        assert len(data["chinese_prompt"]) > 0
        assert len(data["english_prompt"]) > 0

    def test_generate_prompt_with_full_context(self, client):
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "An e-commerce card with shadow and rounded corners.",
                "image_description": "White card, soft shadow, red price tag.",
                "user_judgment": {"score": 70, "strengths": ["Clean"], "weaknesses": ["Generic"]},
                "target_tool": "midjourney",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["english_prompt"]) > 0

    def test_existing_endpoints_still_pass_after_v141(self, client):
        resp = client.post("/analyze", json={"work_description": "Backward compat test with ten chars."})
        assert resp.status_code == 200
        resp2 = client.post("/critique", json={"work_description": "Critique compat test with ten chars."})
        assert resp2.status_code == 200


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
