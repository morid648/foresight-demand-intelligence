"""
End-to-End Integration and System Tests for Project FORESIGHT.
Verifies pipeline execution, model scoring, risk generation, and parity between UI and API calculations.
"""

import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.config import config
from src.io import load_dataframe, load_json
from src.risk import compute_sku_risk_profile
from service.main import app, score_single_sku_logic
from service.schemas import SKUInputPayload

client = TestClient(app)


def test_full_pipeline_artifacts_exist():
    """Verifies that all required production artifacts are present and well-formed."""
    panel_path = config.DATA_PROCESSED_DIR / "weekly_panel.parquet"
    risk_path = config.ARTIFACTS_DIR / "risk_snapshot.csv"
    metrics_path = config.ARTIFACTS_DIR / "metrics.json"

    assert panel_path.exists(), "Processed weekly panel missing"
    assert risk_path.exists(), "Risk snapshot missing"
    assert metrics_path.exists(), "Metrics JSON missing"

    panel_df = load_dataframe(panel_path)
    risk_df = pd.read_csv(risk_path)
    metrics = load_json(metrics_path)

    assert len(panel_df) > 0
    assert len(risk_df) == panel_df["sku_id"].nunique()
    assert "winner" in metrics
    assert "models" in metrics
    assert metrics["beats_baseline"] is True


def test_ui_and_api_scoring_parity():
    """Verifies that API score endpoint produces identical numbers to the core risk engine."""
    payload = SKUInputPayload(
        sku_id="TEST_PARITY_SKU",
        category="Bedding",
        subcategory="Duvets",
        on_hand_units=20,
        on_order_units=10,
        lead_time_days=14,
        unit_cost=500.0,
        unit_price=1500.0,
        recent_weekly_sales=[12.0, 14.0, 16.0, 15.0, 18.0, 20.0, 22.0, 25.0]
    )

    # 1. API Call
    api_response = client.post("/score", json=payload.model_dump())
    assert api_response.status_code == 200
    api_data = api_response.json()

    # 2. Direct Logic Call
    direct_res = score_single_sku_logic(payload)

    # Parity assertions
    assert api_data["sku_id"] == direct_res.sku_id
    assert api_data["action"] == direct_res.action
    assert api_data["lead_time_demand"] == direct_res.lead_time_demand
    assert api_data["stockout_gap_units"] == direct_res.stockout_gap_units
    assert api_data["overstock_excess_units"] == direct_res.overstock_excess_units
    assert api_data["sales_at_risk_inr"] == direct_res.sales_at_risk_inr
    assert api_data["capital_locked_inr"] == direct_res.capital_locked_inr
