"""
Data validation and quality reporting module for SupplyChain IQ.
Ensures strict adherence to data contracts and transparent error reporting.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = [
    "date",
    "product_id",
    "units_sold",
    "inventory_on_hand",
    "unit_cost",
    "lead_time_days",
]

OPTIONAL_COLUMNS = [
    "product_name",
    "category",
    "supplier_id",
    "supplier_name",
    "delivery_delay_days",
    "region",
    "selling_price",
]


@dataclass
class ValidationReport:
    """Detailed summary of data cleaning and contract validation."""
    total_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    rejection_reasons: Dict[str, int] = field(default_factory=dict)
    missing_values_by_column: Dict[str, int] = field(default_factory=dict)
    duplicate_rows_count: int = 0
    distinct_products_count: int = 0
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "rejected_rows": self.rejected_rows,
            "rejection_reasons": self.rejection_reasons,
            "missing_values_by_column": self.missing_values_by_column,
            "duplicate_rows_count": self.duplicate_rows_count,
            "distinct_products_count": self.distinct_products_count,
            "min_date": self.min_date,
            "max_date": self.max_date,
            "warnings": self.warnings,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
        }


def validate_and_clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, ValidationReport]:
    """
    Validates a raw DataFrame against the SupplyChain IQ data contract.
    
    Returns:
        Tuple[pd.DataFrame, ValidationReport]:
            Cleaned and normalized DataFrame (sorted by date, product_id)
            and a comprehensive ValidationReport.
    """
    report = ValidationReport(total_rows=len(df_raw))

    if df_raw.empty:
        report.error_message = "Dataset is empty. At least one row of supply chain data is required."
        return pd.DataFrame(), report

    # Normalize column names: strip whitespace, lowercase
    df = df_raw.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Verify required columns exist
    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        report.error_message = (
            f"Missing required contract columns: {', '.join(missing_required)}. "
            f"Required columns are: {', '.join(REQUIRED_COLUMNS)}."
        )
        report.warnings.append(f"Missing required columns: {missing_required}")
        return pd.DataFrame(), report

    # Optional column check
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            if col == "product_name":
                # Fallback product_name to product_id if absent
                df["product_name"] = df["product_id"].astype(str)
            else:
                report.warnings.append(f"Optional column '{col}' is absent in dataset.")

    # Record missing values per column across original data
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            report.missing_values_by_column[col] = null_count

    # Check for exact duplicate rows
    exact_duplicates = int(df.duplicated().sum())
    report.duplicate_rows_count = exact_duplicates
    if exact_duplicates > 0:
        report.warnings.append(f"Found {exact_duplicates} exact duplicate rows. Retaining unique rows.")
        df = df.drop_duplicates()

    # Reject rows with missing product_id or empty string
    rejection_reasons: Dict[str, int] = {}
    valid_mask = pd.Series(True, index=df.index)

    # 1. Product ID non-empty
    prod_id_series = df["product_id"].astype(str).str.strip()
    invalid_prod_id = df["product_id"].isna() | (prod_id_series == "") | (prod_id_series == "nan")
    if invalid_prod_id.any():
        count = int(invalid_prod_id.sum())
        rejection_reasons["Missing or empty product_id"] = count
        valid_mask &= ~invalid_prod_id

    # 2. Date parsing
    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = parsed_dates.isna()
    if invalid_dates.any():
        count = int(invalid_dates.sum())
        rejection_reasons["Unparseable observation date"] = count
        valid_mask &= ~invalid_dates
    df["date"] = parsed_dates

    # 3. Numeric fields check and nonnegativity
    numeric_fields = ["units_sold", "inventory_on_hand", "unit_cost", "lead_time_days"]
    for num_col in numeric_fields:
        numeric_series = pd.to_numeric(df[num_col], errors="coerce")
        nan_numeric = numeric_series.isna()
        if nan_numeric.any():
            count = int(nan_numeric.sum())
            rejection_reasons[f"Non-numeric value in {num_col}"] = (
                rejection_reasons.get(f"Non-numeric value in {num_col}", 0) + count
            )
            valid_mask &= ~nan_numeric

        negative_mask = (numeric_series < 0) & (~nan_numeric)
        if negative_mask.any():
            count = int(negative_mask.sum())
            rejection_reasons[f"Negative value in {num_col}"] = (
                rejection_reasons.get(f"Negative value in {num_col}", 0) + count
            )
            valid_mask &= ~negative_mask

        df[num_col] = numeric_series

    # Check optional numeric fields if present
    for opt_num in ["delivery_delay_days", "selling_price"]:
        if opt_num in df.columns:
            df[opt_num] = pd.to_numeric(df[opt_num], errors="coerce")

    # Filter valid rows
    rejected_count = int((~valid_mask).sum())
    report.rejected_rows = rejected_count
    report.rejection_reasons = rejection_reasons

    clean_df = df[valid_mask].copy()
    report.valid_rows = len(clean_df)

    if clean_df.empty:
        report.error_message = "All rows were rejected during validation. Check data types and required columns."
        return pd.DataFrame(), report

    # Product name fallback if empty
    if "product_name" in clean_df.columns:
        clean_df["product_name"] = clean_df["product_name"].fillna(clean_df["product_id"])
        clean_df["product_name"] = clean_df["product_name"].replace("", np.nan).fillna(clean_df["product_id"])
    else:
        clean_df["product_name"] = clean_df["product_id"].astype(str)

    # Sort deterministically
    clean_df["product_id"] = clean_df["product_id"].astype(str).str.strip()
    clean_df = clean_df.sort_values(by=["date", "product_id"]).reset_index(drop=True)

    # Summary metrics
    report.distinct_products_count = int(clean_df["product_id"].nunique())
    min_d = clean_df["date"].min()
    max_d = clean_df["date"].max()
    report.min_date = min_d.strftime("%Y-%m-%d") if pd.notna(min_d) else None
    report.max_date = max_d.strftime("%Y-%m-%d") if pd.notna(max_d) else None

    # Check for duplicate (date, product_id) observation pairs
    date_prod_dups = int(clean_df.duplicated(subset=["date", "product_id"]).sum())
    if date_prod_dups > 0:
        report.warnings.append(
            f"Dataset has {date_prod_dups} duplicate (date, product_id) records. "
            "Aggregating units_sold and taking latest inventory state."
        )
        agg_rules = {
            "units_sold": "sum",
            "inventory_on_hand": "last",
            "unit_cost": "last",
            "lead_time_days": "mean",
            "product_name": "first",
        }
        for opt in ["category", "supplier_id", "supplier_name", "region"]:
            if opt in clean_df.columns:
                agg_rules[opt] = "first"
        if "selling_price" in clean_df.columns:
            agg_rules["selling_price"] = "mean"
        if "delivery_delay_days" in clean_df.columns:
            agg_rules["delivery_delay_days"] = "mean"

        clean_df = (
            clean_df.groupby(["date", "product_id"], as_index=False)
            .agg(agg_rules)
            .sort_values(by=["date", "product_id"])
            .reset_index(drop=True)
        )
        report.valid_rows = len(clean_df)

    # Sparsity warning: Check if any product has fewer than 14 records
    prod_counts = clean_df["product_id"].value_counts()
    short_history_prods = prod_counts[prod_counts < 14].index.tolist()
    if short_history_prods:
        report.warnings.append(
            f"{len(short_history_prods)} product(s) have fewer than 14 observations: "
            f"{', '.join(short_history_prods[:3])}{'...' if len(short_history_prods) > 3 else ''}."
        )

    report.is_valid = True
    return clean_df, report
