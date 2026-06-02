"""
Fan segmentation using K-Means clustering.
Selects k via silhouette score, assigns readable segment labels.
"""

import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR, MODELS_DIR, REPORTS_DIR, RANDOM_SEED

SEGMENTATION_FEATURES = [
    "games_attended_last_12_months",
    "avg_ticket_spend",
    "avg_concession_spend",
    "avg_merchandise_spend",
    "promotion_usage_rate",
    "email_engagement_score",
    "fan_value_score",
]

SEGMENT_NAMES = {
    0: "High-Value Fans",
    1: "Promo-Sensitive Fans",
    2: "Family Buyers",
    3: "Merchandise-Heavy Fans",
    4: "Concession-Heavy Fans",
    5: "Casual Low-Frequency Fans",
    6: "Corporate / Group Guests",
    7: "Season Ticket Loyalists",
}


def load_fan_profiles() -> pd.DataFrame:
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / "fan_profiles.csv"
        if p.exists():
            return pd.read_csv(p)
    raise FileNotFoundError("fan_profiles.csv not found.")


def pick_k(X_scaled: np.ndarray, k_range=range(3, 9)) -> int:
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        scores[k] = silhouette_score(X_scaled, labels, sample_size=min(5000, len(X_scaled)))
    best_k = max(scores, key=scores.get)
    print("  Silhouette scores by k:")
    for k, s in scores.items():
        marker = " <-- best" if k == best_k else ""
        print(f"    k={k}: {s:.4f}{marker}")
    return best_k


def assign_readable_labels(df: pd.DataFrame, k: int) -> dict[int, str]:
    """Map cluster IDs to human-readable names based on cluster centroids."""
    label_map = {}
    cluster_profiles = df.groupby("cluster")[SEGMENTATION_FEATURES].mean()

    for cluster_id in range(k):
        row = cluster_profiles.loc[cluster_id]
        # Simple heuristic label assignment
        if row["avg_ticket_spend"] > df["avg_ticket_spend"].quantile(0.75) and row["fan_value_score"] > 0.6:
            label = "High-Value Fans"
        elif row["promotion_usage_rate"] > df["promotion_usage_rate"].quantile(0.70):
            label = "Promo-Sensitive Fans"
        elif row["games_attended_last_12_months"] > 30:
            label = "Season Ticket Loyalists"
        elif row["avg_merchandise_spend"] > df["avg_merchandise_spend"].quantile(0.70):
            label = "Merchandise-Heavy Fans"
        elif row["avg_concession_spend"] > df["avg_concession_spend"].quantile(0.70):
            label = "Concession-Heavy Fans"
        elif row["avg_ticket_spend"] > 200 and row["avg_concession_spend"] < 20:
            label = "Corporate / Group Guests"
        elif row["games_attended_last_12_months"] < 5:
            label = "Casual Low-Frequency Fans"
        else:
            label = "Family Buyers"

        # Ensure no duplicates
        if label in label_map.values():
            label = f"{label} ({cluster_id})"
        label_map[cluster_id] = label

    return label_map


def main():
    print("Loading fan profiles...")
    df = load_fan_profiles()
    print(f"  {len(df)} fan profiles loaded")

    X = df[SEGMENTATION_FEATURES].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\nSelecting optimal k via silhouette score...")
    best_k = pick_k(X_scaled)
    print(f"\nTraining final K-Means with k={best_k}...")

    km = KMeans(n_clusters=best_k, random_state=RANDOM_SEED, n_init=20)
    df["cluster"] = km.fit_predict(X_scaled)

    label_map = assign_readable_labels(df, best_k)
    df["fan_segment"] = df["cluster"].map(label_map)

    print("\nFan segment distribution:")
    seg_counts = df["fan_segment"].value_counts()
    for seg, count in seg_counts.items():
        print(f"  {seg}: {count} fans ({count/len(df)*100:.1f}%)")

    # Segment profile summary
    seg_profile = (
        df.groupby("fan_segment")[
            SEGMENTATION_FEATURES + ["games_attended_last_12_months"]
        ]
        .mean()
        .round(3)
    )

    # Save segmented fan profiles
    out_path = DATA_PROCESSED_DIR / "fan_profiles_segmented.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSegmented profiles saved: {out_path}")

    # Save models
    joblib.dump(km, MODELS_DIR / "fan_segmentation_model.pkl")
    joblib.dump(scaler, MODELS_DIR / "fan_segmentation_scaler.pkl")

    # Update model_features.json
    feat_path = MODELS_DIR / "model_features.json"
    existing = {}
    if feat_path.exists():
        with open(feat_path) as f:
            existing = json.load(f)
    existing.update({
        "segmentation_features": SEGMENTATION_FEATURES,
        "n_clusters": best_k,
        "cluster_label_map": label_map,
    })
    with open(feat_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Append to business insights
    insights_path = REPORTS_DIR / "business_insights.md"
    seg_section = "\n## Fan Segmentation Results\n\n"
    seg_section += f"K-Means clustering identified **{best_k} distinct fan segments**.\n\n"
    seg_section += "| Segment | Count | Avg Ticket Spend | Avg Concession | Avg Merch | Games Attended |\n"
    seg_section += "|---------|-------|-----------------|----------------|-----------|----------------|\n"
    for seg in seg_counts.index:
        r = df[df["fan_segment"] == seg]
        seg_section += (
            f"| {seg} | {len(r)} | "
            f"${r['avg_ticket_spend'].mean():.0f} | "
            f"${r['avg_concession_spend'].mean():.0f} | "
            f"${r['avg_merchandise_spend'].mean():.0f} | "
            f"{r['games_attended_last_12_months'].mean():.1f} |\n"
        )
    seg_section += "\n"

    with open(insights_path, "a") as f:
        f.write(seg_section)

    print(f"Segmentation model saved: {MODELS_DIR / 'fan_segmentation_model.pkl'}")


if __name__ == "__main__":
    main()
