import time

from tests.conftest import SAMPLE


def _seed_list(client):
    c = client.post("/api/clients", json={"name": "John & Maria Doe", "entity_type": "individual"}).json()
    files = [("files", (f.name, f.read_bytes(), "application/json")) for f in sorted((SAMPLE / "john_doe").iterdir())]
    client.post("/api/documents", data={"client_id": c["id"], "engagement": "tax_1040"}, files=files)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    return c, rl


def test_client_magic_link_flow(client):
    c, rl = _seed_list(client)
    r = client.post(f"/api/request-lists/{rl['id']}/client-link", json={"ttl_minutes": 15, "session_minutes": 60}).json()
    url = r["url"]
    token = url.rsplit("/", 1)[1]
    assert "/client/" in url and r["expires_in_minutes"] == 15

    # API calls before the link is opened are refused; the page open consumes the link
    assert client.get(f"/api/client/{token}/list").status_code == 403
    page = client.get(f"/client/{token}")
    assert page.status_code == 200 and token in page.text and "Do not forward" in page.text
    lst = client.get(f"/api/client/{token}/list").json()
    assert lst["tax_year"] == 2026 and lst["client_name"].startswith("John") and lst["questions"] and lst["items"]
    assert all(i["status"] != "not_applicable" for i in lst["items"])
    assert not any(k in lst for k in ("facts", "summary"))            # nothing beyond the list is exposed

    # client answers a question and uploads a file against a pending item
    client.post(f"/api/client/{token}/answers", json={"answers": [{"key": "q_childcare", "answer": "no"}]})
    lst = client.get(f"/api/client/{token}/list").json()
    assert not any(i["item"].startswith("Child and dependent care") for i in lst["items"])
    w2 = next(i for i in lst["items"] if i["item"].startswith("W-2"))
    up = client.post(f"/api/client/{token}/upload/{w2['id']}", files=[("files", ("Acme W-2 2026.txt", b"Form W-2 2026\nWages: 150,000", "text/plain"))]).json()
    assert up["results"][0]["status"] == "ready"
    staff_view = client.get(f"/api/request-lists/{rl['id']}").json()
    assert next(i for i in staff_view["items"] if i["id"] == w2["id"])["status"] == "received"
    doc = client.get(f"/api/clients/{c['id']}/documents").json()[0]
    assert doc["uploaded_by"] == "client" and doc["tax_year"] == 2026
    actions = [a["action"] for a in client.get("/api/admin/audit").json()[:6]]
    assert "client_upload" in actions and "client_organizer_answers" in actions

    # a second open of the same link does not restart the session; an unknown token 404s; revocation works
    store = client.app.state.rag_state.store
    import hashlib
    link = store.get_client_link(hashlib.sha256(token.encode()).hexdigest())
    assert link["opened_at"] is not None and link["session_until"] > time.time()
    assert client.get("/client/not-a-real-token").status_code == 404
    store.conn.execute("UPDATE client_links SET session_until=? WHERE token_hash=?", (time.time() - 1, link["token_hash"])); store.conn.commit()
    assert client.get(f"/api/client/{token}/list").status_code == 410
    assert client.delete(f"/api/request-lists/{rl['id']}/client-link").json()["revoked"] == 1
    # an expired, never-opened link is refused
    r2 = client.post(f"/api/request-lists/{rl['id']}/client-link", json={"ttl_minutes": 5}).json()
    t2 = r2["url"].rsplit("/", 1)[1]
    store.conn.execute("UPDATE client_links SET expires_at=? WHERE token_hash=?", (time.time() - 1, hashlib.sha256(t2.encode()).hexdigest())); store.conn.commit()
    assert client.get(f"/client/{t2}").status_code == 410


def test_graph_mail_notifier_shapes(monkeypatch):
    from app.notify import GraphMailNotifier, build_notifier

    monkeypatch.setenv("GRAPH_MAIL_FROM", "documents@firm.example")
    monkeypatch.delenv("SMS_WEBHOOK_URL", raising=False)
    calls = []

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {}

    class FakeHttp:
        def post(self, url, headers=None, json=None, data=None):
            calls.append((url, headers, json))
            return FakeResp()

    n = GraphMailNotifier(http=FakeHttp(), token_provider=lambda: "tok")
    d = n.send_email("john@example.com", "Reminder", "Hello")
    assert d.ok and d.channel == "email" and "Graph" in d.detail
    url, headers, payload = calls[-1]
    assert url == "https://graph.microsoft.com/v1.0/users/documents@firm.example/sendMail"
    assert headers["Authorization"] == "Bearer tok"
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == "john@example.com" and payload["saveToSentItems"] is True
    assert n.send_email(None, "x", "y").ok is False
    assert n.send_sms("+1555", "hi").channel == "log"               # no SMS gateway configured -> drafted only
    assert isinstance(build_notifier(), GraphMailNotifier)          # Graph wins over SMTP when configured
