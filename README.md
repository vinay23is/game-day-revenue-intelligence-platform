# Game-Day Revenue Intelligence Platform

A sports business intelligence and data science platform for game-day demand forecasting, revenue analytics, fan segmentation, and scenario modeling. Built with Python, SQL, PostgreSQL, Scikit-learn, and Streamlit, this platform demonstrates the full analytics stack from raw data engineering through machine learning to interactive executive dashboards.

The platform answers ten core business questions: which games will have the highest attendance, which opponents and contexts drive demand, where is revenue underperforming, how should concessions and merchandise inventory be scaled, and which fan segments deserve the most marketing attention — all before the first fan walks through the door.

---

## Business Problem

Sports and entertainment organizations need to forecast game-day demand and understand what drives revenue. Attendance directly affects ticket revenue, staffing costs, concessions inventory, merchandise planning, promotional ROI, and partnership value. This platform gives a business intelligence team the tools to answer demand and revenue questions at both the game level and the portfolio level — and to run what-if scenarios for operational planning.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Attendance Forecasting** | Train/test ML models with time-based splits to predict per-game attendance from opponent, scheduling, promotion, weather, and team performance signals |
| **Revenue Prediction** | Predict total game-day revenue (tickets + concessions + merchandise) using ensemble models |
| **Ticket Segment Analysis** | Compare sell-through, average price, and net revenue across 9 pricing tiers |
| **Concessions & Merchandise** | Per-cap spend, gross margin by category, and demand-based inventory recommendations |
| **Fan Segmentation** | K-Means clustering (k=6) on behavioral and encoded features to identify six actionable business segments |
| **Promotion Effectiveness** | Measure attendance lift and revenue impact by promotion type |
| **Scenario Modeling** | Interactive sliders for attendance, pricing, promotion, and demand changes with real-time revenue and inventory projections |
| **Executive Dashboard** | Six-page Streamlit dashboard with KPI cards, Plotly charts, and drill-down tables |
| **SQL Analytics** | 40+ business queries using CTEs, window functions, rankings, aggregations, and CASE logic |
| **PostgreSQL Schema** | Normalized relational data model with foreign keys, check constraints, and performance indexes |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Data manipulation | Pandas, NumPy |
| Machine learning | Scikit-learn (Linear Regression, Random Forest, Gradient Boosting), XGBoost |
| Dashboard | Streamlit, Plotly |
| Database | PostgreSQL 15, SQLAlchemy |
| Containerization | Docker, Docker Compose |
| Testing | pytest |
| Notebooks | Jupyter |

---

## Data

This project uses **fictional professional basketball-style teams** and **simulated business data** for ticketing, concessions, merchandise, promotions, and fan profiles to demonstrate sports analytics workflows. The 30 teams, arenas, and all game-day revenue figures are entirely invented — no official league affiliation or team partnership is implied or claimed. The simulated fields are designed to reflect realistic sports business intelligence patterns where real internal team revenue data is private.

**Data generated at runtime** (no external download required):

| Table | Rows | Description |
|-------|------|-------------|
| `teams` | 30 | Franchise metadata, arena capacity, market tier |
| `games` | ~6,150 | Schedule with opponent, home/away, date, win pct context |
| `attendance` | ~6,150 | Actual and expected attendance, capacity %, tier |
| `weather` | ~6,150 | Temperature, precipitation, snow, severe weather |
| `promotions` | ~6,150 | Promotion type, cost, expected lift, sponsor value |
| `ticket_segments` | 9 | Pricing tiers from Premium Courtside to Student Promo |
| `ticket_sales` | ~55,000 | Per-game per-segment: price, sold, revenue, sell-through |
| `concessions` | ~31,000 | 5 categories × games: units, revenue, margin, inventory |
| `merchandise` | ~31,000 | 5 categories × games: units, revenue, margin, inventory |
| `fan_profiles` | 12,000 | Fan demographics, loyalty tier, spend averages, engagement |
| `fan_transactions` | 120,000 | Individual fan-game spend records |
| `model_predictions` | ~6,150 | Model output shell (populated by training scripts) |

---

## Architecture

```
Data Generation (simulate_business_data.py)
    ↓
Data Cleaning & Validation (data_cleaning.py)
    ↓
PostgreSQL / CSV Storage
    ↓
Feature Engineering (feature_engineering.py)
    ↓
ML Models (train_attendance_model.py, train_revenue_model.py, segmentation.py)
    ↓
SQL Analytics (sql/03_business_analysis_queries.sql + views)
    ↓
Business Reports (generate_reports.py)
    ↓
Streamlit Dashboard (dashboard/app.py)
```

---

## Database Schema

| Table | Primary Key | Foreign Keys | Description |
|-------|-------------|--------------|-------------|
| `teams` | `team_id` | — | 30 franchises with arena and market data |
| `games` | `game_id` | `home_team_id`, `away_team_id` → teams | Full schedule with context signals |
| `weather` | `weather_id` | `game_id` → games | Temperature and condition per game |
| `promotions` | `promotion_id` | `game_id` → games | Promotion type, cost, sponsor value |
| `attendance` | `attendance_id` | `game_id` → games | Actual vs. expected with tier classification |
| `ticket_segments` | `segment_id` | — | 9 pricing tier definitions |
| `ticket_sales` | `ticket_sale_id` | `game_id`, `segment_id` | Per-game per-segment ticketing |
| `concessions` | `concession_id` | `game_id` → games | 5-category concessions per game |
| `merchandise` | `merchandise_id` | `game_id` → games | 5-category merchandise per game |
| `fan_profiles` | `fan_id` | — | 12,000 fan behavioral profiles |
| `fan_transactions` | `transaction_id` | `fan_id`, `game_id` | 120,000 individual spend records |
| `model_predictions` | `prediction_id` | `game_id` → games | ML model output per game |

---

## SQL Analysis

The project includes **40+ SQL business queries** in `sql/03_business_analysis_queries.sql` and **7 reusable analytical views** in `sql/04_kpi_views.sql`.

SQL techniques used: `JOIN`, `LEFT JOIN`, CTEs (`WITH`), window functions (`RANK`, `DENSE_RANK`), `CASE WHEN`, `NULLIF`, date functions, subqueries, `CREATE OR REPLACE VIEW`, check constraints, and performance indexes.

**Example business questions answered:**

- Which opponents drive the highest average attendance?
- Which promotions increase both attendance and total revenue?
- Which ticket segments produce the most net revenue?
- Which games are underperforming their expected demand by more than 10%?
- Which games need the highest concessions inventory preparation?
- Which fan segments generate the most lifetime value?
- What is the gross margin by concessions and merchandise category?

---

## Machine Learning

### Attendance Prediction
- **Target:** `actual_attendance` per game
- **Models:** Linear Regression (baseline), Random Forest, Gradient Boosting, XGBoost (optional)
- **Split:** Time-based — earlier seasons for training, most recent season for testing
- **Features:** Weekend flag, rivalry flag, national TV flag, promotion flag and lift, opponent popularity, home/away team win percentages, recent form, weather, rolling 3- and 5-game attendance, arena capacity, month, day of week

### Pre-Game Revenue Forecast
- **Target:** `total_game_day_revenue = net_ticket_revenue + concessions + merchandise`
- **Models:** Same ensemble as attendance model
- **Leakage prevention:** `actual_attendance`, `capacity_pct`, `total_tickets_sold`, and all actual sales outcomes are **excluded** from input features — only features known before game day are used
- **Pre-game features added:** rolling 3- and 5-game revenue history (lagged), planned average base ticket price (from pricing sheet + demand signals), promotion cost, sponsor value estimate

### Fan Segmentation
- **Algorithm:** K-Means clustering — silhouette scores evaluated for k=3–8, k=6 selected for business interpretability
- **Features:** Games attended, ticket spend, concession spend, merchandise spend, promotion usage rate, email engagement score, fan value score, encoded distance from arena, encoded loyalty tier
- **Output segments:** High-Value Loyalists, Premium Experience Buyers, Promo-Sensitive Fans, Family Night Buyers, Merchandise-Heavy Fans, Casual Low-Frequency Fans

### Evaluation Metrics
| Metric | Usage |
|--------|-------|
| MAE | Mean Absolute Error — primary attendance error in fans |
| RMSE | Root Mean Squared Error — penalizes large misses |
| R² | Variance explained by the model |
| MAPE | Mean Absolute Percentage Error |
| Silhouette Score | Cluster quality for fan segmentation |

---

## Dashboard

Six-page Streamlit dashboard powered by Plotly:

| Page | Content |
|------|---------|
| **Executive Overview** | KPI cards, monthly revenue trend, revenue breakdown pie, top games, top opponents by attendance |
| **Attendance Forecast** | Actual vs. predicted scatter, day-of-week bars, opponent rankings, underperforming game table |
| **Ticket Revenue** | Segment revenue, sell-through rates, opponent revenue, promotion impact, discount vs. revenue |
| **Concessions & Merchandise** | Category revenue/margin, per-cap by tier, inventory recommendations, game-level table |
| **Fan Segmentation** | Cluster profiles, spend by segment, promotion usage, games attended, spend breakdown |
| **Scenario Modeling** | Interactive sliders for attendance, pricing, promotions, demand; real-time revenue projection and inventory/staffing recommendations |

---

## Key Business Insights

After running the full pipeline on simulated data:

- **Weekend rivalry games** average 7–10 percentage points higher capacity utilization than midweek non-rivalry games.
- **Premium Courtside and Club Level** segments drive disproportionate per-seat revenue, while **Upper Bowl and Group Sales** drive total ticket volume.
- **Merchandise Giveaway and Theme Night** promotions show the strongest weekday attendance lift (8–12%), making them the highest-ROI tools for low-demand games.
- **Season Ticket Holders and Premium Members** represent under 20% of the fanbase but generate over 40% of fan-direct revenue across tickets, concessions, and merchandise.
- **Attendance forecasts** with MAE under 1,000 fans can support staffing and inventory planning decisions with meaningful confidence for games with 15,000+ expected attendance.
- **Rivalry games** increase per-cap merchandise spend by 15–20% over regular games.

---

## How to Run Locally

### 1. Clone and set up environment

```bash
git clone https://github.com/vinay23is/game-day-revenue-intelligence-platform.git
cd game-day-revenue-intelligence-platform

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment (optional — PostgreSQL)

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials if using a database
```

### 3. Run the full pipeline

```bash
python src/simulate_business_data.py   # Generate all CSVs (~60 seconds)
python src/data_cleaning.py            # Validate and clean data
python src/feature_engineering.py     # Build model features
python src/train_attendance_model.py  # Train attendance forecasting model
python src/train_revenue_model.py     # Train revenue prediction model
python src/segmentation.py            # Fan segmentation K-Means
python src/generate_reports.py        # Generate business reports
```

### 4. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

### 5. Run tests

```bash
pytest tests/ -v
```

---

## Docker Option

Runs the full pipeline and launches the dashboard in one command:

```bash
cp .env.example .env
docker-compose up --build
```

Dashboard available at `http://localhost:8501`.  
PostgreSQL available at `localhost:5432`.

---

## Project Results

After running the pipeline on 5 seasons of simulated data:

**Attendance Prediction (test season: 2023)**

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
| Linear Regression | 566 | 714 | 0.7810 | 3.29% |
| Random Forest | 597 | 745 | 0.7619 | 3.47% |
| Gradient Boosting | 563 | 717 | 0.7797 | 3.28% |

**Pre-Game Revenue Forecast (test season: 2023 — no post-game leakage)**

| Model | MAE | RMSE | R² | MAPE |
|-------|-----|------|----|------|
| Linear Regression | $132,875 | $168,572 | 0.7773 | 3.52% |
| Random Forest | $136,966 | $173,267 | 0.7648 | 3.63% |
| Gradient Boosting | $129,048 | $168,149 | 0.7785 | 3.43% |

**Fan Segmentation:** K=6 business segments — High-Value Loyalists, Premium Experience Buyers, Promo-Sensitive Fans, Family Night Buyers, Merchandise-Heavy Fans, Casual Low-Frequency Fans.

---

## Resume Bullets

- Built a sports business intelligence platform to analyze game-day attendance, ticket demand, concessions, merchandise, promotions, and projected revenue using Python, SQL, PostgreSQL, and Streamlit.
- Designed a relational data model across games, teams, attendance, ticket segments, concessions, merchandise, promotions, fan profiles, and transactions to support stakeholder-ready analytics.
- Developed 30+ SQL queries using joins, CTEs, window functions, rankings, aggregations, and CASE statements to identify revenue drivers, attendance trends, underperforming games, and high-demand matchups.
- Trained pre-game forecasting models for attendance and game-day revenue using opponent strength, seasonality, promotions, weather, team performance, and pricing features while preventing post-game target leakage.
- Built an interactive dashboard with executive KPIs, attendance forecasting, revenue breakdowns, fan segmentation, and scenario modeling for staffing, food, merchandise, and ticketing decisions.

---

## Limitations

- Internal team ticketing, concessions, merchandise, and CRM data is private; business revenue and fan-profile data in this project is simulated. The models demonstrate the methodology, not operational-accuracy thresholds.
- Forecasts are for portfolio and demonstration purposes. Real deployment would require POS, CRM, and ticketing system integrations.
- Weather effects are modeled for outdoor-attendance sensitivity; indoor arenas are less affected by weather in practice.

---

## Future Improvements

- Integrate real ticket marketplace data (secondary market pricing signals)
- Add point-of-sale and loyalty app data connectors
- Build a Power BI version of the executive dashboard
- Add automated weekly ETL pipeline with Airflow or Prefect
- Add model monitoring and drift detection
- Add promotion ROI optimization (prescriptive analytics layer)
- Add sponsorship value forecasting by game tier

---

## Project Structure

```
game-day-revenue-intelligence-platform/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── data/
│   ├── raw/
│   ├── processed/         ← cleaned CSVs and model features
│   └── simulated/         ← generated CSVs
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_load_data.sql
│   ├── 03_business_analysis_queries.sql
│   ├── 04_kpi_views.sql
│   └── 05_readme_query_index.md
├── notebooks/
│   ├── 01_data_generation_and_cleaning.ipynb
│   ├── 02_exploratory_business_analysis.ipynb
│   ├── 03_attendance_prediction_model.ipynb
│   ├── 04_revenue_prediction_model.ipynb
│   └── 05_fan_segmentation.ipynb
├── src/
│   ├── config.py
│   ├── database.py
│   ├── simulate_business_data.py
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── train_attendance_model.py
│   ├── train_revenue_model.py
│   ├── segmentation.py
│   ├── generate_reports.py
│   └── utils.py
├── dashboard/
│   ├── app.py
│   └── pages/
│       ├── 1_Executive_Overview.py
│       ├── 2_Attendance_Forecast.py
│       ├── 3_Ticket_Revenue.py
│       ├── 4_Concessions_Merchandise.py
│       ├── 5_Fan_Segmentation.py
│       └── 6_Scenario_Modeling.py
├── models/
│   └── model_features.json
├── reports/
│   ├── model_metrics.md
│   ├── business_insights.md
│   └── executive_summary.md
└── tests/
    ├── test_data_generation.py
    ├── test_feature_engineering.py
    └── test_model_training.py
```
