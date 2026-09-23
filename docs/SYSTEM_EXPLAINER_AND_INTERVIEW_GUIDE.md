# Project FORESIGHT — Complete System Explainer & Interview Guide

**Platform Name:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Client / Domain:** NorthBay Living (D2C Home & Lifestyle)  
**Author:** Lead Software & Data Science Engineer  

---

# Table of Contents
1. [The Problem Statement & Business Context](#1-the-problem-statement--business-context)
2. [The Problem FORESIGHT Solves](#2-the-problem-foresight-solves)
3. [How the System Was Made (Architecture & Design Decisions)](#3-how-the-system-was-made-architecture--design-decisions)
4. [How the System Works (Step-by-Step Technical Flow)](#4-how-the-system-works-step-by-step-technical-flow)
5. [How to Use the System (User & Developer Guide)](#5-how-to-use-the-system-user--developer-guide)
6. [How to Explain This Project to Someone (Interview & Presentation Guide)](#6-how-to-explain-this-project-to-someone-interview--presentation-guide)
7. [Technical Defense & Common Interview Q&A](#7-technical-defense--common-interview-qa)

---

## 1. The Problem Statement & Business Context

### Client Scenario: NorthBay Living
NorthBay Living is a fast-growing Direct-to-Consumer (D2C) brand offering home decor, premium bedding, kitchenware, and bath essentials. Like many scaling retail brands, their operations planning relied heavily on **intuition, historical spreadsheets, and static reorder rules**.

### The "Dual Inventory Dilemma"
Spreadsheet planning created two simultaneous operational crises:
1. **Chronic Stockouts on Top-Sellers:** Best-selling SKUs experienced demand spikes during holiday and festive periods. By the time planners noticed low stock, supplier lead times (2–5 weeks) meant shelves went empty, resulting in lost revenue, degraded search rank, and frustrated customers.
2. **Capital Trapped in Overstocked Slow-Movers:** Long-tail or seasonal styles were repeatedly over-ordered, locking up tens of thousands of rupees in working capital in warehouses and incurring high carrying and obsolescence costs.

---

## 2. The Problem FORESIGHT Solves

Traditional machine learning projects stop at producing a Jupyter notebook with a forecast curve and an RMSE score. **Operations planners cannot make purchase orders from an RMSE score.**

FORESIGHT solves this by bridging the gap between time-series predictive modeling and daily merchandising execution:
- **Predicts Demand:** Produces weekly SKU-level forecasts over an 8-week forward planning horizon.
- **Translates Forecasts into Operational Actions:** Automatically classifies every SKU into one of 4 actionable quadrants: `REORDER NOW`, `MARKDOWN / CLEAR`, `WATCH / VOLATILE`, `HEALTHY`.
- **Quantifies Financial Exposure in Rupees ($₹$):** Computes exact **Sales at Risk** (unmet revenue exposure) and **Capital Locked** (tied-up COGS in excess stock).
- **Delivers Decision-First Interfaces:** Provides an interactive operations dashboard for non-technical planners and a high-throughput FastAPI microservice for ERP/WMS systems.

---

## 3. How the System Was Made (Architecture & Design Decisions)

```text
               +-------------------------------------------------------+
               |                 Raw Source Extracts                   |
               | sales_daily • sku_master • calendar • inventory_snaps |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |        Deterministic Data Pipeline (src/pipeline.py)  |
               | Ingest -> Validate -> Clean (CLN-01..05) -> Aggregate |
               +---------------------------+---------------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |     Weekly Analysis-Ready Panel (weekly_panel.parquet)|
               +---------------------------+---------------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
+------------------------------------+           +------------------------------------+
|  Forecasting Subsystem (src/)      |           |  Risk Engine Subsystem (src/)      |
| • Time-safe lag & rolling features |           | • Lead-time demand ($L$)           |
| • Rolling-origin CV (4 folds, 8W)  |           | • Safety buffer ($Z=1.65$)         |
| • Seasonal-Naive benchmark (t-52)  |           | • 4-Quadrant action classification |
| • ML Regressor selection           |           | • ₹ Sales-at-Risk & Capital-Locked |
+------------------+-----------------+           +------------------+-----------------+
                   |                                               |
                   +-----------------------+-----------------------+
                                           |
                                           v
               +-------------------------------------------------------+
               |      Unified Scored Artifacts (risk_snapshot.csv)     |
               +---------------------------+---------------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
+------------------------------------+           +------------------------------------+
|   Streamlit Operations Dashboard   |           |    FastAPI Scoring Microservice    |
|   (app/streamlit_app.py)           |           |    (service/main.py)               |
|   • Executive KPI metric cards     |           |    • GET  /health                  |
|   • Action planning queue & export |           |    • GET  /metadata                |
|   • 2D risk scatter decision grid  |           |    • POST /score                   |
|   • Single SKU demand visualizer   |           |    • POST /score/batch             |
+------------------------------------+           +------------------------------------+
```

### Key Engineering Decisions:
1. **Deterministic Data Cleaning (Rules CLN-01 to CLN-05):**
   - No silent modifications. String normalization, returns handling, duplicate aggregation, and date parsing are fully logged in `reports/data_quality.md`.
2. **Time-Safe Feature Engineering & Zero Leakage:**
   - Features (lags $t-1, t-2, t-4, t-8, t-52$, rolling stats over 4, 8, 12 weeks) are strictly computed as-of cutoff date $T$. No future actuals ever enter feature extraction.
3. **Mandatory Benchmark & Honest Comparison:**
   - A Seasonal-Naive ($t-52$ with moving median fallback) benchmark was implemented first. Candidate models must empirically beat the baseline on WAPE to earn production deployment.
4. **Volume-Weighted Metric (WAPE):**
   - Classical MAPE divides by $y_{true}$, which explodes or fails on zero-sales weeks common in D2C catalogs. WAPE ($\sum |y - \hat{y}| / \sum y$) weights error by total volume, providing a robust, scale-independent metric.
5. **Shared Scoring Engine Core:**
   - The Streamlit dashboard and FastAPI service import identical pure Python functions from `src/`, eliminating metric drift between UI and API.

---

## 4. How the System Works (Step-by-Step Technical Flow)

### Step 1: Ingestion & Validation (`src/validation.py`)
- Reads raw CSV extracts (`sales_daily`, `sku_master`, `calendar`, `inventory_snapshots`).
- Profiles row counts, checks required schemas, audits nulls, and validates 100% SKU coverage across tables.

### Step 2: Deterministic Cleaning & Weekly Aggregation (`src/pipeline.py`)
- Applies cleaning rules (CLN-01 to CLN-05).
- Aggregates daily transactions into continuous ISO-weekly panels per SKU.
- Joins SKU metadata (cost, list price) and latest inventory positions (on-hand, on-order, lead time).

### Step 3: Rolling-Origin Cross-Validation (`src/backtest.py`)
- Evaluates models across 4 expanding-window temporal folds over an 8-week horizon.
- Evaluates Seasonal-Naive ($t-52$), Ridge Linear Regression, HistGradientBoosting, and RandomForest Regressor.
- **Empirical Results:**
  - *Seasonal-Naive Baseline:* WAPE = **33.17%**, Bias = **+0.0035**
  - *Ridge Linear:* WAPE = **23.19%**, Bias = **-0.0286**
  - *HistGradientBoosting:* WAPE = **20.95%**, Bias = **-0.0017**
  - *RandomForest Regressor:* WAPE = **20.79%**, Bias = **-0.0081** (**🏆 Winner, +37.3% relative improvement**).

### Step 4: Inventory Risk Engine & Financial Valuation (`src/risk.py`, `src/impact.py`)
For each SKU:
- **Lead-Time Demand:** $\text{Demand}_L = \sum_{t=1}^{\lfloor L/7 \rfloor} \hat{y}_t + \text{fractional remainder}$.
- **Available Stock:** $\text{Available} = \text{On-Hand} + \text{On-Order}$.
- **Safety Stock Buffer:** $\text{Safety Stock} = Z \times \sigma_{\text{demand}} \times \sqrt{L/7}$ ($Z=1.65$ for 95% service level).
- **Reorder Level:** $\text{Reorder Level} = \text{Demand}_L + \text{Safety Stock}$.
- **Stockout Gap:** $\text{Gap}_{\text{stockout}} = \max(0, \text{Reorder Level} - \text{Available})$.
- **Overstock Excess:** $\text{Excess}_{\text{overstock}} = \max(0, \text{Available} - \text{Demand}_{12\text{W}} - \text{Safety Stock})$.
- **Financial Calculations:**
  - $\text{Sales at Risk (₹)} = \text{Stockout Gap} \times \text{Selling Price}$
  - $\text{Capital Locked (₹)} = \text{Excess Units} \times \text{Unit Cost}$

### Step 5: 4-Quadrant Operational Action Classification
- `REORDER NOW`: High stockout risk, low overstock risk. (Immediate supplier PO required).
- `MARKDOWN / CLEAR`: Low stockout risk, high forward overstock. (Promotional discount required).
- `WATCH / VOLATILE`: High risk on both dimensions. (Supply schedule realignment required).
- `HEALTHY`: Stock safely covers lead time and forward demand within buffer limits.

---

## 5. How to Use the System (User & Developer Guide)

### 1. Single-Command Pipeline Execution
To rerun data ingestion, cleaning, backtesting, and risk scoring from scratch:
```bash
python -m src.pipeline
python -m src.generate_predictions_and_risk
```

### 2. Launch the Streamlit Operations Dashboard
```bash
streamlit run app/streamlit_app.py
```
- Open `http://localhost:8501`.
- Review top KPI cards (Sales at Risk, Capital Locked, Forecast WAPE).
- Filter the Planning Queue by action tab (e.g. "Reorder Now") and export CSV for purchasing.
- Inspect the 2D Decision Grid scatter plot to identify high-exposure bubble clusters.
- Select any SKU in the visualizer to inspect historical actuals vs forward forecast trajectory.

### 3. Launch the FastAPI Microservice
```bash
uvicorn service.main:app --host 0.0.0.0 --port 8000 --reload
```
- Open interactive Swagger UI: `http://localhost:8000/docs`.
- **Sample Single SKU Request (`POST /score`):**
```json
{
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
```
- **Response:** Returns 8-week forecast array, lead-time demand, stockout gap, `REORDER NOW` action, and exact ₹ Sales at Risk.

### 4. Execute the Test Suite
```bash
python -m pytest tests/ -v
```
- Runs 23 unit, component, and integration tests across data validation, feature leakage, baseline logic, backtesting, risk math, and API parity.

---

## 6. How to Explain This Project to Someone (Interview & Presentation Guide)

### The 30-Second Elevator Pitch
> *"Project FORESIGHT is an end-to-end demand forecasting and inventory intelligence platform I engineered for a D2C home & lifestyle brand. It solves the classic retail challenge of stocking out on bestsellers while tying up working capital in slow-movers. I built a deterministic data pipeline, a time-safe machine learning forecaster that achieved a 20.79% WAPE (+37.3% better than seasonal benchmarks), and an inventory risk engine that translates predictions into actionable reorder queues and rupee financial exposure metrics."*

### The 2-Minute Technical Summary
> *"When building FORESIGHT, I focused on three core engineering pillars: rigor, explainability, and actionability.*  
> 
> *First, for predictive rigor, retail sales have heavy seasonality and zero-demand weeks. I chose WAPE as the primary metric and designed an expanding-window rolling-origin cross-validation engine. All features—lags, rolling stats, and Fourier seasonality—were strictly bounded by cutoff dates to guarantee zero future data leakage. My production RandomForest model achieved 20.79% WAPE, outperforming the mandatory Seasonal-Naive benchmark (33.17%).*  
> 
> *Second, for operational actionability, predictions alone don't help warehouse planners. I built a risk engine that computes lead-time demand, statistical safety buffers at 95% service levels, and 12-week overstock horizons. It categorizes every SKU into one of four action states: Reorder Now, Markdown / Clear, Watch, or Healthy, and values the exposure in Indian Rupees.*  
> 
> *Third, for software delivery, I created a dual-interface architecture: a Streamlit dashboard with 2D risk scatter grids and SKU trajectory charts, plus a high-performance FastAPI microservice with automated test suites verifying 100% numerical parity."*

---

## 7. Technical Defense & Common Interview Q&A

### Q1: Why did you choose WAPE instead of MAPE or RMSE?
**Answer:**  
In D2C retail, catalog demand is intermittent with frequent zero-sales weeks. Traditional MAPE ($\frac{1}{n}\sum \frac{|y - \hat{y}|}{y}$) divides by actual sales, causing division-by-zero or astronomical percentage errors on 1-unit sales. RMSE penalizes single large outliers heavily and is scale-dependent. WAPE ($\frac{\sum |y - \hat{y}|}{\sum y}$) volume-weights the absolute error across the entire catalog, accurately reflecting overall unit risk to the business.

### Q2: How did you ensure there was no data leakage in your time-series pipeline?
**Answer:**  
I implemented strict cutoff-date parameterization in `src/features.py`. Every feature (lags, rolling averages, promotional flags) for week $t$ is computed strictly using observations prior to $t-1$. In cross-validation, fold features are generated as-of each fold's historical cutoff. I backed this up with automated unit tests (`tests/test_features.py`) that intentionally inject future data corruptions and verify that historical feature vectors remain 100% invariant.

### Q3: What is the "Honest Baseline Rule" and why is it important?
**Answer:**  
Many data science projects jump straight to complex neural networks or gradient boosting without proving they beat a simple heuristic. In FORESIGHT, I established a Seasonal-Naive ($t-52$) benchmark first. The system policy mandates that if machine learning candidates fail to beat the baseline on rolling-origin WAPE, the system deploys the baseline and documents why. In our case, RandomForest achieved 20.79% WAPE vs 33.17% baseline, justifying deployment.

### Q4: How do you prevent metric drift between the UI and the API?
**Answer:**  
I decoupled all forecasting, risk classification, and financial calculation logic into pure Python modules in `src/`. Both the Streamlit dashboard (`app/`) and the FastAPI router (`service/`) import and execute these identical core functions. I verified this with an automated integration test (`tests/test_integration.py`) asserting exact floating-point equality between API responses and UI data structures.

### Q5: How is financial exposure calculated?
**Answer:**  
Sales at Risk ($₹$) represents potential lost revenue and is computed as $\max(0, \text{Stockout Gap}) \times \text{Selling Price}$. Capital Locked ($₹$) represents tied-up working capital in excess stock and is computed as $\max(0, \text{Excess Units}) \times \text{Cost of Goods Sold (COGS)}$. This gives finance and operations leads actionable rupee metrics.
