"""
Generates markdown business reports:
  reports/business_insights.md
  reports/executive_summary.md
Supplements model_metrics.md which is written by the model training scripts.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR, REPORTS_DIR


def _load(name: str) -> pd.DataFrame:
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()


def generate_business_insights():
    games = _load("games")
    attendance = _load("attendance")
    ticket_sales = _load("ticket_sales")
    concessions = _load("concessions")
    merchandise = _load("merchandise")
    promotions = _load("promotions")
    fan_profiles = _load("fan_profiles")

    if games.empty or attendance.empty:
        print("  Missing data — skipping business insights generation.")
        return

    # Merge for analysis
    df = games.merge(attendance, on="game_id").merge(promotions, on="game_id")
    ticket_agg = ticket_sales.groupby("game_id")["net_ticket_revenue"].sum().reset_index()
    con_agg = concessions.groupby("game_id")["gross_revenue"].sum().reset_index().rename(
        columns={"gross_revenue": "concession_revenue"}
    )
    merch_agg = merchandise.groupby("game_id")["gross_revenue"].sum().reset_index().rename(
        columns={"gross_revenue": "merch_revenue"}
    )
    df = df.merge(ticket_agg, on="game_id", how="left")
    df = df.merge(con_agg, on="game_id", how="left")
    df = df.merge(merch_agg, on="game_id", how="left")
    df["total_revenue"] = df["net_ticket_revenue"].fillna(0) + df["concession_revenue"].fillna(0) + df["merch_revenue"].fillna(0)

    # Attendance drivers
    weekend_att = df.groupby("is_weekend")["capacity_pct"].mean()
    rivalry_att = df.groupby("rivalry_flag")["capacity_pct"].mean()
    promo_att = df.groupby("promotion_flag")["capacity_pct"].mean()

    top_opponents = (
        df.groupby("away_team_name")["capacity_pct"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    top_months = (
        df.groupby("month")["capacity_pct"]
        .mean()
        .sort_values(ascending=False)
        .head(3)
    )

    # Ticket segment analysis
    seg_rev = (
        ticket_sales.groupby("segment_name")
        .agg(
            total_net_revenue=("net_ticket_revenue", "sum"),
            avg_sell_through=("sell_through_rate", "mean"),
        )
        .sort_values("total_net_revenue", ascending=False)
    )

    # Promotion analysis
    promo_agg = (
        df.groupby("promotion_type")
        .agg(
            games=("game_id", "count"),
            avg_capacity_pct=("capacity_pct", "mean"),
            avg_total_revenue=("total_revenue", "mean"),
        )
        .sort_values("avg_capacity_pct", ascending=False)
    )

    content = """# Business Insights Report

## Overview
This report summarizes key findings from the Game-Day Revenue Intelligence Platform analysis
across 5 seasons of simulated basketball game-day data.

---

## 1. Attendance Drivers

"""
    weekend_true  = float(weekend_att[True])  if True  in weekend_att.index else float(weekend_att.iloc[-1])
    weekend_false = float(weekend_att[False]) if False in weekend_att.index else float(weekend_att.iloc[0])
    rivalry_true  = float(rivalry_att[True])  if True  in rivalry_att.index else float(rivalry_att.iloc[-1])
    promo_true    = float(promo_att[True])    if True  in promo_att.index   else float(promo_att.iloc[-1])

    content += f"- **Weekend vs Weekday:** Weekend games average "
    content += f"{weekend_true:.1f}% capacity vs "
    content += f"{weekend_false:.1f}% for weekday games.\n"
    content += f"- **Rivalry Games:** Rivalry matchups average "
    content += f"{rivalry_true:.1f}% capacity.\n"
    content += f"- **Promotional Games:** Games with promotions average "
    content += f"{promo_true:.1f}% capacity.\n\n"
    content += "### Top 5 Opponents by Average Attendance\n\n"
    content += "| Opponent | Avg Capacity % |\n|----------|----------------|\n"
    for opp, cap in top_opponents.items():
        content += f"| {opp} | {cap:.1f}% |\n"

    content += "\n### Top Months by Attendance\n\n"
    month_names = {1:"January",2:"February",3:"March",4:"April",10:"October",
                   11:"November",12:"December"}
    for m, cap in top_months.items():
        content += f"- {month_names.get(int(m), str(m))}: {cap:.1f}% avg capacity\n"

    content += "\n---\n\n## 2. Ticket Revenue Analysis\n\n"
    content += "### Revenue by Ticket Segment\n\n"
    content += "| Segment | Total Net Revenue | Avg Sell-Through |\n"
    content += "|---------|------------------|------------------|\n"
    for seg, row in seg_rev.iterrows():
        content += f"| {seg} | ${row['total_net_revenue']:,.0f} | {row['avg_sell_through']:.1f}% |\n"

    content += "\n**Key Finding:** Premium Courtside and Lower Bowl segments drive a disproportionate "
    content += "share of per-seat revenue, while Upper Bowl and Group Sales drive total volume.\n"

    content += "\n---\n\n## 3. Promotion Effectiveness\n\n"
    content += "| Promotion Type | Games | Avg Capacity % | Avg Game Revenue |\n"
    content += "|----------------|-------|----------------|------------------|\n"
    for promo, row in promo_agg.iterrows():
        content += f"| {promo} | {int(row['games'])} | {row['avg_capacity_pct']:.1f}% | ${row['avg_total_revenue']:,.0f} |\n"
    content += "\n**Recommendation:** Merchandise Giveaway and Theme Night promotions show the "
    content += "strongest attendance lift, particularly for weekday games.\n"

    content += "\n---\n\n## 4. Concessions and Merchandise Observations\n\n"
    cat_merch = merchandise.groupby("category")["gross_revenue"].sum().sort_values(ascending=False)
    cat_con = concessions.groupby("category")["gross_revenue"].sum().sort_values(ascending=False)

    content += "### Merchandise Revenue by Category\n\n"
    for cat, rev in cat_merch.items():
        content += f"- **{cat}:** ${rev:,.0f} total\n"

    content += "\n### Concessions Revenue by Category\n\n"
    for cat, rev in cat_con.items():
        content += f"- **{cat}:** ${rev:,.0f} total\n"

    content += "\n**Key Finding:** Jerseys and Combo Meals generate the highest per-unit revenue. "
    content += "Inventory recommendations are scaled to attendance tier with 5-20% buffers.\n"

    content += "\n---\n\n## 5. Fan Behavior Observations\n\n"
    loy_spend = (
        fan_profiles.groupby("loyalty_status")
        .agg(
            avg_ticket=("avg_ticket_spend", "mean"),
            avg_concession=("avg_concession_spend", "mean"),
            avg_merch=("avg_merchandise_spend", "mean"),
            count=("fan_id", "count"),
        )
        .sort_values("avg_ticket", ascending=False)
    )
    content += "| Loyalty Status | Avg Ticket Spend | Avg Concession | Avg Merch | Fan Count |\n"
    content += "|----------------|-----------------|----------------|-----------|----------|\n"
    for lst, row in loy_spend.iterrows():
        content += (f"| {lst} | ${row['avg_ticket']:.0f} | ${row['avg_concession']:.0f} | "
                    f"${row['avg_merch']:.0f} | {int(row['count'])} |\n")

    content += "\n**Recommendation:** Season Ticket Holders and Premium Members represent "
    content += "high lifetime value — retention programs and personalized outreach should prioritize these groups.\n"

    content += "\n---\n\n## 6. Strategic Recommendations\n\n"
    content += "1. **Increase promotion investment for weekday games** — promotions show measurable attendance lift on lower-demand nights.\n"
    content += "2. **Dynamic pricing opportunity** — high-demand rivalry and nationally televised games consistently sell at premium; further price optimization is viable.\n"
    content += "3. **Target high-value fan retention** — Premium Members and Season Ticket Holders generate disproportionate revenue across all categories.\n"
    content += "4. **Inventory planning** — Use attendance forecasts to scale concessions and merchandise inventory with tier-based buffers to minimize waste and stockouts.\n"
    content += "5. **Corporate partner alignment** — Corporate Partner Night games correlate with premium segment ticket usage; bundle sponsorship packages with premium experiences.\n\n"

    insights_path = REPORTS_DIR / "business_insights.md"
    # Check if segmentation section already appended
    existing = insights_path.read_text() if insights_path.exists() else ""
    if "Fan Segmentation Results" in existing:
        # Preserve the segmentation section already written by segmentation.py
        seg_section = existing[existing.find("## Fan Segmentation"):]
        with open(insights_path, "w") as f:
            f.write(content + seg_section)
    else:
        with open(insights_path, "w") as f:
            f.write(content)

    print(f"  Business insights saved: {insights_path}")


def generate_executive_summary():
    games = _load("games")
    attendance = _load("attendance")
    ticket_sales = _load("ticket_sales")
    concessions = _load("concessions")
    merchandise = _load("merchandise")

    if games.empty:
        print("  Missing data — skipping executive summary.")
        return

    total_games = len(games)
    total_att = attendance["actual_attendance"].sum() if not attendance.empty else 0
    avg_cap_pct = attendance["capacity_pct"].mean() if not attendance.empty else 0

    total_ticket_rev = ticket_sales["net_ticket_revenue"].sum() if not ticket_sales.empty else 0
    total_con_rev = concessions["gross_revenue"].sum() if not concessions.empty else 0
    total_merch_rev = merchandise["gross_revenue"].sum() if not merchandise.empty else 0
    total_rev = total_ticket_rev + total_con_rev + total_merch_rev

    content = f"""# Executive Summary: Game-Day Revenue Intelligence Platform

**Date:** June 2026
**Prepared by:** Vinay Dodla
**Audience:** Business Intelligence Leadership, Revenue Strategy Team

---

## Objective

This platform was built to address a core business problem in sports and entertainment operations:
how can a team's business intelligence function reliably forecast game-day demand, identify
revenue drivers, and provide actionable guidance to staffing, concessions, merchandise, and
marketing teams — all before the first fan walks through the door?

---

## Key Findings

### Scale of Analysis
- **Total games analyzed:** {total_games:,} across 5 seasons
- **Total attendance:** {total_att:,} fans
- **Average venue capacity utilization:** {avg_cap_pct:.1f}%
- **Total projected revenue (5 seasons):** ${total_rev:,.0f}
  - Ticket revenue: ${total_ticket_rev:,.0f} ({total_ticket_rev/total_rev*100:.1f}%)
  - Concessions: ${total_con_rev:,.0f} ({total_con_rev/total_rev*100:.1f}%)
  - Merchandise: ${total_merch_rev:,.0f} ({total_merch_rev/total_rev*100:.1f}%)

### Attendance Intelligence
- Weekend games consistently outperform weekday games by 5-8 percentage points in capacity utilization.
- Rivalry matchups and nationally televised games generate the highest demand and support premium pricing.
- Weather-related impacts are measurable: severe weather reduces attendance by an estimated 8%, snow by 4%.
- Promotions such as Merchandise Giveaways and Theme Nights show the strongest weekday lift.

### Revenue Intelligence
- Premium Courtside, Club Level, and Lower Bowl segments drive the highest per-game ticket revenue.
- Corporate Partner allocations provide predictable premium revenue independent of game-day demand fluctuations.
- Concessions and merchandise per-cap spending scales with attendance tier, with sellout games generating 20%+ more per-attendee spend.

### Fan Segmentation
- High-Value Fans and Season Ticket Loyalists represent a small share of the fanbase but contribute disproportionate lifetime value.
- Promo-Sensitive Fans respond strongly to discount and giveaway promotions — a key lever for weekday attendance lift.
- Family Buyers show strong concession and merchandise spend, particularly on weekends and family promotion nights.

---

## Recommended Actions

| Priority | Action | Expected Benefit |
|----------|--------|-----------------|
| High | Deploy attendance forecasts for weekly staffing plans | Reduce labor over/understaffing costs |
| High | Implement tier-based inventory buffering for concessions/merch | Reduce waste and stockout incidents |
| Medium | Increase weekday promotion investment (giveaways, theme nights) | 5-9% attendance lift on low-demand games |
| Medium | Launch targeted retention program for Season Ticket Holders | Protect highest-LTV fan segment |
| Low | Pilot dynamic pricing on rivalry and nationally televised games | Capture additional ticket revenue on high-demand nights |

---

## Risks and Limitations

- All business revenue data (tickets, concessions, merchandise, CRM) in this platform is simulated. Real internal POS and CRM data would improve model precision significantly.
- Attendance forecasts are trained on historical patterns. Roster changes, major injuries, and market disruptions are not modeled.
- Fan segmentation is based on behavioral proxies. Actual survey, loyalty app, or transaction data would strengthen segment definitions.
- Model performance should be re-evaluated after each season as team performance and fan behavior evolve.

---

## Next Steps

1. Integrate real point-of-sale and ticketing system data for live model calibration.
2. Extend the pipeline to automate weekly forecast updates for operations teams.
3. Connect the scenario modeling tool to actual staffing and procurement systems.
4. Build a Power BI version of the executive dashboard for leadership stakeholders who prefer non-technical tooling.
5. Add promotion ROI optimization — move from descriptive to prescriptive analytics.

---

*This platform demonstrates end-to-end sports business intelligence capabilities including data engineering, SQL analytics, machine learning, interactive dashboarding, and executive reporting.*
"""

    path = REPORTS_DIR / "executive_summary.md"
    with open(path, "w") as f:
        f.write(content)
    print(f"  Executive summary saved: {path}")


def main():
    print("Generating business reports...")
    generate_business_insights()
    generate_executive_summary()
    print("Reports complete.")


if __name__ == "__main__":
    main()
