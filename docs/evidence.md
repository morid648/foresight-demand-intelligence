# Evidence Register — Project FORESIGHT

**Project:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Client:** NorthBay Living  
**Last Updated:** 2026-09-23  

---

## 1. Source-of-Truth Matrix

| Item | Evidence Source | Status | Verified Value / Notes |
|---|---|---|---|
| Source Dataset Paths | Filesystem check (`data/sample/`) | `[x] VERIFIED` | High-fidelity test fixture dataset in `data/sample/` |
| Table Schemas | Zidio Brief / `src/schemas.py` | `[x] VERIFIED` | `sales_daily`, `sku_master`, `calendar`, `inventory_snapshots` |
| Raw Row Counts | `src/validation.py` | `[x] VERIFIED` | 25,893 sales transactions, 40 SKUs, 731 dates, 40 inventory snapshots |
| Weekly Panel Observations | `src/pipeline.py` | `[x] VERIFIED` | 3,741 weekly panel records across 40 SKUs |
| Baseline Benchmark WAPE | `artifacts/metrics.json` | `[x] VERIFIED` | **33.17%** (Seasonal-Naive $t-52$) |
| Model Winner WAPE | `artifacts/metrics.json` | `[x] VERIFIED` | **20.79%** (RandomForest Regressor) |
| Model Improvement | Backtest Evaluation | `[x] VERIFIED` | **+37.3% relative improvement** over baseline |
| Automated Test Suite | `pytest tests/` | `[x] VERIFIED` | **23 passed in 2.89s** (100% success rate) |
| Dashboard Interface | `app/streamlit_app.py` | `[x] VERIFIED` | Executive KPIs, Planning Queue, 2D Grid, SKU Visualizer |
| Scoring API Service | `service/main.py` | `[x] VERIFIED` | `/health`, `/metadata`, `/score`, `/score/batch` with verified parity |
| Container Config | `Dockerfile` | `[x] VERIFIED` | Dockerfile and `.streamlit/config.toml` generated |

---

## 2. Verified Facts & Empirical Audit Log

1. **2026-09-23**: Initialized complete project directory structure (`src/`, `data/`, `app/`, `service/`, `tests/`, `reports/`, `docs/`, `artifacts/`).
2. **2026-09-23**: Executed deterministic data cleaning rules CLN-01 to CLN-05; resolved negative sales and duplicate records; generated `reports/data_quality.md`.
3. **2026-09-23**: Conducted multi-fold expanding-window rolling-origin cross-validation backtest across 4 folds.
4. **2026-09-23**: Validated that `RandomForest` won with aggregate WAPE = **20.79%** vs `Seasonal_Naive` baseline WAPE = **33.17%**; beats baseline condition confirmed.
5. **2026-09-23**: Verified numerical scoring parity between FastAPI microservice and Streamlit dashboard core logic.
6. **2026-09-23**: Executed 23 automated unit, component, and integration tests with zero failures.
