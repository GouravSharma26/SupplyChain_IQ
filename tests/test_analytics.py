"""
Unit tests for supply chain analytics and KPI calculations.
"""

import pandas as pd
import pytest

from supplychain_iq.analytics import (
    calculate_kpis,
    filter_dataset,
    get_daily_demand_trend,
    get_product_demand_summary,
    calculate_supplier_scorecard,
    calculate_product_mix_abc,
    generate_executive_insights,
)


@pytest.fixture
def sample_analytics_df():
    # 2 products across 3 daily dates
    return pd.DataFrame({
        "date": pd.to_datetime(["2026-05-01", "2026-05-01", "2026-05-02", "2026-05-02", "2026-05-03", "2026-05-03"]),
        "product_id": ["P1", "P2", "P1", "P2", "P1", "P2"],
        "product_name": ["Widget 1", "Widget 2", "Widget 1", "Widget 2", "Widget 1", "Widget 2"],
        "category": ["CatA", "CatB", "CatA", "CatB", "CatA", "CatB"],
        "units_sold": [10, 20, 15, 25, 20, 30],  # Total: 120 units
        "inventory_on_hand": [100, 200, 90, 180, 80, 160],  # Latest: P1=80, P2=160
        "unit_cost": [10.0, 20.0, 10.0, 20.0, 10.0, 20.0],
        "lead_time_days": [5, 10, 5, 10, 5, 10],
        "delivery_delay_days": [0, 1, 0, 0, -1, 2],
    })


def test_kpi_units_and_inventory_valuation(sample_analytics_df):
    kpis = calculate_kpis(sample_analytics_df)
    
    # Total units sold = 10+20+15+25+20+30 = 120
    assert kpis.total_units_sold == 120
    
    # Calendar days span: May 1 to May 3 = 3 days
    assert kpis.calendar_days == 3
    assert kpis.avg_daily_demand == 40.0  # 120 / 3
    
    # Latest inventory units: P1 (80) + P2 (160) = 240 units
    assert kpis.total_inventory_units == 240
    
    # Latest inventory valuation: 80 * 10 + 160 * 20 = 800 + 3200 = 4000.0
    assert kpis.total_inventory_value == 4000.0
    
    # Active products
    assert kpis.active_products_count == 2
    
    # Supplier on-time rate: delays [0, 1, 0, 0, -1, 2]. <= 0 are: 0, 0, 0, -1 (4 out of 6 = 66.7%)
    assert kpis.supplier_sample_size == 6
    assert kpis.supplier_on_time_rate == 66.7


def test_filter_dataset(sample_analytics_df):
    # Filter for P1 only
    filtered = filter_dataset(sample_analytics_df, product_ids=["P1"])
    assert len(filtered) == 3
    assert set(filtered["product_id"]) == {"P1"}

    # Filter by date range
    filtered_dates = filter_dataset(
        sample_analytics_df,
        start_date=pd.Timestamp("2026-05-02"),
        end_date=pd.Timestamp("2026-05-03")
    )
    assert len(filtered_dates) == 4
    assert filtered_dates["date"].min() == pd.Timestamp("2026-05-02")


def test_daily_demand_trend(sample_analytics_df):
    trend = get_daily_demand_trend(sample_analytics_df)
    assert len(trend) == 3
    # Day 1: 30, Day 2: 40, Day 3: 50
    assert trend["units_sold"].tolist() == [30, 40, 50]


def test_supplier_scorecard_and_risk_tiers(sample_analytics_df):
    df_with_sup = sample_analytics_df.copy()
    df_with_sup["supplier_id"] = ["SUP-A", "SUP-B"] * 3
    df_with_sup["supplier_name"] = ["Supplier Alpha", "Supplier Beta"] * 3

    scorecard = calculate_supplier_scorecard(df_with_sup)
    assert len(scorecard) == 2
    assert "on_time_rate_pct" in scorecard.columns
    assert "risk_tier" in scorecard.columns

    sup_a = scorecard[scorecard["supplier_id"] == "SUP-A"].iloc[0]
    # SUP-A has delays: 0, 0, -1 -> all <= 0 -> 100% on-time -> Low risk
    assert sup_a["on_time_rate_pct"] == 100.0
    assert sup_a["risk_tier"] == "Low"


def test_product_mix_abc_pareto(sample_analytics_df):
    abc_df = calculate_product_mix_abc(sample_analytics_df)
    assert len(abc_df) == 2
    assert "abc_classification" in abc_df.columns
    assert "cum_value_share_pct" in abc_df.columns

    # Latest inventory values: P2 is 160*20 = 3200 (80%), P1 is 80*10 = 800 (20%)
    # P2 is top value item -> Class A or B
    assert abc_df.iloc[0]["product_id"] == "P2"
    assert abc_df.iloc[0]["inventory_value"] == 3200.0


def test_generate_executive_insights(sample_analytics_df):
    insights = generate_executive_insights(sample_analytics_df)
    assert len(insights) >= 2
    for ins in insights:
        assert "domain" in ins
        assert "metric" in ins
        assert "time_range" in ins
        assert "benchmark" in ins
        assert "caveat" in ins
        assert "recommendation" in ins

