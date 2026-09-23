# Visual Evidences & UI Screenshots — Project FORESIGHT

This directory contains real, live visual evidence captured from the running **Streamlit Operations Planning Dashboard** and the **FastAPI Scoring Microservice**.

---

## 📸 Screenshot 1: Executive Overview & Planning Queue
**File:** [`01_dashboard_kpis_and_queue.png`](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/01_dashboard_kpis_and_queue.png)

### Key UI Elements Shown:
- **Top Header:** System title and live pipeline status badge (`● Production Pipeline Live`).
- **Sidebar Filters:** Operational category filter (`All Categories`), active SKU count (`40 / 40`), active production model (`RandomForest`), and forecast horizon (`8 Weeks`).
- **Top 5 Executive KPI Cards:**
  1. **SKUs Assessed:** 40 total SKUs evaluated across an 8-week planning horizon.
  2. **Forecast WAPE:** Model accuracy comparison vs the Seasonal-Naive benchmark.
  3. **Sales at Risk (₹):** Real-time rupee exposure due to projected stockouts across the portfolio.
  4. **Capital Locked (₹):** Working capital tied up in excess overstocked inventory.
  5. **Urgent Actions:** Total immediate operational action items (Reorders + Markdowns).
- **Interactive Operations Planning Queue:**
  - Tab filters: `All SKUs (40)`, `🔴 Reorder Now (10)`, `🟡 Markdown / Clear (9)`, `🟣 Watch / Volatile (0)`, `🟢 Healthy (21)`.
  - Sortable operational table displaying SKU ID, Category, Subcategory, 8W Demand Forecast, Stock on Hand, Stock on Order, Supplier Lead Time, Stockout Gap, and ₹ Sales at Risk.
  - CSV Export Button: `📥 Export Planning Queue to CSV`.

---

## 📸 Screenshot 2: Risk Decision Grid & Action Quadrants
**File:** [`02_decision_grid_and_actions.png`](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/02_decision_grid_and_actions.png)

### Key UI Elements Shown:
- **2D Risk Decision Grid (Scatter Plot):**
  - **X-Axis:** Overstock Risk Score (normalized excess stock above 12-week forward demand).
  - **Y-Axis:** Stockout Risk Score (normalized stockout gap during lead time).
  - **Bubble Size:** Proportional to total financial exposure in Indian Rupees (₹).
  - **Color-Coded Quadrants:**
    - `REORDER NOW` (Red): High stockout risk requiring immediate purchase order.
    - `MARKDOWN / CLEAR` (Yellow/Light Blue): High overstock requiring promotional discount.
    - `HEALTHY` (Green/Blue): Balanced stock safely covering demand and safety buffer.

---

## 📸 Screenshot 3: SKU Demand Trajectory Drilldown
**File:** [`03_sku_trajectory_drilldown.png`](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/03_sku_trajectory_drilldown.png)

### Key UI Elements Shown:
- **SKU Selector:** Allows deep-dive operational inspection for any individual item (e.g. `NB-BAT-BAT-035`).
- **Demand Trajectory Line Chart:** Visualizes historical weekly actuals alongside the 8-week production model forecast curve.
- **Operational Status Panel:**
  - Status Badge (`HEALTHY`, `REORDER NOW`, `MARKDOWN / CLEAR`).
  - Transparent Human-Readable Decision Rationale.
  - Physical stock on hand, stock on order, supplier lead time (days), safety stock buffer (units), and total 8-week forecasted units.
  - Highlighted alerts for ₹ Sales at Risk or ₹ Capital Locked.
- **Model Transparency & Backtest Integrity:** Benchmark comparison table showing WAPE and Bias across `Seasonal_Naive`, `Ridge_Linear`, `HistGradientBoosting`, and `RandomForest` (`🏆 WINNER / DEPLOYED`).

---

## 📸 Screenshot 4: FastAPI Swagger Microservice Documentation
**File:** [`04_fastapi_swagger_docs.png`](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/04_fastapi_swagger_docs.png)

### Key API Capabilities Shown:
- **Service Identity:** Project FORESIGHT Scoring Service (`v1.0.0`, OpenAPI 3.1).
- **Observability Endpoints:**
  - `GET /health` — Service health and model status check.
  - `GET /metadata` — Model version, parameters ($Z=1.65, H=8$), and benchmark WAPE.
- **Production Scoring Endpoints:**
  - `POST /score` — Real-time single SKU forecast and risk scoring.
  - `POST /score/batch` — Bulk SKU batch scoring for enterprise ERP/WMS integration.
- **Validated Pydantic Schemas:** `SKUInputPayload`, `SKUOutputResponse`, `BatchScoreRequest`, `BatchScoreResponse`.
