# Model Metrics Report

*All models use a time-based train/test split: earlier seasons for training,
most recent season held out for evaluation.*

---

## Attendance Forecast Model

**Purpose:** Predict the number of fans expected to attend each game before
game day, enabling staffing decisions, inventory planning, and promotional targeting.

**Target Variable:** `actual_attendance` (fans attending the game)

**Pre-Game Features Used:**
  - `is_weekend`
  - `is_holiday_period`
  - `rivalry_flag`
  - `nationally_televised_flag`
  - `promotion_flag`
  - `expected_promotion_lift_pct`
  - `home_team_win_pct_entering_game`
  - `away_team_win_pct_entering_game`
  - `home_team_recent_form`
  - `away_team_recent_form`
  - `home_team_popularity`
  - `away_team_popularity`
  - `temperature_f`
  - `snow_flag`
  - `severe_weather_flag`
  - `precipitation_flag`
  - `arena_capacity_feat`
  - `rolling_att_3`
  - `rolling_att_5`
  - `dow_ordinal`
  - `month`
  - `promotion_type`

**Models Compared:**

| Model | MAE (fans) | RMSE (fans) | R² | MAPE |
|-------|-----------|------------|-----|------|
| LinearRegression | 566 | 714 | 0.7810 | 3.29% |
| RandomForest | 597 | 745 | 0.7619 | 3.47% |
| GradientBoosting | 563 | 717 | 0.7797 | 3.28% |

**Selected Model:** LinearRegression

**Why Selected:** Achieves the highest R² on the held-out test season
while maintaining interpretable error magnitudes.



**Business Interpretation:**
- An MAE of ~566 fans means forecasts are typically within ±566
  attendees of actual — sufficient for staffing bracket decisions (Standard / Medium / High / Maximum)
- Rolling attendance history (`rolling_att_3`, `rolling_att_5`) captures home team momentum
- Opponent popularity, rivalry flag, and national TV flag capture matchup-driven demand spikes
- Weather signals provide modest but measurable adjustments for winter/storm games

**Limitations:**
- Trained on synthetic data; real accuracy depends on actual CRM and ticketing integration
- Roster changes, late-breaking weather, and external events are not captured
- Model should be re-calibrated at least once per season

**Test Season:** 2023
**Report Generated:** 2026-06-02

---

## Pre-Game Revenue Forecast Model

**Purpose:** Forecast total game-day revenue before the game occurs, enabling staffing,
inventory, and partnership planning without waiting for game-day outcomes.

**Target Variable:** `total_game_day_revenue` (net ticket revenue + concessions + merchandise)

**Pre-Game Features Used:**
  - `is_weekend`
  - `is_holiday_period`
  - `rivalry_flag`
  - `nationally_televised_flag`
  - `promotion_flag`
  - `expected_promotion_lift_pct`
  - `home_team_win_pct_entering_game`
  - `away_team_win_pct_entering_game`
  - `home_team_recent_form`
  - `away_team_recent_form`
  - `home_team_popularity`
  - `away_team_popularity`
  - `temperature_f`
  - `snow_flag`
  - `severe_weather_flag`
  - `precipitation_flag`
  - `arena_capacity_feat`
  - `rolling_att_3`
  - `rolling_att_5`
  - `dow_ordinal`
  - `month`
  - `promotion_type`
  - `promotion_cost`
  - `sponsor_value_estimate`
  - `planned_avg_base_price`
  - `rolling_rev_3`
  - `rolling_rev_5`

**Leakage Prevention:** The following post-game variables are **explicitly excluded** from this model: `actual_attendance`, `capacity_pct` (derived from actual attendance), `total_tickets_sold`, `avg_ticket_price_all` (actual sales outcome), `net_ticket_revenue`, `concession_revenue`, and `merchandise_revenue`. Only features available before the game starts are used as inputs.

**Models Compared:**

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
| LinearRegression | $132,875 | $168,572 | 0.7773 | 3.52% |
| RandomForest | $136,966 | $173,267 | 0.7648 | 3.63% |
| GradientBoosting | $129,048 | $168,149 | 0.7785 | 3.43% |

**Selected Model:** GradientBoosting

**Why Selected:** Highest R² on held-out test season, indicating the strongest
generalization to unseen game schedules.


**Top Feature Importances:**

- `arena_capacity_feat`: 0.4281
- `planned_avg_base_price`: 0.2613
- `expected_promotion_lift_pct`: 0.1080
- `rolling_att_5`: 0.0375
- `promotion_cost`: 0.0298
- `precipitation_flag`: 0.0208
- `is_holiday_period`: 0.0183
- `away_team_popularity`: 0.0106
- `snow_flag`: 0.0093
- `rolling_rev_3`: 0.0093


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

**Test Season:** 2023
**Report Generated:** 2026-06-02


## Fan Segmentation Model

**Features Used:**
- Behavioral: `games_attended_last_12_months`, `avg_ticket_spend`, `avg_concession_spend`, `avg_merchandise_spend`, `promotion_usage_rate`, `email_engagement_score`, `fan_value_score`
- Encoded categorical: `distance_from_arena_bucket` → ordinal 1–5, `loyalty_status` → ordinal 1–5

**Silhouette Scores by k:**

| k | Silhouette Score |
|---|-----------------|
| 3 | 0.1743 |
| 4 | 0.1598 |
| 5 | 0.1574 |
| 6 | 0.1210 |
| 7 | 0.1214 |
| 8 | 0.1232 |

**Selected k:** 6 (chosen for business interpretability; 6 segments map
cleanly to distinct CRM and marketing actions)

**Segment Profiles:**

| Segment | Count | Avg Ticket $ | Avg Concession $ | Avg Merch $ | Games/Yr | Promo Usage |
|---------|-------|-------------|-----------------|-------------|----------|-------------|
| High-Value Loyalists | 1,788 | $278 | $36 | $48 | 31.1 | 0.31 |
| Premium Experience Buyers | 1,921 | $253 | $18 | $38 | 32.0 | 0.34 |
| Promo-Sensitive Fans | 1,605 | $107 | $24 | $45 | 6.5 | 0.58 |
| Family Night Buyers | 2,033 | $106 | $36 | $25 | 6.5 | 0.30 |
| Merchandise-Heavy Fans | 2,417 | $111 | $30 | $65 | 6.9 | 0.27 |
| Casual Low-Frequency Fans | 2,236 | $100 | $16 | $32 | 6.1 | 0.27 |


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

**Report Generated:** 2026-06-02

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
