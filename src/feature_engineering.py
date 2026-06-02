"""
Builds model-ready feature datasets for attendance and revenue prediction models.
Outputs:
  data/processed/features_attendance.csv
  data/processed/features_revenue.csv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR, RANDOM_SEED

rng = np.random.default_rng(RANDOM_SEED)

DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _load(name: str) -> pd.DataFrame:
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / f"{name}.csv"
        if p.exists():
            return pd.read_csv(p)
    raise FileNotFoundError(f"{name}.csv not found")


def build_features() -> pd.DataFrame:
    games = _load("games")
    attendance = _load("attendance")
    weather = _load("weather")
    promotions = _load("promotions")
    ticket_sales = _load("ticket_sales")
    concessions = _load("concessions")
    merchandise = _load("merchandise")
    teams = _load("teams")

    games["game_date"] = pd.to_datetime(games["game_date"])

    # Aggregate ticket revenue per game
    ticket_rev = (
        ticket_sales.groupby("game_id")
        .agg(
            total_net_ticket_revenue=("net_ticket_revenue", "sum"),
            total_gross_ticket_revenue=("gross_ticket_revenue", "sum"),
            avg_ticket_price_all=("avg_ticket_price", "mean"),
            total_tickets_sold=("tickets_sold", "sum"),
        )
        .reset_index()
    )

    # Aggregate concessions per game
    con_rev = (
        concessions.groupby("game_id")
        .agg(
            total_concession_revenue=("gross_revenue", "sum"),
            avg_concession_per_cap=("per_cap_spend", "mean"),
        )
        .reset_index()
    )

    # Aggregate merchandise per game
    merch_rev = (
        merchandise.groupby("game_id")
        .agg(
            total_merchandise_revenue=("gross_revenue", "sum"),
            avg_merch_per_cap=("per_cap_spend", "mean"),
        )
        .reset_index()
    )

    # Opponent popularity
    team_pop = dict(zip(teams["team_id"], teams["historical_popularity_score"]))
    team_cap = dict(zip(teams["team_id"], teams["arena_capacity"]))

    # Merge all
    df = games.merge(attendance, on="game_id", how="left")
    df = df.merge(weather, on="game_id", how="left")
    df = df.merge(
        promotions[["game_id", "promotion_flag", "promotion_type", "expected_promotion_lift_pct"]],
        on="game_id", how="left"
    )
    df = df.merge(ticket_rev, on="game_id", how="left")
    df = df.merge(con_rev, on="game_id", how="left")
    df = df.merge(merch_rev, on="game_id", how="left")

    # Derived features
    df["away_team_popularity"] = df["away_team_id"].map(team_pop).fillna(0.65)
    df["home_team_popularity"] = df["home_team_id"].map(team_pop).fillna(0.65)
    df["arena_capacity_feat"] = df["home_team_id"].map(team_cap).fillna(18000)

    df["temperature_f"] = df["temperature_f"].fillna(60.0)
    df["precipitation_flag"] = df["precipitation_flag"].fillna(False).astype(int)
    df["snow_flag"] = df["snow_flag"].fillna(False).astype(int)
    df["severe_weather_flag"] = df["severe_weather_flag"].fillna(False).astype(int)

    df["promotion_flag"] = df["promotion_flag"].fillna(False).astype(int)
    df["promotion_type"] = df["promotion_type"].fillna("None")
    df["expected_promotion_lift_pct"] = df["expected_promotion_lift_pct"].fillna(0.0)

    df["is_weekend"] = df["is_weekend"].astype(int)
    df["is_holiday_period"] = df["is_holiday_period"].astype(int)
    df["rivalry_flag"] = df["rivalry_flag"].astype(int)
    df["nationally_televised_flag"] = df["nationally_televised_flag"].astype(int)

    # Rolling attendance features (per home team, sorted by date)
    df = df.sort_values(["home_team_id", "game_date"]).reset_index(drop=True)
    df["rolling_att_3"] = (
        df.groupby("home_team_id")["actual_attendance"]
        .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
        .fillna(df["actual_attendance"].mean())
    )
    df["rolling_att_5"] = (
        df.groupby("home_team_id")["actual_attendance"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .fillna(df["actual_attendance"].mean())
    )

    # Day of week ordinal
    df["dow_ordinal"] = df["day_of_week"].map(
        {d: i for i, d in enumerate(DOW_ORDER)}
    ).fillna(3)

    # Revenue target
    df["total_concession_revenue"] = df["total_concession_revenue"].fillna(0)
    df["total_merchandise_revenue"] = df["total_merchandise_revenue"].fillna(0)
    df["total_net_ticket_revenue"] = df["total_net_ticket_revenue"].fillna(0)
    df["total_game_day_revenue"] = (
        df["total_net_ticket_revenue"]
        + df["total_concession_revenue"]
        + df["total_merchandise_revenue"]
    )

    # Fill remaining numeric NAs
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df.sort_values("game_date").reset_index(drop=True)


ATTENDANCE_FEATURES = [
    "is_weekend", "is_holiday_period", "rivalry_flag", "nationally_televised_flag",
    "promotion_flag", "expected_promotion_lift_pct",
    "home_team_win_pct_entering_game", "away_team_win_pct_entering_game",
    "home_team_recent_form", "away_team_recent_form",
    "home_team_popularity", "away_team_popularity",
    "temperature_f", "snow_flag", "severe_weather_flag", "precipitation_flag",
    "arena_capacity_feat", "rolling_att_3", "rolling_att_5",
    "dow_ordinal", "month",
    "promotion_type",
]

REVENUE_FEATURES = ATTENDANCE_FEATURES + [
    "actual_attendance", "capacity_pct",
    "avg_ticket_price_all", "total_tickets_sold",
]

ATTENDANCE_TARGET = "actual_attendance"
REVENUE_TARGET = "total_game_day_revenue"


def main():
    print("Building feature dataset...")
    df = build_features()

    att_cols = [c for c in ATTENDANCE_FEATURES if c in df.columns] + [ATTENDANCE_TARGET, "game_id", "season", "game_date"]
    rev_cols = [c for c in REVENUE_FEATURES if c in df.columns] + [REVENUE_TARGET, "game_id", "season", "game_date"]

    df_att = df[list(dict.fromkeys(att_cols))].dropna(subset=[ATTENDANCE_TARGET])
    df_rev = df[list(dict.fromkeys(rev_cols))].dropna(subset=[REVENUE_TARGET])

    df_att.to_csv(DATA_PROCESSED_DIR / "features_attendance.csv", index=False)
    df_rev.to_csv(DATA_PROCESSED_DIR / "features_revenue.csv", index=False)
    df.to_csv(DATA_PROCESSED_DIR / "features_full.csv", index=False)

    print(f"  features_attendance.csv: {len(df_att)} rows, {len(df_att.columns)} cols")
    print(f"  features_revenue.csv: {len(df_rev)} rows, {len(df_rev.columns)} cols")
    print(f"  features_full.csv: {len(df)} rows, {len(df.columns)} cols")
    print("Feature engineering complete.")


if __name__ == "__main__":
    main()
