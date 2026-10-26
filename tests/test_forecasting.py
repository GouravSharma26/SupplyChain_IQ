"""
Unit tests for forecasting, chronological holdout evaluation, and baseline benchmarks.
"""

import numpy as np
import pandas as pd
import pytest

from supplychain_iq.forecasting import (
    calculate_metrics,
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
