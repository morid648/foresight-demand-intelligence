"""
Forecast Accuracy and Error Metrics for Project FORESIGHT.
Implements exact formulations for WAPE, Bias, and MAPE.
"""

from typing import Dict, Union
import numpy as np
import pandas as pd


def calculate_wape(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list]
) -> float:
    """Calculates Weighted Absolute Percentage Error (WAPE).
    
    Formula: WAPE = sum(|y - y_hat|) / sum(y)
    Returns float rounded to 4 decimal places (e.g. 0.1852 for 18.52%).
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    total_actual = np.sum(y_t)
    if total_actual == 0:
        return 0.0 if np.sum(np.abs(y_p)) == 0 else 1.0

    total_abs_error = np.sum(np.abs(y_t - y_p))
    return float(round(total_abs_error / total_actual, 4))


def calculate_bias(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list]
) -> float:
    """Calculates Forecast Bias (Normalized Mean Error).
    
    Formula: Bias = sum(y_hat - y) / sum(y)
    Positive value indicates over-forecasting; negative indicates under-forecasting.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    total_actual = np.sum(y_t)
    if total_actual == 0:
        return 0.0

    total_error = np.sum(y_p - y_t)
    return float(round(total_error / total_actual, 4))


def calculate_mape(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list],
    epsilon: float = 1e-5
) -> float:
    """Calculates Mean Absolute Percentage Error (MAPE).
    
    Formula: MAPE = (1/n) * sum(|y - y_hat| / (y + eps))
    Note: MAPE is sensitive to low-volume SKUs and provided strictly as secondary diagnostic.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    non_zero_mask = y_t > 0
    if not np.any(non_zero_mask):
        return 0.0

    pct_errors = np.abs(y_t[non_zero_mask] - y_p[non_zero_mask]) / (y_t[non_zero_mask] + epsilon)
    return float(round(np.mean(pct_errors), 4))


def evaluate_forecast(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list]
) -> Dict[str, float]:
    """Calculates all standard project evaluation metrics."""
    return {
        "wape": calculate_wape(y_true, y_pred),
        "bias": calculate_bias(y_true, y_pred),
        "mape": calculate_mape(y_true, y_pred)
    }
