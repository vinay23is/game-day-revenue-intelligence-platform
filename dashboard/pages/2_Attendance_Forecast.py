"""Attendance Forecast — actual vs. predicted attendance analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR

st.set_page_config(page_title="Attendance Forecast", layout="wide")


@st.cache_data(show_spinner=False)
def load(name):
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


games      = load("games")
attendance = load("attendance")
promotions = load("promotions")
att_preds  = load("attendance_predictions")

st.title("🔮 Attendance Forecast")
st.markdown("Actual vs. predicted attendance, demand drivers, and underperforming game identification.")
st.markdown("---")

if games.empty or attendance.empty:
    st.warning("Data not found. Run the data pipeline first.")
    st.stop()

games["game_date"] = pd.to_datetime(games["game_date"])

df = (
    games[["game_id","game_date","season","home_team_name","away_team_name","day_of_week","month","is_weekend","rivalry_flag","nationally_televised_flag"]]
    .merge(attendance[["game_id","actual_attendance","capacity_pct","expected_attendance_baseline","attendance_tier"]], on="game_id")
    .merge(promotions[["game_id","promotion_type","promotion_flag"]], on="game_id", how="left")
)

has_preds = not att_preds.empty
if has_preds:
    df = df.merge(att_preds[["game_id","predicted_attendance","attendance_prediction_error"]], on="game_id", how="left")
    mae = df["attendance_prediction_error"].abs().mean()
else:
    df["predicted_attendance"] = df["expected_attendance_baseline"]
    df["attendance_prediction_error"] = df["actual_attendance"] - df["expected_attendance_baseline"]
    mae = df["attendance_prediction_error"].abs().mean()

df["underperforming"] = df["attendance_prediction_error"] < -(df["actual_attendance"] * 0.08)
n_underperforming = df["underperforming"].sum()

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avg Actual Attendance",    f"{df['actual_attendance'].mean():,.0f}")
c2.metric("Avg Predicted Attendance", f"{df['predicted_attendance'].mean():,.0f}")
c3.metric("Attendance MAE",           f"{mae:,.0f} fans")
c4.metric("Avg Capacity %",           f"{df['capacity_pct'].mean():.1f}%")
c5.metric("Underperforming Games",    str(int(n_underperforming)))

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    sample = df.sample(min(800, len(df)), random_state=42)
    fig = px.scatter(
        sample, x="actual_attendance", y="predicted_attendance",
        color="attendance_tier",
        hover_data=["game_date","home_team_name","away_team_name"],
        title="Actual vs Predicted Attendance",
        color_discrete_map={"Low":"#ff9999","Medium":"#ffd166","High":"#06d6a0","Sellout":"#0068c9"},
    )
    max_val = max(sample["actual_attendance"].max(), sample["predicted_attendance"].max()) * 1.05
    fig.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                  line=dict(dash="dash", color="gray"))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    dow_att = df.groupby("day_of_week")["actual_attendance"].mean().reset_index()
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow_att["day_of_week"] = pd.Categorical(dow_att["day_of_week"], categories=dow_order, ordered=True)
    dow_att = dow_att.sort_values("day_of_week")
    fig2 = px.bar(dow_att, x="day_of_week", y="actual_attendance",
                  title="Average Attendance by Day of Week",
                  color="actual_attendance", color_continuous_scale="Blues")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    opp_att = df.groupby("away_team_name")["actual_attendance"].mean().nlargest(15).reset_index()
    fig3 = px.bar(opp_att.sort_values("actual_attendance"), x="actual_attendance", y="away_team_name",
                  orientation="h", title="Top 15 Opponents by Avg Attendance",
                  color="actual_attendance", color_continuous_scale="Greens")
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    month_att = df.groupby("month")["actual_attendance"].mean().reset_index()
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   10:"Oct",11:"Nov",12:"Dec"}
    month_att["month_name"] = month_att["month"].map(month_names).fillna(month_att["month"].astype(str))
    fig4 = px.line(month_att.sort_values("month"), x="month_name", y="actual_attendance",
                   markers=True, title="Average Attendance by Month",
                   labels={"actual_attendance":"Avg Attendance","month_name":"Month"})
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------------------------------
# Underperforming games table
# ---------------------------------------------------------------------------
st.markdown("### Underperforming Games (Actual < Predicted by 8%+)")
under = df[df["underperforming"]].sort_values("attendance_prediction_error").head(30)
st.dataframe(
    under[["game_date","home_team_name","away_team_name","actual_attendance","predicted_attendance",
           "attendance_prediction_error","capacity_pct","attendance_tier","promotion_type","day_of_week"]]
    .rename(columns={
        "game_date":"Date","home_team_name":"Home Team","away_team_name":"Opponent",
        "actual_attendance":"Actual Att","predicted_attendance":"Predicted Att",
        "attendance_prediction_error":"Error","capacity_pct":"Cap %",
        "attendance_tier":"Tier","promotion_type":"Promotion","day_of_week":"Day"
    }),
    use_container_width=True
)
