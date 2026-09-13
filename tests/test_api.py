from tests.conftest import SAMPLE


def _seed(client):
    c = client.post("/api/clients", json={"name": "ABC Company, Inc.", "entity_type": "s_corp"}).json()
    files = [("files", (f.name, f.read_bytes(), "text/plain")) for f in sorted((SAMPLE / "abc_company").iterdir())]
    r = client.post("/api/documents", data={"client_id": c["id"], "engagement": "audit"}, files=files)
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

    facts = client.get(f"/api/clients/{c['id']}/facts").json()["series"]
    assert facts["revenue"] == {"2024": 4820000.0, "2025": 5610000.0}

    risk = client.get(f"/api/clients/{c['id']}/risk").json()
    areas = {f["area"] for f in risk["flags"]}
    assert "Receivables" in areas and "Revenue recognition" in areas
    assert risk["ratios"]["current_ratio"] == 1.148

    fc = client.get(f"/api/clients/{c['id']}/forecast").json()
    assert fc["revenue"]["target_year"] == 2026
    assert fc["revenue"]["linear"] == 6400000.0

    # duplicate upload is detected
    f = next((SAMPLE / "abc_company").glob("*2025.txt"))
    r = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", (f.name, f.read_bytes(), "text/plain"))]).json()
    assert r["results"][0]["status"] == "duplicate"


def test_search_and_chat_with_tools(client):
    c, _ = _seed(client)
    hits = client.get("/api/search", params={"q": "line of credit covenant waiver", "client_id": c["id"]}).json()
    assert hits and "covenant" in hits[0]["text"].lower()

    r = client.post("/api/chat", json={"question": "What are the riskiest areas for this year's audit and what do we expect revenue to be?",
                                       "client_id": c["id"]}).json()
    assert {t["tool"] for t in r["tool_trace"]} == {"forecast_financials", "assess_risk"}
    assert r["citations"]
    assert "Receivables" in r["answer"] or "revenue" in r["answer"]

    audit = client.get("/api/admin/audit").json()
    assert audit[0]["action"] == "query" and audit[0]["detail"]["tools"]


def test_profile_switch_reports_stale_chunks(client):
    _seed(client)
    m = client.get("/api/admin/models").json()
    assert m["profile"] == "offline" and m["stale_chunks"] == 0
    # switching to a real profile without keys must fail cleanly and leave the app usable
    r = client.post("/api/admin/models/profile", json={"profile": "anthropic_voyage"})
    assert r.status_code == 400
    assert client.get("/api/admin/models").json()["profile"] == "offline"
    r = client.post("/api/admin/reindex").json()
    assert r["reembedded"] == 0


def test_open_original_file_from_citation(client):
    c, _ = _seed(client)
    r = client.post("/api/chat", json={"question": "line of credit covenant", "client_id": c["id"]}).json()
    cite = r["citations"][0]
    # header auth works
    f = client.get(f"/api/documents/{cite['document_id']}/file")
    assert f.status_code == 200 and b"LINE OF CREDIT" in f.content
    assert f.headers["content-type"].startswith("text/plain")
    # query-token auth works (what a browser link uses), wrong token does not
    assert client.get(f"/api/documents/{cite['document_id']}/file?token=test-token", headers={"X-API-Token": ""}).status_code == 200
    assert client.get(f"/api/documents/{cite['document_id']}/file?token=nope", headers={"X-API-Token": ""}).status_code == 401
    assert client.get("/api/documents/doesnotexist/file").status_code == 404
    assert client.get("/api/admin/audit").json()[0]["action"] == "file_open"
