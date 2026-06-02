"""Tests for simulate_business_data.py — verifies generated CSVs are valid."""

import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_SIMULATED_DIR
from src.simulate_business_data import (
    generate_teams, generate_games, generate_weather, generate_promotions,
    generate_attendance, generate_ticket_segments, generate_ticket_sales,
    generate_concessions, generate_merchandise, generate_fan_profiles,
)


@pytest.fixture(scope="module")
def teams():
    return generate_teams()


@pytest.fixture(scope="module")
def games(teams):
    return generate_games(teams)


@pytest.fixture(scope="module")
def promotions(games):
    return generate_promotions(games)


@pytest.fixture(scope="module")
def weather(games):
    return generate_weather(games)


@pytest.fixture(scope="module")
def attendance(games, teams, promotions, weather):
    return generate_attendance(games, teams, promotions, weather)


@pytest.fixture(scope="module")
def ticket_sales(games, attendance, promotions):
    return generate_ticket_sales(games, attendance, promotions)


@pytest.fixture(scope="module")
def concessions(games, attendance, promotions):
    return generate_concessions(games, attendance, promotions)


@pytest.fixture(scope="module")
def merchandise(games, attendance, promotions, teams):
    return generate_merchandise(games, attendance, promotions, teams)


@pytest.fixture(scope="module")
def fan_profiles():
    return generate_fan_profiles()


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------
def test_teams_row_count(teams):
    assert len(teams) == 30


def test_teams_required_columns(teams):
    required = ["team_id", "team_name", "team_city", "conference", "arena_capacity",
                "historical_popularity_score"]
    for col in required:
        assert col in teams.columns, f"Missing column: {col}"


def test_teams_unique_ids(teams):
    assert teams["team_id"].is_unique


def test_teams_capacity_positive(teams):
    assert (teams["arena_capacity"] > 0).all()


def test_teams_popularity_range(teams):
    assert teams["historical_popularity_score"].between(0, 1).all()


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------
def test_games_row_count(games):
    assert len(games) >= 6000


def test_games_required_columns(games):
    required = ["game_id", "season", "game_date", "home_team_id", "away_team_id",
                "rivalry_flag", "nationally_televised_flag", "is_weekend", "month"]
    for col in required:
        assert col in games.columns


def test_games_unique_ids(games):
    assert games["game_id"].is_unique


def test_games_no_self_matchup(games):
    assert (games["home_team_id"] != games["away_team_id"]).all()


def test_games_win_pct_range(games):
    assert games["home_team_win_pct_entering_game"].between(0, 1).all()
    assert games["away_team_win_pct_entering_game"].between(0, 1).all()


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
def test_attendance_no_negative(attendance):
    assert (attendance["actual_attendance"] >= 0).all()


def test_attendance_not_exceed_capacity(attendance):
    assert (attendance["actual_attendance"] <= attendance["arena_capacity"]).all()


def test_attendance_capacity_pct_range(attendance):
    assert (attendance["capacity_pct"] >= 0).all()
    assert (attendance["capacity_pct"] <= 100.0).all()


def test_attendance_tier_valid(attendance):
    valid_tiers = {"Low", "Medium", "High", "Sellout"}
    assert set(attendance["attendance_tier"].unique()).issubset(valid_tiers)


# ---------------------------------------------------------------------------
# Ticket Sales
# ---------------------------------------------------------------------------
def test_ticket_sales_no_negative_revenue(ticket_sales):
    assert (ticket_sales["gross_ticket_revenue"] >= 0).all()
    assert (ticket_sales["net_ticket_revenue"] >= 0).all()


def test_ticket_sales_sold_le_available(ticket_sales):
    assert (ticket_sales["tickets_sold"] <= ticket_sales["tickets_available"]).all()


def test_ticket_sales_required_columns(ticket_sales):
    required = ["ticket_sale_id", "game_id", "segment_id", "segment_name",
                "tickets_available", "tickets_sold", "avg_ticket_price",
                "gross_ticket_revenue", "net_ticket_revenue", "sell_through_rate"]
    for col in required:
        assert col in ticket_sales.columns


# ---------------------------------------------------------------------------
# Concessions
# ---------------------------------------------------------------------------
def test_concessions_no_negative_revenue(concessions):
    assert (concessions["gross_revenue"] >= 0).all()


def test_concessions_row_count(concessions, games):
    assert len(concessions) >= len(games) * 5  # 5 categories per game


# ---------------------------------------------------------------------------
# Merchandise
# ---------------------------------------------------------------------------
def test_merchandise_no_negative_revenue(merchandise):
    assert (merchandise["gross_revenue"] >= 0).all()


def test_merchandise_row_count(merchandise, games):
    assert len(merchandise) >= len(games) * 5


# ---------------------------------------------------------------------------
# Fan Profiles
# ---------------------------------------------------------------------------
def test_fan_profiles_count(fan_profiles):
    assert len(fan_profiles) >= 10000


def test_fan_profiles_required_columns(fan_profiles):
    required = ["fan_id", "loyalty_status", "avg_ticket_spend",
                "avg_concession_spend", "avg_merchandise_spend", "fan_value_score"]
    for col in required:
        assert col in fan_profiles.columns


def test_fan_profiles_no_negative_spend(fan_profiles):
    assert (fan_profiles["avg_ticket_spend"] >= 0).all()
    assert (fan_profiles["avg_concession_spend"] >= 0).all()
    assert (fan_profiles["avg_merchandise_spend"] >= 0).all()


def test_fan_profiles_value_score_range(fan_profiles):
    assert fan_profiles["fan_value_score"].between(0, 1).all()
