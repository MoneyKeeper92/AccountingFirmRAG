"""Structured extraction: every document becomes one canonical JSON record.

Tax-focused. The record identifies the return type (1040 / 1065 / 1120-S / 1120 / 1041 / 990),
the forms and schedules present, and a flat list of `facts` (name, value, period) so a 1040,
an 1120-S and a trial balance all feed the same planning and forecasting code.
"""
from __future__ import annotations

import re
from typing import Any

RETURN_TYPES = ["1040", "1065", "1120-S", "1120", "1041", "990", "none"]

# Fact vocabulary. Names are line-item concepts, not line numbers, so they survive form changes.
FACT_NAMES_1040 = [
    "wages", "taxable_interest", "tax_exempt_interest", "ordinary_dividends", "qualified_dividends",
    "ira_distributions_taxable", "pensions_taxable", "social_security_taxable", "capital_gain_loss",
    "schedule_c_net_profit", "schedule_e_net_income", "schedule_f_net_profit", "unemployment_compensation",
    "other_income", "total_income", "adjustments_to_income", "adjusted_gross_income",
    "standard_or_itemized_deduction", "itemized_deductions_total", "salt_deduction", "mortgage_interest_deduction",
    "charitable_contributions", "medical_expenses_deduction", "qbi_deduction", "taxable_income",
    "income_tax_before_credits", "child_tax_credit", "education_credits", "other_credits", "self_employment_tax",
    "total_tax", "federal_withholding", "estimated_payments", "refund", "amount_owed", "underpayment_penalty",
    "dependents_count", "home_office_deduction", "hsa_contributions", "ira_contributions", "student_loan_interest",
    "additional_deductions",   # TY2025 Form 1040 line 13b, Schedule 1-A
]
FACT_NAMES_ENTITY = [
    "gross_receipts", "returns_and_allowances", "cost_of_goods_sold", "gross_profit", "officer_compensation",
    "salaries_and_wages", "guaranteed_payments", "rent_expense", "interest_expense", "taxes_and_licenses",
    "depreciation", "section_179", "total_deductions", "ordinary_business_income", "net_rental_income",
    "interest_income", "dividend_income", "total_assets", "cash", "accounts_receivable", "inventory",
    "fixed_assets_net", "total_liabilities", "loans_from_shareholders", "partners_capital", "retained_earnings",
    "aaa_balance", "distributions", "number_of_owners", "corporate_taxable_income", "corporate_total_tax",
    "net_operating_loss", "state_tax", "shareholder_health_insurance", "retirement_plan_contributions",
    # books-based names (P&L / balance sheet / trial balance) so bookkeeping exports map cleanly
    "revenue", "operating_expenses", "net_income", "total_equity", "current_assets", "current_liabilities", "long_term_debt",
]
FACT_NAMES = FACT_NAMES_1040 + [n for n in FACT_NAMES_ENTITY if n not in FACT_NAMES_1040]

DOC_TYPES = [
    # returns
    "form_1040", "form_1065", "form_1120s", "form_1120", "form_1041", "form_990", "state_return", "amended_return",
    # information returns and source documents
    "w2", "1099_int", "1099_div", "1099_b", "1099_nec", "1099_misc", "1099_r", "1099_k", "1099_g", "ssa_1099",
    "1098_mortgage", "1098_t", "1098_e", "1095_a", "k1_1065", "k1_1120s", "k1_1041",
    # books and payroll
    "financial_statements", "balance_sheet", "income_statement", "trial_balance", "general_ledger", "bank_statement",
    "payroll_report", "form_941", "depreciation_schedule", "fixed_asset_register",
    # engagement paperwork
    "organizer", "engagement_letter", "irs_notice", "state_notice", "estimated_payment_record", "extension",
    "irs_transcript_wage_income", "irs_transcript_account", "irs_transcript_return",
    "w2g", "1099_da", "1099_oid", "1099_sa", "1099_s", "1099_q", "1099_c", "1099_ltc", "1099_patr", "rrb_1099", "1042_s",
    "1098_c", "1095_b", "1095_c", "5498", "5498_sa", "3921", "3922", "form_940", "form_w3", "form_1096",
    "correspondence", "prior_year_workpaper", "other",
]

FORMS = [
    # 1040 family
    "1040", "1040-SR", "1040-NR", "1040-X", "Schedule 1", "Schedule 2", "Schedule 3", "Schedule A", "Schedule B",
    "Schedule C", "Schedule D", "Schedule E", "Schedule F", "Schedule H", "Schedule SE", "Schedule 8812",
    "Form 1116", "Form 2106", "Form 2210", "Form 2441", "Form 2555", "Form 3800", "Form 4562", "Form 4797",
    "Form 4868", "Form 4952", "Form 5329", "Form 5695", "Form 6251", "Form 6252", "Form 8283", "Form 8582",
    "Form 8606", "Form 8801", "Form 8812", "Form 8829", "Form 8863", "Form 8880", "Form 8889", "Form 8938",
    "Form 8949", "Form 8959", "Form 8960", "Form 8962", "Form 8995", "Form 8995-A", "Form 1040-ES",
    # 1065 / 1120-S / 1120 family
    "1065", "1120-S", "1120", "1041", "990", "Schedule K", "Schedule K-1", "Schedule L", "Schedule M-1",
    "Schedule M-2", "Schedule M-3", "Schedule B-1", "Schedule D (1120)", "Schedule J", "Form 1125-A", "Form 1125-E",
    "Form 8825", "Form 2553", "Form 7004", "Form 1120-W", "Form 3115", "Form 4626", "Form 8990", "Form 8993",
    "Form 8996", "Form 7203", "Form 8865", "Form 5472", "Form 941", "Form 940", "W-3",
    "state return",
]

CANONICAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "doc_type": {"type": "string", "enum": DOC_TYPES},
        "return_type": {"type": "string", "enum": RETURN_TYPES, "description": "The return this document is, or belongs to; 'none' for books and correspondence"},
        "tax_year": {"type": ["integer", "null"], "description": "Primary tax year the document reports on"},
        "filing_status": {"type": ["string", "null"], "description": "1040 only: single, married filing jointly, married filing separately, head of household, qualifying surviving spouse"},
        "forms_present": {"type": "array", "items": {"type": "string", "enum": FORMS}, "description": "Every form and schedule that appears in the document"},
        "summary": {"type": "string", "description": "Two or three sentences a reviewing preparer would find useful"},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string", "description": "taxpayer, spouse, dependent, entity, shareholder, partner, officer, preparer, employer, payer, lender..."},
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
                    "source_quote": {"type": "string", "description": "The exact line the number came from, including the form and line number when visible"},
                },
                "required": ["name", "value", "period", "unit", "source_quote"],
                "additionalProperties": False,
            },
        },
        "risk_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Anything a reviewing preparer should notice: late estimates, penalties, large swings, missing schedules, elections, basis issues, notices",
        },
    },
    "required": ["doc_type", "return_type", "tax_year", "filing_status", "forms_present", "summary", "entities", "facts", "risk_flags"],
    "additionalProperties": False,
}

EXTRACTION_INSTRUCTIONS = """You are a senior tax preparer's assistant building a CPA firm's client archive.
Read the document and return the canonical JSON record.

Rules:
- Identify the return type (1040, 1065, 1120-S, 1120, 1041, 990) and list every form and schedule present.
- Only report numbers that are literally present. Never estimate or infer a value.
- For multi-year comparatives, emit one fact per year with the correct `period`.
- Use negative numbers for losses and amounts shown in parentheses.
- `unit` is the currency code (usually USD). Counts (dependents, owners) use unit "count".
- Put the form and line in `source_quote` when visible, e.g. "Form 1040 line 11 Adjusted gross income 190,020".
- Prefer totals over sub-lines when both exist.
- Form 1040 line numbers moved for tax year 2025: capital gain 7 -> 7a, adjusted gross income 11 -> 11a/11b,
  deduction 12 -> 12e, QBI deduction 13 -> 13a, new 13b (Schedule 1-A), EIC 27 -> 27a, line 30 is the refundable
  adoption credit. Map by the line's label, never by its number, and quote the number you saw.
- `risk_flags` are short and specific: "Q2 and Q3 estimates paid late; underpayment penalty assessed",
  "No officer compensation despite ordinary income of 268,000", "Distributions exceed AAA balance".
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
    record.setdefault("forms_present", [])
    record.setdefault("return_type", "none")
    record.setdefault("filing_status", None)
    if not record.get("tax_year"):
        # Fall back to the uploader's hint, then to a year in the filename ("2024 1040.pdf", "TB_FY2025.xlsx").
        if hints and hints.get("tax_year"):
            record["tax_year"] = int(hints["tax_year"])
        else:
            m = re.search(r"(?<!\d)(20[0-4]\d)(?!\d)", filename)
            if m:
                record["tax_year"] = int(m.group(1))
    return record
