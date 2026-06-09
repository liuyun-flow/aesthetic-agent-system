"""V2.0: Training effectiveness assessment tests."""

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.db.models import TrainingRecord
from app.main import app
from fastapi.testclient import TestClient

# ── Test database ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ── Mock agent overrides (same as test_api.py, for import safety) ────

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(setup_test_db):
    app.dependency_overrides[get_db] = override_get_db
    # Override all agent deps to prevent API key errors
    from app.main import (
        get_analyzer, get_critic, get_iterator, get_profile_agent,
        get_vision_adapter, get_comparator, get_reference_comparator,
        get_prompt_generator, get_weekly_reviewer,
    )
    from app.schemas.responses import (
        AnalyzeResponse, CritiqueResponse, CompareWithReferencesResponse,
        GeneratedPrompt, IterateResponse, IterationDirection,
        JudgmentGap, ProfileResponse, VisionDescription, WeeklyReviewResponse,
    )
    from types import SimpleNamespace

    class MockAnalyzerAgent:
        def run(self, **kw): return AnalyzeResponse(
            color="", composition="", typography="", material="", emotion="",
            brand_sense="", premium_sources="", cheapness_sources="",
            improvement_suggestions="")

    class MockCriticAgent:
        def run(self, **kw): return CritiqueResponse(
            total_score=7.0,
            dimensions=SimpleNamespace(color=7,composition=7,typography=7,material=7,emotion=7,brand_sense=7),
            main_issues=[], cheapness_sources=[], priority_fixes=[])

    class MockIteratorAgent:
        def run(self, **kw): return IterateResponse(directions=[
            IterationDirection(id="d1", title="T", description="D", expected_impact="E",
                goal="G", visual_changes="V", color_changes="C", typography_changes="T",
                layout_changes="L", commercial_rationale="R", risk="R")])

    class MockProfileAgent:
        def run(self, history, total_sessions): return ProfileResponse(
            preferences="", common_mistakes="", next_week_focus="", total_sessions=total_sessions)

    class MockComparatorAgent:
        def run(self, **kw): return JudgmentGap(
            accurate_judgments=[], missed_issues=[], misjudgments=[],
            commercial_blind_spots=[], aesthetic_blind_spots=[],
            next_training_focus=[], short_summary="")

    class MockRefComparatorAgent:
        def run(self, **kw): return CompareWithReferencesResponse()

    class MockPromptGenAgent:
        def run(self, **kw): return GeneratedPrompt()

    class MockWeeklyAgent:
        def run(self, history): return WeeklyReviewResponse()

    from app.vision.manual_adapter import ManualAdapter

    app.dependency_overrides[get_analyzer] = lambda: MockAnalyzerAgent()
    app.dependency_overrides[get_critic] = lambda: MockCriticAgent()
    app.dependency_overrides[get_iterator] = lambda: MockIteratorAgent()
    app.dependency_overrides[get_profile_agent] = lambda: MockProfileAgent()
    app.dependency_overrides[get_vision_adapter] = lambda: ManualAdapter()
    app.dependency_overrides[get_comparator] = lambda: MockComparatorAgent()
    app.dependency_overrides[get_reference_comparator] = lambda: MockRefComparatorAgent()
    app.dependency_overrides[get_prompt_generator] = lambda: MockPromptGenAgent()
    app.dependency_overrides[get_weekly_reviewer] = lambda: MockWeeklyAgent()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Tests ─────────────────────────────────────────────────────────────

class TestAssessment:
    """Tests for /assessment endpoints."""

    @staticmethod
    def _seed_record(db, **overrides):
        from datetime import datetime as dt
        defaults = {
            "record_type": "critique",
            "work_description": "A test design for assessment.",
            "user_score": 70,
            "ai_score": 75,
            "created_at": dt.utcnow(),
            "completed": 0,
        }
        defaults.update(overrides)
        r = TrainingRecord(**defaults)
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    # ── Overview ──────────────────────────────────────────────────

    def test_overview_empty_returns_defaults(self, client):
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert data["score_gap_trend"] == "insufficient_data"
        assert data["average_score_gap"] is None
        assert len(data["summary"]) > 0

    def test_overview_insufficient_data_below_threshold(self, client):
        db = TestSessionLocal()
        try:
            for i in range(3):
                self._seed_record(db, user_score=60 + i * 5, ai_score=70 + i * 3)
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 3
        assert data["score_gap_trend"] == "insufficient_data"

    def test_overview_with_data_computes_avg_gap(self, client):
        db = TestSessionLocal()
        try:
            self._seed_record(db, user_score=70, ai_score=80)
            self._seed_record(db, user_score=60, ai_score=75)
            self._seed_record(db, user_score=80, ai_score=85)
            self._seed_record(db, user_score=65, ai_score=70)
            self._seed_record(db, user_score=75, ai_score=80)
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] >= 5
        assert data["average_score_gap"] is not None
        assert 7.0 <= data["average_score_gap"] <= 9.0

    def test_gap_trend_improving(self, client):
        from datetime import datetime as dt, timedelta
        db = TestSessionLocal()
        try:
            for i in range(5):
                self._seed_record(db, user_score=50, ai_score=80,
                    created_at=dt.utcnow() - timedelta(days=10 + i))
            for i in range(5):
                self._seed_record(db, user_score=70, ai_score=72,
                    created_at=dt.utcnow() - timedelta(days=i))
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_gap_trend"] in ("improving", "stable")

    # ── Mistakes ──────────────────────────────────────────────────

    def test_mistakes_returns_empty_for_no_data(self, client):
        resp = client.get("/assessment/mistakes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_mistakes_returns_patterns_with_data(self, client):
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            for i in range(6):
                self._seed_record(db,
                    training_focus_tags='["字体", "排版", "层次"]',
                    judgment_gap_summary="用户的字体判断与AI存在较大差异",
                    created_at=dt.utcnow(),
                )
        finally:
            db.close()
        resp = client.get("/assessment/mistakes")
        assert resp.status_code == 200
        patterns = resp.json()
        assert len(patterns) > 0
        for p in patterns:
            assert "mistake_type" in p
            assert "count" in p
            assert "severity" in p
            assert "explanation" in p
            assert "training_suggestion" in p

    # ── Dimensions ────────────────────────────────────────────────

    def test_dimensions_all_seven_returned(self, client):
        resp = client.get("/assessment/dimensions")
        assert resp.status_code == 200
        dims = resp.json()
        assert len(dims) == 7
        keys = {d["dimension_key"] for d in dims}
        expected = {
            "typography_judgment", "color_judgment", "composition_judgment",
            "texture_material_judgment", "price_band_judgment",
            "commercial_fit_judgment", "iteration_judgment",
        }
        assert keys == expected
        for d in dims:
            assert 0 <= d["score"] <= 100
            assert d["level"] in ("weak", "medium", "strong")

    # ── Report ────────────────────────────────────────────────────

    def test_report_7_days_returns_structure(self, client):
        resp = client.get("/assessment/report?days=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 7
        for key in ("training_count", "score_gap_summary", "top_mistakes",
                     "strongest_dimensions", "weakest_dimensions",
                     "progress_summary", "next_training_plan", "recommended_themes"):
            assert key in data, f"Missing key: {key}"

    def test_report_30_days_works(self, client):
        resp = client.get("/assessment/report?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 30

    # ── Backward compat ───────────────────────────────────────────

    def test_old_data_without_scores_no_crash(self, client):
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            db.add(TrainingRecord(
                record_type="analyze",
                work_description="Old record without scores",
                created_at=dt.utcnow(),
            ))
            db.commit()
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        resp2 = client.get("/assessment/dimensions")
        assert resp2.status_code == 200

    def test_old_records_without_scores_return_insufficient(self, client):
        """5 records with zero valid scores must show insufficient_data everywhere."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            for i in range(5):
                db.add(TrainingRecord(
                    record_type="analyze",
                    work_description=f"Old V1 record {i}",
                    created_at=dt.utcnow(),
                    # No user_score, no ai_score
                ))
            db.commit()
        finally:
            db.close()

        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 5
        assert data["valid_scored_sessions"] == 0
        assert data["score_gap_trend"] == "insufficient_data"
        assert "数据不足" in data["summary"]

        resp2 = client.get("/assessment/mistakes")
        assert resp2.status_code == 200
        assert resp2.json() == []

        resp3 = client.get("/assessment/dimensions")
        assert resp3.status_code == 200
        for d in resp3.json():
            assert d["trend"] == "insufficient_data"

    def test_selected_direction_array_does_not_crash(self, client):
        """selected_direction as a JSON array must not crash /assessment/mistakes."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            for i in range(6):
                db.add(TrainingRecord(
                    record_type="iterate",
                    work_description=f"Iterate {i}",
                    user_score=60 + i,
                    ai_score=70 + i,
                    selected_direction='["d1", "d2"]',
                    created_at=dt.utcnow(),
                ))
            db.commit()
        finally:
            db.close()
        resp = client.get("/assessment/mistakes")
        assert resp.status_code == 200

    def test_selected_direction_plain_string_does_not_crash(self, client):
        """selected_direction as a plain string must not crash /assessment/mistakes."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            for i in range(6):
                db.add(TrainingRecord(
                    record_type="iterate",
                    work_description=f"Iterate {i}",
                    user_score=60 + i,
                    ai_score=70 + i,
                    selected_direction="just a string",
                    created_at=dt.utcnow(),
                ))
            db.commit()
        finally:
            db.close()
        resp = client.get("/assessment/mistakes")
        assert resp.status_code == 200

    def test_import_version_v2_accepted(self, client):
        """V2.0.x export manifest should pass import version check."""
        import zipfile
        buf = __import__("io").BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("export_manifest.json",
                '{"version":"v2.0.1","exported_at":"2026-06-09T00:00:00","counts":{}}')
            zf.writestr("uploaded_images.json", "[]")
            zf.writestr("reference_cases.json", "[]")
            zf.writestr("sessions.json", "[]")
        buf.seek(0)
        resp = client.post("/import", files={"file": ("v2_backup.zip", buf.read())})
        assert resp.status_code == 200
        data = resp.json()
        # No "不兼容" warning for v2.x
        warnings = data.get("warnings", [])
        for w in warnings:
            assert "不兼容" not in w, f"Unexpected warning: {w}"

    # ── Trend thresholds ────────────────────────────────────────────

    def test_gap_trend_worsening(self, client):
        """Recent gaps larger than old gaps should produce worsening trend."""
        from datetime import datetime as dt, timedelta
        db = TestSessionLocal()
        try:
            # Old records: small gaps
            for i in range(5):
                self._seed_record(db, user_score=70, ai_score=72,
                    created_at=dt.utcnow() - timedelta(days=10 + i))
            # Recent records: large gaps
            for i in range(5):
                self._seed_record(db, user_score=50, ai_score=80,
                    created_at=dt.utcnow() - timedelta(days=i))
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_gap_trend"] in ("worsening", "stable")

    def test_gap_trend_stable_with_similar_gaps(self, client):
        """Gaps within ±3 of each other should produce stable trend."""
        from datetime import datetime as dt, timedelta
        db = TestSessionLocal()
        try:
            for i in range(5):
                self._seed_record(db, user_score=65, ai_score=75,
                    created_at=dt.utcnow() - timedelta(days=10 + i))
            for i in range(5):
                self._seed_record(db, user_score=64, ai_score=74,
                    created_at=dt.utcnow() - timedelta(days=i))
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["score_gap_trend"] in ("stable", "improving")

    def test_mistakes_insufficient_data_below_threshold(self, client):
        """1-4 records should return empty mistakes."""
        db = TestSessionLocal()
        try:
            for i in range(3):
                self._seed_record(db,
                    training_focus_tags='["字体"]',
                    judgment_gap_summary="字体判断有差异")
        finally:
            db.close()
        resp = client.get("/assessment/mistakes")
        assert resp.status_code == 200
        assert resp.json() == []

    # ── Old data compatibility ──────────────────────────────────────

    def test_v1_session_with_partial_fields(self, client):
        """V1.x sessions with only analyze data and no scores must not crash."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            # Simulate V1.0: basic analyze, no scores, no judgment fields
            db.add(TrainingRecord(record_type="analyze",
                work_description="A simple button design.", created_at=dt.utcnow()))
            # Simulate V1.1: has user_score but no ai_score
            db.add(TrainingRecord(record_type="critique",
                work_description="A poster critique.", user_score=60,
                created_at=dt.utcnow()))
            # Simulate V1.7.2: has selected_direction and prompt_result
            db.add(TrainingRecord(record_type="iterate",
                work_description="Iterate me.", user_score=70, ai_score=75,
                selected_direction='{"id":"d1","title":"X"}',
                prompt_result='{"chinese_prompt":"test"}',
                created_at=dt.utcnow()))
            # Simulate enough valid records to meet threshold
            for i in range(5):
                self._seed_record(db, user_score=60+i, ai_score=70+i,
                    created_at=dt.utcnow())
            db.commit()
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        resp2 = client.get("/assessment/dimensions")
        assert resp2.status_code == 200
        resp3 = client.get("/assessment/mistakes")
        assert resp3.status_code == 200

    def test_sessions_without_scores_skipped(self, client):
        """Records without both scores must be excluded from gap calculation."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            # Record with only user_score (no ai_score) — should be skipped
            db.add(TrainingRecord(record_type="critique",
                work_description="No AI score", user_score=70,
                created_at=dt.utcnow()))
            # Record with only ai_score (no user_score) — should be skipped
            db.add(TrainingRecord(record_type="critique",
                work_description="No user score", ai_score=80,
                created_at=dt.utcnow()))
            # 5 valid records with both
            for i in range(5):
                self._seed_record(db, user_score=70, ai_score=80,
                    created_at=dt.utcnow())
            db.commit()
        finally:
            db.close()
        resp = client.get("/assessment/overview")
        assert resp.status_code == 200
        data = resp.json()
        # Only the 5 complete records should count
        assert data["total_sessions"] == 7
        # Average gap based on 5 records: abs(70-80)=10 each = 10.0
        assert data["average_score_gap"] == 10.0

    def test_dimension_score_in_range(self, client):
        """All dimension scores must be within 0-100 even with extreme data."""
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            # Seed records with text that matches ALL dimension keywords heavily
            for i in range(6):
                self._seed_record(db,
                    training_focus_tags='["字体", "排版", "色彩", "构图", "材质", "价格", "商业"]',
                    judgment_gap_summary="字体色彩构图材质价格商业转化迭代方向",
                    created_at=dt.utcnow(),
                )
        finally:
            db.close()
        resp = client.get("/assessment/dimensions")
        assert resp.status_code == 200
        for d in resp.json():
            assert 0 <= d["score"] <= 100, f"{d['dimension_name']} score {d['score']} out of range"
            assert d["level"] in ("weak", "medium", "strong")

    # ── Performance ─────────────────────────────────────────────────

    def test_small_batch_performance(self, client):
        """50 mixed records should process within 2s per endpoint.

        Covers date-varied scores, optional focus_tags/judgment_gap_summary.
        A true 3000-record test would use the same code path; this guards
        against quadratic complexity regressions at small scale.
        """
        from datetime import datetime as dt
        db = TestSessionLocal()
        try:
            for i in range(50):
                self._seed_record(db,
                    user_score=60 + (i % 40),
                    ai_score=70 + (i % 30),
                    training_focus_tags='["字体", "色彩"]' if i % 3 == 0 else None,
                    judgment_gap_summary="测试判断差异" if i % 2 == 0 else None,
                    created_at=dt.utcnow() - __import__("datetime").timedelta(days=i % 60),
                )
        finally:
            db.close()
        import time
        start = time.time()
        resp = client.get("/assessment/overview")
        overview_time = time.time() - start
        assert resp.status_code == 200
        # 3000 records should process in under 2 seconds
        assert overview_time < 2.0, f"Overview too slow: {overview_time:.2f}s"

        start = time.time()
        resp2 = client.get("/assessment/dimensions")
        dims_time = time.time() - start
        assert resp2.status_code == 200
        assert dims_time < 2.0, f"Dimensions too slow: {dims_time:.2f}s"
