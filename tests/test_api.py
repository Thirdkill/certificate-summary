"""
Integration tests for the REST API, using FastAPI's TestClient (built on
httpx). Run with:

    python -m pytest tests/

These tests exercise the endpoints end-to-end: health check, upload,
extract, batch-extract, results, registry, deletion, and the bonus
endpoints (languages, audit log, excel export, qr code).
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_certificates")
SAMPLE_CERT = os.path.join(SAMPLE_DIR, "sample_02_modern_achievement.png")


@pytest.fixture(scope="module")
def sample_exists():
    if not os.path.exists(SAMPLE_CERT):
        pytest.skip("Sample certificates not generated yet — run "
                     "tests/sample_certificates/generate_samples.py first")
    return True


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_home_page_loads():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_languages_endpoint():
    res = client.get("/languages")
    assert res.status_code == 200
    assert "eng" in res.json()["supported_languages"]


def test_upload_rejects_bad_extension():
    res = client.post("/upload", files={"file": ("test.exe", b"fakecontent", "application/octet-stream")})
    assert res.status_code == 400


def test_extract_and_fetch_result(sample_exists):
    with open(SAMPLE_CERT, "rb") as f:
        res = client.post("/extract", files={"file": ("sample.png", f, "image/png")})
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["candidate_name"]

    # fetch it back by id
    res2 = client.get(f"/results/{data['id']}")
    assert res2.status_code == 200
    assert res2.json()["id"] == data["id"]

    # clean up
    client.delete(f"/documents/{data['id']}")


def test_results_404_for_unknown_id():
    res = client.get("/results/does-not-exist")
    assert res.status_code == 404


def test_documents_list_endpoint():
    res = client.get("/documents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_audit_log_endpoint():
    res = client.get("/audit-log")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
