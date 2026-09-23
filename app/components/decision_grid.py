"""
Interactive Stockout vs Overstock Decision Grid Component for Project FORESIGHT.
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_decision_grid(risk_df: pd.DataFrame) -> None:
    """Renders the stockout vs overstock 2D scatter quadrant plot."""
    st.markdown("### 🎯 Risk Decision Grid (Stockout vs Overstock Exposure)")
    st.caption("Point size indicates total financial exposure in Rupees (₹).")

    # Native Streamlit scatter chart
    plot_df = risk_df.copy()
    plot_df["total_financial_exposure"] = plot_df["sales_at_risk_inr"] + plot_df["capital_locked_inr"]
    plot_df["size_scaled"] = np.clip(plot_df["total_financial_exposure"] / 500.0, 15, 300)

    st.scatter_chart(
        data=plot_df,
        x="overstock_risk_score",
        y="stockout_risk_score",
        color="action",
        size="size_scaled",
        use_container_width=True
    )
