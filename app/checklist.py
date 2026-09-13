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

RULES: list[Rule] = [
    Rule("engagement_letter", "Admin", "Signed engagement letter for {year}", ALWAYS,
         lambda c: "Required before we start work each year", ["engagement"]),
    Rule("organizer", "Admin", "Completed tax organizer, or confirm nothing changed: address, dependents, bank account for direct deposit", ALWAYS,
         lambda c: f"Carried forward from the {c.prior_year} return; we need to know what changed", ["organizer", "questionnaire"]),
    Rule("life_changes", "Admin", "Tell us about anything new in {year}: marriage, move, new job, home sale, new business, inheritance", ALWAYS,
         lambda c: "Each of these changes the return", []),
    Rule("notices", "Admin", "Any IRS or state letters received during the year", ALWAYS,
         lambda c: "Notices often carry deadlines", ["notice", "irs letter", "cp2000"]),
    Rule("w2", "Income", "W-2 from each employer", _fact("wages"),
         lambda c: f"Wages of {c.money('wages')} on the {c.prior_year} return", ["w-2", "w2", "wage"]),
    Rule("1099_int", "Income", "1099-INT from each bank or lender", _fact("interest_income"),
         lambda c: f"Interest income of {c.money('interest_income')} in {c.prior_year}", ["1099-int", "1099int", "interest"]),
    Rule("1099_div", "Income", "1099-DIV / consolidated brokerage statement", _fact("dividend_income"),
         lambda c: f"Dividends of {c.money('dividend_income')} in {c.prior_year}", ["1099-div", "1099div", "dividend"]),
    Rule("1099_b", "Income", "1099-B and cost-basis detail for any sales of stock, RSUs or crypto", lambda c: c.has("1099-b", "capital gain", "rsu", "stock sale", "brokerage", "crypto"),
         lambda c: f"Investment sales were reported in {c.prior_year}", ["1099-b", "1099b", "broker", "consolidated", "gain", "rsu"]),
    Rule("sched_c_income", "Business", "Business income records: 1099-NEC / 1099-K, invoices or sales summary", _fact("schedule_c_net_profit"),
         lambda c: f"Schedule C net profit of {c.money('schedule_c_net_profit')} in {c.prior_year}", ["1099-nec", "1099-k", "nec", "invoice", "sales"]),
    Rule("sched_c_expenses", "Business", "Business expense summary and business bank / credit card statements", _fact("schedule_c_net_profit"),
         lambda c: "Needed to support Schedule C deductions", ["expense", "bank statement", "credit card", "p&l", "profit"]),
    Rule("home_office", "Business", "Home office: square footage, rent or mortgage interest, utilities, insurance for the year", lambda c: c.has("home office"),
         lambda c: f"Home office deduction was claimed in {c.prior_year}", ["home office", "utilities", "square"]),
    Rule("mileage", "Business", "Vehicle mileage log (business vs total miles)", lambda c: c.has("vehicle", "mileage", "auto expense"),
         lambda c: f"Vehicle expenses were deducted in {c.prior_year}", ["mileage", "vehicle"]),
    Rule("k1", "Income", "Schedule K-1 from each partnership, S corporation or trust", lambda c: c.has("k-1", "schedule k", "partnership", "s corp", "s-corp"),
         lambda c: "Pass-through income appeared in prior-year records", ["k-1", "k1", "schedule k"]),
    Rule("rental", "Income", "Rental property: rent received, expenses by category, 1098 for the rental mortgage", lambda c: c.has("rental", "schedule e"),
         lambda c: "Rental activity appears in prior-year records", ["rental", "rent roll", "schedule e"]),
    Rule("1098_mortgage", "Deductions", "1098 mortgage interest statement", lambda c: c.has("mortgage interest", "1098"),
         lambda c: f"Mortgage interest was deducted in {c.prior_year}", ["1098", "mortgage"]),
    Rule("property_tax", "Deductions", "Property tax bills paid in {year}", lambda c: c.has("property tax", "state and local taxes", "real estate tax"),
         lambda c: "State and local taxes were itemized", ["property tax", "real estate tax"]),
    Rule("charitable", "Deductions", "Charitable contribution receipts (letters for gifts of $250 or more)", lambda c: c.has("charitable", "donation", "contribution"),
         lambda c: f"Charitable deductions were claimed in {c.prior_year}", ["donation", "charit", "contribution", "receipt"]),
    Rule("childcare", "Credits", "Child and dependent care provider statement with tax ID and amount paid", lambda c: c.has("dependent", "childcare", "daycare"),
         lambda c: "Dependents were claimed", ["childcare", "daycare", "dependent care", "provider"]),
    Rule("1098_t", "Credits", "1098-T tuition statement and 529 distribution statements (1099-Q)", lambda c: c.has("1098-t", "tuition", "529", "college"),
         lambda c: "Education-related items appear in prior-year records", ["1098-t", "1098t", "tuition", "1099-q", "529"]),
    Rule("hsa", "Deductions", "HSA forms 1099-SA and 5498-SA", lambda c: c.has("hsa", "health savings"),
         lambda c: "HSA activity in prior year", ["1099-sa", "5498-sa", "hsa"]),
    Rule("retirement", "Income", "1099-R for retirement distributions and 5498 for IRA contributions", lambda c: c.has("1099-r", "ira", "401(k)", "pension", "retirement"),
         lambda c: "Retirement account activity in prior year", ["1099-r", "5498", "ira", "pension"]),
    Rule("1095_a", "Credits", "Form 1095-A if health insurance was bought through the marketplace", lambda c: c.has("1095", "marketplace"),
         lambda c: "Marketplace coverage appeared in prior-year records", ["1095"]),
    Rule("student_loan", "Deductions", "1098-E student loan interest", lambda c: c.has("1098-e", "student loan"),
         lambda c: "Student loan interest deducted in prior year", ["1098-e", "1098e", "student loan"]),
    Rule("estimated_payments", "Payments", "Dates and amounts of federal and state estimated tax payments made for {year}", _fact("estimated_payments"),
         lambda c: f"Estimates of {c.money('estimated_payments')} were paid for {c.prior_year}; penalties apply when late", ["estimated", "1040-es", "es payment", "estimate"]),
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
    ctx = Ctx(client=client, tax_year=tax_year, prior_year=prior_year, facts=facts, text=text.replace("_", " ").lower(),
              doc_types={r.get("doc_type") for r in records}, risk_flags=risk_flags, notes=notes)
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
    return result
