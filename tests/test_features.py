"""
Unit tests for time-safe feature engineering and future perturbation leakage prevention.
"""

import pytest
import pandas as pd
import numpy as np
from src.features import build_time_safe_features, extract_inference_features


def test_no_future_leakage_on_cutoff():
    """Modifying future actuals must have zero effect on features generated as-of historical cutoff."""
    base_panel = pd.DataFrame({
        "sku_id": ["SKU1"] * 20,
        "category": ["Decor"] * 20,
        "subcategory": ["Vase"] * 20,
        "unit_cost": [50.0] * 20,
        "list_price": [120.0] * 20,
        "on_hand_units": [10] * 20,
        "on_order_units": [5] * 20,
        "lead_time_days": [14] * 20,
        "week_start": pd.date_range("2024-01-01", periods=20, freq="W"),
        "units_sold": [10 + i for i in range(20)],
        "avg_unit_price": [100.0] * 20,
        "is_holiday_week": [0] * 20,
        "promo_active_days": [0] * 20
    })

    cutoff = pd.Timestamp("2024-03-01")

    # Features on unperturbed dataset
    feat_original = build_time_safe_features(base_panel, cutoff_date=cutoff)

    # Corrupt/perturb future data after cutoff (e.g. week 15..20 units set to 99999)
    corrupted_panel = base_panel.copy()
    corrupted_panel.loc[corrupted_panel["week_start"] > cutoff, "units_sold"] = 999999

    feat_perturbed = build_time_safe_features(corrupted_panel, cutoff_date=cutoff)

    # Target features as of cutoff must be 100% identical
    pd.testing.assert_frame_equal(feat_original, feat_perturbed)


def test_inference_features_structure():
    panel = pd.DataFrame({
        "sku_id": ["SKU_X"] * 10,
        "category": ["Bath"] * 10,
        "subcategory": ["Towel"] * 10,
        "unit_cost": [100.0] * 10,
        "list_price": [250.0] * 10,
        "on_hand_units": [40] * 10,
        "on_order_units": [10] * 10,
        "lead_time_days": [21] * 10,
        "week_start": pd.date_range("2024-01-01", periods=10, freq="W"),
        "units_sold": [5] * 10,
        "avg_unit_price": [220.0] * 10,
        "is_holiday_week": [0] * 10,
        "promo_active_days": [0] * 10
    })

    cutoff = pd.Timestamp("2024-03-03")
    inf_feat = extract_inference_features(panel, cutoff_date=cutoff, horizon_weeks=8)

    assert len(inf_feat) == 8
    assert inf_feat["horizon_step"].tolist() == list(range(1, 9))
    assert inf_feat["lag_1"].iloc[0] == 5.0
    assert inf_feat["roll_4_mean"].iloc[0] == 5.0
