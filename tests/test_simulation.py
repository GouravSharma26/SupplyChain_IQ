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
