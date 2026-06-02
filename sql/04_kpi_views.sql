-- =============================================================================
-- 04_kpi_views.sql
-- Game-Day Revenue Intelligence Platform
-- Creates reusable analytical views for the dashboard and reporting layer.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- vw_game_day_revenue
-- Full game-day P&L per game: tickets, concessions, merchandise, total
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_game_day_revenue AS
SELECT
    g.game_id,
    g.game_date,
    g.season,
    g.home_team_name,
    g.away_team_name,
    g.day_of_week,
    g.month,
    g.is_weekend,
    g.rivalry_flag,
    g.nationally_televised_flag,
    a.actual_attendance,
    a.arena_capacity,
    a.capacity_pct,
    a.attendance_tier,
    p.promotion_type,
    p.promotion_flag,
    ROUND(t_agg.ticket_rev, 2)                                  AS net_ticket_revenue,
    ROUND(c_agg.con_rev, 2)                                     AS concession_revenue,
    ROUND(m_agg.merch_rev, 2)                                   AS merchandise_revenue,
    ROUND(t_agg.ticket_rev + c_agg.con_rev + m_agg.merch_rev, 2) AS total_game_day_revenue,
    ROUND((t_agg.ticket_rev + c_agg.con_rev + m_agg.merch_rev)
          / NULLIF(a.actual_attendance, 0), 2)                  AS revenue_per_attendee
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN promotions p ON g.game_id = p.game_id
JOIN (SELECT game_id, SUM(net_ticket_revenue)  AS ticket_rev FROM ticket_sales GROUP BY game_id) t_agg ON g.game_id = t_agg.game_id
JOIN (SELECT game_id, SUM(gross_revenue)        AS con_rev   FROM concessions  GROUP BY game_id) c_agg ON g.game_id = c_agg.game_id
JOIN (SELECT game_id, SUM(gross_revenue)        AS merch_rev FROM merchandise  GROUP BY game_id) m_agg ON g.game_id = m_agg.game_id;


-- ---------------------------------------------------------------------------
-- vw_attendance_performance
-- Attendance vs. baseline, tier classification, and variance flags
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_attendance_performance AS
SELECT
    g.game_id,
    g.game_date,
    g.season,
    g.home_team_name,
    g.away_team_name,
    g.day_of_week,
    g.month,
    g.is_weekend,
    g.rivalry_flag,
    g.nationally_televised_flag,
    g.home_team_win_pct_entering_game,
    a.actual_attendance,
    a.arena_capacity,
    a.capacity_pct,
    a.expected_attendance_baseline,
    a.attendance_variance,
    a.attendance_tier,
    ROUND(
        (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
        / NULLIF(a.expected_attendance_baseline, 0) * 100, 2
    )                                   AS variance_pct,
    CASE
        WHEN (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
             / NULLIF(a.expected_attendance_baseline, 0) < -0.10 THEN 'Underperforming'
        WHEN (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
             / NULLIF(a.expected_attendance_baseline, 0) > 0.10  THEN 'Overperforming'
        ELSE 'On Target'
    END                                 AS performance_flag,
    p.promotion_type,
    w.weather_condition,
    w.temperature_f,
    w.snow_flag,
    w.severe_weather_flag
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN promotions p ON g.game_id = p.game_id
JOIN weather    w ON g.game_id = w.game_id;


-- ---------------------------------------------------------------------------
-- vw_ticket_segment_performance
-- Per-segment KPIs: revenue, sell-through, pricing
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ticket_segment_performance AS
SELECT
    tk.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.attendance_tier,
    tk.segment_id,
    tk.segment_name,
    ts.price_tier,
    tk.tickets_available,
    tk.tickets_sold,
    tk.avg_ticket_price,
    tk.discount_pct,
    tk.gross_ticket_revenue,
    tk.net_ticket_revenue,
    tk.sell_through_rate,
    DENSE_RANK() OVER (
        PARTITION BY tk.game_id ORDER BY tk.net_ticket_revenue DESC
    )                               AS segment_revenue_rank
FROM ticket_sales tk
JOIN games           g  ON tk.game_id   = g.game_id
JOIN attendance      a  ON tk.game_id   = a.game_id
JOIN ticket_segments ts ON tk.segment_id = ts.segment_id;


-- ---------------------------------------------------------------------------
-- vw_promotion_effectiveness
-- Compares promoted vs. non-promoted games; calculates lift estimate
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_promotion_effectiveness AS
WITH baseline AS (
    SELECT AVG(a.capacity_pct) AS baseline_cap_pct
    FROM promotions p
    JOIN attendance a ON p.game_id = a.game_id
    WHERE p.promotion_flag = FALSE
)
SELECT
    p.promotion_type,
    COUNT(*)                                        AS games,
    ROUND(AVG(a.capacity_pct), 2)                   AS avg_capacity_pct,
    ROUND(b.baseline_cap_pct, 2)                    AS baseline_capacity_pct,
    ROUND(AVG(a.capacity_pct) - b.baseline_cap_pct, 2) AS estimated_att_lift_pct_pts,
    ROUND(AVG(p.promotion_cost), 0)                 AS avg_promo_cost,
    ROUND(AVG(p.sponsor_value_estimate), 0)         AS avg_sponsor_value,
    ROUND(AVG(rev.total_rev), 0)                    AS avg_game_revenue
FROM promotions p
JOIN attendance a ON p.game_id = a.game_id
JOIN (
    SELECT
        g.game_id,
        SUM(tk.net_ticket_revenue) + SUM(c.gross_revenue) + SUM(m.gross_revenue) AS total_rev
    FROM games g
    JOIN ticket_sales tk ON g.game_id = tk.game_id
    JOIN concessions  c  ON g.game_id = c.game_id
    JOIN merchandise  m  ON g.game_id = m.game_id
    GROUP BY g.game_id
) rev ON p.game_id = rev.game_id
CROSS JOIN baseline b
GROUP BY p.promotion_type, b.baseline_cap_pct
ORDER BY avg_capacity_pct DESC;


-- ---------------------------------------------------------------------------
-- vw_concession_merchandise_demand
-- Per-game demand, per-cap spend, margins, and inventory recommendations
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_concession_merchandise_demand AS
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    a.attendance_tier,
    ROUND(c_agg.total_con_rev, 2)               AS total_concession_revenue,
    ROUND(c_agg.total_con_rev / NULLIF(a.actual_attendance, 0), 2) AS concession_per_cap,
    c_agg.total_con_inventory_rec,
    ROUND(m_agg.total_merch_rev, 2)             AS total_merchandise_revenue,
    ROUND(m_agg.total_merch_rev / NULLIF(a.actual_attendance, 0), 2) AS merchandise_per_cap,
    m_agg.total_merch_inventory_rec,
    ROUND(c_agg.total_con_rev + m_agg.total_merch_rev, 2) AS total_ancillary_revenue
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN (
    SELECT game_id,
           SUM(gross_revenue)               AS total_con_rev,
           SUM(recommended_inventory_units) AS total_con_inventory_rec
    FROM concessions GROUP BY game_id
) c_agg ON g.game_id = c_agg.game_id
JOIN (
    SELECT game_id,
           SUM(gross_revenue)               AS total_merch_rev,
           SUM(recommended_inventory_units) AS total_merch_inventory_rec
    FROM merchandise GROUP BY game_id
) m_agg ON g.game_id = m_agg.game_id;


-- ---------------------------------------------------------------------------
-- vw_fan_segment_value
-- Aggregated fan spend and behavioral metrics by loyalty status
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_fan_segment_value AS
SELECT
    loyalty_status,
    COUNT(*)                                            AS fan_count,
    ROUND(AVG(games_attended_last_12_months), 1)        AS avg_games_attended,
    ROUND(AVG(avg_ticket_spend), 2)                     AS avg_ticket_spend,
    ROUND(AVG(avg_concession_spend), 2)                 AS avg_concession_spend,
    ROUND(AVG(avg_merchandise_spend), 2)                AS avg_merchandise_spend,
    ROUND(AVG(avg_ticket_spend + avg_concession_spend + avg_merchandise_spend), 2) AS avg_total_spend,
    ROUND(AVG(promotion_usage_rate) * 100, 1)           AS avg_promo_usage_pct,
    ROUND(AVG(email_engagement_score) * 100, 1)         AS avg_email_engagement_pct,
    ROUND(AVG(fan_value_score), 3)                      AS avg_fan_value_score,
    RANK() OVER (ORDER BY AVG(fan_value_score) DESC)    AS value_rank
FROM fan_profiles
GROUP BY loyalty_status;


-- ---------------------------------------------------------------------------
-- vw_executive_dashboard
-- Single-row summary of key business KPIs across all seasons
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_executive_dashboard AS
WITH rev AS (
    SELECT
        COUNT(DISTINCT g.game_id)               AS total_games,
        SUM(a.actual_attendance)                AS total_attendance,
        ROUND(AVG(a.capacity_pct), 1)           AS avg_capacity_pct,
        ROUND(SUM(tk.net_ticket_revenue), 0)    AS total_ticket_revenue,
        ROUND(SUM(c.gross_revenue), 0)          AS total_concession_revenue,
        ROUND(SUM(m.gross_revenue), 0)          AS total_merchandise_revenue,
        ROUND(SUM(tk.net_ticket_revenue + c.gross_revenue + m.gross_revenue), 0) AS total_game_day_revenue
    FROM games g
    JOIN attendance   a  ON g.game_id = a.game_id
    JOIN ticket_sales tk ON g.game_id = tk.game_id
    JOIN concessions  c  ON g.game_id = c.game_id
    JOIN merchandise  m  ON g.game_id = m.game_id
),
top_opp AS (
    SELECT g.away_team_name AS top_opponent
    FROM games g
    JOIN attendance a ON g.game_id = a.game_id
    GROUP BY g.away_team_name
    ORDER BY AVG(a.capacity_pct) DESC
    LIMIT 1
),
top_fan AS (
    SELECT loyalty_status AS top_fan_segment
    FROM fan_profiles
    GROUP BY loyalty_status
    ORDER BY AVG(fan_value_score) DESC
    LIMIT 1
)
SELECT
    r.total_games,
    r.total_attendance,
    r.avg_capacity_pct,
    r.total_ticket_revenue,
    r.total_concession_revenue,
    r.total_merchandise_revenue,
    r.total_game_day_revenue,
    ROUND(r.total_game_day_revenue::NUMERIC / NULLIF(r.total_attendance, 0), 2) AS avg_revenue_per_attendee,
    o.top_opponent,
    f.top_fan_segment
FROM rev r, top_opp o, top_fan f;
