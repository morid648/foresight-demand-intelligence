"""
Inventory Risk Scoring and Decision Action Engine for Project FORESIGHT.
Computes lead-time demand, stockout gaps, forward overstock accumulation,
and classifies each SKU into one of four operational action quadrants.
"""

from typing import Dict, Any, List, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import config
from src.logging_utils import get_logger
from src.impact import calculate_sales_at_risk_inr, calculate_capital_locked_inr
from src.io import ensure_dir, save_dataframe

logger = get_logger(__name__)


def compute_sku_risk_profile(
    sku_id: str,
    category: str,
    subcategory: str,
    weekly_forecast: np.ndarray,
    on_hand_units: int,
    on_order_units: int,
    lead_time_days: int,
    unit_cost: float,
    unit_price: float,
    historical_weekly_std: float = 5.0
) -> Dict[str, Any]:
    """Computes transparent risk metrics, action quadrant, and financial impact for a single SKU."""
    fcst = np.asarray(weekly_forecast, dtype=float)
    horizon_weeks = len(fcst)
    lead_time_weeks = max(1.0, lead_time_days / 7.0)

    # 1. Lead-Time Demand Calculation
    full_weeks_lead = int(np.floor(lead_time_weeks))
    partial_fraction = lead_time_weeks - full_weeks_lead

    lt_demand_int = np.sum(fcst[:min(horizon_weeks, full_weeks_lead)])
    if full_weeks_lead < horizon_weeks and partial_fraction > 0:
        lt_demand_partial = fcst[full_weeks_lead] * partial_fraction
    else:
        lt_demand_partial = 0.0

    lead_time_demand = float(lt_demand_int + lt_demand_partial)
    available_stock = float(on_hand_units + on_order_units)

    # 2. Safety Buffer Calculation (Z * sigma * sqrt(L))
    safety_stock = float(round(config.SAFETY_STOCK_Z * historical_weekly_std * np.sqrt(lead_time_weeks), 1))
    reorder_level = lead_time_demand + safety_stock

    # 3. Stockout Risk Logic
    stockout_gap = max(0.0, float(reorder_level - available_stock))
    stockout_risk_score = float(np.clip(stockout_gap / (reorder_level + 1e-5), 0.0, 1.0))

    # 4. Overstock Forward Horizon Logic (Overstock Horizon = 12 weeks)
    overstock_window = config.OVERSTOCK_HORIZON_WEEKS
    avg_weekly_fcst = float(np.mean(fcst)) if len(fcst) > 0 else 1.0
    forward_demand = avg_weekly_fcst * overstock_window

    excess_units = max(0.0, float(available_stock - forward_demand - safety_stock))
    overstock_risk_score = float(np.clip(excess_units / (forward_demand + 1e-5), 0.0, 1.0))

    # 5. Financial Exposure Calculations
    sales_at_risk = calculate_sales_at_risk_inr(stockout_gap, unit_price)
    capital_locked = calculate_capital_locked_inr(excess_units, unit_cost)

    # 6. Four-Quadrant Operational Action Classification
    is_high_stockout = stockout_risk_score >= config.HIGH_STOCKOUT_RISK_THRESHOLD
    is_high_overstock = overstock_risk_score >= config.HIGH_OVERSTOCK_RISK_THRESHOLD

    if is_high_stockout and not is_high_overstock:
        action = "REORDER NOW"
        rationale = (f"Projected available stock ({int(available_stock)}) is below reorder level ({int(reorder_level)}) "
                     f"across {lead_time_days}d lead time. Gap of {int(stockout_gap)} units.")
    elif not is_high_stockout and is_high_overstock:
        action = "MARKDOWN / CLEAR"
        rationale = (f"Current stock ({int(available_stock)}) exceeds {overstock_window}-week demand ({int(forward_demand)}). "
                     f"₹{capital_locked:,.0f} working capital locked in {int(excess_units)} excess units.")
    elif is_high_stockout and is_high_overstock:
        action = "WATCH / VOLATILE"
        rationale = ("Simultaneous stockout gap in immediate lead time and high inventory commitments forward. "
                     "Review supplier order schedules.")
    else:
        action = "HEALTHY"
        rationale = (f"Inventory ({int(available_stock)}) covers lead-time demand ({int(lead_time_demand)}) "
                     f"with adequate safety buffer ({int(safety_stock)}).")

    return {
        "sku_id": str(sku_id),
        "category": category,
        "subcategory": subcategory,
        "on_hand_units": int(on_hand_units),
        "on_order_units": int(on_order_units),
        "available_stock": int(available_stock),
        "lead_time_days": int(lead_time_days),
        "lead_time_demand": round(lead_time_demand, 1),
        "safety_stock": round(safety_stock, 1),
        "reorder_level": round(reorder_level, 1),
        "stockout_gap_units": round(stockout_gap, 1),
        "overstock_excess_units": round(excess_units, 1),
        "stockout_risk_score": round(stockout_risk_score, 4),
        "overstock_risk_score": round(overstock_risk_score, 4),
        "cumulative_forecast_demand": round(float(np.sum(fcst)), 1),
        "weekly_forecast": [round(float(v), 2) for v in fcst],
        "action": action,
        "action_rationale": rationale,
        "sales_at_risk_inr": sales_at_risk,
        "capital_locked_inr": capital_locked,
        "unit_price": float(unit_price),
        "unit_cost": float(unit_cost)
    }


def generate_full_risk_snapshot(
    panel_df: pd.DataFrame,
    forecast_records: List[Dict[str, Any]],
    output_path: Path
) -> pd.DataFrame:
    """Generates and saves the unified risk snapshot table across all active SKUs."""
    logger.info("Generating unified operational risk snapshot...")
    latest_skus = panel_df.sort_values("week_start").groupby("sku_id").last().reset_index()

    # Precompute historical standard deviation per SKU for safety stock
    sku_stds = panel_df.groupby("sku_id")["units_sold"].std().fillna(3.0).to_dict()

    fcst_lookup = {r["sku_id"]: r["weekly_forecast"] for r in forecast_records}

    risk_records = []
    for _, sku_row in latest_skus.iterrows():
        s_id = str(sku_row["sku_id"])
        weekly_fcst = fcst_lookup.get(s_id, np.array([float(sku_row["units_sold"])] * config.FORECAST_HORIZON_WEEKS))
        hist_std = sku_stds.get(s_id, 5.0)

        risk_prof = compute_sku_risk_profile(
            sku_id=s_id,
            category=str(sku_row["category"]),
            subcategory=str(sku_row["subcategory"]),
            weekly_forecast=np.asarray(weekly_fcst),
            on_hand_units=int(sku_row["on_hand_units"]),
            on_order_units=int(sku_row["on_order_units"]),
            lead_time_days=int(sku_row["lead_time_days"]),
            unit_cost=float(sku_row["unit_cost"]),
            unit_price=float(sku_row["list_price"]),
            historical_weekly_std=hist_std
        )
        risk_records.append(risk_prof)

    risk_df = pd.DataFrame(risk_records)
    ensure_dir(output_path.parent)
    save_dataframe(risk_df, output_path, format="csv")
    logger.info(f"Saved risk snapshot ({len(risk_df)} SKUs) to {output_path}")
    return risk_df
