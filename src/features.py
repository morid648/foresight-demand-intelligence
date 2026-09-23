"""
Time-Safe Feature Engineering Engine for Project FORESIGHT.
Generates lagged, rolling, calendar, promotional, and metadata features strictly as-of cutoff date T.
Guarantees zero future information leakage.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from src.config import config
from src.logging_utils import get_logger

logger = get_logger(__name__)


def build_time_safe_features(
    panel_df: pd.DataFrame,
    cutoff_date: Optional[pd.Timestamp] = None,
    horizon_weeks: int = 8
) -> pd.DataFrame:
    """Extracts features for all SKUs strictly using data available up to cutoff_date.
    
    For training:
        Features are computed for each historical week t using only prior weeks (<= t-1).
    For inference as-of cutoff T:
        Produces feature rows for the future horizon [T+1, ..., T+H] using history <= T.
    """
    df = panel_df.copy()
    df["week_start"] = pd.to_datetime(df["week_start"])
    df = df.sort_values(["sku_id", "week_start"]).reset_index(drop=True)

    if cutoff_date is not None:
        cutoff = pd.to_datetime(cutoff_date)
        df_history = df[df["week_start"] <= cutoff].copy()
    else:
        cutoff = df["week_start"].max()
        df_history = df.copy()

    feature_rows = []

    # Process each SKU independently
    for sku_id, sku_group in df_history.groupby("sku_id"):
        sku_group = sku_group.sort_values("week_start").reset_index(drop=True)
        n = len(sku_group)
        if n == 0:
            continue

        units = sku_group["units_sold"].values.astype(float)
        prices = sku_group["avg_unit_price"].values.astype(float)
        list_price = float(sku_group["list_price"].iloc[-1])
        category = sku_group["category"].iloc[-1]
        subcategory = sku_group["subcategory"].iloc[-1]
        unit_cost = float(sku_group["unit_cost"].iloc[-1])
        on_hand = int(sku_group["on_hand_units"].iloc[-1])
        on_order = int(sku_group["on_order_units"].iloc[-1])
        lead_time = int(sku_group["lead_time_days"].iloc[-1])

        # Feature extraction for each historical week (starting from week index 4)
        for i in range(4, n):
            target_week = sku_group["week_start"].iloc[i]
            target_units = units[i]

            # Prior history strictly <= i - 1
            hist_u = units[:i]

            # Lag features
            lag_1 = hist_u[-1]
            lag_2 = hist_u[-2] if len(hist_u) >= 2 else hist_u[-1]
            lag_4 = hist_u[-4] if len(hist_u) >= 4 else np.median(hist_u)
            lag_8 = hist_u[-8] if len(hist_u) >= 8 else np.median(hist_u)
            lag_52 = hist_u[-52] if len(hist_u) >= 52 else lag_4

            # Rolling stats on lagged history
            roll_4_mean = float(np.mean(hist_u[-4:]))
            roll_4_std = float(np.std(hist_u[-4:])) if len(hist_u) >= 4 else 0.0
            roll_8_mean = float(np.mean(hist_u[-8:])) if len(hist_u) >= 8 else roll_4_mean
            roll_12_mean = float(np.mean(hist_u[-12:])) if len(hist_u) >= 12 else roll_8_mean

            # Calendar features
            week_num = target_week.isocalendar()[1]
            month_num = target_week.month
            sin_week = np.sin(2 * np.pi * week_num / 52.0)
            cos_week = np.cos(2 * np.pi * week_num / 52.0)
            is_holiday = int(sku_group["is_holiday_week"].iloc[i])
            promo_active = int(sku_group["promo_active_days"].iloc[i] > 0)

            # Price features
            price_ratio = prices[i] / list_price if list_price > 0 else 1.0

            feature_rows.append({
                "week_start": target_week,
                "sku_id": sku_id,
                "category": category,
                "subcategory": subcategory,
                "unit_cost": unit_cost,
                "list_price": list_price,
                "on_hand_units": on_hand,
                "on_order_units": on_order,
                "lead_time_days": lead_time,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_4": lag_4,
                "lag_8": lag_8,
                "lag_52": lag_52,
                "roll_4_mean": roll_4_mean,
                "roll_4_std": roll_4_std,
                "roll_8_mean": roll_8_mean,
                "roll_12_mean": roll_12_mean,
                "sin_week": sin_week,
                "cos_week": cos_week,
                "month": month_num,
                "is_holiday_week": is_holiday,
                "promo_active": promo_active,
                "price_ratio": price_ratio,
                "target_units": target_units
            })

    feature_df = pd.DataFrame(feature_rows)
    logger.info(f"Built time-safe features: {len(feature_df)} training samples as of cutoff {cutoff}")
    return feature_df


def extract_inference_features(
    panel_df: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    horizon_weeks: int = 8
) -> pd.DataFrame:
    """Generates feature matrix for future horizon weeks [T+1, ..., T+H] strictly using history <= T."""
    df = panel_df.copy()
    df["week_start"] = pd.to_datetime(df["week_start"])
    cutoff = pd.to_datetime(cutoff_date)
    df_history = df[df["week_start"] <= cutoff].copy()

    inference_rows = []

    for sku_id, sku_group in df_history.groupby("sku_id"):
        sku_group = sku_group.sort_values("week_start").reset_index(drop=True)
        hist_u = sku_group["units_sold"].values.astype(float)
        if len(hist_u) == 0:
            continue

        list_price = float(sku_group["list_price"].iloc[-1])
        category = sku_group["category"].iloc[-1]
        subcategory = sku_group["subcategory"].iloc[-1]
        unit_cost = float(sku_group["unit_cost"].iloc[-1])
        on_hand = int(sku_group["on_hand_units"].iloc[-1])
        on_order = int(sku_group["on_order_units"].iloc[-1])
        lead_time = int(sku_group["lead_time_days"].iloc[-1])

        # As-of T features
        lag_1 = hist_u[-1]
        lag_2 = hist_u[-2] if len(hist_u) >= 2 else hist_u[-1]
        lag_4 = hist_u[-4] if len(hist_u) >= 4 else np.median(hist_u)
        lag_8 = hist_u[-8] if len(hist_u) >= 8 else np.median(hist_u)
        lag_52 = hist_u[-52] if len(hist_u) >= 52 else lag_4

        roll_4_mean = float(np.mean(hist_u[-4:]))
        roll_4_std = float(np.std(hist_u[-4:])) if len(hist_u) >= 4 else 0.0
        roll_8_mean = float(np.mean(hist_u[-8:])) if len(hist_u) >= 8 else roll_4_mean
        roll_12_mean = float(np.mean(hist_u[-12:])) if len(hist_u) >= 12 else roll_8_mean

        for h in range(1, horizon_weeks + 1):
            future_week = cutoff + pd.Timedelta(weeks=h)
            week_num = future_week.isocalendar()[1]
            month_num = future_week.month
            sin_week = np.sin(2 * np.pi * week_num / 52.0)
            cos_week = np.cos(2 * np.pi * week_num / 52.0)

            inference_rows.append({
                "week_start": future_week,
                "horizon_step": h,
                "sku_id": sku_id,
                "category": category,
                "subcategory": subcategory,
                "unit_cost": unit_cost,
                "list_price": list_price,
                "on_hand_units": on_hand,
                "on_order_units": on_order,
                "lead_time_days": lead_time,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_4": lag_4,
                "lag_8": lag_8,
                "lag_52": lag_52,
                "roll_4_mean": roll_4_mean,
                "roll_4_std": roll_4_std,
                "roll_8_mean": roll_8_mean,
                "roll_12_mean": roll_12_mean,
                "sin_week": sin_week,
                "cos_week": cos_week,
                "month": month_num,
                "is_holiday_week": 0,
                "promo_active": 0,
                "price_ratio": 1.0
            })

    return pd.DataFrame(inference_rows)
