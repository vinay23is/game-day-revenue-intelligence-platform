"""
Trains attendance prediction models and saves the best one to models/.
"""

import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, MODELS_DIR, REPORTS_DIR, RANDOM_SEED
from src.utils import mape, append_to_md
from src.feature_engineering import ATTENDANCE_FEATURES, ATTENDANCE_TARGET

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except Exception:
    HAS_XGB = False

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    path = DATA_PROCESSED_DIR / "features_attendance.csv"
    if not path.exists():
        raise FileNotFoundError(
            "features_attendance.csv not found. Run feature_engineering.py first."
        )
    df = pd.read_csv(path, parse_dates=["game_date"])
    return df


def split_by_season(df: pd.DataFrame):
    """Time-based split: train on older seasons, test on most recent."""
    seasons = sorted(df["season"].unique())
    test_season = seasons[-1]
    train = df[df["season"] < test_season].copy()
    test = df[df["season"] == test_season].copy()
    print(f"  Train seasons: {sorted(train['season'].unique())} ({len(train)} rows)")
    print(f"  Test season:   {test_season} ({len(test)} rows)")
    return train, test


def build_preprocessor(df: pd.DataFrame):
    cat_cols = [c for c in ATTENDANCE_FEATURES if df[c].dtype == object]
    num_cols = [c for c in ATTENDANCE_FEATURES if c in df.columns and df[c].dtype != object]

    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ])
    return pre, num_cols, cat_cols


def evaluate(y_true, y_pred, model_name: str) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    m = mape(np.array(y_true), np.array(y_pred))
    print(f"  {model_name}: MAE={mae:.0f}  RMSE={rmse:.0f}  R²={r2:.4f}  MAPE={m:.2f}%")
    return {"model": model_name, "mae": mae, "rmse": rmse, "r2": r2, "mape": m}


def main():
    print("Loading data...")
    df = load_data()
    train, test = split_by_season(df)

    available_feats = [c for c in ATTENDANCE_FEATURES if c in df.columns]
    X_train = train[available_feats]
    y_train = train[ATTENDANCE_TARGET]
    X_test = test[available_feats]
    y_test = test[ATTENDANCE_TARGET]

    pre, num_cols, cat_cols = build_preprocessor(X_train)

    estimators = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=200, max_depth=12, random_state=RANDOM_SEED, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.05, max_depth=5,
            random_state=RANDOM_SEED
        ),
    }
    if HAS_XGB:
        estimators["XGBoost"] = XGBRegressor(
            n_estimators=200, learning_rate=0.05, max_depth=6,
            random_state=RANDOM_SEED, verbosity=0
        )

    print("\nTraining attendance models...")
    results = []
    pipelines = {}
    for name, est in estimators.items():
        pipe = Pipeline([("preprocessor", pre), ("model", est)])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        metrics = evaluate(y_test, y_pred, name)
        results.append(metrics)
        pipelines[name] = (pipe, y_pred)

    # Best model by R²
    best = max(results, key=lambda x: x["r2"])
    best_name = best["model"]
    best_pipe, best_pred = pipelines[best_name]
    print(f"\nBest model: {best_name} (R²={best['r2']:.4f})")

    # Save model
    joblib.dump(best_pipe, MODELS_DIR / "attendance_model.pkl")

    # Feature importance
    feat_names = num_cols + list(
        best_pipe.named_steps["preprocessor"]
        .named_transformers_["cat"]
        .get_feature_names_out(cat_cols)
    )
    model_step = best_pipe.named_steps["model"]
    if hasattr(model_step, "feature_importances_"):
        importances = model_step.feature_importances_
        fi = (
            pd.Series(importances, index=feat_names)
            .sort_values(ascending=False)
            .head(15)
        )
        print("\nTop feature importances:")
        for feat, imp in fi.items():
            print(f"  {feat}: {imp:.4f}")
        fi_dict = fi.to_dict()
    else:
        fi_dict = {}

    # Save feature list
    feature_meta = {
        "attendance_features": available_feats,
        "attendance_target": ATTENDANCE_TARGET,
        "best_attendance_model": best_name,
        "attendance_feature_importances": fi_dict,
    }
    feat_path = MODELS_DIR / "model_features.json"
    if feat_path.exists():
        with open(feat_path) as f:
            existing = json.load(f)
        existing.update(feature_meta)
        feature_meta = existing
    with open(feat_path, "w") as f:
        json.dump(feature_meta, f, indent=2)

    # Save predictions to model_predictions.csv
    test_copy = test.copy()
    test_copy["predicted_attendance"] = best_pred.astype(int)
    test_copy["attendance_prediction_error"] = (
        test_copy["predicted_attendance"] - test_copy[ATTENDANCE_TARGET]
    )
    pred_path = DATA_PROCESSED_DIR / "attendance_predictions.csv"
    test_copy[["game_id", "predicted_attendance", ATTENDANCE_TARGET, "attendance_prediction_error"]].to_csv(
        pred_path, index=False
    )

    # Write metrics report
    metrics_path = REPORTS_DIR / "model_metrics.md"
    content = f"""# Model Metrics Report

## Attendance Prediction Models

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
"""
    for r in results:
        content += f"| {r['model']} | {r['mae']:.0f} | {r['rmse']:.0f} | {r['r2']:.4f} | {r['mape']:.2f}% |\n"
    content += f"\n**Best Model:** {best_name}  \n"
    content += f"**Test Season:** {df['season'].max()}  \n"
    content += f"**Train/Test Split:** Time-based (earlier seasons for training)  \n\n"

    with open(metrics_path, "w") as f:
        f.write(content)

    print(f"\nModel saved: {MODELS_DIR / 'attendance_model.pkl'}")
    print(f"Metrics saved: {metrics_path}")
    print(f"Predictions saved: {pred_path}")


if __name__ == "__main__":
    main()
