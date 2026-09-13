"""Deterministic projections and tax-planning screens over extracted facts.

The LLM never invents numbers: it calls these tools, gets arithmetic it can cite, and writes
the narrative. Keep the maths auditable; a preparer should be able to redo every figure in Excel.
Thresholds are conventional starting points and should be tuned with the firm.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

FORECAST_METRICS = [
    # 1040
    "wages", "taxable_interest", "ordinary_dividends", "capital_gain_loss", "schedule_c_net_profit", "schedule_e_net_income",
    "adjusted_gross_income", "taxable_income", "total_tax", "federal_withholding", "estimated_payments", "self_employment_tax",
    # entities
    "gross_receipts", "cost_of_goods_sold", "gross_profit", "officer_compensation", "salaries_and_wages", "guaranteed_payments",
    "ordinary_business_income", "distributions", "total_assets", "retained_earnings", "aaa_balance",
    "corporate_taxable_income", "corporate_total_tax",
    # books
    "revenue", "net_income",
]

SE_TAX_RATE = 0.153
SE_NET_FACTOR = 0.9235
ACCUMULATED_EARNINGS_THRESHOLD = 250_000
S_CORP_CANDIDATE_PROFIT = 50_000


def series_by_metric(facts: list[dict]) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for f in facts:
        if f.get("period") is None:
            continue
        out[f["name"]][int(f["period"])] = float(f["value"])
    return out


def project(series: dict[int, float], periods_ahead: int = 1) -> dict[str, Any]:
    """Linear least-squares trend + CAGR; returns both so the reader can pick."""
    if not series:
        return {"error": "no data"}
    years = sorted(series)
    values = [series[y] for y in years]
    last_year, last_val = years[-1], values[-1]
    target_year = last_year + periods_ahead
    result: dict[str, Any] = {"history": {str(y): series[y] for y in years}, "target_year": target_year}
    if len(years) == 1:
        result["linear"] = last_val
        result["cagr"] = last_val
        result["method_note"] = "Only one period available; projection = last actual (flat)."
        return result
    n = len(years)
    mx = sum(years) / n
    my = sum(values) / n
    sxx = sum((y - mx) ** 2 for y in years) or 1.0
    slope = sum((y - mx) * (v - my) for y, v in zip(years, values)) / sxx
    intercept = my - slope * mx
    result["linear"] = round(intercept + slope * target_year, 2)
    result["linear_slope_per_year"] = round(slope, 2)
    first_val = values[0]
    span = years[-1] - years[0]
    if first_val > 0 and last_val > 0 and span > 0:
        cagr = (last_val / first_val) ** (1 / span) - 1
        result["cagr_rate"] = round(cagr, 4)
        result["cagr"] = round(last_val * (1 + cagr) ** periods_ahead, 2)
    else:
        result["cagr"] = None
        result["cagr_rate"] = None
    yoy = [(years[i], (values[i] - values[i - 1]) / abs(values[i - 1]) if values[i - 1] else None) for i in range(1, n)]
    result["yoy_change"] = {str(y): (round(c, 4) if c is not None else None) for y, c in yoy}
    return result


def forecast_client(facts: list[dict], periods_ahead: int = 1, metrics: list[str] | None = None) -> dict[str, Any]:
    series = series_by_metric(facts)
    wanted = metrics or [m for m in FORECAST_METRICS if m in series]
    return {m: project(series[m], periods_ahead) for m in wanted if m in series}


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b in (None, 0):
        return None
    return round(a / b, 4)


def assess_risk(facts: list[dict]) -> dict[str, Any]:
    """Tax-planning screens. Returns key figures and ranked flags for the latest year on file."""
    series = series_by_metric(facts)
    if not series:
        return {"flags": [], "ratios": {}, "profile": "unknown", "note": "No structured facts available for this client yet."}
    years = sorted({y for s in series.values() for y in s})
    latest = years[-1]
    prev = years[-2] if len(years) > 1 else None

    def g(metric: str, year: int | None = latest) -> float | None:
        return series.get(metric, {}).get(year) if year is not None else None

    individual = any(g(m) is not None for m in ("adjusted_gross_income", "wages", "taxable_income")) and g("gross_receipts") is None
    entity = any(g(m) is not None for m in ("gross_receipts", "ordinary_business_income", "officer_compensation", "guaranteed_payments", "corporate_taxable_income"))
    profile = "individual" if individual and not entity else "entity" if entity and not individual else "mixed" if (individual and entity) else "books"

    flags: list[dict[str, Any]] = []

    def flag(area: str, severity: str, detail: str, metric: str | None = None):
        flags.append({"area": area, "severity": severity, "detail": detail, "metric": metric})

    def pct(a: float, b: float) -> str:
        return f"{(a - b) / abs(b):+.0%}" if b else "n/a"

    ratios: dict[str, Any] = {"year": latest}

    # ------------------------------------------------------------- individual (1040)
    if profile in ("individual", "mixed"):
        total_tax, taxable = g("total_tax"), g("taxable_income")
        ratios["effective_tax_rate"] = _ratio(total_tax, taxable)
        payments = (g("federal_withholding") or 0) + (g("estimated_payments") or 0)
        ratios["payments_to_total_tax"] = _ratio(payments, total_tax)
        if total_tax and payments and payments / total_tax < 0.9:
            flag("Estimated payments", "high", f"Withholding plus estimates covered {payments / total_tax:.0%} of {latest} total tax; safe harbour is 90% of this year's tax or 100%/110% of last year's. Set {latest + 1} estimates now.", "estimated_payments")
        if (g("underpayment_penalty") or 0) > 0:
            flag("Estimated payments", "high", f"Underpayment penalty of ${g('underpayment_penalty'):,.0f} in {latest}. Calendar the quarterly dates and confirm amounts.", "underpayment_penalty")
        refund = g("refund")
        if refund and total_tax and refund > 2_000 and refund / total_tax > 0.15:
            flag("Withholding", "medium", f"Refund of ${refund:,.0f} was {refund / total_tax:.0%} of total tax; adjust W-4 or estimates rather than lend to the Treasury.", "refund")
        sc = g("schedule_c_net_profit")
        if sc and sc > S_CORP_CANDIDATE_PROFIT:
            se_tax = sc * SE_NET_FACTOR * SE_TAX_RATE
            ratios["se_tax_estimate"] = round(se_tax, 0)
            flag("Entity choice", "high", f"Schedule C net profit ${sc:,.0f}; self-employment tax roughly ${se_tax:,.0f}. Model an S-corp election (reasonable salary + payroll cost vs SE tax saved).", "schedule_c_net_profit")
        if sc and sc > 0 and not g("estimated_payments"):
            flag("Estimated payments", "medium", "Self-employment income with no estimated payments on file; confirm estimates or increase W-2 withholding.", "estimated_payments")
        if sc and sc > 0 and g("qbi_deduction") is None:
            flag("Deductions", "medium", "Schedule C income but no qualified business income deduction recorded; confirm Form 8995 / 8995-A was applied.", "qbi_deduction")
        item, std = g("itemized_deductions_total"), g("standard_or_itemized_deduction")
        if item and std and abs(item - std) / std < 0.15:
            flag("Deductions", "medium", f"Itemized deductions (${item:,.0f}) are within 15% of the deduction taken (${std:,.0f}); consider bunching charitable gifts or property tax into alternate years.", "itemized_deductions_total")
        cg = g("capital_gain_loss")
        if cg and cg > 10_000:
            flag("Investments", "low", f"Capital gains of ${cg:,.0f} in {latest}; ask about {latest + 1} sales early so estimates and loss harvesting can be planned.", "capital_gain_loss")
        if (g("ordinary_dividends") or 0) + (g("taxable_interest") or 0) > 20_000:
            flag("Investments", "low", "Material investment income; check net investment income tax (Form 8960) exposure and municipal alternatives.", "ordinary_dividends")
        if prev is not None:
            for metric, label, threshold in [("adjusted_gross_income", "Adjusted gross income", 0.20), ("wages", "Wages", 0.25),
                                             ("total_tax", "Total tax", 0.30), ("schedule_c_net_profit", "Schedule C profit", 0.30)]:
                a, b = g(metric, prev), g(metric, latest)
                if a and b is not None and abs((b - a) / abs(a)) >= threshold:
                    flag("Year-over-year", "medium", f"{label} {pct(b, a)} from {prev} to {latest} (${a:,.0f} to ${b:,.0f}); revisit estimates and phase-outs (child tax credit, QBI limits, IRMAA).", metric)

    # ------------------------------------------------------------- entities (1065 / 1120-S / 1120)
    if profile in ("entity", "mixed"):
        gr, cogs = g("gross_receipts") or g("revenue"), g("cost_of_goods_sold")
        obi = g("ordinary_business_income")
        officer, dist, aaa = g("officer_compensation"), g("distributions"), g("aaa_balance")
        ratios["gross_margin"] = _ratio((gr - cogs) if (gr is not None and cogs is not None) else g("gross_profit"), gr)
        ratios["ordinary_income_margin"] = _ratio(obi, gr)
        ratios["distributions_to_officer_comp"] = _ratio(dist, officer)
        is_s_corp = aaa is not None or g("loans_from_shareholders") is not None or (officer is not None and g("partners_capital") is None and g("corporate_taxable_income") is None)
        is_partnership = g("guaranteed_payments") is not None or g("partners_capital") is not None
        is_c_corp = g("corporate_taxable_income") is not None or g("corporate_total_tax") is not None

        if is_s_corp:
            if (officer or 0) == 0 and (obi or 0) > 50_000:
                flag("Reasonable compensation", "high", f"No officer compensation with ordinary business income of ${obi:,.0f}; the IRS expects a reasonable salary before distributions.", "officer_compensation")
            elif officer and dist and dist / officer > 2:
                flag("Reasonable compensation", "high", f"Distributions (${dist:,.0f}) are {dist / officer:.1f}x officer compensation (${officer:,.0f}); document the salary study.", "distributions")
            if aaa is not None and dist and dist > aaa:
                flag("Basis", "high", f"Distributions (${dist:,.0f}) exceed the AAA balance (${aaa:,.0f}); check shareholder basis (Form 7203) for taxable distributions.", "aaa_balance")
            if (g("loans_from_shareholders") or 0) > 0:
                flag("Basis", "medium", f"Shareholder loans of ${g('loans_from_shareholders'):,.0f}: confirm written terms, interest, and debt-basis treatment.", "loans_from_shareholders")
            if officer and g("shareholder_health_insurance") is None:
                flag("Payroll", "low", "Confirm >2% shareholder health insurance is on the W-2 and deducted on the 1040.", "shareholder_health_insurance")
        if is_partnership:
            pc = g("partners_capital")
            if pc is not None and pc < 0:
                flag("Basis", "high", f"Partners' capital is negative (${pc:,.0f}); check outside basis, at-risk limits, and gain on distributions.", "partners_capital")
            gp = g("guaranteed_payments")
            if gp and obi is not None and gp > obi:
                flag("Partner compensation", "medium", f"Guaranteed payments (${gp:,.0f}) exceed ordinary income (${obi:,.0f}); revisit the allocation and partners' estimates.", "guaranteed_payments")
        if is_c_corp:
            re_ = g("retained_earnings")
            if re_ and re_ > ACCUMULATED_EARNINGS_THRESHOLD:
                flag("Accumulated earnings", "medium", f"Retained earnings ${re_:,.0f} exceed the ${ACCUMULATED_EARNINGS_THRESHOLD:,.0f} accumulated-earnings-tax threshold; document business needs or plan dividends.", "retained_earnings")
            ctax, est = g("corporate_total_tax"), g("estimated_payments")
            if ctax and ctax > 500 and (est or 0) < 0.9 * ctax:
                flag("Estimated payments", "high", f"Corporate estimates (${est or 0:,.0f}) below 90% of total tax (${ctax:,.0f}); schedule Form 1120-W instalments.", "estimated_payments")
            if (g("net_operating_loss") or 0) > 0:
                flag("Carryforwards", "low", f"NOL carryforward of ${g('net_operating_loss'):,.0f} available (80% limitation applies).", "net_operating_loss")
        if obi and obi > 100_000 and (g("retirement_plan_contributions") or 0) == 0:
            flag("Deductions", "low", "No retirement plan contributions with six-figure ordinary income; a SEP or 401(k) would reduce owner tax.", "retirement_plan_contributions")
        fa_prev, fa_now = g("fixed_assets_net", prev) if prev else None, g("fixed_assets_net")
        if fa_prev is not None and fa_now is not None and fa_now > fa_prev * 1.15:
            flag("Depreciation", "low", "Fixed assets grew materially; plan Section 179 / bonus depreciation on additions before year end.", "fixed_assets_net")
        if prev is not None and gr:
            gr_prev = g("gross_receipts", prev) or g("revenue", prev)
            if gr_prev and abs((gr - gr_prev) / abs(gr_prev)) >= 0.25:
                flag("Year-over-year", "medium", f"Gross receipts {pct(gr, gr_prev)} from {prev} to {latest}; revisit owner estimates and entity-level state taxes.", "gross_receipts")
            gm_prev = _ratio((gr_prev - (g('cost_of_goods_sold', prev) or 0)) if g('cost_of_goods_sold', prev) is not None else None, gr_prev)
            if gm_prev is not None and ratios["gross_margin"] is not None and abs(ratios["gross_margin"] - gm_prev) >= 0.05:
                flag("Year-over-year", "medium", f"Gross margin moved from {gm_prev:.1%} to {ratios['gross_margin']:.1%}; confirm inventory / COGS cut-off before filing.", "gross_profit")

    order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: order[f["severity"]])
    return {"years_available": years, "profile": profile, "ratios": {k: v for k, v in ratios.items() if v is not None}, "flags": flags,
            "note": "Heuristic screening only. Thresholds are generic; tune per client and confirm against the return."}
