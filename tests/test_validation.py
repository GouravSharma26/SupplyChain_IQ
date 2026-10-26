"""
Unit tests for data validation, schema contracts, and quality reporting.
"""

import pandas as pd
import pytest

from supplychain_iq.validation import validate_and_clean_dataset, REQUIRED_COLUMNS


def test_valid_dataset():
    df = pd.DataFrame({
        "date": ["2026-05-01", "2026-05-02"],
        "product_id": ["P1", "P1"],
        "product_name": ["Widget A", "Widget A"],
        "units_sold": [10, 15],
        "inventory_on_hand": [100, 85],
        "unit_cost": [5.0, 5.0],
        "lead_time_days": [7, 7],
    })
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is True
    assert report.valid_rows == 2
    assert report.rejected_rows == 0
    assert len(clean_df) == 2
    assert clean_df["product_id"].iloc[0] == "P1"


def test_empty_dataset():
    df = pd.DataFrame()
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is False
    assert "empty" in report.error_message.lower()
    assert clean_df.empty


def test_missing_required_columns():
    df = pd.DataFrame({
        "date": ["2026-05-01"],
        "product_id": ["P1"],
        # missing units_sold, inventory_on_hand, unit_cost, lead_time_days
    })
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is False
    assert "Missing required contract columns" in report.error_message


def test_invalid_dates_and_negative_values():
    df = pd.DataFrame({
        "date": ["2026-05-01", "not-a-date", "2026-05-03"],
        "product_id": ["P1", "P1", "P1"],
        "units_sold": [10, 15, -5],  # 3rd row has negative sales
        "inventory_on_hand": [100, 85, 50],
        "unit_cost": [5.0, 5.0, 5.0],
        "lead_time_days": [7, 7, 7],
    })
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is True
    assert report.valid_rows == 1  # Only row 0 is completely valid
    assert report.rejected_rows == 2
    assert "Unparseable observation date" in report.rejection_reasons
    assert "Negative value in units_sold" in report.rejection_reasons


def test_product_name_fallback_when_absent():
    df = pd.DataFrame({
        "date": ["2026-05-01"],
        "product_id": ["SKU-999"],
        "units_sold": [5],
        "inventory_on_hand": [20],
        "unit_cost": [12.0],
        "lead_time_days": [3],
    })
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is True
    assert clean_df["product_name"].iloc[0] == "SKU-999"


def test_exact_duplicates_handling():
    row = {
        "date": "2026-05-01",
        "product_id": "P1",
        "units_sold": 10,
        "inventory_on_hand": 100,
        "unit_cost": 5.0,
        "lead_time_days": 7,
    }
    df = pd.DataFrame([row, row])  # Identical duplicates
    clean_df, report = validate_and_clean_dataset(df)
    assert report.is_valid is True
    assert report.duplicate_rows_count == 1
    assert len(clean_df) == 1
