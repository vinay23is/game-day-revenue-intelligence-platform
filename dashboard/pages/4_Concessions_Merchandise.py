"""Concessions & Merchandise Demand — per-cap spend, margins, inventory."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR
from src.utils import fmt_currency

st.set_page_config(page_title="Concessions & Merchandise", layout="wide")


@st.cache_data(show_spinner=False)
def load(name):
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


games       = load("games")
attendance  = load("attendance")
concessions = load("concessions")
merchandise = load("merchandise")

st.title("🍔 Concessions & Merchandise Demand")
st.markdown("Revenue, per-cap spend, gross margins, and inventory recommendations by game and category.")
st.markdown("---")

if concessions.empty or merchandise.empty:
    st.warning("Data not found. Run the data pipeline first.")
    st.stop()

games["game_date"] = pd.to_datetime(games["game_date"])
att_map = attendance.set_index("game_id")[["actual_attendance","capacity_pct","attendance_tier"]]

con = concessions.copy()
mer = merchandise.copy()

# Per-game aggregates
con_agg = con.groupby("game_id").agg(
    total_con_rev=("gross_revenue","sum"),
    total_con_margin=("gross_margin","sum"),
    total_con_units=("units_sold","sum"),
    total_con_inventory=("recommended_inventory_units","sum"),
).join(att_map, how="left")

mer_agg = mer.groupby("game_id").agg(
    total_merch_rev=("gross_revenue","sum"),
    total_merch_margin=("gross_margin","sum"),
    total_merch_units=("units_sold","sum"),
    total_merch_inventory=("recommended_inventory_units","sum"),
).join(att_map, how="left")

con_agg["con_per_cap"] = con_agg["total_con_rev"] / con_agg["actual_attendance"].replace(0, pd.NA)
mer_agg["merch_per_cap"] = mer_agg["total_merch_rev"] / mer_agg["actual_attendance"].replace(0, pd.NA)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_con_rev   = con_agg["total_con_rev"].sum()
total_merch_rev = mer_agg["total_merch_rev"].sum()
avg_con_cap     = con_agg["con_per_cap"].mean()
avg_merch_cap   = mer_agg["merch_per_cap"].mean()
top_con_cat     = con.groupby("category")["gross_revenue"].sum().idxmax()
top_merch_cat   = mer.groupby("category")["gross_revenue"].sum().idxmax()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Concession Rev",      fmt_currency(total_con_rev))
c2.metric("Total Merchandise Rev",     fmt_currency(total_merch_rev))
c3.metric("Avg Concession/Attendee",   f"${avg_con_cap:.2f}")
c4.metric("Avg Merchandise/Attendee",  f"${avg_merch_cap:.2f}")
c5.metric("Top Concession Category",   top_con_cat)
c6.metric("Top Merchandise Category",  top_merch_cat)

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

con_cat = con.groupby("category")[["gross_revenue","gross_margin"]].sum().reset_index()
with col1:
    fig = px.bar(con_cat.sort_values("gross_revenue", ascending=False),
                 x="category", y=["gross_revenue","gross_margin"],
                 barmode="group", title="Concessions: Revenue vs Margin by Category",
                 labels={"value":"Amount","variable":"Metric"},
                 color_discrete_sequence=["#0068c9","#ff6b6b"])
    fig.update_layout(height=380)
    st.plotly_chart(fig)

merch_cat = mer.groupby("category")[["gross_revenue","gross_margin"]].sum().reset_index()
with col2:
    fig2 = px.bar(merch_cat.sort_values("gross_revenue", ascending=False),
                  x="category", y=["gross_revenue","gross_margin"],
                  barmode="group", title="Merchandise: Revenue vs Margin by Category",
                  labels={"value":"Amount","variable":"Metric"},
                  color_discrete_sequence=["#ffd166","#06d6a0"])
    fig2.update_layout(height=380)
    st.plotly_chart(fig2)

col3, col4 = st.columns(2)

# Per-cap spend by attendance tier
con_tier = con.merge(attendance[["game_id","attendance_tier","actual_attendance"]], on="game_id")
con_tier["per_cap_game"] = con_tier["gross_revenue"] / con_tier["actual_attendance"].replace(0, pd.NA)
tier_percap = con_tier.groupby(["attendance_tier","category"])["per_cap_game"].mean().reset_index()

with col3:
    fig3 = px.bar(tier_percap, x="attendance_tier", y="per_cap_game", color="category",
                  barmode="group", title="Concession Per-Cap Spend by Attendance Tier",
                  category_orders={"attendance_tier":["Low","Medium","High","Sellout"]},
                  labels={"per_cap_game":"Per-Cap Spend","attendance_tier":"Attendance Tier"})
    fig3.update_layout(height=380)
    st.plotly_chart(fig3)

# Inventory recommendations
inv_df = (
    con_agg.reset_index()[["game_id","attendance_tier","total_con_inventory"]]
    .merge(mer_agg.reset_index()[["game_id","total_merch_inventory"]], on="game_id")
    .merge(games[["game_id","away_team_name","game_date","rivalry_flag"]], on="game_id")
)
inv_df["game_label"] = inv_df["away_team_name"].str[:10]
with col4:
    top_inv = inv_df.nlargest(15, "total_con_inventory")
    fig4 = px.bar(top_inv.sort_values("total_con_inventory"),
                  x="total_con_inventory", y="game_label", orientation="h",
                  title="Top 15 Games: Recommended Concession Inventory",
                  color="attendance_tier",
                  color_discrete_map={"Low":"#ff9999","Medium":"#ffd166","High":"#06d6a0","Sellout":"#0068c9"})
    fig4.update_layout(height=380)
    st.plotly_chart(fig4)

# ---------------------------------------------------------------------------
# Inventory table
# ---------------------------------------------------------------------------
st.markdown("### Game-Level Inventory & Revenue Summary")
summary = (
    inv_df.merge(con_agg.reset_index()[["game_id","total_con_rev","con_per_cap"]], on="game_id")
    .merge(mer_agg.reset_index()[["game_id","total_merch_rev","merch_per_cap"]], on="game_id")
    .merge(attendance[["game_id","actual_attendance"]], on="game_id")
    .sort_values("total_con_rev", ascending=False)
    .head(100)
)
summary["total_con_rev"] = summary["total_con_rev"].round(0)
summary["total_merch_rev"] = summary["total_merch_rev"].round(0)
summary["con_per_cap"] = summary["con_per_cap"].round(2)
summary["merch_per_cap"] = summary["merch_per_cap"].round(2)
st.dataframe(
    summary[["game_date","game_label","actual_attendance","attendance_tier",
             "total_con_rev","con_per_cap","total_con_inventory",
             "total_merch_rev","merch_per_cap","total_merch_inventory"]]
    .rename(columns={
        "game_date":"Date","game_label":"Opponent","actual_attendance":"Attendance",
        "attendance_tier":"Tier","total_con_rev":"Concession Rev","con_per_cap":"Con/Cap",
        "total_con_inventory":"Con Inventory","total_merch_rev":"Merch Rev",
        "merch_per_cap":"Merch/Cap","total_merch_inventory":"Merch Inventory"
    })
)
