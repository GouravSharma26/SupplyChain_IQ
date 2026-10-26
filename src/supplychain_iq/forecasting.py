"""
Demand forecasting and chronological model evaluation engine for SupplyChain IQ.
Adheres strictly to FORECASTING_AND_ML.md:
- Strictly chronological split (zero random-shuffling)
- Naïve baseline benchmark
- Out-of-sample MAE & RMSE evaluation
- Minimum history validation with nontechnical fallbacks
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


MIN_HISTORY_FOR_MODEL = 28  # Minimum days required for Exponential Smoothing


@dataclass
class ForecastResult:
    """Encapsulates forecast series, holdout metrics, and diagnostic metadata."""
    model_name: str
    baseline_name: str
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    test_days: int
    forecast_horizon: int
    mae_model: Optional[float] = None
    rmse_model: Optional[float] = None
    mae_baseline: Optional[float] = None
    rmse_baseline: Optional[float] = None
    historical_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    test_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    forecast_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    warnings: List[str] = field(default_factory=list)
    fallback_used: bool = False

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "baseline_name": self.baseline_name,
            "train_period": f"{self.train_start} to {self.train_end}",
            "test_period": f"{self.test_start} to {self.test_end}",
            "test_window_days": self.test_days,
            "forecast_horizon_days": self.forecast_horizon,
            "model_mae": self.mae_model,
            "model_rmse": self.rmse_model,
            "baseline_mae": self.mae_baseline,
            "baseline_rmse": self.rmse_baseline,
            "fallback_used": self.fallback_used,
            "warnings": self.warnings,
        }


def prepare_regular_time_series(df: pd.DataFrame, product_id: Optional[str] = None) -> pd.DataFrame:
    """
    Filters and aggregates daily demand into a continuous time-series index.
    Missing calendar days within the range are filled with 0 (no recorded sales).
    """
    if df.empty:
        return pd.DataFrame(columns=["date", "units_sold"])

    data = df.copy()
    if product_id is not None and product_id != "ALL":
        data = data[data["product_id"] == product_id]

    if data.empty:
        return pd.DataFrame(columns=["date", "units_sold"])

    # Aggregate daily demand
    daily = (
        data.groupby("date", as_index=False)["units_sold"]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Reindex to continuous calendar dates
    min_date = daily["date"].min()
    max_date = daily["date"].max()
    full_idx = pd.date_range(start=min_date, end=max_date, freq="D", name="date")
    
    daily = daily.set_index("date").reindex(full_idx, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": "date"})
    return daily


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> Tuple[float, float]:
    """Computes MAE and RMSE between actual and predicted vectors."""
    if len(actual) == 0:
        return 0.0, 0.0
    err = actual - predicted
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    return round(mae, 2), round(rmse, 2)


def generate_demand_forecast(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    horizon_days: int = 14,
    test_days: Optional[int] = None,
) -> ForecastResult:
    """
    Executes a chronological train/test split, fits Exponential Smoothing and Naïve baseline,
    evaluates holdout accuracy, and forecasts future periods.
    """
    ts = prepare_regular_time_series(df, product_id)
    n_obs = len(ts)

    # Fallback definition for empty or severely deficient series (< 7 days)
    if n_obs < 7:
        warnings = [f"Insufficient history ({n_obs} days). Minimum 7 days required for forecasting."]
        empty_df = pd.DataFrame(columns=["date", "units_sold"])
        return ForecastResult(
            model_name="Unavailable (Insufficient Data)",
            baseline_name="Unavailable",
            train_start="N/A",
            train_end="N/A",
            test_start="N/A",
            test_end="N/A",
            test_days=0,
            forecast_horizon=horizon_days,
            mae_model=None,
            rmse_model=None,
            mae_baseline=None,
            rmse_baseline=None,
            historical_df=ts,
            test_df=empty_df,
            forecast_df=empty_df,
            warnings=warnings,
            fallback_used=True,
        )

    # Determine chronological holdout window (default: 20% of data or min 7, max 30)
    if test_days is None:
        test_days = max(7, min(30, int(n_obs * 0.20)))
    test_days = min(test_days, n_obs - 5)  # Ensure at least 5 days in train

    train_df = ts.iloc[:-test_days].copy()
    test_df = ts.iloc[-test_days:].copy()

    train_start = train_df["date"].min().strftime("%Y-%m-%d")
    train_end = train_df["date"].max().strftime("%Y-%m-%d")
    test_start = test_df["date"].min().strftime("%Y-%m-%d")
    test_end = test_df["date"].max().strftime("%Y-%m-%d")

    actual_test = test_df["units_sold"].to_numpy(dtype=float)

    # 1. Naïve Baseline: Last observed training value carried forward
    last_train_val = float(train_df["units_sold"].iloc[-1])
    baseline_pred = np.full(shape=test_days, fill_value=last_train_val)
    mae_baseline, rmse_baseline = calculate_metrics(actual_test, baseline_pred)
    baseline_name = f"Naïve Baseline (Last Observed = {int(last_train_val)} units)"

    # 2. Statistical Model: Exponential Smoothing with additive trend
    model_name = "Holt Exponential Smoothing (Additive Trend)"
    warnings: List[str] = []
    fallback_used = False
    model_pred = None

    if len(train_df) < MIN_HISTORY_FOR_MODEL:
        fallback_used = True
        warnings.append(
            f"Training series has {len(train_df)} observations (< {MIN_HISTORY_FOR_MODEL} threshold). "
            "Falling back to Naïve Baseline."
        )
        model_name = baseline_name
        model_pred = baseline_pred.copy()
        mae_model, rmse_model = mae_baseline, rmse_baseline
    else:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            # Try fitting Holt's linear trend model
            train_series = train_df["units_sold"].astype(float)
            # Add small epsilon if constant 0
            if train_series.std() == 0:
                train_series = train_series + 0.001

            hw_model = ExponentialSmoothing(
                train_series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)

            raw_pred = hw_model.forecast(test_days).to_numpy()
            model_pred = np.clip(np.round(raw_pred), a_min=0, a_max=None)
            mae_model, rmse_model = calculate_metrics(actual_test, model_pred)

        except Exception as ex:
            fallback_used = True
            warnings.append(
                f"Statistical model convergence failed ({type(ex).__name__}). "
                "Fell back to Naïve Baseline."
            )
            model_name = f"Fallback ({baseline_name})"
            model_pred = baseline_pred.copy()
            mae_model, rmse_model = mae_baseline, rmse_baseline

    # Build evaluation DataFrame
    eval_df = test_df.copy()
    eval_df["actual"] = eval_df["units_sold"]
    eval_df["baseline_pred"] = baseline_pred
    eval_df["model_pred"] = model_pred

    # 3. Fit on full available history and forecast future horizon
    future_dates = pd.date_range(
        start=ts["date"].max() + pd.Timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )

    if not fallback_used:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            full_series = ts["units_sold"].astype(float)
            if full_series.std() == 0:
                full_series = full_series + 0.001
            final_fit = ExponentialSmoothing(
                full_series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)
            future_raw = final_fit.forecast(horizon_days).to_numpy()
            future_forecast = np.clip(np.round(future_raw), a_min=0, a_max=None)
        except Exception:
            # Fallback for future projection
            last_val = float(ts["units_sold"].iloc[-1])
            future_forecast = np.full(shape=horizon_days, fill_value=last_val)
    else:
        last_val = float(ts["units_sold"].iloc[-1])
        future_forecast = np.full(shape=horizon_days, fill_value=last_val)

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "forecast": future_forecast,
    })

    return ForecastResult(
        model_name=model_name,
        baseline_name=baseline_name,
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        test_days=test_days,
        forecast_horizon=horizon_days,
        mae_model=mae_model,
        rmse_model=rmse_model,
        mae_baseline=mae_baseline,
        rmse_baseline=rmse_baseline,
        historical_df=ts,
        test_df=eval_df,
        forecast_df=forecast_df,
        warnings=warnings,
        fallback_used=fallback_used,
    )
