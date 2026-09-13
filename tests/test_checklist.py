from tests.conftest import SAMPLE


def _seed_john(client):
    c = client.post("/api/clients", json={"name": "John & Maria Doe", "entity_type": "individual"}).json()
    files = [("files", (f.name, f.read_bytes(), "application/json")) for f in sorted((SAMPLE / "john_doe").iterdir())]
    r = client.post("/api/documents", data={"client_id": c["id"], "engagement": "tax"}, files=files)
    assert r.status_code == 200 and all(x["status"] == "ready" for x in r.json()["results"])
    return c


def test_request_list_from_prior_return(client):
    c = _seed_john(client)
    r = client.post(f"/api/clients/{c['id']}/request-lists", json={})
    assert r.status_code == 200, r.text
    rl = r.json()
    assert rl["tax_year"] == 2026 and rl["prior_year"] == 2025
    keys = {i["key"] for i in rl["items"]}
    for expected in ("engagement_letter", "w2", "1099_int", "1099_div", "1099_b", "sched_c_income", "home_office",
                     "1098_mortgage", "charitable", "childcare", "estimated_payments", "property_tax"):
        assert expected in keys, expected
    assert not any(k in keys for k in ("hsa", "1095_a", "student_loan"))   # nothing in the file suggests these
    assert "rental" in keys                                              # the preparer's note mentions a rental purchase
    followups = [i["item"] for i in rl["items"] if i["category"] == "Follow-up"]
    assert any("rental property" in f.lower() or "s-corp" in f.lower() for f in followups)
    assert "W-2 from each employer" in rl["email_body"] and "$142,500" in rl["email_body"]
    assert rl["counts"]["pending"] == len(rl["items"])
    assert client.get(f"/api/clients/{c['id']}/request-lists").json()[0]["pending"] == len(rl["items"])


def test_receive_items_and_pending_count(client):
    c = _seed_john(client)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    w2 = next(i for i in rl["items"] if i["key"] == "w2")
    before = rl["counts"]["pending"]

    # staff upload for a specific item: filed into the client folder with the right year, item ticked
    r = client.post(f"/api/request-lists/{rl['id']}/items/{w2['id']}/upload",
                    files=[("files", ("Acme W-2 2026.txt", b"Form W-2 Wage and Tax Statement 2026\nWages: 150,000", "text/plain"))]).json()
    assert r["results"][0]["status"] == "ready"
    lst = r["list"]
    item = next(i for i in lst["items"] if i["id"] == w2["id"])
    assert item["status"] == "received" and item["received_filename"] == "Acme W-2 2026.txt"
    assert lst["counts"]["pending"] == before - 1
    doc = client.get(f"/api/documents/{item['document_id']}").json()
    assert doc["client_id"] == c["id"] and doc["tax_year"] == 2026 and doc["engagement"] == "tax"

    # not applicable + reopen
    ho = next(i for i in lst["items"] if i["key"] == "home_office")
    lst = client.patch(f"/api/request-lists/{rl['id']}/items/{ho['id']}", json={"status": "not_applicable"}).json()
    assert lst["counts"]["pending"] == before - 2
    lst = client.patch(f"/api/request-lists/{rl['id']}/items/{ho['id']}", json={"status": "pending"}).json()
    assert lst["counts"]["pending"] == before - 1


def test_inbound_reply_auto_matches_attachments(client):
    c = _seed_john(client)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    r = client.post(f"/api/request-lists/{rl['id']}/inbound", data={"sender": "john@example.com", "subject": "Re: Documents needed"},
                    files=[("files", ("1099-INT First Bank 2026.txt", b"Form 1099-INT Interest Income 2026\nInterest income: 2,100", "text/plain")),
                           ("files", ("Chase 1098 statement.txt", b"Form 1098 Mortgage Interest Statement\nMortgage interest: 13,900", "text/plain")),
                           ("files", ("photo_of_dog.txt", b"nothing useful", "text/plain"))]).json()
    matched = {x["filename"]: x["matched_item"] for x in r["results"]}
    assert matched["1099-INT First Bank 2026.txt"].startswith("1099-INT")
    assert matched["Chase 1098 statement.txt"].startswith("1098 mortgage")
    assert matched["photo_of_dog.txt"] is None
    # every attachment was filed in the client folder regardless of matching
    docs = client.get(f"/api/clients/{c['id']}/documents").json()
    assert {d["filename"] for d in docs} >= set(matched)
    assert r["list"]["counts"]["received"] == 2
    audit = client.get("/api/admin/audit").json()
    assert audit[0]["action"] == "request_list_inbound" and audit[0]["detail"]["matched"] == 2


def test_request_list_needs_documents(client):
    c = client.post("/api/clients", json={"name": "Empty Client"}).json()
    r = client.post(f"/api/clients/{c['id']}/request-lists", json={})
    assert r.status_code == 400 and "upload last year" in r.json()["detail"]
