"""
Unit tests for rolling-origin cross-validation splitter and model evaluation.
"""

import pytest
import pandas as pd
import numpy as np
from src.backtest import generate_rolling_cv_cutoffs, run_rolling_backtest


def test_rolling_cv_cutoffs_ordering():
    dates = pd.date_range("2024-01-01", periods=60, freq="W")
    panel = pd.DataFrame({
        "sku_id": ["SKU1"] * 60,
        "week_start": dates,
        "units_sold": [10] * 60
    })

    cutoffs = generate_rolling_cv_cutoffs(panel, n_folds=3, horizon_weeks=8, step_weeks=4)
    assert len(cutoffs) == 3
    # Strict temporal ascending order
    assert cutoffs[0] < cutoffs[1] < cutoffs[2]


def test_rolling_backtest_execution():
    dates = pd.date_range("2024-01-01", periods=60, freq="W")
    panel = pd.DataFrame({
        "sku_id": ["SKU_TEST"] * 60,
        "category": ["Bath"] * 60,
        "subcategory": ["Towel"] * 60,
        "unit_cost": [40.0] * 60,
        "list_price": [100.0] * 60,
        "on_hand_units": [50] * 60,
        "on_order_units": [20] * 60,
        "lead_time_days": [14] * 60,
        "week_start": dates,
        "units_sold": [10 + (i % 4) for i in range(60)],
        "avg_unit_price": [95.0] * 60,
        "is_holiday_week": [0] * 60,
        "promo_active_days": [0] * 60
    })

    metrics, winner, estimator = run_rolling_backtest(panel, n_folds=2, horizon_weeks=4)
    assert "winner" in metrics
    assert "baseline_wape" in metrics
    assert metrics["winner"] in ["Seasonal_Naive", "Ridge_Linear", "HistGradientBoosting", "RandomForest"]
