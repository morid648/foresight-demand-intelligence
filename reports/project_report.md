# Comprehensive Technical Project Report — Project FORESIGHT

**Project Name:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Target Client:** NorthBay Living  
**Version:** 1.0.0 (Production Release)  
**Date:** 2026-09-23  

---

## 1. Executive Summary
Project FORESIGHT delivers an end-to-end, production-grade demand forecasting and inventory risk intelligence system for NorthBay Living, a D2C home and lifestyle brand. By combining automated deterministic data cleaning, leakage-proof time-series feature engineering, rolling-origin cross-validation, and an explainable 4-quadrant inventory risk engine, FORESIGHT replaces error-prone spreadsheet planning with reliable, automated operations decision support.

Across extensive multi-fold temporal backtesting, the production **RandomForest Forecaster** achieved an aggregate **WAPE of 20.79%** (Bias: -0.0081), outperforming the mandatory **Seasonal-Naive baseline benchmark (WAPE: 33.17%)** by **+37.3% relative accuracy improvement**.

---

## 2. Ingestion Pipeline & Data Architecture
The data pipeline (`src/pipeline.py`) unifies four core tables (`sales_daily`, `sku_master`, `calendar`, `inventory_snapshots`) into a weekly SKU panel (`ISO week`, `sku_id`):

- **CLN-01 (String Normalization):** Strips leading/trailing whitespace and standardizes SKU IDs and category naming.
- **CLN-02 (Negative Return Handling):** Deterministically adjusts return/correction anomalies with audit logging.
- **CLN-03 (Duplicate Resolution):** Aggregates duplicate daily records for identical SKU/date pairs.
- **CLN-04 (Temporal Alignment):** Standardizes all timestamp fields to UTC/ISO format.
- **CLN-05 (Missing Value Handling):** Imputes non-promotional default flags (0, 'None').

---

## 3. Modeling Methodology & Backtest Verification
- **Target Variable:** Weekly units sold per SKU ($y_{i,t}$).
- **Feature Engineering:** Features computed strictly as-of historical cutoff $T$:
  - Lags: $t-1, t-2, t-4, t-8, t-52$
  - Rolling Stats: 4, 8, 12-week rolling mean and standard deviation on lagged values
  - Calendar & Seasonality: Sine/Cosine ISO week-of-year cyclical encoding, month, holiday flags
  - Promotional uplift: Active promo days, price ratios
- **Cross-Validation Strategy:** 4 expanding-window rolling-origin folds with 8-week forward horizons ($H=8$).

### Empirical Backtest Results
```text
Model Architecture       Aggregate WAPE    Bias         Aggregate MAPE    Status
-------------------------------------------------------------------------------------------------
Seasonal-Naive ($t-52$)  33.17%            +0.0035      44.82%            Baseline Benchmark
Ridge Linear             23.19%            -0.0286      32.14%            Candidate
HistGradientBoosting     20.95%            -0.0017      28.56%            Candidate
RandomForest Regressor   20.79%            -0.0081      27.91%            🏆 Selected Production Winner
```

---

## 4. Inventory Risk Engine & Financial Valuation
For each SKU, the risk engine (`src/risk.py`, `src/impact.py`) evaluates forward inventory dynamics:
1. **Lead-Time Demand:** Cumulative forecast over supplier replenishment window $L$.
2. **Safety Stock Buffer:** $Z \times \sigma_{\text{demand}} \times \sqrt{L/7}$ ($Z=1.65$ for 95% service level).
3. **Stockout Gap:** $\max(0, \text{Lead Time Demand} + \text{Safety Stock} - \text{Available Stock})$.
4. **Overstock Excess:** $\max(0, \text{Available Stock} - \text{Demand}_{12\text{W}} - \text{Safety Stock})$.
5. **Financial Exposure:**
   - $\text{Sales at Risk (₹)} = \text{Stockout Gap} \times \text{Unit Selling Price}$
   - $\text{Capital Locked (₹)} = \text{Excess Units} \times \text{Unit Cost}$

### 4-Quadrant Operational Action Mapping
- **REORDER NOW:** High stockout risk, low overstock risk. Direct replenishment trigger.
- **MARKDOWN / CLEAR:** Low stockout risk, high forward overstock. Working capital clearance trigger.
- **WATCH / VOLATILE:** High risk on both dimensions. Order realignment trigger.
- **HEALTHY:** Low risk on both dimensions. Stock safely within buffer parameters.

---

## 5. Software Delivery & Deployment Topology
- **Interactive UI Dashboard (`app/`):** Streamlit planning dashboard with KPI cards, sortable/filterable action queue with CSV export, 2D scatter decision grid, and single-SKU trajectory drilldowns.
- **Microservice API (`service/`):** FastAPI endpoints providing `/health`, `/metadata`, `/score`, and `/score/batch` sharing identical scoring logic with the UI.
- **Test Coverage (`tests/`):** 23 automated unit and integration tests passing with 100% success rate.
