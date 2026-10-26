"""
Data loader module for SupplyChain IQ.
Handles deterministic sample dataset generation, bundling, and CSV ingestion.
"""

from pathlib import Path
from typing import Optional, Tuple, Union
import io
import numpy as np
import pandas as pd

from supplychain_iq.validation import validate_and_clean_dataset, ValidationReport

SAMPLE_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_supply_chain.csv"
DATA_PROVENANCE_NOTE = (
    "Sample Dataset Provenance: Synthetically generated deterministic dataset (180 days, 5 SKUs, "
    "seed=42) designed for SupplyChain IQ verification, baseline forecasting, and inventory simulation."
)


def generate_synthetic_dataset(num_days: int = 180, seed: int = 42) -> pd.DataFrame:
    """
    Generates a deterministic, realistic supply chain dataset for demonstration.
    Simulates daily sales, dynamic inventory replenishment, lead times, and supplier performance.
    """
    np.random.seed(seed)
    
    products = [
        {
            "product_id": "PRD-001",
            "product_name": "Industrial Sensor Node",
            "category": "Electronics",
            "supplier_id": "SUP-101",
            "supplier_name": "Apex Micro Systems",
            "base_demand": 24,
            "unit_cost": 42.50,
            "selling_price": 85.00,
            "lead_time_days": 7,
            "initial_stock": 280,
            "batch_order_qty": 200,
        },
        {
            "product_id": "PRD-002",
            "product_name": "Hydraulic Control Valve",
            "category": "Hardware",
            "supplier_id": "SUP-102",
            "supplier_name": "Vanguard Flow Systems",
            "base_demand": 12,
            "unit_cost": 115.00,
            "selling_price": 220.00,
            "lead_time_days": 14,
            "initial_stock": 210,
            "batch_order_qty": 180,
        },
        {
            "product_id": "PRD-003",
            "product_name": "Li-Polymer Battery Pack",
            "category": "Energy Storage",
            "supplier_id": "SUP-101",
            "supplier_name": "Apex Micro Systems",
            "base_demand": 38,
            "unit_cost": 62.00,
            "selling_price": 125.00,
            "lead_time_days": 10,
            "initial_stock": 450,
            "batch_order_qty": 350,
        },
        {
            "product_id": "PRD-004",
            "product_name": "Thermal Conductive Adhesive",
            "category": "Consumables",
            "supplier_id": "SUP-103",
            "supplier_name": "Prime Materials Corp",
            "base_demand": 55,
            "unit_cost": 18.00,
            "selling_price": 38.00,
            "lead_time_days": 4,
            "initial_stock": 420,
            "batch_order_qty": 300,
        },
        {
            "product_id": "PRD-005",
            "product_name": "Embedded IoT Gateway",
            "category": "Electronics",
            "supplier_id": "SUP-101",
            "supplier_name": "Apex Micro Systems",
            "base_demand": 16,
            "unit_cost": 155.00,
            "selling_price": 295.00,
            "lead_time_days": 12,
            "initial_stock": 200,
            "batch_order_qty": 150,
        },
    ]

    start_date = pd.Timestamp("2026-05-01")
    date_range = [start_date + pd.Timedelta(days=i) for i in range(num_days)]
    
    rows = []

    for p in products:
        current_stock = p["initial_stock"]
        pipeline_orders = []  # List of tuples: (arrival_day_index, qty)
        
        for day_idx, current_date in enumerate(date_range):
            # Check pipeline deliveries arriving on this day
            arrived_qty = sum(qty for arr_idx, qty in pipeline_orders if arr_idx == day_idx)
            current_stock += arrived_qty

            # Weekly seasonality factor (higher mid-week Tue-Thu)
            dow = current_date.dayofweek
            seasonality = 1.0 + (0.15 if dow in [1, 2, 3] else -0.12 if dow in [5, 6] else 0.02)
            
            # Subtle trend over time
            trend_factor = 1.0 + (day_idx / num_days) * 0.10
            
            # Simulated Poisson-like demand
            expected_demand = p["base_demand"] * seasonality * trend_factor
            actual_sales = max(0, int(np.random.poisson(lam=expected_demand)))
            
            # Stock cannot drop below zero
            units_sold = min(actual_sales, current_stock)
            current_stock -= units_sold

            # Reorder logic for simulation realism: order when below 2.5 * lead_time_demand
            reorder_threshold = int(p["base_demand"] * p["lead_time_days"] * 1.5)
            # Pending orders in transit
            pending_qty = sum(qty for arr_idx, qty in pipeline_orders if arr_idx > day_idx)
            if (current_stock + pending_qty) <= reorder_threshold:
                # Place replenishment order
                # Delivery delay jitter (-1, 0, 1, 2 days)
                delay_days = max(0, int(np.random.choice([0, 0, 1, 2, 3], p=[0.60, 0.20, 0.10, 0.07, 0.03])))
                arrival_day = day_idx + p["lead_time_days"] + delay_days
                pipeline_orders.append((arrival_day, p["batch_order_qty"]))

            delay = int(np.random.choice([0, 1, 2, 4], p=[0.75, 0.15, 0.07, 0.03]))

            rows.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "product_id": p["product_id"],
                "product_name": p["product_name"],
                "category": p["category"],
                "supplier_id": p["supplier_id"],
                "supplier_name": p["supplier_name"],
                "units_sold": units_sold,
                "inventory_on_hand": current_stock,
                "unit_cost": p["unit_cost"],
                "selling_price": p["selling_price"],
                "lead_time_days": p["lead_time_days"],
                "delivery_delay_days": delay,
                "region": "North America",
            })

    df = pd.DataFrame(rows)
    return df


def ensure_sample_csv_exists(file_path: Optional[Path] = None) -> Path:
    """Ensures deterministic sample CSV exists on disk."""
    target_path = file_path or SAMPLE_DATA_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        df = generate_synthetic_dataset(num_days=180, seed=42)
        df.to_csv(target_path, index=False)
    return target_path


def load_sample_dataset(file_path: Optional[Path] = None) -> Tuple[pd.DataFrame, ValidationReport]:
    """Loads and validates the bundled sample dataset."""
    target_path = ensure_sample_csv_exists(file_path)
    df_raw = pd.read_csv(target_path)
    return validate_and_clean_dataset(df_raw)


def load_csv_data(
    file_or_buffer: Union[str, Path, io.BytesIO, io.StringIO]
) -> Tuple[pd.DataFrame, ValidationReport]:
    """Loads and validates user-provided CSV data."""
    try:
        df_raw = pd.read_csv(file_or_buffer)
    except Exception as e:
        report = ValidationReport(
            total_rows=0,
            is_valid=False,
            error_message=f"Failed to read CSV file: {str(e)}"
        )
        return pd.DataFrame(), report
    return validate_and_clean_dataset(df_raw)
