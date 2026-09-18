from app.ingest.forms_catalog import CATALOG, detect
from app import statements
from tests.conftest import SAMPLE


def _seed(client, folder, name, entity_type, engagement):
    c = client.post("/api/clients", json={"name": name, "entity_type": entity_type}).json()
    files = [("files", (f.name, f.read_bytes(), "text/plain")) for f in sorted((SAMPLE / folder).iterdir())]
    r = client.post("/api/documents", data={"client_id": c["id"], "engagement": engagement}, files=files).json()
    assert all(x["status"] == "ready" for x in r["results"]), r
    return c


def test_forms_catalog_detects_major_forms():
    cases = {
        "Form W-2 Wage and Tax Statement 2025": "w2", "Form 1099-NEC Nonemployee Compensation": "1099_nec", "1099-DIV Dividends and Distributions": "1099_div",
        "Form 1099-R Distributions From Pensions": "1099_r", "SSA-1099 Social Security Benefit Statement": "ssa_1099", "Form 1098 Mortgage Interest Statement": "1098_mortgage",
        "Form 1098-T Tuition Statement": "1098_t", "Form 1095-A Health Insurance Marketplace Statement": "1095_a", "Form 5498 IRA Contribution Information": "5498",
        "Schedule K-1 (Form 1120-S) Shareholder's Share": "k1_1120s", "Schedule K-1 (Form 1065) Partner's Share": "k1_1065",
        "FORM 1065 U.S. RETURN OF PARTNERSHIP INCOME ... Schedule K-1 issued to each partner": "form_1065",
        "Form 1120 U.S. Corporation Income Tax Return": "form_1120", "Form 1120-S U.S. Income Tax Return for an S Corporation": "form_1120s",
        "Form 1040 U.S. Individual Income Tax Return": "form_1040", "Form 1040-ES Estimated Tax Payment Voucher": "estimated_payment_record",
        "Form 941 Employer's Quarterly Federal Tax Return": "form_941", "Notice CP2000 Internal Revenue Service": "irs_notice",
        "Wage and Income Transcript": "irs_transcript_wage_income", "Trial Balance as of December 31": "trial_balance",
    }
    for text, expected in cases.items():
        spec = detect(text)
        assert spec and spec.doc_type == expected, (text, spec and spec.doc_type)
    assert detect("", "Doe_1099-INT_First_Bank_2026.pdf").doc_type == "1099_int"
    assert len(CATALOG) >= 80 and len({s.code for s in CATALOG}) == len(CATALOG)


def test_forms_endpoint_and_overview(client):
    forms = client.get("/api/forms").json()
    assert any(f["code"] == "1099-B" and f["plain"] for f in forms)
    c = _seed(client, "john_doe", "John & Maria Doe", "individual", "tax_1040")
    o = client.get(f"/api/clients/{c['id']}/overview").json()
    assert o["prior_return"]["tax_year"] == 2025 and o["prior_return"]["return_type"] == "1040" and o["this_year"] == 2026
    labels = {f["label"]: f["value"] for f in o["prior_return"]["figures"]}
    assert labels["Adjusted gross income"] == 191022 and labels["Total tax"] == 24870
    assert o["request_list"] is None and o["documents_this_year"] == []


def test_start_return_and_review(client):
    c = _seed(client, "john_doe", "John & Maria Doe", "individual", "tax_1040")
    r = client.post(f"/api/clients/{c['id']}/start-return", json={}).json()
    assert r["tax_year"] == 2026 and r["request_list"]["created"] is True and r["request_list"]["pending"] > 10
    assert "still needed" in r["headline"] and any("request email" in s for s in r["next_steps"])
    assert any("Estimated payments" in w for w in r["watch"])
    r2 = client.post(f"/api/clients/{c['id']}/start-return", json={}).json()
    assert r2["request_list"]["created"] is False and r2["request_list"]["id"] == r["request_list"]["id"]
    o = client.get(f"/api/clients/{c['id']}/overview").json()
    assert o["request_list"]["counts"]["pending"] == r["request_list"]["pending"] and o["request_list"]["pending_items"]

    # review the 2025 return against 2024
    docs = client.get(f"/api/clients/{c['id']}/documents").json()
    d2025 = next(d for d in docs if d["tax_year"] == 2025)
    rv = client.post(f"/api/clients/{c['id']}/review-return", json={"document_id": d2025["id"]}).json()
    assert rv["prior_year"] == 2024
    big = {ch["name"] for ch in rv["changes"] if ch["big"]}
    assert "schedule_c_net_profit" in big and "total_tax" in big
    assert "Schedule A" in rv["new_forms"] and rv["missing_forms"] == []
    assert rv["headline"] and rv["checks"]
    tb = next(iter(client.get(f"/api/clients/{c['id']}/documents").json()))
    assert client.post(f"/api/clients/{c['id']}/review-return", json={"document_id": "nope"}).status_code == 400


def test_statements_from_trial_balance_and_from_return(client):
    s_corp = _seed(client, "abc_company", "ABC Company, Inc.", "s_corp", "tax_1120s")
    st = client.get(f"/api/clients/{s_corp['id']}/statements").json()
    assert st["source"] == "trial balance" and st["year"] == 2025
    inc, bs = st["income_statement"], st["balance_sheet"]
    assert inc["Revenue"] == 5_610_000 and inc["Cost of goods sold"] == 3_640_000
    exp = dict(inc["expenses"])
    assert exp["Wages"] == 1_105_000 and exp["Rent"] == 168_000 and exp["Depreciation"] == 96_000
    liabs = dict(bs["liabilities"])
    assert dict(bs["assets"])["Cash"] == 148_000 and liabs["Loans payable"] == 690_000 and liabs["Line of credit and cards"] == 690_000
    assert liabs["Accrued and other current liabilities"] == 143_000 + 100_000          # accrued wages + customer deposits
    assert bs["balances"] is True and st["unclassified_accounts"] == []
    x = client.get(f"/api/clients/{s_corp['id']}/statements?format=xlsx")
    assert x.status_code == 200 and x.headers["content-type"].startswith("application/vnd.openxmlformats") and len(x.content) > 4000

    # a client with only a return (no trial balance) falls back to the return's figures
    corp = _seed(client, "northline_corp", "Northline Distribution Corp.", "c_corp", "tax_1120")
    st2 = client.get(f"/api/clients/{corp['id']}/statements").json()
    assert st2["source"] == "tax return and books" and st2["income_statement"]["Revenue"] == 9_650_000
    assert dict(st2["income_statement"]["expenses"])["Officer and owner compensation"] == 430_000
    assert st2["balance_sheet"]["Total assets"] == 5_210_000
    # an individual has no statements
    ind = client.post("/api/clients", json={"name": "Nobody", "entity_type": "individual"}).json()
    assert client.get(f"/api/clients/{ind['id']}/statements").status_code == 400


def test_parse_trial_balance_shapes():
    rows = statements.parse_trial_balance("Account | Debit | Credit\nCash | 1000 |\nSales |  | 5000\nRent expense | 300 |\nCommon stock |  | 100\n")
    assert [r["account"] for r in rows] == ["Cash", "Sales", "Rent expense", "Common stock"]
    st = statements.statements_from_trial_balance(rows, 2025)
    assert st["income_statement"]["Revenue"] == 5000 and st["income_statement"]["Net income"] == 4700
    assert st["balance_sheet"]["balances"] is False or st["balance_sheet"]["Total assets"] == 1000


def test_keying_sheet(client):
    c = _seed(client, "john_doe", "John & Maria Doe", "individual", "tax_1040")
    rl = client.post(f"/api/clients/{c['id']}/request-lists", json={"tax_year": 2026}).json()
    client.post(f"/api/request-lists/{rl['id']}/inbound", files=[
        ("files", ("Acme W-2 2026.txt", b"Form W-2 Wage and Tax Statement 2026\nEmployer: ACME CORPORATION\nWages: 150,000\nFederal income tax withheld: 19,000", "text/plain")),
        ("files", ("First Bank 1099-INT 2026.txt", b"Form 1099-INT Interest Income 2026\nPayer: FIRST BANK\nInterest income: 2,100", "text/plain"))])
    tr = SAMPLE / "transcripts" / "Doe_John_WageIncome_Transcript_2025.txt"
    client.post(f"/api/request-lists/{rl['id']}/reconcile-transcript", files=[("files", (tr.name, tr.read_bytes(), "text/plain"))])
    sheet = client.get(f"/api/clients/{c['id']}/keying-sheet?tax_year=2026").json()
    inputs = {r["atx_input"] for r in sheet["rows"]}
    assert "W-2 input" in inputs and "1099-INT input (Sch B)" in inputs
    w2 = next(r for r in sheet["rows"] if r["atx_input"] == "W-2 input" and r["field"] == "Wages")
    assert w2["value"] == 150000 and "Acme" in w2["source"]
    assert sheet["count"] >= 3
    x = client.get(f"/api/clients/{c['id']}/keying-sheet?tax_year=2026&format=xlsx")
    assert x.status_code == 200 and len(x.content) > 3000
    # the transcript for 2025 is not mixed into the 2026 sheet
    assert not any("transcript" in (r["source"] or "").lower() for r in sheet["rows"])


def test_brief_chat_style(client):
    c = _seed(client, "john_doe", "John & Maria Doe", "individual", "tax_1040")
    r = client.post("/api/chat", json={"question": "what did they owe last year", "client_id": c["id"], "style": "brief"})
    assert r.status_code == 200 and r.json()["answer"]
    assert client.post("/api/chat", json={"question": "x y", "client_id": c["id"], "style": "loud"}).status_code == 422
    assert client.get("/").text.count("Tax Assistant") >= 1 and client.get("/workbench").status_code == 200
