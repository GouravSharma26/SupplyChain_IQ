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


def calculate_wape(actual: np.ndarray, predicted: np.ndarray) -> Optional[float]:
    """
    Computes Weighted Absolute Percentage Error (WAPE = sum(|actual - predicted|) / sum(actual)).
    Avoids MAPE's division-by-zero vulnerability on zero-demand days.
    """
    if len(actual) == 0:
        return None
    actual_sum = float(np.sum(np.abs(actual)))
    err_sum = float(np.sum(np.abs(actual - predicted)))
    if actual_sum == 0.0:
        return 0.0 if err_sum == 0.0 else None
    return round((err_sum / actual_sum) * 100.0, 2)


def seasonal_naive_forecast(train_series: np.ndarray, horizon: int, season_length: int = 7) -> np.ndarray:
    """
    Generates seasonal naïve predictions by repeating the last observed seasonal cycle.
    Falls back to simple last-value naïve if history is shorter than season_length.
    """
    n = len(train_series)
    if n == 0:
        return np.zeros(horizon)
    if n < season_length:
        return np.full(horizon, fill_value=float(train_series[-1]))

    cycle = train_series[-season_length:]
    repeats = int(np.ceil(horizon / season_length))
    return np.tile(cycle, repeats)[:horizon]


@dataclass
class RollingOriginFold:
    """Out-of-sample metrics for a single rolling-origin cutoff window."""
    fold_index: int
    cutoff_date: str
    train_days: int
    test_days: int
    naive_mae: float
    naive_rmse: float
    naive_wape: Optional[float]
    seasonal_mae: float
    seasonal_rmse: float
    seasonal_wape: Optional[float]
    holt_mae: float
    holt_rmse: float
    holt_wape: Optional[float]


@dataclass
class RollingOriginReport:
    """Multi-fold rolling origin evaluation benchmark report."""
    product_id: str
    total_folds: int
    horizon_days: int
    step_days: int
    avg_naive_mae: float
    avg_naive_rmse: float
    avg_naive_wape: float
    avg_seasonal_mae: float
    avg_seasonal_rmse: float
    avg_seasonal_wape: float
    avg_holt_mae: float
    avg_holt_rmse: float
    avg_holt_wape: float
    best_model: str
    folds: List[RollingOriginFold] = field(default_factory=list)
    notes: str = ""

    def to_summary_table(self) -> pd.DataFrame:
        """Converts model benchmark comparison into a presentable comparison table."""
        return pd.DataFrame([
            {
                "Model / Baseline": "Naïve Baseline (Last Value)",
                "Avg MAE": self.avg_naive_mae,
                "Avg RMSE": self.avg_naive_rmse,
                "Avg WAPE (%)": f"{self.avg_naive_wape:.1f}%",
                "Folds Evaluated": self.total_folds,
            },
            {
                "Model / Baseline": "Seasonal Naïve (7-day lag)",
                "Avg MAE": self.avg_seasonal_mae,
                "Avg RMSE": self.avg_seasonal_rmse,
                "Avg WAPE (%)": f"{self.avg_seasonal_wape:.1f}%",
                "Folds Evaluated": self.total_folds,
            },
            {
                "Model / Baseline": "Holt Exponential Smoothing",
                "Avg MAE": self.avg_holt_mae,
                "Avg RMSE": self.avg_holt_rmse,
                "Avg WAPE (%)": f"{self.avg_holt_wape:.1f}%",
                "Folds Evaluated": self.total_folds,
            },
        ])


def evaluate_rolling_origin_backtest(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    initial_train_days: int = 45,
    horizon_days: int = 14,
    step_days: int = 14,
) -> RollingOriginReport:
    """
    Executes expanding-window rolling origin backtesting across sequential chronological folds.
    Evaluates Naïve, Seasonal Naïve, and Holt Exponential Smoothing without data leakage.
    """
    ts = prepare_regular_time_series(df, product_id)
    n_obs = len(ts)
    p_label = product_id if product_id is not None else "ALL"

    if n_obs < (initial_train_days + horizon_days):
        return RollingOriginReport(
            product_id=p_label,
            total_folds=0,
            horizon_days=horizon_days,
            step_days=step_days,
            avg_naive_mae=0.0,
            avg_naive_rmse=0.0,
            avg_naive_wape=0.0,
            avg_seasonal_mae=0.0,
            avg_seasonal_rmse=0.0,
            avg_seasonal_wape=0.0,
            avg_holt_mae=0.0,
            avg_holt_rmse=0.0,
            avg_holt_wape=0.0,
            best_model="Insufficient History",
            notes=f"Series has {n_obs} days; requires at least {initial_train_days + horizon_days} days for rolling backtest.",
        )

    folds: List[RollingOriginFold] = []
    series_values = ts["units_sold"].to_numpy().astype(float)
    dates = ts["date"].to_numpy()

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    cutoff_idx = initial_train_days
    fold_counter = 1

    while (cutoff_idx + horizon_days) <= n_obs:
        train_y = series_values[:cutoff_idx]
        test_y = series_values[cutoff_idx : cutoff_idx + horizon_days]
        cutoff_date_str = str(pd.to_datetime(dates[cutoff_idx - 1]).strftime("%Y-%m-%d"))

        # 1. Naïve Baseline
        pred_naive = np.full(horizon_days, fill_value=float(train_y[-1]))
        mae_n, rmse_n = calculate_metrics(test_y, pred_naive)
        wape_n = calculate_wape(test_y, pred_naive) or 0.0

        # 2. Seasonal Naïve (7-day cycle)
        pred_seasonal = seasonal_naive_forecast(train_y, horizon=horizon_days, season_length=7)
        mae_s, rmse_s = calculate_metrics(test_y, pred_seasonal)
        wape_s = calculate_wape(test_y, pred_seasonal) or 0.0

        # 3. Holt Exponential Smoothing
        try:
            fit_series = train_y if np.std(train_y) > 0 else train_y + 0.001
            model_fit = ExponentialSmoothing(
                fit_series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)
            raw_holt = model_fit.forecast(horizon_days)
            pred_holt = np.clip(np.round(raw_holt), a_min=0, a_max=None)
        except Exception:
            pred_holt = pred_naive.copy()

        mae_h, rmse_h = calculate_metrics(test_y, pred_holt)
        wape_h = calculate_wape(test_y, pred_holt) or 0.0

        folds.append(
            RollingOriginFold(
                fold_index=fold_counter,
                cutoff_date=cutoff_date_str,
                train_days=cutoff_idx,
                test_days=horizon_days,
                naive_mae=mae_n,
                naive_rmse=rmse_n,
                naive_wape=wape_n,
                seasonal_mae=mae_s,
                seasonal_rmse=rmse_s,
                seasonal_wape=wape_s,
                holt_mae=mae_h,
                holt_rmse=rmse_h,
                holt_wape=wape_h,
            )
        )

        fold_counter += 1
        cutoff_idx += step_days

    # Aggregate metrics across all folds
    avg_n_mae = round(float(np.mean([f.naive_mae for f in folds])), 2)
    avg_n_rmse = round(float(np.mean([f.naive_rmse for f in folds])), 2)
    avg_n_wape = round(float(np.mean([f.naive_wape for f in folds if f.naive_wape is not None])), 2)

    avg_s_mae = round(float(np.mean([f.seasonal_mae for f in folds])), 2)
    avg_s_rmse = round(float(np.mean([f.seasonal_rmse for f in folds])), 2)
    avg_s_wape = round(float(np.mean([f.seasonal_wape for f in folds if f.seasonal_wape is not None])), 2)

    avg_h_mae = round(float(np.mean([f.holt_mae for f in folds])), 2)
    avg_h_rmse = round(float(np.mean([f.holt_rmse for f in folds])), 2)
    avg_h_wape = round(float(np.mean([f.holt_wape for f in folds if f.holt_wape is not None])), 2)

    # Determine winning model based on MAE
    model_scores = {
        "Holt Exponential Smoothing": avg_h_mae,
        "Seasonal Naïve (7-day)": avg_s_mae,
        "Naïve Baseline": avg_n_mae,
    }
    best_model = min(model_scores, key=model_scores.get)

    return RollingOriginReport(
        product_id=p_label,
        total_folds=len(folds),
        horizon_days=horizon_days,
        step_days=step_days,
        avg_naive_mae=avg_n_mae,
        avg_naive_rmse=avg_n_rmse,
        avg_naive_wape=avg_n_wape,
        avg_seasonal_mae=avg_s_mae,
        avg_seasonal_rmse=avg_s_rmse,
        avg_seasonal_wape=avg_s_wape,
        avg_holt_mae=avg_h_mae,
        avg_holt_rmse=avg_h_rmse,
        avg_holt_wape=avg_h_wape,
        best_model=best_model,
        folds=folds,
        notes=f"Evaluated across {len(folds)} rolling folds with {horizon_days}-day out-of-sample horizons.",
    )


def benchmark_all_skus(
    df: pd.DataFrame,
    initial_train_days: int = 45,
    horizon_days: int = 14,
    step_days: int = 14,
) -> pd.DataFrame:
    """
    Evaluates rolling origin backtesting across all SKUs, compiling an executive cross-product benchmark.
    Avoids masking individual product forecast difficulties behind aggregate numbers.
    """
    if df.empty or "product_id" not in df.columns:
        return pd.DataFrame()

    unique_products = sorted(df["product_id"].unique())
    results = []

    for p_id in unique_products:
        report = evaluate_rolling_origin_backtest(
            df,
            product_id=p_id,
            initial_train_days=initial_train_days,
            horizon_days=horizon_days,
            step_days=step_days,
        )
        if report.total_folds > 0:
            results.append({
                "product_id": p_id,
                "folds": report.total_folds,
                "naive_mae": report.avg_naive_mae,
                "seasonal_mae": report.avg_seasonal_mae,
                "holt_mae": report.avg_holt_mae,
                "best_model": report.best_model,
                "holt_wape_pct": report.avg_holt_wape,
            })

    return pd.DataFrame(results).reset_index(drop=True)

