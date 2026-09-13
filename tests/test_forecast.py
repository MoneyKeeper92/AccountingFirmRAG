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


def test_individual_screens():
    r = forecast.assess_risk(facts(
        adjusted_gross_income={2024: 150000.0, 2025: 200000.0},
        taxable_income={2025: 160000.0},
        total_tax={2025: 30000.0},
        federal_withholding={2025: 20000.0},
        estimated_payments={2025: 4000.0},
        schedule_c_net_profit={2025: 90000.0},
    ))
    assert r["profile"] == "individual"
    areas = [f["area"] for f in r["flags"]]
    assert "Estimated payments" in areas and "Entity choice" in areas and "Year-over-year" in areas
    assert r["ratios"]["payments_to_total_tax"] == 0.8
    assert r["ratios"]["se_tax_estimate"] == round(90000 * 0.9235 * 0.153, 0)
    assert r["flags"][0]["severity"] == "high"
    assert any("Form 8995" in f["detail"] for f in r["flags"])          # QBI not recorded


def test_s_corp_and_c_corp_screens():
    s = forecast.assess_risk(facts(gross_receipts={2025: 1_000_000.0}, ordinary_business_income={2025: 300000.0},
                                   officer_compensation={2025: 60000.0}, distributions={2025: 250000.0}, aaa_balance={2025: 200000.0}))
    areas = {f["area"] for f in s["flags"]}
    assert "Reasonable compensation" in areas and "Basis" in areas
    assert s["ratios"]["distributions_to_officer_comp"] == 4.1667
    c = forecast.assess_risk(facts(gross_receipts={2025: 5_000_000.0}, corporate_taxable_income={2025: 300000.0},
                                   corporate_total_tax={2025: 63000.0}, estimated_payments={2025: 30000.0}, retained_earnings={2025: 900000.0}))
    areas = {f["area"] for f in c["flags"]}
    assert "Estimated payments" in areas and "Accumulated earnings" in areas


def test_empty_facts():
    assert forecast.assess_risk([])["flags"] == []
    assert forecast.forecast_client([]) == {}
