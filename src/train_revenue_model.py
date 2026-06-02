"""
Pre-Game Revenue Forecast Model
Trains total game-day revenue prediction using ONLY features available before
the game starts. Post-game outcomes (actual attendance, actual ticket sales,
actual concessions/merchandise revenue) are deliberately excluded.

Target: total_game_day_revenue = net_ticket_revenue + concessions + merchandise
"""

import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import date

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
from src.utils import mape
from src.feature_engineering import REVENUE_PREGAME_FEATURES, REVENUE_TARGET

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except Exception:
    HAS_XGB = False


def load_data():
    path = DATA_PROCESSED_DIR / "features_revenue.csv"
    if not path.exists():
        raise FileNotFoundError(
            "features_revenue.csv not found. Run feature_engineering.py first."
        )
    df = pd.read_csv(path, parse_dates=["game_date"])
    df = df[df[REVENUE_TARGET] > 0].copy()
    return df


def split_by_season(df: pd.DataFrame):
    seasons = sorted(df["season"].unique())
    test_season = seasons[-1]
    train = df[df["season"] < test_season].copy()
    test  = df[df["season"] == test_season].copy()
    print(f"  Train seasons: {sorted(train['season'].unique())} ({len(train)} rows)")
    print(f"  Test season:   {test_season} ({len(test)} rows)")
    return train, test


def build_preprocessor(df: pd.DataFrame, feature_list: list):
    cat_cols = [c for c in feature_list if c in df.columns and df[c].dtype == object]
    num_cols = [c for c in feature_list if c in df.columns and df[c].dtype != object]
    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ])
    return pre, num_cols, cat_cols


def evaluate(y_true, y_pred, model_name: str) -> dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    m    = mape(np.array(y_true), np.array(y_pred))
    print(f"  {model_name}: MAE=${mae:,.0f}  RMSE=${rmse:,.0f}  R²={r2:.4f}  MAPE={m:.2f}%")
    return {"model": model_name, "mae": mae, "rmse": rmse, "r2": r2, "mape": m}


def main():
    print("Loading pre-game revenue feature data...")
    df = load_data()
    train, test = split_by_season(df)

    available_feats = [c for c in REVENUE_PREGAME_FEATURES if c in df.columns]
    X_train = train[available_feats]
    y_train = train[REVENUE_TARGET]
    X_test  = test[available_feats]
    y_test  = test[REVENUE_TARGET]

    pre, num_cols, cat_cols = build_preprocessor(X_train, available_feats)

    estimators = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(
            n_estimators=200, max_depth=14, random_state=RANDOM_SEED, n_jobs=-1
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

    print("\nTraining pre-game revenue models...")
    results = []
    pipelines = {}
    for name, est in estimators.items():
        pipe = Pipeline([("preprocessor", pre), ("model", est)])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        metrics = evaluate(y_test, y_pred, name)
        results.append(metrics)
        pipelines[name] = (pipe, y_pred)

    best = max(results, key=lambda x: x["r2"])
    best_name = best["model"]
    best_pipe, best_pred = pipelines[best_name]
    print(f"\nBest pre-game revenue model: {best_name} (R²={best['r2']:.4f})")

    joblib.dump(best_pipe, MODELS_DIR / "revenue_model.pkl")

    # Feature importance
    feat_names = num_cols + list(
        best_pipe.named_steps["preprocessor"]
        .named_transformers_["cat"]
        .get_feature_names_out(cat_cols)
    )
    model_step = best_pipe.named_steps["model"]
    fi_dict = {}
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

    # Update model_features.json
    feat_path = MODELS_DIR / "model_features.json"
    existing = {}
    if feat_path.exists():
        with open(feat_path) as f:
            existing = json.load(f)
    existing.update({
        "revenue_pregame_features": available_feats,
        "revenue_target": REVENUE_TARGET,
        "best_revenue_model": best_name,
        "revenue_feature_importances": fi_dict,
        "revenue_leakage_excluded": [
            "actual_attendance", "capacity_pct", "total_tickets_sold",
            "avg_ticket_price_all", "net_ticket_revenue",
            "concessions_actual", "merchandise_actual",
        ],
    })
    with open(feat_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Save predictions
    test_copy = test[["game_id", REVENUE_TARGET]].copy()
    test_copy["predicted_total_revenue"] = np.round(best_pred, 2)
    test_copy["revenue_prediction_error"] = (
        test_copy["predicted_total_revenue"] - test_copy[REVENUE_TARGET]
    )
    pred_path = DATA_PROCESSED_DIR / "revenue_predictions.csv"
    test_copy.to_csv(pred_path, index=False)

    # -----------------------------------------------------------------------
    # Write comprehensive metrics section
    # -----------------------------------------------------------------------
    leakage_note = (
        "**Leakage Prevention:** The following post-game variables are "
        "**explicitly excluded** from this model: `actual_attendance`, "
        "`capacity_pct` (derived from actual attendance), `total_tickets_sold`, "
        "`avg_ticket_price_all` (actual sales outcome), `net_ticket_revenue`, "
        "`concession_revenue`, and `merchandise_revenue`. Only features available "
        "before the game starts are used as inputs."
    )

    feat_str = "\n".join(f"  - `{f}`" for f in available_feats)
    fi_str = ""
    if fi_dict:
        fi_str = "\n**Top Feature Importances:**\n\n"
        for feat, imp in sorted(fi_dict.items(), key=lambda x: -x[1])[:10]:
            fi_str += f"- `{feat}`: {imp:.4f}\n"

    metrics_path = REPORTS_DIR / "model_metrics.md"
    section = f"""
## Pre-Game Revenue Forecast Model

**Purpose:** Forecast total game-day revenue before the game occurs, enabling staffing,
inventory, and partnership planning without waiting for game-day outcomes.

**Target Variable:** `total_game_day_revenue` (net ticket revenue + concessions + merchandise)

**Pre-Game Features Used:**
{feat_str}

{leakage_note}

**Models Compared:**

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
"""
    for r in results:
        section += f"| {r['model']} | ${r['mae']:,.0f} | ${r['rmse']:,.0f} | {r['r2']:.4f} | {r['mape']:.2f}% |\n"

    section += f"""
**Selected Model:** {best_name}

**Why Selected:** Highest R² on held-out test season, indicating the strongest
generalization to unseen game schedules.

{fi_str}

**Business Interpretation:**
The pre-game revenue forecast enables the business intelligence team to:
- Set staffing levels and shift schedules before the game
- Calculate concessions and merchandise purchase orders 1–3 days in advance
- Set realistic revenue targets for sponsor and partner reporting
- Flag unusually low projections for promotional intervention

**Limitations:**
- Model is trained on synthetic data; real-world accuracy depends on actual
  ticketing, POS, and CRM data quality
- Pre-game features exclude game-day surprises (weather changes, star player
  injuries, last-minute demand spikes)
- Revenue model R² on synthetic data reflects that the same demand signals
  drive both attendance and revenue in the simulation

**Test Season:** {df["season"].max()}
**Report Generated:** {date.today().isoformat()}

"""
    with open(metrics_path, "a") as f:
        f.write(section)

    print(f"\nModel saved        : {MODELS_DIR / 'revenue_model.pkl'}")
    print(f"Predictions saved  : {pred_path}")
    print(f"Metrics appended   : {metrics_path}")


if __name__ == "__main__":
    main()
