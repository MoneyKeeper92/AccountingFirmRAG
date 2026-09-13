from pathlib import Path

from app.ingest.mef import is_mef_xml, parse_mef
from tests.conftest import SAMPLE

MEF = SAMPLE / "mef"


def test_parse_1040_mef():
    data = (MEF / "Doe_1040_TY2025_efile.xml").read_bytes()
    assert is_mef_xml(data)
    out = parse_mef(data)
    rec = out["record"]
    assert rec["return_type"] == "1040" and rec["tax_year"] == 2025 and rec["doc_type"] == "form_1040"
    assert rec["filing_status"] == "married filing jointly"
    assert {"1040", "Schedule A", "Schedule C", "Schedule D", "Schedule SE", "Form 8949", "Form 8995"} <= set(rec["forms_present"])
    facts = {f["name"]: f["value"] for f in rec["facts"]}
    assert facts["adjusted_gross_income"] == 191022 and facts["wages"] == 142500 and facts["total_tax"] == 24870
    assert facts["schedule_c_net_profit"] == 38900 and facts["self_employment_tax"] == 5496 and facts["underpayment_penalty"] == 96
    assert facts["estimated_payments"] == 4000 and facts["amount_owed"] == 2866
    assert {"name": "John Doe", "role": "taxpayer"} in rec["entities"]
    text = out["pages"][0]
    assert "123456789" not in text and "***-**-6789" in text            # SSN masked in the indexed text
    assert "[Schedule C]" in text and "Net Profit Or Loss Amt: 38900" in text
    assert any(u.startswith("Schedule A:") for u in out["unmapped"])     # unmapped amounts are reported, not lost


def test_parse_1120s_mef():
    out = parse_mef((MEF / "ABC_1120S_TY2025_efile.xml").read_bytes())
    rec = out["record"]
    assert rec["return_type"] == "1120-S" and rec["doc_type"] == "form_1120s"
    assert {"1120-S", "Schedule K", "Schedule L", "Schedule M-2", "Schedule K-1", "Form 1125-E", "Form 4562"} <= set(rec["forms_present"])
    facts = {f["name"]: f["value"] for f in rec["facts"]}
    assert facts["gross_receipts"] == 5_610_000 and facts["officer_compensation"] == 120_000 and facts["distributions"] == 328_000
    assert facts["aaa_balance"] == 920_000 and facts["loans_from_shareholders"] == 150_000 and facts["number_of_owners"] == 2
    assert "taxable_income" not in facts and "corporate_taxable_income" not in facts


def test_mef_upload_skips_the_model_and_feeds_planning(client):
    c = client.post("/api/clients", json={"name": "MeF Co", "entity_type": "s_corp"}).json()
    f = MEF / "ABC_1120S_TY2025_efile.xml"
    r = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", (f.name, f.read_bytes(), "application/xml"))]).json()["results"][0]
    assert r["status"] == "ready" and r["doc_type"] == "form_1120s" and r["facts"] >= 15
    doc = client.get(f"/api/documents/{r['document_id']}").json()
    assert doc["extractor_model"] == "mef_xml:deterministic"
    risk = client.get(f"/api/clients/{c['id']}/risk").json()
    assert "Reasonable compensation" in {fl["area"] for fl in risk["flags"]}
    hits = client.get("/api/search", params={"q": "loans from shareholders", "client_id": c["id"]}).json()
    assert hits and "Loans From Shareholders" in hits[0]["text"]
    # a non-MeF xml file still goes through the normal path
    r2 = client.post("/api/documents", data={"client_id": c["id"]}, files=[("files", ("note.xml", b"<note><body>Gross receipts: 5</body></note>", "application/xml"))]).json()["results"][0]
    assert r2["status"] == "ready" and client.get(f"/api/documents/{r2['document_id']}").json()["extractor_model"] != "mef_xml:deterministic"
