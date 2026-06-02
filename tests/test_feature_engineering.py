"""Tests for feature_engineering.py — verifies model-ready feature datasets."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR
from src.feature_engineering import (
    ATTENDANCE_FEATURES, REVENUE_FEATURES,
    ATTENDANCE_TARGET, REVENUE_TARGET
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
        if feat != "promotion_type":  # categorical, may be encoded
            assert feat in att_features.columns, f"Missing feature: {feat}"


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
# Revenue feature set
# ---------------------------------------------------------------------------
def test_revenue_target_column_exists(rev_features):
    assert REVENUE_TARGET in rev_features.columns


def test_revenue_target_no_nulls(rev_features):
    assert rev_features[REVENUE_TARGET].notna().all()


def test_revenue_target_positive(rev_features):
    assert (rev_features[REVENUE_TARGET] > 0).all()


def test_revenue_feature_columns_exist(rev_features):
    extra_revenue_feats = ["actual_attendance", "capacity_pct", "avg_ticket_price_all"]
    for feat in extra_revenue_feats:
        assert feat in rev_features.columns, f"Missing revenue feature: {feat}"


def test_revenue_has_enough_rows(rev_features):
    assert len(rev_features) >= 5000


def test_revenue_attendance_not_negative(rev_features):
    assert (rev_features["actual_attendance"] >= 0).all()


def test_revenue_capacity_pct_range(rev_features):
    assert (rev_features["capacity_pct"] >= 0).all()
    assert (rev_features["capacity_pct"] <= 100).all()


# ---------------------------------------------------------------------------
# Cross-dataset consistency
# ---------------------------------------------------------------------------
def test_same_game_ids_in_both(att_features, rev_features):
    att_ids = set(att_features["game_id"])
    rev_ids = set(rev_features["game_id"])
    overlap = att_ids & rev_ids
    assert len(overlap) >= 5000, "Very few overlapping game IDs between att and rev features"
