-- =============================================================================
-- 03_business_analysis_queries.sql
-- Game-Day Revenue Intelligence Platform
-- 40+ business analysis queries across attendance, ticket revenue, promotions,
-- concessions, merchandise, fan analytics, and executive KPIs.
-- =============================================================================


-- ============================================================
-- SECTION 1: ATTENDANCE ANALYTICS
-- ============================================================

-- Q01: Top 10 opponents by average attendance
-- Business question: Which visiting teams drive the highest fan turnout?
SELECT
    g.away_team_name                        AS opponent,
    COUNT(*)                                AS games_played,
    ROUND(AVG(a.actual_attendance), 0)      AS avg_attendance,
    ROUND(AVG(a.capacity_pct), 1)           AS avg_capacity_pct,
    MAX(a.actual_attendance)                AS max_attendance
FROM games g
JOIN attendance a ON g.game_id = a.game_id
GROUP BY g.away_team_name
ORDER BY avg_attendance DESC
LIMIT 10;


-- Q02: Attendance by day of week
-- Business question: Which days of the week see the strongest fan turnout?
SELECT
    g.day_of_week,
    COUNT(*)                                AS games,
    ROUND(AVG(a.actual_attendance), 0)      AS avg_attendance,
    ROUND(AVG(a.capacity_pct), 1)           AS avg_capacity_pct
FROM games g
JOIN attendance a ON g.game_id = a.game_id
GROUP BY g.day_of_week
ORDER BY avg_attendance DESC;


-- Q03: Attendance by month
-- Business question: Are there seasonal peaks and troughs in fan demand?
SELECT
    g.month,
    TO_CHAR(TO_DATE(g.month::TEXT, 'MM'), 'Month') AS month_name,
    COUNT(*)                                        AS games,
    ROUND(AVG(a.actual_attendance), 0)              AS avg_attendance,
    ROUND(AVG(a.capacity_pct), 1)                   AS avg_capacity_pct
FROM games g
JOIN attendance a ON g.game_id = a.game_id
GROUP BY g.month
ORDER BY g.month;


-- Q04: Weekend vs weekday attendance comparison
-- Business question: How much does the weekend premium affect demand?
SELECT
    CASE WHEN g.is_weekend THEN 'Weekend' ELSE 'Weekday' END  AS game_type,
    COUNT(*)                                                    AS games,
    ROUND(AVG(a.actual_attendance), 0)                         AS avg_attendance,
    ROUND(AVG(a.capacity_pct), 1)                              AS avg_capacity_pct,
    MIN(a.actual_attendance)                                    AS min_attendance,
    MAX(a.actual_attendance)                                    AS max_attendance
FROM games g
JOIN attendance a ON g.game_id = a.game_id
GROUP BY g.is_weekend
ORDER BY avg_attendance DESC;


-- Q05: Average capacity percentage by opponent tier
-- Business question: Do high-popularity visiting teams meaningfully lift demand?
SELECT
    t.market_size_tier                      AS opponent_market_tier,
    t.historical_popularity_score           AS avg_opp_popularity,
    COUNT(*)                                AS games,
    ROUND(AVG(a.capacity_pct), 2)           AS avg_capacity_pct
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN teams t ON g.away_team_id = t.team_id
GROUP BY t.market_size_tier, t.historical_popularity_score
ORDER BY avg_capacity_pct DESC;


-- Q06: Sellout and near-sellout games
-- Business question: Which games hit maximum demand and are candidates for dynamic pricing?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    a.arena_capacity,
    ROUND(a.capacity_pct, 1)    AS capacity_pct,
    a.attendance_tier,
    p.promotion_type
FROM games g
JOIN attendance a  ON g.game_id = a.game_id
JOIN promotions p  ON g.game_id = p.game_id
WHERE a.capacity_pct >= 97
ORDER BY a.capacity_pct DESC
LIMIT 25;


-- Q07: Games underperforming expected attendance by more than 10%
-- Business question: Which games are leaving seats empty that could have been filled?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    a.expected_attendance_baseline,
    a.attendance_variance,
    ROUND(
        (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
        / NULLIF(a.expected_attendance_baseline, 0) * 100, 1
    ) AS variance_pct,
    a.attendance_tier,
    p.promotion_type,
    w.weather_condition
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN promotions p ON g.game_id = p.game_id
JOIN weather    w ON g.game_id = w.game_id
WHERE (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
      / NULLIF(a.expected_attendance_baseline, 0) < -0.10
ORDER BY variance_pct ASC
LIMIT 20;


-- Q08: Games overperforming expected attendance by more than 10%
-- Business question: What conditions create outperformance — good for prescriptive modeling?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    a.expected_attendance_baseline,
    ROUND(
        (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
        / NULLIF(a.expected_attendance_baseline, 0) * 100, 1
    ) AS variance_pct,
    g.rivalry_flag,
    g.nationally_televised_flag,
    p.promotion_type
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN promotions p ON g.game_id = p.game_id
WHERE (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
      / NULLIF(a.expected_attendance_baseline, 0) > 0.10
ORDER BY variance_pct DESC
LIMIT 20;


-- ============================================================
-- SECTION 2: TICKET REVENUE ANALYTICS
-- ============================================================

-- Q09: Total and average revenue by ticket segment
-- Business question: Which segments contribute the most ticket revenue?
SELECT
    ts.segment_name,
    ts.price_tier,
    COUNT(*)                                    AS game_records,
    SUM(tk.tickets_sold)                        AS total_tickets_sold,
    ROUND(AVG(tk.avg_ticket_price), 2)          AS avg_ticket_price,
    ROUND(SUM(tk.gross_ticket_revenue), 0)      AS total_gross_revenue,
    ROUND(SUM(tk.net_ticket_revenue), 0)        AS total_net_revenue,
    ROUND(AVG(tk.sell_through_rate), 1)         AS avg_sell_through_pct
FROM ticket_sales tk
JOIN ticket_segments ts ON tk.segment_id = ts.segment_id
GROUP BY ts.segment_name, ts.price_tier
ORDER BY total_net_revenue DESC;


-- Q10: Average ticket price by segment across demand tiers
-- Business question: How does game demand affect per-ticket yield by segment?
SELECT
    tk.segment_name,
    a.attendance_tier,
    ROUND(AVG(tk.avg_ticket_price), 2)          AS avg_ticket_price,
    ROUND(AVG(tk.sell_through_rate), 1)         AS avg_sell_through_pct,
    COUNT(*)                                    AS records
FROM ticket_sales tk
JOIN attendance a ON tk.game_id = a.game_id
GROUP BY tk.segment_name, a.attendance_tier
ORDER BY tk.segment_name, a.attendance_tier;


-- Q11: Sell-through rate ranking by ticket segment
-- Business question: Which segments consistently sell out vs. leave inventory unused?
WITH seg_summary AS (
    SELECT
        segment_name,
        ROUND(AVG(sell_through_rate), 2)    AS avg_sell_through,
        ROUND(MIN(sell_through_rate), 2)    AS min_sell_through,
        ROUND(MAX(sell_through_rate), 2)    AS max_sell_through
    FROM ticket_sales
    GROUP BY segment_name
)
SELECT
    segment_name,
    avg_sell_through,
    min_sell_through,
    max_sell_through,
    RANK() OVER (ORDER BY avg_sell_through DESC)    AS sell_through_rank
FROM seg_summary
ORDER BY avg_sell_through DESC;


-- Q12: Top 15 games by total net ticket revenue
-- Business question: Which specific matchups generate the highest ticketing returns?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    g.rivalry_flag,
    g.nationally_televised_flag,
    ROUND(SUM(tk.net_ticket_revenue), 0)    AS total_net_ticket_revenue,
    SUM(tk.tickets_sold)                    AS total_tickets_sold,
    a.capacity_pct,
    p.promotion_type
FROM games g
JOIN ticket_sales tk ON g.game_id = tk.game_id
JOIN attendance a    ON g.game_id = a.game_id
JOIN promotions p    ON g.game_id = p.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
         g.rivalry_flag, g.nationally_televised_flag, a.capacity_pct, p.promotion_type
ORDER BY total_net_ticket_revenue DESC
LIMIT 15;


-- Q13: Bottom 15 games by ticket revenue (low-demand opportunities)
-- Business question: Which games need promotional or pricing intervention?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    g.day_of_week,
    ROUND(SUM(tk.net_ticket_revenue), 0)    AS total_net_ticket_revenue,
    a.capacity_pct,
    p.promotion_type
FROM games g
JOIN ticket_sales tk ON g.game_id = tk.game_id
JOIN attendance a    ON g.game_id = a.game_id
JOIN promotions p    ON g.game_id = p.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
         g.day_of_week, a.capacity_pct, p.promotion_type
ORDER BY total_net_ticket_revenue ASC
LIMIT 15;


-- Q14: Discount impact on net ticket revenue
-- Business question: Are discounts eroding net revenue or driving volume that offsets the loss?
SELECT
    tk.segment_name,
    CASE
        WHEN tk.discount_pct = 0            THEN 'No Discount'
        WHEN tk.discount_pct < 10           THEN '1-9%'
        WHEN tk.discount_pct < 20           THEN '10-19%'
        WHEN tk.discount_pct < 30           THEN '20-29%'
        ELSE '30%+'
    END                                             AS discount_bucket,
    COUNT(*)                                        AS records,
    ROUND(AVG(tk.tickets_sold), 0)                  AS avg_tickets_sold,
    ROUND(AVG(tk.gross_ticket_revenue), 0)          AS avg_gross_revenue,
    ROUND(AVG(tk.net_ticket_revenue), 0)            AS avg_net_revenue,
    ROUND(AVG(tk.sell_through_rate), 1)             AS avg_sell_through
FROM ticket_sales tk
GROUP BY tk.segment_name, discount_bucket
ORDER BY tk.segment_name, discount_bucket;


-- Q15: Corporate partner allocation value by game
-- Business question: Which games maximise the value of corporate partner packages?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    ROUND(SUM(tk.net_ticket_revenue), 0)            AS corporate_ticket_revenue,
    ROUND(AVG(p2.sponsor_value_estimate), 0)        AS sponsor_value_estimate,
    ROUND(SUM(tk.net_ticket_revenue)
          + AVG(p2.sponsor_value_estimate), 0)      AS total_partner_value
FROM games g
JOIN ticket_sales tk ON g.game_id = tk.game_id AND tk.segment_name = 'Corporate Partner Allocation'
JOIN promotions  p2  ON g.game_id = p2.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name
ORDER BY total_partner_value DESC
LIMIT 20;


-- ============================================================
-- SECTION 3: PROMOTION ANALYTICS
-- ============================================================

-- Q16: Average attendance lift by promotion type
-- Business question: Which promotion types move the needle on attendance?
SELECT
    p.promotion_type,
    COUNT(*)                                AS games,
    ROUND(AVG(a.capacity_pct), 2)           AS avg_capacity_pct,
    ROUND(AVG(p.expected_promotion_lift_pct), 2) AS avg_expected_lift_pct,
    ROUND(AVG(a.actual_attendance), 0)      AS avg_actual_attendance
FROM promotions p
JOIN attendance a ON p.game_id = a.game_id
GROUP BY p.promotion_type
ORDER BY avg_capacity_pct DESC;


-- Q17: Total revenue by promotion type
-- Business question: Which promotions are associated with higher game-day revenue?
WITH game_rev AS (
    SELECT
        g.game_id,
        p.promotion_type,
        SUM(tk.net_ticket_revenue)                                          AS ticket_rev,
        (SELECT SUM(c.gross_revenue) FROM concessions c WHERE c.game_id = g.game_id)   AS con_rev,
        (SELECT SUM(m.gross_revenue) FROM merchandise m WHERE m.game_id = g.game_id)   AS merch_rev
    FROM games g
    JOIN promotions  p  ON g.game_id = p.game_id
    JOIN ticket_sales tk ON g.game_id = tk.game_id
    GROUP BY g.game_id, p.promotion_type
)
SELECT
    promotion_type,
    COUNT(*)                                                        AS games,
    ROUND(AVG(ticket_rev + COALESCE(con_rev,0) + COALESCE(merch_rev,0)), 0)  AS avg_total_revenue,
    ROUND(SUM(ticket_rev + COALESCE(con_rev,0) + COALESCE(merch_rev,0)), 0)  AS total_revenue
FROM game_rev
GROUP BY promotion_type
ORDER BY avg_total_revenue DESC;


-- Q18: Promotion ROI estimate
-- Business question: Do promotions generate enough incremental revenue to justify their cost?
SELECT
    p.promotion_type,
    COUNT(*)                                                AS games,
    ROUND(AVG(p.promotion_cost), 0)                        AS avg_promo_cost,
    ROUND(AVG(p.sponsor_value_estimate), 0)                AS avg_sponsor_value,
    ROUND(AVG(a.capacity_pct), 1)                          AS avg_capacity_pct,
    ROUND(AVG(p.sponsor_value_estimate) - AVG(p.promotion_cost), 0) AS avg_net_sponsor_gain
FROM promotions p
JOIN attendance a ON p.game_id = a.game_id
WHERE p.promotion_flag = TRUE
GROUP BY p.promotion_type
ORDER BY avg_net_sponsor_gain DESC;


-- Q19: Best promotion type for weekday games
-- Business question: On low-demand weeknight games, which promotion drives the most attendance?
SELECT
    p.promotion_type,
    COUNT(*)                                AS weekday_games,
    ROUND(AVG(a.capacity_pct), 2)           AS avg_capacity_pct,
    ROUND(AVG(a.actual_attendance), 0)      AS avg_attendance
FROM promotions p
JOIN attendance a ON p.game_id = a.game_id
JOIN games      g ON g.game_id = p.game_id
WHERE g.is_weekend = FALSE
  AND p.promotion_flag = TRUE
GROUP BY p.promotion_type
ORDER BY avg_capacity_pct DESC;


-- Q20: Best promotion type for low-demand games (attendance tier = Low)
-- Business question: Which promotions rescue the weakest games?
SELECT
    p.promotion_type,
    COUNT(*)                                AS low_demand_games,
    ROUND(AVG(a.capacity_pct), 2)           AS avg_capacity_pct,
    ROUND(AVG(a.actual_attendance), 0)      AS avg_attendance
FROM promotions p
JOIN attendance a ON p.game_id = a.game_id
WHERE a.attendance_tier = 'Low'
  AND p.promotion_flag = TRUE
GROUP BY p.promotion_type
ORDER BY avg_capacity_pct DESC;


-- ============================================================
-- SECTION 4: CONCESSIONS AND MERCHANDISE
-- ============================================================

-- Q21: Concession revenue per attendee by game
-- Business question: Which games generate the highest food/beverage per-cap spend?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    a.attendance_tier,
    ROUND(SUM(c.gross_revenue), 0)                              AS total_concession_revenue,
    ROUND(SUM(c.gross_revenue) / NULLIF(a.actual_attendance, 0), 2) AS concession_per_cap
FROM games g
JOIN concessions c ON g.game_id = c.game_id
JOIN attendance  a ON g.game_id = a.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
         a.actual_attendance, a.attendance_tier
ORDER BY concession_per_cap DESC
LIMIT 20;


-- Q22: Merchandise revenue per attendee by game
-- Business question: Which games generate the highest merchandise per-cap spend?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    g.rivalry_flag,
    ROUND(SUM(m.gross_revenue), 0)                              AS total_merch_revenue,
    ROUND(SUM(m.gross_revenue) / NULLIF(a.actual_attendance, 0), 2) AS merch_per_cap
FROM games g
JOIN merchandise m ON g.game_id = m.game_id
JOIN attendance  a ON g.game_id = a.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
         a.actual_attendance, g.rivalry_flag
ORDER BY merch_per_cap DESC
LIMIT 20;


-- Q23: Highest food demand games (by food + beverage units)
-- Business question: Which upcoming games need the largest food inventory preparation?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    SUM(CASE WHEN c.category IN ('Food','Beverage','Combo Meals') THEN c.units_sold ELSE 0 END) AS food_bev_units,
    ROUND(SUM(CASE WHEN c.category IN ('Food','Beverage','Combo Meals') THEN c.gross_revenue ELSE 0 END), 0) AS food_bev_revenue,
    SUM(CASE WHEN c.category IN ('Food','Beverage','Combo Meals') THEN c.recommended_inventory_units ELSE 0 END) AS food_bev_inventory_rec
FROM games g
JOIN concessions c ON g.game_id = c.game_id
JOIN attendance  a ON g.game_id = a.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name, a.actual_attendance
ORDER BY food_bev_units DESC
LIMIT 20;


-- Q24: Highest merchandise demand games
-- Business question: Which games need the most jersey and apparel stock?
SELECT
    g.game_id,
    g.game_date,
    g.home_team_name,
    g.away_team_name,
    g.rivalry_flag,
    a.actual_attendance,
    SUM(m.units_sold)                                   AS total_merch_units,
    ROUND(SUM(m.gross_revenue), 0)                      AS total_merch_revenue,
    SUM(m.recommended_inventory_units)                  AS total_inventory_rec
FROM games g
JOIN merchandise m ON g.game_id = m.game_id
JOIN attendance  a ON g.game_id = a.game_id
GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
         g.rivalry_flag, a.actual_attendance
ORDER BY total_merch_units DESC
LIMIT 20;


-- Q25: Inventory recommendation by attendance tier
-- Business question: How should inventory levels scale with expected game demand?
SELECT
    a.attendance_tier,
    COUNT(DISTINCT g.game_id)                           AS games,
    ROUND(AVG(a.actual_attendance), 0)                  AS avg_attendance,
    ROUND(AVG(c_agg.total_con_inventory), 0)            AS avg_concession_inventory_rec,
    ROUND(AVG(m_agg.total_merch_inventory), 0)          AS avg_merch_inventory_rec
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN (
    SELECT game_id, SUM(recommended_inventory_units) AS total_con_inventory
    FROM concessions GROUP BY game_id
) c_agg ON g.game_id = c_agg.game_id
JOIN (
    SELECT game_id, SUM(recommended_inventory_units) AS total_merch_inventory
    FROM merchandise GROUP BY game_id
) m_agg ON g.game_id = m_agg.game_id
GROUP BY a.attendance_tier
ORDER BY avg_attendance DESC;


-- Q26: Gross margin by concessions category
-- Business question: Which concession categories are most profitable?
SELECT
    category,
    ROUND(SUM(gross_revenue), 0)            AS total_revenue,
    ROUND(SUM(estimated_cost), 0)           AS total_cost,
    ROUND(SUM(gross_margin), 0)             AS total_margin,
    ROUND(AVG(gross_margin / NULLIF(gross_revenue, 0)) * 100, 1) AS avg_margin_pct,
    ROUND(AVG(per_cap_spend), 2)            AS avg_per_cap_spend
FROM concessions
GROUP BY category
ORDER BY total_margin DESC;


-- Q27: Gross margin by merchandise category
-- Business question: Which merchandise categories yield the highest margin contribution?
SELECT
    category,
    ROUND(SUM(gross_revenue), 0)            AS total_revenue,
    ROUND(SUM(estimated_cost), 0)           AS total_cost,
    ROUND(SUM(gross_margin), 0)             AS total_margin,
    ROUND(AVG(gross_margin / NULLIF(gross_revenue, 0)) * 100, 1) AS avg_margin_pct,
    ROUND(AVG(per_cap_spend), 2)            AS avg_per_cap_spend
FROM merchandise
GROUP BY category
ORDER BY total_margin DESC;


-- ============================================================
-- SECTION 5: FAN ANALYTICS
-- ============================================================

-- Q28: Fan segment spend ranking (by loyalty status)
-- Business question: Which fan loyalty tiers generate the most total spend per person?
SELECT
    loyalty_status,
    COUNT(*)                                    AS fan_count,
    ROUND(AVG(avg_ticket_spend), 2)             AS avg_ticket_spend,
    ROUND(AVG(avg_concession_spend), 2)         AS avg_concession_spend,
    ROUND(AVG(avg_merchandise_spend), 2)        AS avg_merch_spend,
    ROUND(AVG(avg_ticket_spend + avg_concession_spend + avg_merchandise_spend), 2) AS avg_total_spend,
    RANK() OVER (ORDER BY AVG(avg_ticket_spend + avg_concession_spend + avg_merchandise_spend) DESC) AS spend_rank
FROM fan_profiles
GROUP BY loyalty_status
ORDER BY avg_total_spend DESC;


-- Q29: Loyalty status by total spend — cumulative revenue contribution
-- Business question: What share of fan-generated revenue comes from top loyalty tiers?
WITH loyalty_spend AS (
    SELECT
        fp.loyalty_status,
        SUM(ft.total_spend)             AS total_revenue,
        COUNT(DISTINCT ft.fan_id)       AS unique_fans
    FROM fan_transactions ft
    JOIN fan_profiles fp ON ft.fan_id = fp.fan_id
    GROUP BY fp.loyalty_status
),
total AS (SELECT SUM(total_revenue) AS grand_total FROM loyalty_spend)
SELECT
    ls.loyalty_status,
    ls.unique_fans,
    ROUND(ls.total_revenue, 0)                          AS total_revenue,
    ROUND(ls.total_revenue / t.grand_total * 100, 1)    AS revenue_share_pct,
    ROUND(ls.total_revenue / NULLIF(ls.unique_fans, 0), 2) AS revenue_per_fan
FROM loyalty_spend ls, total t
ORDER BY revenue_per_fan DESC;


-- Q30: Promotion usage by fan segment
-- Business question: Which fan types are most responsive to promotions?
SELECT
    loyalty_status,
    COUNT(*)                                AS fans,
    ROUND(AVG(promotion_usage_rate) * 100, 1)  AS avg_promo_usage_pct,
    ROUND(AVG(avg_ticket_spend), 2)         AS avg_ticket_spend,
    ROUND(AVG(games_attended_last_12_months), 1) AS avg_games_attended
FROM fan_profiles
GROUP BY loyalty_status
ORDER BY avg_promo_usage_pct DESC;


-- Q31: Repeat buyers vs casual buyers spending comparison
-- Business question: What is the value differential between engaged and casual fans?
SELECT
    CASE
        WHEN games_attended_last_12_months >= 20 THEN 'High Frequency (20+)'
        WHEN games_attended_last_12_months >= 8  THEN 'Regular (8-19)'
        WHEN games_attended_last_12_months >= 3  THEN 'Occasional (3-7)'
        ELSE 'Casual (1-2)'
    END                                         AS frequency_tier,
    COUNT(*)                                    AS fans,
    ROUND(AVG(avg_ticket_spend), 2)             AS avg_ticket_spend,
    ROUND(AVG(avg_concession_spend), 2)         AS avg_concession_spend,
    ROUND(AVG(avg_merchandise_spend), 2)        AS avg_merch_spend,
    ROUND(AVG(fan_value_score), 3)              AS avg_fan_value_score
FROM fan_profiles
GROUP BY frequency_tier
ORDER BY avg_fan_value_score DESC;


-- Q32: Distance from arena vs average spend
-- Business question: Do fans who travel farther tend to spend more once they arrive?
SELECT
    distance_from_arena_bucket,
    COUNT(*)                                    AS fans,
    ROUND(AVG(avg_ticket_spend), 2)             AS avg_ticket_spend,
    ROUND(AVG(avg_concession_spend), 2)         AS avg_concession_spend,
    ROUND(AVG(avg_merchandise_spend), 2)        AS avg_merch_spend,
    ROUND(AVG(games_attended_last_12_months), 1) AS avg_games_attended
FROM fan_profiles
GROUP BY distance_from_arena_bucket
ORDER BY avg_ticket_spend DESC;


-- Q33: Highest-value fan groups by household type
-- Business question: Which household types represent priority acquisition and retention targets?
SELECT
    household_type,
    COUNT(*)                                    AS fans,
    ROUND(AVG(fan_value_score), 3)              AS avg_fan_value_score,
    ROUND(AVG(avg_ticket_spend), 2)             AS avg_ticket_spend,
    ROUND(AVG(avg_concession_spend), 2)         AS avg_concession_spend,
    ROUND(AVG(avg_merchandise_spend), 2)        AS avg_merch_spend,
    RANK() OVER (ORDER BY AVG(fan_value_score) DESC) AS value_rank
FROM fan_profiles
GROUP BY household_type
ORDER BY avg_fan_value_score DESC;


-- ============================================================
-- SECTION 6: EXECUTIVE KPIs
-- ============================================================

-- Q34: Total game-day revenue breakdown per game
-- Business question: What is the complete revenue picture for each game?
SELECT
    g.game_id,
    g.game_date,
    g.season,
    g.home_team_name,
    g.away_team_name,
    a.actual_attendance,
    ROUND(a.capacity_pct, 1)                                AS capacity_pct,
    ROUND(t_agg.ticket_rev, 0)                              AS ticket_revenue,
    ROUND(c_agg.con_rev, 0)                                 AS concession_revenue,
    ROUND(m_agg.merch_rev, 0)                               AS merchandise_revenue,
    ROUND(t_agg.ticket_rev + c_agg.con_rev + m_agg.merch_rev, 0) AS total_game_day_revenue
FROM games g
JOIN attendance a ON g.game_id = a.game_id
JOIN (SELECT game_id, SUM(net_ticket_revenue) AS ticket_rev FROM ticket_sales GROUP BY game_id) t_agg ON g.game_id = t_agg.game_id
JOIN (SELECT game_id, SUM(gross_revenue) AS con_rev FROM concessions GROUP BY game_id) c_agg ON g.game_id = c_agg.game_id
JOIN (SELECT game_id, SUM(gross_revenue) AS merch_rev FROM merchandise GROUP BY game_id) m_agg ON g.game_id = m_agg.game_id
ORDER BY total_game_day_revenue DESC;


-- Q35: Total revenue split across all games
-- Business question: What is the aggregate revenue composition across all seasons?
SELECT
    ROUND(SUM(t.net_ticket_revenue), 0)                     AS total_ticket_revenue,
    ROUND(SUM(c.gross_revenue), 0)                          AS total_concession_revenue,
    ROUND(SUM(m.gross_revenue), 0)                          AS total_merchandise_revenue,
    ROUND(SUM(t.net_ticket_revenue + c.gross_revenue + m.gross_revenue), 0) AS total_game_day_revenue,
    ROUND(SUM(t.net_ticket_revenue) /
          NULLIF(SUM(t.net_ticket_revenue + c.gross_revenue + m.gross_revenue), 0) * 100, 1) AS ticket_share_pct,
    ROUND(SUM(c.gross_revenue) /
          NULLIF(SUM(t.net_ticket_revenue + c.gross_revenue + m.gross_revenue), 0) * 100, 1) AS concession_share_pct,
    ROUND(SUM(m.gross_revenue) /
          NULLIF(SUM(t.net_ticket_revenue + c.gross_revenue + m.gross_revenue), 0) * 100, 1) AS merch_share_pct
FROM ticket_sales  t
JOIN concessions   c ON t.game_id = c.game_id
JOIN merchandise   m ON t.game_id = m.game_id;


-- Q36: Top 10 games by projected total revenue
-- Business question: Which games should receive the most operational investment?
WITH game_totals AS (
    SELECT
        g.game_id,
        g.game_date,
        g.home_team_name,
        g.away_team_name,
        g.rivalry_flag,
        g.nationally_televised_flag,
        a.actual_attendance,
        ROUND(a.capacity_pct, 1)        AS capacity_pct,
        p.promotion_type,
        ROUND(SUM(tk.net_ticket_revenue), 0) AS ticket_rev,
        ROUND(con.con_rev, 0)           AS con_rev,
        ROUND(mer.merch_rev, 0)         AS merch_rev
    FROM games g
    JOIN attendance a  ON g.game_id = a.game_id
    JOIN promotions p  ON g.game_id = p.game_id
    JOIN ticket_sales tk ON g.game_id = tk.game_id
    JOIN (SELECT game_id, SUM(gross_revenue) AS con_rev   FROM concessions  GROUP BY game_id) con ON g.game_id = con.game_id
    JOIN (SELECT game_id, SUM(gross_revenue) AS merch_rev FROM merchandise  GROUP BY game_id) mer ON g.game_id = mer.game_id
    GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
             g.rivalry_flag, g.nationally_televised_flag, a.actual_attendance,
             a.capacity_pct, p.promotion_type, con.con_rev, mer.merch_rev
)
SELECT
    game_id, game_date, home_team_name, away_team_name,
    rivalry_flag, nationally_televised_flag, actual_attendance, capacity_pct,
    promotion_type, ticket_rev, con_rev, merch_rev,
    ticket_rev + con_rev + merch_rev    AS total_revenue,
    DENSE_RANK() OVER (ORDER BY ticket_rev + con_rev + merch_rev DESC) AS revenue_rank
FROM game_totals
ORDER BY total_revenue DESC
LIMIT 10;


-- Q37: Underperforming high-potential games
-- Business question: Which games had strong conditions but fell short of expected attendance?
WITH potential AS (
    SELECT
        g.game_id,
        g.game_date,
        g.home_team_name,
        g.away_team_name,
        a.capacity_pct,
        a.attendance_tier,
        (CASE WHEN g.rivalry_flag           THEN 1 ELSE 0 END
         + CASE WHEN g.nationally_televised_flag THEN 1 ELSE 0 END
         + CASE WHEN g.is_weekend           THEN 1 ELSE 0 END)  AS demand_signal_score,
        (a.actual_attendance - a.expected_attendance_baseline)::NUMERIC
        / NULLIF(a.expected_attendance_baseline, 0) * 100       AS variance_pct
    FROM games g
    JOIN attendance a ON g.game_id = a.game_id
)
SELECT *
FROM potential
WHERE demand_signal_score >= 2
  AND variance_pct < -5
ORDER BY variance_pct ASC
LIMIT 20;


-- Q38: Monthly revenue trend
-- Business question: How does game-day revenue trend across the season calendar?
SELECT
    g.season,
    g.month,
    TO_CHAR(TO_DATE(g.month::TEXT, 'MM'), 'Month') AS month_name,
    COUNT(DISTINCT g.game_id)                       AS games,
    ROUND(SUM(tk.net_ticket_revenue), 0)            AS ticket_revenue,
    ROUND(con.con_rev, 0)                           AS concession_revenue,
    ROUND(mer.merch_rev, 0)                         AS merchandise_revenue,
    ROUND(SUM(tk.net_ticket_revenue) + con.con_rev + mer.merch_rev, 0) AS total_revenue
FROM games g
JOIN ticket_sales tk ON g.game_id = tk.game_id
JOIN (SELECT c.game_id, g2.season, g2.month, SUM(c.gross_revenue) AS con_rev
      FROM concessions c JOIN games g2 ON c.game_id = g2.game_id
      GROUP BY c.game_id, g2.season, g2.month) con ON g.game_id = con.game_id
JOIN (SELECT m.game_id, g2.season, g2.month, SUM(m.gross_revenue) AS merch_rev
      FROM merchandise m JOIN games g2 ON m.game_id = g2.game_id
      GROUP BY m.game_id, g2.season, g2.month) mer ON g.game_id = mer.game_id
GROUP BY g.season, g.month, con.con_rev, mer.merch_rev
ORDER BY g.season, g.month;


-- Q39: Average spend per fan by game type (rivalry vs. regular)
-- Business question: Do rivalry games justify higher staffing and inventory investment?
SELECT
    CASE WHEN g.rivalry_flag THEN 'Rivalry Game' ELSE 'Regular Game' END AS game_type,
    COUNT(DISTINCT ft.transaction_id)       AS transactions,
    COUNT(DISTINCT ft.fan_id)               AS unique_fans,
    ROUND(AVG(ft.total_spend), 2)           AS avg_total_spend_per_txn,
    ROUND(AVG(ft.ticket_spend), 2)          AS avg_ticket_spend,
    ROUND(AVG(ft.concession_spend), 2)      AS avg_concession_spend,
    ROUND(AVG(ft.merchandise_spend), 2)     AS avg_merch_spend
FROM fan_transactions ft
JOIN games g ON ft.game_id = g.game_id
GROUP BY g.rivalry_flag
ORDER BY avg_total_spend_per_txn DESC;


-- Q40: Games needing higher staffing or inventory (near-sellout + high revenue)
-- Business question: Which upcoming games require maximum operational readiness?
WITH game_summary AS (
    SELECT
        g.game_id,
        g.game_date,
        g.home_team_name,
        g.away_team_name,
        a.actual_attendance,
        a.arena_capacity,
        ROUND(a.capacity_pct, 1)    AS capacity_pct,
        a.attendance_tier,
        p.promotion_type,
        ROUND(SUM(tk.net_ticket_revenue), 0)    AS ticket_rev,
        SUM(c.recommended_inventory_units)       AS total_con_inventory_rec,
        SUM(m.recommended_inventory_units)       AS total_merch_inventory_rec,
        CASE
            WHEN a.capacity_pct >= 95 THEN 'Maximum Staffing'
            WHEN a.capacity_pct >= 85 THEN 'High Staffing'
            WHEN a.capacity_pct >= 70 THEN 'Medium Staffing'
            ELSE 'Standard Staffing'
        END AS staffing_level
    FROM games g
    JOIN attendance   a  ON g.game_id = a.game_id
    JOIN promotions   p  ON g.game_id = p.game_id
    JOIN ticket_sales tk ON g.game_id = tk.game_id
    JOIN concessions  c  ON g.game_id = c.game_id
    JOIN merchandise  m  ON g.game_id = m.game_id
    GROUP BY g.game_id, g.game_date, g.home_team_name, g.away_team_name,
             a.actual_attendance, a.arena_capacity, a.capacity_pct,
             a.attendance_tier, p.promotion_type
)
SELECT *
FROM game_summary
WHERE attendance_tier IN ('High', 'Sellout')
ORDER BY capacity_pct DESC
LIMIT 20;
