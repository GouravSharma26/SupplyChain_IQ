"""
Supply chain analytics and KPI calculations for SupplyChain IQ.
Computes KPIs strictly outside Streamlit UI to ensure testability and data integrity.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd


@dataclass
class KPISummary:
    """Summary of core supply chain operational metrics."""
    total_units_sold: int
    calendar_days: int
    avg_daily_demand: float
    total_inventory_units: int
    total_inventory_value: float
    avg_lead_time_days: float
    lead_time_sample_size: int
    active_products_count: int
    potential_stockout_count: int
    supplier_on_time_rate: Optional[float] = None
    supplier_sample_size: int = 0
    inventory_turnover: Optional[float] = None
    turnover_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_units_sold": self.total_units_sold,
            "calendar_days": self.calendar_days,
            "avg_daily_demand": self.avg_daily_demand,
            "total_inventory_units": self.total_inventory_units,
            "total_inventory_value": self.total_inventory_value,
            "avg_lead_time_days": self.avg_lead_time_days,
            "lead_time_sample_size": self.lead_time_sample_size,
            "active_products_count": self.active_products_count,
            "potential_stockout_count": self.potential_stockout_count,
            "supplier_on_time_rate": self.supplier_on_time_rate,
            "supplier_sample_size": self.supplier_sample_size,
            "inventory_turnover": self.inventory_turnover,
            "turnover_note": self.turnover_note,
        }


def filter_dataset(
    df: pd.DataFrame,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    product_ids: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filters dataset chronologically and by dimensions."""
    if df.empty:
        return df.copy()

    filtered = df.copy()
    if start_date is not None:
        filtered = filtered[filtered["date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["date"] <= pd.to_datetime(end_date)]
    if product_ids:
        filtered = filtered[filtered["product_id"].isin(product_ids)]
    if categories and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(categories)]

    return filtered.reset_index(drop=True)


def calculate_kpis(df: pd.DataFrame, stockout_product_count: int = 0) -> KPISummary:
    """
    Calculates executive supply chain KPIs adhering strictly to DATA_AND_METRICS.md.
    Uses latest snapshot for current inventory valuation rather than summing across dates.
    """
    if df.empty:
        return KPISummary(
            total_units_sold=0,
            calendar_days=0,
            avg_daily_demand=0.0,
            total_inventory_units=0,
            total_inventory_value=0.0,
            avg_lead_time_days=0.0,
            lead_time_sample_size=0,
            active_products_count=0,
            potential_stockout_count=0,
            inventory_turnover=None,
            turnover_note="Unavailable: Dataset is empty",
        )

    # 1. Total units sold
    total_units_sold = int(df["units_sold"].sum())

    # 2. Calendar days span
    min_date = df["date"].min()
    max_date = df["date"].max()
    calendar_days = max(1, (max_date - min_date).days + 1)
    avg_daily_demand = round(total_units_sold / calendar_days, 2)

    # 3. Inventory snapshot valuation (latest record per product_id)
    latest_inventory_df = (
        df.sort_values("date")
        .groupby("product_id")
        .last()
        .reset_index()
    )
    total_inventory_units = int(latest_inventory_df["inventory_on_hand"].sum())
    total_inventory_value = round(
        float((latest_inventory_df["inventory_on_hand"] * latest_inventory_df["unit_cost"]).sum()), 2
    )

    # 4. Average lead time
    lead_times = df["lead_time_days"].dropna()
    avg_lead_time = round(float(lead_times.mean()), 1) if not lead_times.empty else 0.0
    lead_time_sample_size = len(lead_times)

    # 5. Distinct active products
    active_products = int(df["product_id"].nunique())

    # 6. Supplier on-time rate (if delivery_delay_days exists)
    supplier_on_time_rate = None
    supplier_sample_size = 0
    if "delivery_delay_days" in df.columns:
        delays = df["delivery_delay_days"].dropna()
        if not delays.empty:
            supplier_sample_size = len(delays)
            on_time_count = (delays <= 0).sum()
            supplier_on_time_rate = round(float((on_time_count / supplier_sample_size) * 100), 1)

    # 7. Inventory turnover (COGS / average inventory)
    # COGS = units_sold * unit_cost over the period
    cogs = float((df["units_sold"] * df["unit_cost"]).sum())
    # Daily average inventory value across all observation dates
    daily_inv_val = (
        df.groupby("date")
        .apply(lambda d: (d["inventory_on_hand"] * d["unit_cost"]).sum(), include_groups=False)
    )
    avg_inv_val = float(daily_inv_val.mean()) if not daily_inv_val.empty else 0.0

    if avg_inv_val > 0 and calendar_days >= 30:
        # Annualized turnover = (COGS / avg_inv_val) * (365 / calendar_days)
        turnover = round((cogs / avg_inv_val) * (365 / calendar_days), 2)
        turnover_note = f"Annualized based on {calendar_days} calendar days."
    else:
        turnover = None
        turnover_note = (
            "Unavailable: Requires at least 30 calendar days of inventory and cost history "
            "for meaningful annualized turnover."
        )

    return KPISummary(
        total_units_sold=total_units_sold,
        calendar_days=calendar_days,
        avg_daily_demand=avg_daily_demand,
        total_inventory_units=total_inventory_units,
        total_inventory_value=total_inventory_value,
        avg_lead_time_days=avg_lead_time,
        lead_time_sample_size=lead_time_sample_size,
        active_products_count=active_products,
        potential_stockout_count=stockout_product_count,
        supplier_on_time_rate=supplier_on_time_rate,
        supplier_sample_size=supplier_sample_size,
        inventory_turnover=turnover,
        turnover_note=turnover_note,
    )


def get_daily_demand_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates units sold by calendar date across all or filtered products."""
    if df.empty:
        return pd.DataFrame(columns=["date", "units_sold"])

    trend = (
        df.groupby("date", as_index=False)["units_sold"]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    return trend


def get_product_demand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarizes volume, revenue, and cost by product."""
    if df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby(["product_id", "product_name"], as_index=False)
        .agg(
            total_units_sold=("units_sold", "sum"),
            avg_daily_demand=("units_sold", lambda s: round(s.sum() / max(1, df["date"].nunique()), 2)),
            latest_stock=("inventory_on_hand", "last"),
            unit_cost=("unit_cost", "last"),
            avg_lead_time=("lead_time_days", "mean"),
        )
    )
    summary["latest_inventory_value"] = summary["latest_stock"] * summary["unit_cost"]
    summary["avg_lead_time"] = summary["avg_lead_time"].round(1)
    return summary.sort_values(by="total_units_sold", ascending=False).reset_index(drop=True)


def get_inventory_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates daily total on-hand inventory units and estimated value."""
    if df.empty:
        return pd.DataFrame(columns=["date", "total_inventory_units", "total_inventory_value"])

    df_copy = df.copy()
    df_copy["row_val"] = df_copy["inventory_on_hand"] * df_copy["unit_cost"]
    daily_inv = (
        df_copy.groupby("date", as_index=False)
        .agg(
            total_inventory_units=("inventory_on_hand", "sum"),
            total_inventory_value=("row_val", "sum"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily_inv["total_inventory_value"] = daily_inv["total_inventory_value"].round(2)
    return daily_inv


def calculate_supplier_scorecard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes empirical supplier performance metrics from observation or purchase order records.
    Calculates on-time percentage, delay duration, lead times, and assigns operational risk tiers.
    """
    if df.empty or "supplier_id" not in df.columns:
        return pd.DataFrame()

    has_delay = "delivery_delay_days" in df.columns
    has_supplier_name = "supplier_name" in df.columns

    records = []
    for sup_id, group in df.groupby("supplier_id"):
        sup_name = group["supplier_name"].iloc[0] if has_supplier_name else f"Supplier {sup_id}"
        total_obs = len(group)
        lead_time_mean = round(float(group["lead_time_days"].mean()), 1) if "lead_time_days" in group.columns else 0.0

        if has_delay:
            delays = group["delivery_delay_days"].dropna()
            total_shipments = len(delays)
            on_time_count = int((delays <= 0).sum())
            on_time_rate = round(float((on_time_count / max(1, total_shipments)) * 100), 1)
            avg_delay = round(float(delays[delays > 0].mean()), 1) if (delays > 0).any() else 0.0
            max_delay = int(delays.max()) if not delays.empty else 0
        else:
            on_time_rate = None
            avg_delay = 0.0
            max_delay = 0
            total_shipments = 0

        # Assign Risk Category: Low (>=95%), Moderate (85-94%), High (<85%)
        if on_time_rate is not None:
            if on_time_rate >= 95.0:
                risk_tier = "Low"
            elif on_time_rate >= 85.0:
                risk_tier = "Moderate"
            else:
                risk_tier = "High"
        else:
            risk_tier = "Unclassified"

        records.append({
            "supplier_id": str(sup_id),
            "supplier_name": str(sup_name),
            "total_observations": total_obs,
            "avg_lead_time_days": lead_time_mean,
            "on_time_rate_pct": on_time_rate,
            "avg_delay_days": avg_delay,
            "max_delay_days": max_delay,
            "risk_tier": risk_tier,
        })

    return pd.DataFrame(records).sort_values(by="avg_lead_time_days", ascending=True).reset_index(drop=True)


def calculate_product_mix_abc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs Pareto ABC inventory classification based on latest inventory valuation.
    - Class A: Cumulative value up to 70% (Critical control)
    - Class B: Next 20% (70% - 90%, Moderate control)
    - Class C: Remaining 10% (90% - 100%, Simplified control)
    """
    if df.empty:
        return pd.DataFrame()

    latest_df = (
        df.sort_values("date")
        .groupby("product_id")
        .last()
        .reset_index()
    )
    latest_df["inventory_value"] = latest_df["inventory_on_hand"] * latest_df["unit_cost"]

    # Total units sold across historical window
    sales_vol = df.groupby("product_id")["units_sold"].sum().reset_index()
    merged = pd.merge(latest_df, sales_vol, on="product_id", suffixes=("", "_total"))

    # Sort descending by inventory valuation
    sorted_df = merged.sort_values(by="inventory_value", ascending=False).reset_index(drop=True)
    total_val = sorted_df["inventory_value"].sum()

    if total_val > 0:
        sorted_df["value_share_pct"] = (sorted_df["inventory_value"] / total_val * 100).round(1)
        sorted_df["cum_value_share_pct"] = sorted_df["value_share_pct"].cumsum().round(1)
    else:
        sorted_df["value_share_pct"] = 0.0
        sorted_df["cum_value_share_pct"] = 0.0

    def assign_abc(cum_share: float) -> str:
        if cum_share <= 70.0:
            return "Class A"
        elif cum_share <= 90.0:
            return "Class B"
        return "Class C"

    sorted_df["abc_classification"] = sorted_df["cum_value_share_pct"].apply(assign_abc)
    sorted_df["inventory_value"] = sorted_df["inventory_value"].round(2)

    return sorted_df[[
        "product_id",
        "product_name",
        "category",
        "inventory_on_hand",
        "unit_cost",
        "inventory_value",
        "value_share_pct",
        "cum_value_share_pct",
        "abc_classification",
    ]]


def generate_executive_insights(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates structured, auditable business insights adhering to Phase 3 criteria:
    Each insight contains a metric, time range, comparison benchmark, and explicit caveats.
    """
    if df.empty:
        return []

    min_date = df["date"].min().strftime("%Y-%m-%d")
    max_date = df["date"].max().strftime("%Y-%m-%d")
    calendar_days = max(1, (df["date"].max() - df["date"].min()).days + 1)
    kpis = calculate_kpis(df)
    abc_df = calculate_product_mix_abc(df)
    sup_df = calculate_supplier_scorecard(df)

    insights = []

    # 1. Demand & Growth Velocity
    insights.append({
        "domain": "Demand Velocity",
        "metric": f"{kpis.total_units_sold:,} units ({kpis.avg_daily_demand:.1f} units/day)",
        "time_range": f"{min_date} to {max_date} ({calendar_days} calendar days)",
        "benchmark": "Benchmark against baseline run-rate across 5 enterprise SKUs",
        "caveat": "Observed sales serve as proxy for unconstrained demand; stockouts may cap reported velocity.",
        "recommendation": "Review high-velocity SKUs against reorder triggers to prevent stock compression.",
    })

    # 2. Inventory Capital Exposure & Pareto Concentration
    top_class_a = abc_df[abc_df["abc_classification"] == "Class A"]
    class_a_share = top_class_a["value_share_pct"].sum() if not top_class_a.empty else 0.0
    insights.append({
        "domain": "Capital Exposure & Pareto Concentration",
        "metric": f"${kpis.total_inventory_value:,.2f} total valuation ({class_a_share:.1f}% concentrated in Class A)",
        "time_range": f"Snapshot as of {max_date}",
        "benchmark": "Target Pareto threshold: 70% capital allocation in high-turnover lines",
        "caveat": "Valuation reflects unit costs provided in input records, not adjusted for carrying or holding overhead.",
        "recommendation": "Enforce tight continuous cycle-counting on Class A items; apply periodic review on Class C.",
    })

    # 3. Supplier Fulfillment Reliability
    if not sup_df.empty and "on_time_rate_pct" in sup_df.columns and sup_df["on_time_rate_pct"].notna().any():
        avg_on_time = round(float(sup_df["on_time_rate_pct"].dropna().mean()), 1)
        high_risk = sup_df[sup_df["risk_tier"] == "High"]
        risk_note = f"{len(high_risk)} high-risk supplier(s) identified" if not high_risk.empty else "All suppliers meet baseline SLAs"
        insights.append({
            "domain": "Supplier Lead-Time & Reliability",
            "metric": f"{avg_on_time}% average on-time delivery ({risk_note})",
            "time_range": f"{min_date} to {max_date}",
            "benchmark": "Enterprise target: >=95% on-time fulfillment rate",
            "caveat": "Delay days computed from empirical shipment delivery jitter against baseline lead time.",
            "recommendation": "Buffer safety stock dynamically on suppliers exhibiting >15% late-delivery variance.",
        })

    # 4. Inventory Turnover Velocity
    if kpis.inventory_turnover is not None:
        insights.append({
            "domain": "Inventory Turnover Velocity",
            "metric": f"{kpis.inventory_turnover:.2f}x annualized turns",
            "time_range": f"{min_date} to {max_date} ({calendar_days} days observed)",
            "benchmark": "Industry wholesale benchmark: 4.0x - 8.0x annualized turns",
            "caveat": kpis.turnover_note,
            "recommendation": "Maintain reorder points synchronized with seasonal shifts to preserve turnover velocity.",
        })

    return insights
