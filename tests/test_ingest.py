from app.ingest.chunker import chunk_pages
from app.ingest.parsers import parse_file
from app.providers.mock_llm import MockLLM, _forms_present, _guess_doc_type, _regex_facts
from app.ingest.extractor import CANONICAL_SCHEMA
from app.config import SlotConfig
from tests.conftest import SAMPLE

S_CORP_2025 = SAMPLE / "abc_company" / "ABC_Company_1120S_2025.txt"


def test_csv_parser_reads_label_value_rows():
    p = parse_file("tb.csv", b"Account,Debit,Credit\nCash,148000,\nSales,,5610000\n")
    assert p.kind == "csv"
    assert "Cash | 148000" in p.text and "Sales |  | 5610000" in p.text


def test_json_parser_pretty_prints():
    p = parse_file("x.json", b'{"tax_year": 2025, "adjusted_gross_income": 190020}')
    assert '"tax_year": 2025' in p.text


def test_unsupported_extension():
    import pytest
    with pytest.raises(ValueError):
        parse_file("photo.heic", b"...")


def test_chunker_keeps_page_and_section():
    text = S_CORP_2025.read_text()
    chunks = chunk_pages([text], target_chars=500, overlap_chars=80)
    assert len(chunks) >= 3
    assert all(c["page"] == 1 for c in chunks)
    assert any(c["section"] and "DEDUCTIONS" in c["section"] for c in chunks)


def test_regex_extractor_on_1120s():
    text = S_CORP_2025.read_text()
    facts = {f["name"]: f for f in _regex_facts(text)}
    assert facts["gross_receipts"]["value"] == 5_610_000
    assert facts["cost_of_goods_sold"]["value"] == 3_640_000          # "(Form 1125-A)" between label and amount
    assert facts["officer_compensation"]["value"] == 120_000           # "(Form 1125-E)"
    assert facts["distributions"]["value"] == 328_000
    assert facts["aaa_balance"]["value"] == 920_000
    assert facts["retained_earnings"]["value"] == 1_005_000
    assert facts["loans_from_shareholders"]["value"] == 150_000
    assert facts["number_of_owners"]["unit"] == "count"
    assert facts["gross_receipts"]["period"] == 2025
    assert _guess_doc_type(text) == "form_1120s"
    forms = _forms_present(text)
    assert {"1120-S", "Schedule K", "Schedule L", "Schedule M-2", "Form 1125-E", "Form 7203"} <= set(forms)
    assert "1120" not in forms


def test_trial_balance_rows_extract():
    text = parse_file("tb.csv", (SAMPLE / "abc_company" / "ABC_Company_Trial_Balance_2025.csv").read_bytes()).text
    facts = {f["name"]: f["value"] for f in _regex_facts(text)}
    assert facts["retained_earnings"] == 1_065_000 and facts["cash"] == 148_000 and facts["revenue"] == 5_610_000
    assert _guess_doc_type(text, "ABC_Company_Trial_Balance_2025.csv") == "trial_balance"
    assert _guess_doc_type("Account | Debit | Credit", "1120S_2025.pdf") == "form_1120s"


def test_regex_extractor_on_1040_json():
    text = (SAMPLE / "john_doe" / "John_Doe_1040_2025_summary.json").read_text()
    facts = {f["name"]: f for f in _regex_facts(text)}
    assert facts["adjusted_gross_income"]["value"] == 191_022
    assert facts["wages"]["period"] == 2025
    assert facts["underpayment_penalty"]["value"] == 96
    assert _guess_doc_type(text) == "form_1040"
    assert {"Schedule A", "Schedule C", "Schedule D", "Form 8949", "Form 2210"} <= set(_forms_present(text))


def test_1120_taxable_income_is_corporate_and_prompt_wrapper_ignored():
    mock = MockLLM(SlotConfig.from_dict({"provider": "mock"}))
    text = (SAMPLE / "northline_corp" / "Northline_Distribution_1120_2025.txt").read_text()
    wrapped = f"Filename: x.txt\nKnown context: client_id=abc, engagement=tax_1120s\n\n<document>\n{text}\n</document>"
    rec = mock.extract_json("i", wrapped, CANONICAL_SCHEMA)
    assert rec["doc_type"] == "form_1120" and rec["return_type"] == "1120"
    names = {f["name"]: f["value"] for f in rec["facts"]}
    assert names["corporate_taxable_income"] == 286_000 and names["corporate_total_tax"] == 60_060
    assert "taxable_income" not in names
    assert not rec["summary"].startswith("Filename")
    p = (SAMPLE / "riverbend_partners" / "Riverbend_Partners_1065_2025.txt").read_text()
    rec = mock.extract_json("i", p, CANONICAL_SCHEMA)
    assert rec["return_type"] == "1065" and "Form 8825" in rec["forms_present"]
    assert {f["name"]: f["value"] for f in rec["facts"]}["net_rental_income"] == 41_000
