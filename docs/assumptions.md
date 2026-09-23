# Assumptions Register — Project FORESIGHT

**Project:** FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform  
**Client:** NorthBay Living  
**Standard:** Documented rationale for all engineering & business logic assumptions.  

---

| ID | Date | Parameter / Area | Decision & Assumption | Why Needed | Alternative Considered | Expected Impact | How to Validate |
|---|---|---|---|---|---|---|---|
| **ASM-01** | 2026-09-23 | Target Grain | Weekly Sunday-to-Saturday aggregation per SKU. | Daily demand is noisy and intermittent; inventory reordering in D2C happens weekly. | Bi-weekly or monthly aggregation. | Reduces intermittent zero-spike noise; provides stable demand forecasts for planning. | Verified against client brief D1 specification. |
| **ASM-02** | 2026-09-23 | Forecast Horizon | 8-week forward horizon ($H=8$). | Operations planning cycle requires forward coverage across typical supplier lead times (2–6 weeks). | 4-week or 12-week horizon. | Enables lead-time demand coverage with margin. | Compare with SKU lead times in `inventory_snapshots`. |
| **ASM-03** | 2026-09-23 | Primary Accuracy Metric | Weighted Absolute Percentage Error (WAPE). | Classical MAPE explodes or becomes undefined on zero/near-zero demand weeks common in D2C catalogs. | MAPE, RMSE, MAE. | Scale-independent, volume-weighted error metric reflecting total unit risk. | Verified against project brief core methodology. |
| **ASM-04** | 2026-09-23 | Baseline Model | Seasonal-Naive ($t-52$ with moving median fallback for short history). | Required by project brief as mandatory benchmark to beat before deploying ML. | Simple moving average, mean forecaster. | Sets realistic high bar for seasonal products. | Verified against backtest results. |
| **ASM-05** | 2026-09-23 | Safety Stock Factor | Rule-based safety stock: $Z \times \sigma_{\text{demand}} \times \sqrt{L}$ ($Z=1.65$ for 95% service level). | Provides standard buffer against lead time demand variance without arbitrary magic numbers. | Fixed 2-week buffer, zero buffer. | Prevents avoidable stockouts during demand spikes. | Test with different $Z$ factors in `config.py`. |
| **ASM-06** | 2026-09-23 | Forward Overstock Window | 12 weeks ($W_{\text{forward}}=12$). | D2C seasonal inventory held $>12$ weeks incurs substantial holding cost and obsolescence risk. | 26 weeks, 52 weeks. | Flags slow-moving capital in time for promotional markdown. | Calibrate against inventory turnover rates. |
| **ASM-07** | 2026-09-23 | Test Fixture Generation | High-fidelity synthetic catalog (50 SKUs across 4 categories, 104 weeks history) used for automated testing. | Enables full end-to-end pipeline execution and verification while production client files are delivered. | Static 2-row mock. | Guarantees 100% reproducible testing of features, models, backtests, and UI. | Run pipeline and compare against schema contracts. |
