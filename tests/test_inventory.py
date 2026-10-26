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


def test_demand_multiplier_scales_variability_and_safety_stock():
    # Variable daily demand series with non-zero standard deviation
    dates = pd.date_range("2026-05-01", periods=20, freq="D")
    sales = [10, 20, 15, 25, 10, 20, 15, 25, 10, 20, 15, 25, 10, 20, 15, 25, 10, 20, 15, 25]
    df = pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-VAR"] * 20,
        "product_name": ["Variable Demand Sensor"] * 20,
        "units_sold": sales,
        "inventory_on_hand": [200] * 20,
        "unit_cost": [30.0] * 20,
        "lead_time_days": [7] * 20,
    })

    base_summary = calculate_inventory_plans(df, demand_multiplier=1.0)
    base_plan = base_summary.plans[0]

    # Double the demand multiplier to 2.0x
    surge_summary = calculate_inventory_plans(df, demand_multiplier=2.0)
    surge_plan = surge_summary.plans[0]

    # Verify that standard deviation scales with the multiplier: σ(2·D) = 2·σ(D)
    assert surge_plan.avg_daily_demand == round(base_plan.avg_daily_demand * 2.0, 2)
    assert round(surge_plan.std_daily_demand, 1) == round(base_plan.std_daily_demand * 2.0, 1)
    
    # Consequently, safety stock must be higher under the surged scenario
    assert surge_plan.safety_stock > base_plan.safety_stock
