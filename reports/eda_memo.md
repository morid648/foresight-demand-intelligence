# Executive EDA & Demand Insight Memo — Project FORESIGHT

**Date:** 2026-09-23  
**Target:** Head of Operations, Merchandising Lead, NorthBay Living  
**Data Grain:** Weekly SKU Panel (3,741 observations across 40 SKUs)  

---

## 1. Key Business Insights

### Finding 1: Festive & Q4 Demand Surge
- **Observation:** The Festive season (October–November) accounts for **24.88%** of annual volume, creating intense 6–8 week demand peaks.
- **Operational Impact:** Holiday/festive promotional weeks exhibit a **3.02x demand multiplier** over non-event weeks.
- **Action Required:** Safety buffers and reorder horizons for Tier-1 SKUs must be expanded ahead of Q4 to avoid peak-season stockouts.

### Finding 2: Category Concentration (Pareto Profile)
- **Top Categories:** **Home Decor** drives **28.3%** of gross revenue.
- **Category Summary Table:**

| Category | SKU Count | Total Units | Total Revenue (₹) | Revenue Share |
|---|---|---|---|---|
| Bath | 8 | 32,674 | ₹144,180,491.43 | 20.36% |
| Bedding | 12 | 49,862 | ₹182,427,592.95 | 25.76% |
| Home Decor | 12 | 49,553 | ₹200,415,096.37 | 28.3% |
| Kitchen & Dining | 8 | 31,801 | ₹181,070,827.02 | 25.57% |

### Finding 3: Tail SKU Velocity & Dead Stock Risk
- **Top 5 Bestsellers:** Drive disproportionate volume (e.g. `NB-BAT-ROB-040` with 4,474 units).
- **Slow-Moving Tail:** Bottom 5 SKUs exhibit high zero-sales weeks and average less than 46.2 units/week.
- **Action Required:** Automatic markdown triggers must be established for SKUs where on-hand inventory exceeds 12+ weeks of sell-through.

---

## 2. Baseline Modeling Strategy & Protocol Freeze

1. **Target:** Weekly units sold per SKU ($y_{i,t}$).
2. **Primary Benchmark:** Seasonal-Naive ($t-52$) with 8-week moving median fallback for SKUs with $<52$ weeks history.
3. **Primary Metric:** WAPE (Volume-Weighted Absolute Percentage Error).
4. **Secondary Diagnostic:** Forecast Bias (to catch chronic under/over-ordering).
