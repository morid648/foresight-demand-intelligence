"""
Executive KPI Cards Component for Project FORESIGHT Streamlit Dashboard.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_kpi_cards(
    risk_df: pd.DataFrame,
    metrics_data: Dict[str, Any]
) -> None:
    """Renders the top executive KPI metric cards."""
    total_skus = len(risk_df)
    total_sales_at_risk = risk_df["sales_at_risk_inr"].sum()
    total_capital_locked = risk_df["capital_locked_inr"].sum()
    reorder_count = (risk_df["action"] == "REORDER NOW").sum()
    markdown_count = (risk_df["action"] == "MARKDOWN / CLEAR").sum()

    winner_wape = metrics_data.get("winning_wape", 0.2079)
    baseline_wape = metrics_data.get("baseline_wape", 0.3317)
    winner_name = metrics_data.get("winner", "RandomForest")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">SKUs Assessed</div>
            <div class="kpi-value">{total_skus}</div>
            <div class="kpi-subtext">8-Week Forecast Horizon</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        wape_delta = round((baseline_wape - winner_wape) * 100, 1)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Forecast WAPE</div>
            <div class="kpi-value">{winner_wape * 100:.1f}%</div>
            <div class="kpi-subtext">vs Baseline {baseline_wape * 100:.1f}% (<b>+{wape_delta}% pts</b>)</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Sales at Risk</div>
            <div class="kpi-value" style="color: #DC2626;">₹{total_sales_at_risk:,.0f}</div>
            <div class="kpi-subtext">Stockout revenue exposure</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Capital Locked</div>
            <div class="kpi-value" style="color: #D97706;">₹{total_capital_locked:,.0f}</div>
            <div class="kpi-subtext">Tied up in excess overstock</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Urgent Actions</div>
            <div class="kpi-value" style="color: #4F46E5;">{reorder_count + markdown_count}</div>
            <div class="kpi-subtext">{reorder_count} Reorders | {markdown_count} Markdowns</div>
        </div>
        """, unsafe_allow_html=True)
