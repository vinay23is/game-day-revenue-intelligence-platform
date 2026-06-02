"""Tests for feature_engineering.py — verifies model-ready feature datasets."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR
from src.feature_engineering import (
    ATTENDANCE_FEATURES, REVENUE_PREGAME_FEATURES,
    ATTENDANCE_TARGET, REVENUE_TARGET,
)


@pytest.fixture(scope="module")
def att_features():
    path = DATA_PROCESSED_DIR / "features_attendance.csv"
    if not path.exists():
        pytest.skip("features_attendance.csv not found — run feature_engineering.py first")
    return pd.read_csv(path)


@pytest.fixture(scope="module")
def rev_features():
    path = DATA_PROCESSED_DIR / "features_revenue.csv"
    if not path.exists():
        pytest.skip("features_revenue.csv not found — run feature_engineering.py first")
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Attendance feature set
# ---------------------------------------------------------------------------
def test_attendance_target_column_exists(att_features):
    assert ATTENDANCE_TARGET in att_features.columns


def test_attendance_feature_columns_exist(att_features):
    for feat in ATTENDANCE_FEATURES:
        if feat != "promotion_type":  # categorical, present as-is
            assert feat in att_features.columns, f"Missing attendance feature: {feat}"


def test_attendance_target_no_nulls(att_features):
    assert att_features[ATTENDANCE_TARGET].notna().all()


def test_attendance_target_positive(att_features):
    assert (att_features[ATTENDANCE_TARGET] > 0).all()


def test_attendance_numeric_features_no_nulls(att_features):
    numeric_feats = [c for c in ATTENDANCE_FEATURES if c in att_features.columns and c != "promotion_type"]
    null_counts = att_features[numeric_feats].isnull().sum()
    assert null_counts.sum() == 0, f"Null values found: {null_counts[null_counts > 0]}"


def test_attendance_has_enough_rows(att_features):
    assert len(att_features) >= 5000


def test_attendance_rolling_features_exist(att_features):
    assert "rolling_att_3" in att_features.columns
    assert "rolling_att_5" in att_features.columns


def test_attendance_boolean_flags_binary(att_features):
    for col in ["is_weekend", "rivalry_flag", "nationally_televised_flag", "promotion_flag"]:
        if col in att_features.columns:
            assert att_features[col].isin([0, 1]).all(), f"{col} is not binary"


# ---------------------------------------------------------------------------
# Revenue pre-game feature set (no post-game leakage)
# ---------------------------------------------------------------------------
def test_revenue_target_column_exists(rev_features):
    assert REVENUE_TARGET in rev_features.columns


def test_revenue_target_no_nulls(rev_features):
    assert rev_features[REVENUE_TARGET].notna().all()


def test_revenue_target_positive(rev_features):
    assert (rev_features[REVENUE_TARGET] > 0).all()


def test_revenue_pregame_feature_columns_exist(rev_features):
    # New pre-game only features must exist
    required = ["rolling_rev_3", "rolling_rev_5", "planned_avg_base_price",
                "promotion_cost", "sponsor_value_estimate"]
    for feat in required:
        assert feat in rev_features.columns, f"Missing pre-game revenue feature: {feat}"


def test_revenue_no_leakage_columns(rev_features):
    # Post-game outcomes must NOT appear as input features
    forbidden = ["actual_attendance", "capacity_pct", "total_tickets_sold",
                 "avg_ticket_price_all", "total_gross_ticket_revenue",
                 "total_net_ticket_revenue", "total_concession_revenue",
                 "total_merchandise_revenue"]
    for col in forbidden:
        assert col not in rev_features.columns, (
            f"Leakage column '{col}' found in revenue feature set"
        )


def test_revenue_has_enough_rows(rev_features):
    assert len(rev_features) >= 5000


def test_rolling_revenue_features_non_negative(rev_features):
    assert (rev_features["rolling_rev_3"] >= 0).all()
    assert (rev_features["rolling_rev_5"] >= 0).all()


def test_planned_avg_price_positive(rev_features):
    assert (rev_features["planned_avg_base_price"] > 0).all()


# ---------------------------------------------------------------------------
# Cross-dataset consistency
# ---------------------------------------------------------------------------
def test_same_game_ids_in_both(att_features, rev_features):
    att_ids = set(att_features["game_id"])
    rev_ids = set(rev_features["game_id"])
    overlap = att_ids & rev_ids
    assert len(overlap) >= 5000, "Very few overlapping game IDs between att and rev features"
