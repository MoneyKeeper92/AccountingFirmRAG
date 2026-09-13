import time

from tests.conftest import SAMPLE


def _seed_john(client):
    c = client.post("/api/clients", json={"name": "John & Maria Doe", "entity_type": "individual"}).json()
    files = [("files", (f.name, f.read_bytes(), "application/json")) for f in sorted((SAMPLE / "john_doe").iterdir())]
    r = client.post("/api/documents", data={"client_id": c["id"], "engagement": "tax_1040"}, files=files)
    assert all(x["status"] == "ready" for x in r.json()["results"])
    return c


# ------------------------------------------------------------------ verify before use

def test_fact_accept_reject_edit_flow_and_effect_on_planning(client):
    c = _seed_john(client)
    review = client.get(f"/api/clients/{c['id']}/facts/review").json()
    assert review["summary"]["extracted"] == review["summary"]["total"] > 20
    penalty = next(f for f in review["facts"] if f["name"] == "underpayment_penalty")
    agi_2025 = next(f for f in review["facts"] if f["name"] == "adjusted_gross_income" and f["period"] == 2025)

    # reject the penalty -> the penalty flag disappears from the planning screen
    assert any(f["metric"] == "underpayment_penalty" for f in client.get(f"/api/clients/{c['id']}/risk").json()["flags"])
    r = client.patch(f"/api/facts/{penalty['id']}", json={"status": "rejected", "note": "was a state penalty"}).json()
    assert r["status"] == "rejected" and r["verified_by"] == "staff"
    assert not any(f["metric"] == "underpayment_penalty" for f in client.get(f"/api/clients/{c['id']}/risk").json()["flags"])
    assert "underpayment_penalty" not in client.get(f"/api/clients/{c['id']}/facts").json()["series"]

    # edit AGI -> the edited value drives the series; original kept
    r = client.patch(f"/api/facts/{agi_2025['id']}", json={"status": "edited", "value": 191500}).json()
    assert r["value"] == 191500 and r["original_value"] == 191022 and r["status"] == "edited"
    assert client.get(f"/api/clients/{c['id']}/facts").json()["series"]["adjusted_gross_income"]["2025"] == 191500
    # undo restores the extracted value
    r = client.patch(f"/api/facts/{agi_2025['id']}", json={"status": "extracted"}).json()
    assert r["value"] == 191022 and r["original_value"] is None

    # accept + validation + audit
    wages = next(f for f in review["facts"] if f["name"] == "wages" and f["period"] == 2025)
    assert client.patch(f"/api/facts/{wages['id']}", json={"status": "accepted"}).json()["status"] == "accepted"
    assert client.patch(f"/api/facts/{wages['id']}", json={"status": "edited"}).status_code == 400
    assert client.patch("/api/facts/nope", json={"status": "accepted"}).status_code == 404
    summary = client.get(f"/api/clients/{c['id']}/facts/review").json()["summary"]
    assert summary["accepted"] == 1 and summary["rejected"] == 1
    actions = [a["action"] for a in client.get("/api/admin/audit").json()[:6]]
    assert actions.count("fact_verify") >= 4


def test_citation_feedback_is_logged(client):
    c = _seed_john(client)
    r = client.post("/api/chat", json={"question": "home office", "client_id": c["id"]}).json()
    cite = r["citations"][0]
    assert client.post("/api/feedback", json={"verdict": "reject", "question": "home office", "document_id": cite["document_id"],
                                              "client_id": c["id"], "excerpt": cite["excerpt"], "note": "wrong year"}).json()["recorded"]
    top = client.get("/api/admin/audit").json()[0]
    assert top["action"] == "citation_feedback" and top["detail"]["verdict"] == "reject" and top["detail"]["document_id"] == cite["document_id"]
    assert client.post("/api/feedback", json={"verdict": "maybe"}).status_code == 422


# ------------------------------------------------------------------ reminders

def test_reminders_follow_schedule_and_stop_when_complete(client):
    c = _seed_john(client)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    lid = rl["id"]
    # draft lists are never due; sending sets the anchor
    assert client.get("/api/reminders/due").json() == []
    rl = client.patch(f"/api/request-lists/{lid}", json={"status": "sent", "client_email": "john@example.com", "reminder_days": "7,14"}).json()
    assert rl["sent_at"] and rl["reminder_channel"] == "email"
    assert client.get("/api/reminders/due").json() == []                       # sent just now: not due yet

    store = client.app.state.rag_state.store
    eight_days_later = time.time() + 8 * 86400
    due = store.due_reminders(now=eight_days_later)
    assert [d["id"] for d in due] == [lid] and due[0]["reminder_number"] == 1 and due[0]["pending"] == rl["counts"]["pending"]

    # send: LogNotifier drafts it and the audit log has the body; counter advances; second interval not yet reached
    r = client.post(f"/api/reminders/{lid}/send").json()
    assert r["sent"] and r["reminder_number"] == 1 and r["deliveries"][0]["channel"] == "log" and "still needed" in r["subject"]
    top = client.get("/api/admin/audit").json()[0]
    assert top["action"] == "reminder_sent" and top["detail"]["reminder_number"] == 1
    assert store.due_reminders(now=time.time() + 5 * 86400) == []
    assert [d["reminder_number"] for d in store.due_reminders(now=time.time() + 15 * 86400)] == [2]
    client.post(f"/api/reminders/{lid}/send")
    assert store.due_reminders(now=time.time() + 60 * 86400) == []              # schedule exhausted -> a person follows up

    # email+sms channel adds an sms delivery; 'off' disables; completing the list stops everything
    client.patch(f"/api/request-lists/{lid}", json={"reminder_channel": "email+sms", "client_phone": "+15551234567", "reminder_days": "1,2,3,4"})
    r = client.post(f"/api/reminders/{lid}/send").json()
    assert [d["channel"] for d in r["deliveries"]] == ["log", "log"]
    client.patch(f"/api/request-lists/{lid}", json={"reminder_channel": "off"})
    assert client.post(f"/api/reminders/{lid}/send").json()["sent"] is False
    client.patch(f"/api/request-lists/{lid}", json={"reminder_channel": "email"})
    for it in client.get(f"/api/request-lists/{lid}").json()["items"]:
        client.patch(f"/api/request-lists/{lid}/items/{it['id']}", json={"status": "not_applicable"})
    assert client.get(f"/api/request-lists/{lid}").json()["status"] == "complete"
    assert client.post(f"/api/reminders/{lid}/send").json()["reason"].startswith("nothing pending")
    assert store.due_reminders(now=time.time() + 365 * 86400) == []
    assert client.patch(f"/api/request-lists/{lid}", json={"reminder_days": "abc"}).status_code == 422


# ------------------------------------------------------------------ conditional organizer

def test_organizer_answers_open_and_close_items(client):
    c = _seed_john(client)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    lid = rl["id"]
    org = client.get(f"/api/request-lists/{lid}/organizer").json()
    assert org["return_type"] == "1040"
    keys = {q["key"] for q in org["questions"]}
    assert "q_home" in keys and "q_childcare" in keys and "q_assets" not in keys           # entity question hidden for a 1040
    assert all(q["answer"] is None for q in org["questions"])
    pending_before = rl["counts"]["pending"]

    # "no" to childcare retires the childcare item; "yes" to home adds a closing-statement slot
    r = client.post(f"/api/request-lists/{lid}/organizer", json={"answers": [{"key": "q_childcare", "answer": "no"}, {"key": "q_home", "answer": "yes"}]}).json()
    assert r["effects"] == {"added": 1, "reopened": 0, "retired": 1}
    items = {i["key"]: i for i in r["list"]["items"]}
    assert items["childcare"]["status"] == "not_applicable" and items["childcare"]["note"].startswith("Answered no")
    assert items["closing_statement"]["status"] == "pending"
    assert r["list"]["counts"]["pending"] == pending_before                    # one retired, one added

    # flipping childcare back to yes reopens the retired item rather than duplicating it
    r = client.post(f"/api/request-lists/{lid}/organizer", json={"answers": [{"key": "q_childcare", "answer": "yes"}]}).json()
    assert r["effects"]["reopened"] == 1 and r["effects"]["added"] == 0
    assert sum(1 for i in r["list"]["items"] if i["key"] == "childcare") == 1
    org = client.get(f"/api/request-lists/{lid}/organizer").json()
    assert {q["key"]: q["answer"] for q in org["questions"]}["q_childcare"] == "yes"
    assert client.post(f"/api/request-lists/{lid}/organizer", json={"answers": [{"key": "q_home", "answer": "maybe"}]}).status_code == 400
    assert client.get("/api/admin/audit").json()[0]["action"] == "organizer_answers"

    # entity list shows entity questions
    s_corp = client.post("/api/clients", json={"name": "ABC Company, Inc.", "entity_type": "s_corp"}).json()
    files = [("files", (f.name, f.read_bytes(), "text/plain")) for f in sorted((SAMPLE / "abc_company").iterdir())]
    client.post("/api/documents", data={"client_id": s_corp["id"], "engagement": "tax_1120s"}, files=files)
    rl2 = client.post(f"/api/clients/{s_corp['id']}/request-lists", json={}).json()
    org2 = client.get(f"/api/request-lists/{rl2['id']}/organizer").json()
    k2 = {q["key"] for q in org2["questions"]}
    assert "q_assets" in k2 and "q_contractors" in k2 and "q_childcare" not in k2
