"""ETL pipelines: raw -> staging -> curated validation and relational loading."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from supplychain_iq.db.database import get_db_session, init_db
from supplychain_iq.db.models import (
    DailyDemand,
    InventorySnapshot,
    Product,
    PurchaseOrder,
    Supplier,
)
from supplychain_iq.validation import validate_and_clean_dataset


@dataclass
class ETLLoadResult:
    """Detailed summary of an ETL loading batch."""
    status: str
    load_timestamp: datetime
    products_loaded: int = 0
    suppliers_loaded: int = 0
    daily_demands_loaded: int = 0
    snapshots_loaded: int = 0
    purchase_orders_loaded: int = 0
    rejected_rows: int = 0
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "load_timestamp": self.load_timestamp.isoformat(),
            "products_loaded": self.products_loaded,
            "suppliers_loaded": self.suppliers_loaded,
            "daily_demands_loaded": self.daily_demands_loaded,
            "snapshots_loaded": self.snapshots_loaded,
            "purchase_orders_loaded": self.purchase_orders_loaded,
            "rejected_rows": self.rejected_rows,
            "rejection_reasons": self.rejection_reasons,
        }


def load_from_curated_dataframe(session: Session, df: pd.DataFrame) -> ETLLoadResult:
    """Ingest a validated supply chain dataframe into relational models with idempotency."""
    result = ETLLoadResult(
        status="IN_PROGRESS",
        load_timestamp=datetime.now(timezone.utc),
    )

    # Staging & Validation Gate
    clean_df, report = validate_and_clean_dataset(df)
    if not report.is_valid or clean_df.empty:
        result.status = "REJECTED"
        result.rejected_rows = report.rejected_rows or len(df)
        reasons = [report.error_message] if report.error_message else []
        reasons.extend(report.warnings)
        result.rejection_reasons = reasons
        return result

    result.rejected_rows = report.rejected_rows
    result.rejection_reasons = [f"{k}: {v}" for k, v in report.rejection_reasons.items()]

    # 1. Staging -> Curated Suppliers
    # Determine unique suppliers if supplier columns exist, or infer from categories
    suppliers_map: Dict[str, Supplier] = {}
    if "supplier_id" in clean_df.columns:
        sup_records = clean_df.groupby("supplier_id").agg({
            "lead_time_days": "mean"
        }).reset_index()
        for _, row in sup_records.iterrows():
            sup_id = str(row["supplier_id"])
            existing_sup = session.get(Supplier, sup_id)
            if not existing_sup:
                existing_sup = Supplier(
                    id=sup_id,
                    name=f"Supplier {sup_id}",
                    country="Domestic",
                    lead_time_days=float(row["lead_time_days"]),
                    reliability_score=0.92,
                )
                session.add(existing_sup)
                result.suppliers_loaded += 1
            suppliers_map[sup_id] = existing_sup
    else:
        # Create default tier-1 suppliers for products
        default_sups = [
            ("SUP-GLOBAL-01", "Global Logistics Corp", "Germany", 10.0, 0.94),
            ("SUP-APAC-02", "PacRim Industrial", "Japan", 14.0, 0.88),
            ("SUP-LOCAL-03", "Apex Domestic Distributors", "USA", 5.0, 0.97),
        ]
        for sup_id, name, country, lead_t, rel in default_sups:
            existing_sup = session.get(Supplier, sup_id)
            if not existing_sup:
                existing_sup = Supplier(
                    id=sup_id,
                    name=name,
                    country=country,
                    lead_time_days=lead_t,
                    reliability_score=rel,
                )
                session.add(existing_sup)
                result.suppliers_loaded += 1
            suppliers_map[sup_id] = existing_sup
    session.flush()

    # 2. Staging -> Curated Products
    products_grouped = clean_df.groupby("product_id").agg({
        "product_name": "first",
        "category": "first" if "category" in clean_df.columns else lambda x: "General",
        "unit_cost": "mean",
    }).reset_index()

    supplier_keys = list(suppliers_map.keys())
    for idx, row in products_grouped.iterrows():
        p_id = str(row["product_id"])
        existing_p = session.get(Product, p_id)
        assigned_sup = supplier_keys[idx % len(supplier_keys)] if supplier_keys else None
        cost = float(row["unit_cost"])
        price = cost * 1.45  # Standard 45% markup

        if not existing_p:
            existing_p = Product(
                id=p_id,
                name=str(row["product_name"]),
                category=str(row["category"]) if "category" in clean_df.columns else "General",
                unit_cost=cost,
                selling_price=price,
                min_order_qty=25,
                supplier_id=assigned_sup,
            )
            session.add(existing_p)
            result.products_loaded += 1
        else:
            existing_p.name = str(row["product_name"])
            existing_p.unit_cost = cost
            existing_p.selling_price = price
    session.flush()

    # 3. Staging -> Curated DailyDemand & InventorySnapshots
    for _, row in clean_df.iterrows():
        obs_date = pd.to_datetime(row["date"]).date()
        p_id = str(row["product_id"])
        units = float(row["units_sold"])
        stock = float(row["inventory_on_hand"])

        # Idempotent DailyDemand upsert
        existing_demand = session.execute(
            select(DailyDemand).where(
                DailyDemand.date == obs_date,
                DailyDemand.product_id == p_id,
            )
        ).scalar_one_or_none()

        if not existing_demand:
            demand_entry = DailyDemand(
                date=obs_date,
                product_id=p_id,
                units_sold=units,
                channel="Omnichannel",
                promotion_applied=False,
            )
            session.add(demand_entry)
            result.daily_demands_loaded += 1
        else:
            existing_demand.units_sold = units

        # Idempotent InventorySnapshot upsert
        existing_snap = session.execute(
            select(InventorySnapshot).where(
                InventorySnapshot.date == obs_date,
                InventorySnapshot.product_id == p_id,
            )
        ).scalar_one_or_none()

        if not existing_snap:
            snap_entry = InventorySnapshot(
                date=obs_date,
                product_id=p_id,
                inventory_on_hand=stock,
                safety_stock_target=stock * 0.25,
                stockout_flag=stock <= 0,
            )
            session.add(snap_entry)
            result.snapshots_loaded += 1
        else:
            existing_snap.inventory_on_hand = stock
            existing_snap.stockout_flag = stock <= 0

    session.flush()

    # 4. Synthesize realistic PurchaseOrders if none exist
    po_count = session.execute(select(func.count(PurchaseOrder.id))).scalar_one()
    if po_count == 0:
        rng = np.random.default_rng(42)
        po_id_counter = 1000
        min_date = clean_df["date"].min().date() if hasattr(clean_df["date"].min(), "date") else pd.to_datetime(clean_df["date"].min()).date()
        max_date = clean_df["date"].max().date() if hasattr(clean_df["date"].max(), "date") else pd.to_datetime(clean_df["date"].max()).date()
        total_days = max(1, (max_date - min_date).days)

        for p_id in products_grouped["product_id"]:
            prod = session.get(Product, str(p_id))
            sup_id = prod.supplier_id if prod else supplier_keys[0]
            sup = session.get(Supplier, sup_id)
            base_lead = int(sup.lead_time_days) if sup else 7

            # Generate ~8 purchase orders across the timeline
            for _ in range(8):
                po_id_counter += 1
                offset = int(rng.integers(0, total_days))
                order_d = min_date + timedelta(days=offset)
                expected_d = order_d + timedelta(days=base_lead)

                # 20% probability of late delivery
                is_late = bool(rng.random() < 0.22)
                delay = int(rng.integers(2, 8)) if is_late else 0
                actual_d = expected_d + timedelta(days=delay)

                po = PurchaseOrder(
                    id=f"PO-{po_id_counter}",
                    order_date=order_d,
                    expected_delivery_date=expected_d,
                    actual_delivery_date=actual_d,
                    product_id=str(p_id),
                    supplier_id=sup_id,
                    order_quantity=int(rng.integers(50, 300)),
                    unit_cost=prod.unit_cost if prod else 20.0,
                    status="Delivered",
                    is_late=is_late,
                    delay_days=delay,
                )
                session.add(po)
                result.purchase_orders_loaded += 1

    session.flush()
    result.status = "SUCCESS"
    return result


def query_curated_dataframe(session: Session) -> pd.DataFrame:
    """Extract a curated consolidated dataframe matching the application contract."""
    stmt = (
        select(
            DailyDemand.date.label("date"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.category.label("category"),
            DailyDemand.units_sold.label("units_sold"),
            InventorySnapshot.inventory_on_hand.label("inventory_on_hand"),
            Product.unit_cost.label("unit_cost"),
            Supplier.lead_time_days.label("lead_time_days"),
            Supplier.id.label("supplier_id"),
            Supplier.name.label("supplier_name"),
        )
        .join(Product, DailyDemand.product_id == Product.id)
        .join(
            InventorySnapshot,
            (DailyDemand.date == InventorySnapshot.date)
            & (DailyDemand.product_id == InventorySnapshot.product_id),
        )
        .outerjoin(Supplier, Product.supplier_id == Supplier.id)
        .order_by(DailyDemand.date.asc(), Product.id.asc())
    )

    rows = session.execute(stmt).all()
    if not rows:
        return pd.DataFrame(columns=[
            "date", "product_id", "product_name", "category",
            "units_sold", "inventory_on_hand", "unit_cost",
            "lead_time_days", "supplier_id", "supplier_name"
        ])

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def query_supplier_fulfillment_metrics(session: Session) -> pd.DataFrame:
    """Calculate empirical supplier fulfillment KPIs from purchase order records."""
    stmt = select(PurchaseOrder)
    pos = session.execute(stmt).scalars().all()
    if not pos:
        return pd.DataFrame()

    records = [
        {
            "po_id": po.id,
            "order_date": po.order_date,
            "expected_delivery_date": po.expected_delivery_date,
            "actual_delivery_date": po.actual_delivery_date,
            "supplier_id": po.supplier_id,
            "product_id": po.product_id,
            "order_quantity": po.order_quantity,
            "is_late": po.is_late,
            "delay_days": po.delay_days,
        }
        for po in pos
    ]
    df_pos = pd.DataFrame(records)

    summary = df_pos.groupby("supplier_id").agg(
        total_orders=("po_id", "count"),
        late_orders=("is_late", "sum"),
        avg_delay_days=("delay_days", "mean"),
        max_delay_days=("delay_days", "max"),
    ).reset_index()

    summary["on_time_rate"] = 1.0 - (summary["late_orders"] / summary["total_orders"])
    return summary
