"""
Unit tests for data validation, cleaning, and weekly panel pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date
from src.validation import validate_raw_datasets
from src.pipeline import clean_raw_data, build_weekly_panel


@pytest.fixture
def sample_raw_data():
    sales = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02", "2025-01-02", "2025-01-03"],
        "sku_id": ["SKU01", "SKU01", "SKU01", "SKU01"],
        "units_sold": [5, 10, 2, -1],  # Contains negative value & duplicate
        "revenue": [500.0, 1000.0, 200.0, -100.0],
        "unit_price": [100.0, 100.0, 100.0, 100.0],
        "promo_flag": [0, 1, 0, 0]
    })
    sku = pd.DataFrame({
        "sku_id": ["  SKU01  "],  # Leading/trailing whitespace
        "category": ["  Home Decor  "],
        "subcategory": ["Vases"],
        "launch_date": ["2024-01-01"],
        "unit_cost": [40.0],
        "list_price": [100.0]
    })
    cal = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
        "week": [1, 1, 1, 1],
        "month": [1, 1, 1, 1],
        "season": ["Winter", "Winter", "Winter", "Winter"],
        "is_holiday": [1, 0, 0, 0],
        "promo_event": ["New Year", None, None, None]
    })
    inv = pd.DataFrame({
        "date": ["2025-01-03"],
        "sku_id": ["SKU01"],
        "on_hand_units": [50],
        "on_order_units": [20],
        "lead_time_days": [14],
        "reorder_point": [30]
    })
    return sales, sku, cal, inv


def test_validation_profiling(sample_raw_data):
    sales, sku, cal, inv = sample_raw_data
    profile = validate_raw_datasets(sales, sku, cal, inv)
    assert profile["sales_daily"]["row_count"] == 4
    assert profile["sales_daily"]["negative_units_count"] == 1
    assert profile["sales_daily"]["duplicate_daily_sku_records"] == 1


def test_validation_critical_missing_column():
    bad_sales = pd.DataFrame({"sku_id": ["A"], "units_sold": [1]})
    dummy = pd.DataFrame()
    with pytest.raises(ValueError, match="missing required columns"):
        validate_raw_datasets(bad_sales, dummy, dummy, dummy)


def test_deterministic_cleaning_rules(sample_raw_data):
    sales, sku, cal, inv = sample_raw_data
    sales_clean, sku_clean, cal_clean, inv_clean, audit = clean_raw_data(sales, sku, cal, inv)

    # Test CLN-01 (whitespace stripped)
    assert sku_clean["sku_id"].iloc[0] == "SKU01"
    assert sku_clean["category"].iloc[0] == "Home Decor"

    # Test CLN-02 (negative sales corrected)
    assert (sales_clean["units_sold"] >= 0).all()
    assert (sales_clean["revenue"] >= 0).all()

    # Test CLN-03 (duplicates aggregated)
    assert len(sales_clean) == 3  # 4 rows collapsed to 3 unique dates for SKU01
    dup_date_row = sales_clean[sales_clean["date"] == pd.Timestamp("2025-01-02")]
    assert dup_date_row["units_sold"].iloc[0] == 12  # 10 + 2
    assert dup_date_row["promo_flag"].iloc[0] == 1  # max promo flag


def test_weekly_panel_aggregation(sample_raw_data):
    sales, sku, cal, inv = sample_raw_data
    sales_clean, sku_clean, cal_clean, inv_clean, _ = clean_raw_data(sales, sku, cal, inv)
    panel = build_weekly_panel(sales_clean, sku_clean, cal_clean, inv_clean)

    assert len(panel) == 1
    assert panel["units_sold"].iloc[0] == 17  # 5 + 12 + 0
    assert panel["on_hand_units"].iloc[0] == 50
    assert panel["unit_cost"].iloc[0] == 40.0
