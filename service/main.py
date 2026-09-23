"""
FastAPI Microservice for Project FORESIGHT.
Exposes /health, /metadata, /score, and /score/batch using the shared core scoring engine.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd

from src.config import config
from src.logging_utils import get_logger
from src.io import load_json
from src.baseline import SeasonalNaiveBaseline
from src.risk import compute_sku_risk_profile
from service.schemas import (
    SKUInputPayload,
    SKUOutputResponse,
    BatchScoreRequest,
    BatchScoreResponse,
    HealthResponse,
    MetadataResponse
)

logger = get_logger(__name__)

app = FastAPI(
    title="Project FORESIGHT Scoring Service",
    description="Operational Demand Forecasting & Inventory Risk Scoring API for NorthBay Living",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def score_single_sku_logic(payload: SKUInputPayload) -> SKUOutputResponse:
    """Shared scoring logic for API endpoints."""
    recent_sales = np.array(payload.recent_weekly_sales, dtype=float)
    if len(recent_sales) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recent_weekly_sales array cannot be empty"
        )

    # Generate 8-week forward forecast using seasonal/trend weighted projection
    n = len(recent_sales)
    if n >= 52:
        # Seasonal 52w lag
        weekly_fcst = np.array([max(0.0, recent_sales[-52 + (h % 52)]) for h in range(config.FORECAST_HORIZON_WEEKS)])
    else:
        # Exponential moving median / average
        recent_window = min(n, 8)
        med_val = float(np.median(recent_sales[-recent_window:]))
        # Add slight trend if available
        trend = float(np.mean(np.diff(recent_sales[-recent_window:]))) if recent_window >= 4 else 0.0
        weekly_fcst = np.array([max(0.0, med_val + (h * trend * 0.1)) for h in range(config.FORECAST_HORIZON_WEEKS)])

    hist_std = float(np.std(recent_sales)) if n >= 2 else 5.0

    profile = compute_sku_risk_profile(
        sku_id=payload.sku_id,
        category=payload.category,
        subcategory=payload.subcategory,
        weekly_forecast=weekly_fcst,
        on_hand_units=payload.on_hand_units,
        on_order_units=payload.on_order_units,
        lead_time_days=payload.lead_time_days,
        unit_cost=payload.unit_cost,
        unit_price=payload.unit_price,
        historical_weekly_std=hist_std
    )

    return SKUOutputResponse(
        sku_id=profile["sku_id"],
        category=profile["category"],
        subcategory=profile["subcategory"],
        forecast_horizon_weeks=config.FORECAST_HORIZON_WEEKS,
        weekly_forecast=profile["weekly_forecast"],
        cumulative_forecast_demand=profile["cumulative_forecast_demand"],
        lead_time_demand=profile["lead_time_demand"],
        safety_stock=profile["safety_stock"],
        reorder_level=profile["reorder_level"],
        stockout_gap_units=profile["stockout_gap_units"],
        overstock_excess_units=profile["overstock_excess_units"],
        stockout_risk_score=profile["stockout_risk_score"],
        overstock_risk_score=profile["overstock_risk_score"],
        action=profile["action"],
        action_rationale=profile["action_rationale"],
        sales_at_risk_inr=profile["sales_at_risk_inr"],
        capital_locked_inr=profile["capital_locked_inr"]
    )


@app.get("/health", response_model=HealthResponse, tags=["Observability"])
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="foresight-scoring-service",
        version="1.0.0",
        uptime_status="operational"
    )


@app.get("/metadata", response_model=MetadataResponse, tags=["Observability"])
def get_metadata() -> MetadataResponse:
    """Returns active model metadata, parameters, and backtest results."""
    baseline_wape = None
    winner_wape = None
    model_name = "RandomForest"

    metrics_path = config.ARTIFACTS_DIR / "metrics.json"
    if metrics_path.exists():
        try:
            m_data = load_json(metrics_path)
            model_name = m_data.get("winner", "RandomForest")
            baseline_wape = m_data.get("baseline_wape")
            winner_wape = m_data.get("winning_wape")
        except Exception:
            pass

    return MetadataResponse(
        model_name=model_name,
        forecast_horizon_weeks=config.FORECAST_HORIZON_WEEKS,
        seasonal_period_weeks=config.SEASONAL_PERIOD_WEEKS,
        safety_stock_z=config.SAFETY_STOCK_Z,
        overstock_horizon_weeks=config.OVERSTOCK_HORIZON_WEEKS,
        baseline_wape=baseline_wape,
        winner_wape=winner_wape
    )


@app.post("/score", response_model=SKUOutputResponse, tags=["Scoring"])
def score_sku(payload: SKUInputPayload) -> SKUOutputResponse:
    """Scores a single SKU's demand forecast, risk quadrant, and financial impact."""
    try:
        return score_single_sku_logic(payload)
    except Exception as e:
        logger.error(f"Error scoring SKU {payload.sku_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scoring computation error: {str(e)}"
        )


@app.post("/score/batch", response_model=BatchScoreResponse, tags=["Scoring"])
def score_batch(payload: BatchScoreRequest) -> BatchScoreResponse:
    """Scores multiple SKUs in batch."""
    results = []
    total_sales_at_risk = 0.0
    total_capital_locked = 0.0

    for sku_item in payload.skus:
        res = score_single_sku_logic(sku_item)
        results.append(res)
        total_sales_at_risk += res.sales_at_risk_inr
        total_capital_locked += res.capital_locked_inr

    return BatchScoreResponse(
        total_skus_assessed=len(results),
        total_sales_at_risk_inr=round(total_sales_at_risk, 2),
        total_capital_locked_inr=round(total_capital_locked, 2),
        results=results
    )
