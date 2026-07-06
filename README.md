# Game-Day Revenue Intelligence Platform

A sports business intelligence platform for game-day demand forecasting, revenue analytics, fan segmentation, and scenario modeling — built for a sports franchise's business ops team, not for fans.

There's no public hosted demo — the dashboard is a local Streamlit app that runs against a self-contained data pipeline (or PostgreSQL, optionally). See **Running Locally** below; it's a 5-minute setup with no external accounts needed.

## What problem does this solve?

Sports and entertainment organizations need to forecast game-day attendance and understand what actually drives revenue, because attendance ripples into ticket revenue, staffing, concessions inventory, merchandise planning, and promotion ROI. I built this to demonstrate the full analytics stack a sports BI team would use to answer that: raw data engineering, SQL analysis, machine learning forecasts, and an executive dashboard that lets a non-technical stakeholder run "what-if" scenarios (What if we drop ticket prices 10%? What if we run a bobblehead promotion?) without touching a notebook.

Because real team-level financial and CRM data is private, the project uses realistic **simulated** data for 30 fictional teams — no real league, team, or player data is used or implied.

## Tech Stack

- **Language:** Python 3.11
- **Data / ML:** Pandas, NumPy, Scikit-learn (Linear Regression, Random Forest, Gradient Boosting), XGBoost (optional)
- **Dashboard:** Streamlit, Plotly
- **Database:** PostgreSQL 15, SQLAlchemy (optional — the pipeline also runs on CSVs alone)
- **Infra:** Docker, Docker Compose
- **Testing:** pytest
- **Notebooks:** Jupyter (exploratory work in `notebooks/`)

## Architecture

```
Data Generation (simulate_business_data.py)
    → Data Cleaning & Validation (data_cleaning.py)
    → PostgreSQL / CSV storage
    → Feature Engineering (feature_engineering.py)
    → ML Models (train_attendance_model.py, train_revenue_model.py, segmentation.py)
    → SQL Analytics (sql/03_business_analysis_queries.sql + KPI views)
    → Business Reports (generate_reports.py)
    → Streamlit Dashboard (dashboard/app.py, 6 pages)
```

The database schema is fully relational: `games` is the hub table, with `attendance`, `weather`, `promotions`, `ticket_sales`, `concessions`, and `merchandise` all foreign-keyed to it, plus a separate `fan_profiles` / `fan_transactions` pair for the segmentation work. Everything downstream (features, models, dashboard) reads from this same schema, so the ML models and the SQL analytics answer questions against one consistent source of data.

## Key Features

- **Attendance forecasting** — Random Forest / Gradient Boosting / Linear Regression models predict per-game attendance from opponent strength, scheduling (weekend, rivalry, national TV), promotions, weather, and recent team form, evaluated with a **time-based train/test split** (train on earlier seasons, test on the most recent one) so the reported accuracy reflects genuine forecasting, not lookback
- **Pre-game revenue forecasting** — predicts total game-day revenue (tickets + concessions + merchandise) while deliberately excluding any post-game outcome fields (actual attendance, capacity %, tickets sold) from the feature set to avoid target leakage
- **Fan segmentation** — K-Means clustering (k=6, chosen via silhouette score across k=3–8) on spend and engagement behavior, producing six named, business-usable segments (e.g. High-Value Loyalists, Promo-Sensitive Fans)
- **Scenario modeling page** — interactive sliders for attendance, pricing, and promotions that recompute projected revenue and inventory/staffing needs in real time
- **40+ SQL business queries** using CTEs, window functions (`RANK`, `DENSE_RANK`), and CASE logic, plus 7 reusable KPI views
- **Six-page Streamlit dashboard** — executive overview, attendance forecast, ticket revenue, concessions/merchandise, fan segmentation, and scenario modeling, all backed by Plotly charts

## Interesting Engineering Decisions

- **Time-based splits instead of random splits for both ML models** — attendance and revenue are trained on earlier seasons and tested on the most recent one, because a random split would leak future-season patterns into training and overstate real-world forecasting accuracy.
- **Explicit leakage guard on the revenue model** — actual attendance, capacity %, and realized ticket/concession/merchandise sales are excluded from the pre-game revenue model's inputs on purpose, since none of those are known before the gates open; only pre-game-knowable features (pricing plan, promotion cost, rolling revenue history) are used.
- **Data is clearly labeled as simulated, not scraped or real** — the README and code both call out that the 30 teams and all revenue figures are invented, since real per-team financial and CRM data isn't public. This is a design constraint stated up front rather than discovered by a reader.
- **Dashboard doesn't require PostgreSQL** — `docker-compose up` optionally wires up Postgres, but the whole pipeline (generation → cleaning → features → models → dashboard) also runs directly against CSVs, so there's a zero-config path to seeing it work.

## Running Locally

**Option A — Python venv**
```bash
git clone https://github.com/vinay23is/game-day-revenue-intelligence-platform.git
cd game-day-revenue-intelligence-platform
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python src/simulate_business_data.py   # generates all CSVs (~60s)
python src/data_cleaning.py
python src/feature_engineering.py
python src/train_attendance_model.py
python src/train_revenue_model.py
python src/segmentation.py
python src/generate_reports.py

streamlit run dashboard/app.py         # open http://localhost:8501
```

**Option B — Docker (runs the full pipeline + dashboard in one command)**
```bash
cp .env.example .env
docker-compose up --build              # dashboard at http://localhost:8501, Postgres at localhost:5432
```

**Tests**
```bash
pytest tests/ -v
```

Licensed under MIT (see `LICENSE`).
