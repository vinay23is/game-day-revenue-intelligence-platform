-- =============================================================================
-- 02_load_data.sql
-- Game-Day Revenue Intelligence Platform
-- Loads CSV data into PostgreSQL tables using COPY commands.
--
-- PREREQUISITES:
--   1. Run 01_create_tables.sql first.
--   2. Run: python src/simulate_business_data.py
--      to generate all CSV files in data/simulated/.
--   3. Adjust DATA_PATH to the absolute path of your data/simulated/ directory.
--
-- LOAD ORDER (respects foreign key dependencies):
--   teams -> games -> weather, promotions, attendance, ticket_segments
--   -> ticket_sales -> concessions, merchandise
--   -> fan_profiles -> fan_transactions -> model_predictions
-- =============================================================================

-- Set this to the absolute path of your data/simulated/ folder.
-- Example on macOS: /Users/yourname/game-day-revenue-intelligence-platform/data/simulated
-- Replace \copy with COPY if running directly as superuser inside psql.

-- Step 1: teams (no foreign key dependencies)
\copy teams (team_id, team_abbr, team_name, team_city, conference, division, arena_name, arena_capacity, market_size_tier, historical_popularity_score)
FROM 'data/simulated/teams.csv'
WITH (FORMAT csv, HEADER true);

-- Step 2: games (depends on teams)
\copy games (game_id, season, game_date, home_team_id, away_team_id, home_team_name, away_team_name, home_team_abbr, away_team_abbr, day_of_week, month, is_weekend, is_holiday_period, rivalry_flag, nationally_televised_flag, home_team_win_pct_entering_game, away_team_win_pct_entering_game, home_team_recent_form, away_team_recent_form, home_score, away_score, home_win_flag)
FROM 'data/simulated/games.csv'
WITH (FORMAT csv, HEADER true);

-- Step 3: weather (depends on games)
\copy weather (game_id, temperature_f, precipitation_flag, snow_flag, severe_weather_flag, weather_condition)
FROM 'data/simulated/weather.csv'
WITH (FORMAT csv, HEADER true);

-- Step 4: promotions (depends on games)
\copy promotions (promotion_id, game_id, promotion_flag, promotion_type, promotion_cost, expected_promotion_lift_pct, sponsor_category, sponsor_value_estimate)
FROM 'data/simulated/promotions.csv'
WITH (FORMAT csv, HEADER true);

-- Step 5: attendance (depends on games)
\copy attendance (game_id, arena_capacity, actual_attendance, capacity_pct, expected_attendance_baseline, attendance_variance, attendance_tier)
FROM 'data/simulated/attendance.csv'
WITH (FORMAT csv, HEADER true);

-- Step 6: ticket_segments (no foreign key dependencies)
\copy ticket_segments (segment_id, segment_name, avg_base_price, price_tier)
FROM 'data/simulated/ticket_segments.csv'
WITH (FORMAT csv, HEADER true);

-- Step 7: ticket_sales (depends on games, ticket_segments)
\copy ticket_sales (ticket_sale_id, game_id, segment_id, segment_name, tickets_available, tickets_sold, avg_ticket_price, discount_pct, gross_ticket_revenue, net_ticket_revenue, sell_through_rate)
FROM 'data/simulated/ticket_sales.csv'
WITH (FORMAT csv, HEADER true);

-- Step 8: concessions (depends on games)
\copy concessions (concession_id, game_id, category, units_sold, avg_unit_price, gross_revenue, estimated_cost, gross_margin, per_cap_spend, recommended_inventory_units)
FROM 'data/simulated/concessions.csv'
WITH (FORMAT csv, HEADER true);

-- Step 9: merchandise (depends on games)
\copy merchandise (merchandise_id, game_id, category, units_sold, avg_unit_price, gross_revenue, estimated_cost, gross_margin, per_cap_spend, recommended_inventory_units)
FROM 'data/simulated/merchandise.csv'
WITH (FORMAT csv, HEADER true);

-- Step 10: fan_profiles (no foreign key dependencies)
\copy fan_profiles (fan_id, age_group, household_type, distance_from_arena_bucket, preferred_ticket_segment, loyalty_status, games_attended_last_12_months, avg_ticket_spend, avg_concession_spend, avg_merchandise_spend, promotion_usage_rate, email_engagement_score, fan_value_score)
FROM 'data/simulated/fan_profiles.csv'
WITH (FORMAT csv, HEADER true);

-- Step 11: fan_transactions (depends on fan_profiles, games)
\copy fan_transactions (transaction_id, fan_id, game_id, ticket_spend, concession_spend, merchandise_spend, used_promotion, total_spend, transaction_date)
FROM 'data/simulated/fan_transactions.csv'
WITH (FORMAT csv, HEADER true);

-- Step 12: model_predictions (depends on games) — populated by ML pipeline
\copy model_predictions (game_id, predicted_attendance, predicted_ticket_revenue, predicted_concessions_revenue, predicted_merchandise_revenue, predicted_total_revenue, actual_total_revenue, attendance_prediction_error, revenue_prediction_error, model_run_date)
FROM 'data/simulated/model_predictions.csv'
WITH (FORMAT csv, HEADER true, NULL '');

-- Verify row counts after loading
SELECT 'teams'            AS table_name, COUNT(*) AS rows FROM teams
UNION ALL SELECT 'games',             COUNT(*) FROM games
UNION ALL SELECT 'weather',           COUNT(*) FROM weather
UNION ALL SELECT 'promotions',        COUNT(*) FROM promotions
UNION ALL SELECT 'attendance',        COUNT(*) FROM attendance
UNION ALL SELECT 'ticket_segments',   COUNT(*) FROM ticket_segments
UNION ALL SELECT 'ticket_sales',      COUNT(*) FROM ticket_sales
UNION ALL SELECT 'concessions',       COUNT(*) FROM concessions
UNION ALL SELECT 'merchandise',       COUNT(*) FROM merchandise
UNION ALL SELECT 'fan_profiles',      COUNT(*) FROM fan_profiles
UNION ALL SELECT 'fan_transactions',  COUNT(*) FROM fan_transactions
UNION ALL SELECT 'model_predictions', COUNT(*) FROM model_predictions
ORDER BY table_name;
