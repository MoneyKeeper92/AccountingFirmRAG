from app import forecast


def facts(**series):
    out = []
    for name, by_year in series.items():
        for year, value in by_year.items():
            out.append({"name": name, "value": value, "period": year})
    return out


def test_linear_and_cagr_projection():
    p = forecast.project({2023: 100.0, 2024: 110.0, 2025: 121.0}, periods_ahead=1)
    assert p["target_year"] == 2026
    assert abs(p["linear"] - 131.33) < 0.01
    assert abs(p["cagr"] - 133.1) < 0.01
    assert p["yoy_change"]["2025"] == 0.1


def test_single_period_is_flat():
    p = forecast.project({2025: 50.0})
    assert p["linear"] == 50.0 and "Only one period" in p["method_note"]


def test_risk_flags_liquidity_and_receivables():
    r = forecast.assess_risk(facts(
        revenue={2024: 1000.0, 2025: 1100.0},
        accounts_receivable={2024: 100.0, 2025: 300.0},
        current_assets={2025: 500.0},
        current_liabilities={2025: 600.0},
        total_liabilities={2025: 900.0},
        total_equity={2025: 300.0},
    ))
    areas = {f["area"] for f in r["flags"]}
    assert "Liquidity" in areas
    assert "Revenue recognition" in areas
    assert r["ratios"]["current_ratio"] == 0.8333
    assert r["flags"][0]["severity"] == "high"


def test_empty_facts():
    assert forecast.assess_risk([])["flags"] == []
    assert forecast.forecast_client([]) == {}
