import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRM_RAG_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("FIRM_RAG_UPLOADS", str(tmp_path / "uploads"))
    monkeypatch.setenv("FIRM_RAG_PROFILE", "offline")
    monkeypatch.setenv("FIRM_RAG_API_TOKEN", "test-token")
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings.load())
    with TestClient(app) as c:
        c.headers.update({"X-API-Token": "test-token"})
        yield c


SAMPLE = ROOT / "sample_data"
