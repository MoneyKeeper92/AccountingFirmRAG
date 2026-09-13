from app.ingest.chunker import chunk_pages
from app.ingest.parsers import parse_file
from app.providers.mock_llm import _regex_facts, _guess_doc_type
from tests.conftest import SAMPLE


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
    text = (SAMPLE / "abc_company" / "ABC_Company_Financial_Statements_FY2025.txt").read_text()
    chunks = chunk_pages([text], target_chars=600, overlap_chars=80)
    assert len(chunks) >= 3
    assert all(c["page"] == 1 for c in chunks)
    assert any(c["section"] and "BALANCE SHEET" in c["section"] for c in chunks)


def test_regex_extractor_on_statements():
    text = (SAMPLE / "abc_company" / "ABC_Company_Financial_Statements_FY2025.txt").read_text()
    facts = {f["name"]: f for f in _regex_facts(text)}
    assert facts["revenue"]["value"] == 5_610_000
    assert facts["net_income"]["value"] == 268_000
    assert facts["accounts_receivable"]["value"] == 1_180_000
    assert facts["revenue"]["period"] == 2025
    assert _guess_doc_type(text) == "financial_statements"


def test_regex_extractor_on_json_return():
    text = (SAMPLE / "john_doe" / "John_Doe_1040_2025_summary.json").read_text()
    facts = {f["name"]: f for f in _regex_facts(text)}
    assert facts["adjusted_gross_income"]["value"] == 190_020
    assert facts["wages"]["period"] == 2025
