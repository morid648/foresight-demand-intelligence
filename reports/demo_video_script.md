# Product Demo Video Script (3–5 Minutes) — Project FORESIGHT

**Title:** FORESIGHT: AI-Powered Demand & Inventory Intelligence Platform  
**Target Duration:** 3:30 – 4:30 minutes  

---

### Segment 1: The Operational Problem (0:00 – 0:45)
- **Visual:** Open on NorthBay Living D2C operations scenario / split screen of stockout alerts and spreadsheet chaos.
- **Narrative:**
  > "Welcome to Project FORESIGHT. For D2C brands like NorthBay Living, managing inventory using spreadsheets creates a constant tug-of-war. Bestselling products stock out during festive surges, costing millions in lost revenue, while slow-moving styles tie up critical working capital in dusty warehouses. Planners don't just need complex machine learning predictions—they need clear, operational decisions on what to reorder, what to clear, and where the financial stakes are highest. That's why we built FORESIGHT."

---

### Segment 2: System Architecture & Reproducible Data Pipeline (0:45 – 1:30)
- **Visual:** Terminal showing single-command pipeline execution `python -m src.pipeline` generating processed panel, followed by architecture diagram.
- **Narrative:**
  > "FORESIGHT transforms daily transactional sales, SKU metadata, calendar events, and inventory positions into a unified, weekly panel. Our automated pipeline enforces strict deterministic data cleaning rules—handling returns, deduplicating records, and verifying 100% SKU coverage with zero manual intervention. Every metric is backed by our leakage-free rolling-origin backtesting engine."

---

### Segment 3: The Planning Dashboard in Action (1:30 – 2:45)
- **Visual:** Screen recording of Streamlit Dashboard (`app/streamlit_app.py`).
- **Walkthrough Actions:**
  1. **Executive Overview KPIs:** Show the headline cards displaying Assessed SKUs, 20.79% WAPE (+37.3% improvement over baseline), Total Sales at Risk (₹), and Capital Locked (₹).
  2. **Interactive Planning Queue:** Filter by "Reorder Now" to view high-priority stockout risks, sort by sales-at-risk, and demonstrate the instant CSV export for purchase ordering.
  3. **Risk Decision Grid:** Point out the 2D scatter quadrant plot highlighting SKUs with massive financial exposure in the upper and right quadrants.
  4. **SKU Trajectory Visualizer:** Select a specific SKU (e.g., `NB-HOM-VAS-001`) to inspect historical actuals alongside the 8-week forward forecast curve and inventory safety buffer.

---

### Segment 4: The Real-Time Scoring API (2:45 – 3:30)
- **Visual:** FastAPI Swagger UI (`http://localhost:8000/docs`) executing a `/score` POST request.
- **Narrative:**
  > "Because enterprise systems require real-time integration, FORESIGHT exposes a high-performance FastAPI microservice. Whether scoring an individual SKU or a bulk batch of thousands, the API utilizes the exact same underlying scoring engine as the dashboard—guaranteeing 100% parity and zero metric drift across systems."

---

### Segment 5: Conclusion & Business Impact (3:30 – 4:00)
- **Visual:** Summary slide with key business metrics and live repository link.
- **Narrative:**
  > "By bridging the gap between advanced time-series modeling and daily merchandising execution, FORESIGHT empowers planners to protect revenue and unlock tied-up capital. Thank you."
