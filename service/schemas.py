"""
API Schemas for Project FORESIGHT FastAPI Service.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SKUInputPayload(BaseModel):
    sku_id: str
    category: str = "Home Decor"
    subcategory: str = "Vases"
    on_hand_units: int = Field(ge=0, description="Current stock on hand")
    on_order_units: int = Field(default=0, ge=0, description="Stock on order from supplier")
    lead_time_days: int = Field(default=14, ge=1, description="Lead time in days")
    unit_cost: float = Field(ge=0.0, description="Cost price in INR")
    unit_price: float = Field(ge=0.0, description="Selling list price in INR")
    recent_weekly_sales: List[float] = Field(
        ...,
        min_length=1,
        description="Array of past weekly sales units (oldest to newest)"
    )


class BatchScoreRequest(BaseModel):
    skus: List[SKUInputPayload] = Field(..., min_length=1)


class SKUOutputResponse(BaseModel):
    sku_id: str
    category: str
    subcategory: str
    forecast_horizon_weeks: int
    weekly_forecast: List[float]
    cumulative_forecast_demand: float
    lead_time_demand: float
    safety_stock: float
    reorder_level: float
    stockout_gap_units: float
    overstock_excess_units: float
    stockout_risk_score: float
    overstock_risk_score: float
    action: Literal["REORDER NOW", "MARKDOWN / CLEAR", "WATCH / VOLATILE", "HEALTHY"]
    action_rationale: str
    sales_at_risk_inr: float
    capital_locked_inr: float


class BatchScoreResponse(BaseModel):
    total_skus_assessed: int
    total_sales_at_risk_inr: float
    total_capital_locked_inr: float
    results: List[SKUOutputResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_status: str


class MetadataResponse(BaseModel):
    model_name: str
    forecast_horizon_weeks: int
    seasonal_period_weeks: int
    safety_stock_z: float
    overstock_horizon_weeks: int
    baseline_wape: Optional[float]
    winner_wape: Optional[float]
