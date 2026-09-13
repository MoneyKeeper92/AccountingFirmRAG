import json

from app.ingest.transcript import is_wage_income_transcript, parse_wage_income_transcript, tax_period
from tests.conftest import SAMPLE

TRANSCRIPT = SAMPLE / "transcripts" / "Doe_John_WageIncome_Transcript_2025.txt"


def test_parse_wage_income_transcript():
    text = TRANSCRIPT.read_text()
    assert is_wage_income_transcript(text) and tax_period(text) == 2025
    entries = parse_wage_income_transcript(text)
    by = {(e.form, e.payer): e for e in entries}
    assert ("W-2", "ACME CORPORATION") in by and by[("W-2", "ACME CORPORATION")].amount == 142500
    assert by[("1099-INT", "FIRST BANK OF SPRINGFIELD")].amount == 1860
    assert by[("1099-DIV", "VANGUARD BROKERAGE SERVICES")].amount == 4210
    assert by[("1099-B", "VANGUARD BROKERAGE SERVICES")].amount == 21000
    assert by[("1099-NEC", "NORTHLINE DISTRIBUTION CORP")].amount == 36000
    assert by[("1098", "HOMETOWN MORTGAGE LLC")].amount == 14200
    assert by[("1099-G", "ILLINOIS DEPARTMENT OF REVENUE")].amount == 640
    assert len(entries) == 7
    assert not any("XXX-XX" in e.payer or "MAIN ST" in e.payer for e in entries)


def _seed_john(client):
    c = client.post("/api/clients", json={"name": "John & Maria Doe", "entity_type": "individual"}).json()
    files = [("files", (f.name, f.read_bytes(), "application/json")) for f in sorted((SAMPLE / "john_doe").iterdir())]
    client.post("/api/documents", data={"client_id": c["id"], "engagement": "tax_1040"}, files=files)
    return c


def test_transcript_reconciles_request_list(client):
    c = _seed_john(client)
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    lid = rl["id"]
    # the client already sent the Acme W-2 for 2026
    client.post(f"/api/request-lists/{lid}/inbound", files=[("files", ("Acme Corporation W-2 2026.txt", b"Form W-2 Wage and Tax Statement 2026\nEmployer: ACME CORPORATION\nWages: 150,000", "text/plain"))])
    r = client.post(f"/api/request-lists/{lid}/reconcile-transcript",
                    files=[("files", (TRANSCRIPT.name, TRANSCRIPT.read_bytes(), "text/plain"))]).json()
    assert r["entries"] == 7 and r["added"] == 7 and r["generic_retired"] >= 3
    assert any(c_["form"] == "W-2" and c_["status"] == "received" for c_ in r["details"])      # matched the received Acme W-2
    assert r["matched_received"] == 1
    items = {i["key"]: i for i in r["list"]["items"]}
    # the generic W-2 item was already ticked by the inbound match, so it is left alone; the
    # still-pending generics are retired in favour of the per-payer items
    assert items["w2"]["status"] == "received"
    assert items["1099_int"]["status"] == "not_applicable" and "transcript" in items["1099_int"]["note"]
    assert items["1098_mortgage"]["status"] == "not_applicable" and items["1099_div"]["status"] == "not_applicable"
    specific = [i for i in r["list"]["items"] if i["key"].startswith("irs:")]
    assert any("FIRST BANK OF SPRINGFIELD" in i["item"] and "$1,860" in i["item"] and i["status"] == "pending" for i in specific)
    assert any(i["key"].startswith("irs:1099-g") and i["category"] == "Income" for i in specific)
    assert "late March" in r["caveats"][0]
    # the transcript itself is filed under the client with no facts (does not pollute the return series)
    doc = client.get(f"/api/documents/{r['transcript_document_id']}").json()
    assert doc["doc_type"] == "irs_transcript_wage_income" and doc["extractor_model"] == "irs_transcript:deterministic"
    assert len(json.loads(doc["canonical_json"])["transcript_entries"]) == 7
    assert "wages" in client.get(f"/api/clients/{c['id']}/facts").json()["series"]           # from the return, unchanged
    # idempotent: running again adds nothing
    r2 = client.post(f"/api/request-lists/{lid}/reconcile-transcript", data={"document_id": r["transcript_document_id"]}).json()
    assert r2["added"] == 0
    assert client.get("/api/admin/audit").json()[0]["action"] == "transcript_reconcile"
    # a non-transcript document is rejected clearly
    other = client.get(f"/api/clients/{c['id']}/documents").json()[-1]["id"]
    assert client.post(f"/api/request-lists/{lid}/reconcile-transcript", data={"document_id": other}).status_code == 400


def _blank_pdf() -> bytes:
    """A minimal one-page PDF with no text layer, written by hand so the test needs no PDF writer."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def test_scanned_pdf_uses_ocr_provider_when_configured(client):
    st = client.app.state.rag_state

    class StubOCR:
        identity = "stub_ocr"
        calls = 0
        def extract_pages(self, data, filename):
            StubOCR.calls += 1
            return [(SAMPLE / "abc_company" / "ABC_Company_1120S_2025.txt").read_text()]

    c = client.post("/api/clients", json={"name": "Scan Co", "entity_type": "s_corp"}).json()
    # without OCR: flagged, no facts
    r = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", ("scan.pdf", _blank_pdf(), "application/pdf"))]).json()["results"][0]
    assert r["status"] == "ready" and r["facts"] == 0 and any("OCR" in w for w in r["warnings"])
    # with OCR configured: transcribed, extracted, warning says so
    st.pipeline.ocr = StubOCR()
    r = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", ("scan2.pdf", _blank_pdf() + b"\n%x", "application/pdf"))]).json()["results"][0]
    assert StubOCR.calls == 1 and r["doc_type"] == "form_1120s" and r["facts"] > 15
    assert any("transcribed by stub_ocr" in w for w in r["warnings"])
    st.pipeline.ocr = None


def test_inference_geo_is_passed_through(monkeypatch):
    from types import SimpleNamespace
    from app.config import SlotConfig
    from app.providers.anthropic_llm import AnthropicLLM

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    a = AnthropicLLM(SlotConfig.from_dict({"provider": "anthropic", "model": "claude-opus-5", "inference_geo": "us"}))
    captured = {}
    def fake(**kw):
        captured.update(kw)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")], stop_reason="end_turn", model="m",
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0), stop_details=None)
    a.client = SimpleNamespace(messages=SimpleNamespace(create=fake))
    a.chat("s", [{"role": "user", "content": "hi"}])
    assert captured["inference_geo"] == "us"
