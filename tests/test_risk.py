"""
Unit tests for inventory risk scoring, 4-quadrant action logic, and financial calculations.
"""

import pytest
import numpy as np
import pandas as pd
from src.risk import compute_sku_risk_profile
from src.impact import calculate_sales_at_risk_inr, calculate_capital_locked_inr


def test_reorder_now_quadrant():
    # Low stock on hand (5), zero on order, high lead time demand (30)
    weekly_fcst = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
    profile = compute_sku_risk_profile(
        sku_id="SKU_REORDER",
        category="Bedding",
        subcategory="Duvets",
        weekly_forecast=weekly_fcst,
        on_hand_units=5,
        on_order_units=0,
        lead_time_days=21,  # 3 weeks -> LT demand = 30
        unit_cost=1000.0,
        unit_price=2500.0,
        historical_weekly_std=4.0
    )

    assert profile["action"] == "REORDER NOW"
    assert profile["stockout_gap_units"] > 0
    assert profile["sales_at_risk_inr"] > 0
    assert profile["overstock_excess_units"] == 0.0


def test_markdown_clear_quadrant():
    # Massive stock on hand (500), low demand (2/week -> 12-week forward demand = 24)
    weekly_fcst = np.array([2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0])
    profile = compute_sku_risk_profile(
        sku_id="SKU_OVERSTOCK",
        category="Decor",
        subcategory="Candles",
        weekly_forecast=weekly_fcst,
        on_hand_units=500,
        on_order_units=0,
        lead_time_days=14,
        unit_cost=200.0,
        unit_price=600.0,
        historical_weekly_std=1.0
    )

    assert profile["action"] == "MARKDOWN / CLEAR"
    assert profile["overstock_excess_units"] > 400
    assert profile["capital_locked_inr"] > 80000.0
    assert profile["stockout_gap_units"] == 0.0


def test_healthy_quadrant():
    # Balanced stock: on-hand=40, LT demand=20, 12-week demand=120
    weekly_fcst = np.array([10.0] * 8)
    profile = compute_sku_risk_profile(
        sku_id="SKU_HEALTHY",
        category="Kitchen",
        subcategory="Dinnerware",
        weekly_forecast=weekly_fcst,
        on_hand_units=40,
        on_order_units=20,
        lead_time_days=14,  # LT demand = 20
        unit_cost=500.0,
        unit_price=1200.0,
        historical_weekly_std=2.0
    )

    assert profile["action"] == "HEALTHY"
    assert profile["stockout_gap_units"] == 0.0
    assert profile["overstock_excess_units"] == 0.0


def test_financial_impact_arithmetic():
    assert calculate_sales_at_risk_inr(15, 1000.0) == 15000.0
    assert calculate_sales_at_risk_inr(0, 1000.0) == 0.0
    assert calculate_capital_locked_inr(50, 400.0) == 20000.0
