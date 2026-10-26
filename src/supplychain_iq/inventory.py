"""
Inventory optimization, reorder-point calculations, and what-if simulation for SupplyChain IQ.
Adheres strictly to DATA_AND_METRICS.md formulas and assumption disclosures.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd


SERVICE_LEVEL_Z = {
    "90% (Z=1.28)": 1.28,
    "95% (Z=1.65)": 1.65,
    "99% (Z=2.33)": 2.33,
}

ASSUMPTION_DISCLOSURE = (
    "Decision Support Notice: Recommendations and scenario simulations are automated rule-based "
    "estimates intended for operational planning. They do not constitute automated purchasing orders "
    "or financial obligations."
)


@dataclass
class ProductInventoryPlan:
    """Calculated replenishment parameters for a single SKU."""
    product_id: str
    product_name: str
    current_stock: int
    unit_cost: float
    lead_time_days: int
    avg_daily_demand: float
    std_daily_demand: float
    lead_time_demand: float
    safety_stock: int
    reorder_point: int
    target_stock: int
    suggested_replenishment: int
    stockout_risk_flag: bool
    estimated_replenishment_cost: float
    status_label: str  # "URGENT REORDER", "MONITOR", "HEALTHY"


@dataclass
class InventoryPlanSummary:
    """Executive inventory planning aggregate metrics."""
    plans: List[ProductInventoryPlan]
    total_skus: int
    at_risk_skus_count: int
    total_suggested_units: int
    total_suggested_cost: float
    service_level: str
    review_period_days: int
    demand_multiplier: float
    lead_time_delta_days: int

    def to_dataframe(self) -> pd.DataFrame:
        """Converts SKU plans into a presentation DataFrame."""
        rows = []
        for p in self.plans:
            rows.append({
                "Product ID": p.product_id,
                "Product Name": p.product_name,
                "Current Stock": p.current_stock,
                "Unit Cost ($)": f"${p.unit_cost:.2f}",
                "Lead Time (Days)": p.lead_time_days,
                "Avg Daily Demand": round(p.avg_daily_demand, 1),
                "Lead-Time Demand": round(p.lead_time_demand, 1),
                "Safety Stock": p.safety_stock,
                "Reorder Point": p.reorder_point,
                "Target Stock": p.target_stock,
                "Suggested Reorder": p.suggested_replenishment,
                "Est. Reorder Cost ($)": f"${p.estimated_replenishment_cost:,.2f}",
                "Stockout Risk": "AT RISK" if p.stockout_risk_flag else "OK",
                "Status": p.status_label,
            })
        return pd.DataFrame(rows)


def calculate_inventory_plans(
    df: pd.DataFrame,
    service_level_label: str = "95% (Z=1.65)",
    review_period_days: int = 7,
    demand_multiplier: float = 1.0,
    lead_time_delta_days: int = 0,
) -> InventoryPlanSummary:
    """
    Computes reorder points, safety stock, and replenishment plans across all products.
    Supports what-if simulation via demand multiplier and lead time adjustment.
    """
    if df.empty:
        return InventoryPlanSummary(
            plans=[],
            total_skus=0,
            at_risk_skus_count=0,
            total_suggested_units=0,
            total_suggested_cost=0.0,
            service_level=service_level_label,
            review_period_days=review_period_days,
            demand_multiplier=demand_multiplier,
            lead_time_delta_days=lead_time_delta_days,
        )

    z_factor = SERVICE_LEVEL_Z.get(service_level_label, 1.65)
    plans: List[ProductInventoryPlan] = []

    # Calculate overall calendar days span
    calendar_days = max(1, (df["date"].max() - df["date"].min()).days + 1)

    for pid, group in df.groupby("product_id"):
        # Most recent snapshot for stock and cost
        sorted_grp = group.sort_values("date")
        latest_row = sorted_grp.iloc[-1]
        
        product_name = str(latest_row.get("product_name", pid))
        current_stock = max(0, int(latest_row["inventory_on_hand"]))
        unit_cost = float(latest_row["unit_cost"])
        
        # Base lead time with what-if scenario adjustment (minimum 1 day)
        base_lead_time = max(1, int(round(float(group["lead_time_days"].mean()))))
        scenario_lead_time = max(1, base_lead_time + lead_time_delta_days)

        # Baseline demand metrics
        total_units = float(group["units_sold"].sum())
        base_daily_demand = total_units / calendar_days
        
        # Scenario demand
        scenario_daily_demand = max(0.0, base_daily_demand * demand_multiplier)

        # Daily sales standard deviation for safety stock calculation
        # Baseline standard deviation of observed daily demand
        daily_units = group.groupby("date")["units_sold"].sum()
        base_std_demand = float(daily_units.std()) if len(daily_units) > 1 else (base_daily_demand * 0.25)
        if np.isnan(base_std_demand) or base_std_demand == 0:
            base_std_demand = base_daily_demand * 0.25

        # In scenario simulation, scaling demand by c scales standard deviation by c: σ(c·D) = c·σ(D)
        scenario_std_daily_demand = max(0.0, base_std_demand * demand_multiplier)

        # 1. Lead-time demand = avg_daily_demand * lead_time
        lead_time_demand = scenario_daily_demand * scenario_lead_time

        # 2. Safety stock = Z * sigma_demand * sqrt(lead_time)
        safety_stock = int(np.ceil(z_factor * scenario_std_daily_demand * np.sqrt(scenario_lead_time)))

        # 3. Reorder point = lead_time_demand + safety_stock
        reorder_point = int(np.ceil(lead_time_demand + safety_stock))

        # 4. Target stock = reorder_point + (avg_daily_demand * review_period)
        cycle_stock = int(np.ceil(scenario_daily_demand * review_period_days))
        target_stock = reorder_point + cycle_stock

        # 5. Suggested replenishment = max(0, target_stock - current_stock)
        suggested_replenishment = max(0, target_stock - current_stock)
        replenishment_cost = round(suggested_replenishment * unit_cost, 2)

        # 6. Risk flag
        stockout_risk = current_stock < reorder_point

        if current_stock == 0:
            status_label = "CRITICAL: STOCKOUT"
        elif stockout_risk:
            status_label = "URGENT: REORDER"
        elif current_stock < (reorder_point * 1.25):
            status_label = "MONITOR CLOSELY"
        else:
            status_label = "HEALTHY"

        plans.append(ProductInventoryPlan(
            product_id=str(pid),
            product_name=product_name,
            current_stock=current_stock,
            unit_cost=unit_cost,
            lead_time_days=scenario_lead_time,
            avg_daily_demand=round(scenario_daily_demand, 2),
            std_daily_demand=round(scenario_std_daily_demand, 2),
            lead_time_demand=round(lead_time_demand, 1),
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            target_stock=target_stock,
            suggested_replenishment=suggested_replenishment,
            stockout_risk_flag=stockout_risk,
            estimated_replenishment_cost=replenishment_cost,
            status_label=status_label,
        ))

    at_risk = sum(1 for p in plans if p.stockout_risk_flag)
    total_suggested_units = sum(p.suggested_replenishment for p in plans)
    total_suggested_cost = round(sum(p.estimated_replenishment_cost for p in plans), 2)

    return InventoryPlanSummary(
        plans=plans,
        total_skus=len(plans),
        at_risk_skus_count=at_risk,
        total_suggested_units=total_suggested_units,
        total_suggested_cost=total_suggested_cost,
        service_level=service_level_label,
        review_period_days=review_period_days,
        demand_multiplier=demand_multiplier,
        lead_time_delta_days=lead_time_delta_days,
    )
