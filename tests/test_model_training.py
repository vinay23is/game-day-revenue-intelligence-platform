"""Tests for model training — verifies model files, metrics, and predictions are created."""

import pytest
import json
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import MODELS_DIR, REPORTS_DIR, DATA_PROCESSED_DIR


def test_attendance_model_file_exists():
    assert (MODELS_DIR / "attendance_model.pkl").exists(), \
        "attendance_model.pkl not found — run train_attendance_model.py"


def test_revenue_model_file_exists():
    assert (MODELS_DIR / "revenue_model.pkl").exists(), \
        "revenue_model.pkl not found — run train_revenue_model.py"


def test_segmentation_model_file_exists():
    assert (MODELS_DIR / "fan_segmentation_model.pkl").exists(), \
        "fan_segmentation_model.pkl not found — run segmentation.py"


def test_model_features_json_exists():
    assert (MODELS_DIR / "model_features.json").exists()


def test_model_features_json_valid():
    path = MODELS_DIR / "model_features.json"
    if not path.exists():
        pytest.skip("model_features.json not found")
    with open(path) as f:
        meta = json.load(f)
    assert "attendance_features" in meta
    assert "revenue_features" in meta
    assert len(meta["attendance_features"]) > 5


def test_model_features_json_has_best_models():
    path = MODELS_DIR / "model_features.json"
    if not path.exists():
        pytest.skip("model_features.json not found")
    with open(path) as f:
        meta = json.load(f)
    assert "best_attendance_model" in meta
    assert "best_revenue_model" in meta
    assert meta["best_attendance_model"] in [
        "LinearRegression", "RandomForest", "GradientBoosting", "XGBoost"
    ]


def test_metrics_report_exists():
    assert (REPORTS_DIR / "model_metrics.md").exists(), \
        "model_metrics.md not found — run train_attendance_model.py"


def test_metrics_report_non_empty():
    path = REPORTS_DIR / "model_metrics.md"
    if not path.exists():
        pytest.skip("model_metrics.md not found")
    content = path.read_text()
    assert len(content) > 100
    assert "MAE" in content
    assert "R²" in content


def test_attendance_predictions_csv_exists():
    path = DATA_PROCESSED_DIR / "attendance_predictions.csv"
    assert path.exists(), "attendance_predictions.csv not found"


def test_attendance_predictions_columns():
    path = DATA_PROCESSED_DIR / "attendance_predictions.csv"
    if not path.exists():
        pytest.skip("attendance_predictions.csv not found")
    df = pd.read_csv(path)
    assert "game_id" in df.columns
    assert "predicted_attendance" in df.columns
    assert "actual_attendance" in df.columns


def test_attendance_predictions_no_null_preds():
    path = DATA_PROCESSED_DIR / "attendance_predictions.csv"
    if not path.exists():
        pytest.skip("attendance_predictions.csv not found")
    df = pd.read_csv(path)
    assert df["predicted_attendance"].notna().all()


def test_revenue_predictions_csv_exists():
    path = DATA_PROCESSED_DIR / "revenue_predictions.csv"
    assert path.exists(), "revenue_predictions.csv not found"


def test_revenue_predictions_positive():
    path = DATA_PROCESSED_DIR / "revenue_predictions.csv"
    if not path.exists():
        pytest.skip("revenue_predictions.csv not found")
    df = pd.read_csv(path)
    assert (df["predicted_total_revenue"] > 0).all()


def test_segmented_fan_profiles_csv_exists():
    path = DATA_PROCESSED_DIR / "fan_profiles_segmented.csv"
    assert path.exists(), "fan_profiles_segmented.csv not found — run segmentation.py"


def test_segmented_fan_profiles_has_segment_column():
    path = DATA_PROCESSED_DIR / "fan_profiles_segmented.csv"
    if not path.exists():
        pytest.skip("fan_profiles_segmented.csv not found")
    df = pd.read_csv(path)
    assert "fan_segment" in df.columns or "cluster" in df.columns


def test_segmented_fan_profiles_no_null_segments():
    path = DATA_PROCESSED_DIR / "fan_profiles_segmented.csv"
    if not path.exists():
        pytest.skip("fan_profiles_segmented.csv not found")
    df = pd.read_csv(path)
    if "fan_segment" in df.columns:
        assert df["fan_segment"].notna().all()
