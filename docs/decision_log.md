# Decision Log — Project FORESIGHT

**Project:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Client:** NorthBay Living  

---

## Technical & Modeling Decision Entries

### DEC-001: Architecture Layering & Shared Scoring Core
- **Date:** 2026-09-23
- **Context:** PRD and Architecture require both a Streamlit operations dashboard and a FastAPI scoring service.
- **Decision:** Implement all feature engineering (`src/features.py`), model inference (`src/forecast.py`), risk scoring (`src/risk.py`), and impact calculations (`src/impact.py`) in `src/` as pure, modular Python functions. Both Streamlit (`app/`) and FastAPI (`service/`) import and execute these identical core functions.
- **Alternatives Rejected:** Duplicate scoring logic in Streamlit components or FastAPI routers (causes metric drift and maintenance overhead).
- **Impact:** Guarantees zero divergence in numbers between the UI dashboard and the API endpoints.

### DEC-002: Cross-Validation Strategy (Rolling-Origin Evaluation)
- **Date:** 2026-09-23
- **Context:** Demand forecasting models must be evaluated without temporal leakage. Random $k$-fold cross-validation is forbidden for time-series.
- **Decision:** Implement strict rolling-origin cross-validation with expanding/sliding training windows and $H$-step forward validation horizons. Features for each fold are generated strictly as-of the fold's cutoff date $T_k$.
- **Alternatives Rejected:** Single train/test temporal split (high variance), standard random k-fold (data leakage).
- **Impact:** Backtest results reflect true real-world production performance.

### DEC-003: Model Selection Policy (Honest Baseline Comparison)
- **Date:** 2026-09-23
- **Context:** Project brief and rules require shipping the seasonal-naive baseline if candidate ML models fail to beat it on WAPE across the backtest folds.
- **Decision:** Implement automated winner selection in `src/forecast.py` and `src/backtest.py`. If candidate WAPE is higher than seasonal-naive baseline WAPE, the system automatically defaults production scoring to baseline and records the finding in `docs/evidence.md` without hiding results.
- **Alternatives Rejected:** Forcing complex models regardless of accuracy; tuning test split post-hoc to favor ML.
- **Impact:** 100% defensible modeling decisions compliant with `rules.md`.

### DEC-004: Risk Decision Quadrants & Financial Quantifications
- **Date:** 2026-09-23
- **Context:** Operations planners need immediate clarity on what actions to take and the financial stakes in rupees ($₹$).
- **Decision:** Map every SKU into one of four mutually exclusive action states: `REORDER NOW`, `MARKDOWN / CLEAR`, `WATCH / VOLATILE`, `HEALTHY`. Quantify sales at risk using realized unit selling price and capital locked using unit cost from `sku_master`.
- **Alternatives Rejected:** Vague risk probabilities without action labels; unit-only counts without ₹ revenue/capital valuation.
- **Impact:** Direct operational utility for non-technical merchandising and finance stakeholders.
