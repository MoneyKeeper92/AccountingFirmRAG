"""Deterministic forecasting + risk heuristics over extracted facts.

The LLM never invents numbers: it calls these tools, gets back arithmetic it
can cite, and writes the narrative. Keep the maths auditable - an accountant
should be able to reproduce every figure in Excel.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

FORECAST_METRICS = [
    "revenue", "cost_of_goods_sold", "gross_profit", "operating_expenses", "net_income",
    "total_assets", "current_assets", "cash", "accounts_receivable", "inventory",
    "total_liabilities", "current_liabilities", "long_term_debt", "total_equity",
    "wages", "adjusted_gross_income", "taxable_income", "total_tax", "schedule_c_net_profit",
]


def series_by_metric(facts: list[dict]) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for f in facts:
        if f.get("period") is None:
            continue
        # If the same metric/period appears in several documents, keep the last loaded.
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
    """Ratio analysis + trend flags. Thresholds are conventional starting points
    and should be tuned per industry with the engagement partner."""
    series = series_by_metric(facts)
    if not series:
        return {"flags": [], "ratios": {}, "note": "No structured facts available for this client yet."}
    years = sorted({y for s in series.values() for y in s})
    latest = years[-1]
    prev = years[-2] if len(years) > 1 else None

    def g(metric: str, year: int | None = latest) -> float | None:
        return series.get(metric, {}).get(year) if year is not None else None

    ratios: dict[str, Any] = {"year": latest}
    ratios["current_ratio"] = _ratio(g("current_assets"), g("current_liabilities"))
    ratios["debt_to_equity"] = _ratio(g("total_liabilities"), g("total_equity"))
    ratios["gross_margin"] = _ratio(g("gross_profit"), g("revenue"))
    ratios["net_margin"] = _ratio(g("net_income"), g("revenue"))
    ratios["ar_days"] = round(g("accounts_receivable") / g("revenue") * 365, 1) if g("accounts_receivable") and g("revenue") else None
    ratios["inventory_days"] = round(g("inventory") / g("cost_of_goods_sold") * 365, 1) if g("inventory") and g("cost_of_goods_sold") else None
    ratios["cash_to_current_liabilities"] = _ratio(g("cash"), g("current_liabilities"))
    ratios["effective_tax_rate"] = _ratio(g("total_tax"), g("taxable_income"))

    flags: list[dict[str, Any]] = []

    def flag(area: str, severity: str, detail: str, metric: str | None = None):
        flags.append({"area": area, "severity": severity, "detail": detail, "metric": metric})

    cr = ratios["current_ratio"]
    if cr is not None and cr < 1.0:
        flag("Liquidity", "high", f"Current ratio {cr} is below 1.0 - going-concern and covenant questions.", "current_ratio")
    elif cr is not None and cr < 1.2:
        flag("Liquidity", "medium", f"Current ratio {cr} is thin.", "current_ratio")
    de = ratios["debt_to_equity"]
    if de is not None and de > 2.0:
        flag("Leverage", "high", f"Debt-to-equity {de} - review debt covenants and interest coverage.", "debt_to_equity")
    if ratios["ar_days"] and ratios["ar_days"] > 75:
        flag("Receivables", "high", f"AR days {ratios['ar_days']} - test collectability / allowance for doubtful accounts.", "accounts_receivable")
    elif ratios["ar_days"] and ratios["ar_days"] > 50:
        flag("Receivables", "medium", f"AR days {ratios['ar_days']} - confirm aging and subsequent receipts.", "accounts_receivable")
    if ratios["inventory_days"] and ratios["inventory_days"] > 120:
        flag("Inventory", "high", f"Inventory days {ratios['inventory_days']} - obsolescence / NRV testing.", "inventory")
    nm = ratios["net_margin"]
    if nm is not None and nm < 0:
        flag("Profitability", "high", f"Net loss in {latest} (net margin {nm}).", "net_income")

    if prev is not None:
        for metric, label, up_is_bad, threshold in [
            ("revenue", "Revenue", False, 0.25),
            ("accounts_receivable", "Accounts receivable", True, 0.30),
            ("inventory", "Inventory", True, 0.30),
            ("operating_expenses", "Operating expenses", True, 0.25),
            ("gross_profit", "Gross profit", False, 0.20),
            ("total_tax", "Total tax", True, 0.30),
            ("adjusted_gross_income", "Adjusted gross income", False, 0.25),
        ]:
            a, b = g(metric, prev), g(metric, latest)
            if a and b is not None:
                change = (b - a) / abs(a)
                if abs(change) >= threshold:
                    direction = "up" if change > 0 else "down"
                    sev = "high" if (change > 0) == up_is_bad or abs(change) > 0.5 else "medium"
                    flag("Analytical review", sev, f"{label} {direction} {abs(change):.0%} from {prev} to {latest} - obtain and corroborate explanation.", metric)
        rev_a, rev_b = g("revenue", prev), g("revenue", latest)
        ar_a, ar_b = g("accounts_receivable", prev), g("accounts_receivable", latest)
        if rev_a and rev_b and ar_a and ar_b and (ar_b - ar_a) / ar_a > (rev_b - rev_a) / rev_a + 0.15:
            flag("Revenue recognition", "high", "Receivables growing materially faster than revenue - cut-off and fictitious-sales risk.", "accounts_receivable")

    order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: order[f["severity"]])
    return {"years_available": years, "ratios": ratios, "flags": flags,
            "note": "Heuristic screening only. Thresholds are generic; tune per industry and materiality."}
