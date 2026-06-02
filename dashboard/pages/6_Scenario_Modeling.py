"""Scenario Modeling — interactive sliders for what-if revenue and inventory planning."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR

st.set_page_config(page_title="Scenario Modeling", layout="wide")


@st.cache_data(show_spinner=False)
def load(name):
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


games        = load("games")
attendance   = load("attendance")
ticket_sales = load("ticket_sales")
concessions  = load("concessions")
merchandise  = load("merchandise")

st.title("🎛️ Scenario Modeling")
st.markdown(
    "Adjust demand, pricing, and promotion assumptions to project revenue, "
    "staffing level, and inventory requirements."
)
st.markdown("---")

if games.empty or attendance.empty:
    st.warning("Data not found. Run the data pipeline first.")
    st.stop()

# ---------------------------------------------------------------------------
# Compute baselines from data
# ---------------------------------------------------------------------------
avg_att      = float(attendance["actual_attendance"].mean())
avg_cap      = float(attendance["arena_capacity"].mean())
avg_cap_pct  = float(attendance["capacity_pct"].mean())

ticket_agg = ticket_sales.groupby("game_id")["net_ticket_revenue"].sum()
avg_ticket_rev = float(ticket_agg.mean())
avg_ticket_price = float(ticket_sales["avg_ticket_price"].mean())

con_agg = concessions.groupby("game_id")["gross_revenue"].sum()
avg_con_rev = float(con_agg.mean())
con_per_cap = avg_con_rev / avg_att if avg_att > 0 else 0

merch_agg = merchandise.groupby("game_id")["gross_revenue"].sum()
avg_merch_rev = float(merch_agg.mean())
merch_per_cap = avg_merch_rev / avg_att if avg_att > 0 else 0

total_baseline = avg_ticket_rev + avg_con_rev + avg_merch_rev

# ---------------------------------------------------------------------------
# Sidebar sliders
# ---------------------------------------------------------------------------
st.sidebar.markdown("## Scenario Inputs")
att_change   = st.sidebar.slider("Attendance Change (%)",   -20, 20,  0, step=1)
price_change = st.sidebar.slider("Ticket Price Change (%)", -20, 20,  0, step=1)
promo_lift   = st.sidebar.slider("Promotion Lift (%)",        0, 25,  0, step=1)
con_change   = st.sidebar.slider("Concession Demand Change (%)", -20, 30, 0, step=1)
merch_change = st.sidebar.slider("Merchandise Demand Change (%)", -20, 30, 0, step=1)

# ---------------------------------------------------------------------------
# Scenario calculations
# ---------------------------------------------------------------------------
new_att      = avg_att * (1 + (att_change + promo_lift) / 100)
new_cap_pct  = (new_att / avg_cap * 100) if avg_cap > 0 else avg_cap_pct
new_cap_pct  = min(new_cap_pct, 100.0)

tickets_sold_ratio = new_att / avg_att if avg_att > 0 else 1
new_ticket_rev  = avg_ticket_rev * tickets_sold_ratio * (1 + price_change / 100)
new_con_rev     = avg_con_rev * (1 + con_change / 100) * (new_att / avg_att if avg_att > 0 else 1)
new_merch_rev   = avg_merch_rev * (1 + merch_change / 100) * (new_att / avg_att if avg_att > 0 else 1)
new_total       = new_ticket_rev + new_con_rev + new_merch_rev
revenue_change  = new_total - total_baseline
revenue_change_pct = revenue_change / total_baseline * 100 if total_baseline > 0 else 0

# Staffing level
if new_cap_pct >= 95:
    staffing = "Maximum Staffing"
    staffing_color = "#0068c9"
elif new_cap_pct >= 85:
    staffing = "High Staffing"
    staffing_color = "#06d6a0"
elif new_cap_pct >= 70:
    staffing = "Medium Staffing"
    staffing_color = "#ffd166"
else:
    staffing = "Standard Staffing"
    staffing_color = "#ff9999"

# Inventory buffers
if new_cap_pct >= 97:
    inv_buffer = 1.20
elif new_cap_pct >= 88:
    inv_buffer = 1.15
elif new_cap_pct >= 75:
    inv_buffer = 1.10
else:
    inv_buffer = 1.05

new_con_inventory   = int(new_att * (con_per_cap / (concessions["avg_unit_price"].mean() or 10)) * inv_buffer)
new_merch_inventory = int(new_att * (merch_per_cap / (merchandise["avg_unit_price"].mean() or 30)) * inv_buffer)

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
st.markdown("### Projected Scenario Results")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Projected Attendance",     f"{new_att:,.0f}", f"{att_change + promo_lift:+.1f}%")
c2.metric("Projected Cap %",          f"{new_cap_pct:.1f}%")
c3.metric("Total Revenue",            f"${new_total:,.0f}", f"${revenue_change:+,.0f}")
c4.metric("Revenue Change",           f"{revenue_change_pct:+.1f}%",
          delta_color="normal" if revenue_change >= 0 else "inverse")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Ticket Revenue",           f"${new_ticket_rev:,.0f}")
c6.metric("Concessions Revenue",      f"${new_con_rev:,.0f}")
c7.metric("Merchandise Revenue",      f"${new_merch_rev:,.0f}")
c8.metric("Staffing Level",           staffing)

st.markdown("---")

# ---------------------------------------------------------------------------
# Before vs After revenue bar chart
# ---------------------------------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    categories = ["Ticket Revenue","Concession Revenue","Merchandise Revenue","Total Revenue"]
    baseline_vals = [avg_ticket_rev, avg_con_rev, avg_merch_rev, total_baseline]
    scenario_vals = [new_ticket_rev, new_con_rev, new_merch_rev, new_total]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Baseline", x=categories, y=baseline_vals,
                         marker_color="#b0bec5"))
    fig.add_trace(go.Bar(name="Scenario", x=categories, y=scenario_vals,
                         marker_color="#0068c9"))
    fig.update_layout(
        barmode="group", title="Baseline vs Scenario Revenue",
        yaxis_title="Revenue ($)", height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # Inventory recommendations
    con_cats = concessions["category"].unique()
    merch_cats = merchandise["category"].unique()
    inv_labels, inv_vals = [], []
    for cat in con_cats:
        cat_data = concessions[concessions["category"] == cat]
        unit_price = cat_data["avg_unit_price"].mean() or 10
        inv_labels.append(f"Con: {cat}")
        inv_vals.append(int(new_att * (cat_data["per_cap_spend"].mean() / unit_price) * inv_buffer))
    for cat in merch_cats:
        cat_data = merchandise[merchandise["category"] == cat]
        unit_price = cat_data["avg_unit_price"].mean() or 30
        inv_labels.append(f"Merch: {cat}")
        inv_vals.append(int(new_att * (cat_data["per_cap_spend"].mean() / unit_price) * inv_buffer))

    inv_df = pd.DataFrame({"Category": inv_labels, "Recommended Units": inv_vals})
    fig2 = px.bar(inv_df.sort_values("Recommended Units", ascending=False),
                  x="Recommended Units", y="Category", orientation="h",
                  title="Recommended Inventory by Category (Scenario)",
                  color="Recommended Units", color_continuous_scale="Blues")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# Business interpretation
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Business Interpretation")

direction = "increase" if revenue_change >= 0 else "decrease"
st.info(
    f"""
    **Scenario Summary**

    Under this scenario, attendance is projected at **{new_att:,.0f} fans**
    ({att_change + promo_lift:+.0f}% vs. baseline), yielding **{new_cap_pct:.1f}% capacity utilization**.

    Total game-day revenue is projected at **${new_total:,.0f}**, a **{direction} of
    ${abs(revenue_change):,.0f} ({abs(revenue_change_pct):.1f}%)** compared to the
    baseline average of ${total_baseline:,.0f}.

    **Staffing recommendation: {staffing}**
    **Inventory buffer applied: {(inv_buffer - 1) * 100:.0f}%** above demand forecast
    (based on {new_cap_pct:.0f}% capacity utilization)

    - Ticket revenue driver: {price_change:+.0f}% price change × {tickets_sold_ratio:.2f}x attendance ratio
    - Concessions driver: {con_change:+.0f}% demand × attendance volume
    - Merchandise driver: {merch_change:+.0f}% demand × attendance volume
    """
)
