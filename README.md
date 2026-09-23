# 📦 Project FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/tests-23%20passed-brightgreen.svg)]()

> **Client:** NorthBay Living (D2C Home & Lifestyle Brand)  
> **Core Outcome:** Weekly SKU-level demand forecasting, stockout & overstock risk intelligence, rupee financial exposure quantification, and actionable operations planning.

---

## 🚀 Key Highlights & Headline Metrics

- **Primary Forecast Metric (WAPE):** **20.79%** (RandomForest candidate) vs **33.17%** (Seasonal-Naive baseline benchmark) — **+37.3% relative accuracy improvement**.
- **Leakage-Proof Evaluation:** Multi-fold expanding rolling-origin cross-validation (4 folds, 8-week horizon) with strictly historical features.
- **Inventory Risk Intelligence:** 4-quadrant decision engine (`REORDER NOW`, `MARKDOWN / CLEAR`, `WATCH / VOLATILE`, `HEALTHY`) with safety buffers based on supplier lead times ($L$).
- **Rupee Impact Quantification:** Realized revenue exposure for stockout gaps ($\text{Gap} \times \text{Price}$) and tied-up working capital for excess overstock ($\text{Excess} \times \text{Cost}$).
- **Production-Ready Dual Interface:** Interactive operations Streamlit dashboard (`app/`) and real-time FastAPI microservice (`service/`) sharing the identical scoring engine core.

---

## 📊 Backtest Benchmark Summary

| Model Architecture | Aggregate WAPE | Forecast Bias | Aggregate MAPE | Backtest Decision |
|---|---|---|---|---|
| **Seasonal-Naive Baseline ($t-52$)** | **33.17%** | **+0.0035** | **44.82%** | Mandatory Benchmark |
| **Ridge Linear Regression** | 23.19% | -0.0286 | 32.14% | Candidate |
| **HistGradientBoosting** | 20.95% | -0.0017 | 28.56% | Candidate |
| **RandomForest Regressor** | **20.79%** | **-0.0081** | **27.91%** | 🏆 **Selected Production Winner** |

*All results verified across 4 temporal rolling-origin folds. Production winner beat baseline by >12 percentage points.*

---

## 🏛️ System Architecture

```text
  Raw Data Extracts (sales_daily, sku_master, calendar, inventory_snapshots)
                           │
                           ▼
  Data Pipeline (src/pipeline.py) ──► Validation & CLN-01..05 Cleaning Rules
                           │
                           ▼
  Analysis-Ready Weekly Panel (data/processed/weekly_panel.parquet)
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
  Forecasting Subsystem             Risk Subsystem (src/risk.py)
  • Time-safe lag & rolling stats   • Lead-time demand ($L$)
  • Rolling-origin backtest         • Safety stock buffer ($Z=1.65$)
  • Seasonal-naive benchmark        • 4-quadrant action classification
  • Candidate model selection       • Sales at risk & capital locked (₹)
           │                               │
           └───────────────┬───────────────┘
                           │
                           ▼
  Unified Scored Snapshot (artifacts/risk_snapshot.csv)
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
  Streamlit Planning UI             FastAPI Microservice
  (app/streamlit_app.py)            (service/main.py)
  • Executive KPI Cards             • GET  /health
  • Planning Action Queue           • GET  /metadata
  • 2D Risk Decision Grid           • POST /score
  • SKU Trajectory Drilldown        • POST /score/batch
```

---

## 🛠️ Quickstart & Local Setup

### 1. Environment Installation
```bash
# Clone the repository
git clone https://github.com/morid648/foresight-demand-intelligence.git
cd foresight-demand-intelligence

# Install dependencies
pip install -r requirements.txt
```

### 2. Single-Command Pipeline Execution
Run the full data pipeline to clean extracts, aggregate the weekly panel, train models, backtest, and generate risk snapshots:
```bash
# Execute end-to-end pipeline & risk generation
python -m src.pipeline
python -m src.generate_predictions_and_risk
```

### 3. Launch the Planning Dashboard
```bash
streamlit run app/streamlit_app.py
```
*Access dashboard in browser at `http://localhost:8501`.*

### 4. Launch the FastAPI Scoring Service
```bash
uvicorn service.main:app --host 0.0.0.0 --port 8000 --reload
```
*Interactive API Swagger documentation available at `http://localhost:8000/docs`.*

### 5. Run Test Suite
```bash
python -m pytest tests/ -v
```

---

## 📁 Repository Structure

```text
foresight_agent_specs/
├─ app/                         # Streamlit planning dashboard
│  ├─ components/               # UI components (KPIs, Queue, Grid, Visualizer)
│  ├─ streamlit_app.py          # Dashboard entrypoint
│  └─ styles.css                # Custom UI styles
├─ artifacts/                   # Generated metrics and scored tables
│  ├─ forecast_snapshot.csv     # 8-week SKU forward forecasts
│  ├─ metrics.json              # Verified backtest WAPE/Bias metrics
│  └─ risk_snapshot.csv         # Full 4-quadrant inventory risk table
├─ data/
│  ├─ processed/                # Analysis-ready weekly panel
│  ├─ raw/                      # Confidential client raw extracts
│  └─ sample/                   # High-fidelity test fixture data
├─ docs/
│  ├─ assumptions.md            # Documented business logic assumptions
│  ├─ decision_log.md           # Engineering & modeling decisions
│  └─ evidence.md               # Verified facts & source-of-truth matrix
├─ reports/
│  ├─ data_quality.md           # Automated data ingestion & cleaning profile
│  ├─ eda_memo.md               # Executive demand insight memo
│  ├─ executive_readout_outline.md # 8-slide presentation outline
│  └─ project_report.md         # Full project technical report
├─ service/                     # FastAPI scoring microservice
│  ├─ main.py                   # API routes (/health, /metadata, /score, /score/batch)
│  └─ schemas.py                # Pydantic request/response models
├─ src/                         # Core modular business logic
│  ├─ backtest.py               # Rolling-origin cross-validation
│  ├─ baseline.py               # Seasonal-Naive forecaster
│  ├─ config.py                 # Centralized configuration
│  ├─ features.py               # Time-safe feature engineering
│  ├─ forecast.py               # Candidate ML regressor pipelines
│  ├─ impact.py                 # Financial rupee calculations
│  ├─ io.py                     # Atomic file I/O utilities
│  ├─ logging_utils.py          # Structured production logger
│  ├─ metrics.py                # WAPE, Bias, and MAPE formulas
│  ├─ pipeline.py               # Data cleaning & weekly aggregation
│  ├─ risk.py                   # Inventory risk engine & action classifier
│  ├─ schemas.py                # Core Pydantic contracts
│  └─ validation.py             # Schema & integrity validation
├─ tests/                       # Complete pytest suite (23 unit & integration tests)
├─ Dockerfile                   # Containerized deployment config
└─ requirements.txt             # Python dependencies
```

---

## 🛡️ Non-Negotiable Anti-Hallucination & Integrity Principles
- **No Fabricated Performance:** All WAPE and Bias metrics are derived from executed rolling-origin CV backtest runs recorded in `artifacts/metrics.json`.
- **Honest Baseline Rule:** If candidate models lose to Seasonal-Naive, the baseline is deployed and documented.
- **Zero Future Leakage:** All feature extraction uses strictly $t \le T$ cutoff timestamps verified by `tests/test_features.py`.
- **Single Scoring Core:** The Streamlit dashboard and FastAPI service share identical underlying scoring functions to prevent metric drift.
