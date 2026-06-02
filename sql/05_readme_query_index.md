# SQL Query Index

This document indexes all SQL queries in `03_business_analysis_queries.sql` and views in `04_kpi_views.sql`.

---

## Business Analysis Queries (`03_business_analysis_queries.sql`)

### Section 1 — Attendance Analytics

| Query | Business Question |
|-------|-------------------|
| Q01 | Top 10 opponents by average attendance |
| Q02 | Attendance by day of week |
| Q03 | Attendance by month (seasonality) |
| Q04 | Weekend vs weekday attendance comparison |
| Q05 | Average capacity percentage by opponent market tier |
| Q06 | Sellout and near-sellout games |
| Q07 | Games underperforming expected attendance by >10% |
| Q08 | Games overperforming expected attendance by >10% |

### Section 2 — Ticket Revenue Analytics

| Query | Business Question |
|-------|-------------------|
| Q09 | Total and average revenue by ticket segment |
| Q10 | Average ticket price by segment across demand tiers |
| Q11 | Sell-through rate ranking by ticket segment (window function) |
| Q12 | Top 15 games by total net ticket revenue |
| Q13 | Bottom 15 games by ticket revenue (intervention candidates) |
| Q14 | Discount impact on net ticket revenue |
| Q15 | Corporate partner allocation value by game |

### Section 3 — Promotion Analytics

| Query | Business Question |
|-------|-------------------|
| Q16 | Average attendance lift by promotion type |
| Q17 | Total revenue by promotion type |
| Q18 | Promotion ROI estimate (sponsor value vs. cost) |
| Q19 | Best promotion type for weekday games |
| Q20 | Best promotion type for low-demand games |

### Section 4 — Concessions and Merchandise

| Query | Business Question |
|-------|-------------------|
| Q21 | Concession revenue per attendee by game |
| Q22 | Merchandise revenue per attendee by game |
| Q23 | Highest food demand games (inventory planning) |
| Q24 | Highest merchandise demand games |
| Q25 | Inventory recommendation by attendance tier |
| Q26 | Gross margin by concessions category |
| Q27 | Gross margin by merchandise category |

### Section 5 — Fan Analytics

| Query | Business Question |
|-------|-------------------|
| Q28 | Fan segment spend ranking by loyalty tier |
| Q29 | Loyalty status cumulative revenue contribution |
| Q30 | Promotion usage by fan segment |
| Q31 | Repeat buyers vs casual buyers comparison |
| Q32 | Distance from arena vs average spend |
| Q33 | Highest-value fan groups by household type |

### Section 6 — Executive KPIs

| Query | Business Question |
|-------|-------------------|
| Q34 | Total game-day revenue per game (full P&L breakdown) |
| Q35 | Aggregate revenue split: tickets, concessions, merchandise |
| Q36 | Top 10 games by projected total revenue (DENSE_RANK) |
| Q37 | Underperforming high-potential games |
| Q38 | Monthly revenue trend by season |
| Q39 | Average fan spend by game type (rivalry vs. regular) |
| Q40 | Games needing maximum staffing and inventory |

---

## KPI Views (`04_kpi_views.sql`)

| View | Description |
|------|-------------|
| `vw_game_day_revenue` | Full per-game revenue P&L: tickets, concessions, merchandise, total, revenue/attendee |
| `vw_attendance_performance` | Attendance vs. baseline with variance % and performance flag |
| `vw_ticket_segment_performance` | Per-game, per-segment KPIs with revenue ranking window function |
| `vw_promotion_effectiveness` | Promotion lift vs. baseline, cost, sponsor value, revenue |
| `vw_concession_merchandise_demand` | Per-game per-cap spend, margins, and inventory recommendations |
| `vw_fan_segment_value` | Fan loyalty tier aggregations: spend, engagement, value score |
| `vw_executive_dashboard` | Single-row executive summary of all platform KPIs |

---

## SQL Techniques Used

- `JOIN` (INNER, multiple tables)
- `LEFT JOIN` with NULLable aggregations
- Common Table Expressions (`WITH ... AS`)
- Window functions: `RANK()`, `DENSE_RANK()`, `ROW_NUMBER()`, `AVG() OVER`
- `CASE WHEN` for bucketing and labeling
- `NULLIF` for safe division
- `COALESCE` for null handling
- `DATE` and `TO_CHAR` for calendar formatting
- Subqueries in `FROM` clause
- `CROSS JOIN` for scalar baseline comparisons
- Aggregate functions: `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`
- `GROUP BY`, `ORDER BY`, `LIMIT`
- `CREATE OR REPLACE VIEW`
- `CHECK` constraints, `SERIAL`, `CASCADE`
- `CREATE INDEX` for performance
