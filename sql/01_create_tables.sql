-- =============================================================================
-- 01_create_tables.sql
-- Game-Day Revenue Intelligence Platform
-- Creates all tables with primary keys, foreign keys, and correct data types.
-- =============================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS model_predictions   CASCADE;
DROP TABLE IF EXISTS fan_transactions    CASCADE;
DROP TABLE IF EXISTS fan_profiles        CASCADE;
DROP TABLE IF EXISTS merchandise         CASCADE;
DROP TABLE IF EXISTS concessions         CASCADE;
DROP TABLE IF EXISTS ticket_sales        CASCADE;
DROP TABLE IF EXISTS ticket_segments     CASCADE;
DROP TABLE IF EXISTS promotions          CASCADE;
DROP TABLE IF EXISTS attendance          CASCADE;
DROP TABLE IF EXISTS weather             CASCADE;
DROP TABLE IF EXISTS games               CASCADE;
DROP TABLE IF EXISTS teams               CASCADE;

-- ---------------------------------------------------------------------------
-- teams
-- ---------------------------------------------------------------------------
CREATE TABLE teams (
    team_id                      SERIAL PRIMARY KEY,
    team_abbr                    CHAR(3)        NOT NULL UNIQUE,
    team_name                    VARCHAR(60)    NOT NULL,
    team_city                    VARCHAR(60)    NOT NULL,
    conference                   VARCHAR(10)    NOT NULL,
    division                     VARCHAR(20)    NOT NULL,
    arena_name                   VARCHAR(80)    NOT NULL,
    arena_capacity               INTEGER        NOT NULL CHECK (arena_capacity > 0),
    market_size_tier             VARCHAR(10)    NOT NULL,
    historical_popularity_score  NUMERIC(4,3)   NOT NULL CHECK (historical_popularity_score BETWEEN 0 AND 1)
);

-- ---------------------------------------------------------------------------
-- games
-- ---------------------------------------------------------------------------
CREATE TABLE games (
    game_id                          SERIAL PRIMARY KEY,
    season                           SMALLINT       NOT NULL,
    game_date                        DATE           NOT NULL,
    home_team_id                     INTEGER        NOT NULL REFERENCES teams(team_id),
    away_team_id                     INTEGER        NOT NULL REFERENCES teams(team_id),
    home_team_name                   VARCHAR(60),
    away_team_name                   VARCHAR(60),
    home_team_abbr                   CHAR(3),
    away_team_abbr                   CHAR(3),
    day_of_week                      VARCHAR(10),
    month                            SMALLINT       CHECK (month BETWEEN 1 AND 12),
    is_weekend                       BOOLEAN        DEFAULT FALSE,
    is_holiday_period                BOOLEAN        DEFAULT FALSE,
    rivalry_flag                     BOOLEAN        DEFAULT FALSE,
    nationally_televised_flag        BOOLEAN        DEFAULT FALSE,
    home_team_win_pct_entering_game  NUMERIC(5,4)   CHECK (home_team_win_pct_entering_game BETWEEN 0 AND 1),
    away_team_win_pct_entering_game  NUMERIC(5,4)   CHECK (away_team_win_pct_entering_game BETWEEN 0 AND 1),
    home_team_recent_form            NUMERIC(5,4),
    away_team_recent_form            NUMERIC(5,4),
    home_score                       SMALLINT,
    away_score                       SMALLINT,
    home_win_flag                    SMALLINT       CHECK (home_win_flag IN (0,1))
);

-- ---------------------------------------------------------------------------
-- weather
-- ---------------------------------------------------------------------------
CREATE TABLE weather (
    weather_id           SERIAL PRIMARY KEY,
    game_id              INTEGER        NOT NULL UNIQUE REFERENCES games(game_id),
    temperature_f        NUMERIC(5,1),
    precipitation_flag   BOOLEAN        DEFAULT FALSE,
    snow_flag            BOOLEAN        DEFAULT FALSE,
    severe_weather_flag  BOOLEAN        DEFAULT FALSE,
    weather_condition    VARCHAR(30)
);

-- ---------------------------------------------------------------------------
-- promotions
-- ---------------------------------------------------------------------------
CREATE TABLE promotions (
    promotion_id                  SERIAL PRIMARY KEY,
    game_id                       INTEGER        NOT NULL UNIQUE REFERENCES games(game_id),
    promotion_flag                BOOLEAN        DEFAULT FALSE,
    promotion_type                VARCHAR(40)    NOT NULL DEFAULT 'None',
    promotion_cost                NUMERIC(10,2)  DEFAULT 0,
    expected_promotion_lift_pct   NUMERIC(5,2)   DEFAULT 0,
    sponsor_category              VARCHAR(30)    DEFAULT 'None',
    sponsor_value_estimate        NUMERIC(12,2)  DEFAULT 0
);

-- ---------------------------------------------------------------------------
-- attendance
-- ---------------------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id                  SERIAL PRIMARY KEY,
    game_id                        INTEGER        NOT NULL UNIQUE REFERENCES games(game_id),
    arena_capacity                 INTEGER        NOT NULL,
    actual_attendance              INTEGER        NOT NULL CHECK (actual_attendance >= 0),
    capacity_pct                   NUMERIC(6,2),
    expected_attendance_baseline   INTEGER,
    attendance_variance            INTEGER,
    attendance_tier                VARCHAR(10)    CHECK (attendance_tier IN ('Low','Medium','High','Sellout'))
);

-- ---------------------------------------------------------------------------
-- ticket_segments
-- ---------------------------------------------------------------------------
CREATE TABLE ticket_segments (
    segment_id     SERIAL PRIMARY KEY,
    segment_name   VARCHAR(50)    NOT NULL UNIQUE,
    avg_base_price NUMERIC(8,2)   NOT NULL CHECK (avg_base_price > 0),
    price_tier     VARCHAR(20)    NOT NULL
);

-- ---------------------------------------------------------------------------
-- ticket_sales
-- ---------------------------------------------------------------------------
CREATE TABLE ticket_sales (
    ticket_sale_id      SERIAL PRIMARY KEY,
    game_id             INTEGER        NOT NULL REFERENCES games(game_id),
    segment_id          INTEGER        NOT NULL REFERENCES ticket_segments(segment_id),
    segment_name        VARCHAR(50),
    tickets_available   INTEGER        NOT NULL CHECK (tickets_available > 0),
    tickets_sold        INTEGER        NOT NULL CHECK (tickets_sold >= 0),
    avg_ticket_price    NUMERIC(8,2)   NOT NULL CHECK (avg_ticket_price >= 0),
    discount_pct        NUMERIC(5,2)   DEFAULT 0,
    gross_ticket_revenue  NUMERIC(12,2) NOT NULL CHECK (gross_ticket_revenue >= 0),
    net_ticket_revenue    NUMERIC(12,2) NOT NULL CHECK (net_ticket_revenue >= 0),
    sell_through_rate     NUMERIC(6,2),
    CONSTRAINT chk_sold_le_available CHECK (tickets_sold <= tickets_available)
);

-- ---------------------------------------------------------------------------
-- concessions
-- ---------------------------------------------------------------------------
CREATE TABLE concessions (
    concession_id               SERIAL PRIMARY KEY,
    game_id                     INTEGER        NOT NULL REFERENCES games(game_id),
    category                    VARCHAR(30)    NOT NULL,
    units_sold                  INTEGER        NOT NULL CHECK (units_sold >= 0),
    avg_unit_price              NUMERIC(8,2),
    gross_revenue               NUMERIC(12,2)  NOT NULL CHECK (gross_revenue >= 0),
    estimated_cost              NUMERIC(12,2),
    gross_margin                NUMERIC(12,2),
    per_cap_spend               NUMERIC(8,2),
    recommended_inventory_units INTEGER
);

-- ---------------------------------------------------------------------------
-- merchandise
-- ---------------------------------------------------------------------------
CREATE TABLE merchandise (
    merchandise_id              SERIAL PRIMARY KEY,
    game_id                     INTEGER        NOT NULL REFERENCES games(game_id),
    category                    VARCHAR(30)    NOT NULL,
    units_sold                  INTEGER        NOT NULL CHECK (units_sold >= 0),
    avg_unit_price              NUMERIC(8,2),
    gross_revenue               NUMERIC(12,2)  NOT NULL CHECK (gross_revenue >= 0),
    estimated_cost              NUMERIC(12,2),
    gross_margin                NUMERIC(12,2),
    per_cap_spend               NUMERIC(8,2),
    recommended_inventory_units INTEGER
);

-- ---------------------------------------------------------------------------
-- fan_profiles
-- ---------------------------------------------------------------------------
CREATE TABLE fan_profiles (
    fan_id                          SERIAL PRIMARY KEY,
    age_group                       VARCHAR(10),
    household_type                  VARCHAR(30),
    distance_from_arena_bucket      VARCHAR(20),
    preferred_ticket_segment        VARCHAR(50),
    loyalty_status                  VARCHAR(30),
    games_attended_last_12_months   SMALLINT       CHECK (games_attended_last_12_months >= 0),
    avg_ticket_spend                NUMERIC(8,2)   CHECK (avg_ticket_spend >= 0),
    avg_concession_spend            NUMERIC(8,2)   CHECK (avg_concession_spend >= 0),
    avg_merchandise_spend           NUMERIC(8,2)   CHECK (avg_merchandise_spend >= 0),
    promotion_usage_rate            NUMERIC(5,4)   CHECK (promotion_usage_rate BETWEEN 0 AND 1),
    email_engagement_score          NUMERIC(5,4)   CHECK (email_engagement_score BETWEEN 0 AND 1),
    fan_value_score                 NUMERIC(5,4)   CHECK (fan_value_score BETWEEN 0 AND 1)
);

-- ---------------------------------------------------------------------------
-- fan_transactions
-- ---------------------------------------------------------------------------
CREATE TABLE fan_transactions (
    transaction_id      SERIAL PRIMARY KEY,
    fan_id              INTEGER        NOT NULL REFERENCES fan_profiles(fan_id),
    game_id             INTEGER        NOT NULL REFERENCES games(game_id),
    ticket_spend        NUMERIC(10,2)  DEFAULT 0 CHECK (ticket_spend >= 0),
    concession_spend    NUMERIC(10,2)  DEFAULT 0 CHECK (concession_spend >= 0),
    merchandise_spend   NUMERIC(10,2)  DEFAULT 0 CHECK (merchandise_spend >= 0),
    used_promotion      BOOLEAN        DEFAULT FALSE,
    total_spend         NUMERIC(10,2)  DEFAULT 0 CHECK (total_spend >= 0),
    transaction_date    DATE
);

-- ---------------------------------------------------------------------------
-- model_predictions
-- ---------------------------------------------------------------------------
CREATE TABLE model_predictions (
    prediction_id                  SERIAL PRIMARY KEY,
    game_id                        INTEGER        NOT NULL UNIQUE REFERENCES games(game_id),
    predicted_attendance           INTEGER,
    predicted_ticket_revenue       NUMERIC(12,2),
    predicted_concessions_revenue  NUMERIC(12,2),
    predicted_merchandise_revenue  NUMERIC(12,2),
    predicted_total_revenue        NUMERIC(12,2),
    actual_total_revenue           NUMERIC(12,2),
    attendance_prediction_error    INTEGER,
    revenue_prediction_error       NUMERIC(12,2),
    model_run_date                 DATE
);

-- Indexes for common query patterns
CREATE INDEX idx_games_season        ON games(season);
CREATE INDEX idx_games_game_date     ON games(game_date);
CREATE INDEX idx_games_home_team     ON games(home_team_id);
CREATE INDEX idx_games_away_team     ON games(away_team_id);
CREATE INDEX idx_ticket_sales_game   ON ticket_sales(game_id);
CREATE INDEX idx_ticket_sales_seg    ON ticket_sales(segment_id);
CREATE INDEX idx_concessions_game    ON concessions(game_id);
CREATE INDEX idx_merchandise_game    ON merchandise(game_id);
CREATE INDEX idx_fan_txn_fan         ON fan_transactions(fan_id);
CREATE INDEX idx_fan_txn_game        ON fan_transactions(game_id);
CREATE INDEX idx_attendance_tier     ON attendance(attendance_tier);
CREATE INDEX idx_promotions_type     ON promotions(promotion_type);
