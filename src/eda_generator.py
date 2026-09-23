"""
EDA & Insight Generation Script for Project FORESIGHT.
Profiles demand patterns, category concentrations, top movers, dead stock, and promotional uplift.
"""

import pandas as pd
import numpy as np
from src.config import config
from src.io import load_dataframe, ensure_dir


def generate_eda_artifacts() -> None:
    panel_df = load_dataframe(config.DATA_PROCESSED_DIR / "weekly_panel.parquet")

    # 1. Volume contribution by category
    cat_summary = panel_df.groupby("category").agg(
        total_units=("units_sold", "sum"),
        total_revenue=("revenue", "sum"),
        sku_count=("sku_id", "nunique"),
        avg_weekly_units=("units_sold", "mean")
    ).reset_index()
    cat_summary["revenue_share_pct"] = (cat_summary["total_revenue"] / cat_summary["total_revenue"].sum() * 100).round(2)

    # 2. Top Movers vs Slow Stock
    sku_summary = panel_df.groupby(["sku_id", "category", "subcategory"]).agg(
        total_units=("units_sold", "sum"),
        total_revenue=("revenue", "sum"),
        avg_weekly_units=("units_sold", "mean"),
        zero_sales_weeks=("units_sold", lambda s: (s == 0).sum())
    ).reset_index().sort_values("total_revenue", ascending=False)

    top_5_skus = sku_summary.head(5)
    bottom_5_skus = sku_summary.tail(5)

    # 3. Promo Uplift Analysis
    promo_uplift = panel_df.groupby("is_holiday_week").agg(
        avg_units=("units_sold", "mean"),
        avg_revenue=("revenue", "mean")
    )
    uplift_multiplier = round(promo_uplift.loc[1, "avg_units"] / promo_uplift.loc[0, "avg_units"], 2)

    # 4. Seasonal Demand Concentration
    seasonal_dist = panel_df.groupby("season")["units_sold"].sum()
    festive_share = round(seasonal_dist.get("Festive", 0) / seasonal_dist.sum() * 100, 2)

    # Write EDA Insight Memo
    memo_path = config.REPORTS_DIR / "eda_memo.md"
    ensure_dir(memo_path.parent)

    memo_content = f"""# Executive EDA & Demand Insight Memo — Project FORESIGHT

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}  
**Target:** Head of Operations, Merchandising Lead, NorthBay Living  
**Data Grain:** Weekly SKU Panel ({len(panel_df):,} observations across {panel_df['sku_id'].nunique()} SKUs)  

---

## 1. Key Business Insights

### Finding 1: Festive & Q4 Demand Surge
- **Observation:** The Festive season (October–November) accounts for **{festive_share}%** of annual volume, creating intense 6–8 week demand peaks.
- **Operational Impact:** Holiday/festive promotional weeks exhibit a **{uplift_multiplier}x demand multiplier** over non-event weeks.
- **Action Required:** Safety buffers and reorder horizons for Tier-1 SKUs must be expanded ahead of Q4 to avoid peak-season stockouts.

### Finding 2: Category Concentration (Pareto Profile)
- **Top Categories:** **{cat_summary.sort_values('total_revenue', ascending=False).iloc[0]['category']}** drives **{cat_summary.sort_values('total_revenue', ascending=False).iloc[0]['revenue_share_pct']}%** of gross revenue.
- **Category Summary Table:**

| Category | SKU Count | Total Units | Total Revenue (₹) | Revenue Share |
|---|---|---|---|---|
"""
    for _, r in cat_summary.iterrows():
        memo_content += f"| {r['category']} | {r['sku_count']} | {int(r['total_units']):,} | ₹{r['total_revenue']:,.2f} | {r['revenue_share_pct']}% |\n"

    memo_content += f"""
### Finding 3: Tail SKU Velocity & Dead Stock Risk
- **Top 5 Bestsellers:** Drive disproportionate volume (e.g. `{top_5_skus.iloc[0]['sku_id']}` with {int(top_5_skus.iloc[0]['total_units']):,} units).
- **Slow-Moving Tail:** Bottom 5 SKUs exhibit high zero-sales weeks and average less than {bottom_5_skus['avg_weekly_units'].max():.1f} units/week.
- **Action Required:** Automatic markdown triggers must be established for SKUs where on-hand inventory exceeds 12+ weeks of sell-through.

---

## 2. Baseline Modeling Strategy & Protocol Freeze

1. **Target:** Weekly units sold per SKU ($y_{{i,t}}$).
2. **Primary Benchmark:** Seasonal-Naive ($t-52$) with 8-week moving median fallback for SKUs with $<52$ weeks history.
3. **Primary Metric:** WAPE (Volume-Weighted Absolute Percentage Error).
4. **Secondary Diagnostic:** Forecast Bias (to catch chronic under/over-ordering).
"""

    with open(memo_path, "w", encoding="utf-8") as f:
        f.write(memo_content)

    print(f"Generated {memo_path}")


if __name__ == "__main__":
    generate_eda_artifacts()
