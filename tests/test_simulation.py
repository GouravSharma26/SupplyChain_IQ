"""Tests for multi-period inventory policy simulation and sensitivity analysis."""

import numpy as np
import pandas as pd
import pytest

from supplychain_iq.simulation import (
    compare_standard_inventory_policies,
    run_lead_time_sensitivity_analysis,
    simulate_inventory_policy,
)


@pytest.fixture
def sim_demand_df():
    """Generates 90 days of demand data for a product."""
    dates = pd.date_range("2026-05-01", periods=90, freq="D")
    sales = [15.0 + (i % 5) * 3.0 for i in range(90)]
    return pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-SIM"] * 90,
        "product_name": ["Simulated Part"] * 90,
        "units_sold": sales,
        "inventory_on_hand": [100.0] * 90,
        "unit_cost": [25.0] * 90,
        "lead_time_days": [7.0] * 90,
    })


def test_simulate_inventory_policy_metrics(sim_demand_df):
    """Verify trace simulation computes fill rate, stockout days, and holding costs."""
    result = simulate_inventory_policy(
        sim_demand_df,
        product_id="SKU-SIM",
        target_service_level_pct=95.0,
        review_period_days=7,
        annual_holding_cost_rate=0.20,
    )

    assert result.total_demand_units > 0
    assert result.fulfilled_demand_units <= result.total_demand_units
    assert 0.0 <= result.fill_rate_pct <= 100.0
    assert 0.0 <= result.stockout_rate_pct <= 100.0
    assert result.avg_inventory_value >= 0.0
    assert result.estimated_holding_cost >= 0.0
    assert result.total_orders_placed >= 1


def test_compare_standard_policies_tradeoff(sim_demand_df):
    """Verify policy trade-off: higher service level buffers higher inventory and cost."""
    comparison = compare_standard_inventory_policies(sim_demand_df, product_id="SKU-SIM")
    assert len(comparison) == 3
    assert "Policy Name" in comparison.columns
    assert "Fill Rate" in comparison.columns
    assert "Est. Holding Cost (Annualized)" in comparison.columns


def test_lead_time_sensitivity_analysis(sim_demand_df):
    """Verify sensitivity table captures degradation as delay increases."""
    sens = run_lead_time_sensitivity_analysis(
        sim_demand_df,
        product_id="SKU-SIM",
        delay_steps=[0, 3, 7],
    )
    assert len(sens) == 9  # 3 delays * 3 service levels
    assert "Supplier Delay Delta (Days)" in sens.columns
    assert "Fill Rate (%)" in sens.columns
    assert "Holding Cost ($)" in sens.columns


def test_numeric_service_level_mapping_to_z():
    """Verify numeric target service levels (90, 95, 99) map strictly to their intended Z-scores."""
    from supplychain_iq.simulation import map_service_level_to_z

    # Integer targets
    assert map_service_level_to_z(90) == 1.28
    assert map_service_level_to_z(95) == 1.65
    assert map_service_level_to_z(99) == 2.33

    # Float targets
    assert map_service_level_to_z(90.0) == 1.28
    assert map_service_level_to_z(95.0) == 1.65
    assert map_service_level_to_z(99.0) == 2.33

    # Unit interval targets (0.90, 0.95, 0.99)
    assert map_service_level_to_z(0.90) == 1.28
    assert map_service_level_to_z(0.95) == 1.65
    assert map_service_level_to_z(0.99) == 2.33

    # Fallback to standard 95% (Z=1.65) for unknown
    assert map_service_level_to_z(None) == 1.65


def test_policies_reflect_configured_service_level(sim_demand_df):
    """
    Regression test proving that each policy uses its intended safety-stock factor
    and that otherwise comparable policies reflect the configured service level.
    """
    # Run comparable policies: same SKU, same demand trace, same 7-day review period
    res_90 = simulate_inventory_policy(sim_demand_df, product_id="SKU-SIM", target_service_level_pct=90.0, review_period_days=7)
    res_95 = simulate_inventory_policy(sim_demand_df, product_id="SKU-SIM", target_service_level_pct=95.0, review_period_days=7)
    res_99 = simulate_inventory_policy(sim_demand_df, product_id="SKU-SIM", target_service_level_pct=99.0, review_period_days=7)

    # 1. Proves intended safety-stock factors (Z-scores) are applied
    assert res_90.z_score == 1.28
    assert res_95.z_score == 1.65
    assert res_99.z_score == 2.33

    # 2. Proves safety stock scales monotonically with configured service level
    assert res_90.safety_stock_units < res_95.safety_stock_units < res_99.safety_stock_units

    # 3. Proves reorder point and target stock thresholds scale with configured service level
    assert res_90.reorder_point < res_95.reorder_point < res_99.reorder_point
    assert res_90.target_stock < res_95.target_stock < res_99.target_stock

    # 4. Proves average working capital and holding costs reflect configured service level
    assert res_90.avg_inventory_value < res_95.avg_inventory_value < res_99.avg_inventory_value
    assert res_90.estimated_holding_cost < res_95.estimated_holding_cost < res_99.estimated_holding_cost

    # 5. Proves service-level protection: higher service level yields >= fill rate and <= stockouts
    assert res_99.fill_rate_pct >= res_95.fill_rate_pct >= res_90.fill_rate_pct
    assert res_99.stockout_days <= res_95.stockout_days <= res_90.stockout_days

    # 6. Verify integer inputs also apply identical correct factors
    res_int_90 = simulate_inventory_policy(sim_demand_df, product_id="SKU-SIM", target_service_level_pct=90, review_period_days=7)
    res_int_99 = simulate_inventory_policy(sim_demand_df, product_id="SKU-SIM", target_service_level_pct=99, review_period_days=7)
    assert res_int_90.z_score == 1.28
    assert res_int_99.z_score == 2.33
    assert res_int_90.safety_stock_units == res_90.safety_stock_units
    assert res_int_99.safety_stock_units == res_99.safety_stock_units

