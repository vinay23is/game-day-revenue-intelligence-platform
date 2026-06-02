"""Ticket Revenue — segment analysis, sell-through, and pricing insights."""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR
from src.utils import fmt_currency, truncate

st.set_page_config(page_title="Ticket Revenue", layout="wide")


@st.cache_data(show_spinner=False)
def load(name):
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


games        = load("games")
ticket_sales = load("ticket_sales")
attendance   = load("attendance")
promotions   = load("promotions")

st.title("🎟️ Ticket Revenue Analysis")
st.markdown("Segment performance, sell-through rates, pricing, and promotion impact on ticketing.")
st.markdown("---")

if ticket_sales.empty:
    st.warning("Data not found. Run the data pipeline first.")
    st.stop()

games["game_date"] = pd.to_datetime(games["game_date"])
df = ticket_sales.merge(
    games[["game_id","game_date","home_team_name","away_team_name","day_of_week","rivalry_flag"]],
    on="game_id", how="left"
).merge(
    attendance[["game_id","capacity_pct","attendance_tier"]], on="game_id", how="left"
).merge(
    promotions[["game_id","promotion_type"]], on="game_id", how="left"
)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_net    = df["net_ticket_revenue"].sum()
avg_per_game = df.groupby("game_id")["net_ticket_revenue"].sum().mean()
best_seg     = df.groupby("segment_name")["net_ticket_revenue"].sum().idxmax()
best_st      = df.groupby("segment_name")["sell_through_rate"].mean().idxmax()
avg_price    = df["avg_ticket_price"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Net Ticket Revenue", fmt_currency(total_net))
c2.metric("Avg Revenue per Game",     fmt_currency(avg_per_game))
c3.metric("Best Segment by Revenue",  truncate(best_seg, 14))
c4.metric("Highest Sell-Through Seg", truncate(best_st, 14))
c5.metric("Avg Ticket Price",         f"${avg_price:.2f}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

seg_rev = df.groupby("segment_name")["net_ticket_revenue"].sum().reset_index().sort_values("net_ticket_revenue", ascending=False)
with col1:
    fig = px.bar(seg_rev, x="segment_name", y="net_ticket_revenue",
                 title="Total Net Revenue by Ticket Segment",
                 color="net_ticket_revenue", color_continuous_scale="Blues",
                 labels={"segment_name":"Segment","net_ticket_revenue":"Net Revenue"})
    fig.update_xaxes(tickangle=-35)
    fig.update_layout(height=380)
    st.plotly_chart(fig)

seg_st = df.groupby("segment_name")["sell_through_rate"].mean().reset_index().sort_values("sell_through_rate", ascending=False)
with col2:
    fig2 = px.bar(seg_st, x="segment_name", y="sell_through_rate",
                  title="Average Sell-Through Rate by Segment (%)",
                  color="sell_through_rate", color_continuous_scale="Greens",
                  labels={"segment_name":"Segment","sell_through_rate":"Sell-Through %"})
    fig2.update_xaxes(tickangle=-35)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2)

col3, col4 = st.columns(2)

opp_rev = (
    df.groupby("away_team_name")["net_ticket_revenue"]
    .sum().nlargest(12).reset_index()
    .rename(columns={"away_team_name":"Opponent","net_ticket_revenue":"Net Revenue"})
)
with col3:
    fig3 = px.bar(opp_rev.sort_values("Net Revenue"), x="Net Revenue", y="Opponent",
                  orientation="h", title="Ticket Revenue by Opponent (Top 12)",
                  color="Net Revenue", color_continuous_scale="Purples")
    fig3.update_layout(height=380)
    st.plotly_chart(fig3)

promo_rev = df.groupby("promotion_type")["net_ticket_revenue"].mean().reset_index().sort_values("net_ticket_revenue", ascending=False)
with col4:
    fig4 = px.bar(promo_rev, x="promotion_type", y="net_ticket_revenue",
                  title="Avg Ticket Revenue by Promotion Type",
                  color="net_ticket_revenue", color_continuous_scale="Oranges",
                  labels={"promotion_type":"Promotion","net_ticket_revenue":"Avg Net Revenue"})
    fig4.update_xaxes(tickangle=-35)
    fig4.update_layout(height=380)
    st.plotly_chart(fig4)

# Discount vs revenue scatter
st.markdown("### Discount Rate vs Net Ticket Revenue by Segment")
sample = df.sample(min(2000, len(df)), random_state=42)
fig5 = px.scatter(sample, x="discount_pct", y="net_ticket_revenue",
                  color="segment_name", opacity=0.6,
                  title="Discount % vs Net Ticket Revenue",
                  labels={"discount_pct":"Discount %","net_ticket_revenue":"Net Ticket Revenue"})
fig5.update_layout(height=400)
st.plotly_chart(fig5)

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------
st.markdown("### Ticket Sales Detail Table")
table_df = (
    df.groupby(["game_id","game_date","away_team_name","segment_name"])
    .agg(tickets_sold=("tickets_sold","sum"),
         avg_ticket_price=("avg_ticket_price","mean"),
         net_ticket_revenue=("net_ticket_revenue","sum"),
         sell_through_rate=("sell_through_rate","mean"))
    .reset_index()
    .sort_values("net_ticket_revenue", ascending=False)
    .head(200)
)
table_df["avg_ticket_price"] = table_df["avg_ticket_price"].round(2)
table_df["net_ticket_revenue"] = table_df["net_ticket_revenue"].round(0)
table_df["sell_through_rate"] = table_df["sell_through_rate"].round(1)
st.dataframe(
    table_df.rename(columns={
        "game_id":"Game ID","game_date":"Date","away_team_name":"Opponent",
        "segment_name":"Segment","tickets_sold":"Tickets Sold",
        "avg_ticket_price":"Avg Price","net_ticket_revenue":"Net Revenue",
        "sell_through_rate":"Sell-Through %"
    })
)
