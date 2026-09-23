"""
Planning Action Queue Table Component for Project FORESIGHT Streamlit Dashboard.
"""

import streamlit as st
import pandas as pd


def render_action_queue(risk_df: pd.DataFrame) -> None:
    """Renders the operations planning queue table with search and action filters."""
    st.markdown("### 📋 Operations Planning Queue")

    tab_all, tab_reorder, tab_clear, tab_watch, tab_healthy = st.tabs([
        f"All SKUs ({len(risk_df)})",
        f"🔴 Reorder Now ({(risk_df['action'] == 'REORDER NOW').sum()})",
        f"🟡 Markdown / Clear ({(risk_df['action'] == 'MARKDOWN / CLEAR').sum()})",
        f"🟣 Watch / Volatile ({(risk_df['action'] == 'WATCH / VOLATILE').sum()})",
        f"🟢 Healthy ({(risk_df['action'] == 'HEALTHY').sum()})"
    ])

    def format_table(df_subset: pd.DataFrame) -> pd.DataFrame:
        display_cols = [
            "sku_id", "category", "subcategory", "cumulative_forecast_demand",
            "on_hand_units", "on_order_units", "lead_time_days",
            "stockout_gap_units", "overstock_excess_units",
            "sales_at_risk_inr", "capital_locked_inr", "action"
        ]
        return df_subset[display_cols].rename(columns={
            "sku_id": "SKU ID",
            "category": "Category",
            "subcategory": "Subcategory",
            "cumulative_forecast_demand": "8W Demand",
            "on_hand_units": "On-Hand",
            "on_order_units": "On-Order",
            "lead_time_days": "Lead Time (d)",
            "stockout_gap_units": "Stockout Gap",
            "overstock_excess_units": "Excess Units",
            "sales_at_risk_inr": "Sales at Risk (₹)",
            "capital_locked_inr": "Capital Locked (₹)",
            "action": "Action"
        })

    with tab_all:
        st.dataframe(format_table(risk_df), use_container_width=True, hide_index=True)

    with tab_reorder:
        reorder_df = risk_df[risk_df["action"] == "REORDER NOW"]
        st.dataframe(format_table(reorder_df), use_container_width=True, hide_index=True)

    with tab_clear:
        clear_df = risk_df[risk_df["action"] == "MARKDOWN / CLEAR"]
        st.dataframe(format_table(clear_df), use_container_width=True, hide_index=True)

    with tab_watch:
        watch_df = risk_df[risk_df["action"] == "WATCH / VOLATILE"]
        st.dataframe(format_table(watch_df), use_container_width=True, hide_index=True)

    with tab_healthy:
        healthy_df = risk_df[risk_df["action"] == "HEALTHY"]
        st.dataframe(format_table(healthy_df), use_container_width=True, hide_index=True)

    # Export Button
    csv_bytes = risk_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Planning Queue to CSV",
        data=csv_bytes,
        file_name="foresight_planning_queue.csv",
        mime="text/csv"
    )
