"""
Multi-period inventory policy simulation and sensitivity analysis for SupplyChain IQ.
Adheres strictly to Plan B Phase 6 requirements:
- Distinguishes deterministic rule-based replenishment from empirical trace simulation.
- Day-by-day discrete event simulation tracking stockouts, fill rates, inventory holding costs, and orders.
- Evaluates policy trade-offs (Lean 90% vs Balanced 95% vs Resilient 99%).
- Lead time disruption sensitivity analysis.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from supplychain_iq.inventory import SERVICE_LEVEL_Z


@dataclass
class PolicySimulationResult:
    """Summary metrics of a multi-period inventory policy simulation."""
    policy_name: str
    target_service_level_pct: float
    review_period_days: int
    total_demand_units: int
    fulfilled_demand_units: int
    unmet_demand_units: int
    fill_rate_pct: float
    stockout_days: int
    stockout_rate_pct: float
    avg_inventory_units: float
    avg_inventory_value: float
    estimated_holding_cost: float
    total_orders_placed: int
    total_replenishment_units: int
    holding_cost_rate_annual: float = 0.20

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Policy Name": self.policy_name,
            "Target Service Level": f"{self.target_service_level_pct:.0f}%",
            "Review Period": f"{self.review_period_days} days",
            "Fill Rate": f"{self.fill_rate_pct:.1f}%",
            "Stockout Days": f"{self.stockout_days} days ({self.stockout_rate_pct:.1f}%)",
            "Avg Inventory Value": f"${self.avg_inventory_value:,.2f}",
            "Est. Holding Cost (Annualized)": f"${self.estimated_holding_cost:,.2f}",
            "Orders Placed": self.total_orders_placed,
        }


def simulate_inventory_policy(
    df: pd.DataFrame,
    product_id: str,
    target_service_level_pct: float = 95.0,
    review_period_days: int = 7,
    lead_time_delay_days: int = 0,
    annual_holding_cost_rate: float = 0.20,
    policy_name: str = "Standard Policy",
) -> PolicySimulationResult:
    """
    Simulates daily inventory movement across the historical demand sequence under a specified (s, S) policy.
    """
    sub_df = df[df["product_id"] == product_id].sort_values("date").reset_index(drop=True)
    if sub_df.empty:
        return PolicySimulationResult(
            policy_name=policy_name,
            target_service_level_pct=target_service_level_pct,
            review_period_days=review_period_days,
            total_demand_units=0,
            fulfilled_demand_units=0,
            unmet_demand_units=0,
            fill_rate_pct=100.0,
            stockout_days=0,
            stockout_rate_pct=0.0,
            avg_inventory_units=0.0,
            avg_inventory_value=0.0,
            estimated_holding_cost=0.0,
            total_orders_placed=0,
            total_replenishment_units=0,
        )

    # Calculate baseline parameters
    demands = sub_df["units_sold"].to_numpy().astype(float)
    avg_daily_demand = float(np.mean(demands))
    std_daily_demand = float(np.std(demands, ddof=1)) if len(demands) > 1 else 0.0
    base_lead_time = float(sub_df["lead_time_days"].iloc[0]) if "lead_time_days" in sub_df.columns else 7.0
    effective_lead_time = max(1.0, base_lead_time + lead_time_delay_days)
    unit_cost = float(sub_df["unit_cost"].iloc[0])

    # Compute Policy Thresholds: ROP and Target Stock S
    z = SERVICE_LEVEL_Z.get(target_service_level_pct, 1.65)
    safety_stock = z * std_daily_demand * np.sqrt(effective_lead_time)
    lead_time_demand = avg_daily_demand * effective_lead_time
    reorder_point = int(np.ceil(lead_time_demand + safety_stock))
    review_demand = avg_daily_demand * review_period_days
    target_stock = int(np.ceil(reorder_point + review_demand))

    # Initial state
    current_stock = float(target_stock)
    pipeline_orders: List[Tuple[int, int]] = []  # List of (arrival_day_index, quantity)

    total_demand = 0
    fulfilled_demand = 0
    unmet_demand = 0
    stockout_days_count = 0
    daily_stock_values = []
    total_orders = 0
    total_replenishment_qty = 0

    n_days = len(demands)
    for t in range(n_days):
        # 1. Pipeline arrivals at start of day
        arrived_qty = sum(qty for arr_day, qty in pipeline_orders if arr_day == t)
        current_stock += arrived_qty

        # 2. Demand fulfillment
        daily_d = int(demands[t])
        total_demand += daily_d
        units_sold = min(daily_d, int(current_stock))
        fulfilled_demand += units_sold
        unmet = daily_d - units_sold
        unmet_demand += unmet

        if current_stock <= 0 or unmet > 0:
            stockout_days_count += 1

        current_stock = max(0.0, current_stock - units_sold)
        daily_stock_values.append(current_stock * unit_cost)

        # 3. Replenishment Review Check
        is_review_day = (review_period_days <= 1) or (t % review_period_days == 0)
        pending_on_order = sum(qty for arr_day, qty in pipeline_orders if arr_day > t)
        inventory_position = current_stock + pending_on_order

        if is_review_day and (inventory_position <= reorder_point):
            order_qty = max(0, target_stock - int(inventory_position))
            if order_qty > 0:
                arrival_day = t + int(effective_lead_time)
                pipeline_orders.append((arrival_day, order_qty))
                total_orders += 1
                total_replenishment_qty += order_qty

    # Metrics Compilation
    fill_rate = round((fulfilled_demand / max(1, total_demand)) * 100.0, 1)
    stockout_rate = round((stockout_days_count / max(1, n_days)) * 100.0, 1)
    avg_inv_val = float(np.mean(daily_stock_values)) if daily_stock_values else 0.0
    avg_inv_units = round(avg_inv_val / max(0.01, unit_cost), 1)

    # Annualized holding cost = avg inventory value * annual rate * (days / 365)
    holding_cost = round(avg_inv_val * annual_holding_cost_rate * (n_days / 365.0), 2)

    return PolicySimulationResult(
        policy_name=policy_name,
        target_service_level_pct=target_service_level_pct,
        review_period_days=review_period_days,
        total_demand_units=total_demand,
        fulfilled_demand_units=fulfilled_demand,
        unmet_demand_units=unmet_demand,
        fill_rate_pct=fill_rate,
        stockout_days=stockout_days_count,
        stockout_rate_pct=stockout_rate,
        avg_inventory_units=avg_inv_units,
        avg_inventory_value=round(avg_inv_val, 2),
        estimated_holding_cost=holding_cost,
        total_orders_placed=total_orders,
        total_replenishment_units=total_replenishment_qty,
        holding_cost_rate_annual=annual_holding_cost_rate,
    )


def compare_standard_inventory_policies(
    df: pd.DataFrame,
    product_id: str,
    annual_holding_cost_rate: float = 0.20,
) -> pd.DataFrame:
    """
    Compares 3 standard enterprise operating policies on identical historical demand traces:
    - Lean Just-in-Time: 90% Service Level, 0-day review period (continuous reorder)
    - Balanced Policy: 95% Service Level, 7-day review period
    - Resilient Buffer: 99% Service Level, 14-day review period
    """
    policies = [
        ("Lean JIT", 90.0, 1),
        ("Balanced Standard", 95.0, 7),
        ("Resilient Buffer", 99.0, 14),
    ]

    results = []
    for name, sl, rev in policies:
        res = simulate_inventory_policy(
            df=df,
            product_id=product_id,
            target_service_level_pct=sl,
            review_period_days=rev,
            annual_holding_cost_rate=annual_holding_cost_rate,
            policy_name=name,
        )
        results.append(res.to_dict())

    return pd.DataFrame(results)


def run_lead_time_sensitivity_analysis(
    df: pd.DataFrame,
    product_id: str,
    delay_steps: Optional[List[int]] = None,
) -> pd.DataFrame:
    """
    Evaluates policy degradation as supplier lead time delays increase (+0d to +10d).
    Produces sensitivity trade-off between Fill Rate % and Holding Cost ($).
    """
    if delay_steps is None:
        delay_steps = [0, 2, 4, 7, 10]

    records = []
    for delay in delay_steps:
        for sl in [90.0, 95.0, 99.0]:
            res = simulate_inventory_policy(
                df=df,
                product_id=product_id,
                target_service_level_pct=sl,
                review_period_days=7,
                lead_time_delay_days=delay,
                policy_name=f"{sl:.0f}% SL (+{delay}d delay)",
            )
            records.append({
                "Supplier Delay Delta (Days)": delay,
                "Service Level Target": f"{sl:.0f}%",
                "Fill Rate (%)": res.fill_rate_pct,
                "Stockout Days": res.stockout_days,
                "Avg Inventory Value ($)": res.avg_inventory_value,
                "Holding Cost ($)": res.estimated_holding_cost,
            })

    return pd.DataFrame(records)
