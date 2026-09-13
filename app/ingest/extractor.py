"""Structured extraction: every document becomes one canonical JSON record.

The schema is deliberately small. Facts are (name, value, period) triples so
the forecasting tools can work across tax returns, financial statements and
trial balances alike. Extend FACT_NAMES as the practice needs.
"""
from __future__ import annotations

import re
from typing import Any

FACT_NAMES = [
    "revenue", "cost_of_goods_sold", "gross_profit", "operating_expenses", "net_income",
    "total_assets", "current_assets", "cash", "accounts_receivable", "inventory",
    "total_liabilities", "current_liabilities", "long_term_debt", "total_equity",
    "wages", "interest_income", "dividend_income", "schedule_c_net_profit",
    "adjusted_gross_income", "taxable_income", "total_tax", "estimated_payments",
    "depreciation", "capital_expenditures", "distributions", "retained_earnings",
]

DOC_TYPES = [
    "individual_tax_return", "business_tax_return", "financial_statements", "balance_sheet",
    "income_statement", "cash_flow_statement", "trial_balance", "general_ledger", "audit_workpaper",
    "audit_report", "management_letter", "engagement_letter", "bank_statement", "payroll_report",
    "w2_1099", "k1", "fixed_asset_register", "correspondence", "other",
]

CANONICAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "doc_type": {"type": "string", "enum": DOC_TYPES},
        "tax_year": {"type": ["integer", "null"], "description": "Primary tax/fiscal year the document reports on"},
        "summary": {"type": "string", "description": "Two or three sentences a partner would find useful"},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string", "description": "taxpayer, spouse, entity, preparer, bank, customer, vendor..."},
                },
                "required": ["name", "role"],
                "additionalProperties": False,
            },
        },
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": FACT_NAMES},
                    "value": {"type": "number"},
                    "period": {"type": ["integer", "null"]},
                    "unit": {"type": "string"},
                    "source_quote": {"type": "string", "description": "The exact line the number came from"},
                },
                "required": ["name", "value", "period", "unit", "source_quote"],
                "additionalProperties": False,
            },
        },
        "risk_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Anything unusual an auditor/preparer should notice: qualified opinions, related-party notes, late filings, large swings, missing schedules",
        },
    },
    "required": ["doc_type", "tax_year", "summary", "entities", "facts", "risk_flags"],
    "additionalProperties": False,
}

EXTRACTION_INSTRUCTIONS = """You are a senior accountant's assistant preparing a firm's client archive.
Read the document and return the canonical JSON record.

Rules:
- Only report numbers that are literally present. Never estimate or infer a value.
- For multi-year comparative statements, emit one fact per year with the correct `period`.
- Use negative numbers for losses and amounts shown in parentheses.
- `unit` is the currency code (usually USD). Do not scale numbers - if the statement says "in thousands", multiply out.
- Prefer totals over sub-lines when both exist (e.g. total revenue rather than product-line revenue).
- `risk_flags` should be short, specific, and phrased for a reviewing partner.
"""


def extract_canonical(llm, text: str, filename: str, hints: dict[str, Any] | None = None) -> dict[str, Any]:
    hint_text = ""
    if hints:
        hint_text = "\nKnown context (from the person who uploaded the file): " + ", ".join(f"{k}={v}" for k, v in hints.items() if v)
    prompt = f"Filename: {filename}{hint_text}\n\n<document>\n{text[:400_000]}\n</document>"
    record = llm.extract_json(EXTRACTION_INSTRUCTIONS, prompt, CANONICAL_SCHEMA)
    record.setdefault("entities", [])
    record.setdefault("facts", [])
    record.setdefault("risk_flags", [])
    if not record.get("tax_year"):
        # Fall back to the uploader's hint, then to a year in the filename ("2024 1040.pdf", "TB_FY2025.xlsx").
        if hints and hints.get("tax_year"):
            record["tax_year"] = int(hints["tax_year"])
        else:
            m = re.search(r"(?<!\d)(20[0-4]\d)(?!\d)", filename)
            if m:
                record["tax_year"] = int(m.group(1))
    return record
