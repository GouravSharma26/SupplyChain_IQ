"""Tests for Supplier Delay Risk Machine Learning models and evaluations."""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from supplychain_iq.ml.supplier_risk import (
    SupplierRiskEvaluator,
    extract_order_features_and_targets,
    train_and_evaluate_supplier_risk_models,
)


@pytest.fixture
def synthetic_orders_df():
    """Generates 30 synthetic purchase orders for ML testing."""
    rng = np.random.default_rng(42)
    start_date = pd.Timestamp("2026-05-01")
    rows = []
    for i in range(30):
        order_d = start_date + pd.Timedelta(days=i * 5)
        base_lead = 7
        is_late = int(rng.random() < 0.30)
        delay = int(rng.integers(2, 6)) if is_late else 0
        expected_d = order_d + pd.Timedelta(days=base_lead)
        actual_d = expected_d + pd.Timedelta(days=delay)

        rows.append({
            "order_date": order_d.strftime("%Y-%m-%d"),
            "expected_delivery_date": expected_d.strftime("%Y-%m-%d"),
            "actual_delivery_date": actual_d.strftime("%Y-%m-%d"),
            "product_id": rng.choice(["PRD-001", "PRD-002", "PRD-003"]),
            "supplier_id": rng.choice(["SUP-101", "SUP-102"]),
            "order_quantity": int(rng.integers(50, 300)),
            "unit_cost": float(rng.uniform(15.0, 50.0)),
            "is_late": is_late,
            "delay_days": delay,
            "status": "Delivered",
        })
    return pd.DataFrame(rows)


def test_target_leakage_exclusions(synthetic_orders_df):
    """Verify that features exclude arrival dates and delay fields."""
    X, y_class, y_reg, exclusions = extract_order_features_and_targets(synthetic_orders_df)
    
    assert "actual_delivery_date" not in X.columns
    assert "delay_days" not in X.columns
    assert "is_late" not in X.columns
    assert "status" not in X.columns
    assert len(exclusions) >= 2


def test_supplier_risk_model_training_and_evaluation(synthetic_orders_df):
    """Verify out-of-sample classification and regression training and benchmarking."""
    evaluator = SupplierRiskEvaluator(random_state=42)
    report = evaluator.fit_and_evaluate(synthetic_orders_df, train_ratio=0.70)

    assert report.total_orders_analyzed == 30
    assert report.train_orders_count == 21
    assert report.test_orders_count == 9

    # Classification metrics
    clf = report.classification
    assert clf is not None
    assert clf.precision >= 0.0
    assert clf.recall >= 0.0
    assert clf.f1 >= 0.0
    assert clf.pr_auc >= 0.0
    assert len(clf.confusion_matrix) == 2  # 2x2 matrix

    # Regression metrics
    reg = report.regression
    assert reg is not None
    assert reg.mae >= 0.0
    assert reg.rmse >= 0.0
    assert reg.baseline_mae >= 0.0

    # Summary table formatting
    summary = report.to_summary_table()
    assert len(summary) == 2
    assert "Out-of-Sample Lift" in summary.columns


def test_inference_on_new_order(synthetic_orders_df):
    """Verify inference helper produces valid probability and delay predictions."""
    evaluator = SupplierRiskEvaluator(random_state=42)
    evaluator.fit_and_evaluate(synthetic_orders_df)

    pred = evaluator.predict_new_order_risk(
        order_quantity=150,
        unit_cost=30.0,
        promised_lead_time_days=7,
        supplier_id="SUP-101",
        product_id="PRD-001",
    )
    assert "late_delivery_probability_pct" in pred
    assert 0.0 <= pred["late_delivery_probability_pct"] <= 100.0
    assert "predicted_delay_days" in pred
    assert pred["predicted_delay_days"] >= 0.0
    assert pred["risk_assessment"] in ["High Risk", "Moderate Risk", "Low Risk"]


def test_insufficient_order_history_fallback():
    """Verify graceful fallback when history is too small for ML."""
    tiny_df = pd.DataFrame([{
        "order_date": "2026-05-01",
        "expected_delivery_date": "2026-05-08",
        "actual_delivery_date": "2026-05-08",
        "product_id": "PRD-1",
        "supplier_id": "SUP-1",
        "order_quantity": 50,
        "unit_cost": 20.0,
        "is_late": 0,
        "delay_days": 0,
    }])
    report = train_and_evaluate_supplier_risk_models(tiny_df)
    assert report.classification is None
    assert len(report.limitations) > 0
    assert "Insufficient purchase order history" in report.limitations[0]


def test_synthesize_orders_from_demand_data():
    """Verify purchase order history synthesis from demand records."""
    from supplychain_iq.ml import synthesize_orders_from_demand_data

    demand_df = pd.DataFrame([
        {
            "date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
            "product_id": "PRD-001",
            "supplier_id": "SUP-101",
            "unit_cost": 25.0,
            "lead_time_days": 7.0,
            "units_sold": 10,
            "inventory_on_hand": 100,
        }
        for i in range(30)
    ])

    orders = synthesize_orders_from_demand_data(demand_df, num_orders=20)
    assert len(orders) == 20
    assert "order_date" in orders.columns
    assert "order_quantity" in orders.columns
    assert "is_late" in orders.columns
    assert "delay_days" in orders.columns
    assert orders["order_quantity"].min() >= 10

