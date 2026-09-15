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


def test_mef_verified_aliases_and_k1s():
    """Element names verified against the public MeF stylesheets TY2023-2025 (research 14A)."""
    xml = b"""<?xml version="1.0"?><Return xmlns="http://www.irs.gov/efile"><ReturnHeader><TaxYr>2025</TaxYr><ReturnTypeCd>1120S</ReturnTypeCd>
    <Filer><EIN>111222333</EIN><BusinessName><BusinessNameLine1Txt>RIVER LLC</BusinessNameLine1Txt></BusinessName></Filer></ReturnHeader>
    <ReturnData><IRS1120S><GrossReceiptsOrSalesAmt>900000</GrossReceiptsOrSalesAmt><OfficersCompensationAmt>80000</OfficersCompensationAmt>
    <OrdinaryBusinessIncomeLossAmt>200000</OrdinaryBusinessIncomeLossAmt></IRS1120S>
    <IRS1120SScheduleL><RetainedEarningEOYAmt>410000</RetainedEarningEOYAmt><TotalAssetsEOYAmt>1200000</TotalAssetsEOYAmt></IRS1120SScheduleL>
    <IRS1120SScheduleM2><BalanceBOYAccumAdjAcctAmt>300000</BalanceBOYAccumAdjAcctAmt><BalanceEOYAccumAdjAcctAmt>390000</BalanceEOYAccumAdjAcctAmt></IRS1120SScheduleM2>
    <IRS1120SScheduleK1><ShareholderPersonNm>ANA RIVER</ShareholderPersonNm><OrdinaryIncomeLossAmt>120000</OrdinaryIncomeLossAmt><DistributionsAmt>70000</DistributionsAmt></IRS1120SScheduleK1>
    <IRS1120SScheduleK1><ShareholderPersonNm>BEN RIVER</ShareholderPersonNm><OrdinaryIncomeLossAmt>80000</OrdinaryIncomeLossAmt><DistributionsAmt>50000</DistributionsAmt></IRS1120SScheduleK1>
    </ReturnData></Return>"""
    rec = parse_mef(xml)["record"]
    facts = {f["name"]: f["value"] for f in rec["facts"]}
    assert facts["officer_compensation"] == 80000 and facts["retained_earnings"] == 410000 and facts["aaa_balance"] == 390000
    assert [k["owner"] for k in rec["k1s"]] == ["ANA RIVER", "BEN RIVER"]
    assert rec["k1s"][0]["ordinary_income"] == 120000 and rec["k1s"][1]["distributions"] == 50000
    assert {"name": "ANA RIVER", "role": "shareholder"} in rec["entities"]
    assert "2 K-1(s)" in rec["summary"]
    # per-owner amounts never enter the facts series
    assert "ordinary_income" not in facts

    xml1040 = b"""<?xml version="1.0"?><Return xmlns="http://www.irs.gov/efile"><ReturnHeader><TaxYr>2025</TaxYr><ReturnTypeCd>1040</ReturnTypeCd></ReturnHeader>
    <ReturnData><IRS1040><AdjustedGrossIncomeAmt>100000</AdjustedGrossIncomeAmt><TotalAdditionalDeductionsAmt>6000</TotalAdditionalDeductionsAmt></IRS1040></ReturnData></Return>"""
    facts = {f["name"]: f["value"] for f in parse_mef(xml1040)["record"]["facts"]}
    assert facts["additional_deductions"] == 6000          # TY2025 line 13b, Schedule 1-A
