"""Financial statements from what the archive already knows.

Builds an income statement and a balance sheet for an entity client and year from two sources,
in order of preference: rows of a trial balance / general ledger export (classified by account
name), then the facts extracted from the return or books. Designed for a preparer who wants a
clean two-page set to work from or to hand to the client; every line says where it came from.
"""
from __future__ import annotations

import io
import re
from typing import Any

from . import forecast

# account-name classification for trial balances: (regex, statement, section, sign)  sign: +1 debit-normal, -1 credit-normal
TB_RULES: list[tuple[str, str, str]] = [
    (r"cash|checking|savings|petty|money\s+market", "bs", "Cash"),
    (r"accounts?\s+receivable|a/r\b|trade\s+receivable", "bs", "Accounts receivable"),
    (r"allowance\s+for\s+doubtful|bad\s+debt\s+allowance", "bs", "Accounts receivable"),
    (r"inventor", "bs", "Inventory"),

    (r"equipment|vehicle|furniture|building|land|leasehold|fixed\s+asset|machinery|computer", "bs", "Property and equipment"),
    (r"accumulated\s+(?:depreciation|amortization)", "bs", "Property and equipment"),
    (r"accounts?\s+payable|a/p\b", "bs", "Accounts payable"),
    (r"accrued|payroll\s+(?:liabilit|tax\s+payable)|wages\s+payable|sales\s+tax\s+payable|customer\s+deposit|deposits?\s+(?:payable|received)|deferred\s+revenue|unearned", "bs", "Accrued and other current liabilities"),
    (r"prepaid|security\s+deposit|other\s+current\s+asset|undeposited", "bs", "Other current assets"),
    (r"line\s+of\s+credit|credit\s+card|short[-\s]term", "bs", "Line of credit and cards"),
    (r"loan|note(?:s)?\s+payable|mortgage|long[-\s]term\s+debt|financing", "bs", "Loans payable"),
    (r"shareholder\s+loan|loans?\s+from\s+(?:shareholder|officer|partner|member)|due\s+to\s+(?:shareholder|officer|partner)", "bs", "Loans from owners"),
    (r"common\s+stock|capital\s+stock|paid[-\s]in|members?'?\s+capital|partners?'?\s+capital|owner'?s?\s+capital|contributed", "bs", "Owner capital"),
    (r"retained\s+earnings|accumulated\s+adjust|aaa\b", "bs", "Retained earnings"),
    (r"distribution|dividend(?:s)?\s+paid|draw|withdrawal", "bs", "Distributions"),
    (r"sales|revenue|fees?\s+earned|service\s+income|gross\s+receipts|income(?!\s+tax)", "is", "Revenue"),
    (r"returns?\s+and\s+allowances|discounts?\s+given", "is", "Revenue"),
    (r"cost\s+of\s+(?:goods|sales)|cogs|purchases|direct\s+(?:labor|materials)|freight[-\s]in|subcontract", "is", "Cost of goods sold"),
    (r"officer|owner'?s?\s+(?:salary|compensation)|guaranteed\s+payment", "is", "Officer and owner compensation"),
    (r"wage|salar|payroll(?!\s+tax)", "is", "Wages"),
    (r"payroll\s+tax|fica|futa|suta|employer\s+tax", "is", "Payroll taxes"),
    (r"rent|lease", "is", "Rent"),
    (r"interest\s+expense|interest\s+paid|finance\s+charge", "is", "Interest"),
    (r"depreciation|amortization", "is", "Depreciation"),
    (r"tax(?:es)?\s+and\s+licen|property\s+tax|license|franchise\s+tax|state\s+tax", "is", "Taxes and licenses"),
    (r"insurance|health\s+insurance", "is", "Insurance"),
    (r"utilit|telephone|internet|phone", "is", "Utilities"),
    (r"advertis|marketing", "is", "Advertising"),
    (r"repair|maintenance", "is", "Repairs and maintenance"),
    (r"professional|legal|accounting|consult", "is", "Professional fees"),
    (r"travel|meals|auto|vehicle\s+expense|mileage|fuel", "is", "Travel, meals and auto"),
    (r"supplies|office", "is", "Office and supplies"),
    (r"bank\s+(?:fee|charge)|merchant\s+fee|service\s+charge", "is", "Bank and merchant fees"),
    (r"expense|dues|subscription|training|charit|donation|miscellaneous|other", "is", "Other expenses"),
]
IS_ORDER = ["Revenue", "Cost of goods sold", "Officer and owner compensation", "Wages", "Payroll taxes", "Rent", "Interest", "Depreciation",
            "Taxes and licenses", "Insurance", "Utilities", "Advertising", "Repairs and maintenance", "Professional fees",
            "Travel, meals and auto", "Office and supplies", "Bank and merchant fees", "Other expenses"]
BS_ASSETS = ["Cash", "Accounts receivable", "Inventory", "Other current assets", "Property and equipment"]
BS_LIABS = ["Accounts payable", "Accrued and other current liabilities", "Line of credit and cards", "Loans payable", "Loans from owners"]
BS_EQUITY = ["Owner capital", "Retained earnings", "Distributions", "Current year net income"]


def _classify(account: str) -> tuple[str, str] | None:
    a = account.lower()
    for pat, stmt, section in TB_RULES:
        if re.search(pat, a):
            return stmt, section
    return None


def parse_trial_balance(text: str) -> list[dict[str, Any]]:
    """Rows like 'Cash | 148000 |' or 'Sales |  | 5610000' (from the CSV parser) or 'Cash,148000,' raw."""
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        parts = [p.strip() for p in re.split(r"\s*[|,]\s*", line)]
        if len(parts) < 2 or not parts[0] or parts[0].lower() in ("account", "account name", "description"):
            continue
        nums = []
        for p in parts[1:]:
            p2 = p.replace("$", "").replace(",", "").strip()
            neg = p2.startswith("(") and p2.endswith(")")
            p2 = p2.strip("()")
            try:
                nums.append(-float(p2) if neg else float(p2) if p2 else None)
            except ValueError:
                nums.append(None)
        if not any(n is not None for n in nums):
            continue
        debit = nums[0] if len(nums) >= 1 and nums[0] is not None else 0.0
        credit = nums[1] if len(nums) >= 2 and nums[1] is not None else 0.0
        if len(nums) == 1:              # single balance column: positive = debit
            debit, credit = (nums[0], 0.0) if nums[0] >= 0 else (0.0, -nums[0])
        rows.append({"account": parts[0], "debit": debit, "credit": credit})
    return rows


def statements_from_trial_balance(rows: list[dict[str, Any]], year: int | None) -> dict[str, Any]:
    is_lines: dict[str, float] = {}
    bs_lines: dict[str, float] = {}
    unclassified = []
    for r in rows:
        c = _classify(r["account"])
        net_debit = r["debit"] - r["credit"]
        if not c:
            unclassified.append(r["account"])
            continue
        stmt, section = c
        if stmt == "is":
            # revenue is credit-normal: show as positive revenue; expenses debit-normal: positive expense
            is_lines[section] = is_lines.get(section, 0.0) + (-net_debit if section == "Revenue" else net_debit)
        else:
            sign = 1 if section in BS_ASSETS or section == "Distributions" else -1
            bs_lines[section] = bs_lines.get(section, 0.0) + sign * net_debit
    revenue = is_lines.get("Revenue", 0.0)
    cogs = is_lines.get("Cost of goods sold", 0.0)
    expenses = {k: v for k, v in is_lines.items() if k not in ("Revenue", "Cost of goods sold")}
    net_income = revenue - cogs - sum(expenses.values())
    bs_lines["Current year net income"] = net_income
    assets = {k: bs_lines[k] for k in BS_ASSETS if k in bs_lines}
    liabs = {k: bs_lines[k] for k in BS_LIABS if k in bs_lines}
    equity = {k: (-bs_lines[k] if k == "Distributions" else bs_lines[k]) for k in BS_EQUITY if k in bs_lines}
    return _package(year, "trial balance", revenue, cogs, expenses, net_income, assets, liabs, equity, unclassified)


def statements_from_facts(facts: list[dict], year: int | None) -> dict[str, Any] | None:
    series = forecast.series_by_metric(facts)
    years = sorted({y for s in series.values() for y in s})
    if not years:
        return None
    year = year or years[-1]
    g = lambda m: series.get(m, {}).get(year)  # noqa: E731
    revenue = g("gross_receipts") if g("gross_receipts") is not None else g("revenue")
    if revenue is None and g("ordinary_business_income") is None and g("net_income") is None:
        return None
    revenue = (revenue or 0.0) - (g("returns_and_allowances") or 0.0)
    cogs = g("cost_of_goods_sold") or 0.0
    expenses: dict[str, float] = {}
    for name, label in [("officer_compensation", "Officer and owner compensation"), ("guaranteed_payments", "Officer and owner compensation"),
                        ("salaries_and_wages", "Wages"), ("rent_expense", "Rent"), ("interest_expense", "Interest"), ("depreciation", "Depreciation"),
                        ("taxes_and_licenses", "Taxes and licenses"), ("shareholder_health_insurance", "Insurance"),
                        ("retirement_plan_contributions", "Retirement plan")]:
        v = g(name)
        if v:
            expenses[label] = expenses.get(label, 0.0) + v
    total_ded = g("total_deductions")
    listed = sum(expenses.values())
    if total_ded and total_ded > listed:
        expenses["Other expenses"] = total_ded - listed
    elif g("operating_expenses") and g("operating_expenses") > listed:
        expenses["Other expenses"] = g("operating_expenses") - listed
    obi = g("ordinary_business_income")
    net_income = obi if obi is not None else (g("net_income") if g("net_income") is not None else revenue - cogs - sum(expenses.values()))
    assets = {k: v for k, v in [("Cash", g("cash")), ("Accounts receivable", g("accounts_receivable")), ("Inventory", g("inventory")),
                                 ("Property and equipment", g("fixed_assets_net"))] if v is not None}
    total_assets = g("total_assets")
    if total_assets is not None and total_assets > sum(assets.values()):
        assets["Other assets"] = total_assets - sum(assets.values())
    liabs = {k: v for k, v in [("Loans from owners", g("loans_from_shareholders")), ("Loans payable", g("long_term_debt")),
                                ("Accrued and other current liabilities", g("current_liabilities"))] if v}
    total_liab = g("total_liabilities")
    if total_liab is not None and total_liab > sum(liabs.values()):
        liabs["Other liabilities"] = total_liab - sum(liabs.values())
    equity = {k: v for k, v in [("Retained earnings", g("retained_earnings")), ("Partners' capital", g("partners_capital")),
                                 ("AAA balance (S corp)", g("aaa_balance")), ("Distributions", -(g("distributions") or 0) or None)] if v is not None}
    if total_assets is not None and total_liab is not None and not equity:
        equity["Total equity"] = total_assets - total_liab
    return _package(year, "tax return and books", revenue, cogs, expenses, net_income, assets, liabs, equity, [])


def _package(year, source, revenue, cogs, expenses, net_income, assets, liabs, equity, unclassified) -> dict[str, Any]:
    gross_profit = revenue - cogs
    total_exp = sum(expenses.values())
    ordered_exp = [(k, expenses[k]) for k in IS_ORDER if k in expenses] + [(k, v) for k, v in expenses.items() if k not in IS_ORDER]
    total_assets = sum(assets.values())
    total_liabs = sum(liabs.values())
    total_equity = sum(v for v in equity.values())
    return {
        "year": year, "source": source,
        "income_statement": {"Revenue": round(revenue, 2), "Cost of goods sold": round(cogs, 2), "Gross profit": round(gross_profit, 2),
                              "expenses": [(k, round(v, 2)) for k, v in ordered_exp], "Total expenses": round(total_exp, 2),
                              "Net income": round(net_income, 2),
                              "gross_margin": round(gross_profit / revenue, 4) if revenue else None, "net_margin": round(net_income / revenue, 4) if revenue else None},
        "balance_sheet": {"assets": [(k, round(v, 2)) for k, v in assets.items()], "Total assets": round(total_assets, 2),
                           "liabilities": [(k, round(v, 2)) for k, v in liabs.items()], "Total liabilities": round(total_liabs, 2),
                           "equity": [(k, round(v, 2)) for k, v in equity.items()], "Total equity": round(total_equity, 2),
                           "balances": abs(total_assets - total_liabs - total_equity) < 1.0 if assets else None},
        "unclassified_accounts": unclassified,
        "note": "Prepared from the archive for review; not a compilation or audited statement.",
    }


def build_statements(store, client_id: str, year: int | None = None) -> dict[str, Any] | None:
    """Trial balance for the year if one is on file, otherwise the return's figures."""
    docs = [d for d in store.list_documents(client_id) if d["status"] == "ready"]
    tb_docs = [d for d in docs if d.get("doc_type") in ("trial_balance", "general_ledger") and (year is None or d.get("tax_year") == year)]
    if tb_docs:
        tb = sorted(tb_docs, key=lambda d: (d.get("tax_year") or 0, d["created_at"]))[-1]
        text = store.document_text(tb["id"])
        rows = parse_trial_balance(text)
        if len(rows) >= 4:
            out = statements_from_trial_balance(rows, tb.get("tax_year") or year)
            out["source_document_id"] = tb["id"]
            out["source_filename"] = tb["filename"]
            return out
    return statements_from_facts(store.facts_for_client(client_id), year)


def to_xlsx(st: dict[str, Any], client_name: str) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Income statement"
    bold = Font(bold=True)
    ws.append([client_name]); ws["A1"].font = bold
    ws.append([f"Income statement, year {st['year']} (from {st['source']})"]); ws.append([])
    inc = st["income_statement"]
    for k in ("Revenue", "Cost of goods sold", "Gross profit"):
        ws.append([k, inc[k]])
    ws.append([]); ws.append(["Expenses"]); ws[f"A{ws.max_row}"].font = bold
    for k, v in inc["expenses"]:
        ws.append([f"  {k}", v])
    ws.append(["Total expenses", inc["Total expenses"]]); ws.append(["Net income", inc["Net income"]]); ws[f"A{ws.max_row}"].font = bold
    ws2 = wb.create_sheet("Balance sheet")
    ws2.append([client_name]); ws2["A1"].font = bold
    ws2.append([f"Balance sheet, end of {st['year']} (from {st['source']})"]); ws2.append([])
    bs = st["balance_sheet"]
    for title, rows, total in (("Assets", bs["assets"], bs["Total assets"]), ("Liabilities", bs["liabilities"], bs["Total liabilities"]), ("Equity", bs["equity"], bs["Total equity"])):
        ws2.append([title]); ws2[f"A{ws2.max_row}"].font = bold
        for k, v in rows:
            ws2.append([f"  {k}", v])
        ws2.append([f"Total {title.lower()}", total]); ws2.append([])
    for w in (ws, ws2):
        w.column_dimensions["A"].width = 38; w.column_dimensions["B"].width = 16
        for row in w.iter_rows(min_col=2, max_col=2):
            for c in row:
                c.number_format = "#,##0;(#,##0)"
    ws.append([]); ws.append([st["note"]])
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()
