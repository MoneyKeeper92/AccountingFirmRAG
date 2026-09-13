"""Tax-season document request lists.

Given last year's return and whatever else is in the client's folder, build a draft request
list, an email the preparer can send, and then track what has come back.

The list is rule-based on purpose: every item says *why* it is being asked for ("wages of
$142,500 on the 2025 return"), which is what makes the client actually respond. A configured
language model can polish the email wording; it does not decide what to ask for.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Ctx:
    client: dict
    tax_year: int                       # the year being prepared (e.g. 2026)
    prior_year: int                     # the year we have a return for (e.g. 2025)
    facts: dict[str, float]             # prior-year facts: name -> value
    text: str                           # lower-cased text of the client's prior-year documents
    doc_types: set[str]
    risk_flags: list[str]
    notes: list[str] = field(default_factory=list)
    return_type: str = "1040"           # 1040 | 1065 | 1120-S | 1120

    @property
    def entity(self) -> bool:
        return self.return_type in ("1065", "1120-S", "1120")

    def has(self, *words: str) -> bool:
        return any(w in self.text for w in words)

    def money(self, name: str) -> str:
        v = self.facts.get(name)
        return f"${v:,.0f}" if v is not None else "an amount"


@dataclass
class Rule:
    key: str
    category: str
    item: str
    when: Callable[[Ctx], bool]
    why: Callable[[Ctx], str]
    match_words: list[str]              # filename / text keywords used to auto-match inbound files


def _fact(name: str) -> Callable[[Ctx], bool]:
    return lambda c: (c.facts.get(name) or 0) != 0


ALWAYS = lambda c: True  # noqa: E731
INDIV = lambda c: not c.entity  # noqa: E731
ENTITY = lambda c: c.entity  # noqa: E731


def _and(*conds):
    return lambda c: all(f(c) for f in conds)


RULES: list[Rule] = [
    Rule("engagement_letter", "Admin", "Signed engagement letter for {year}", ALWAYS,
         lambda c: "Required before we start work each year", ["engagement"]),
    Rule("organizer", "Admin", "Completed tax organizer, or confirm nothing changed: address, dependents, bank account for direct deposit", INDIV,
         lambda c: f"Carried forward from the {c.prior_year} return; we need to know what changed", ["organizer", "questionnaire"]),
    Rule("life_changes", "Admin", "Tell us about anything new in {year}: marriage, move, new job, home sale, new business, inheritance", INDIV,
         lambda c: "Each of these changes the return", []),
    Rule("notices", "Admin", "Any IRS or state letters received during the year", INDIV,
         lambda c: "Notices often carry deadlines", ["notice", "irs letter", "cp2000"]),
    Rule("w2", "Income", "W-2 from each employer", _and(INDIV, _fact("wages")),
         lambda c: f"Wages of {c.money('wages')} on the {c.prior_year} return", ["w-2", "w2", "wage"]),
    Rule("1099_int", "Income", "1099-INT from each bank or lender", _and(INDIV, _fact("taxable_interest")),
         lambda c: f"Taxable interest of {c.money('taxable_interest')} on the {c.prior_year} return", ["1099-int", "1099int", "interest"]),
    Rule("1099_div", "Income", "1099-DIV / consolidated brokerage statement", _and(INDIV, _fact("ordinary_dividends")),
         lambda c: f"Dividends of {c.money('ordinary_dividends')} on the {c.prior_year} return", ["1099-div", "1099div", "dividend"]),
    Rule("1099_b", "Income", "1099-B and cost-basis detail for any sales of stock, RSUs or crypto", _and(INDIV, lambda c: c.has("1099-b", "capital gain", "rsu", "stock sale", "brokerage", "crypto", "form 8949", "schedule d")),
         lambda c: f"Investment sales were reported in {c.prior_year}", ["1099-b", "1099b", "broker", "consolidated", "gain", "rsu"]),
    Rule("sched_c_income", "Business", "Business income records: 1099-NEC / 1099-K, invoices or sales summary", _and(INDIV, _fact("schedule_c_net_profit")),
         lambda c: f"Schedule C net profit of {c.money('schedule_c_net_profit')} in {c.prior_year}", ["1099-nec", "1099-k", "nec", "invoice", "sales"]),
    Rule("sched_c_expenses", "Business", "Business expense summary and business bank / credit card statements", _and(INDIV, _fact("schedule_c_net_profit")),
         lambda c: "Needed to support Schedule C deductions", ["expense", "bank statement", "credit card", "p&l", "profit"]),
    Rule("home_office", "Business", "Home office: square footage, rent or mortgage interest, utilities, insurance for the year", _and(INDIV, lambda c: c.has("home office")),
         lambda c: f"Home office deduction was claimed in {c.prior_year}", ["home office", "utilities", "square"]),
    Rule("mileage", "Business", "Vehicle mileage log (business vs total miles)", _and(INDIV, lambda c: c.has("vehicle", "mileage", "auto expense")),
         lambda c: f"Vehicle expenses were deducted in {c.prior_year}", ["mileage", "vehicle"]),
    Rule("k1", "Income", "Schedule K-1 from each partnership, S corporation or trust", _and(INDIV, lambda c: c.has("k-1", "schedule k-1", "partnership", "s corp", "s-corp")),
         lambda c: "Pass-through income appeared in prior-year records", ["k-1", "k1", "schedule k"]),
    Rule("rental", "Income", "Rental property: rent received, expenses by category, 1098 for the rental mortgage", _and(INDIV, lambda c: c.has("rental", "schedule e")),
         lambda c: "Rental activity appears in prior-year records", ["rental", "rent roll", "schedule e"]),
    Rule("1098_mortgage", "Deductions", "1098 mortgage interest statement", _and(INDIV, lambda c: c.has("mortgage interest", "1098")),
         lambda c: f"Mortgage interest was deducted in {c.prior_year}", ["1098", "mortgage"]),
    Rule("property_tax", "Deductions", "Property tax bills paid in {year}", _and(INDIV, lambda c: c.has("property tax", "state and local taxes", "real estate tax", "salt")),
         lambda c: "State and local taxes were itemized", ["property tax", "real estate tax"]),
    Rule("charitable", "Deductions", "Charitable contribution receipts (letters for gifts of $250 or more)", _and(INDIV, lambda c: c.has("charitable", "donation", "contribution")),
         lambda c: f"Charitable deductions were claimed in {c.prior_year}", ["donation", "charit", "contribution", "receipt"]),
    Rule("childcare", "Credits", "Child and dependent care provider statement with tax ID and amount paid", _and(INDIV, lambda c: c.has("dependent", "childcare", "daycare")),
         lambda c: "Dependents were claimed", ["childcare", "daycare", "dependent care", "provider"]),
    Rule("1098_t", "Credits", "1098-T tuition statement and 529 distribution statements (1099-Q)", _and(INDIV, lambda c: c.has("1098-t", "tuition", "529", "college")),
         lambda c: "Education-related items appear in prior-year records", ["1098-t", "1098t", "tuition", "1099-q", "529"]),
    Rule("hsa", "Deductions", "HSA forms 1099-SA and 5498-SA", _and(INDIV, lambda c: c.has("hsa", "health savings")),
         lambda c: "HSA activity in prior year", ["1099-sa", "5498-sa", "hsa"]),
    Rule("retirement", "Income", "1099-R for retirement distributions and 5498 for IRA contributions", _and(INDIV, lambda c: c.has("1099-r", "ira", "401(k)", "pension", "retirement")),
         lambda c: "Retirement account activity in prior year", ["1099-r", "5498", "ira", "pension"]),
    Rule("1095_a", "Credits", "Form 1095-A if health insurance was bought through the marketplace", _and(INDIV, lambda c: c.has("1095", "marketplace")),
         lambda c: "Marketplace coverage appeared in prior-year records", ["1095"]),
    Rule("student_loan", "Deductions", "1098-E student loan interest", _and(INDIV, lambda c: c.has("1098-e", "student loan")),
         lambda c: "Student loan interest deducted in prior year", ["1098-e", "1098e", "student loan"]),
    Rule("estimated_payments", "Payments", "Dates and amounts of federal and state estimated tax payments made for {year}",
         _and(INDIV, lambda c: (c.facts.get("estimated_payments") or 0) != 0 or (c.facts.get("schedule_c_net_profit") or 0) > 0 or c.has("underpayment", "form 2210")),
         lambda c: f"Estimates of {c.money('estimated_payments')} were paid for {c.prior_year}; penalties apply when late", ["estimated", "1040-es", "1120-w", "es payment", "estimate"]),

    # ------------------------------------------------------------- entity returns (1065 / 1120-S / 1120)
    Rule("books", "Books", "Year-end financial statements: profit and loss, balance sheet, trial balance and general ledger export for {year}", ENTITY,
         lambda c: f"Starting point for the {c.return_type} return", ["trial balance", "general ledger", "balance sheet", "profit and loss", "p&l", "income statement", "financials"]),
    Rule("bank_statements", "Books", "December {year} bank and credit card statements with reconciliations, plus January {year} statements for cut-off", ENTITY,
         lambda c: "Needed to tie cash and confirm year-end cut-off", ["bank statement", "reconciliation", "credit card"]),
    Rule("payroll", "Payroll", "Payroll reports for {year}: four quarterly 941s, W-3/W-2s, state unemployment returns", _and(ENTITY, lambda c: (c.facts.get("salaries_and_wages") or 0) > 0 or (c.facts.get("officer_compensation") or 0) > 0),
         lambda c: f"Wages of {c.money('salaries_and_wages')} and officer compensation of {c.money('officer_compensation')} on the {c.prior_year} return", ["941", "w-3", "w3", "payroll", "unemployment"]),
    Rule("officer_comp", "Owners", "Officer / owner compensation and distributions by owner for {year}", ENTITY,
         lambda c: f"Distributions of {c.money('distributions')} in {c.prior_year}; needed for basis and reasonable-compensation support", ["distribution", "officer", "compensation", "owner draw"]),
    Rule("owner_changes", "Owners", "Any changes in ownership, new owners, buyouts or capital contributions during {year}", ENTITY,
         lambda c: "Changes ownership percentages and K-1 allocations", ["ownership", "buyout", "capital contribution", "operating agreement"]),
    Rule("1099s_issued", "Payroll", "1099-NEC / 1099-MISC forms issued to contractors for {year}, or the vendor list with amounts paid", ENTITY,
         lambda c: "Required filings; the return asks whether they were filed", ["1099-nec", "1099-misc", "contractor", "vendor"]),
    Rule("fixed_assets", "Books", "Invoices for equipment, vehicles or property bought or sold in {year}, with dates and any financing", _and(ENTITY, lambda c: (c.facts.get("depreciation") or 0) > 0 or c.has("section 179", "bonus depreciation", "equipment", "forklift", "production line", "capital plan")),
         lambda c: "Needed for the depreciation schedule and Section 179 / bonus elections", ["invoice", "equipment", "asset", "vehicle", "purchase", "financing"]),
    Rule("loans", "Books", "Year-end loan statements and any new loan agreements, including loans to or from owners", _and(ENTITY, lambda c: (c.facts.get("interest_expense") or 0) > 0 or (c.facts.get("loans_from_shareholders") or 0) > 0 or c.has("loan")),
         lambda c: "Interest expense and owner loans need documented terms", ["loan", "note", "statement", "line of credit"]),
    Rule("health_insurance", "Owners", "Health insurance premiums paid for >2% shareholders (should appear on W-2 box 1)", _and(ENTITY, lambda c: c.return_type == "1120-S"),
         lambda c: f"Shareholder health insurance of {c.money('shareholder_health_insurance')} in {c.prior_year}", ["health insurance", "premium"]),
    Rule("retirement_plan", "Deductions", "Retirement plan contributions made for {year} (SEP, SIMPLE, 401(k)) and the plan year-end statement", ENTITY,
         lambda c: "Deductible if funded by the return due date", ["401", "sep", "simple", "retirement", "pension"]),
    Rule("guaranteed_payments", "Owners", "Guaranteed payments to each partner for {year} and any changes to the partnership agreement", _and(ENTITY, lambda c: c.return_type == "1065"),
         lambda c: f"Guaranteed payments of {c.money('guaranteed_payments')} in {c.prior_year}", ["guaranteed", "partnership agreement"]),
    Rule("dividends_paid", "Owners", "Dividends declared or paid to shareholders in {year} and board minutes documenting retained-earnings plans", _and(ENTITY, lambda c: c.return_type == "1120"),
         lambda c: f"Retained earnings of {c.money('retained_earnings')} at the end of {c.prior_year}", ["dividend", "minutes", "board"]),
    Rule("state_activity", "Admin", "States where the business had employees, property, or significant sales in {year}", ENTITY,
         lambda c: "Determines state filing and nexus", ["nexus", "state", "sales by state"]),
    Rule("entity_notices", "Admin", "Any IRS or state notices received by the business during the year", ENTITY,
         lambda c: "Notices often carry deadlines", ["notice", "irs letter"]),
    Rule("entity_estimates", "Payments", "Owner (or corporate) estimated tax payments made for {year}: dates and amounts", ENTITY,
         lambda c: "Pass-through owners pay tax personally; corporations pay on Form 1120-W instalments", ["estimated", "1040-es", "1120-w", "estimate"]),
]


def build_items(ctx: Ctx) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in RULES:
        if r.when(ctx):
            items.append({"key": r.key, "category": r.category, "item": r.item.format(year=ctx.tax_year), "why": r.why(ctx)})
    # Follow-ups the preparer wrote down last year ("Ask about ...") and risk flags the extractor raised.
    for i, note in enumerate(_follow_ups(ctx)):
        items.append({"key": f"followup_{i}", "category": "Follow-up", "item": note, "why": f"Noted during the {ctx.prior_year} engagement"})
    return items


def _follow_ups(ctx: Ctx) -> list[str]:
    out: list[str] = []
    for line in ctx.notes:
        if re.search(r"\b(ask about|follow up|confirm|recommend|next year|remind)\b", line, re.I):
            out.append(line.strip().rstrip(".").strip()[:200])
    for flag in ctx.risk_flags:
        if flag and flag not in out and "scanned" not in flag.lower():
            out.append(f"Follow up: {flag.strip()[:180]}")
    seen, uniq = set(), []
    for o in out:
        if o.lower() not in seen:
            seen.add(o.lower()); uniq.append(o)
    return uniq[:8]


def draft_email(client: dict, tax_year: int, items: list[dict[str, Any]], firm_name: str = "our office") -> tuple[str, str]:
    first = (client.get("name") or "there").split("&")[0].split(",")[0].strip()
    subject = f"Documents needed for your {tax_year} tax return"
    by_cat: dict[str, list[dict]] = {}
    for it in items:
        by_cat.setdefault(it["category"], []).append(it)
    order = ["Income", "Business", "Deductions", "Credits", "Payments", "Follow-up", "Admin"]
    lines = [f"Hi {first},", "",
             f"We are getting started on your {tax_year} return. Based on last year's return, here is what we will need. "
             "Please upload to the client portal or reply to this email with attachments; send things as they arrive rather than waiting for everything.", ""]
    for cat in order + [c for c in by_cat if c not in order]:
        if cat not in by_cat:
            continue
        lines.append(f"{cat.upper()}")
        for it in by_cat[cat]:
            lines.append(f"  [ ] {it['item']}  ({it['why']})")
        lines.append("")
    lines += ["If any item no longer applies, just tell us and we will take it off the list.", "", "Thank you,", firm_name]
    return subject, "\n".join(lines)


def match_inbound(filename: str, text_head: str, pending: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the pending item an incoming file most likely satisfies. Specific tokens beat generic ones."""
    hay = (filename + " " + text_head[:600]).lower()
    rules = {r.key: r for r in RULES}
    best, best_score = None, 0
    for it in pending:
        r = rules.get(it["key"])
        words = r.match_words if r else []
        score = 0
        for w in words:
            if w in hay:
                score = max(score, len(w) + (10 if w in filename.lower() else 0))
        if score > best_score:
            best, best_score = it, score
    return best


# --------------------------------------------------------------------------- builder

def build_for_client(store, llm, client_id: str, tax_year: int | None, firm_name: str = "our office") -> dict[str, Any]:
    """Assemble context from the archive, run the rules, draft the email, store the list."""
    from . import forecast

    client = store.get_client(client_id)
    if not client:
        raise ValueError("client not found")
    records = store.canonical_records(client_id)
    years = sorted({r["tax_year"] for r in records if r.get("tax_year")})
    if tax_year is None:
        tax_year = (years[-1] + 1) if years else None
    if tax_year is None:
        raise ValueError("No documents with a tax year on file for this client; upload last year's return first")
    prior_candidates = [y for y in years if y < tax_year]
    prior_year = prior_candidates[-1] if prior_candidates else tax_year - 1

    series = forecast.series_by_metric(store.facts_for_client(client_id))
    facts = {name: by_year[prior_year] for name, by_year in series.items() if prior_year in by_year}
    for name, by_year in series.items():                       # fall back to the latest year we have
        if name not in facts and by_year:
            facts[name] = by_year[max(by_year)]

    text = store.client_text(client_id)
    notes = [ln.strip().strip('",') for ln in text.splitlines() if ln.strip()]
    risk_flags = [f for r in records for f in (r.get("risk_flags") or [])]
    # JSON exports use snake_case keys ("mortgage_interest"); normalise so the keyword rules read them like prose.
    return_type = _return_type(client, records)
    ctx = Ctx(client=client, tax_year=tax_year, prior_year=prior_year, facts=facts, text=text.replace("_", " ").lower(),
              doc_types={r.get("doc_type") for r in records}, risk_flags=risk_flags, notes=notes, return_type=return_type)
    items = build_items(ctx)
    subject, body = draft_email(client, tax_year, items, firm_name)

    if llm is not None and not llm.identity.startswith("mock"):
        try:
            polished = llm.chat(
                "You write short, warm, plain-English emails from a CPA firm to its clients. Keep every checklist item and its "
                "reason; do not add items; do not mention AI. Return only the email body.",
                [llm.user_message(f"Rewrite this request email for {client['name']} (entity type: {client.get('entity_type')}):\n\n{body}")],
            )
            if polished.text.strip():
                body = polished.text.strip()
        except Exception:      # noqa: BLE001 - the template body is always good enough to send
            pass
    result = store.create_request_list(client_id, tax_year, subject, body, items)
    result["prior_year"] = prior_year
    result["return_type"] = return_type
    return result


def _return_type(client: dict, records: list[dict]) -> str:
    by_entity = {"partnership": "1065", "llc": "1065", "s_corp": "1120-S", "c_corp": "1120", "individual": "1040", "trust": "1041"}
    votes = [r.get("return_type") for r in records if r.get("return_type") and r.get("return_type") != "none"]
    if votes:
        return max(set(votes), key=votes.count)
    return by_entity.get((client.get("entity_type") or "").lower(), "1040")


# --------------------------------------------------------------------- conditional organizer
# Yes/no questions the preparer asks (or the client answers in the portal). "yes" opens upload
# slots; "no" retires the matching items so the pending count reflects reality.

ORGANIZER_QUESTIONS: list[dict[str, Any]] = [
    {"key": "q_life_changes", "for": "1040", "text": "Any big changes in {year}: marriage, divorce, new child, move to another state?",
     "yes_items": [{"key": "life_change_docs", "category": "Admin", "item": "Details of the life change (dates, new address, dependent SSNs)", "why": "Answered yes on the organizer"}], "no_marks": []},
    {"key": "q_home", "for": "1040", "text": "Did you buy, sell or refinance a home in {year}?",
     "yes_items": [{"key": "closing_statement", "category": "Deductions", "item": "Closing statement (and 1099-S if you sold)", "why": "Home purchase / sale / refinance in the year"}], "no_marks": []},
    {"key": "q_childcare", "for": "1040", "text": "Did you pay for childcare or dependent care in {year}?", "yes_items": ["childcare"], "no_marks": ["childcare"]},
    {"key": "q_education", "for": "1040", "text": "Did anyone in the household pay tuition or take 529 withdrawals?", "yes_items": ["1098_t"], "no_marks": ["1098_t"]},
    {"key": "q_investments", "for": "1040", "text": "Did you sell any stock, RSUs, crypto or other investments?", "yes_items": ["1099_b"], "no_marks": ["1099_b"]},
    {"key": "q_side_income", "for": "1040", "text": "Any self-employment, gig or 1099-NEC income?", "yes_items": ["sched_c_income", "sched_c_expenses", "estimated_payments"], "no_marks": ["sched_c_income", "sched_c_expenses", "home_office", "mileage"]},
    {"key": "q_rental", "for": "1040", "text": "Did you own rental property in {year}?", "yes_items": ["rental"], "no_marks": ["rental"]},
    {"key": "q_retirement", "for": "1040", "text": "Did you contribute to or withdraw from an IRA, 401(k) or HSA?", "yes_items": ["retirement", "hsa"], "no_marks": ["retirement", "hsa"]},
    {"key": "q_marketplace", "for": "1040", "text": "Was anyone covered by health insurance from the marketplace (Form 1095-A)?", "yes_items": ["1095_a"], "no_marks": ["1095_a"]},
    {"key": "q_estimates", "for": "1040", "text": "Did you make any estimated tax payments for {year}?", "yes_items": ["estimated_payments"], "no_marks": ["estimated_payments"]},
    {"key": "q_charity", "for": "1040", "text": "Did you give more than $250 to any single charity?", "yes_items": ["charitable"], "no_marks": []},
    {"key": "q_notices", "for": "both", "text": "Did you receive any letters from the IRS or a state?", "yes_items": ["notices", "entity_notices"], "no_marks": ["notices", "entity_notices"]},
    {"key": "q_assets", "for": "entity", "text": "Did the business buy or sell equipment, vehicles or property in {year}?", "yes_items": ["fixed_assets"], "no_marks": ["fixed_assets"]},
    {"key": "q_owners", "for": "entity", "text": "Any change in owners, ownership percentages or capital contributions?", "yes_items": ["owner_changes"], "no_marks": ["owner_changes"]},
    {"key": "q_contractors", "for": "entity", "text": "Did the business pay any contractor more than $600?", "yes_items": ["1099s_issued"], "no_marks": ["1099s_issued"]},
    {"key": "q_loans", "for": "entity", "text": "Any new loans, lines of credit, or loans to/from owners?", "yes_items": ["loans"], "no_marks": []},
    {"key": "q_states", "for": "entity", "text": "Did the business have employees, property or significant sales in a new state?", "yes_items": ["state_activity"], "no_marks": ["state_activity"]},
    {"key": "q_retirement_plan", "for": "entity", "text": "Did the business fund a retirement plan for {year}?", "yes_items": ["retirement_plan"], "no_marks": ["retirement_plan"]},
]


def organizer_for(return_type: str, tax_year: int) -> list[dict[str, Any]]:
    kind = "entity" if return_type in ("1065", "1120-S", "1120") else "1040"
    return [{**q, "text": q["text"].format(year=tax_year)} for q in ORGANIZER_QUESTIONS if q["for"] in (kind, "both")]


def apply_organizer_answer(store, rl: dict, question: dict[str, Any], answer: str | None) -> dict[str, int]:
    """yes -> make sure the linked items exist and are pending; no -> retire linked rule items."""
    rules = {r.key: r for r in RULES}
    by_key = store.items_by_key(rl["id"])
    added = reopened = retired = 0
    if answer == "yes":
        for spec in question["yes_items"]:
            if isinstance(spec, str):
                r = rules.get(spec)
                if not r:
                    continue
                existing = by_key.get(spec)
                if existing:
                    if existing["status"] == "not_applicable":
                        store.set_request_item(existing["id"], "pending"); reopened += 1
                else:
                    store.add_request_item(rl["id"], r.item.format(year=rl["tax_year"]), "Answered yes on the organizer", r.category, key=spec); added += 1
            else:
                existing = by_key.get(spec["key"])
                if existing:
                    if existing["status"] == "not_applicable":
                        store.set_request_item(existing["id"], "pending"); reopened += 1
                else:
                    store.add_request_item(rl["id"], spec["item"].format(year=rl["tax_year"]), spec["why"], spec["category"], key=spec["key"]); added += 1
    elif answer == "no":
        for key in question["no_marks"]:
            existing = by_key.get(key)
            if existing and existing["status"] == "pending":
                store.set_request_item(existing["id"], "not_applicable", note="Answered no on the organizer"); retired += 1
    return {"added": added, "reopened": reopened, "retired": retired}
