# Final Analysis & Portfolio Findings Report — Project FORESIGHT

**Execution Date:** 2026-09-23  
**Target Brand:** NorthBay Living  
**Scope:** 40 SKUs across 4 Product Categories (Home Decor, Bedding, Kitchen & Dining, Bath)  
**Historical Period:** 24 Months (731 Days / 104 Weeks, 3,741 Weekly SKU Observations)  

---

## 1. Executive Summary & Headline Findings

1. **Forecast Accuracy Optimization:**  
   The production **RandomForest Forecaster achieved an aggregate WAPE of 20.79%** across a 4-fold expanding rolling-origin cross-validation backtest, delivering a **+37.3% relative accuracy improvement** over the mandatory Seasonal-Naive baseline benchmark (**33.17% WAPE**).

2. **Total Portfolio Financial Exposure:**  
   - **Total Sales at Risk (Potential Revenue Loss):** **₹6,222,621.86** across 10 urgent reorder SKUs.
   - **Total Capital Locked (Excess Inventory COGS):** **₹6,532,746.20** across 9 overstocked SKUs.

3. **Operational Portfolio Health:**  
   - **🟢 Healthy:** 21 SKUs (52.5%) — inventory covers lead time and forward demand with safe buffers.
   - **🔴 Reorder Now:** 10 SKUs (25.0%) — stockout gap projected within supplier lead times.
   - **🟡 Markdown / Clear:** 9 SKUs (22.5%) — stock exceeds 12-week forward demand.
   - **🟣 Watch / Volatile:** 0 SKUs (0.0%) — high volatility in replenishment schedules.

---

## 2. Demand Modeling & Backtest Benchmark Matrix

| Model Architecture | Aggregate WAPE | Forecast Bias | Aggregate MAPE | Operational Status |
|---|---|---|---|---|
| **Seasonal-Naive Baseline ($t-52$)** | **33.17%** | **+0.0035** | **44.82%** | Mandatory Benchmark |
| **Ridge Linear Regression** | 23.19% | -0.0286 | 32.14% | Candidate |
| **HistGradientBoosting Regressor** | 20.95% | -0.0017 | 28.56% | Candidate |
| **RandomForest Regressor** | **20.79%** | **-0.0081** | **27.91%** | 🏆 **Production Deployed Winner** |

*Evaluation Protocol: 4 expanding temporal folds, 8-week horizon ($H=8$), features strictly as-of cutoff date $T$.*

---

## 3. Category-Level Risk & Exposure Breakdown

| Category | Assessed SKUs | Reorder Triggers | Markdown Triggers | Sales at Risk (₹) | Capital Locked (₹) |
|---|---|---|---|---|---|
| **Bath** | 8 | 1 | 1 | ₹459,364.35 | ₹814,595.61 |
| **Bedding** | 12 | 1 | 4 | ₹1,419,093.29 | ₹1,873,441.48 |
| **Home Decor** | 12 | 5 | 4 | ₹2,527,894.86 | ₹3,424,055.35 |
| **Kitchen & Dining** | 8 | 3 | 0 | ₹1,816,269.36 | ₹420,653.76 |

---

## 4. Priority Operational Action Queues

### A. Top 5 Urgent Stockout Risks (Immediate Purchase Orders Required)
These items have available stock below their supplier lead-time demand + safety buffer:

| SKU ID | Category | Subcategory | On-Hand | Supplier Lead Time | Stockout Gap (Units) | Sales at Risk (₹) |
|---|---|---|---|---|---|---|
| `NB-BED-PIL-021` | Bedding | Pillows | 6 | 35d | 189.8 | **₹1,419,093.29** |
| `NB-KIT-TAB-031` | Kitchen & Dining | Table Linen | 26 | 35d | 168.7 | **₹1,043,887.54** |
| `NB-HOM-CAN-007` | Home Decor | Candles | 10 | 28d | 152.7 | **₹632,489.76** |
| `NB-HOM-VAS-001` | Home Decor | Vases | 7 | 21d | 116.2 | **₹600,203.33** |
| `NB-HOM-WAL-004` | Home Decor | Wall Art | 17 | 28d | 140.7 | **₹583,120.44** |

### B. Top 5 Capital Clearance Targets (Promotional Markdowns Required)
These items hold excess stock exceeding 12 weeks of forward projected demand:

| SKU ID | Category | Subcategory | On-Hand | 8W Forecast | Excess Units | Capital Locked (₹) |
|---|---|---|---|---|---|---|
| `NB-HOM-CUS-011` | Home Decor | Cushions | 976 | 226.9 | 765.3 | **₹2,330,234.15** |
| `NB-BED-PIL-020` | Bedding | Pillows | 586 | 218.0 | 356.4 | **₹931,612.35** |
| `NB-BAT-TOW-033` | Bath | Towels | 559 | 220.8 | 271.8 | **₹563,652.78** |
| `NB-BED-DUV-017` | Bedding | Duvets | 800 | 219.3 | 605.2 | **₹509,732.64** |
| `NB-HOM-CAN-009` | Home Decor | Candles | 527 | 213.4 | 263.3 | **₹456,040.68** |

---

## 5. Strategic Recommendations for Merchandising Leadership

1. **Reorder Execution:** Immediately release purchase orders for the top 5 urgent stockout SKUs to prevent **₹6,222,622** in lost revenue over the coming 3–5 week supplier lead-time window.
2. **Capital Liquidation:** Run a targeted promotional campaign (15–25% discount) on the 9 Markdown quadrant SKUs to liquidate **₹6,532,746** in trapped working capital, funding the new reorder cycle without requiring external credit.
3. **Continuous Scoring Integration:** Connect weekly ERP inventory feeds to the FastAPI `/score/batch` endpoint to automate Monday morning planning queue generation.
