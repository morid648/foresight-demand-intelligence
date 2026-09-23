"""
Unit and integration tests for FastAPI scoring service endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from service.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "foresight-scoring-service"


def test_metadata_endpoint():
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert data["forecast_horizon_weeks"] == 8


def test_score_single_sku_reorder_endpoint():
    payload = {
        "sku_id": "NB-HOM-VAS-001",
        "category": "Home Decor",
        "subcategory": "Vases",
        "on_hand_units": 5,
        "on_order_units": 0,
        "lead_time_days": 21,
        "unit_cost": 450.0,
        "unit_price": 1200.0,
        "recent_weekly_sales": [15.0, 18.0, 20.0, 22.0, 19.0, 25.0, 30.0, 28.0]
    }
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sku_id"] == "NB-HOM-VAS-001"
    assert data["action"] == "REORDER NOW"
    assert len(data["weekly_forecast"]) == 8
    assert data["sales_at_risk_inr"] > 0


def test_score_batch_endpoint():
    payload = {
        "skus": [
            {
                "sku_id": "NB-BED-DUV-002",
                "category": "Bedding",
                "subcategory": "Duvets",
                "on_hand_units": 400,
                "on_order_units": 0,
                "lead_time_days": 14,
                "unit_cost": 800.0,
                "unit_price": 2000.0,
                "recent_weekly_sales": [5.0, 4.0, 6.0, 5.0]
            },
            {
                "sku_id": "NB-KIT-DIN-003",
                "category": "Kitchen & Dining",
                "subcategory": "Dinnerware",
                "on_hand_units": 50,
                "on_order_units": 20,
                "lead_time_days": 14,
                "unit_cost": 300.0,
                "unit_price": 800.0,
                "recent_weekly_sales": [10.0, 12.0, 11.0, 10.0]
            }
        ]
    }
    response = client.post("/score/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_skus_assessed"] == 2
    assert len(data["results"]) == 2
    assert data["total_capital_locked_inr"] > 0
