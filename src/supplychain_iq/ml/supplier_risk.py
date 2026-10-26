"""
Machine Learning models for Supplier Late-Delivery Risk Classification & Delay Regression.
Adheres strictly to FORECASTING_AND_ML.md and Plan B Phase 5 requirements:
- Strict target leakage exclusions (only order-time features allowed)
- Chronological train/test split (no random shuffling)
- Binary classification evaluated against Majority Class baseline (Precision, Recall, F1, PR-AUC, Confusion Matrix)
- Continuous delay regression evaluated against Mean Delay baseline (MAE, RMSE, R²)
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


@dataclass
class ClassificationMetrics:
    """Out-of-sample evaluation metrics for late delivery classification."""
    model_name: str
    precision: float
    recall: float
    f1: float
    pr_auc: float
    accuracy: float
    baseline_accuracy: float
    confusion_matrix: List[List[int]]  # [[TN, FP], [FN, TP]]
    class_balance_positive_pct: float
    threshold: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "pr_auc": self.pr_auc,
            "accuracy": self.accuracy,
            "baseline_accuracy": self.baseline_accuracy,
            "confusion_matrix": self.confusion_matrix,
            "positive_class_pct": f"{self.class_balance_positive_pct:.1f}%",
        }


@dataclass
class RegressionMetrics:
    """Out-of-sample evaluation metrics for continuous delay duration regression."""
    model_name: str
    mae: float
    rmse: float
    r2: float
    baseline_mae: float
    baseline_rmse: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "baseline_mae": self.baseline_mae,
            "baseline_rmse": self.baseline_rmse,
        }


@dataclass
class SupplierRiskReport:
    """Comprehensive ML report combining classification, regression, and feature importance."""
    total_orders_analyzed: int
    train_orders_count: int
    test_orders_count: int
    train_date_range: str
    test_date_range: str
    classification: Optional[ClassificationMetrics] = None
    regression: Optional[RegressionMetrics] = None
    feature_importances: Dict[str, float] = field(default_factory=dict)
    leakage_exclusions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_summary_table(self) -> pd.DataFrame:
        """Converts model evaluation metrics into an executive benchmark table."""
        rows = []
        if self.classification:
            rows.append({
                "Task": "Late Delivery Risk (Classification)",
                "Candidate Model": f"Random Forest (F1: {self.classification.f1:.2f}, PR-AUC: {self.classification.pr_auc:.2f})",
                "Baseline Model": f"Majority Class Baseline (Acc: {self.classification.baseline_accuracy:.2f})",
                "Key Error / Metric": f"Precision: {self.classification.precision:.2f} | Recall: {self.classification.recall:.2f}",
                "Out-of-Sample Lift": f"{(self.classification.accuracy - self.classification.baseline_accuracy)*100:+.1f}% Accuracy Delta",
            })
        if self.regression:
            rows.append({
                "Task": "Delay Duration Days (Regression)",
                "Candidate Model": f"Gradient Boosting (MAE: {self.regression.mae:.2f}d, R²: {self.regression.r2:.2f})",
                "Baseline Model": f"Training Mean Baseline (MAE: {self.regression.baseline_mae:.2f}d)",
                "Key Error / Metric": f"RMSE: {self.regression.rmse:.2f} days",
                "Out-of-Sample Lift": f"{((self.regression.baseline_mae - self.regression.mae) / max(0.01, self.regression.baseline_mae))*100:+.1f}% MAE Improvement",
            })
        return pd.DataFrame(rows)


def extract_order_features_and_targets(
    orders_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, List[str]]:
    """
    Extracts features available strictly at order placement time.
    Excludes target leakage columns (e.g. arrival dates, post-delivery delay fields).
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df = df.sort_values("order_date").reset_index(drop=True)

    # Document target leakage exclusions
    leakage_exclusions = [
        "actual_delivery_date (future arrival observation)",
        "delay_days (direct linear target function)",
        "delivery_status (post-shipment fulfillment state)",
    ]

    # Feature Engineering (strictly pre-shipment variables)
    features = pd.DataFrame(index=df.index)
    features["order_quantity"] = df["order_quantity"].astype(float)
    features["unit_cost"] = df["unit_cost"].astype(float)
    features["order_value"] = features["order_quantity"] * features["unit_cost"]
    
    # Base expected lead time days
    if "expected_delivery_date" in df.columns:
        expected_d = pd.to_datetime(df["expected_delivery_date"])
        features["promised_lead_time_days"] = (expected_d - df["order_date"]).dt.days.clip(lower=1)
    else:
        features["promised_lead_time_days"] = 7.0

    # Temporal variables at order creation
    features["order_dayofweek"] = df["order_date"].dt.dayofweek
    features["order_month"] = df["order_date"].dt.month
    features["is_quarter_end"] = df["order_date"].dt.is_quarter_end.astype(int)

    # Categorical encoding (supplier and product)
    cat_columns = []
    if "supplier_id" in df.columns:
        cat_columns.append("supplier_id")
    if "product_id" in df.columns:
        cat_columns.append("product_id")

    if cat_columns:
        dummies = pd.get_dummies(df[cat_columns].astype(str), prefix=cat_columns, drop_first=True)
        features = pd.concat([features, dummies], axis=1)

    # Targets
    target_class = df["is_late"].astype(int)
    target_reg = df["delay_days"].astype(float)

    return features, target_class, target_reg, leakage_exclusions


class SupplierRiskEvaluator:
    """Manages training, out-of-sample evaluation, and risk inference for supplier delays."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.clf_model: Optional[RandomForestClassifier] = None
        self.reg_model: Optional[GradientBoostingRegressor] = None
        self.feature_names: List[str] = []
        self.report: Optional[SupplierRiskReport] = None

    def fit_and_evaluate(
        self,
        orders_df: pd.DataFrame,
        train_ratio: float = 0.75,
    ) -> SupplierRiskReport:
        """
        Executes chronological split, trains models, evaluates against baselines,
        and generates an auditable SupplierRiskReport.
        """
        n_orders = len(orders_df)
        if n_orders < 12:
            return SupplierRiskReport(
                total_orders_analyzed=n_orders,
                train_orders_count=0,
                test_orders_count=0,
                train_date_range="N/A",
                test_date_range="N/A",
                limitations=[
                    f"Insufficient purchase order history ({n_orders} orders). Minimum 12 orders required for training/testing."
                ],
            )

        X, y_class, y_reg, leakage_exclusions = extract_order_features_and_targets(orders_df)
        self.feature_names = list(X.columns)

        # Chronological Split (strictly ordered by order_date)
        split_idx = int(n_orders * train_ratio)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_class_train, y_class_test = y_class.iloc[:split_idx], y_class.iloc[split_idx:]
        y_reg_train, y_reg_test = y_reg.iloc[:split_idx], y_reg.iloc[split_idx:]

        order_dates = pd.to_datetime(orders_df["order_date"]).sort_values().reset_index(drop=True)
        train_range = f"{order_dates.iloc[0].strftime('%Y-%m-%d')} to {order_dates.iloc[split_idx-1].strftime('%Y-%m-%d')}"
        test_range = f"{order_dates.iloc[split_idx].strftime('%Y-%m-%d')} to {order_dates.iloc[-1].strftime('%Y-%m-%d')}"

        # 1. Classification Model: Random Forest
        self.clf_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=4,
            random_state=self.random_state,
            class_weight="balanced" if y_class_train.nunique() > 1 else None,
        )
        self.clf_model.fit(X_train, y_class_train)

        # Predictions
        pred_class = self.clf_model.predict(X_test)
        if hasattr(self.clf_model, "predict_proba") and len(self.clf_model.classes_) > 1:
            pred_probs = self.clf_model.predict_proba(X_test)[:, 1]
        else:
            pred_probs = pred_class.astype(float)

        # Majority Class Baseline
        majority_class = int(y_class_train.mode().iloc[0])
        baseline_class_preds = np.full(len(y_class_test), fill_value=majority_class)
        baseline_accuracy = float(np.mean(baseline_class_preds == y_class_test))

        cm = confusion_matrix(y_class_test, pred_class, labels=[0, 1]).tolist()
        positive_pct = float(y_class_test.mean() * 100.0)

        clf_metrics = ClassificationMetrics(
            model_name="Random Forest Classifier (Balanced)",
            precision=round(float(precision_score(y_class_test, pred_class, zero_division=0)), 2),
            recall=round(float(recall_score(y_class_test, pred_class, zero_division=0)), 2),
            f1=round(float(f1_score(y_class_test, pred_class, zero_division=0)), 2),
            pr_auc=round(float(average_precision_score(y_class_test, pred_probs)), 2) if positive_pct > 0 else 0.0,
            accuracy=round(float(np.mean(pred_class == y_class_test)), 2),
            baseline_accuracy=round(baseline_accuracy, 2),
            confusion_matrix=cm,
            class_balance_positive_pct=positive_pct,
        )

        # 2. Regression Model: Gradient Boosting Regressor
        self.reg_model = GradientBoostingRegressor(
            n_estimators=40,
            max_depth=3,
            random_state=self.random_state,
        )
        self.reg_model.fit(X_train, y_reg_train)

        pred_reg = np.clip(self.reg_model.predict(X_test), a_min=0, a_max=None)
        
        # Mean Delay Baseline
        mean_delay_train = float(y_reg_train.mean())
        baseline_reg_preds = np.full(len(y_reg_test), fill_value=mean_delay_train)
        base_mae = round(float(mean_absolute_error(y_reg_test, baseline_reg_preds)), 2)
        base_rmse = round(float(np.sqrt(mean_squared_error(y_reg_test, baseline_reg_preds))), 2)

        reg_metrics = RegressionMetrics(
            model_name="Gradient Boosting Regressor",
            mae=round(float(mean_absolute_error(y_reg_test, pred_reg)), 2),
            rmse=round(float(np.sqrt(mean_squared_error(y_reg_test, pred_reg))), 2),
            r2=round(float(r2_score(y_reg_test, pred_reg)), 2) if np.var(y_reg_test) > 0 else 0.0,
            baseline_mae=base_mae,
            baseline_rmse=base_rmse,
        )

        # 3. Feature Importances
        importances = self.clf_model.feature_importances_
        feature_importance_dict = {
            col: round(float(imp), 3) for col, imp in sorted(zip(X.columns, importances), key=lambda x: x[1], reverse=True)
        }

        self.report = SupplierRiskReport(
            total_orders_analyzed=n_orders,
            train_orders_count=len(X_train),
            test_orders_count=len(X_test),
            train_date_range=train_range,
            test_date_range=test_range,
            classification=clf_metrics,
            regression=reg_metrics,
            feature_importances=feature_importance_dict,
            leakage_exclusions=leakage_exclusions,
            limitations=[
                "Model outputs represent statistical probabilistic estimates for decision support, not physical delivery guarantees.",
                "Feature importances are observational correlations and do not imply operational causality.",
                "Predictions reflect historical lead-time patterns and may shift under macro supplier disruptions.",
            ],
        )
        return self.report

    def predict_new_order_risk(
        self,
        order_quantity: int,
        unit_cost: float,
        promised_lead_time_days: int = 7,
        supplier_id: str = "SUP-101",
        product_id: str = "PRD-001",
    ) -> Dict[str, Any]:
        """Inference helper for an upcoming or simulated purchase order."""
        if self.clf_model is None or self.reg_model is None:
            return {"error": "Models not yet fitted."}

        # Create dummy record to match feature space
        row = pd.DataFrame([{
            "order_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "expected_delivery_date": (pd.Timestamp.now() + pd.Timedelta(days=promised_lead_time_days)).strftime("%Y-%m-%d"),
            "order_quantity": order_quantity,
            "unit_cost": unit_cost,
            "supplier_id": supplier_id,
            "product_id": product_id,
            "is_late": 0,
            "delay_days": 0,
        }])

        X_new, _, _, _ = extract_order_features_and_targets(row)
        # Align columns
        for col in self.feature_names:
            if col not in X_new.columns:
                X_new[col] = 0
        X_new = X_new[self.feature_names]

        prob_late = float(self.clf_model.predict_proba(X_new)[0, 1]) if hasattr(self.clf_model, "predict_proba") else 0.0
        predicted_delay = float(np.clip(self.reg_model.predict(X_new)[0], a_min=0, a_max=None))

        return {
            "late_delivery_probability_pct": round(prob_late * 100.0, 1),
            "predicted_delay_days": round(predicted_delay, 1),
            "risk_assessment": "High Risk" if prob_late >= 0.40 else "Moderate Risk" if prob_late >= 0.20 else "Low Risk",
        }


def train_and_evaluate_supplier_risk_models(orders_df: pd.DataFrame) -> SupplierRiskReport:
    """Convenience functional interface for model training and evaluation."""
    evaluator = SupplierRiskEvaluator()
    return evaluator.fit_and_evaluate(orders_df)


def synthesize_orders_from_demand_data(df: pd.DataFrame, num_orders: int = 45) -> pd.DataFrame:
    """
    Synthesizes a realistic purchase order history for training when analyzing
    datasets without explicit ERP purchase order ledgers.
    """
    rng = np.random.default_rng(42)
    products = df["product_id"].unique() if "product_id" in df.columns else ["PRD-001"]
    suppliers = (
        df["supplier_id"].unique()
        if "supplier_id" in df.columns
        else ["SUP-GLOBAL-01", "SUP-APAC-02", "SUP-LOCAL-03"]
    )

    costs = df.groupby("product_id")["unit_cost"].mean().to_dict() if "unit_cost" in df.columns else {}
    lead_times = df.groupby("product_id")["lead_time_days"].mean().to_dict() if "lead_time_days" in df.columns else {}

    min_date = pd.to_datetime(df["date"].min())
    max_date = pd.to_datetime(df["date"].max())
    span_days = max(1, (max_date - min_date).days)

    rows = []
    for _ in range(num_orders):
        p_id = str(rng.choice(products))
        s_id = str(rng.choice(suppliers))
        unit_c = float(costs.get(p_id, 25.0))
        base_lead = int(round(lead_times.get(p_id, 7.0)))

        offset = int(rng.integers(0, span_days))
        order_d = min_date + pd.Timedelta(days=offset)
        expected_d = order_d + pd.Timedelta(days=base_lead)

        is_late = int(rng.random() < 0.25)
        delay = int(rng.integers(2, 7)) if is_late else 0
        actual_d = expected_d + pd.Timedelta(days=delay)
        qty = int(rng.integers(50, 400))

        rows.append({
            "order_date": order_d.strftime("%Y-%m-%d"),
            "expected_delivery_date": expected_d.strftime("%Y-%m-%d"),
            "actual_delivery_date": actual_d.strftime("%Y-%m-%d"),
            "product_id": p_id,
            "supplier_id": s_id,
            "order_quantity": qty,
            "unit_cost": unit_c,
            "is_late": is_late,
            "delay_days": delay,
            "status": "Delivered",
        })

    res_df = pd.DataFrame(rows)
    res_df["order_date"] = pd.to_datetime(res_df["order_date"])
    return res_df.sort_values("order_date").reset_index(drop=True)

