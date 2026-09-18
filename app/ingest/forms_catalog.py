"""Catalog of the IRS forms the archive recognises.

One entry per form or schedule: how to spot it in text or a filename, what document type it
becomes, which request-list item it satisfies, and a one-line plain-English description a
non-technical preparer can read on the dashboard. Detection order matters: entity returns
before individual, specific 1099 variants before generic ones, K-1 before its parent return.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FormSpec:
    code: str                       # "1099-INT"
    name: str                       # "Interest income"
    family: str                     # return | schedule | source | entity_schedule | payroll | notice | engagement | books
    doc_type: str                   # value stored on documents.doc_type
    patterns: tuple[str, ...]       # regexes, case-insensitive, matched against the document head + filename
    request_key: str | None = None  # request-list rule key this document satisfies
    return_type: str | None = None  # 1040 | 1065 | 1120-S | 1120 | 1041 | 990
    plain: str = ""                 # what it is, for the dashboard


# fmt: off
CATALOG: list[FormSpec] = [
    # ---- K-1s first (they mention the parent form)
    FormSpec("K-1 (1120-S)", "S corporation shareholder share", "source", "k1_1120s", (r"schedule\s+k-?1[^\n]{0,60}1120-?s", r"\bk-?1\b[^\n]{0,40}\b1120-?s\b"), "k1", "1120-S", "Shareholder's share of an S corporation's income"),
    FormSpec("K-1 (1041)", "Beneficiary share of a trust or estate", "source", "k1_1041", (r"schedule\s+k-?1[^\n]{0,60}1041", r"\bk-?1\b[^\n]{0,40}\b1041\b"), "k1", "1041", "Beneficiary's share of trust or estate income"),
    FormSpec("K-1 (1065)", "Partner share of partnership income", "source", "k1_1065", (r"schedule\s+k-?1[^\n]{0,60}1065", r"schedule\s+k-?1", r"\bk-?1\b"), "k1", "1065", "Partner's share of a partnership's income"),
    # ---- entity and individual returns
    FormSpec("1120-S", "S corporation return", "return", "form_1120s", (r"form\s+1120-?s\b", r"\b1120-?s\b", r"s\s+corporation\s+income\s+tax\s+return"), None, "1120-S", "The S corporation's annual return"),
    FormSpec("1065", "Partnership return", "return", "form_1065", (r"form\s+1065\b", r"\b1065\b", r"return\s+of\s+partnership\s+income"), None, "1065", "The partnership's annual return"),
    FormSpec("1120", "C corporation return", "return", "form_1120", (r"form\s+1120\b(?!-?(?:s|w)\b)", r"\b1120\b(?!-?(?:s|w)\b)", r"corporation\s+income\s+tax\s+return"), None, "1120", "The C corporation's annual return"),
    FormSpec("1041", "Trust or estate return", "return", "form_1041", (r"form\s+1041\b", r"\b1041\b"), None, "1041", "Income tax return for a trust or estate"),
    FormSpec("990", "Nonprofit return", "return", "form_990", (r"form\s+990(?:-?ez|-?pf)?\b",), None, "990", "Annual information return for a nonprofit"),
    FormSpec("Form 1040-ES", "Estimated payments", "schedule", "estimated_payment_record", (r"1040-?es\b", r"estimated\s+tax\s+(?:payment\s+)?voucher"), "estimated_payments", "1040", "Quarterly estimated tax vouchers or payment records"),
    FormSpec("1040-X", "Amended individual return", "return", "amended_return", (r"form\s+1040-?x\b", r"amended\s+u\.?s\.?\s+individual"), None, "1040", "An amended individual return"),
    FormSpec("1040", "Individual return", "return", "form_1040", (r"form\s+1040(?:-?sr|-?nr)?\b(?!-?(?:es|x|v)\b)", r"\b1040\b(?!-?(?:es|x|v|sr|nr)\b)", r"individual\s+income\s+tax\s+return"), None, "1040", "The individual (personal) return"),
    # ---- wage and income source documents
    FormSpec("W-2", "Wages", "source", "w2", (r"\bw-?2\b(?!\s*g)", r"wage\s+and\s+tax\s+statement"), "w2", None, "What an employer paid and withheld"),
    FormSpec("W-2G", "Gambling winnings", "source", "w2g", (r"\bw-?2\s*g\b", r"certain\s+gambling\s+winnings"), None, None, "Gambling winnings and withholding"),
    FormSpec("1099-NEC", "Contractor income", "source", "1099_nec", (r"1099-?nec", r"nonemployee\s+compensation"), "sched_c_income", None, "Pay received as a contractor"),
    FormSpec("1099-MISC", "Miscellaneous income", "source", "1099_misc", (r"1099-?misc",), "sched_c_income", None, "Rents, royalties, prizes and other income"),
    FormSpec("1099-K", "Card and app payments", "source", "1099_k", (r"1099-?k\b",), "sched_c_income", None, "Payments received through cards or apps"),
    FormSpec("1099-INT", "Interest", "source", "1099_int", (r"1099-?int", r"interest\s+income\s+statement"), "1099_int", None, "Interest paid by a bank or lender"),
    FormSpec("1099-DIV", "Dividends", "source", "1099_div", (r"1099-?div", r"dividends\s+and\s+distributions"), "1099_div", None, "Dividends and capital gain distributions"),
    FormSpec("1099-B", "Investment sales", "source", "1099_b", (r"1099-?b\b", r"proceeds\s+from\s+broker"), "1099_b", None, "Sales of stock and other investments"),
    FormSpec("1099-DA", "Digital asset sales", "source", "1099_da", (r"1099-?da\b", r"digital\s+asset\s+proceeds"), "1099_b", None, "Sales of crypto and other digital assets"),
    FormSpec("1099-OID", "Original issue discount", "source", "1099_oid", (r"1099-?oid",), "1099_int", None, "Interest on discounted bonds"),
    FormSpec("1099-R", "Retirement distributions", "source", "1099_r", (r"1099-?r\b", r"distributions\s+from\s+pensions"), "retirement", None, "Money taken from a retirement account or pension"),
    FormSpec("1099-G", "Government payments", "source", "1099_g", (r"1099-?g\b", r"certain\s+government\s+payments"), None, None, "Unemployment or a state tax refund"),
    FormSpec("1099-SA", "HSA distributions", "source", "1099_sa", (r"1099-?sa\b",), "hsa", None, "Money taken from a health savings account"),
    FormSpec("1099-S", "Real estate sale", "source", "1099_s", (r"1099-?s\b(?!a)", r"proceeds\s+from\s+real\s+estate"), None, None, "Proceeds from selling real estate"),
    FormSpec("1099-Q", "Education account payments", "source", "1099_q", (r"1099-?q\b",), "1098_t", None, "Payments from a 529 or Coverdell account"),
    FormSpec("1099-C", "Cancelled debt", "source", "1099_c", (r"1099-?c\b", r"cancellation\s+of\s+debt"), None, None, "Debt that was forgiven"),
    FormSpec("1099-LTC", "Long-term care benefits", "source", "1099_ltc", (r"1099-?ltc",), None, None, "Long-term care insurance payments"),
    FormSpec("1099-PATR", "Cooperative distributions", "source", "1099_patr", (r"1099-?patr",), None, None, "Distributions from a cooperative"),
    FormSpec("SSA-1099", "Social Security benefits", "source", "ssa_1099", (r"ssa-?1099", r"social\s+security\s+benefit\s+statement"), "retirement", None, "Social Security benefits paid"),
    FormSpec("RRB-1099", "Railroad retirement", "source", "rrb_1099", (r"rrb-?1099",), "retirement", None, "Railroad retirement benefits"),
    FormSpec("1042-S", "Foreign person US income", "source", "1042_s", (r"1042-?s\b",), None, None, "US income paid to a foreign person"),
    FormSpec("1098", "Mortgage interest", "source", "1098_mortgage", (r"\b1098\b(?!-)", r"mortgage\s+interest\s+statement"), "1098_mortgage", None, "Mortgage interest paid to a lender"),
    FormSpec("1098-T", "Tuition", "source", "1098_t", (r"1098-?t\b", r"tuition\s+statement"), "1098_t", None, "Tuition paid to a school"),
    FormSpec("1098-E", "Student loan interest", "source", "1098_e", (r"1098-?e\b", r"student\s+loan\s+interest\s+statement"), "student_loan", None, "Student loan interest paid"),
    FormSpec("1098-C", "Vehicle donation", "source", "1098_c", (r"1098-?c\b",), "charitable", None, "A donated vehicle, boat or plane"),
    FormSpec("1095-A", "Marketplace health coverage", "source", "1095_a", (r"1095-?a\b", r"health\s+insurance\s+marketplace\s+statement"), "1095_a", None, "Health insurance bought through the marketplace"),
    FormSpec("1095-B", "Health coverage", "source", "1095_b", (r"1095-?b\b",), None, None, "Proof of health coverage"),
    FormSpec("1095-C", "Employer health coverage", "source", "1095_c", (r"1095-?c\b",), None, None, "Employer-offered health coverage"),
    FormSpec("5498", "IRA contributions", "source", "5498", (r"\b5498\b(?!-)", r"ira\s+contribution\s+information"), "retirement", None, "Contributions to an IRA"),
    FormSpec("5498-SA", "HSA contributions", "source", "5498_sa", (r"5498-?sa\b",), "hsa", None, "Contributions to a health savings account"),
    FormSpec("3921", "Incentive stock options", "source", "3921", (r"\b3921\b",), "1099_b", None, "Exercise of incentive stock options"),
    FormSpec("3922", "Employee stock purchase plan", "source", "3922", (r"\b3922\b",), "1099_b", None, "Shares bought through an employee plan"),
    # ---- 1040 schedules and forms (when filed as standalone pages)
    FormSpec("Schedule C", "Business profit or loss", "schedule", "form_1040", (r"schedule\s+c\b", r"profit\s+or\s+loss\s+from\s+business"), None, "1040", "Self-employment income and expenses"),
    FormSpec("Schedule E", "Rental and pass-through income", "schedule", "form_1040", (r"schedule\s+e\b", r"supplemental\s+income\s+and\s+loss"), None, "1040", "Rental, royalty and K-1 income"),
    FormSpec("Schedule D", "Capital gains", "schedule", "form_1040", (r"schedule\s+d\b", r"capital\s+gains\s+and\s+losses"), None, "1040", "Gains and losses on investments"),
    FormSpec("Schedule A", "Itemized deductions", "schedule", "form_1040", (r"schedule\s+a\b", r"itemized\s+deductions"), None, "1040", "Mortgage interest, taxes, charity, medical"),
    FormSpec("Schedule B", "Interest and dividends", "schedule", "form_1040", (r"schedule\s+b\b",), None, "1040", "Interest and dividend detail"),
    FormSpec("Schedule F", "Farm income", "schedule", "form_1040", (r"schedule\s+f\b", r"profit\s+or\s+loss\s+from\s+farming"), None, "1040", "Farm income and expenses"),
    FormSpec("Schedule SE", "Self-employment tax", "schedule", "form_1040", (r"schedule\s+se\b",), None, "1040", "Social Security and Medicare tax on self-employment"),
    FormSpec("Schedule H", "Household employment", "schedule", "form_1040", (r"schedule\s+h\b",), None, "1040", "Taxes for household employees"),
    FormSpec("Form 8949", "Investment sale detail", "schedule", "form_1040", (r"form\s+8949\b",), None, "1040", "Each investment sale, matched to the 1099-B"),
    FormSpec("Form 8995", "QBI deduction", "schedule", "form_1040", (r"form\s+8995(?:-a)?\b",), None, "1040", "The 20% deduction for business income"),
    FormSpec("Form 4562", "Depreciation", "schedule", "depreciation_schedule", (r"form\s+4562\b", r"depreciation\s+and\s+amortization"), None, None, "Depreciation of equipment and property"),
    FormSpec("Form 2441", "Child care credit", "schedule", "form_1040", (r"form\s+2441\b",), None, "1040", "Credit for child and dependent care"),
    FormSpec("Form 8863", "Education credits", "schedule", "form_1040", (r"form\s+8863\b",), None, "1040", "Education credits"),
    FormSpec("Form 8889", "HSA", "schedule", "form_1040", (r"form\s+8889\b",), None, "1040", "Health savings account contributions and distributions"),
    FormSpec("Form 2210", "Underpayment penalty", "schedule", "form_1040", (r"form\s+2210\b",), None, "1040", "Penalty for underpaying estimates"),
    FormSpec("Form 4868", "Extension", "schedule", "extension", (r"form\s+4868\b", r"automatic\s+extension\s+of\s+time"), None, "1040", "Extension to file an individual return"),
    FormSpec("Form 7004", "Business extension", "schedule", "extension", (r"form\s+7004\b",), None, None, "Extension to file a business return"),
    FormSpec("Form 1120-W", "Corporate estimates", "schedule", "estimated_payment_record", (r"1120-?w\b",), "entity_estimates", "1120", "Corporate estimated tax worksheet"),
    FormSpec("Form 7203", "S corp shareholder basis", "entity_schedule", "form_1120s", (r"form\s+7203\b",), None, "1120-S", "Shareholder stock and debt basis"),
    FormSpec("Form 2553", "S election", "entity_schedule", "correspondence", (r"form\s+2553\b", r"election\s+by\s+a\s+small\s+business\s+corporation"), None, "1120-S", "The election to be taxed as an S corporation"),
    FormSpec("Form 8825", "Partnership rental income", "entity_schedule", "form_1065", (r"form\s+8825\b",), None, "1065", "Rental real estate income of a partnership"),
    # ---- payroll and information-return filings
    FormSpec("941", "Quarterly payroll return", "payroll", "form_941", (r"form\s+941\b", r"\b941\b", r"employer'?s\s+quarterly\s+federal\s+tax\s+return"), "payroll", None, "Quarterly payroll taxes filed by the business"),
    FormSpec("940", "Annual unemployment return", "payroll", "form_940", (r"form\s+940\b", r"\b940\b"), "payroll", None, "Federal unemployment tax return"),
    FormSpec("W-3", "W-2 transmittal", "payroll", "form_w3", (r"\bw-?3\b", r"transmittal\s+of\s+wage"), "payroll", None, "Summary of all W-2s issued"),
    FormSpec("1096", "1099 transmittal", "payroll", "form_1096", (r"\b1096\b",), "1099s_issued", None, "Summary of all 1099s issued"),
    # ---- books and engagement paperwork
    FormSpec("Trial balance", "Trial balance", "books", "trial_balance", (r"trial\s+balance", r"\btb\b"), "books", None, "Every account with its year-end balance"),
    FormSpec("General ledger", "General ledger", "books", "general_ledger", (r"general\s+ledger", r"\bgl\s+detail\b"), "books", None, "Every transaction by account"),
    FormSpec("Financial statements", "Financial statements", "books", "financial_statements", (r"balance\s+sheet[\s\S]{0,400}(?:income\s+statement|profit\s+and\s+loss)", r"financial\s+statements"), "books", None, "Balance sheet and income statement"),
    FormSpec("Balance sheet", "Balance sheet", "books", "balance_sheet", (r"balance\s+sheet",), "books", None, "What the business owns and owes"),
    FormSpec("Income statement", "Income statement", "books", "income_statement", (r"income\s+statement", r"profit\s+and\s+loss", r"\bp&l\b"), "books", None, "Revenue and expenses for the year"),
    FormSpec("Bank statement", "Bank statement", "books", "bank_statement", (r"bank\s+statement", r"statement\s+of\s+account", r"checking\s+account\s+statement"), "bank_statements", None, "Monthly bank activity"),
    FormSpec("Payroll report", "Payroll report", "payroll", "payroll_report", (r"payroll\s+(?:summary|report|register|journal)",), "payroll", None, "Payroll summary from the payroll provider"),
    FormSpec("Depreciation schedule", "Depreciation schedule", "books", "depreciation_schedule", (r"depreciation\s+schedule", r"fixed\s+asset\s+(?:register|listing|schedule)"), "fixed_assets", None, "List of assets and their depreciation"),
    FormSpec("IRS transcript", "IRS wage and income transcript", "notice", "irs_transcript_wage_income", (r"wage\s+and\s+income\s+transcript",), None, "1040", "What the IRS received from employers and payers"),
    FormSpec("IRS account transcript", "IRS account transcript", "notice", "irs_transcript_account", (r"account\s+transcript",), None, None, "IRS record of the account: balances, payments, penalties"),
    FormSpec("IRS notice", "IRS letter or notice", "notice", "irs_notice", (r"(?:irs|internal\s+revenue\s+service)[\s\S]{0,120}(?:notice|letter)", r"notice\s+(?:cp|lt)\s?\d+", r"\bcp2000\b"), "notices", None, "A letter from the IRS"),
    FormSpec("State notice", "State tax notice", "notice", "state_notice", (r"department\s+of\s+revenue[\s\S]{0,120}notice", r"franchise\s+tax\s+board[\s\S]{0,120}notice"), "notices", None, "A letter from a state tax agency"),
    FormSpec("Organizer", "Tax organizer", "engagement", "organizer", (r"tax\s+organizer", r"\borganizer\b", r"questionnaire"), "organizer", None, "The client's answers about the year"),
    FormSpec("Engagement letter", "Engagement letter", "engagement", "engagement_letter", (r"engagement\s+letter",), "engagement_letter", None, "The signed agreement for this year's work"),
    FormSpec("State return", "State tax return", "return", "state_return", (r"state\s+(?:income\s+)?tax\s+return", r"form\s+(?:it-201|540|m1|il-1040|pa-40|nj-1040|d-400|ia\s*1040)\b"), None, None, "A state income tax return"),
]
# fmt: on

_COMPILED = [(spec, [re.compile(p, re.I) for p in spec.patterns]) for spec in CATALOG]
BY_DOC_TYPE = {spec.doc_type: spec for spec in CATALOG}


def detect(text: str, filename: str = "") -> FormSpec | None:
    """First catalog entry whose pattern matches. Two passes: the document's first lines (a return's
    own title) win over anything mentioned further down (a 1065 that talks about its K-1s), then the
    wider head plus the filename."""
    title = text[:220].lower()
    best: tuple[int, int, FormSpec] | None = None          # (match position, catalog order, spec)
    for order, (spec, pats) in enumerate(_COMPILED):
        for p in pats:
            m = p.search(title)
            if m and (best is None or (m.start(), order) < (best[0], best[1])):
                best = (m.start(), order, spec)
    if best:
        return best[2]
    head = (filename.replace("_", " ").replace("-", " ") + "\n" + text[:1500]).lower()
    fn = filename.lower().replace("_", " ")
    for spec, pats in _COMPILED:
        for p in pats:
            if p.search(head) or p.search(fn):
                return spec
    return None


def forms_for_dashboard() -> list[dict]:
    families = {"return": "Returns", "schedule": "1040 schedules and forms", "entity_schedule": "Business return schedules",
                "source": "Income and deduction documents", "payroll": "Payroll filings", "books": "Books and records",
                "notice": "IRS and state letters", "engagement": "Engagement paperwork"}
    return [{"code": s.code, "name": s.name, "family": families.get(s.family, s.family), "plain": s.plain} for s in CATALOG]
