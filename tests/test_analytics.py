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
