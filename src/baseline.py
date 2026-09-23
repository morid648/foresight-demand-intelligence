"""
Seasonal-Naive Baseline Forecaster for Project FORESIGHT.
Implements 52-week seasonal-naive benchmark with moving-median fallback for short-history SKUs.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from src.config import config
from src.logging_utils import get_logger

logger = get_logger(__name__)


class SeasonalNaiveBaseline:
    """Seasonal-Naive baseline forecaster.
    
    Forecast logic:
    - If historical series length >= 52 weeks: forecast(t+h) = y(t+h-52).
    - If historical series length < 52 weeks: forecast(t+h) = median(last 8 weeks).
    """

    def __init__(self, seasonal_period: int = 52, fallback_window: int = 8):
        self.seasonal_period = seasonal_period
        self.fallback_window = fallback_window
        self.history_per_sku: Dict[str, np.ndarray] = {}

    def fit(self, panel_df: pd.DataFrame, cutoff_date: Optional[pd.Timestamp] = None) -> "SeasonalNaiveBaseline":
        """Ingests history up to cutoff_date per SKU."""
        df = panel_df.copy()
        if cutoff_date is not None:
            df = df[df["week_start"] <= pd.to_datetime(cutoff_date)]

        df = df.sort_values(["sku_id", "week_start"])
        self.history_per_sku = {}

        for sku_id, group in df.groupby("sku_id"):
            self.history_per_sku[str(sku_id)] = group["units_sold"].values.astype(float)

        logger.info(f"SeasonalNaiveBaseline fitted on {len(self.history_per_sku)} SKUs as of cutoff {cutoff_date}")
        return self

    def predict_sku(self, sku_id: str, horizon: int = 8) -> Tuple[np.ndarray, str]:
        """Generates H-step forecast for a single SKU.
        
        Returns:
            (forecast_array, method_used)
        """
        history = self.history_per_sku.get(str(sku_id))
        if history is None or len(history) == 0:
            return np.zeros(horizon, dtype=float), "no_history_zero"

        n_hist = len(history)
        forecast = np.zeros(horizon, dtype=float)

        if n_hist >= self.seasonal_period:
            method = "seasonal_52w"
            for h in range(horizon):
                # t + (h+1) - 52
                idx = n_hist + h - self.seasonal_period
                if idx < n_hist:
                    forecast[h] = max(0.0, history[idx])
                else:
                    # Recursive wrap
                    forecast[h] = max(0.0, forecast[h - self.seasonal_period])
        else:
            method = "median_fallback"
            window = min(n_hist, self.fallback_window)
            med_val = float(np.median(history[-window:]))
            forecast[:] = max(0.0, med_val)

        return forecast, method

    def predict_panel(self, horizon: int = 8) -> pd.DataFrame:
        """Generates predictions for all fitted SKUs."""
        records = []
        for sku_id in self.history_per_sku.keys():
            fcst, method = self.predict_sku(sku_id, horizon=horizon)
            for h_idx, val in enumerate(fcst):
                records.append({
                    "sku_id": sku_id,
                    "horizon_step": h_idx + 1,
                    "baseline_forecast": float(val),
                    "baseline_method": method
                })
        return pd.DataFrame(records)
