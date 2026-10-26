"""
Unit tests for inventory optimization, reorder points, and scenario simulation.
"""

import pandas as pd
import pytest

from supplychain_iq.inventory import calculate_inventory_plans


@pytest.fixture
def inventory_sample_df():
    # 30 days of data for a single product with known parameters
    dates = pd.date_range("2026-05-01", periods=30, freq="D")
    return pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-100"] * 30,
        "product_name": ["Precision Servo"] * 30,
        "units_sold": [10] * 30,  # Exactly 10 units/day -> std = 0
        "inventory_on_hand": [50] * 30,  # Current stock = 50
        "unit_cost": [25.0] * 30,
        "lead_time_days": [7] * 30,
    })


def test_reorder_point_and_replenishment(inventory_sample_df):
    # avg_daily_demand = 300 / 30 = 10.0
    # lead_time = 7 days
    # lead_time_demand = 70.0
    # review_period = 7 days -> cycle stock = 70.0
    summary = calculate_inventory_plans(
        inventory_sample_df,
        service_level_label="95% (Z=1.65)",
        review_period_days=7,
        demand_multiplier=1.0,
        lead_time_delta_days=0,
    )

    assert summary.total_skus == 1
    plan = summary.plans[0]
    
    assert plan.product_id == "SKU-100"
    assert plan.avg_daily_demand == 10.0
    assert plan.lead_time_days == 7
    assert plan.lead_time_demand == 70.0
    # Reorder point must be >= lead_time_demand
    assert plan.reorder_point >= 70
    # Current stock is 50 < 70, so stockout risk must be TRUE
    assert plan.stockout_risk_flag is True
    assert plan.suggested_replenishment > 0
    assert plan.estimated_replenishment_cost == plan.suggested_replenishment * 25.0


def test_what_if_scenario_demand_multiplier(inventory_sample_df):
    # Base plan
    base_summary = calculate_inventory_plans(inventory_sample_df, demand_multiplier=1.0)
    base_plan = base_summary.plans[0]

    # Scenario with 1.5x demand surge
    surge_summary = calculate_inventory_plans(inventory_sample_df, demand_multiplier=1.5)
    surge_plan = surge_summary.plans[0]

    # Demand and lead-time demand should increase by 1.5x
    assert surge_plan.avg_daily_demand == 15.0
    assert surge_plan.lead_time_demand == 105.0
    assert surge_plan.reorder_point > base_plan.reorder_point
    assert surge_plan.suggested_replenishment > base_plan.suggested_replenishment


def test_what_if_scenario_lead_time_delta(inventory_sample_df):
    # Base lead time = 7 days. Add 3 days -> 10 days
    delayed_summary = calculate_inventory_plans(inventory_sample_df, lead_time_delta_days=3)
    plan = delayed_summary.plans[0]

    assert plan.lead_time_days == 10
    assert plan.lead_time_demand == 100.0  # 10 * 10
