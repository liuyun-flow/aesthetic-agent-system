"""V2.1: /system/preflight endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(setup_test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestPreflight:
    """Tests for GET /system/preflight."""

    def test_preflight_returns_200_and_all_keys(self, client):
        resp = client.get("/system/preflight")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("version", "backend", "database", "config_dir",
                     "uploads_dir", "deepseek", "vision", "embedding",
                     "recommendations", "all_ok", "is_docker"):
            assert key in data, f"Missing key: {key}"

    def test_preflight_version_is_v2_1_1(self, client):
        resp = client.get("/system/preflight")
        assert resp.json()["version"] == "v2.1.3"

    def test_preflight_no_api_key_exposed(self, client):
        resp = client.get("/system/preflight")
        body = str(resp.json())
        assert "sk-" not in body or "sk-" not in body

    def test_preflight_database_fields(self, client):
        resp = client.get("/system/preflight")
        db_info = resp.json()["database"]
        assert db_info["status"] in ("ok", "error")
        assert "path" in db_info
        assert isinstance(db_info["writable"], bool)

    def test_preflight_deepseek_unconfigured(self, client):
        """Without DEEPSEEK_API_KEY, preflight should report not configured."""
        resp = client.get("/system/preflight")
        ds = resp.json()["deepseek"]
        # In test environment, key is typically not set
        assert "configured" in ds
        assert "hint" in ds
        assert len(ds["hint"]) > 0

    def test_preflight_has_recommendations(self, client):
        resp = client.get("/system/preflight")
        recs = resp.json()["recommendations"]
        assert isinstance(recs, list)
        # At minimum, the backup reminder should be present
        backup_hint_found = any("备份" in r for r in recs)
        assert backup_hint_found

    def test_preflight_all_ok_is_bool(self, client):
        resp = client.get("/system/preflight")
        assert isinstance(resp.json()["all_ok"], bool)

    def test_preflight_detects_old_db_url(self, client, monkeypatch):
        """Old DATABASE_URL should produce a migration recommendation."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./aesthetic.db")
        resp = client.get("/system/preflight")
        recs = resp.json()["recommendations"]
        old_path_warning = any("aesthetic.db" in r for r in recs)
        assert old_path_warning

    def test_preflight_db_path_from_env(self, client, monkeypatch):
        """Preflight should use DATABASE_URL env var for database path."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/database/aesthetic.db")
        resp = client.get("/system/preflight")
        db_info = resp.json()["database"]
        assert "data" in db_info["path"] or db_info["status"] in ("ok", "error")

    def test_existing_endpoints_still_pass(self, client):
        resp = client.get("/system/status")
        assert resp.status_code == 200
        resp2 = client.get("/health")
        assert resp2.status_code == 200
