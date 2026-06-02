"""Fan Segmentation — loyalty tiers, K-Means cluster profiles, spend breakdown."""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR

st.set_page_config(page_title="Fan Segmentation", layout="wide")

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


fan_profiles = load("fan_profiles_segmented") if (DATA_PROCESSED_DIR / "fan_profiles_segmented.csv").exists() else load("fan_profiles")
fan_txn      = load("fan_transactions")

st.title("👥 Fan Segmentation")
st.markdown("Fan behavior analysis, loyalty tiers, K-Means segments, and spend profiling.")
st.markdown("---")

if fan_profiles.empty:
    st.warning("Data not found. Run the data pipeline first.")
    st.stop()

# Use 'fan_segment' if available (from segmentation.py), else 'loyalty_status'
seg_col = "fan_segment" if "fan_segment" in fan_profiles.columns else "loyalty_status"
fan_profiles["_segment"] = fan_profiles[seg_col]

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_fans   = len(fan_profiles)
best_seg     = fan_profiles.groupby("_segment")["fan_value_score"].mean().idxmax()
avg_val      = fan_profiles["fan_value_score"].mean()
avg_promo    = fan_profiles["promotion_usage_rate"].mean() * 100
repeat_pct   = (fan_profiles["games_attended_last_12_months"] >= 5).mean() * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Fan Profiles",    f"{total_fans:,}")
c2.metric("Highest-Value Segment", truncate(best_seg, 20))
c3.metric("Avg Fan Value Score",   f"{avg_val:.3f}")
c4.metric("Avg Promo Usage",       f"{avg_promo:.1f}%")
c5.metric("Repeat Buyers (5+ games)", f"{repeat_pct:.1f}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Segment Summary
# ---------------------------------------------------------------------------
seg_summary = (
    fan_profiles.groupby("_segment")
    .agg(
        fan_count=("fan_id","count"),
        avg_games=("games_attended_last_12_months","mean"),
        avg_ticket=("avg_ticket_spend","mean"),
        avg_concession=("avg_concession_spend","mean"),
        avg_merch=("avg_merchandise_spend","mean"),
        avg_promo=("promotion_usage_rate","mean"),
        avg_email=("email_engagement_score","mean"),
        avg_value=("fan_value_score","mean"),
    )
    .reset_index()
)
seg_summary["avg_total_spend"] = seg_summary["avg_ticket"] + seg_summary["avg_concession"] + seg_summary["avg_merch"]
seg_summary = seg_summary.sort_values("avg_value", ascending=False)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    fig = px.bar(seg_summary, x="_segment", y="fan_count",
                 title="Fan Count by Segment",
                 color="avg_value", color_continuous_scale="Blues",
                 labels={"_segment":"Segment","fan_count":"Fan Count","avg_value":"Avg Value Score"})
    fig.update_xaxes(tickangle=-30)
    fig.update_layout(height=380)
    st.plotly_chart(fig)

with col2:
    fig2 = px.bar(seg_summary, x="_segment", y="avg_total_spend",
                  title="Average Total Spend per Fan by Segment",
                  color="avg_total_spend", color_continuous_scale="Greens",
                  labels={"_segment":"Segment","avg_total_spend":"Avg Total Spend"})
    fig2.update_xaxes(tickangle=-30)
    fig2.update_layout(height=380)
    st.plotly_chart(fig2)

col3, col4 = st.columns(2)

with col3:
    fig3 = px.bar(seg_summary.sort_values("avg_promo", ascending=False),
                  x="_segment", y="avg_promo",
                  title="Promotion Usage Rate by Segment",
                  color="avg_promo", color_continuous_scale="Oranges",
                  labels={"_segment":"Segment","avg_promo":"Avg Promo Usage Rate"})
    fig3.update_xaxes(tickangle=-30)
    fig3.update_layout(height=380)
    st.plotly_chart(fig3)

with col4:
    fig4 = px.bar(seg_summary.sort_values("avg_games", ascending=False),
                  x="_segment", y="avg_games",
                  title="Avg Games Attended (Last 12 Months) by Segment",
                  color="avg_games", color_continuous_scale="Purples",
                  labels={"_segment":"Segment","avg_games":"Avg Games Attended"})
    fig4.update_xaxes(tickangle=-30)
    fig4.update_layout(height=380)
    st.plotly_chart(fig4)

# Spend breakdown grouped bar
st.markdown("### Spend Breakdown by Segment (Tickets / Concessions / Merchandise)")
spend_melt = seg_summary.melt(id_vars=["_segment"],
                              value_vars=["avg_ticket","avg_concession","avg_merch"],
                              var_name="Category", value_name="Avg Spend")
spend_melt["Category"] = spend_melt["Category"].map({
    "avg_ticket":"Tickets","avg_concession":"Concessions","avg_merch":"Merchandise"
})
fig5 = px.bar(spend_melt.sort_values("Avg Spend", ascending=False),
              x="_segment", y="Avg Spend", color="Category",
              barmode="group",
              color_discrete_sequence=["#0068c9","#ff6b6b","#ffd166"],
              labels={"_segment":"Segment"})
fig5.update_xaxes(tickangle=-30)
fig5.update_layout(height=420)
st.plotly_chart(fig5)

# ---------------------------------------------------------------------------
# Segment summary table
# ---------------------------------------------------------------------------
st.markdown("### Segment Profile Table")
st.dataframe(
    seg_summary.rename(columns={
        "_segment":"Fan Segment","fan_count":"Fans",
        "avg_games":"Avg Games","avg_ticket":"Avg Ticket $",
        "avg_concession":"Avg Concession $","avg_merch":"Avg Merch $",
        "avg_total_spend":"Avg Total $","avg_promo":"Promo Usage",
        "avg_email":"Email Engagement","avg_value":"Fan Value Score"
    }).round(2)
)
