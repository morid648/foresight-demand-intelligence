"""
Rolling-Origin Cross-Validation and Model Evaluation Engine for Project FORESIGHT.
Executes multi-fold leakage-free backtesting and enforces honest baseline comparison.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import config
from src.logging_utils import get_logger
from src.io import ensure_dir, save_json, save_dataframe
from src.metrics import calculate_wape, calculate_bias, calculate_mape
from src.baseline import SeasonalNaiveBaseline
from src.features import build_time_safe_features, extract_inference_features
from src.forecast import get_candidate_models

logger = get_logger(__name__)


def generate_rolling_cv_cutoffs(
    panel_df: pd.DataFrame,
    n_folds: int = 4,
    horizon_weeks: int = 8,
    step_weeks: int = 4
) -> List[pd.Timestamp]:
    """Computes cutoff timestamps for expanding-window rolling CV."""
    all_dates = sorted(panel_df["week_start"].unique())
    max_date = all_dates[-1]

    cutoffs = []
    for i in range(n_folds):
        # Reserve horizon_weeks at end for latest fold
        offset_steps = horizon_weeks + (i * step_weeks)
        if len(all_dates) > offset_steps + 26:  # Ensure at least 26 weeks training
            cutoff_date = all_dates[-offset_steps]
            cutoffs.append(pd.Timestamp(cutoff_date))

    cutoffs = sorted(cutoffs)
    logger.info(f"Generated {len(cutoffs)} rolling CV cutoffs: {[c.strftime('%Y-%m-%d') for c in cutoffs]}")
    return cutoffs


def run_rolling_backtest(
    panel_df: pd.DataFrame,
    n_folds: int = 4,
    horizon_weeks: int = 8
) -> Tuple[Dict[str, Any], str, Any]:
    """Executes rolling-origin evaluation for baseline and candidate models."""
    logger.info("Starting Rolling-Origin Cross-Validation Backtest...")
    cutoffs = generate_rolling_cv_cutoffs(panel_df, n_folds=n_folds, horizon_weeks=horizon_weeks)

    candidates = get_candidate_models()
    model_names = ["Seasonal_Naive"] + list(candidates.keys())

    fold_results: Dict[str, List[Dict[str, float]]] = {m: [] for m in model_names}
    all_actuals: Dict[str, List[float]] = {m: [] for m in model_names}
    all_predictions: Dict[str, List[float]] = {m: [] for m in model_names}

    for fold_idx, cutoff in enumerate(cutoffs):
        logger.info(f"--- Running Fold {fold_idx + 1}/{len(cutoffs)} (Cutoff: {cutoff.strftime('%Y-%m-%d')}) ---")

        # Ground truth validation window
        val_start = cutoff + pd.Timedelta(days=1)
        val_end = cutoff + pd.Timedelta(weeks=horizon_weeks)
        val_df = panel_df[(panel_df["week_start"] >= val_start) & (panel_df["week_start"] <= val_end)].copy()

        # Step 1: Baseline Evaluation
        baseline = SeasonalNaiveBaseline(seasonal_period=config.SEASONAL_PERIOD_WEEKS)
        baseline.fit(panel_df, cutoff_date=cutoff)

        baseline_preds = []
        baseline_trues = []
        for _, val_row in val_df.iterrows():
            sku_id = str(val_row["sku_id"])
            # Step in horizon
            step_idx = int((val_row["week_start"] - cutoff).days // 7)
            if 0 <= step_idx < horizon_weeks:
                fcst_arr, _ = baseline.predict_sku(sku_id, horizon=horizon_weeks)
                pred_val = fcst_arr[step_idx]
                actual_val = float(val_row["units_sold"])
                baseline_preds.append(pred_val)
                baseline_trues.append(actual_val)

        base_wape = calculate_wape(baseline_trues, baseline_preds)
        base_bias = calculate_bias(baseline_trues, baseline_preds)
        fold_results["Seasonal_Naive"].append({"fold": fold_idx + 1, "wape": base_wape, "bias": base_bias})
        all_actuals["Seasonal_Naive"].extend(baseline_trues)
        all_predictions["Seasonal_Naive"].extend(baseline_preds)

        # Step 2: Candidates Feature Generation & Training strictly <= cutoff
        train_features = build_time_safe_features(panel_df, cutoff_date=cutoff)
        X_train = train_features.drop(columns=["week_start", "sku_id", "target_units"])
        y_train = train_features["target_units"].values

        # Validation features
        val_features = build_time_safe_features(panel_df, cutoff_date=val_end)
        val_features = val_features[(val_features["week_start"] >= val_start) & (val_features["week_start"] <= val_end)]

        if len(val_features) > 0:
            X_val = val_features.drop(columns=["week_start", "sku_id", "target_units"])
            y_val = val_features["target_units"].values

            for name, pipeline in candidates.items():
                pipeline.fit(X_train, y_train)
                preds = pipeline.predict(X_val)

                cand_wape = calculate_wape(y_val, preds)
                cand_bias = calculate_bias(y_val, preds)
                fold_results[name].append({"fold": fold_idx + 1, "wape": cand_wape, "bias": cand_bias})
                all_actuals[name].extend(y_val.tolist())
                all_predictions[name].extend(preds.tolist())

    # Aggregate Metrics Calculation
    summary_metrics: Dict[str, Any] = {"models": {}, "folds": len(cutoffs), "horizon_weeks": horizon_weeks}

    best_wape = float("inf")
    winner_name = "Seasonal_Naive"

    for m_name in model_names:
        agg_wape = calculate_wape(all_actuals[m_name], all_predictions[m_name])
        agg_bias = calculate_bias(all_actuals[m_name], all_predictions[m_name])
        agg_mape = calculate_mape(all_actuals[m_name], all_predictions[m_name])

        summary_metrics["models"][m_name] = {
            "aggregate_wape": agg_wape,
            "aggregate_bias": agg_bias,
            "aggregate_mape": agg_mape,
            "fold_breakdown": fold_results[m_name]
        }
        logger.info(f"Model: {m_name:20s} | Aggregate WAPE: {agg_wape:.4f} | Bias: {agg_bias:+.4f}")

        if agg_wape < best_wape:
            best_wape = agg_wape
            winner_name = m_name

    # Baseline comparison logic
    baseline_wape = summary_metrics["models"]["Seasonal_Naive"]["aggregate_wape"]
    summary_metrics["winner"] = winner_name
    summary_metrics["baseline_wape"] = baseline_wape
    summary_metrics["winning_wape"] = best_wape
    summary_metrics["beats_baseline"] = bool(best_wape < baseline_wape)

    # Save artifacts
    artifacts_dir = ensure_dir(config.ARTIFACTS_DIR)
    save_json(summary_metrics, artifacts_dir / "metrics.json")

    # Fit best model on all available historical data
    max_cutoff = panel_df["week_start"].max()
    if winner_name != "Seasonal_Naive":
        full_train_features = build_time_safe_features(panel_df, cutoff_date=max_cutoff)
        X_full = full_train_features.drop(columns=["week_start", "sku_id", "target_units"])
        y_full = full_train_features["target_units"].values
        best_estimator = candidates[winner_name]
        best_estimator.fit(X_full, y_full)
    else:
        best_estimator = SeasonalNaiveBaseline(seasonal_period=config.SEASONAL_PERIOD_WEEKS)
        best_estimator.fit(panel_df, cutoff_date=max_cutoff)

    logger.info(f"Winning model selected: {winner_name} (WAPE={best_wape:.4f} vs Baseline WAPE={baseline_wape:.4f})")
    return summary_metrics, winner_name, best_estimator
