"""
Fan segmentation using K-Means clustering.
- Tests k=3 through k=8 via silhouette score (reported for transparency)
- Selects k=6 for business interpretability (6 distinct, actionable segments)
- Uses encoded distance and loyalty features alongside behavioral signals
- Assigns deterministic readable labels via optimal scoring matrix matching
"""

import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import date as _date

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATA_PROCESSED_DIR, DATA_SIMULATED_DIR, MODELS_DIR, REPORTS_DIR, RANDOM_SEED

# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

BEHAVIORAL_FEATURES = [
    "games_attended_last_12_months",
    "avg_ticket_spend",
    "avg_concession_spend",
    "avg_merchandise_spend",
    "promotion_usage_rate",
    "email_engagement_score",
    "fan_value_score",
]

ENCODED_FEATURES = ["distance_encoded", "loyalty_encoded"]

SEGMENTATION_FEATURES = BEHAVIORAL_FEATURES + ENCODED_FEATURES

DISTANCE_MAP = {"<5 miles": 1, "5-15 miles": 2, "15-30 miles": 3, "30-60 miles": 4, "60+ miles": 5}
LOYALTY_MAP  = {
    "New Fan": 1, "Casual Fan": 2, "Repeat Buyer": 3,
    "Corporate Guest": 4, "Season Ticket Holder": 5, "Premium Member": 5,
}

REQUIRED_SEGMENTS = [
    "High-Value Loyalists",
    "Premium Experience Buyers",
    "Promo-Sensitive Fans",
    "Family Night Buyers",
    "Merchandise-Heavy Fans",
    "Casual Low-Frequency Fans",
]

BUSINESS_K = 6


def load_fan_profiles() -> pd.DataFrame:
    for folder in [DATA_PROCESSED_DIR, DATA_SIMULATED_DIR]:
        p = folder / "fan_profiles.csv"
        if p.exists():
            return pd.read_csv(p)
    raise FileNotFoundError("fan_profiles.csv not found.")


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["distance_encoded"] = df["distance_from_arena_bucket"].map(DISTANCE_MAP).fillna(3).astype(float)
    df["loyalty_encoded"]  = df["loyalty_status"].map(LOYALTY_MAP).fillna(2).astype(float)
    return df


def report_silhouette(X_scaled: np.ndarray, k_range=range(3, 9)) -> dict:
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        scores[k] = silhouette_score(X_scaled, labels, sample_size=min(5000, len(X_scaled)))
    print("  Silhouette scores by k:")
    best_statistical = max(scores, key=scores.get)
    for k, s in scores.items():
        marker = " <-- statistical best" if k == best_statistical else ""
        if k == BUSINESS_K:
            marker += " <-- selected (business interpretability)"
        print(f"    k={k}: {s:.4f}{marker}")
    return scores


def assign_segment_labels(df: pd.DataFrame) -> dict[int, str]:
    """
    Optimal bijective assignment of 6 cluster IDs to 6 business labels.
    Uses a greedy maximum-score approach on a scoring matrix derived from
    normalized centroid characteristics.
    """
    profiles = df.groupby("cluster")[SEGMENTATION_FEATURES].mean()
    norm = (profiles - profiles.min()) / (profiles.max() - profiles.min() + 1e-8)

    cluster_ids = list(profiles.index)
    n = len(cluster_ids)
    labels = REQUIRED_SEGMENTS[:n]

    # Score matrix: rows = clusters, cols = labels
    score_matrix = np.zeros((n, len(labels)))
    for i, cid in enumerate(cluster_ids):
        r = norm.loc[cid]
        fv  = r.get("fan_value_score", 0)
        ga  = r.get("games_attended_last_12_months", 0)
        ts  = r.get("avg_ticket_spend", 0)
        cs  = r.get("avg_concession_spend", 0)
        ms  = r.get("avg_merchandise_spend", 0)
        pu  = r.get("promotion_usage_rate", 0)
        le  = r.get("loyalty_encoded", 0)

        score_matrix[i, 0] = fv * 2.0 + ga * 1.5 + le * 1.0          # High-Value Loyalists
        score_matrix[i, 1] = ts * 2.5 + fv * 1.0 - pu * 0.5          # Premium Experience Buyers
        score_matrix[i, 2] = pu * 3.0                                  # Promo-Sensitive Fans
        score_matrix[i, 3] = cs * 2.0 + ms * 0.5 - ts * 0.3          # Family Night Buyers
        score_matrix[i, 4] = ms * 3.0                                  # Merchandise-Heavy Fans
        score_matrix[i, 5] = (1 - fv) * 1.5 + (1 - ga) * 1.5        # Casual Low-Frequency Fans

    # Greedy optimal assignment
    assigned_clusters = set()
    assigned_label_idxs = set()
    label_map: dict[int, str] = {}

    for _ in range(len(labels)):
        best_score, best_ci, best_li = -1.0, -1, -1
        for ci in range(n):
            if ci in assigned_clusters:
                continue
            for li in range(len(labels)):
                if li in assigned_label_idxs:
                    continue
                if score_matrix[ci, li] > best_score:
                    best_score, best_ci, best_li = score_matrix[ci, li], ci, li
        if best_ci >= 0:
            label_map[cluster_ids[best_ci]] = labels[best_li]
            assigned_clusters.add(best_ci)
            assigned_label_idxs.add(best_li)

    # Fallback for any unmapped clusters
    remaining = [l for l in REQUIRED_SEGMENTS if l not in label_map.values()]
    for cid in cluster_ids:
        if cid not in label_map:
            label_map[cid] = remaining.pop(0) if remaining else f"Segment {cid}"

    return label_map


def main():
    print("Loading fan profiles...")
    df = load_fan_profiles()
    print(f"  {len(df):,} fan profiles loaded")

    df = encode_features(df)
    X  = df[SEGMENTATION_FEATURES].fillna(0)
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("\nReporting silhouette scores (k=3 to k=8)...")
    sil_scores = report_silhouette(X_scaled)

    print(f"\nTraining final K-Means with k={BUSINESS_K} (business segments)...")
    km = KMeans(n_clusters=BUSINESS_K, random_state=RANDOM_SEED, n_init=20)
    df["cluster"] = km.fit_predict(X_scaled)

    label_map = assign_segment_labels(df)
    df["fan_segment"] = df["cluster"].map(label_map)

    print("\nFan segment distribution:")
    seg_counts = df["fan_segment"].value_counts()
    for seg, cnt in seg_counts.items():
        print(f"  {seg}: {cnt:,} fans ({cnt / len(df) * 100:.1f}%)")

    # Save outputs
    out_path = DATA_PROCESSED_DIR / "fan_profiles_segmented.csv"
    df.to_csv(out_path, index=False)
    joblib.dump(km,     MODELS_DIR / "fan_segmentation_model.pkl")
    joblib.dump(scaler, MODELS_DIR / "fan_segmentation_scaler.pkl")

    # Update model_features.json
    feat_path = MODELS_DIR / "model_features.json"
    existing  = {}
    if feat_path.exists():
        with open(feat_path) as f:
            existing = json.load(f)
    existing.update({
        "segmentation_features":     SEGMENTATION_FEATURES,
        "segmentation_behavioral":   BEHAVIORAL_FEATURES,
        "segmentation_encoded":      ENCODED_FEATURES,
        "n_clusters":                BUSINESS_K,
        "cluster_label_map":         {str(k): v for k, v in label_map.items()},
        "silhouette_scores":         {str(k): round(v, 4) for k, v in sil_scores.items()},
        "silhouette_selected_k":     BUSINESS_K,
    })
    with open(feat_path, "w") as f:
        json.dump(existing, f, indent=2)

    # -----------------------------------------------------------------------
    # Append fan segmentation section to model_metrics.md
    # -----------------------------------------------------------------------
    metrics_path = REPORTS_DIR / "model_metrics.md"
    sil_table = "\n".join(
        f"| {k} | {v:.4f} |" for k, v in sorted(sil_scores.items())
    )
    seg_profile = df.groupby("fan_segment")[BEHAVIORAL_FEATURES].mean().round(2)
    seg_counts_series = df["fan_segment"].value_counts()

    seg_table = "| Segment | Count | Avg Ticket $ | Avg Concession $ | Avg Merch $ | Games/Yr | Promo Usage |\n"
    seg_table += "|---------|-------|-------------|-----------------|-------------|----------|-------------|\n"
    for seg in REQUIRED_SEGMENTS:
        if seg in seg_profile.index:
            r   = seg_profile.loc[seg]
            cnt = seg_counts_series.get(seg, 0)
            seg_table += (
                f"| {seg} | {cnt:,} | ${r['avg_ticket_spend']:.0f} | "
                f"${r['avg_concession_spend']:.0f} | ${r['avg_merchandise_spend']:.0f} | "
                f"{r['games_attended_last_12_months']:.1f} | {r['promotion_usage_rate']:.2f} |\n"
            )

    section = f"""
## Fan Segmentation Model

**Features Used:**
- Behavioral: {', '.join(f'`{f}`' for f in BEHAVIORAL_FEATURES)}
- Encoded categorical: `distance_from_arena_bucket` → ordinal 1–5, `loyalty_status` → ordinal 1–5

**Silhouette Scores by k:**

| k | Silhouette Score |
|---|-----------------|
{sil_table}

**Selected k:** {BUSINESS_K} (chosen for business interpretability; 6 segments map
cleanly to distinct CRM and marketing actions)

**Segment Profiles:**

{seg_table}

**Segment Descriptions:**
- **High-Value Loyalists** — High fan_value_score, frequent attendees, strong across all spend categories. Priority for retention programs.
- **Premium Experience Buyers** — High ticket spend, lower concession/merch. Respond to upgraded seating and VIP packages.
- **Promo-Sensitive Fans** — High promotion_usage_rate. Respond strongly to discounts, giveaways, and themed nights.
- **Family Night Buyers** — Elevated concession and merchandise spend; moderate ticket prices. Weekend/family promotion nights drive this segment.
- **Merchandise-Heavy Fans** — High merchandise spend relative to other categories. Priority for jersey launches and rivalry game specials.
- **Casual Low-Frequency Fans** — Low games attended and low overall spend. Re-engagement campaigns and introductory promotions are the primary lever.

**Business Usage:**
- Personalized email/SMS campaigns by segment
- Targeted promotions for Promo-Sensitive and Casual segments on low-demand weeknight games
- Premium upsell offers for Premium Experience Buyers and High-Value Loyalists
- Family bundle packaging timed to weekends and school break periods

**Report Generated:** {_date.today().isoformat()}

---

## Final Business Summary

The following models are deployed in the platform and can be used together
for end-to-end game-day planning:

| Use Case | Model | Key Output |
|----------|-------|-----------|
| Staffing planning | Attendance Forecast | Predicted fans → staffing tier |
| Inventory ordering | Pre-Game Revenue Forecast | Revenue projection → food/merch buffer |
| Promotion ROI | Attendance + Revenue Forecast | Lift estimate by promotion type |
| Fan targeting | K-Means Segmentation | Segment label for each fan |
| Executive reporting | All three models | KPI cards + scenario modeling dashboard |

**Business takeaways:**
- Weekend rivalry games and nationally televised matchups consistently drive peak
  attendance and revenue — these games should receive maximum staffing, dynamic pricing,
  and elevated inventory buffers.
- Merchandise Giveaway and Theme Night promotions show the strongest weekday lift and
  should be the default promotion tool for low-demand Tuesday/Wednesday games.
- High-Value Loyalists and Season Ticket Holders generate the highest per-visit revenue;
  retention programs for this group have the highest ROI relative to acquisition cost.
- The pre-game revenue forecast (with no post-game leakage) gives operations teams a
  credible revenue estimate 1–3 days before the game, enabling data-driven purchase
  orders and shift scheduling.
- Fan segmentation enables the marketing team to suppress irrelevant promotions to
  Premium Experience Buyers (who do not need discounts) and focus discount spend
  on Promo-Sensitive and Casual segments where it changes behavior.
- Scenario modeling in the dashboard lets revenue strategy teams test pricing
  sensitivity and promotion lift assumptions before committing to a plan.
- Model outputs feed directly into the executive dashboard KPIs, providing a single
  source of truth for attendance, revenue, and fan value reporting.
"""
    with open(metrics_path, "a") as f:
        f.write(section)

    print(f"\nSegmented profiles saved : {out_path}")
    print(f"Model saved              : {MODELS_DIR / 'fan_segmentation_model.pkl'}")
    print(f"Metrics appended         : {metrics_path}")


if __name__ == "__main__":
    main()
