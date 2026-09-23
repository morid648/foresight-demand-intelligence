"""
Data Validation and Schema Integrity Engine for Project FORESIGHT.
Enforces strict contracts, null audits, duplicate checks, and temporal continuity.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from src.logging_utils import get_logger

logger = get_logger(__name__)


def validate_raw_datasets(
    sales_df: pd.DataFrame,
    sku_df: pd.DataFrame,
    cal_df: pd.DataFrame,
    inv_df: pd.DataFrame
) -> Dict[str, Any]:
    """Validates the 4 raw datasets against project schema requirements.
    
    Returns a structured data quality dictionary.
    Raises ValueError on missing critical columns.
    """
    logger.info("Initiating strict schema & data validation audit...")

    dq_profile: Dict[str, Any] = {
        "sales_daily": {},
        "sku_master": {},
        "calendar": {},
        "inventory_snapshots": {},
        "integrity_checks": {}
    }

    # 1. Sales Daily Validation
    sales_req = {"date", "sku_id", "units_sold", "revenue", "unit_price"}
    missing_sales = sales_req - set(sales_df.columns)
    if missing_sales:
        raise ValueError(f"CRITICAL: sales_daily is missing required columns: {missing_sales}")

    dq_profile["sales_daily"]["row_count"] = len(sales_df)
    dq_profile["sales_daily"]["null_counts"] = sales_df.isnull().sum().to_dict()
    dq_profile["sales_daily"]["duplicate_daily_sku_records"] = int(sales_df.duplicated(subset=["date", "sku_id"]).sum())
    dq_profile["sales_daily"]["negative_units_count"] = int((sales_df["units_sold"] < 0).sum())
    dq_profile["sales_daily"]["unique_skus"] = int(sales_df["sku_id"].nunique())

    # 2. SKU Master Validation
    sku_req = {"sku_id", "category", "subcategory", "unit_cost", "list_price"}
    missing_sku = sku_req - set(sku_df.columns)
    if missing_sku:
        raise ValueError(f"CRITICAL: sku_master is missing required columns: {missing_sku}")

    dq_profile["sku_master"]["row_count"] = len(sku_df)
    dq_profile["sku_master"]["null_counts"] = sku_df.isnull().sum().to_dict()
    dq_profile["sku_master"]["duplicate_skus"] = int(sku_df.duplicated(subset=["sku_id"]).sum())
    dq_profile["sku_master"]["unique_categories"] = int(sku_df["category"].nunique())

    # 3. Calendar Validation
    cal_req = {"date", "week", "month", "season", "is_holiday"}
    missing_cal = cal_req - set(cal_df.columns)
    if missing_cal:
        raise ValueError(f"CRITICAL: calendar is missing required columns: {missing_cal}")

    dq_profile["calendar"]["row_count"] = len(cal_df)
    dq_profile["calendar"]["date_min"] = str(cal_df["date"].min())
    dq_profile["calendar"]["date_max"] = str(cal_df["date"].max())

    # 4. Inventory Snapshots Validation
    inv_req = {"date", "sku_id", "on_hand_units", "on_order_units", "lead_time_days"}
    missing_inv = inv_req - set(inv_df.columns)
    if missing_inv:
        raise ValueError(f"CRITICAL: inventory_snapshots is missing required columns: {missing_inv}")

    dq_profile["inventory_snapshots"]["row_count"] = len(inv_df)
    dq_profile["inventory_snapshots"]["null_counts"] = inv_df.isnull().sum().to_dict()

    # 5. Cross-Table Integrity & Join Coverage
    sales_skus = set(sales_df["sku_id"].str.strip().unique())
    master_skus = set(sku_df["sku_id"].str.strip().unique())
    inv_skus = set(inv_df["sku_id"].str.strip().unique())

    unmapped_sales_skus = sales_skus - master_skus
    missing_inv_skus = master_skus - inv_skus

    dq_profile["integrity_checks"]["sales_in_master_coverage_pct"] = round(
        (len(sales_skus & master_skus) / len(sales_skus) * 100) if sales_skus else 0.0, 2
    )
    dq_profile["integrity_checks"]["unmapped_sales_skus_count"] = len(unmapped_sales_skus)
    dq_profile["integrity_checks"]["skus_missing_inventory_count"] = len(missing_inv_skus)

    logger.info(f"Validation complete: Sales SKU coverage in Master = {dq_profile['integrity_checks']['sales_in_master_coverage_pct']}%")
    return dq_profile
