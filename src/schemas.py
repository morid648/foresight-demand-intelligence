"""
Core Data Contracts and Schema Definitions for Project FORESIGHT.
"""

from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class SalesDailyRecord(BaseModel):
    """Raw daily sales transaction record."""
    model_config = ConfigDict(extra="ignore")

    date: date
    sku_id: str
    units_sold: int = Field(ge=0, description="Daily units sold, non-negative")
    revenue: float = Field(ge=0.0, description="Daily realized revenue")
    unit_price: float = Field(ge=0.0, description="Realized unit selling price")
    promo_flag: int = Field(default=0, ge=0, le=1, description="Binary flag indicating active promotion")


class SKUMasterRecord(BaseModel):
    """SKU catalogue master record."""
    model_config = ConfigDict(extra="ignore")

    sku_id: str
    category: str
    subcategory: str
    launch_date: date
    unit_cost: float = Field(ge=0.0, description="Cost of goods sold per unit (COGS)")
    list_price: float = Field(ge=0.0, description="MSRP / Standard list price")


class CalendarRecord(BaseModel):
    """Calendar reference record."""
    model_config = ConfigDict(extra="ignore")

    date: date
    week: int = Field(ge=1, le=53, description="ISO week number")
    month: int = Field(ge=1, le=12, description="Month number")
    season: str
    is_holiday: int = Field(default=0, ge=0, le=1)
    promo_event: Optional[str] = None


class InventorySnapshotRecord(BaseModel):
    """Periodic inventory position record."""
    model_config = ConfigDict(extra="ignore")

    date: date
    sku_id: str
    on_hand_units: int = Field(ge=0, description="Current physical stock")
    on_order_units: int = Field(default=0, ge=0, description="Stock in transit from supplier")
    lead_time_days: int = Field(ge=1, description="Supplier replenishment lead time in days")
    reorder_point: Optional[int] = Field(default=None, ge=0)


class WeeklyPanelRecord(BaseModel):
    """Processed weekly aggregated panel record per SKU."""
    model_config = ConfigDict(extra="ignore")

    week_start: date
    sku_id: str
    category: str
    subcategory: str
    units_sold: float = Field(ge=0.0)
    revenue: float = Field(ge=0.0)
    avg_unit_price: float = Field(ge=0.0)
    promo_active_days: int = Field(ge=0, le=7)
    is_holiday_week: int = Field(ge=0, le=1)
    unit_cost: float = Field(ge=0.0)
    list_price: float = Field(ge=0.0)
    on_hand_units: int = Field(ge=0)
    on_order_units: int = Field(ge=0)
    lead_time_days: int = Field(ge=1)


class ScoreRequest(BaseModel):
    """FastAPI payload for single SKU scoring."""
    sku_id: str
    category: str = "General"
    subcategory: str = "General"
    on_hand_units: int = Field(ge=0)
    on_order_units: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=14, ge=1)
    unit_cost: float = Field(ge=0.0)
    unit_price: float = Field(ge=0.0)
    recent_weekly_sales: List[float] = Field(..., description="Historical weekly sales array (most recent last)")
    planned_promotions: Optional[List[int]] = Field(default=None, description="Binary promo flags for horizon weeks")


class ScoreResponse(BaseModel):
    """FastAPI response payload with demand forecast, risk scores, and financial impact."""
    sku_id: str
    model_name: str
    forecast_horizon_weeks: int
    weekly_forecast: List[float]
    cumulative_forecast_demand: float
    lead_time_demand: float
    stockout_gap_units: float
    overstock_excess_units: float
    stockout_risk_score: float = Field(ge=0.0, le=1.0)
    overstock_risk_score: float = Field(ge=0.0, le=1.0)
    action: Literal["REORDER NOW", "MARKDOWN / CLEAR", "WATCH / VOLATILE", "HEALTHY"]
    action_rationale: str
    sales_at_risk_inr: float
    capital_locked_inr: float
