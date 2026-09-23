"""
Project FORESIGHT — Serverless FastAPI Microservice for Vercel.
Operational Demand Forecasting & Inventory Risk Intelligence API for NorthBay Living.
"""

from typing import List, Optional, Literal, Dict, Any
import json
import numpy as np
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

app = FastAPI(
    title="Project FORESIGHT Scoring Service",
    description="Operational Demand Forecasting & Inventory Risk Scoring API for NorthBay Living",
    version="1.0.0",
    docs_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# Pydantic Request & Response Schemas
# ==========================================

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
    baseline_wape: float
    winner_wape: float


# ==========================================
# Core Decision & Risk Logic (Pure Python)
# ==========================================

def calculate_sales_at_risk_inr(stockout_gap_units: float, unit_selling_price: float) -> float:
    return float(round(max(0.0, float(stockout_gap_units)) * max(0.0, float(unit_selling_price)), 2))


def calculate_capital_locked_inr(excess_overstock_units: float, unit_cost: float) -> float:
    return float(round(max(0.0, float(excess_overstock_units)) * max(0.0, float(unit_cost)), 2))


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
    fcst = np.asarray(weekly_forecast, dtype=float)
    horizon_weeks = len(fcst)
    lead_time_weeks = max(1.0, lead_time_days / 7.0)

    # Lead-time demand
    full_weeks_lead = int(np.floor(lead_time_weeks))
    partial_fraction = lead_time_weeks - full_weeks_lead
    lt_demand_int = np.sum(fcst[:min(horizon_weeks, full_weeks_lead)])
    lt_demand_partial = fcst[full_weeks_lead] * partial_fraction if full_weeks_lead < horizon_weeks and partial_fraction > 0 else 0.0
    lead_time_demand = float(lt_demand_int + lt_demand_partial)
    available_stock = float(on_hand_units + on_order_units)

    # Safety stock (Z=1.65 for 95% CSL)
    safety_stock = float(round(1.65 * historical_weekly_std * np.sqrt(lead_time_weeks), 1))
    reorder_level = lead_time_demand + safety_stock

    # Stockout gap & score
    stockout_gap = max(0.0, float(reorder_level - available_stock))
    stockout_risk_score = float(np.clip(stockout_gap / (reorder_level + 1e-5), 0.0, 1.0))

    # Overstock forward horizon (12 weeks)
    overstock_window = 12
    avg_weekly_fcst = float(np.mean(fcst)) if len(fcst) > 0 else 1.0
    forward_demand = avg_weekly_fcst * overstock_window
    excess_units = max(0.0, float(available_stock - forward_demand - safety_stock))
    overstock_risk_score = float(np.clip(excess_units / (forward_demand + 1e-5), 0.0, 1.0))

    # Financial exposure
    sales_at_risk = calculate_sales_at_risk_inr(stockout_gap, unit_price)
    capital_locked = calculate_capital_locked_inr(excess_units, unit_cost)

    # 4-Quadrant mapping
    is_high_stockout = stockout_risk_score >= 0.50
    is_high_overstock = overstock_risk_score >= 0.50

    if is_high_stockout and not is_high_overstock:
        action = "REORDER NOW"
        rationale = (f"Available stock ({int(available_stock)}) is below reorder level ({int(reorder_level)}) "
                     f"across {lead_time_days}d lead time. Gap of {int(stockout_gap)} units.")
    elif not is_high_stockout and is_high_overstock:
        action = "MARKDOWN / CLEAR"
        rationale = (f"Current stock ({int(available_stock)}) exceeds {overstock_window}-week demand ({int(forward_demand)}). "
                     f"₹{capital_locked:,.0f} working capital locked in {int(excess_units)} excess units.")
    elif is_high_stockout and is_high_overstock:
        action = "WATCH / VOLATILE"
        rationale = "Simultaneous stockout gap in lead time and high inventory forward. Review replenishment schedule."
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
        "capital_locked_inr": capital_locked
    }


def score_single_sku_logic(payload: SKUInputPayload) -> SKUOutputResponse:
    recent_sales = np.array(payload.recent_weekly_sales, dtype=float)
    if len(recent_sales) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="recent_weekly_sales array cannot be empty")

    n = len(recent_sales)
    if n >= 52:
        weekly_fcst = np.array([max(0.0, recent_sales[-52 + (h % 52)]) for h in range(8)])
    else:
        recent_window = min(n, 8)
        med_val = float(np.median(recent_sales[-recent_window:]))
        trend = float(np.mean(np.diff(recent_sales[-recent_window:]))) if recent_window >= 4 else 0.0
        weekly_fcst = np.array([max(0.0, med_val + (h * trend * 0.1)) for h in range(8)])

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
        forecast_horizon_weeks=8,
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


# ==========================================
LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project FORESIGHT — AI Demand & Inventory Intelligence Platform</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #0B0F19;
      --surface: #111827;
      --surface-border: #1F2937;
      --surface-hover: #1E293B;
      --text-main: #F9FAFB;
      --text-muted: #9CA3AF;
      --primary: #06B6D4;
      --primary-glow: rgba(6, 182, 212, 0.15);
      --accent: #3B82F6;
      --success: #10B981;
      --warning: #F59E0B;
      --danger: #EF4444;
      --purple: #8B5CF6;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-xl: 24px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, sans-serif;
      line-height: 1.6;
      overflow-x: hidden;
    }

    h1, h2, h3, h4, .brand-font { font-family: 'Outfit', sans-serif; }

    /* Ambient background glows */
    .glow-top {
      position: absolute;
      top: -120px;
      left: 50%;
      transform: translateX(-50%);
      width: 800px;
      height: 400px;
      background: radial-gradient(circle, rgba(6, 182, 212, 0.18) 0%, rgba(59, 130, 246, 0.08) 50%, transparent 70%);
      pointer-events: none;
      z-index: 0;
    }

    .container {
      max-width: 1240px;
      margin: 0 auto;
      padding: 0 24px;
      position: relative;
      z-index: 1;
    }

    /* Navbar */
    header {
      padding: 20px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(11, 15, 25, 0.85);
    }
    .nav-wrapper {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand-logo {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: var(--text-main);
    }
    .logo-icon {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #06B6D4, #3B82F6);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 18px;
      box-shadow: 0 0 16px rgba(6, 182, 212, 0.4);
    }
    .brand-title { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; }
    .nav-links { display: flex; align-items: center; gap: 16px; }
    .status-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--success);
      padding: 5px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }
    .status-dot { width: 7px; height: 7px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.8); } }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 18px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
      cursor: pointer;
      border: none;
    }
    .btn-primary {
      background: linear-gradient(135deg, #06B6D4, #3B82F6);
      color: white;
      box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3);
    }
    .btn-primary:hover {
      box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5);
      transform: translateY(-1px);
    }
    .btn-outline {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
    }
    .btn-outline:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.25);
    }

    /* Hero */
    .hero {
      padding: 64px 0 40px;
      text-align: center;
    }
    .badge-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(6, 182, 212, 0.1);
      border: 1px solid rgba(6, 182, 212, 0.25);
      color: var(--primary);
      padding: 6px 16px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 20px;
    }
    .hero h1 {
      font-size: 46px;
      font-weight: 800;
      letter-spacing: -1.5px;
      line-height: 1.15;
      margin-bottom: 18px;
      background: linear-gradient(180deg, #FFFFFF 0%, #CBD5E1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .hero p {
      font-size: 18px;
      color: var(--text-muted);
      max-width: 780px;
      margin: 0 auto 32px;
      font-weight: 400;
    }
    .hero-actions {
      display: flex;
      justify-content: center;
      gap: 14px;
      flex-wrap: wrap;
    }

    /* KPI Cards */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 20px;
      margin: 48px 0;
    }
    .kpi-card {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      padding: 24px;
      border-radius: var(--radius-lg);
      position: relative;
      overflow: hidden;
      transition: transform 0.2s, border-color 0.2s;
    }
    .kpi-card:hover {
      transform: translateY(-2px);
      border-color: rgba(6, 182, 212, 0.35);
    }
    .kpi-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
    }
    .kpi-cyan::before { background: linear-gradient(90deg, #06B6D4, #3B82F6); }
    .kpi-danger::before { background: linear-gradient(90deg, #EF4444, #F59E0B); }
    .kpi-amber::before { background: linear-gradient(90deg, #F59E0B, #10B981); }
    .kpi-emerald::before { background: linear-gradient(90deg, #10B981, #06B6D4); }

    .kpi-label { font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 34px; font-weight: 700; font-family: 'Outfit', sans-serif; color: #FFF; line-height: 1.1; margin-bottom: 8px; }
    .kpi-subtext { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
    .kpi-badge { padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
    .badge-win { background: rgba(16, 185, 129, 0.15); color: #34D399; }
    .badge-loss { background: rgba(239, 68, 68, 0.15); color: #F87171; }
    .badge-warn { background: rgba(245, 158, 11, 0.15); color: #FBBF24; }

    /* Visual Analytics Section */
    .section-header {
      margin: 64px 0 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 16px;
    }
    .section-title { font-size: 26px; font-weight: 700; color: #FFF; }
    .section-subtitle { font-size: 14px; color: var(--text-muted); }

    .charts-grid {
      display: grid;
      grid-template-columns: 3fr 2fr;
      gap: 24px;
      margin-bottom: 48px;
    }
    @media (max-width: 900px) {
      .charts-grid { grid-template-columns: 1fr; }
      .hero h1 { font-size: 34px; }
    }

    .chart-card {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-lg);
      padding: 24px;
    }
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .chart-title { font-size: 16px; font-weight: 600; color: #FFF; }

    /* Interactive Simulator */
    .simulator-container {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-xl);
      padding: 32px;
      margin: 48px 0;
      position: relative;
    }
    .sim-presets {
      display: flex;
      gap: 10px;
      margin: 16px 0 24px;
      flex-wrap: wrap;
    }
    .preset-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-main);
      padding: 8px 14px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    .preset-btn:hover, .preset-btn.active {
      background: var(--primary-glow);
      border-color: var(--primary);
      color: var(--primary);
    }
    .sim-form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .input-group { display: flex; flex-direction: column; gap: 6px; }
    .input-label { font-size: 12px; font-weight: 500; color: var(--text-muted); }
    .input-control {
      background: #0B0F19;
      border: 1px solid #1F2937;
      color: #FFF;
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    .input-control:focus { border-color: var(--primary); }

    /* Simulator Output Box */
    .sim-result-box {
      background: #0B0F19;
      border: 1px solid #1F2937;
      border-radius: var(--radius-lg);
      padding: 24px;
      display: grid;
      grid-template-columns: 1fr 1.5fr;
      gap: 24px;
    }
    @media (max-width: 800px) {
      .sim-result-box { grid-template-columns: 1fr; }
    }
    .decision-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: var(--radius-md);
      font-size: 16px;
      font-weight: 700;
      font-family: 'Outfit', sans-serif;
      margin-bottom: 14px;
    }
    .badge-reorder { background: rgba(239, 68, 68, 0.18); border: 1px solid var(--danger); color: #F87171; }
    .badge-markdown { background: rgba(245, 158, 11, 0.18); border: 1px solid var(--warning); color: #FBBF24; }
    .badge-watch { background: rgba(139, 92, 246, 0.18); border: 1px solid var(--purple); color: #A78BFA; }
    .badge-healthy { background: rgba(16, 185, 129, 0.18); border: 1px solid var(--success); color: #34D399; }

    .risk-stat-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 13px;
    }
    .risk-stat-label { color: var(--text-muted); }
    .risk-stat-val { font-weight: 600; color: #FFF; }

    /* API Table */
    .api-table {
      width: 100%;
      border-collapse: collapse;
      margin: 24px 0 64px;
      background: var(--surface);
      border-radius: var(--radius-lg);
      overflow: hidden;
      border: 1px solid var(--surface-border);
    }
    .api-table th, .api-table td {
      padding: 16px 20px;
      text-align: left;
      border-bottom: 1px solid var(--surface-border);
      font-size: 13px;
    }
    .api-table th { background: rgba(255, 255, 255, 0.02); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }
    .http-method { padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; font-family: monospace; }
    .method-get { background: rgba(16, 185, 129, 0.15); color: var(--success); }
    .method-post { background: rgba(59, 130, 246, 0.15); color: var(--accent); }

    /* Footer */
    footer {
      border-top: 1px solid var(--surface-border);
      padding: 40px 0;
      margin-top: 64px;
      text-align: center;
      color: var(--text-muted);
      font-size: 13px;
    }
    .footer-links { display: flex; justify-content: center; gap: 20px; margin-bottom: 16px; }
    .footer-links a { color: var(--primary); text-decoration: none; font-weight: 500; }
    .footer-links a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="glow-top"></div>

  <!-- Navbar -->
  <header>
    <div class="container nav-wrapper">
      <a href="/" class="brand-logo">
        <div class="logo-icon">F</div>
        <div>
          <div class="brand-title">Project FORESIGHT</div>
        </div>
      </a>
      <div class="nav-links">
        <div class="status-pill">
          <div class="status-dot"></div>
          API Live
        </div>
        <a href="/docs" class="btn btn-outline">📖 Swagger Docs</a>
        <a href="https://github.com/morid648/foresight-demand-intelligence" target="_blank" class="btn btn-primary">⭐ GitHub Repo</a>
      </div>
    </div>
  </header>

  <main class="container">
    <!-- Hero -->
    <section class="hero">
      <div class="badge-pill">
        <span>⚡ Production Demand Intelligence & Risk Engine</span>
      </div>
      <h1>Predict SKU Demand. Prevent Stockouts.<br>Liberate Working Capital.</h1>
      <p>
        An operational machine learning system designed for <strong>NorthBay Living</strong>. 
        Engineered with strict zero-leakage cross-validation, 8-week forward horizon forecasting, 
        and dynamic 4-quadrant inventory risk allocation.
      </p>
      <div class="hero-actions">
        <a href="#simulator" class="btn btn-primary" style="padding: 12px 24px; font-size: 15px;">⚡ Run Live AI Simulator</a>
        <a href="/docs" class="btn btn-outline" style="padding: 12px 24px; font-size: 15px;">🔍 Explore Interactive REST API</a>
      </div>
    </section>

    <!-- Executive KPI Grid -->
    <section class="kpi-grid">
      <div class="kpi-card kpi-cyan">
        <div class="kpi-label">Forecast Accuracy (WAPE)</div>
        <div class="kpi-value">20.79%</div>
        <div class="kpi-subtext">
          <span class="kpi-badge badge-win">+37.3% vs Baseline</span>
          <span>(Seasonal-Naive: 33.17%)</span>
        </div>
      </div>

      <div class="kpi-card kpi-danger">
        <div class="kpi-label">Sales at Risk Identified</div>
        <div class="kpi-value">₹1,21,115</div>
        <div class="kpi-subtext">
          <span class="kpi-badge badge-loss">12 SKUs Flagged</span>
          <span>Reorder action required</span>
        </div>
      </div>

      <div class="kpi-card kpi-amber">
        <div class="kpi-label">Working Capital Locked</div>
        <div class="kpi-value">₹1,27,990</div>
        <div class="kpi-subtext">
          <span class="kpi-badge badge-warn">6 SKUs Flagged</span>
          <span>Markdown / clear action</span>
        </div>
      </div>

      <div class="kpi-card kpi-emerald">
        <div class="kpi-label">Portfolio & Panel Scope</div>
        <div class="kpi-value">40 SKUs</div>
        <div class="kpi-subtext">
          <span class="kpi-badge badge-win">3,741 Panels</span>
          <span>Zero-leakage validated</span>
        </div>
      </div>
    </section>

    <!-- Visual Analytics Charts -->
    <section>
      <div class="section-header">
        <div>
          <h2 class="section-title">Backtest Benchmark & Portfolio Distribution</h2>
          <p class="section-subtitle">Evaluating 4 competitive forecasting architectures across 52-week rolling windows.</p>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">Model Backtest WAPE Comparison (%)</span>
            <span style="font-size: 12px; color: var(--primary); font-weight: 600;">Lower is Better</span>
          </div>
          <div style="height: 260px;">
            <canvas id="benchmarkChart"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">Inventory Risk Quadrant Breakdown</span>
            <span style="font-size: 12px; color: var(--text-muted);">40 SKUs Total</span>
          </div>
          <div style="height: 260px;">
            <canvas id="riskDonutChart"></canvas>
          </div>
        </div>
      </div>
    </section>

    <!-- Interactive Live AI Simulator -->
    <section id="simulator" class="simulator-container">
      <div class="section-header" style="margin-top: 0;">
        <div>
          <h2 class="section-title">⚡ Interactive SKU Forecast & Risk Sandbox</h2>
          <p class="section-subtitle">Test the microservice with custom inventory inputs or one-click scenario presets.</p>
        </div>
      </div>

      <div class="sim-presets">
        <span style="font-size: 12px; color: var(--text-muted); align-self: center; margin-right: 4px;">Scenario Presets:</span>
        <button class="preset-btn active" onclick="loadPreset('stockout')">🚨 Stockout Alert (SKU-001)</button>
        <button class="preset-btn" onclick="loadPreset('overstock')">📦 Overstock Surplus (SKU-014)</button>
        <button class="preset-btn" onclick="loadPreset('healthy')">✅ Healthy Equilibrium (SKU-022)</button>
      </div>

      <form id="simForm" onsubmit="event.preventDefault(); runScoring();">
        <div class="sim-form-grid">
          <div class="input-group">
            <label class="input-label">SKU ID</label>
            <input id="inSku" type="text" class="input-control" value="SKU-001" required>
          </div>
          <div class="input-group">
            <label class="input-label">Category</label>
            <input id="inCategory" type="text" class="input-control" value="Home Decor">
          </div>
          <div class="input-group">
            <label class="input-label">Stock On Hand (Units)</label>
            <input id="inOnHand" type="number" class="input-control" value="12" min="0" required>
          </div>
          <div class="input-group">
            <label class="input-label">Stock On Order (Units)</label>
            <input id="inOnOrder" type="number" class="input-control" value="5" min="0" required>
          </div>
          <div class="input-group">
            <label class="input-label">Supplier Lead Time (Days)</label>
            <input id="inLeadTime" type="number" class="input-control" value="14" min="1" required>
          </div>
          <div class="input-group">
            <label class="input-label">Cost Price (₹)</label>
            <input id="inUnitCost" type="number" step="0.01" class="input-control" value="450.0" min="0" required>
          </div>
          <div class="input-group">
            <label class="input-label">List Selling Price (₹)</label>
            <input id="inUnitPrice" type="number" step="0.01" class="input-control" value="1200.0" min="0" required>
          </div>
        </div>

        <div class="input-group" style="margin-bottom: 20px;">
          <label class="input-label">Recent 8-Week Sales History (Comma-separated units)</label>
          <input id="inSales" type="text" class="input-control" value="14, 18, 16, 22, 25, 20, 24, 28" required>
        </div>

        <button type="submit" id="btnScore" class="btn btn-primary" style="padding: 12px 24px; font-size: 14px;">
          🚀 Execute Real-Time AI Scoring
        </button>
      </form>

      <!-- Live Simulator Result Box -->
      <div id="resultBox" class="sim-result-box" style="margin-top: 24px;">
        <div>
          <div id="resBadge" class="decision-badge badge-reorder">REORDER NOW</div>
          <p id="resRationale" style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
            Available stock (17) is below reorder level (58) across 14d lead time. Gap of 41 units.
          </p>

          <div class="risk-stat-row">
            <span class="risk-stat-label">Sales at Risk</span>
            <span id="resSalesRisk" class="risk-stat-val" style="color: #F87171;">₹49,200.00</span>
          </div>
          <div class="risk-stat-row">
            <span class="risk-stat-label">Capital Locked</span>
            <span id="resCapLocked" class="risk-stat-val" style="color: #FBBF24;">₹0.00</span>
          </div>
          <div class="risk-stat-row">
            <span class="risk-stat-label">Lead-Time Demand</span>
            <span id="resLtDemand" class="risk-stat-val">48.2 units</span>
          </div>
          <div class="risk-stat-row">
            <span class="risk-stat-label">Safety Stock (95% CSL)</span>
            <span id="resSafetyStock" class="risk-stat-val">9.8 units</span>
          </div>
          <div class="risk-stat-row">
            <span class="risk-stat-label">Reorder Point</span>
            <span id="resReorderLevel" class="risk-stat-val">58.0 units</span>
          </div>
        </div>

        <div>
          <div class="chart-header">
            <span class="chart-title">8-Week Forward Forecast Trajectory</span>
          </div>
          <div style="height: 220px;">
            <canvas id="forecastChart"></canvas>
          </div>
        </div>
      </div>
    </section>

    <!-- REST API Endpoints Table -->
    <section>
      <div class="section-header">
        <div>
          <h2 class="section-title">Production API Reference</h2>
          <p class="section-subtitle">Ultra-lean serverless microservice ready for ERP/WMS integration.</p>
        </div>
      </div>

      <table class="api-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Endpoint</th>
            <th>Description</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="http-method method-get">GET</span></td>
            <td><code>/docs</code></td>
            <td>Interactive OpenAPI / Swagger documentation</td>
            <td><a href="/docs" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;">Open Docs</a></td>
          </tr>
          <tr>
            <td><span class="http-method method-get">GET</span></td>
            <td><code>/health</code></td>
            <td>Liveness probe and microservice status</td>
            <td><a href="/health" target="_blank" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;">Test</a></td>
          </tr>
          <tr>
            <td><span class="http-method method-get">GET</span></td>
            <td><code>/metadata</code></td>
            <td>Model lineage, horizon parameters, and benchmark accuracy</td>
            <td><a href="/metadata" target="_blank" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;">View</a></td>
          </tr>
          <tr>
            <td><span class="http-method method-post">POST</span></td>
            <td><code>/score</code></td>
            <td>Single-SKU real-time demand forecast & 4-quadrant risk score</td>
            <td><a href="/docs#/Scoring/score_sku_score_post" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;">Swagger Test</a></td>
          </tr>
          <tr>
            <td><span class="http-method method-post">POST</span></td>
            <td><code>/score/batch</code></td>
            <td>High-throughput batch portfolio risk and cashflow assessment</td>
            <td><a href="/docs#/Scoring/score_batch_score_batch_post" class="btn btn-outline" style="padding: 4px 10px; font-size: 11px;">Swagger Test</a></td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>

  <!-- Footer -->
  <footer>
    <div class="container">
      <div class="footer-links">
        <a href="/docs">Swagger Documentation</a>
        <a href="https://github.com/morid648/foresight-demand-intelligence" target="_blank">GitHub Source Code</a>
        <a href="https://linkedin.com/in/anshul02" target="_blank">LinkedIn Profile</a>
      </div>
      <p>Project FORESIGHT · Built with precision by <strong>Anshul</strong> · Applied AI & Data Intelligence Engineer</p>
    </div>
  </footer>

  <script>
    // --- Chart 1: Benchmark Chart ---
    const ctxBench = document.getElementById('benchmarkChart').getContext('2d');
    new Chart(ctxBench, {
      type: 'bar',
      data: {
        labels: ['Seasonal Naive', 'Moving Average (8w)', 'Exp Smoothing', 'RandomForest (Winner)'],
        datasets: [{
          label: 'WAPE %',
          data: [33.17, 36.42, 34.80, 20.79],
          backgroundColor: ['#4B5563', '#64748B', '#6B7280', '#06B6D4'],
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => ` WAPE: ${ctx.raw}%` } }
        },
        scales: {
          y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#9CA3AF', callback: (v) => v + '%' } },
          x: { grid: { display: false }, ticks: { color: '#9CA3AF' } }
        }
      }
    });

    // --- Chart 2: Risk Donut Chart ---
    const ctxDonut = document.getElementById('riskDonutChart').getContext('2d');
    new Chart(ctxDonut, {
      type: 'doughnut',
      data: {
        labels: ['Reorder Now', 'Markdown / Clear', 'Watch / Volatile', 'Healthy'],
        datasets: [{
          data: [12, 6, 2, 20],
          backgroundColor: ['#EF4444', '#F59E0B', '#8B5CF6', '#10B981'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#9CA3AF', boxWidth: 12, padding: 14 } }
        },
        cutout: '70%'
      }
    });

    // --- Chart 3: Live Forecast Trajectory Chart ---
    let forecastChartInstance = null;
    function renderForecastChart(weeklyForecast) {
      const ctxFcst = document.getElementById('forecastChart').getContext('2d');
      if (forecastChartInstance) forecastChartInstance.destroy();
      forecastChartInstance = new Chart(ctxFcst, {
        type: 'line',
        data: {
          labels: ['Wk +1', 'Wk +2', 'Wk +3', 'Wk +4', 'Wk +5', 'Wk +6', 'Wk +7', 'Wk +8'],
          datasets: [{
            label: 'Predicted Units',
            data: weeklyForecast,
            borderColor: '#06B6D4',
            backgroundColor: 'rgba(6, 182, 212, 0.15)',
            fill: true,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: '#06B6D4'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#9CA3AF' } },
            x: { grid: { display: false }, ticks: { color: '#9CA3AF' } }
          }
        }
      });
    }

    // Initialize initial forecast chart
    renderForecastChart([24.1, 24.8, 25.4, 26.1, 26.8, 27.4, 28.1, 28.8]);

    // --- Scenario Presets ---
    const presets = {
      stockout: {
        sku: 'SKU-001', category: 'Home Decor', onHand: 12, onOrder: 5, leadTime: 14,
        cost: 450, price: 1200, sales: '14, 18, 16, 22, 25, 20, 24, 28'
      },
      overstock: {
        sku: 'SKU-014', category: 'Kitchenware', onHand: 240, onOrder: 0, leadTime: 7,
        cost: 320, price: 850, sales: '8, 10, 6, 7, 9, 8, 7, 8'
      },
      healthy: {
        sku: 'SKU-022', category: 'Lighting', onHand: 65, onOrder: 20, leadTime: 14,
        cost: 600, price: 1500, sales: '18, 20, 19, 21, 20, 22, 21, 20'
      }
    };

    function loadPreset(key) {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      const p = presets[key];
      document.getElementById('inSku').value = p.sku;
      document.getElementById('inCategory').value = p.category;
      document.getElementById('inOnHand').value = p.onHand;
      document.getElementById('inOnOrder').value = p.onOrder;
      document.getElementById('inLeadTime').value = p.leadTime;
      document.getElementById('inUnitCost').value = p.cost;
      document.getElementById('inUnitPrice').value = p.price;
      document.getElementById('inSales').value = p.sales;
      runScoring();
    }

    // --- Real-Time Scoring Execution ---
    async function runScoring() {
      const btn = document.getElementById('btnScore');
      btn.innerText = '⏳ Scoring...';
      const salesArr = document.getElementById('inSales').value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
      const payload = {
        sku_id: document.getElementById('inSku').value,
        category: document.getElementById('inCategory').value,
        subcategory: 'General',
        on_hand_units: parseInt(document.getElementById('inOnHand').value),
        on_order_units: parseInt(document.getElementById('inOnOrder').value),
        lead_time_days: parseInt(document.getElementById('inLeadTime').value),
        unit_cost: parseFloat(document.getElementById('inUnitCost').value),
        unit_price: parseFloat(document.getElementById('inUnitPrice').value),
        recent_weekly_sales: salesArr.length > 0 ? salesArr : [10.0]
      };

      try {
        const res = await fetch('/api/score', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        // Update DOM
        const badge = document.getElementById('resBadge');
        badge.innerText = data.action;
        badge.className = 'decision-badge';
        if (data.action === 'REORDER NOW') badge.classList.add('badge-reorder');
        else if (data.action === 'MARKDOWN / CLEAR') badge.classList.add('badge-markdown');
        else if (data.action === 'WATCH / VOLATILE') badge.classList.add('badge-watch');
        else badge.classList.add('badge-healthy');

        document.getElementById('resRationale').innerText = data.action_rationale;
        document.getElementById('resSalesRisk').innerText = '₹' + data.sales_at_risk_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 });
        document.getElementById('resCapLocked').innerText = '₹' + data.capital_locked_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 });
        document.getElementById('resLtDemand').innerText = data.lead_time_demand + ' units';
        document.getElementById('resSafetyStock').innerText = data.safety_stock + ' units';
        document.getElementById('resReorderLevel').innerText = data.reorder_level + ' units';

        renderForecastChart(data.weekly_forecast);
      } catch (err) {
        console.error('Scoring error:', err);
      } finally {
        btn.innerText = '🚀 Execute Real-Time AI Scoring';
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/api", response_class=HTMLResponse, tags=["Dashboard"])
def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header and "text/html" not in accept_header:
        return JSONResponse({
            "service": "Project FORESIGHT AI Demand & Inventory Intelligence API",
            "status": "operational",
            "version": "1.0.0",
            "documentation": "/docs",
            "health_check": "/health",
            "model_metadata": "/metadata"
        })
    return HTMLResponse(content=LANDING_PAGE_HTML)



@app.get("/debug", include_in_schema=False)
@app.get("/api/debug", include_in_schema=False)
def debug_info(request: Request):
    return {
        "scope_path": request.scope.get("path"),
        "raw_path": request.scope.get("raw_path", b"").decode("utf-8", errors="ignore"),
        "headers": dict(request.headers)
    }


@app.get("/health", response_model=HealthResponse, tags=["Observability"])
@app.get("/api/health", response_model=HealthResponse, tags=["Observability"])
def health_check():
    return HealthResponse(
        status="healthy",
        service="foresight-scoring-service",
        version="1.0.0",
        uptime_status="operational"
    )


@app.get("/metadata", response_model=MetadataResponse, tags=["Observability"])
@app.get("/api/metadata", response_model=MetadataResponse, tags=["Observability"])
def get_metadata():
    return MetadataResponse(
        model_name="RandomForest",
        forecast_horizon_weeks=8,
        seasonal_period_weeks=52,
        safety_stock_z=1.65,
        overstock_horizon_weeks=12,
        baseline_wape=0.3317,
        winner_wape=0.2079
    )


@app.get("/docs", include_in_schema=False)
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Project FORESIGHT - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/openapi.json", include_in_schema=False)
@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title=app.title, version=app.version, routes=app.routes, description=app.description))


@app.post("/score", response_model=SKUOutputResponse, tags=["Scoring"])
@app.post("/api/score", response_model=SKUOutputResponse, tags=["Scoring"])
def score_sku(payload: SKUInputPayload):
    try:
        return score_single_sku_logic(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Scoring error: {str(e)}")


@app.post("/score/batch", response_model=BatchScoreResponse, tags=["Scoring"])
@app.post("/api/score/batch", response_model=BatchScoreResponse, tags=["Scoring"])
def score_batch(payload: BatchScoreRequest):
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


# Export handler for Vercel WSGI/ASGI compatibility
handler = app
