"""
Model Transparency and Evaluation Summary Component for Project FORESIGHT.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_transparency_panel(metrics_data: Dict[str, Any]) -> None:
    """Renders non-technical model evaluation, benchmark comparisons, and validation protocol."""
    st.markdown("### 🔬 Model Transparency & Backtest Integrity")

    st.markdown("""
    Project FORESIGHT follows a strict **leakage-free rolling-origin backtesting protocol**.
    Every candidate model is evaluated against the **Seasonal-Naive baseline benchmark**.
    """)

    models_dict = metrics_data.get("models", {})
    if models_dict:
        rows = []
        for m_name, m_stats in models_dict.items():
            rows.append({
                "Model Architecture": m_name,
                "Aggregate WAPE": f"{m_stats['aggregate_wape'] * 100:.2f}%",
                "Forecast Bias": f"{m_stats['aggregate_bias']:+.4f}",
                "Aggregate MAPE": f"{m_stats['aggregate_mape'] * 100:.2f}%",
                "Status": "🏆 WINNER / DEPLOYED" if m_name == metrics_data.get("winner") else "Benchmark Candidate"
            })
        df_models = pd.DataFrame(rows)
        st.dataframe(df_models, use_container_width=True, hide_index=True)

    with st.expander("ℹ️ Learn more about our Validation Methodology & Anti-Leakage Policy"):
        st.markdown(f"""
        - **Rolling Origin CV:** Evaluated across **{metrics_data.get('folds', 4)} folds** using expanding temporal windows.
        - **Zero Leakage:** All lag features, rolling windows, and promotional aggregates are computed strictly as-of each fold's historical cutoff.
        - **Metric Integrity:** WAPE ($\sum |y - \hat{{y}}| / \sum y$) serves as the primary metric to avoid distortion on zero-demand weeks.
        - **Baseline Benchmark Rule:** Candidate models must strictly beat Seasonal-Naive to earn production deployment status.
        """)
