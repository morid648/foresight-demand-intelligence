# 📦 Project FORESIGHT — Executive Technical Project Report
## AI-Powered Demand Forecasting & Inventory Risk Intelligence Platform

**Target Client Context:** NorthBay Living (D2C Home & Lifestyle Brand)  
**Author:** Anshul ([LinkedIn](https://www.linkedin.com/in/anshul-chaudhary-508138308/) | [GitHub](https://github.com/morid648))  
**Repository:** [github.com/morid648/foresight-demand-intelligence](https://github.com/morid648/foresight-demand-intelligence)  
**Live Production API & Dashboard:** [foresight-demand-intelligence.vercel.app](https://foresight-demand-intelligence.vercel.app/)  
**Version:** 1.0.0 (Production Release) · **Test Coverage:** 23/23 Automated Tests Passing (100%)

---

## 1. Executive Summary & Problem Overview

### 1.1 Business Context
NorthBay Living operates a growing D2C portfolio of 40 active SKUs across 4 product categories (*Home Decor, Kitchenware, Furniture, Lighting*). Prior to Project FORESIGHT, the brand relied on static spreadsheet heuristics (e.g., 4-week trailing sales averages) for replenishment planning. This approach suffered from four systemic failure modes:
1. **Pervasive Stockouts on High-Velocity SKUs:** Supplier lead times (7 to 28 days) were frequently breached during seasonal sales surges, resulting in unfulfilled customer demand and lost revenue.
2. **Working Capital Trapped in Overstocked SKUs:** Long-tail items accumulated excessive stock beyond forward demand windows, straining working capital and driving margin erosion through forced markdowns.
3. **Spreadsheet Fragility & Zero Auditability:** Manual calculations lacked repeatable data cleaning, audit trails, and automated error tracking.
4. **Lack of Financial Exposure Prioritization:** Inventory alerts treated all SKUs equally rather than prioritizing purchase orders and markdowns by exact rupee (₹) financial impact.

### 1.2 The FORESIGHT Solution
Project FORESIGHT is an automated demand intelligence and inventory risk governance platform. It ingests daily transactional and inventory records, constructs a clean weekly panel dataset, generates multi-horizon weekly demand forecasts using machine learning with strict temporal boundaries, and applies an explainable 4-quadrant inventory risk engine to quantify financial exposure and output prioritized operational action queues.

```
+-----------------------------------------------------------------------------------------------+
|                                      PROJECT FORESIGHT IMPACT                                 |
+------------------------------+--------------------------------+-------------------------------+
|       20.79% WAPE            |      ₹1,21,115 SAVINGS         |       ₹1,27,990 RELEASED      |
|  +37.3% accuracy improvement |   Revenue at risk identified   | Working capital flagged in    |
|  over Seasonal-Naive baseline|  across 12 stockout-gap SKUs   |    6 overstock excess SKUs    |
+------------------------------+--------------------------------+-------------------------------+
```

---

## 2. Technology Stack & Infrastructure

The platform was built using a modern, production-grade Python data science and microservice architecture:

| Tier / Component | Technology | Version | Purpose & Rationale |
|---|---|---|---|
| **Core Runtime** | Python | `3.11+ / 3.12` | Type-annotated, modern Python ecosystem |
| **Data Processing** | Pandas, NumPy, PyArrow | `2.2+ / 1.26+` | High-performance vector operations & Parquet storage |
| **Machine Learning** | Scikit-Learn | `1.4+` | RandomForest, HistGradientBoosting, Ridge Regressors |
| **Microservice API** | FastAPI, Uvicorn, Pydantic v2 | `0.110+` | REST API, OpenAPI 3.0 docs, strict schema validation |
| **Operations UI** | Streamlit | `1.32+` | Interactive business planning & decision support dashboard |
| **Visual Analytics** | Plotly & Chart.js | `5.18+ / 4.4+` | Dynamic risk scatter matrices & forecast confidence bands |
| **Testing & CI** | Pytest, AnyIO | `8.0+` | 23 automated unit, integration, and parity test suites |
| **Cloud Deployment** | Vercel Serverless, Docker | Cloud Native | High-availability serverless deployment (<100ms response) |

---

## 3. End-to-End System Architecture

Project FORESIGHT implements a modular 5-stage architecture ensuring strict separation of concerns, complete reproducibility, and zero future data leakage:

```
[ Raw CSV Data Sources ]
  │  • sales_daily.csv (30k+ records)
  │  • sku_master.csv (40 SKUs metadata)
  │  • calendar.csv (Holidays, seasonality)
  │  • inventory_snapshots.csv (Stock & on-order)
  ▼
[ 1. Ingestion & Validation Pipeline (src/pipeline.py, src/validation.py) ]
  │  • CLN-01: String stripping & SKU normalization
  │  • CLN-02: Deterministic return/correction handling
  │  • CLN-03: Daily multi-order deduplication
  │  • CLN-04: ISO weekly panel aggregation (3,741 weekly records)
  │  • CLN-05: Promo missing flag imputation & type casting
  ▼
[ 2. Leakage-Free Feature Engineering (src/features.py) ]
  │  • Historical Lags: t-1, t-2, t-4, t-8, t-52
  │  • Rolling Window Statistics: 4, 8, 12-week mean & std on lagged values
  │  • Cyclical Seasonality: Sine/Cosine ISO week encodings
  │  • Commercial Context: Promotional indicators & price ratios
  ▼
[ 3. Modeling & Rolling-Origin Backtest Engine (src/forecast.py, src/backtest.py) ]
  │  • 4-Fold Expanding-Window Cross-Validation (Horizon H = 8 weeks)
  │  • Model Arena: Seasonal-Naive Baseline vs Ridge vs HistGB vs RandomForest
  │  • Evaluation Metrics: Volume-weighted WAPE, Directional Bias, MAPE
  ▼
[ 4. 4-Quadrant Risk & Financial Valuation Engine (src/risk.py, src/impact.py) ]
  │  • Lead-Time Demand ($LTD$) + Safety Stock ($SS$) via $Z=1.65$ (95% CSL)
  │  • Reorder Level ($ROL = LTD + SS$) & Stockout Gap ($\max(0, ROL - Stock)$)
  │  • 12-Week Overstock Forward Horizon & Excess Units Calculation
  │  • Financial Rupee Valuation: Sales at Risk (₹) & Capital Locked (₹)
  ▼
[ 5. Delivery Interfaces (Dual Production Topology) ]
  ├─► Streamlit Planning Dashboard (app/streamlit_app.py): Operations Planner UI
  └─► FastAPI Microservice (api/index.py): Real-time ERP/WMS Scoring Engine
```

---

## 4. Modeling Methodology & Empirical Backtest Results

### 4.1 Cross-Validation Strategy
To prevent temporal data leakage, standard random k-fold cross-validation was strictly prohibited. Instead, the backtesting engine (`src/backtest.py`) employs a **4-fold expanding-window rolling-origin evaluation** across a 52-week test regime:
- **Fold 1:** Train weeks 1–52 $\rightarrow$ Forecast weeks 53–60 ($H=8$)
- **Fold 2:** Train weeks 1–64 $\rightarrow$ Forecast weeks 65–72 ($H=8$)
- **Fold 3:** Train weeks 1–76 $\rightarrow$ Forecast weeks 77–84 ($H=8$)
- **Fold 4:** Train weeks 1–88 $\rightarrow$ Forecast weeks 89–96 ($H=8$)

### 4.2 Benchmark Model Performance Matrix

```
===================================================================================================
Model Architecture          Aggregate WAPE    Forecast Bias    Aggregate MAPE    Status
===================================================================================================
Seasonal-Naive Baseline (t-52)  33.17%           +0.0035          44.82%         Mandatory Baseline
Ridge Linear Regression         23.19%           -0.0286          32.14%         Candidate
HistGradientBoosting Regressor  20.95%           -0.0017          28.56%         Candidate
RandomForest Regressor          20.79%           -0.0081          27.91%         🏆 Production Winner
===================================================================================================
```

**Key Mathematical Insights:**
1. **Primary Metric Selection:** Weighted Absolute Percentage Error ($\text{WAPE} = \frac{\sum |y - \hat{y}|}{\sum y}$) was chosen as the primary decision metric to prevent distortion from zero-demand weeks that invalidate standard MAPE.
2. **Superior Accuracy:** The **RandomForest Regressor** achieved a **20.79% WAPE**, representing a **+37.3% relative accuracy gain** over the seasonal-naive benchmark.
3. **Unbiased Forecasts:** Forecast bias remained negligible ($\text{Bias} = -0.0081$), proving the model neither systematically under-forecasts (risking stockouts) nor over-forecasts (risking excess stock).

---

## 5. 4-Quadrant Inventory Risk & Financial Valuation Engine

### 5.1 Mathematical Formulations
For each SKU $i$ with lead time $L_i$ (days), unit selling price $P_i$, unit cost $C_i$, on-hand inventory $I_i$, and on-order stock $O_i$:

1. **Available Stock:**
   $$\text{StockAvailable}_i = I_i + O_i$$
2. **Lead-Time Demand ($LTD_i$):**
   $$LTD_i = \sum_{w=1}^{\lfloor L_i/7 \rfloor} \hat{y}_{i,w} + \left(\frac{L_i \pmod 7}{7}\right) \hat{y}_{i,\lfloor L_i/7 \rfloor + 1}$$
3. **Safety Stock ($SS_i$) at 95% Cycle Service Level ($Z = 1.65$):**
   $$SS_i = 1.65 \times \sigma_{i,\text{weekly}} \times \sqrt{\frac{L_i}{7}}$$
4. **Reorder Level ($ROL_i$):**
   $$ROL_i = LTD_i + SS_i$$
5. **Stockout Gap & Risk Score ($S_i$):**
   $$\text{Gap}_i = \max(0, ROL_i - \text{StockAvailable}_i), \quad S_i = \min\left(1.0, \frac{\text{Gap}_i}{ROL_i + \epsilon}\right)$$
6. **Overstock Excess & Risk Score ($O_i$):**
   $$\text{Demand}_{12\text{W}, i} = 12 \times \bar{\hat{y}}_i, \quad \text{Excess}_i = \max(0, \text{StockAvailable}_i - \text{Demand}_{12\text{W}, i} - SS_i), \quad O_i = \min\left(1.0, \frac{\text{Excess}_i}{\text{Demand}_{12\text{W}, i} + \epsilon}\right)$$

### 5.2 Financial Exposure Calculations
- **Sales at Risk (₹):** Total potential lost revenue from projected stockouts:
  $$\text{Sales at Risk}_i = \text{Gap}_i \times P_i$$
- **Capital Locked (₹):** Total working capital trapped in surplus inventory beyond 12 weeks:
  $$\text{Capital Locked}_i = \text{Excess}_i \times C_i$$

### 5.3 4-Quadrant Portfolio Risk Distribution

| Quadrant | Stockout Risk | Overstock Risk | SKUs Flagged | Operational Trigger & Action | Total Financial Exposure |
|---|---|---|---|---|---|
| 🔴 **REORDER NOW** | $\ge 0.50$ | $< 0.50$ | **12 SKUs** | Immediate purchase order issuance to supplier | **₹1,21,115 Sales at Risk** |
| 🟡 **MARKDOWN / CLEAR** | $< 0.50$ | $\ge 0.50$ | **6 SKUs** | Targeted promotional bundle / clearance markdown | **₹1,27,990 Capital Locked** |
| 🟣 **WATCH / VOLATILE** | $\ge 0.50$ | $\ge 0.50$ | **2 SKUs** | Lead time and replenishment schedule realignment | High Volatility Review |
| 🟢 **HEALTHY** | $< 0.50$ | $< 0.50$ | **20 SKUs** | Routine buffer monitoring; stock in equilibrium | Optimal Buffer |

---

## 6. Visual Interface & Application Screenshots

The platform includes a rich, two-tier visual layer for both human business planners and automated enterprise systems.

### Screenshot 1: Streamlit Dashboard — Executive KPIs & Priority Action Queue
![Dashboard KPIs and Action Queue](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/01_dashboard_kpis_and_queue.png)
*Figure 1: Executive KPI banner displaying portfolio health metrics alongside the sortable, filterable action table with one-click CSV export.*

---

### Screenshot 2: 2D Inventory Risk Decision Grid & Financial Breakdown
![Decision Grid and Actions](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/02_decision_grid_and_actions.png)
*Figure 2: Interactive 2D scatter matrix mapping Stockout Risk vs. Overstock Risk across the 4 operational quadrants, with category financial exposure charts.*

---

### Screenshot 3: Deep-Dive SKU Trajectory & Lead-Time Forecast Drilldown
![SKU Trajectory Drilldown](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/03_sku_trajectory_drilldown.png)
*Figure 3: Historical actuals versus 8-week forward forecast with dynamic lead-time demand threshold and safety buffer visualization.*

---

### Screenshot 4: Serverless FastAPI Microservice & OpenAPI Documentation
![FastAPI Swagger Docs](file:///g:/Data%20Analytics/19.Portfolio/foresight_agent_specs/screenshots/04_fastapi_swagger_docs.png)
*Figure 4: Production FastAPI Swagger UI (`/docs`) providing interactive schema exploration and real-time `/score` and `/score/batch` testing.*

---

## 7. Automated Test Suite & Quality Assurance

The codebase includes an extensive automated test suite covering edge cases, arithmetic correctness, and UI/API parity:

```bash
python -m pytest tests/ -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: G:\Data Analytics\19.Portfolio\foresight_agent_specs
configfile: pyproject.toml
collected 23 items

tests/test_backtest.py::test_rolling_cv_cutoffs_ordering PASSED          [  4%]
tests/test_backtest.py::test_rolling_backtest_execution PASSED           [  8%]
tests/test_baseline.py::test_wape_exact_calculation PASSED               [ 13%]
tests/test_baseline.py::test_wape_zero_actuals PASSED                    [ 17%]
tests/test_baseline.py::test_bias_direction PASSED                       [ 21%]
tests/test_baseline.py::test_seasonal_naive_with_sufficient_history PASSED [ 26%]
tests/test_baseline.py::test_seasonal_naive_short_history_fallback PASSED [ 30%]
tests/test_features.py::test_no_future_leakage_on_cutoff PASSED          [ 34%]
tests/test_features.py::test_inference_features_structure PASSED         [ 39%]
tests/test_integration.py::test_full_pipeline_artifacts_exist PASSED     [ 43%]
tests/test_integration.py::test_ui_and_api_scoring_parity PASSED         [ 47%]
tests/test_pipeline.py::test_validation_profiling PASSED                 [ 52%]
tests/test_pipeline.py::test_validation_critical_missing_column PASSED   [ 56%]
tests/test_pipeline.py::test_deterministic_cleaning_rules PASSED         [ 60%]
tests/test_pipeline.py::test_weekly_panel_aggregation PASSED             [ 65%]
tests/test_risk.py::test_reorder_now_quadrant PASSED                     [ 69%]
tests/test_risk.py::test_markdown_clear_quadrant PASSED                  [ 73%]
tests/test_risk.py::test_healthy_quadrant PASSED                         [ 78%]
tests/test_risk.py::test_financial_impact_arithmetic PASSED              [ 82%]
tests/test_service.py::test_health_endpoint PASSED                       [ 86%]
tests/test_service.py::test_metadata_endpoint PASSED                     [ 91%]
tests/test_service.py::test_score_single_sku_reorder_endpoint PASSED     [ 95%]
tests/test_service.py::test_score_batch_endpoint PASSED                  [100%]

============================= 23 passed in 3.10s ==============================
```

---

## 8. Conclusion & Business Impact

Project FORESIGHT demonstrates how modern machine learning and deterministic supply chain heuristics can transform retail inventory planning:

1. **Quantifiable Financial Value:** Identifies **₹1,21,115 in preventable lost revenue** from stockout gaps and flags **₹1,27,990 in working capital** to be unlocked through targeted markdowns.
2. **Operational Efficiency:** Eliminates manual spreadsheet friction by delivering automated, daily/weekly actionable decision queues with clear human-interpretable rationales.
3. **Engineering Rigor:** Built with 100% test pass rate, strict temporal leakage prevention, and dual production interfaces (Streamlit + FastAPI) deployed to serverless cloud infrastructure.

---

### Author Contact Information
- **Lead Engineer:** Anshul
- **LinkedIn:** [https://www.linkedin.com/in/anshul-chaudhary-508138308/](https://www.linkedin.com/in/anshul-chaudhary-508138308/)
- **GitHub Repository:** [https://github.com/morid648/foresight-demand-intelligence](https://github.com/morid648/foresight-demand-intelligence)
- **Live Deployment:** [https://foresight-demand-intelligence.vercel.app/](https://foresight-demand-intelligence.vercel.app/)
