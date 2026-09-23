"""
End-to-End Forecaster and Risk Engine Runner for Project FORESIGHT.
Fits production model, executes rolling CV, and produces scored forecast and risk snapshots.
"""

from pathlib import Path
import numpy as np
import pandas as pd

from src.config import config
from src.logging_utils import get_logger
from src.io import load_dataframe, save_dataframe, save_json, ensure_dir
from src.backtest import run_rolling_backtest
from src.features import extract_inference_features
from src.risk import generate_full_risk_snapshot

logger = get_logger(__name__)


def generate_production_artifacts() -> None:
    """Trains production models, generates rolling backtest results, and produces scored snapshots."""
    logger.info("Generating production forecast and inventory risk snapshots...")
    panel_df = load_dataframe(config.DATA_PROCESSED_DIR / "weekly_panel.parquet")

    # Step 1: Run Multi-Fold Rolling Backtest
    summary_metrics, winner_name, best_estimator = run_rolling_backtest(
        panel_df,
        n_folds=config.BACKTEST_FOLDS,
        horizon_weeks=config.FORECAST_HORIZON_WEEKS
    )

    # Step 2: Generate Forward Forecasts as of latest historical cutoff
    latest_cutoff = panel_df["week_start"].max()
    inf_features = extract_inference_features(
        panel_df,
        cutoff_date=latest_cutoff,
        horizon_weeks=config.FORECAST_HORIZON_WEEKS
    )

    forecast_records = []
    if winner_name != "Seasonal_Naive":
        X_inf = inf_features.drop(columns=["week_start", "sku_id", "horizon_step"])
        preds = best_estimator.predict(X_inf)
        inf_features["forecast_units"] = preds

        for sku_id, sku_group in inf_features.groupby("sku_id"):
            sku_group = sku_group.sort_values("horizon_step")
            forecast_records.append({
                "sku_id": str(sku_id),
                "weekly_forecast": sku_group["forecast_units"].values.tolist()
            })
    else:
        for sku_id in panel_df["sku_id"].unique():
            fcst_arr, _ = best_estimator.predict_sku(sku_id, horizon=config.FORECAST_HORIZON_WEEKS)
            forecast_records.append({
                "sku_id": str(sku_id),
                "weekly_forecast": fcst_arr.tolist()
            })

    # Save Forecast Snapshot
    artifacts_dir = ensure_dir(config.ARTIFACTS_DIR)
    fcst_df_rows = []
    for r in forecast_records:
        for step, val in enumerate(r["weekly_forecast"], 1):
            fcst_df_rows.append({
                "sku_id": r["sku_id"],
                "horizon_week": step,
                "forecast_units": round(val, 2)
            })
    df_fcst = pd.DataFrame(fcst_df_rows)
    save_dataframe(df_fcst, artifacts_dir / "forecast_snapshot.csv", format="csv")

    # Step 3: Compute Full Risk Engine Profile & Action Quadrants
    risk_df = generate_full_risk_snapshot(
        panel_df=panel_df,
        forecast_records=forecast_records,
        output_path=artifacts_dir / "risk_snapshot.csv"
    )

    logger.info("Production forecasting and risk snapshot artifacts successfully created.")


if __name__ == "__main__":
    generate_production_artifacts()
