"""
Game-Day Revenue Intelligence Platform
Main Streamlit entry point and landing page.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR

st.set_page_config(
    page_title="Game-Day Revenue Intelligence",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Data loader (cached, CSV-first fallback)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_table(name: str) -> pd.DataFrame:
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.image(
    "https://via.placeholder.com/280x60/1a1a2e/ffffff?text=Game-Day+BI+Platform",
    use_container_width=True,
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Navigation**

    Use the pages in the sidebar to explore:
    - 📊 Executive Overview
    - 🔮 Attendance Forecast
    - 🎟️ Ticket Revenue
    - 🍔 Concessions & Merch
    - 👥 Fan Segmentation
    - 🎛️ Scenario Modeling
    """
)
st.sidebar.markdown("---")
st.sidebar.caption("Game-Day Revenue Intelligence Platform")
st.sidebar.caption("Sports Business Intelligence & Data Science")

# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

st.title("Game-Day Revenue Intelligence Platform")
st.markdown(
    "##### Sports Business Intelligence | Attendance Forecasting | Revenue Analytics | Fan Segmentation"
)
st.markdown("---")

col1, col2, col3 = st.columns(3)

games = load_table("games")
attendance = load_table("attendance")
ticket_sales = load_table("ticket_sales")

with col1:
    st.metric("Total Games Analyzed", f"{len(games):,}" if not games.empty else "—")
    st.metric("Seasons Covered", str(games["season"].nunique()) if not games.empty else "—")

with col2:
    if not attendance.empty:
        st.metric("Total Fan Attendance", f"{attendance['actual_attendance'].sum():,.0f}")
        st.metric("Avg Capacity Utilization", f"{attendance['capacity_pct'].mean():.1f}%")
    else:
        st.metric("Total Fan Attendance", "—")
        st.metric("Avg Capacity Utilization", "—")

with col3:
    if not ticket_sales.empty:
        total_rev = ticket_sales["net_ticket_revenue"].sum()
        st.metric("Total Ticket Revenue", f"${total_rev:,.0f}")
    else:
        st.metric("Total Ticket Revenue", "—")
    st.metric("Teams", "30 Franchises | 2 Conferences")

st.markdown("---")

st.markdown(
    """
    ## About This Platform

    This platform provides a comprehensive sports business intelligence solution for analyzing
    game-day demand, revenue, fan behavior, and operational planning. It combines:

    - **SQL analytics** across 12 relational tables with 40+ business queries
    - **Machine learning models** for attendance and revenue forecasting
    - **Fan segmentation** using K-Means clustering
    - **Interactive dashboards** for business stakeholders
    - **Scenario modeling** for staffing, inventory, and pricing decisions

    ---

    ## Data Overview

    This project uses public-style basketball game data concepts combined with simulated business
    data for ticketing, concessions, merchandise, promotions, and fan profiles. The simulated
    fields are designed to demonstrate sports business intelligence workflows where real internal
    team revenue data is private.
    """
)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.info("**Data Pipeline**\n\nSimulated → Cleaned → Feature-engineered → Model predictions")
with col_b:
    st.info("**ML Models**\n\nAttendance forecast · Revenue forecast · Fan segmentation (K-Means)")
with col_c:
    st.info("**Dashboard**\n\nExecutive KPIs · Forecast · Tickets · Concessions · Fans · Scenarios")

st.markdown("---")
st.markdown(
    """
    ### Quick Start

    ```bash
    python src/simulate_business_data.py   # generate all CSV data
    python src/data_cleaning.py            # validate and clean
    python src/feature_engineering.py     # build model features
    python src/train_attendance_model.py  # train attendance model
    python src/train_revenue_model.py     # train revenue model
    python src/segmentation.py            # fan segmentation
    streamlit run dashboard/app.py        # launch this dashboard
    ```
    """
)
