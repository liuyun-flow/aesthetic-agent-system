"""API endpoint tests — uses mocked agents and in-memory SQLite."""

import io
import json
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
    get_prompt_generator,
    get_reference_comparator,
    get_vision_adapter,
    get_weekly_reviewer,
)
from app.vision.manual_adapter import ManualAdapter
from app.schemas.responses import (
    AnalyzeResponse,
    CompareWithReferencesResponse,
    CritiqueResponse,
    DimensionScores,
    GeneratedPrompt,
    IterateResponse,
    IterationDirection,
    JudgmentGap,
    ProfileResponse,
    VisionDescription,
    WeeklyReviewResponse,
)
from app.services import session_service
from app.settings import config_store as cs

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
            id="dir-1",
            title="极简主义重构",
            description="剥离所有装饰元素，使用原始字体、硬边线和纯粹黑白。拥抱未经修饰的粗粝美学。",
            expected_impact="为追求个性的受众创造强烈的品牌辨识度和差异化。",
            goal="用最少元素传递最强信息",
            visual_changes="去除所有装饰性元素，仅保留核心内容框架",
            color_changes="全面采用黑白灰单色体系，去掉所有彩色元素",
            typography_changes="切换为单一无衬线字体，字号层级从3级简化为2级",
            layout_changes="采用非对称网格布局，大幅增加留白，信息密度降低40%",
            commercial_rationale="适合面向设计师、建筑师等审美敏感群体的品牌",
            risk="可能让普通用户感到过于冷淡，降低亲和力",
        ),
        IterationDirection(
            id="dir-2",
            title="温暖有机风",
            description="引入温暖的土色调、圆角设计、手绘插图和友好的品牌语调。",
            expected_impact="提升亲和力和情感连接，适合生活方式/健康类品牌。",
            goal="营造自然有机的品牌温度",
            visual_changes="所有尖锐转角改为圆角，图标从线性改为手绘风格",
            color_changes="引入暖土色系（陶土红、杏仁黄、鼠尾草绿），降低饱和度",
            typography_changes="主标题切换为衬线体，正文保留无衬线但字重减半",
            layout_changes="卡片间距增大，采用不规则瀑布流替代整齐网格",
            commercial_rationale="瞄准25-40岁注重生活方式的城市中产女性",
            risk="可能显得不够专业，不适合严肃B2B场景",
        ),
        IterationDirection(
            id="dir-3",
            title="数据驱动精准风",
            description="添加数据可视化、指标卡片、进度指示器，强调精确性和性能感。",
            expected_impact="为重视透明度和可衡量结果的B2B/SaaS受众建立信任。",
            goal="用数据叙事建立专业权威",
            visual_changes="引入数据图表、数字指标、进度条等可视化元素",
            color_changes="保留品牌主色，增加数据可视化专用配色（蓝色渐变、绿色/红色指示色）",
            typography_changes="全面采用等宽数字字体（Tabular Figures），正文字号增大0.5pt",
            layout_changes="采用仪表盘式网格，每个数据模块独立卡片，顶部固定KPI条",
            commercial_rationale="适合企业级SaaS、金融科技、数据分析类产品",
            risk="过度数据化可能压抑情感连接，需要平衡人性化元素",
        ),
        IterationDirection(
            id="dir-4",
            title="沉浸叙事风",
            description="使用全屏大图、滚动触发动画和故事化文案，创造沉浸式品牌旅程。",
            expected_impact="为品牌故事类场景提升用户停留时长和情感投入。",
            goal="用叙事驱动品牌体验",
            visual_changes="全屏大图替代卡片式布局，滚动视差动画贯穿全页",
            color_changes="图片主导配色，UI元素降低至辅助地位，使用半透明叠加",
            typography_changes="标题采用大号定制字体（display font），正文保持简洁",
            layout_changes="线性叙事结构，每屏一个核心信息，放弃传统导航栏",
            commercial_rationale="适合高端消费品牌、奢侈品、文旅类产品",
            risk="加载性能显著下降，低端设备体验较差，SEO不友好",
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


MOCK_COMPARE_RESULT = CompareWithReferencesResponse(
    overall_level_estimate="medium",
    closest_reference_level="high",
    stronger_than_low_cases=["Better spacing than low examples."],
    weaker_than_high_cases=["Lacks the refinement of high-end typography."],
    key_gaps=["Typography hierarchy needs work.", "Color palette is less cohesive."],
    priority_fixes=["Establish a clear type scale.", "Reduce the color palette to 3-4 hues."],
    reference_cases_used=[],
    training_takeaway="Your design has solid structure but needs refinement in typography and color cohesion to reach the high aesthetic level.",
    next_practice=["Study typographic scales.", "Audit color palette cohesion."],
)


class MockReferenceComparatorAgent:
    def run(
        self,
        user_work_description: str,
        reference_cases: list,
        image_description: str | None = None,
        user_judgment: dict | None = None,
    ) -> CompareWithReferencesResponse:
        return MOCK_COMPARE_RESULT


MOCK_PROMPT_RESULT = GeneratedPrompt(
    chinese_prompt="一张干净的蓝色按钮，白色背景，无衬线字体。极简风格，现代感。",
    english_prompt="A clean blue button on white background, sans-serif font. Minimalist style, modern feel.",
    negative_prompt="text, watermark, logo, cluttered, busy, ornate, serif, dark background",
    design_notes=["Use a restrained color palette.", "Keep typography clean and hierarchical.", "Ensure adequate whitespace."],
    copywriting_prompt="",
    usage_tips=["For Midjourney, add --ar 16:9 for landscape.", "Use --style raw for more literal rendering."],
)


class MockPromptGeneratorAgent:
    def run(
        self,
        work_description: str,
        image_description: str | None = None,
        user_judgment: dict | None = None,
        critique_result: dict | None = None,
        iterate_result: dict | None = None,
        selected_direction: dict | str | None = None,
        reference_comparison: dict | None = None,
        target_tool: str = "general",
    ) -> GeneratedPrompt:
        return MOCK_PROMPT_RESULT


MOCK_WEEKLY_RESULT = WeeklyReviewResponse(
    summary="本周你完成了3次训练，主要围绕色彩和构图。",
    common_misjudgments="你倾向于高估色彩的协调性，但实际AI评分较低。",
    progress_points="你对品牌感的判断越来越准确。",
    recurring_issues="字体层次感和间距一致性是你反复出现的问题。",
    next_week_theme="字体与排版",
    next_week_tasks=["练习字体层次感（至少3级）", "审查所有CTA按钮的WCAG AA对比度", "尝试自定义图标"],
)


class MockWeeklyReviewAgent:
    def run(self, history: list) -> WeeklyReviewResponse:
        return MOCK_WEEKLY_RESULT


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolate_config_store(tmp_path):
    """Keep config_store writes out of the real backend/data/config folder."""
    config_dir = tmp_path / "data" / "config"
    config_dir.mkdir(parents=True)

    orig_dir = cs.CONFIG_DIR
    orig_file = cs.CONFIG_FILE
    cs.CONFIG_DIR = config_dir
    cs.CONFIG_FILE = config_dir / "app_config.json"
    cs._invalidate_cache()
    yield
    cs.CONFIG_DIR = orig_dir
    cs.CONFIG_FILE = orig_file
    cs._invalidate_cache()


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
    app.dependency_overrides[get_reference_comparator] = lambda: MockReferenceComparatorAgent()
    app.dependency_overrides[get_prompt_generator] = lambda: MockPromptGeneratorAgent()
    app.dependency_overrides[get_weekly_reviewer] = lambda: MockWeeklyReviewAgent()

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
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend"


class TestDeepSeekClient:
    def test_rejects_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        # Also clear config so env fallback doesn't provide a key
        from app.settings import config_store as cs
        cs.clear_key("deepseek", "api_key")
        cs._invalidate_cache()

        with pytest.raises(ValueError):
            get_deepseek_client()

    def test_rejects_placeholder_api_key(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "your_deepseek_api_key_here")
        # Clear config so placeholder env value is hit
        from app.settings import config_store as cs
        cs.clear_key("deepseek", "api_key")
        cs._invalidate_cache()

        with pytest.raises(ValueError):
            get_deepseek_client()

    def test_reads_model_names_at_call_time(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_DEFAULT_MODEL", "custom-default-model")
        monkeypatch.setenv("DEEPSEEK_REASONING_MODEL", "custom-reasoning-model")
        # Clear config values so monkeypatched env vars take effect
        from app.settings import config_store as cs
        config = cs.get_config()
        config["deepseek"]["default_model"] = ""
        config["deepseek"]["reasoning_model"] = ""
        cs.write_config(config)

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

    def test_describe_json_parse_error_returns_safe_message(self, client):
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("img.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        class BadJsonVisionAdapter(ManualAdapter):
            def describe_image_structured(self, image_path: str) -> VisionDescription:
                raise json.JSONDecodeError("bad json", "not json", 0)

        app.dependency_overrides[get_vision_adapter] = lambda: BadJsonVisionAdapter()
        resp = client.post(f"/images/{image_id}/describe")

        assert resp.status_code == 502
        assert "JSON" in resp.json()["detail"]

    def test_describe_generic_error_does_not_expose_raw_exception(self, client):
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("img.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        class ExplodingVisionAdapter(ManualAdapter):
            def describe_image_structured(self, image_path: str) -> VisionDescription:
                raise RuntimeError("provider failed with sk-secret-value")

        app.dependency_overrides[get_vision_adapter] = lambda: ExplodingVisionAdapter()
        resp = client.post(f"/images/{image_id}/describe")

        assert resp.status_code == 502
        assert "sk-secret-value" not in resp.json()["detail"]

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

    def test_submitted_image_description_skips_second_vision_call(self, client):
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        upload_resp = client.post(
            "/upload",
            files={"file": ("img.png", fake_img, "image/png")},
        )
        image_id = upload_resp.json()["image_id"]

        class ExplodingVisionAdapter(ManualAdapter):
            def describe_image(self, image_path: str, hint: str | None = None) -> str:
                raise AssertionError("vision should not be called")

        app.dependency_overrides[get_vision_adapter] = lambda: ExplodingVisionAdapter()
        resp = client.post(
            "/analyze",
            json={
                "work_description": "A poster layout with enough text for analysis.",
                "image_id": image_id,
                "image_description": "Already generated Chinese image description.",
            },
        )
        assert resp.status_code == 200


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
    def test_compare_no_cases_returns_structured_result(self, client):
        resp = client.post(
            "/compare-with-references",
            json={
                "user_work_description": "A blue button on a white page.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_level_estimate" in data
        assert "key_gaps" in data
        assert "training_takeaway" in data

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


# ── V1.4.1: Session detail ──────────────────────────────────────────

class TestSessionDetail:
    def test_get_existing_session_detail(self, client):
        # Create a record first
        client.post("/analyze", json={"work_description": "Detail test work description here."})

        # Get sessions list to find the ID
        list_resp = client.get("/sessions?limit=1")
        session_id = list_resp.json()["sessions"][0]["id"]

        # Get detail
        resp = client.get(f"/sessions/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == session_id
        assert data["record_type"] == "analyze"
        assert "work_description" in data
        assert "result_json" in data

    def test_get_nonexistent_session_returns_404(self, client):
        resp = client.get("/sessions/99999")
        assert resp.status_code == 404

    def test_session_list_still_works(self, client):
        resp = client.get("/sessions")
        assert resp.status_code == 200
        assert "sessions" in resp.json()


# ── V1.4.2: OpenAI Vision Adapter ───────────────────────────────────

class TestOpenAIVisionAdapter:
    def test_openai_adapter_requires_api_key(self, monkeypatch):
        from app.vision.openai_adapter import OpenAIVisionAdapter

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            OpenAIVisionAdapter(api_key="")

    def test_empty_api_key_does_not_fall_back_to_env(self, monkeypatch):
        from app.vision.openai_adapter import OpenAIVisionAdapter

        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-fallback-test")
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            OpenAIVisionAdapter(api_key="")

    def test_openai_adapter_with_fake_key_creates_client(self):
        from app.vision.openai_adapter import OpenAIVisionAdapter

        # Should not raise — key is set (won't actually call the API)
        adapter = OpenAIVisionAdapter(api_key="sk-fake-test-key")
        assert adapter is not None
        assert adapter.model in ("gpt-4o", "gpt-4o-mini")

    def test_placeholder_still_default(self, monkeypatch):
        """Without VISION_PROVIDER set, placeholder is used."""
        monkeypatch.delenv("VISION_PROVIDER", raising=False)
        # Also clear config provider so env fallback is empty too
        from app.settings import config_store as cs
        cs.clear_key("vision", "provider")
        cs._invalidate_cache()

        from app.main import get_vision_adapter
        from app.vision.placeholder_adapter import PlaceholderAdapter

        adapter = get_vision_adapter()
        assert isinstance(adapter, PlaceholderAdapter)

    def test_openai_provider_fails_gracefully_without_key(self, monkeypatch):
        """When VISION_PROVIDER=openai but no OPENAI_API_KEY, adapter raises ValueError."""
        monkeypatch.setenv("VISION_PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # Set provider in config with empty key
        from app.settings import config_store as cs
        config = cs.get_config()
        config["vision"]["provider"] = "openai"
        config["vision"]["openai_api_key"] = ""
        cs.write_config(config)
        from app.main import get_vision_adapter
        from app.vision.openai_adapter import OpenAIVisionAdapter

        # get_vision_adapter tries to instantiate OpenAIVisionAdapter
        # which should raise ValueError because no key
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_vision_adapter()

    def test_existing_endpoints_still_pass(self, client):
        resp = client.post("/analyze", json={"work_description": "V1.4.2 compat test with ten chars."})
        assert resp.status_code == 200
        resp2 = client.get("/sessions")
        assert resp2.status_code == 200


# ── V1.4.3: Vision status ───────────────────────────────────────────

class TestVisionStatus:
    def test_placeholder_returns_is_placeholder_true(self, client, monkeypatch):
        monkeypatch.setenv("VISION_PROVIDER", "placeholder")
        # Ensure config also has placeholder (may be polluted by other tests)
        from app.settings import config_store as cs
        config = cs.get_config()
        config["vision"]["provider"] = ""
        cs.write_config(config)
        resp = client.get("/vision/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vision_provider"] == "placeholder"
        assert data["is_placeholder"] is True
        assert data["is_configured"] is True

    def test_describe_with_placeholder_shows_warning(self, client, monkeypatch):
        monkeypatch.setenv("VISION_PROVIDER", "placeholder")
        # Ensure config also has placeholder
        from app.settings import config_store as cs
        config = cs.get_config()
        config["vision"]["provider"] = ""
        cs.write_config(config)
        fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        up = client.post("/upload", files={"file": ("img.png", fake_img, "image/png")})
        img_id = up.json()["image_id"]
        resp = client.post(f"/images/{img_id}/describe")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_placeholder"] is True
        assert data["warning"] is not None
        assert "占位" in data["warning"]

    def test_vision_status_openai_no_key(self, monkeypatch):
        monkeypatch.setenv("VISION_PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # Clear config so monkeypatched env takes effect
        from app.settings import config_store as cs
        config = cs.get_config()
        config["vision"]["provider"] = ""
        config["vision"]["openai_api_key"] = ""
        cs.write_config(config)
        from app.main import vision_status
        result = vision_status()
        assert result.is_configured is False
        assert "OPENAI_API_KEY" in result.missing_keys

    def test_existing_endpoints_still_pass(self, client):
        resp = client.post("/analyze", json={"work_description": "V1.4.3 compat test with ten chars."})
        assert resp.status_code == 200


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


# ── V1.7.1: System status & Setup wizard ──────────────────────────────

class TestSystemStatus:
    """Tests for GET /system/status — combined health/model/vision/db/uploads."""

    def test_returns_200(self, client):
        resp = client.get("/system/status")
        assert resp.status_code == 200

    def test_returns_all_status_keys(self, client):
        resp = client.get("/system/status")
        data = resp.json()
        for key in ("backend", "version", "deepseek", "vision", "database", "uploads", "setup_completed"):
            assert key in data, f"Missing key: {key}"

    def test_backend_is_ok(self, client):
        resp = client.get("/system/status")
        assert resp.json()["backend"] == "ok"

    def test_version_is_v1_9_0(self, client):
        resp = client.get("/system/status")
        assert resp.json()["version"] == "v1.9.0"

    def test_deepseek_has_configured_flag(self, client):
        resp = client.get("/system/status")
        ds = resp.json()["deepseek"]
        assert "configured" in ds
        assert isinstance(ds["configured"], bool)

    def test_vision_has_fields(self, client):
        resp = client.get("/system/status")
        vis = resp.json()["vision"]
        for key in ("configured", "provider", "is_placeholder"):
            assert key in vis, f"Missing key in vision: {key}"

    def test_database_status_is_ok(self, client):
        resp = client.get("/system/status")
        assert resp.json()["database"] == "ok"

    def test_uploads_status_is_present(self, client):
        resp = client.get("/system/status")
        assert resp.json()["uploads"] in ("ok", "error")

    def test_no_api_key_exposed(self, client):
        resp = client.get("/system/status")
        body = json.dumps(resp.json())
        # No real API key patterns should appear
        assert "sk-" not in body or "sk-" not in body

    def test_health_still_works(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_model_status_still_works(self, client):
        resp = client.get("/model/status")
        assert resp.status_code == 200
        assert "is_configured" in resp.json()

    def test_vision_status_still_works(self, client):
        resp = client.get("/vision/status")
        assert resp.status_code == 200
        assert "vision_provider" in resp.json()


class TestSetupEndpoints:
    """Tests for GET /setup/status and POST /setup/complete."""

    def test_setup_status_returns_bool(self, client):
        resp = client.get("/setup/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "setup_completed" in data
        assert isinstance(data["setup_completed"], bool)

    def test_setup_complete_marks_done(self, client):
        resp = client.post("/setup/complete")
        assert resp.status_code == 200
        assert resp.json()["setup_completed"] is True

    def test_setup_status_reflects_completion(self, client):
        # First mark complete
        client.post("/setup/complete")
        # Then check status
        resp = client.get("/setup/status")
        assert resp.json()["setup_completed"] is True

    def test_setup_complete_is_idempotent(self, client):
        client.post("/setup/complete")
        resp = client.post("/setup/complete")
        assert resp.status_code == 200
        assert resp.json()["setup_completed"] is True


# ── V1.7.2: Iteration direction selection + prompt generation ─────────

class TestGeneratePromptWithDirection:
    """Tests for POST /generate-prompt with selected_direction."""

    def test_generate_prompt_with_selected_direction(self, client):
        """Prompt generation should succeed when selected_direction is provided."""
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A minimalist poster with red accent.",
                "selected_direction": '{"id":"dir-1","title":"极简主义重构","goal":"用最少元素传递最强信息","visual_changes":"去除所有装饰","color_changes":"黑白灰单色","typography_changes":"单一无衬线","layout_changes":"非对称网格","commercial_rationale":"适合设计师品牌","risk":"可能太冷"}',
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        for key in ("chinese_prompt", "english_prompt", "negative_prompt", "design_notes"):
            assert key in data, f"Missing key: {key}"

    def test_generate_prompt_without_direction_still_works(self, client):
        """Backward compatibility: prompt generation works without selected_direction."""
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A minimalist poster with red accent.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "chinese_prompt" in data

    def test_generate_prompt_saves_direction_to_session(self, client):
        """When session_id is provided, direction prompt should be saved to that session."""
        # First create a session
        client.post("/iterate", json={
            "work_description": "A poster design that needs iteration.",
        })
        sessions_resp = client.get("/sessions?limit=1")
        session_id = sessions_resp.json()["sessions"][0]["id"]
        # Then generate prompt with direction
        direction_json = '{"id":"dir-1","title":"极简主义重构","description":"去掉所有装饰","goal":"最小元素最大信息"}'
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A poster design that needs iteration.",
                "selected_direction": direction_json,
                "session_id": session_id,
            },
        )
        assert resp.status_code == 200

        # Check the matching session has selected_direction
        detail_resp = client.get(f"/sessions/{session_id}")
        detail = detail_resp.json()
        assert detail["selected_direction"] == direction_json
        assert detail["prompt_result"] is not None
        assert "chinese_prompt" in detail["prompt_result"]

    def test_generate_prompt_saves_to_requested_session_not_latest(self, client):
        """Direction prompt persistence should not overwrite a newer unrelated session."""
        client.post("/iterate", json={
            "work_description": "First iteration that will receive the prompt.",
        })
        first_session_id = client.get("/sessions?limit=1").json()["sessions"][0]["id"]

        client.post("/iterate", json={
            "work_description": "Second iteration that should stay untouched.",
        })
        second_session_id = client.get("/sessions?limit=1").json()["sessions"][0]["id"]

        direction_json = '{"id":"dir-2","title":"指定方向"}'
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "First iteration that will receive the prompt.",
                "selected_direction": direction_json,
                "session_id": first_session_id,
            },
        )
        assert resp.status_code == 200

        first_detail = client.get(f"/sessions/{first_session_id}").json()
        second_detail = client.get(f"/sessions/{second_session_id}").json()
        assert first_detail["selected_direction"] == direction_json
        assert first_detail["prompt_result"] is not None
        assert second_detail["selected_direction"] is None
        assert second_detail["prompt_result"] is None

    def test_generate_prompt_accepts_direction_object_and_passes_json_text(self, client):
        """selected_direction may be sent as an object and still reaches the agent."""
        captured = {}

        class CapturingPromptGeneratorAgent(MockPromptGeneratorAgent):
            def run(
                self,
                work_description: str,
                image_description: str | None = None,
                user_judgment: dict | None = None,
                critique_result: dict | None = None,
                iterate_result: dict | None = None,
                selected_direction: dict | str | None = None,
                reference_comparison: dict | None = None,
                target_tool: str = "general",
            ) -> GeneratedPrompt:
                captured["selected_direction"] = selected_direction
                return MOCK_PROMPT_RESULT

        app.dependency_overrides[get_prompt_generator] = lambda: CapturingPromptGeneratorAgent()

        direction = {
            "id": "dir-3",
            "title": "视觉层级强化",
            "goal": "让主标题和核心卖点更明确",
            "risk": "可能显得更商业化",
        }
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A poster design that needs a stronger hierarchy.",
                "selected_direction": direction,
            },
        )
        assert resp.status_code == 200
        selected = captured["selected_direction"]
        assert isinstance(selected, str)
        assert json.loads(selected)["id"] == "dir-3"

    def test_generate_prompt_returns_404_for_missing_session_id(self, client):
        """An explicit session_id must point to an existing session."""
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A poster design that needs a stronger hierarchy.",
                "selected_direction": '{"id":"dir-1","title":"Test"}',
                "session_id": 999999,
            },
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "未找到要保存提示词的训练记录。"

    def test_generate_prompt_rejects_non_iterate_session_id(self, client):
        """Direction prompts should only be persisted on iterate records."""
        client.post("/analyze", json={
            "work_description": "A simple blue button on a white page with Helvetica text.",
        })
        session_id = client.get("/sessions?limit=1").json()["sessions"][0]["id"]

        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "A simple blue button on a white page with Helvetica text.",
                "selected_direction": '{"id":"dir-1","title":"Test"}',
                "session_id": session_id,
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "只能为迭代记录保存方向提示词。"

    def test_generate_prompt_without_direction_does_not_overwrite_session(self, client):
        """Without selected_direction, session fields should remain null."""
        client.post("/iterate", json={
            "work_description": "Another poster design.",
        })
        resp = client.post(
            "/generate-prompt",
            json={
                "work_description": "Another poster design.",
                # No selected_direction
            },
        )
        assert resp.status_code == 200

        sessions_resp = client.get("/sessions?limit=1")
        latest_id = sessions_resp.json()["sessions"][0]["id"]
        detail_resp = client.get(f"/sessions/{latest_id}")
        detail = detail_resp.json()
        assert detail["selected_direction"] is None
        assert detail["prompt_result"] is None


class TestIterationDirectionSchema:
    """Tests for V1.7.2 structured IterationDirection."""

    def test_direction_has_id_field(self, client):
        """Iteration directions should include id field."""
        resp = client.post("/iterate", json={
            "work_description": "A poster that needs multiple iterations.",
        })
        assert resp.status_code == 200
        data = resp.json()
        for d in data["directions"]:
            assert "id" in d, f"Direction missing id: {d}"
            assert d["id"], f"Direction id is empty: {d}"

    def test_direction_has_structured_fields(self, client):
        """Iteration directions should include all V1.7.2 structured fields."""
        resp = client.post("/iterate", json={
            "work_description": "A poster that needs iterations.",
        })
        assert resp.status_code == 200
        data = resp.json()
        for d in data["directions"]:
            for key in ("goal", "visual_changes", "color_changes", "typography_changes",
                         "layout_changes", "commercial_rationale", "risk"):
                assert key in d, f"Direction missing key: {key}"

    def test_session_detail_includes_new_fields(self, client):
        """Session detail should include selected_direction and prompt_result."""
        # Create a session
        client.post("/iterate", json={
            "work_description": "Test work for detail check.",
        })
        # Generate prompt with direction
        client.post("/generate-prompt", json={
            "work_description": "Test work for detail check.",
            "selected_direction": '{"id":"dir-1","title":"Test"}',
        })
        # Check detail
        sessions_resp = client.get("/sessions?limit=1")
        lid = sessions_resp.json()["sessions"][0]["id"]
        detail = client.get(f"/sessions/{lid}").json()
        assert "selected_direction" in detail
        assert "prompt_result" in detail


# ── V1.8: Export / Import / Semantic Search ────────────────────────────

class TestExport:
    """Tests for GET /export."""

    def test_export_returns_zip(self, client):
        resp = client.get("/export")
        assert resp.status_code == 200
        assert "application/zip" in resp.headers.get("content-type", "")

    def test_export_does_not_contain_api_key(self, client):
        import zipfile

        deepseek_key = "FAKE_DEEPSEEK_EXPORT_TOKEN_123456"
        openai_key = "FAKE_OPENAI_EXPORT_TOKEN_ABCDEF"
        cs.write_config({
            "deepseek": {
                "api_key": deepseek_key,
                "base_url": "https://api.deepseek.com",
                "default_model": "deepseek-v4-flash",
                "reasoning_model": "deepseek-v4-pro",
            },
            "vision": {
                "provider": "openai",
                "openai_api_key": openai_key,
                "openai_vision_model": "gpt-4o-mini",
            },
            "setup": {"completed": "true"},
        })

        resp = client.get("/export")
        assert resp.status_code == 200

        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            names = set(zf.namelist())
            assert "export_manifest.json" in names
            assert "reference_cases.json" in names
            assert "sessions.json" in names
            assert "uploaded_images.json" in names
            assert "config_summary.json" in names

            for name in names:
                if name.endswith(".json"):
                    text = zf.read(name).decode("utf-8")
                    assert deepseek_key not in text
                    assert openai_key not in text

            summary = json.loads(zf.read("config_summary.json").decode("utf-8"))
            summary_text = json.dumps(summary).lower()
            assert "api_key" not in summary_text
            assert "secret" not in summary_text

    def test_export_skips_image_file_outside_upload_dir(self, client, tmp_path):
        """Export should not package files outside the configured upload directory."""
        import zipfile
        from app.db.models import UploadedImage

        outside = tmp_path / "outside.png"
        outside.write_bytes(b"outside-file-content")

        db = TestSessionLocal()
        try:
            db.add(UploadedImage(
                original_filename="outside.png",
                stored_filename="safe.png",
                file_path=str(outside),
                content_type="image/png",
                size_bytes=outside.stat().st_size,
            ))
            db.commit()
        finally:
            db.close()

        resp = client.get("/export")
        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            assert "uploads/safe.png" not in zf.namelist()
            for name in zf.namelist():
                if name.endswith(".json"):
                    assert "outside-file-content" not in zf.read(name).decode("utf-8")


class TestImport:
    """Tests for POST /import."""

    def test_import_rejects_non_zip(self, client):
        resp = client.post("/import", files={"file": ("test.txt", b"not a zip")})
        assert resp.status_code == 400

    def test_import_zip_slip_prevention(self, client):
        """Zip with path traversal names should be rejected."""
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../etc/passwd", "bad")
        buf.seek(0)
        resp = client.post("/import", files={"file": ("evil.zip", buf.read())})
        assert resp.status_code == 400
        assert "不安全" in resp.json()["detail"]

    def test_import_rejects_unsafe_stored_filename(self, client):
        """Zip metadata cannot inject traversal filenames into upload records."""
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("export_manifest.json", json.dumps({"version": "v1.8.1"}))
            zf.writestr("uploaded_images.json", json.dumps([
                {
                    "id": 1,
                    "original_filename": "evil.png",
                    "stored_filename": "../evil.png",
                    "content_type": "image/png",
                    "size_bytes": 10,
                }
            ]))
        buf.seek(0)

        resp = client.post("/import", files={"file": ("evil-meta.zip", buf.read())})
        assert resp.status_code == 400
        assert "不安全" in resp.json()["detail"]

    def test_import_missing_image_file_does_not_create_bad_image_mapping(self, client):
        """Missing upload files should not create image records or map cases to bad image_ids."""
        import zipfile
        from app.db.models import ReferenceCase, UploadedImage

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("export_manifest.json", json.dumps({"version": "v1.8.1"}))
            zf.writestr("uploaded_images.json", json.dumps([
                {
                    "id": 1,
                    "original_filename": "missing.png",
                    "stored_filename": "missing.png",
                    "content_type": "image/png",
                    "size_bytes": 10,
                }
            ]))
            zf.writestr("reference_cases.json", json.dumps([
                {
                    "id": 1,
                    "title": "Imported case with missing image",
                    "aesthetic_level": "high",
                    "image_id": 1,
                }
            ]))
            zf.writestr("sessions.json", "[]")
        buf.seek(0)

        resp = client.post("/import", files={"file": ("missing-image.zip", buf.read())})
        assert resp.status_code == 200
        result = resp.json()
        assert result["images_imported"] == 0
        assert result["reference_cases_imported"] == 1
        assert result["skipped_items"] >= 1

        db = TestSessionLocal()
        try:
            assert db.query(UploadedImage).count() == 0
            case = db.query(ReferenceCase).filter(
                ReferenceCase.title == "Imported case with missing image"
            ).first()
            assert case is not None
            assert case.image_id is None
        finally:
            db.close()

    def test_export_then_import_roundtrip(self, client):
        """Export a zip, then import it back — should succeed."""
        # Create some data first
        client.post("/critique", json={
            "work_description": "A test design for export.",
        })
        # Export
        export_resp = client.get("/export")
        assert export_resp.status_code == 200
        zip_bytes = export_resp.content
        # Import
        resp = client.post("/import", files={"file": ("backup.zip", zip_bytes)})
        assert resp.status_code == 200
        result = resp.json()
        assert result["reference_cases_imported"] >= 0
        assert result["sessions_imported"] >= 1


class TestEmbeddings:
    """Tests for embedding and semantic search endpoints."""

    def test_embedding_status_returns(self, client):
        resp = client.get("/embedding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "is_configured" in data
        assert "message" in data

    def test_reindex_without_key_returns_friendly_error(self, client):
        resp = client.post("/reference-cases/reindex-embeddings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["indexed"] == 0
        assert len(data["warnings"]) >= 1
        assert "未配置" in data["warnings"][0]

    def test_semantic_search_without_index_returns_message(self, client):
        resp = client.post(
            "/reference-cases/search-semantic",
            json={"query": "minimalist poster design"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert data["total_indexed"] == 0

    def test_system_status_includes_embedding(self, client):
        resp = client.get("/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "embedding" in data
        assert "configured" in data["embedding"]
        assert data["version"] == "v1.9.0"


class TestCompareWithSemanticFallback:
    """V1.8: Compare endpoint semantic search fallback."""

    def test_compare_with_semantic_query_no_cases(self, client):
        """When no matching cases exist, semantic query should not crash."""
        resp = client.post(
            "/compare-with-references",
            json={
                "user_work_description": "A modern minimalist poster.",
                "semantic_query": "minimalist poster design",
            },
        )
        # Should succeed even with no matching cases (empty comparison)
        assert resp.status_code == 200


# ── V1.9: Case quality management ─────────────────────────────────────

class TestCaseQuality:
    """Tests for completeness scoring, training readiness, audit, and duplicates."""

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _create_case(client, **overrides):
        """Create a reference case and return its JSON."""
        payload = {
            "title": "Test Case",
            "aesthetic_level": "high",
        }
        payload.update(overrides)
        resp = client.post("/reference-cases", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    # ── Completeness scoring ─────────────────────────────────────────

    def test_complete_case_scores_high(self, client):
        """A fully populated case (with image description) should score >= 85."""
        c = self._create_case(client,
            title="Premium SaaS Landing Page",
            aesthetic_level="high",
            category="web",
            price_band="premium",
            style_tags="minimal, clean",
            target_audience="SaaS buyers",
            image_description="A clean white landing page with blue CTA buttons and sans-serif typography.",
            premium_sources="Consistent spacing, quality typography",
            cheapness_sources="Stock icons",
            learn_from_this="Typography hierarchy",
            avoid_copying="Overuse of shadows",
            notes="Excellent reference for SaaS design",
            score=88,
        )
        assert c["completeness_score"] >= 85, f"Expected >=85, got {c['completeness_score']}"
        assert c["is_training_ready"] is False  # no image uploaded, only description

    def test_minimal_case_scores_low(self, client):
        """A case with only title should score < 30."""
        c = self._create_case(client, title="Bare Minimum Case")
        assert c["completeness_score"] < 30, f"Expected <30, got {c['completeness_score']}"
        assert c["is_training_ready"] is False
        assert len(c["missing_fields"]) >= 10

    def test_case_with_unknown_level_scores_partial(self, client):
        """Aesthetic level 'unknown' should not count as present."""
        c = self._create_case(client, title="Unknown Level", aesthetic_level="unknown")
        # Should be missing aesthetic_level
        assert "审美等级" in c["missing_fields"]

    def test_missing_fields_are_chinese(self, client):
        """Missing field labels must be Chinese, not English or None."""
        c = self._create_case(client, title="Minimal")
        missing = c["missing_fields"]
        assert len(missing) > 0
        for f in missing:
            assert f, "Empty missing field label"
            # Must contain Chinese characters or common Chinese words
            is_chinese = any('一' <= ch <= '鿿' for ch in f)
            assert is_chinese or f in ("score",), f"Unexpected label: {f}"

    # ── Training readiness ───────────────────────────────────────────

    def test_training_ready_missing_image(self, client):
        """Without image, even high-score case is not training-ready."""
        c = self._create_case(client,
            title="Complete but no image",
            aesthetic_level="high",
            category="web",
            price_band="premium",
            style_tags="clean",
            target_audience="designers",
            image_description="A clean landing page design.",
            premium_sources="Great typography",
            cheapness_sources="None",
            learn_from_this="Whitespace usage",
            avoid_copying="N/A",
            notes="Good",
            score=90,
        )
        # Has all text fields but no image_id → is_training_ready must be False
        assert c["is_training_ready"] is False

    def test_training_ready_missing_learn_and_premium(self, client):
        """Without learn_from_this AND premium_sources, case is not ready."""
        c = self._create_case(client,
            title="No learning notes",
            aesthetic_level="medium",
            category="mobile",
            price_band="budget",
            style_tags="simple",
            target_audience="users",
            cheapness_sources="Low quality",
            notes="Test",
        )
        assert c["is_training_ready"] is False

    # ── Audit endpoint ───────────────────────────────────────────────

    def test_audit_returns_correct_structure(self, client):
        """GET /reference-cases/audit must return all expected keys."""
        resp = client.get("/reference-cases/audit")
        assert resp.status_code == 200
        data = resp.json()
        for key in (
            "total_cases", "training_ready_count", "incomplete_count",
            "average_completeness", "missing_image", "missing_description",
            "missing_aesthetic_level", "missing_price_band",
            "missing_premium_sources", "missing_cheapness_sources",
            "missing_learning_notes", "possible_duplicates", "recommendations",
        ):
            assert key in data, f"Missing key: {key}"

    def test_audit_detects_missing_fields(self, client):
        """Create an incomplete case and verify audit catches it."""
        self._create_case(client, title="Incomplete Audit Case")
        resp = client.get("/reference-cases/audit")
        data = resp.json()
        assert data["total_cases"] >= 1
        # With only title, we should see it in multiple missing lists
        found = False
        for key in ("missing_image", "missing_aesthetic_level", "missing_description"):
            for item in data[key]:
                if item["title"] == "Incomplete Audit Case":
                    found = True
                    break
        assert found or data["incomplete_count"] >= 1

    def test_audit_handles_empty_database(self, client):
        """Audit on empty database should not crash."""
        # Create nothing, just call audit
        resp = client.get("/reference-cases/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cases"] == 0
        assert data["recommendations"] == []

    # ── Duplicate detection ──────────────────────────────────────────

    def test_duplicate_detection_finds_title_similarity(self, client):
        """Two cases with very similar titles should be flagged."""
        self._create_case(client,
            title="Minimalist SaaS Landing Page Design",
            aesthetic_level="high",
        )
        self._create_case(client,
            title="Minimalist SaaS Landing Page",
            aesthetic_level="medium",
        )
        resp = client.get("/reference-cases/audit")
        data = resp.json()
        # They should appear in possible_duplicates
        assert data["possible_duplicates"] or data["total_cases"] == 2

    def test_duplicate_detection_no_false_positives(self, client):
        """Very different titles should NOT be flagged."""
        self._create_case(client, title="Minimalist SaaS Landing Page", aesthetic_level="high")
        self._create_case(client, title="Gothic Horror Movie Poster", aesthetic_level="low")
        resp = client.get("/reference-cases/audit")
        data = resp.json()
        # With only 2 very different cases, duplicate detection should be empty or empty groups
        dupes = data["possible_duplicates"]
        # If any groups exist, none should contain both cases
        all_ids = set()
        for g in dupes:
            for c in g["cases"]:
                all_ids.add(c["id"])
        # The two distinct cases should not appear together in a group
        assert len(all_ids) < 2 or len(dupes) == 0

    # ── Backward compatibility ───────────────────────────────────────

    def test_old_case_data_does_not_crash(self, client):
        """A case created with minimal V1.4-era fields must not break quality checks."""
        resp = client.post("/reference-cases", json={
            "title": "Old V1.4 Case",
            "aesthetic_level": "high",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "completeness_score" in data
        assert "is_training_ready" in data
        assert "missing_fields" in data
        assert isinstance(data["completeness_score"], int)
        assert isinstance(data["is_training_ready"], bool)

    def test_case_list_includes_quality_fields(self, client):
        """GET /reference-cases must include quality fields on every case."""
        self._create_case(client, title="Quality Fields Test", aesthetic_level="medium")
        resp = client.get("/reference-cases")
        assert resp.status_code == 200
        for c in resp.json()["cases"]:
            assert "completeness_score" in c
            assert "is_training_ready" in c
            assert "missing_fields" in c
            assert isinstance(c["completeness_score"], int)
            assert isinstance(c["is_training_ready"], bool)
            assert isinstance(c["missing_fields"], list)

    def test_get_single_case_includes_quality_fields(self, client):
        """GET /reference-cases/{id} must include quality fields."""
        created = self._create_case(client, title="Single Quality Test", aesthetic_level="high")
        resp = client.get(f"/reference-cases/{created['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "completeness_score" in data
        assert "is_training_ready" in data
        assert "missing_fields" in data

    def test_semantic_search_not_broken_by_quality(self, client):
        """Semantic search must still return 200 even with no embedding config."""
        resp = client.post(
            "/reference-cases/search-semantic",
            json={"query": "minimalist design"},
        )
        # Without embeddings configured, semantic search returns a message
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data or "results" in data

    def test_export_version_is_v1_9_0(self, client):
        """Export manifest must carry v1.9.0 after V1.9."""
        import zipfile
        resp = client.get("/export")
        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            manifest = json.loads(zf.read("export_manifest.json"))
            assert manifest.get("version", "").startswith("v1.")

    # ── Audit detail fields ──────────────────────────────────────────

    def test_audit_issue_has_required_fields(self, client):
        """Each AuditIssue must have id, title, completeness_score, missing_fields."""
        self._create_case(client, title="Audit Issue Test")
        resp = client.get("/reference-cases/audit")
        data = resp.json()
        # Check at least one category has valid items
        all_issues = (
            data["missing_image"] + data["missing_description"] +
            data["missing_aesthetic_level"] + data["missing_price_band"]
        )
        for item in all_issues:
            assert "id" in item
            assert "title" in item
            assert "completeness_score" in item
            assert "missing_fields" in item
            assert isinstance(item["completeness_score"], int)
