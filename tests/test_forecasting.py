"""
Unit tests for forecasting, chronological holdout evaluation, and baseline benchmarks.
"""

import numpy as np
import pandas as pd
import pytest

from supplychain_iq.forecasting import (
    calculate_metrics,
    calculate_wape,
    seasonal_naive_forecast,
    evaluate_rolling_origin_backtest,
    benchmark_all_skus,
    generate_demand_forecast,
    prepare_regular_time_series,
)


def test_calculate_metrics():
    actual = np.array([10.0, 20.0, 30.0])
    pred = np.array([12.0, 18.0, 35.0])
    # abs err: [2, 2, 5] -> MAE = 9 / 3 = 3.0
    # sq err: [4, 4, 25] = 33 -> RMSE = sqrt(11) = 3.32
    mae, rmse = calculate_metrics(actual, pred)
    assert mae == 3.0
    assert rmse == 3.32


def test_short_history_fallback():
    # Only 10 days of data (< 28 days threshold for full statistical model)
    dates = pd.date_range("2026-05-01", periods=10, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "product_id": ["P1"] * 10,
        "units_sold": [10, 12, 14, 11, 13, 15, 12, 14, 16, 15],
    })

    result = generate_demand_forecast(df, product_id="P1", horizon_days=7, test_days=3)
    assert result.fallback_used is True
    assert len(result.warnings) > 0
    assert "Naïve Baseline" in result.model_name
    assert len(result.forecast_df) == 7
    assert (result.forecast_df["forecast"] >= 0).all()


def test_severely_deficient_history_returns_none_metrics():
    # Only 4 days of data (< 7 days threshold for any evaluation split)
    dates = pd.date_range("2026-05-01", periods=4, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "product_id": ["P1"] * 4,
        "units_sold": [10, 12, 14, 11],
    })

    result = generate_demand_forecast(df, product_id="P1", horizon_days=7)
    assert result.fallback_used is True
    assert "Insufficient history" in result.warnings[0]
    # Metrics must be None, NOT 0.0, to prevent misleading perception of perfect accuracy
    assert result.mae_model is None
    assert result.rmse_model is None
    assert result.mae_baseline is None
    assert result.rmse_baseline is None


def test_chronological_holdout_and_evaluation():
    # 60 days of data (> 28 days threshold)
    dates = pd.date_range("2026-05-01", periods=60, freq="D")
    # Linear trend + slight noise
    sales = [20 + i * 0.5 + (i % 3) for i in range(60)]
    df = pd.DataFrame({
        "date": dates,
        "product_id": ["P1"] * 60,
        "units_sold": sales,
    })

    result = generate_demand_forecast(df, product_id="P1", horizon_days=14, test_days=12)
    
    # Check chronological order: test starts right after train
    assert pd.to_datetime(result.test_start) > pd.to_datetime(result.train_end)
    assert result.test_days == 12
    assert result.forecast_horizon == 14

    # Ensure evaluation metrics are nonnegative floats
    assert result.mae_model >= 0.0
    assert result.rmse_model >= 0.0
    assert result.mae_baseline >= 0.0
    assert result.rmse_baseline >= 0.0

    # Ensure out-of-sample forecast has 14 days and starts after history ends
    assert len(result.forecast_df) == 14
    assert result.forecast_df["date"].min() > pd.to_datetime(result.test_end)
    assert (result.forecast_df["forecast"] >= 0).all()


def test_calculate_wape():
    actual = np.array([10.0, 0.0, 30.0])  # Contains intermittent zero demand
    pred = np.array([12.0, 2.0, 28.0])
    # |10-12| + |0-2| + |30-28| = 2 + 2 + 2 = 6.0
    # sum(actual) = 40.0
    # WAPE = (6.0 / 40.0) * 100 = 15.0%
    wape = calculate_wape(actual, pred)
    assert wape == 15.0


def test_wape_undefined_when_zero_actual_with_nonzero_error():
    """Verify that WAPE returns None when holdout demand is zero but prediction error is nonzero."""
    actual = np.array([0.0, 0.0, 0.0, 0.0])
    pred = np.array([10.0, 15.0, 5.0, 8.0])

    # sum(actual) == 0.0, sum(|actual - pred|) == 38.0
    wape = calculate_wape(actual, pred)
    # Must preserve None and not be coerced to 0.0
    assert wape is None


def test_wape_zero_when_both_actual_and_error_zero():
    """Verify that WAPE returns 0.0 when both actual demand and predicted error are zero."""
    actual = np.array([0.0, 0.0, 0.0])
    pred = np.array([0.0, 0.0, 0.0])

    wape = calculate_wape(actual, pred)
    assert wape == 0.0


def test_rolling_origin_preserves_none_and_excludes_from_aggregate():
    """
    Regression test proving that undefined WAPE in a holdout fold is preserved as None
    and NOT turned into 0.0 or included as a perfect score in aggregate comparisons.
    """
    dates = pd.date_range("2026-01-01", periods=75, freq="D")
    sales = [10.0] * 45 + [0.0] * 14 + [10.0] * 16  # Fold 1 holdout (idx 45..58) has 0 actual demand
    df = pd.DataFrame({"date": dates, "product_id": ["SKU-ZERO"] * 75, "units_sold": sales})

    report = evaluate_rolling_origin_backtest(
        df,
        product_id="SKU-ZERO",
        initial_train_days=45,
        horizon_days=14,
        step_days=14,
    )

    assert report.total_folds >= 2
    fold1 = report.folds[0]
    fold2 = report.folds[1]

    # Fold 1 has actual holdout demand == 0.0 but pred_naive carried forward == 10.0
    assert fold1.naive_wape is None

    # Fold 2 has actual demand == 140.0, pred_naive carried forward == 0.0, so error == 140.0 -> WAPE == 100.0%
    assert fold2.naive_wape == 100.0

    # Aggregate avg_naive_wape MUST be 100.0%, NOT (0.0 + 100.0) / 2 = 50.0%
    assert report.avg_naive_wape == 100.0



def test_seasonal_naive_forecast():
    # 7-day pattern
    cycle = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0])
    train = np.tile(cycle, 3)  # 21 days
    pred = seasonal_naive_forecast(train, horizon=14, season_length=7)
    assert len(pred) == 14
    assert np.array_equal(pred[:7], cycle)
    assert np.array_equal(pred[7:], cycle)


def test_evaluate_rolling_origin_backtest():
    dates = pd.date_range("2026-05-01", periods=90, freq="D")
    sales = [20.0 + (i % 7) * 3.0 for i in range(90)]
    df = pd.DataFrame({
        "date": dates,
        "product_id": ["SKU-ROLL"] * 90,
        "units_sold": sales,
    })

    report = evaluate_rolling_origin_backtest(
        df, product_id="SKU-ROLL", initial_train_days=45, horizon_days=14, step_days=14
    )
    assert report.total_folds >= 2
    assert report.avg_naive_mae >= 0.0
    assert report.avg_seasonal_mae >= 0.0
    assert report.avg_holt_mae >= 0.0
    assert report.best_model in [
        "Holt Exponential Smoothing",
        "Seasonal Naïve (7-day)",
        "Naïve Baseline",
    ]

    summary_table = report.to_summary_table()
    assert len(summary_table) == 3
    assert "Avg WAPE (%)" in summary_table.columns


def test_benchmark_all_skus():
    dates = pd.date_range("2026-05-01", periods=90, freq="D")
    df1 = pd.DataFrame({"date": dates, "product_id": ["SKU-1"] * 90, "units_sold": [15] * 90})
    df2 = pd.DataFrame({"date": dates, "product_id": ["SKU-2"] * 90, "units_sold": [25] * 90})
    df = pd.concat([df1, df2], ignore_index=True)

    benchmark_df = benchmark_all_skus(df, initial_train_days=45, horizon_days=14, step_days=14)
    assert len(benchmark_df) == 2
    assert "product_id" in benchmark_df.columns
    assert "best_model" in benchmark_df.columns

