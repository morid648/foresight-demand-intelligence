"""
SKU Detail Drilldown & Demand Forecast Trajectory Visualizer Component.
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_sku_viewer(
    risk_df: pd.DataFrame,
    panel_df: pd.DataFrame
) -> None:
    """Renders detailed single SKU inspector with historical actuals and forecast trajectory."""
    st.markdown("### 🔍 SKU Demand & Inventory Drilldown")

    sku_list = sorted(risk_df["sku_id"].unique())
    selected_sku = st.selectbox("Select SKU to inspect:", options=sku_list)

    sku_risk = risk_df[risk_df["sku_id"] == selected_sku].iloc[0]
    sku_history = panel_df[panel_df["sku_id"] == selected_sku].sort_values("week_start")

    col_chart, col_info = st.columns([2, 1])

    with col_chart:
        st.markdown(f"**Demand Trajectory: {selected_sku} ({sku_risk['category']} / {sku_risk['subcategory']})**")

        # Build combined actuals and forecast series for native line_chart
        hist_df = sku_history[["week_start", "units_sold"]].rename(columns={"units_sold": "Historical Actuals"}).set_index("week_start")

        # Generate future weeks
        last_date = sku_history["week_start"].max()
        future_dates = [last_date + pd.Timedelta(weeks=h) for h in range(1, 9)]
        fcst_vals = sku_risk["weekly_forecast"]

        fcst_df = pd.DataFrame({
            "week_start": future_dates,
            "Production Forecast": fcst_vals
        }).set_index("week_start")

        combined = pd.concat([hist_df, fcst_df], axis=1)
        st.line_chart(combined, use_container_width=True)

    with col_info:
        st.markdown("#### Operational Status")
        action_colors = {
            "REORDER NOW": "badge-reorder",
            "MARKDOWN / CLEAR": "badge-markdown",
            "WATCH / VOLATILE": "badge-watch",
            "HEALTHY": "badge-healthy"
        }
        badge_cls = action_colors.get(sku_risk["action"], "badge-healthy")
        st.markdown(f'<span class="{badge_cls}">{sku_risk["action"]}</span>', unsafe_allow_html=True)

        st.markdown(f"**Rationale:** {sku_risk['action_rationale']}")

        st.markdown("---")
        st.markdown(f"- **Current Stock on Hand:** {int(sku_risk['on_hand_units']):,} units")
        st.markdown(f"- **Stock in Transit (On-Order):** {int(sku_risk['on_order_units']):,} units")
        st.markdown(f"- **Supplier Lead Time:** {int(sku_risk['lead_time_days'])} days")
        st.markdown(f"- **Safety Stock Buffer:** {sku_risk['safety_stock']:.1f} units")
        st.markdown(f"- **8-Week Forecast Demand:** {sku_risk['cumulative_forecast_demand']:.1f} units")

        if sku_risk["sales_at_risk_inr"] > 0:
            st.error(f"⚠️ Sales at Risk: ₹{sku_risk['sales_at_risk_inr']:,.2f}")
        if sku_risk["capital_locked_inr"] > 0:
            st.warning(f"📦 Capital Locked: ₹{sku_risk['capital_locked_inr']:,.2f}")
