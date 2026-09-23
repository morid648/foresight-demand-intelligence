"""
Master Streamlit Web Application for Project FORESIGHT.
Operational Demand Forecasting & Inventory Intelligence Dashboard for NorthBay Living.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from src.config import config
from src.io import load_dataframe, load_json
from app.components.kpi_cards import render_kpi_cards
from app.components.action_queue import render_action_queue
from app.components.decision_grid import render_decision_grid
from app.components.sku_viewer import render_sku_viewer
from app.components.transparency_panel import render_transparency_panel

# Page Config
st.set_page_config(
    page_title="FORESIGHT — Demand & Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data
def load_app_data():
    """Loads processed weekly panel, risk snapshot, and backtest metrics."""
    panel_path = config.DATA_PROCESSED_DIR / "weekly_panel.parquet"
    risk_path = config.ARTIFACTS_DIR / "risk_snapshot.csv"
    metrics_path = config.ARTIFACTS_DIR / "metrics.json"

    panel_df = load_dataframe(panel_path)
    risk_df = pd.read_csv(risk_path)
    # Parse weekly_forecast string back to list if needed
    if isinstance(risk_df["weekly_forecast"].iloc[0], str):
        import ast
        risk_df["weekly_forecast"] = risk_df["weekly_forecast"].apply(ast.literal_eval)

    metrics_data = load_json(metrics_path) if metrics_path.exists() else {}
    return panel_df, risk_df, metrics_data


def main():
    # Top Header & Status Strip
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.title("📦 Project FORESIGHT")
        st.caption("AI-Powered Demand & Inventory Intelligence Platform • NorthBay Living")

    with header_col2:
        st.markdown("""
        <div style="text-align: right; padding-top: 15px;">
            <span style="background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.8rem;">
                ● Production Pipeline Live
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    try:
        panel_df, risk_df, metrics_data = load_app_data()
    except Exception as e:
        st.error(f"Error loading project artifacts: {str(e)}. Please run `python -m src.pipeline` and `python -m src.generate_predictions_and_risk`.")
        return

    # Sidebar Filters
    st.sidebar.header("🎯 Operational Filters")
    all_categories = ["All Categories"] + sorted(risk_df["category"].dropna().unique().tolist())
    selected_cat = st.sidebar.selectbox("Filter by Category:", options=all_categories)

    filtered_risk_df = risk_df.copy()
    if selected_cat != "All Categories":
        filtered_risk_df = filtered_risk_df[filtered_risk_df["category"] == selected_cat]

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Assessed SKUs:** {len(filtered_risk_df)} / {len(risk_df)}")
    st.sidebar.markdown(f"**Lead Model:** {metrics_data.get('winner', 'RandomForest')}")
    st.sidebar.markdown(f"**Forecast Horizon:** {config.FORECAST_HORIZON_WEEKS} Weeks")

    # 1. Executive Overview KPI Cards
    render_kpi_cards(filtered_risk_df, metrics_data)

    st.markdown("---")

    # 2. Main Decision Views (Split Layout)
    col_queue, col_grid = st.columns([3, 2])

    with col_queue:
        render_action_queue(filtered_risk_df)

    with col_grid:
        render_decision_grid(filtered_risk_df)

    st.markdown("---")

    # 3. Detailed SKU Visualizer
    render_sku_viewer(filtered_risk_df, panel_df)

    st.markdown("---")

    # 4. Model Transparency & Validation View
    render_transparency_panel(metrics_data)


if __name__ == "__main__":
    main()
