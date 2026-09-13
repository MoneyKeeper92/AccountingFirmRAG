from tests.conftest import SAMPLE


def _seed(client):
    c = client.post("/api/clients", json={"name": "ABC Company, Inc.", "entity_type": "s_corp"}).json()
    files = [("files", (f.name, f.read_bytes(), "text/plain")) for f in sorted((SAMPLE / "abc_company").iterdir())]
    r = client.post("/api/documents", data={"client_id": c["id"], "engagement": "tax_1120s"}, files=files)
    assert r.status_code == 200, r.text
    return c, r.json()["results"]


def test_auth_required(client):
    assert client.get("/api/clients", headers={"X-API-Token": "wrong"}).status_code == 401


def test_upload_extract_and_query(client):
    c, results = _seed(client)
    assert all(r["status"] == "ready" for r in results), results
    docs = client.get(f"/api/clients/{c['id']}/documents").json()
    assert len(docs) == 3
    assert {d["tax_year"] for d in docs} == {2024, 2025}
    assert {d["doc_type"] for d in docs} == {"form_1120s", "trial_balance"}

    facts = client.get(f"/api/clients/{c['id']}/facts").json()["series"]
    assert facts["gross_receipts"] == {"2024": 4820000.0, "2025": 5610000.0}
    assert facts["officer_compensation"] == {"2024": 120000.0, "2025": 120000.0}

    risk = client.get(f"/api/clients/{c['id']}/risk").json()
    assert risk["profile"] == "entity"
    areas = {f["area"] for f in risk["flags"]}
    assert "Reasonable compensation" in areas and "Basis" in areas
    assert risk["flags"][0]["severity"] == "high"
    assert risk["ratios"]["distributions_to_officer_comp"] == 2.7333

    fc = client.get(f"/api/clients/{c['id']}/forecast").json()
    assert fc["gross_receipts"]["target_year"] == 2026
    assert fc["gross_receipts"]["linear"] == 6400000.0

    f = next((SAMPLE / "abc_company").glob("*2025.txt"))
    r = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", (f.name, f.read_bytes(), "text/plain"))]).json()
    assert r["results"][0]["status"] == "duplicate"


def test_search_and_chat_with_tools(client):
    c, _ = _seed(client)
    hits = client.get("/api/search", params={"q": "shareholder loan written note interest", "client_id": c["id"]}).json()
    assert hits and "loan" in hits[0]["text"].lower()

    r = client.post("/api/chat", json={"question": "What should we watch when planning this year's return, and what do we expect gross receipts to be?",
                                       "client_id": c["id"]}).json()
    assert {t["tool"] for t in r["tool_trace"]} == {"forecast_financials", "assess_risk"}
    assert r["citations"]
    assert "Reasonable compensation" in r["answer"] and "gross_receipts" in r["answer"]

    audit = client.get("/api/admin/audit").json()
    assert audit[0]["action"] == "query" and audit[0]["detail"]["tools"]


def test_profile_switch_reports_stale_chunks(client):
    _seed(client)
    m = client.get("/api/admin/models").json()
    assert m["profile"] == "offline" and m["stale_chunks"] == 0
    r = client.post("/api/admin/models/profile", json={"profile": "anthropic_voyage"})
    assert r.status_code == 400
    assert client.get("/api/admin/models").json()["profile"] == "offline"
    r = client.post("/api/admin/reindex").json()
    assert r["reembedded"] == 0


def test_open_original_file_from_citation(client):
    c, _ = _seed(client)
    r = client.post("/api/chat", json={"question": "related party lease amendment", "client_id": c["id"]}).json()
    cite = r["citations"][0]
    f = client.get(f"/api/documents/{cite['document_id']}/file")
    assert f.status_code == 200 and b"1120-S" in f.content or b"Account" in f.content
    assert client.get(f"/api/documents/{cite['document_id']}/file?token=test-token", headers={"X-API-Token": ""}).status_code == 200
    assert client.get(f"/api/documents/{cite['document_id']}/file?token=nope", headers={"X-API-Token": ""}).status_code == 401
    assert client.get("/api/documents/doesnotexist/file").status_code == 404
    assert client.get("/api/admin/audit").json()[0]["action"] == "file_open"


def test_pointer_mode_redirects_to_source(client, monkeypatch):
    from app.config import Settings
    from app.main import create_app
    from fastapi.testclient import TestClient

    monkeypatch.setenv("FIRM_RAG_KEEP_ORIGINALS", "false")
    app = create_app(Settings.load())
    with TestClient(app) as c2:
        c2.headers.update({"X-API-Token": "test-token"})
        cl = c2.post("/api/clients", json={"name": "Pointer Co"}).json()
        f = next((SAMPLE / "abc_company").glob("*2025.txt"))
        r = c2.post("/api/documents", data={"client_id": cl["id"], "source_uri": "https://firm.sharepoint.com/sites/clients/ABC/2025/1120S.pdf"},
                    files=[("files", (f.name, f.read_bytes(), "text/plain"))]).json()["results"][0]
        assert r["status"] == "ready" and r["original_stored"] is False
        assert not list((Settings.load().uploads_dir).glob(f"**/{r['document_id']}__*"))
        resp = c2.get(f"/api/documents/{r['document_id']}/file", follow_redirects=False)
        assert resp.status_code == 307 and resp.headers["location"].startswith("https://firm.sharepoint.com/")
        r2 = c2.post("/api/documents", data={"client_id": cl["id"]}, files=[("files", ("other.txt", b"Gross receipts: 1", "text/plain"))]).json()["results"][0]
        assert c2.get(f"/api/documents/{r2['document_id']}/file").status_code == 404
