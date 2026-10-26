"""CLI and helper script to deterministically seed the relational database."""

import argparse
from pathlib import Path
import pandas as pd

from supplychain_iq.data_loader import load_sample_dataset
from supplychain_iq.db.database import get_db_engine, get_db_session, init_db
from supplychain_iq.db.etl import load_from_curated_dataframe


def seed_database(database_url: str = None) -> None:
    """Populate the database with validated benchmark records."""
    engine = get_db_engine(database_url)
    init_db(engine)

    print("Loading benchmark supply chain data...")
    df, report = load_sample_dataset()

    with get_db_session(engine) as session:
        result = load_from_curated_dataframe(session, df)
        print(f"ETL Status: {result.status}")
        print(f"Suppliers Loaded: {result.suppliers_loaded}")
        print(f"Products Loaded: {result.products_loaded}")
        print(f"Daily Demand Records Loaded: {result.daily_demands_loaded}")
        print(f"Inventory Snapshots Loaded: {result.snapshots_loaded}")
        print(f"Purchase Orders Loaded: {result.purchase_orders_loaded}")
        print(f"Rejected Rows: {result.rejected_rows}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SupplyChain IQ database.")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL")
    args = parser.parse_args()
    seed_database(args.db_url)
