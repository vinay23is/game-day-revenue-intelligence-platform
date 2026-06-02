"""
Validates and cleans all simulated CSVs, then writes cleaned copies to data/processed/.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_SIMULATED_DIR, DATA_PROCESSED_DIR

ISSUES: list[str] = []


def _check(condition: bool, msg: str):
    if not condition:
        ISSUES.append(f"  WARNING: {msg}")
        print(f"  WARNING: {msg}")


def clean_teams(df: pd.DataFrame) -> pd.DataFrame:
    _check(df["team_id"].is_unique, "team_id has duplicates")
    _check(df["team_name"].is_unique, "team_name has duplicates")
    _check(df["arena_capacity"].min() > 0, "arena_capacity has non-positive values")
    _check(df["historical_popularity_score"].between(0, 1).all(),
           "popularity score out of [0,1]")
    return df.dropna(subset=["team_id", "team_name"])


def clean_games(df: pd.DataFrame) -> pd.DataFrame:
    _check(df["game_id"].is_unique, "game_id has duplicates")
    _check(df["home_team_id"].notna().all(), "games has null home_team_id")
    _check(df["away_team_id"].notna().all(), "games has null away_team_id")
    df["game_date"] = pd.to_datetime(df["game_date"])
    _check((df["game_date"].dt.year >= 2019).all(), "game_date before 2019")
    df["home_team_win_pct_entering_game"] = df[
        "home_team_win_pct_entering_game"
    ].clip(0, 1)
    df["away_team_win_pct_entering_game"] = df[
        "away_team_win_pct_entering_game"
    ].clip(0, 1)
    return df


def clean_attendance(df: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    _check(df["game_id"].is_unique, "attendance game_id has duplicates")
    _check((df["actual_attendance"] >= 0).all(), "negative attendance found")
    _check(
        (df["actual_attendance"] <= df["arena_capacity"]).all(),
        "attendance exceeds arena capacity"
    )
    df["actual_attendance"] = df["actual_attendance"].clip(lower=0)
    df["capacity_pct"] = (df["actual_attendance"] / df["arena_capacity"] * 100).round(2)
    return df


def clean_ticket_sales(df: pd.DataFrame) -> pd.DataFrame:
    _check((df["gross_ticket_revenue"] >= 0).all(), "negative gross ticket revenue")
    _check((df["net_ticket_revenue"] >= 0).all(), "negative net ticket revenue")
    _check(
        (df["tickets_sold"] <= df["tickets_available"]).all(),
        "tickets_sold > tickets_available"
    )
    df["tickets_sold"] = df.apply(
        lambda r: min(r["tickets_sold"], r["tickets_available"]), axis=1
    )
    df["gross_ticket_revenue"] = df["gross_ticket_revenue"].clip(lower=0)
    df["net_ticket_revenue"] = df["net_ticket_revenue"].clip(lower=0)
    df["discount_pct"] = df["discount_pct"].clip(0, 100)
    return df


def clean_concessions(df: pd.DataFrame) -> pd.DataFrame:
    _check((df["gross_revenue"] >= 0).all(), "negative concessions revenue")
    _check((df["gross_margin"] >= 0).all(), "negative concessions margin")
    df["gross_revenue"] = df["gross_revenue"].clip(lower=0)
    df["gross_margin"] = df["gross_margin"].clip(lower=0)
    return df


def clean_merchandise(df: pd.DataFrame) -> pd.DataFrame:
    _check((df["gross_revenue"] >= 0).all(), "negative merchandise revenue")
    _check((df["gross_margin"] >= 0).all(), "negative merchandise margin")
    df["gross_revenue"] = df["gross_revenue"].clip(lower=0)
    df["gross_margin"] = df["gross_margin"].clip(lower=0)
    return df


def clean_fan_profiles(df: pd.DataFrame) -> pd.DataFrame:
    _check(df["fan_id"].is_unique, "fan_id has duplicates")
    _check((df["avg_ticket_spend"] >= 0).all(), "negative avg_ticket_spend")
    df["avg_ticket_spend"] = df["avg_ticket_spend"].clip(lower=0)
    df["avg_concession_spend"] = df["avg_concession_spend"].clip(lower=0)
    df["avg_merchandise_spend"] = df["avg_merchandise_spend"].clip(lower=0)
    df["promotion_usage_rate"] = df["promotion_usage_rate"].clip(0, 1)
    df["email_engagement_score"] = df["email_engagement_score"].clip(0, 1)
    df["fan_value_score"] = df["fan_value_score"].clip(0, 1)
    return df


def clean_fan_transactions(df: pd.DataFrame) -> pd.DataFrame:
    _check((df["total_spend"] >= 0).all(), "negative total_spend in transactions")
    df["ticket_spend"] = df["ticket_spend"].clip(lower=0)
    df["concession_spend"] = df["concession_spend"].clip(lower=0)
    df["merchandise_spend"] = df["merchandise_spend"].clip(lower=0)
    df["total_spend"] = df["ticket_spend"] + df["concession_spend"] + df["merchandise_spend"]
    return df


def main():
    global ISSUES
    ISSUES = []

    tables = {
        "teams": clean_teams,
        "games": None,
        "attendance": None,
        "weather": lambda df: df,
        "promotions": lambda df: df,
        "ticket_segments": lambda df: df,
        "ticket_sales": clean_ticket_sales,
        "concessions": clean_concessions,
        "merchandise": clean_merchandise,
        "fan_profiles": clean_fan_profiles,
        "fan_transactions": clean_fan_transactions,
        "model_predictions": lambda df: df,
    }

    loaded: dict[str, pd.DataFrame] = {}
    for name in tables:
        path = DATA_SIMULATED_DIR / f"{name}.csv"
        if path.exists():
            loaded[name] = pd.read_csv(path)
            print(f"Loaded {name}.csv ({len(loaded[name])} rows)")
        else:
            print(f"MISSING: {name}.csv — run simulate_business_data.py first")

    # Special cleaners that need cross-table context
    if "teams" in loaded:
        loaded["teams"] = clean_teams(loaded["teams"])
    if "games" in loaded:
        loaded["games"] = clean_games(loaded["games"])
    if "attendance" in loaded and "games" in loaded:
        loaded["attendance"] = clean_attendance(loaded["attendance"], loaded["games"])

    for name, cleaner in tables.items():
        if name in ("teams", "games", "attendance"):
            continue
        if name in loaded and cleaner is not None:
            loaded[name] = cleaner(loaded[name])

    # Write cleaned files
    for name, df in loaded.items():
        out_path = DATA_PROCESSED_DIR / f"{name}.csv"
        df.to_csv(out_path, index=False)

    print(f"\nCleaned {len(loaded)} tables written to {DATA_PROCESSED_DIR}")
    if ISSUES:
        print(f"\n{len(ISSUES)} data quality issue(s) found:")
        for issue in ISSUES:
            print(issue)
    else:
        print("All data quality checks passed.")


if __name__ == "__main__":
    main()
