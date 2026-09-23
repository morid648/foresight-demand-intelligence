# Executive Readout Presentation Outline — Project FORESIGHT

**Target Audience:** C-Suite Leadership, Head of Operations, Merchandising Lead (NorthBay Living)  
**Tone:** Action-oriented, quantitative, executive-focused  

---

### Slide 1: Executive Summary & The Problem
- **The Challenge:** Historical reliance on spreadsheet judgement led to severe dual pains: fast-selling bestsellers stocked out during peak seasons while slow-moving styles accumulated excess capital.
- **The Solution:** Project FORESIGHT — an AI-powered demand intelligence and inventory risk platform that automates weekly SKU forecasting, quantifies ₹ revenue exposure, and provides clear operational action queues.
- **Key Headline:** Model achieves **20.79% WAPE** across multi-fold rolling backtests, delivering a **+37.3% relative improvement** over seasonal benchmarks.

---

### Slide 2: Data Reality & Ingestion Integrity
- **Scope:** 24 months of daily transaction data, 40 active SKUs across 4 core product categories (Bedding, Home Decor, Kitchen & Dining, Bath).
- **Automated Data Quality:** Standardized cleaning rules (CLN-01 to CLN-05) eliminated negative returns distortion, deduplicated transactions, and created continuous weekly panel continuity.
- **Traceability:** 100% automated single-command pipeline with reproducible outputs.

---

### Slide 3: Demand Forecast Performance & Baseline Benchmark
- **Honest Benchmark Methodology:** Evaluated via expanding-window rolling-origin cross-validation (4 folds, 8-week horizon).
- **Model Comparison:**
  - *Seasonal-Naive Baseline ($t-52$):* WAPE = **33.17%** | Bias = +0.0035
  - *Ridge Regularized Linear:* WAPE = **23.19%** | Bias = -0.0286
  - *HistGradientBoosting:* WAPE = **20.95%** | Bias = -0.0017
  - *RandomForest Regressor (Winner):* WAPE = **20.79%** | Bias = -0.0081
- **Takeaway:** The selected model captures complex non-linear promotional spikes and seasonal patterns with negligible bias.

---

### Slide 4: Inventory Risk Intelligence & 4-Quadrant Framework
- **Translating Predictions into Operations:**
  1. **REORDER NOW (High Stockout / Low Overstock):** Inventory insufficient to cover supplier lead-time demand plus safety buffer ($Z=1.65$). Immediate purchase order required.
  2. **MARKDOWN / CLEAR (Low Stockout / High Overstock):** Stock exceeds 12-week forward demand window. Working capital at risk of obsolescence.
  3. **WATCH / VOLATILE (High Stockout / High Overstock):** Mismatch in immediate vs forward inventory commitments requiring supply schedule realignment.
  4. **HEALTHY (Balanced Position):** Inventory safely covers demand within target bounds.

---

### Slide 5: Rupee Financial Exposure Valuation
- **Sales at Risk ($₹$):** Total potential lost revenue from projected stockout units multiplied by realized selling price.
- **Capital Locked ($₹$):** Excess inventory units multiplied by unit cost of goods sold.
- **Portfolio Health Summary:**
  - Identified urgent reorder triggers for key bestseller styles before lead-time cutoffs.
  - Flagged capital locked in long-tail categories to fund reorder cycles without new working capital injection.

---

### Slide 6: Operational Workflow & The Dual Platform
- **Streamlit Operations Planning Dashboard:** Built for non-technical planners with sortable planning queues, instant CSV exports, and 2D risk scatter grids.
- **FastAPI Real-Time Scoring Microservice:** Shared scoring engine providing `/score` and `/score/batch` endpoints for ERP/WMS integration.

---

### Slide 7: Implementation Roadmap & Recommended Actions
1. **Week 1–2:** Transition weekly replenishment reviews from spreadsheets to the FORESIGHT Planning Queue.
2. **Week 3–4:** Execute promotional clearance campaigns on the identified Markdown quadrant SKUs to free working capital.
3. **Week 5+:** Connect supplier EDI / ERP extracts directly to the automated ingestion pipeline.

---

### Slide 8: Technical Defensibility, Assumptions & Future Scope
- **Assumptions:** 8-week forecast horizon, $Z=1.65$ safety stock (95% service level), 12-week overstock horizon.
- **Future Enhancements:** Dynamic price elasticity simulation and multi-echelon warehouse distribution optimization.
