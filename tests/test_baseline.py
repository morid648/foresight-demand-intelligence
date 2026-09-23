"""
Unit tests for forecast metrics and Seasonal-Naive baseline forecaster.
"""

import pytest
import numpy as np
import pandas as pd
from src.metrics import calculate_wape, calculate_bias, calculate_mape, evaluate_forecast
from src.baseline import SeasonalNaiveBaseline


def test_wape_exact_calculation():
    y_true = [100, 200, 300, 400]
    y_pred = [110, 190, 310, 380]
    # abs errors: 10 + 10 + 10 + 20 = 50. total actual = 1000. WAPE = 50/1000 = 0.05
    assert calculate_wape(y_true, y_pred) == 0.05


def test_wape_zero_actuals():
    assert calculate_wape([0, 0], [0, 0]) == 0.0
    assert calculate_wape([0, 0], [10, 10]) == 1.0


def test_bias_direction():
    y_true = [100, 100]
    y_pred_over = [120, 120]  # Over-forecast (+40/200 = +0.20)
    y_pred_under = [80, 80]   # Under-forecast (-40/200 = -0.20)

    assert calculate_bias(y_true, y_pred_over) == 0.20
    assert calculate_bias(y_true, y_pred_under) == -0.20


def test_seasonal_naive_with_sufficient_history():
    # 60 weeks of historical data where weeks 1..8 had values 10, 20, 30...
    history_vals = [i % 50 for i in range(60)]
    panel = pd.DataFrame({
        "sku_id": ["SKU_A"] * 60,
        "week_start": pd.date_range("2024-01-01", periods=60, freq="W"),
        "units_sold": history_vals
    })

    model = SeasonalNaiveBaseline(seasonal_period=52)
    model.fit(panel)
    fcst, method = model.predict_sku("SKU_A", horizon=8)

    assert method == "seasonal_52w"
    assert len(fcst) == 8
    # For h=0 (week 61), target lag is 61 - 52 = week 9 (index 8)
    assert fcst[0] == history_vals[60 + 0 - 52]


def test_seasonal_naive_short_history_fallback():
    # Only 10 weeks of history (< 52)
    panel = pd.DataFrame({
        "sku_id": ["SKU_NEW"] * 10,
        "week_start": pd.date_range("2025-01-01", periods=10, freq="W"),
        "units_sold": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
    })

    model = SeasonalNaiveBaseline(seasonal_period=52, fallback_window=8)
    model.fit(panel)
    fcst, method = model.predict_sku("SKU_NEW", horizon=8)

    assert method == "median_fallback"
    assert len(fcst) == 8
    # Last 8 values: 14, 16, 18, 20, 22, 24, 26, 28 -> median = 21.0
    assert fcst[0] == 21.0
