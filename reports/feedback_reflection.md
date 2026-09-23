# Engineering Feedback & Reflection — Project FORESIGHT

**Author:** Lead Software & Data Science Engineer  
**Project:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Client:** NorthBay Living  

---

## 1. Key Engineering Challenges Encountered

### Challenge 1: Temporal Data Leakage in Feature Engineering
- **The Problem:** In demand forecasting, calculating rolling statistics (mean, std, promo uplift) across the whole dataset inadvertently introduces future information into past training periods, creating artificially optimistic accuracy metrics that collapse in production.
- **The Solution:** Implemented strict cutoff-bounded feature generation in `src/features.py`. Every feature is derived exclusively from observations strictly prior to cutoff timestamp $t-1$. Verified temporal integrity via unit tests with intentional future data corruption in `tests/test_features.py`.

### Challenge 2: Intermittent Demand & Metric Distortion
- **The Problem:** D2C home decor and bedding catalogs frequently exhibit intermittent zero-sales weeks. Traditional Mean Absolute Percentage Error (MAPE) produces division-by-zero errors or heavily distorts low-volume items.
- **The Solution:** Adopted Weighted Absolute Percentage Error (WAPE = $\sum |y - \hat{y}| / \sum y$) as the non-negotiable primary accuracy metric, while reporting Forecast Bias as a secondary diagnostic to catch persistent over/under-forecasting.

### Challenge 3: Unifying UI and API Scoring Logic
- **The Problem:** Many data science projects suffer from metric drift where the interactive UI dashboard and production API service implement separate, slightly divergent calculation paths.
- **The Solution:** Decoupled the core forecasting and risk classification engines into pure Python modules in `src/`. Both the Streamlit application (`app/`) and FastAPI service (`service/`) import and execute these shared functions, confirmed by automated parity integration tests in `tests/test_integration.py`.

---

## 2. Key Learnings & Takeaways
1. **The Baseline is the Anchor:** Setting up a robust Seasonal-Naive baseline ($t-52$) prior to training complex models provides an indispensable sanity check. Complex gradient boosting or ensemble models are only justified if they empirically beat the baseline under fair rolling-origin cross-validation.
2. **Business Impact Over Raw Math:** Operations planners think in terms of purchase order lead times, safety stocks, and rupee financial exposure—not RMSE or loss functions. Framing predictions within a 4-quadrant actionable decision grid (`REORDER NOW`, `MARKDOWN / CLEAR`, `WATCH / VOLATILE`, `HEALTHY`) is what transforms analytics into business decisions.
