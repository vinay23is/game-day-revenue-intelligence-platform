"""Executive Overview — top-line KPIs and revenue trends."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR

st.set_page_config(page_title="Executive Overview", layout="wide")

def fmt_currency(v: float) -> str:
    a = abs(v)
    if a >= 1_000_000_000: return f"${v / 1_000_000_000:.2f}B"
    if a >= 1_000_000:     return f"${v / 1_000_000:.1f}M"
    if a >= 1_000:         return f"${v / 1_000:.1f}K"
    return f"${v:,.0f}"

def truncate(text: str, max_len: int = 18) -> str:
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 1] + "…"



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
promotions   = load("promotions")
fan_profiles = load("fan_profiles")

st.title("📊 Executive Overview")
st.markdown("Top-line KPIs and revenue trends across all seasons.")
st.markdown("---")

if games.empty or attendance.empty:
    st.warning("Data not found. Run `python src/simulate_business_data.py` first.")
    st.stop()

games["game_date"] = pd.to_datetime(games["game_date"])

# ---------------------------------------------------------------------------
# Build game-level revenue table
# ---------------------------------------------------------------------------
ticket_agg = ticket_sales.groupby("game_id")["net_ticket_revenue"].sum().reset_index()
con_agg    = concessions.groupby("game_id")["gross_revenue"].sum().reset_index().rename(columns={"gross_revenue": "concession_revenue"})
merch_agg  = merchandise.groupby("game_id")["gross_revenue"].sum().reset_index().rename(columns={"gross_revenue": "merchandise_revenue"})

df = (
    games[["game_id","game_date","season","home_team_name","away_team_name","month","is_weekend","rivalry_flag"]]
    .merge(attendance[["game_id","actual_attendance","capacity_pct","attendance_tier"]], on="game_id")
    .merge(ticket_agg, on="game_id", how="left")
    .merge(con_agg,    on="game_id", how="left")
    .merge(merch_agg,  on="game_id", how="left")
)
df["net_ticket_revenue"]   = df["net_ticket_revenue"].fillna(0)
df["concession_revenue"]   = df["concession_revenue"].fillna(0)
df["merchandise_revenue"]  = df["merchandise_revenue"].fillna(0)
df["total_revenue"]        = df["net_ticket_revenue"] + df["concession_revenue"] + df["merchandise_revenue"]
df["revenue_per_attendee"] = df["total_revenue"] / df["actual_attendance"].replace(0, pd.NA)

# ---------------------------------------------------------------------------
# KPI metrics row
# ---------------------------------------------------------------------------
total_games  = len(df)
total_att    = df["actual_attendance"].sum()
avg_cap      = df["capacity_pct"].mean()
total_ticket = df["net_ticket_revenue"].sum()
total_con    = df["concession_revenue"].sum()
total_merch  = df["merchandise_revenue"].sum()
total_rev    = df["total_revenue"].sum()
avg_per_att  = df["revenue_per_attendee"].mean()
top_opp      = df.groupby("away_team_name")["capacity_pct"].mean().idxmax()
top_loyalty  = fan_profiles.groupby("loyalty_status")["fan_value_score"].mean().idxmax() if not fan_profiles.empty else "—"

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Games",      f"{total_games:,}")
c2.metric("Total Attendance", f"{total_att / 1_000_000:.1f}M fans")
c3.metric("Avg Capacity %",   f"{avg_cap:.1f}%")
c4.metric("Total Revenue",    fmt_currency(total_rev))
c5.metric("Avg $/Attendee",   f"${avg_per_att:.2f}")

c6, c7, c8, c9, c10 = st.columns(5)
c6.metric("Ticket Revenue",   fmt_currency(total_ticket))
c7.metric("Concessions",      fmt_currency(total_con))
c8.metric("Merchandise",      fmt_currency(total_merch))
c9.metric("Top Opponent",     truncate(top_opp, 16))
c10.metric("Top Fan Segment", truncate(top_loyalty, 18))

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

# Revenue trend by month
with row1_col1:
    monthly = df.groupby(["season","month"])[["net_ticket_revenue","concession_revenue","merchandise_revenue"]].sum().reset_index()
    monthly["period"] = monthly["season"].astype(str) + "-M" + monthly["month"].astype(str).str.zfill(2)
    monthly_melt = monthly.melt(id_vars=["period"], value_vars=["net_ticket_revenue","concession_revenue","merchandise_revenue"],
                                var_name="Revenue Type", value_name="Revenue")
    monthly_melt["Revenue Type"] = monthly_melt["Revenue Type"].map({
        "net_ticket_revenue": "Tickets",
        "concession_revenue": "Concessions",
        "merchandise_revenue": "Merchandise"
    })
    fig = px.area(monthly_melt.sort_values("period"), x="period", y="Revenue", color="Revenue Type",
                  title="Monthly Revenue Trend (All Seasons)",
                  color_discrete_sequence=["#0068c9","#ff6b6b","#ffd166"])
    fig.update_layout(xaxis_tickangle=-45, height=380)
    st.plotly_chart(fig)

# Revenue breakdown (pie)
with row1_col2:
    rev_labels = ["Ticket Revenue","Concession Revenue","Merchandise Revenue"]
    rev_vals   = [total_ticket, total_con, total_merch]
    fig2 = go.Figure(go.Pie(
        labels=rev_labels, values=rev_vals,
        marker_colors=["#0068c9","#ff6b6b","#ffd166"],
        hole=0.45
    ))
    fig2.update_layout(title="Revenue Breakdown by Category", height=380)
    st.plotly_chart(fig2)

row2_col1, row2_col2 = st.columns(2)

# Top 10 games by revenue
with row2_col1:
    top10 = df.nlargest(10, "total_revenue")[["game_date","home_team_name","away_team_name","total_revenue","capacity_pct"]].copy()
    top10["label"] = top10["away_team_name"].str[:12] + " (" + top10["game_date"].dt.strftime("%m/%d") + ")"
    fig3 = px.bar(top10.sort_values("total_revenue"), x="total_revenue", y="label",
                  orientation="h", title="Top 10 Games by Total Revenue",
                  color="capacity_pct", color_continuous_scale="Blues",
                  labels={"total_revenue":"Total Revenue","label":"Game","capacity_pct":"Capacity %"})
    fig3.update_layout(height=380)
    st.plotly_chart(fig3)

# Top 10 opponents by avg attendance
with row2_col2:
    opp_att = df.groupby("away_team_name")["capacity_pct"].mean().nlargest(10).reset_index()
    opp_att.columns = ["Opponent","Avg Capacity %"]
    fig4 = px.bar(opp_att.sort_values("Avg Capacity %"), x="Avg Capacity %", y="Opponent",
                  orientation="h", title="Top 10 Opponents by Avg Capacity %",
                  color="Avg Capacity %", color_continuous_scale="Greens")
    fig4.update_layout(height=380)
    st.plotly_chart(fig4)

# Attendance vs capacity scatter
st.markdown("### Attendance vs Capacity by Game")
fig5 = px.scatter(
    df, x="actual_attendance", y="total_revenue",
    color="attendance_tier", size="capacity_pct",
    hover_data=["game_date","home_team_name","away_team_name"],
    title="Attendance vs Total Revenue (colored by demand tier)",
    color_discrete_map={"Low":"#ff9999","Medium":"#ffd166","High":"#06d6a0","Sellout":"#0068c9"},
    labels={"actual_attendance":"Actual Attendance","total_revenue":"Total Revenue"}
)
fig5.update_layout(height=420)
st.plotly_chart(fig5)
