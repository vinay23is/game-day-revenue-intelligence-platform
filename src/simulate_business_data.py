"""
Generates all simulated CSVs for the Game-Day Revenue Intelligence Platform.
All data is internally consistent: attendance drives ticket sales, concessions,
merchandise, and inventory recommendations.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (
    DATA_SIMULATED_DIR, RANDOM_SEED, NUM_TEAMS, SEASONS,
    TICKET_SEGMENTS, PROMOTION_TYPES, CONCESSION_CATEGORIES,
    MERCHANDISE_CATEGORIES, LOYALTY_STATUSES, NUM_FAN_PROFILES,
    NUM_FAN_TRANSACTIONS
)

rng = np.random.default_rng(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

TEAM_DATA = [
    ("ATL", "Atlanta Flyers",          "Atlanta",       "East", "Southeast", "Peach State Arena",        19621, "Large",   0.72),
    ("BOS", "Boston Harbors",          "Boston",        "East", "Atlantic",  "Harbor Center",            19156, "Large",   0.91),
    ("BKN", "Brooklyn Bridgers",       "Brooklyn",      "East", "Atlantic",  "Bridge Arena",             17732, "Large",   0.78),
    ("CHA", "Charlotte Crowns",        "Charlotte",     "East", "Southeast", "Crown Coliseum",           19077, "Medium",  0.61),
    ("CHI", "Chicago Cyclones",        "Chicago",       "East", "Central",   "Lakefront Center",         20917, "Large",   0.83),
    ("CLE", "Cleveland Comets",        "Cleveland",     "East", "Central",   "Lakeside Arena",           19432, "Medium",  0.74),
    ("DAL", "Dallas Wranglers",        "Dallas",        "West", "Southwest", "Lone Star Center",         19200, "Large",   0.76),
    ("DEN", "Denver Peaks",            "Denver",        "West", "Northwest", "Mile High Arena",          19520, "Medium",  0.69),
    ("DET", "Detroit Motors",          "Detroit",       "East", "Central",   "Motor City Arena",         20491, "Medium",  0.58),
    ("GSF", "San Francisco Waves",     "San Francisco", "West", "Pacific",   "Bay Arena",                18064, "Large",   0.95),
    ("HOU", "Houston Meteors",         "Houston",       "West", "Southwest", "Space City Center",        18055, "Large",   0.71),
    ("IND", "Indianapolis Racers",     "Indianapolis",  "East", "Central",   "Speedway Fieldhouse",      17923, "Medium",  0.65),
    ("LAB", "Los Angeles Blaze",       "Los Angeles",   "West", "Pacific",   "Metro Arena",              19060, "Large",   0.73),
    ("LAS", "Los Angeles Stars",       "Los Angeles",   "West", "Pacific",   "Metro Arena",              19060, "Large",   0.97),
    ("MEM", "Memphis Blues",           "Memphis",       "West", "Southwest", "Bluff City Forum",         17794, "Small",   0.62),
    ("MIA", "Miami Storm",             "Miami",         "East", "Southeast", "Bayfront Arena",           19600, "Large",   0.84),
    ("MIL", "Milwaukee Barons",        "Milwaukee",     "East", "Central",   "Lakefront Forum",          17341, "Medium",  0.80),
    ("MIN", "Minneapolis Northstars",  "Minneapolis",   "West", "Northwest", "North Star Center",        18978, "Medium",  0.60),
    ("NOR", "New Orleans Crescents",   "New Orleans",   "West", "Southwest", "Crescent Center",          16867, "Small",   0.59),
    ("NYE", "New York Empire",         "New York",      "East", "Atlantic",  "Empire Garden",            19812, "Large",   0.88),
    ("OKC", "Oklahoma City Outlaws",   "Oklahoma City", "West", "Northwest", "Prairie Center",           18203, "Small",   0.67),
    ("ORL", "Orlando Rays",            "Orlando",       "East", "Southeast", "Sunshine Arena",           18846, "Medium",  0.57),
    ("PHI", "Philadelphia Founders",   "Philadelphia",  "East", "Atlantic",  "Liberty Center",           20478, "Large",   0.81),
    ("PHX", "Phoenix Firebirds",       "Phoenix",       "West", "Pacific",   "Desert Center",            17125, "Large",   0.86),
    ("POR", "Portland Pines",          "Portland",      "West", "Northwest", "Rose District Arena",      19393, "Medium",  0.70),
    ("SAC", "Sacramento Capitals",     "Sacramento",    "West", "Pacific",   "Capitol One Arena",        17608, "Medium",  0.63),
    ("SAT", "San Antonio Legends",     "San Antonio",   "West", "Southwest", "Alamo Center",             18418, "Medium",  0.75),
    ("TOR", "Toronto Towers",          "Toronto",       "East", "Atlantic",  "Tower Arena",              19800, "Large",   0.79),
    ("SLC", "Salt Lake Summit",        "Salt Lake City","West", "Northwest", "Summit Center",            18206, "Medium",  0.68),
    ("WAS", "Washington Republic",     "Washington",    "East", "Southeast", "Capitol Arena",            20356, "Large",   0.66),
]


def generate_teams() -> pd.DataFrame:
    rows = []
    for i, row in enumerate(TEAM_DATA, start=1):
        abbr, name, city, conf, div, arena, cap, mkt, pop = row
        rows.append({
            "team_id": i,
            "team_abbr": abbr,
            "team_name": name,
            "team_city": city,
            "conference": conf,
            "division": div,
            "arena_name": arena,
            "arena_capacity": cap,
            "market_size_tier": mkt,
            "historical_popularity_score": pop,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

RIVALRY_PAIRS = {
    ("BOS", "NYE"), ("BOS", "PHI"), ("LAS", "LAB"), ("LAS", "GSF"),
    ("CHI", "DET"), ("MIA", "BOS"), ("GSF", "LAS"), ("PHI", "NYE"),
    ("CLE", "GSF"), ("CLE", "BOS"), ("MIL", "BOS"), ("PHX", "LAS"),
}

NATIONALLY_TELEVISED_TEAMS = {"LAS", "GSF", "BOS", "CHI", "MIA", "NYE", "PHI"}

HOLIDAY_MONTHS = {12, 1}  # Dec-Jan holiday stretch; Feb for All-Star


def generate_games(teams: pd.DataFrame) -> pd.DataFrame:
    abbr_to_id = dict(zip(teams["team_abbr"], teams["team_id"]))
    abbr_to_name = dict(zip(teams["team_abbr"], teams["team_name"]))
    abbr_to_pop = dict(zip(teams["team_abbr"], teams["historical_popularity_score"]))
    team_abbrs = teams["team_abbr"].tolist()

    records = []
    game_id = 1

    # Seasonal win-rate evolution per team
    season_win_pct = {}
    for abbr in team_abbrs:
        base = abbr_to_pop[abbr] * 0.55 + rng.uniform(-0.05, 0.05)
        season_win_pct[abbr] = np.clip(base, 0.25, 0.75)

    for season in SEASONS:
        # Drift win pcts slightly each season
        for abbr in team_abbrs:
            season_win_pct[abbr] = np.clip(
                season_win_pct[abbr] + rng.uniform(-0.07, 0.07), 0.20, 0.80
            )

        # Build schedule: each team plays ~41 home games across opponent rotations
        home_games: dict[str, list] = {a: [] for a in team_abbrs}
        opponents = team_abbrs.copy()

        for home_abbr in team_abbrs:
            opp_pool = [a for a in opponents if a != home_abbr]
            chosen = list(rng.choice(opp_pool, size=min(41, len(opp_pool)), replace=False))
            # duplicate some high-popularity opponents to reach ~41
            while len(chosen) < 41:
                chosen.append(rng.choice(opp_pool))
            home_games[home_abbr] = chosen[:41]

        # Date range for season
        start_date = pd.Timestamp(f"{season}-10-15")
        end_date = pd.Timestamp(f"{season+1}-04-15")
        date_range = pd.date_range(start_date, end_date, freq="D")
        game_dates = [d for d in date_range if d.dayofweek in (1, 2, 3, 4, 5, 6)]

        # Running form tracker
        recent_results: dict[str, list] = {a: [] for a in team_abbrs}

        date_cursor = 0
        for home_abbr in team_abbrs:
            for away_abbr in home_games[home_abbr]:
                if date_cursor >= len(game_dates):
                    date_cursor = 0
                game_date = game_dates[date_cursor]
                date_cursor = (date_cursor + 17) % len(game_dates)

                is_rivalry = (
                    (home_abbr, away_abbr) in RIVALRY_PAIRS
                    or (away_abbr, home_abbr) in RIVALRY_PAIRS
                )
                is_tv = (
                    home_abbr in NATIONALLY_TELEVISED_TEAMS
                    or away_abbr in NATIONALLY_TELEVISED_TEAMS
                )
                is_weekend = game_date.dayofweek >= 4
                month = game_date.month
                is_holiday = month in HOLIDAY_MONTHS

                home_wp = season_win_pct[home_abbr]
                away_wp = season_win_pct[away_abbr]

                # Recent form = win rate in last 5 games (default 0.5)
                h_recent = np.mean(recent_results[home_abbr][-5:]) if recent_results[home_abbr] else 0.5
                a_recent = np.mean(recent_results[away_abbr][-5:]) if recent_results[away_abbr] else 0.5

                # Simulate game outcome
                home_win_prob = 0.55 + 0.2 * (home_wp - away_wp)
                home_win = rng.random() < home_win_prob
                home_score = int(rng.integers(95, 130))
                away_score = int(home_score + rng.integers(-20, 20))
                if home_win:
                    away_score = min(away_score, home_score - 1)
                else:
                    away_score = max(away_score, home_score + 1)

                recent_results[home_abbr].append(int(home_win))
                recent_results[away_abbr].append(int(not home_win))

                records.append({
                    "game_id": game_id,
                    "season": season,
                    "game_date": game_date.date(),
                    "home_team_id": abbr_to_id[home_abbr],
                    "away_team_id": abbr_to_id[away_abbr],
                    "home_team_name": abbr_to_name[home_abbr],
                    "away_team_name": abbr_to_name[away_abbr],
                    "home_team_abbr": home_abbr,
                    "away_team_abbr": away_abbr,
                    "day_of_week": game_date.strftime("%A"),
                    "month": month,
                    "is_weekend": is_weekend,
                    "is_holiday_period": is_holiday,
                    "rivalry_flag": is_rivalry,
                    "nationally_televised_flag": is_tv,
                    "home_team_win_pct_entering_game": round(home_wp, 4),
                    "away_team_win_pct_entering_game": round(away_wp, 4),
                    "home_team_recent_form": round(h_recent, 4),
                    "away_team_recent_form": round(a_recent, 4),
                    "home_score": home_score,
                    "away_score": away_score,
                    "home_win_flag": int(home_win),
                })
                game_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def generate_weather(games: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in games.iterrows():
        month = row["month"]
        # Temperature model
        if month in (12, 1, 2):
            temp = rng.normal(28, 12)
        elif month in (3, 4, 10, 11):
            temp = rng.normal(52, 15)
        else:
            temp = rng.normal(75, 12)
        temp = float(np.clip(temp, 5, 105))

        snow = bool(temp < 35 and rng.random() < 0.25)
        precip = bool(rng.random() < 0.18 or snow)
        severe = bool(rng.random() < 0.03 and precip)

        if severe:
            condition = "Severe Storm"
        elif snow:
            condition = "Snow"
        elif precip and temp < 50:
            condition = "Rain/Cold"
        elif precip:
            condition = "Rain"
        elif temp > 85:
            condition = "Hot/Sunny"
        else:
            condition = "Clear"

        records.append({
            "game_id": row["game_id"],
            "temperature_f": round(temp, 1),
            "precipitation_flag": precip,
            "snow_flag": snow,
            "severe_weather_flag": severe,
            "weather_condition": condition,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Promotions
# ---------------------------------------------------------------------------

def generate_promotions(games: pd.DataFrame) -> pd.DataFrame:
    promo_costs = {
        "None": 0,
        "Family Night": 8000,
        "Student Discount": 3500,
        "Merchandise Giveaway": 22000,
        "Food Voucher": 12000,
        "Theme Night": 18000,
        "Corporate Partner Night": 5000,
        "Community Night": 9000,
        "Premium Experience": 30000,
    }
    promo_lift = {
        "None": 0.0,
        "Family Night": 0.06,
        "Student Discount": 0.04,
        "Merchandise Giveaway": 0.09,
        "Food Voucher": 0.05,
        "Theme Night": 0.07,
        "Corporate Partner Night": 0.03,
        "Community Night": 0.05,
        "Premium Experience": 0.04,
    }
    sponsor_cats = ["None", "Beverage", "Financial", "Healthcare", "Tech", "Auto", "Retail"]

    records = []
    for i, (_, row) in enumerate(games.iterrows(), start=1):
        # ~55% of games have a promotion
        if rng.random() < 0.55:
            promo_type = rng.choice(PROMOTION_TYPES[1:])
        else:
            promo_type = "None"

        has_promo = promo_type != "None"
        cost = promo_costs[promo_type] * (1 + rng.uniform(-0.15, 0.15))
        lift = promo_lift[promo_type] + rng.uniform(-0.01, 0.01)
        sponsor = rng.choice(sponsor_cats[1:]) if has_promo else "None"
        sponsor_val = float(rng.uniform(5000, 75000)) if has_promo else 0.0

        records.append({
            "promotion_id": i,
            "game_id": row["game_id"],
            "promotion_flag": has_promo,
            "promotion_type": promo_type,
            "promotion_cost": round(cost, 2) if has_promo else 0.0,
            "expected_promotion_lift_pct": round(lift * 100, 2) if has_promo else 0.0,
            "sponsor_category": sponsor,
            "sponsor_value_estimate": round(sponsor_val, 2) if has_promo else 0.0,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

def generate_attendance(
    games: pd.DataFrame,
    teams: pd.DataFrame,
    promotions: pd.DataFrame,
    weather: pd.DataFrame,
) -> pd.DataFrame:
    team_cap = dict(zip(teams["team_id"], teams["arena_capacity"]))
    team_pop = dict(zip(teams["team_abbr"], teams["historical_popularity_score"]))

    promo_lift = promotions.set_index("game_id")["expected_promotion_lift_pct"] / 100.0
    promo_flag = promotions.set_index("game_id")["promotion_flag"]
    wx = weather.set_index("game_id")

    records = []
    for _, row in games.iterrows():
        gid = row["game_id"]
        cap = team_cap[row["home_team_id"]]
        home_pop = team_pop.get(row["home_team_abbr"], 0.7)
        away_pop = team_pop.get(row["away_team_abbr"], 0.7)

        base = 0.72
        base += 0.08 * home_pop
        base += 0.06 * away_pop
        base += 0.04 * row["home_team_win_pct_entering_game"]
        base += 0.03 * row["away_team_win_pct_entering_game"]
        if row["is_weekend"]:
            base += 0.05
        if row["rivalry_flag"]:
            base += 0.07
        if row["nationally_televised_flag"]:
            base += 0.04
        if row["is_holiday_period"]:
            base += 0.03
        if promo_flag.get(gid, False):
            base += promo_lift.get(gid, 0.0)

        w = wx.loc[gid] if gid in wx.index else None
        if w is not None:
            if w["severe_weather_flag"]:
                base -= 0.08
            elif w["snow_flag"]:
                base -= 0.04
            elif w["precipitation_flag"]:
                base -= 0.02

        base = np.clip(base, 0.55, 1.02)
        noise = rng.normal(0, 0.04)
        pct = float(np.clip(base + noise, 0.50, 1.0))

        actual = int(cap * pct)
        actual = min(actual, cap)
        expected_base = int(cap * np.clip(base, 0.55, 1.0))
        variance = actual - expected_base

        if pct >= 0.95:
            tier = "Sellout"
        elif pct >= 0.88:
            tier = "High"
        elif pct >= 0.75:
            tier = "Medium"
        else:
            tier = "Low"

        records.append({
            "game_id": gid,
            "arena_capacity": cap,
            "actual_attendance": actual,
            "capacity_pct": round(pct * 100, 2),
            "expected_attendance_baseline": expected_base,
            "attendance_variance": variance,
            "attendance_tier": tier,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Ticket Segments
# ---------------------------------------------------------------------------

def generate_ticket_segments() -> pd.DataFrame:
    return pd.DataFrame(TICKET_SEGMENTS)


# ---------------------------------------------------------------------------
# Ticket Sales
# ---------------------------------------------------------------------------

def generate_ticket_sales(
    games: pd.DataFrame,
    attendance: pd.DataFrame,
    promotions: pd.DataFrame,
) -> pd.DataFrame:
    att_map = attendance.set_index("game_id")
    promo_map = promotions.set_index("game_id")

    seg_alloc = {
        1: 0.03,   # Premium Courtside
        2: 0.14,   # Lower Bowl
        3: 0.08,   # Club Level
        4: 0.30,   # Upper Bowl
        5: 0.12,   # Family Pack
        6: 0.08,   # Student Promo
        7: 0.10,   # Group Sales
        8: 0.10,   # Season Ticket
        9: 0.05,   # Corporate Partner
    }

    records = []
    sale_id = 1
    for _, grow in games.iterrows():
        gid = grow["game_id"]
        att_row = att_map.loc[gid]
        actual_att = att_row["actual_attendance"]
        cap = att_row["arena_capacity"]
        cap_pct = att_row["capacity_pct"] / 100.0

        promo_row = promo_map.loc[gid] if gid in promo_map.index else None
        promo_type = promo_row["promotion_type"] if promo_row is not None else "None"

        for seg in TICKET_SEGMENTS:
            sid = seg["segment_id"]
            base_price = seg["avg_base_price"]
            alloc_frac = seg_alloc[sid]

            avail = int(cap * alloc_frac)
            avail = max(avail, 1)

            # Demand driven by attendance
            sell_through = np.clip(cap_pct * 1.05 + rng.uniform(-0.08, 0.08), 0.30, 1.0)

            # Segment-specific adjustments
            if sid == 6:  # Student
                discount = 0.30 + rng.uniform(0, 0.10)
                if promo_type == "Student Discount":
                    discount += 0.10
                    sell_through = min(sell_through + 0.12, 1.0)
            elif sid in (1, 3, 9):  # Premium
                discount = rng.uniform(0.0, 0.05)
                sell_through = np.clip(sell_through * 1.05, 0.0, 1.0)
            elif sid == 5:  # Family
                discount = 0.15 + rng.uniform(0, 0.05)
                if promo_type == "Family Night":
                    discount += 0.05
                    sell_through = min(sell_through + 0.08, 1.0)
            else:
                discount = rng.uniform(0.0, 0.12)

            # High-demand games push prices up
            price_mult = 1.0 + 0.25 * (cap_pct - 0.75)
            avg_price = round(base_price * price_mult * (1 - discount * 0.5), 2)
            avg_price = max(avg_price, 5.0)

            sold = int(avail * sell_through)
            sold = min(sold, actual_att)  # can't sell more than attendees
            gross = round(sold * avg_price, 2)
            net = round(gross * (1 - discount * 0.3), 2)

            records.append({
                "ticket_sale_id": sale_id,
                "game_id": gid,
                "segment_id": sid,
                "segment_name": seg["segment_name"],
                "tickets_available": avail,
                "tickets_sold": sold,
                "avg_ticket_price": avg_price,
                "discount_pct": round(discount * 100, 2),
                "gross_ticket_revenue": gross,
                "net_ticket_revenue": net,
                "sell_through_rate": round(sell_through * 100, 2),
            })
            sale_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Concessions
# ---------------------------------------------------------------------------

_CONCESSION_BASE_PER_CAP = {
    "Food": 9.50,
    "Beverage": 8.00,
    "Snacks": 4.50,
    "Combo Meals": 14.00,
    "Premium Dining": 22.00,
}
_CONCESSION_COST_PCT = {
    "Food": 0.38,
    "Beverage": 0.22,
    "Snacks": 0.30,
    "Combo Meals": 0.35,
    "Premium Dining": 0.40,
}
_CONCESSION_UNIT_PRICE = {
    "Food": 12.0,
    "Beverage": 9.0,
    "Snacks": 6.0,
    "Combo Meals": 18.0,
    "Premium Dining": 35.0,
}


def generate_concessions(
    games: pd.DataFrame,
    attendance: pd.DataFrame,
    promotions: pd.DataFrame,
) -> pd.DataFrame:
    att_map = attendance.set_index("game_id")
    promo_map = promotions.set_index("game_id")

    records = []
    con_id = 1
    for _, grow in games.iterrows():
        gid = grow["game_id"]
        att = att_map.loc[gid]["actual_attendance"]
        cap = att_map.loc[gid]["arena_capacity"]
        cap_pct = att_map.loc[gid]["capacity_pct"] / 100.0
        tier = att_map.loc[gid]["attendance_tier"]
        promo_row = promo_map.loc[gid] if gid in promo_map.index else None
        promo_type = promo_row["promotion_type"] if promo_row is not None else "None"

        for cat in CONCESSION_CATEGORIES:
            base_spend = _CONCESSION_BASE_PER_CAP[cat]
            unit_price = _CONCESSION_UNIT_PRICE[cat]
            cost_pct = _CONCESSION_COST_PCT[cat]

            # Demand modifier
            demand_mult = 0.85 + cap_pct * 0.30
            if grow["is_weekend"]:
                demand_mult += 0.05
            if promo_type == "Food Voucher":
                demand_mult += 0.12 if cat in ("Food", "Beverage", "Combo Meals") else 0.04
            if promo_type == "Family Night" and cat in ("Snacks", "Combo Meals"):
                demand_mult += 0.08
            demand_mult += rng.uniform(-0.07, 0.07)

            per_cap = base_spend * demand_mult
            gross = round(per_cap * att, 2)
            units = max(1, int(gross / unit_price))
            cost = round(gross * cost_pct, 2)
            margin = round(gross - cost, 2)

            # Inventory recommendation with buffer
            if tier == "Sellout":
                buffer = 1.20
            elif tier == "High":
                buffer = 1.15
            elif tier == "Medium":
                buffer = 1.10
            else:
                buffer = 1.05
            rec_inventory = int(units * buffer)

            records.append({
                "concession_id": con_id,
                "game_id": gid,
                "category": cat,
                "units_sold": units,
                "avg_unit_price": unit_price,
                "gross_revenue": gross,
                "estimated_cost": cost,
                "gross_margin": margin,
                "per_cap_spend": round(per_cap, 2),
                "recommended_inventory_units": rec_inventory,
            })
            con_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Merchandise
# ---------------------------------------------------------------------------

_MERCH_BASE_PER_CAP = {
    "Jerseys": 6.50,
    "Hats": 4.80,
    "T-Shirts": 5.20,
    "Collectibles": 3.10,
    "Game-Day Specials": 2.80,
}
_MERCH_COST_PCT = {
    "Jerseys": 0.42,
    "Hats": 0.35,
    "T-Shirts": 0.32,
    "Collectibles": 0.38,
    "Game-Day Specials": 0.30,
}
_MERCH_UNIT_PRICE = {
    "Jerseys": 110.0,
    "Hats": 32.0,
    "T-Shirts": 28.0,
    "Collectibles": 45.0,
    "Game-Day Specials": 20.0,
}


def generate_merchandise(
    games: pd.DataFrame,
    attendance: pd.DataFrame,
    promotions: pd.DataFrame,
    teams: pd.DataFrame,
) -> pd.DataFrame:
    att_map = attendance.set_index("game_id")
    promo_map = promotions.set_index("game_id")
    away_pop = dict(zip(
        games["game_id"],
        games["away_team_abbr"].map(
            dict(zip(teams["team_abbr"], teams["historical_popularity_score"]))
        )
    ))

    records = []
    merch_id = 1
    for _, grow in games.iterrows():
        gid = grow["game_id"]
        att = att_map.loc[gid]["actual_attendance"]
        tier = att_map.loc[gid]["attendance_tier"]
        cap_pct = att_map.loc[gid]["capacity_pct"] / 100.0
        promo_row = promo_map.loc[gid] if gid in promo_map.index else None
        promo_type = promo_row["promotion_type"] if promo_row is not None else "None"
        opp_pop = away_pop.get(gid, 0.7)

        for cat in MERCHANDISE_CATEGORIES:
            base_spend = _MERCH_BASE_PER_CAP[cat]
            unit_price = _MERCH_UNIT_PRICE[cat]
            cost_pct = _MERCH_COST_PCT[cat]

            demand_mult = 0.80 + cap_pct * 0.35
            if grow["rivalry_flag"]:
                demand_mult += 0.15
            demand_mult += 0.10 * opp_pop
            if grow["home_team_win_pct_entering_game"] > 0.55:
                demand_mult += 0.05
            if promo_type == "Merchandise Giveaway":
                demand_mult += 0.12 if cat in ("T-Shirts", "Hats", "Game-Day Specials") else 0.06
            demand_mult += rng.uniform(-0.07, 0.07)

            per_cap = base_spend * demand_mult
            gross = round(per_cap * att, 2)
            units = max(1, int(gross / unit_price))
            cost = round(gross * cost_pct, 2)
            margin = round(gross - cost, 2)

            if tier == "Sellout":
                buffer = 1.20
            elif tier == "High":
                buffer = 1.15
            elif tier == "Medium":
                buffer = 1.10
            else:
                buffer = 1.05
            rec_inventory = int(units * buffer)

            records.append({
                "merchandise_id": merch_id,
                "game_id": gid,
                "category": cat,
                "units_sold": units,
                "avg_unit_price": unit_price,
                "gross_revenue": gross,
                "estimated_cost": cost,
                "gross_margin": margin,
                "per_cap_spend": round(per_cap, 2),
                "recommended_inventory_units": rec_inventory,
            })
            merch_id += 1

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Fan Profiles
# ---------------------------------------------------------------------------

def generate_fan_profiles() -> pd.DataFrame:
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    household_types = ["Single", "Couple", "Family with Kids", "Empty Nester", "Student", "Corporate"]
    distance_buckets = ["<5 miles", "5-15 miles", "15-30 miles", "30-60 miles", "60+ miles"]
    preferred_segs = [s["segment_name"] for s in TICKET_SEGMENTS]

    n = NUM_FAN_PROFILES
    loyalty = rng.choice(LOYALTY_STATUSES, size=n,
                         p=[0.10, 0.30, 0.25, 0.15, 0.12, 0.08])

    loyalty_games_map = {
        "New Fan": (1, 4), "Casual Fan": (2, 8), "Repeat Buyer": (5, 15),
        "Season Ticket Holder": (35, 41), "Premium Member": (20, 41),
        "Corporate Guest": (3, 12)
    }
    loyalty_ticket_map = {
        "New Fan": (40, 90), "Casual Fan": (55, 120), "Repeat Buyer": (75, 180),
        "Season Ticket Holder": (130, 280), "Premium Member": (200, 450),
        "Corporate Guest": (150, 380)
    }

    records = []
    for fan_id in range(1, n + 1):
        lst = loyalty[fan_id - 1]
        lo_g, hi_g = loyalty_games_map[lst]
        games_attended = int(rng.integers(lo_g, hi_g + 1))

        lo_t, hi_t = loyalty_ticket_map[lst]
        avg_ticket = round(float(rng.uniform(lo_t, hi_t)), 2)
        avg_concession = round(float(rng.uniform(8, 45)), 2)
        avg_merch = round(float(rng.uniform(5, 80)), 2)

        promo_usage = float(np.clip(rng.beta(2, 5) + rng.uniform(0, 0.1), 0, 1))
        email_eng = float(np.clip(rng.beta(3, 3), 0, 1))

        fan_value = (
            0.35 * (avg_ticket / 450.0)
            + 0.20 * (games_attended / 41.0)
            + 0.15 * (avg_merch / 80.0)
            + 0.15 * (avg_concession / 45.0)
            + 0.10 * email_eng
            + 0.05 * (1 - promo_usage)
        )

        age_weights = {
            "18-24": 0.14, "25-34": 0.22, "35-44": 0.24,
            "45-54": 0.20, "55-64": 0.13, "65+": 0.07
        }
        records.append({
            "fan_id": fan_id,
            "age_group": rng.choice(list(age_weights.keys()),
                                    p=list(age_weights.values())),
            "household_type": rng.choice(household_types),
            "distance_from_arena_bucket": rng.choice(
                distance_buckets, p=[0.18, 0.28, 0.25, 0.18, 0.11]
            ),
            "preferred_ticket_segment": rng.choice(preferred_segs),
            "loyalty_status": lst,
            "games_attended_last_12_months": games_attended,
            "avg_ticket_spend": avg_ticket,
            "avg_concession_spend": avg_concession,
            "avg_merchandise_spend": avg_merch,
            "promotion_usage_rate": round(promo_usage, 4),
            "email_engagement_score": round(email_eng, 4),
            "fan_value_score": round(fan_value, 4),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Fan Transactions
# ---------------------------------------------------------------------------

def generate_fan_transactions(
    fan_profiles: pd.DataFrame,
    games: pd.DataFrame,
    attendance: pd.DataFrame,
    promotions: pd.DataFrame,
) -> pd.DataFrame:
    game_ids = games["game_id"].tolist()
    game_dates = dict(zip(games["game_id"], games["game_date"]))
    att_map = attendance.set_index("game_id")["actual_attendance"]
    promo_map = promotions.set_index("game_id")["promotion_flag"]

    n = NUM_FAN_TRANSACTIONS
    records = []

    # Sample games proportional to attendance
    att_vals = np.array([att_map[g] for g in game_ids], dtype=float)
    att_probs = att_vals / att_vals.sum()
    selected_games = rng.choice(game_ids, size=n, p=att_probs)

    fan_ids = rng.integers(1, NUM_FAN_PROFILES + 1, size=n)
    fan_lookup = fan_profiles.set_index("fan_id")

    for txn_id, (gid, fid) in enumerate(zip(selected_games, fan_ids), start=1):
        fan = fan_lookup.loc[fid]
        used_promo = bool(
            promo_map.get(gid, False) and rng.random() < fan["promotion_usage_rate"]
        )
        ticket_spend = round(
            fan["avg_ticket_spend"] * rng.uniform(0.7, 1.4), 2
        )
        concession_spend = round(
            fan["avg_concession_spend"] * rng.uniform(0.5, 2.0), 2
        )
        merch_spend = round(
            fan["avg_merchandise_spend"] * rng.uniform(0.0, 2.5), 2
        )
        if used_promo:
            ticket_spend = round(ticket_spend * 0.88, 2)
            concession_spend = round(concession_spend * 1.15, 2)

        total = round(ticket_spend + concession_spend + merch_spend, 2)
        records.append({
            "transaction_id": txn_id,
            "fan_id": int(fid),
            "game_id": int(gid),
            "ticket_spend": max(ticket_spend, 0.0),
            "concession_spend": max(concession_spend, 0.0),
            "merchandise_spend": max(merch_spend, 0.0),
            "used_promotion": used_promo,
            "total_spend": max(total, 0.0),
            "transaction_date": game_dates[gid],
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Model prediction shell (filled after training)
# ---------------------------------------------------------------------------

def generate_model_prediction_shell(games: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in games.iterrows():
        records.append({
            "game_id": row["game_id"],
            "predicted_attendance": None,
            "predicted_ticket_revenue": None,
            "predicted_concessions_revenue": None,
            "predicted_merchandise_revenue": None,
            "predicted_total_revenue": None,
            "actual_total_revenue": None,
            "attendance_prediction_error": None,
            "revenue_prediction_error": None,
            "model_run_date": None,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating teams...")
    teams = generate_teams()
    teams.to_csv(DATA_SIMULATED_DIR / "teams.csv", index=False)
    print(f"  teams.csv: {len(teams)} rows")

    print("Generating games...")
    games = generate_games(teams)
    games.to_csv(DATA_SIMULATED_DIR / "games.csv", index=False)
    print(f"  games.csv: {len(games)} rows")

    print("Generating weather...")
    weather = generate_weather(games)
    weather.to_csv(DATA_SIMULATED_DIR / "weather.csv", index=False)
    print(f"  weather.csv: {len(weather)} rows")

    print("Generating promotions...")
    promotions = generate_promotions(games)
    promotions.to_csv(DATA_SIMULATED_DIR / "promotions.csv", index=False)
    print(f"  promotions.csv: {len(promotions)} rows")

    print("Generating attendance...")
    attendance = generate_attendance(games, teams, promotions, weather)
    attendance.to_csv(DATA_SIMULATED_DIR / "attendance.csv", index=False)
    print(f"  attendance.csv: {len(attendance)} rows")

    print("Generating ticket segments...")
    ticket_segments = generate_ticket_segments()
    ticket_segments.to_csv(DATA_SIMULATED_DIR / "ticket_segments.csv", index=False)
    print(f"  ticket_segments.csv: {len(ticket_segments)} rows")

    print("Generating ticket sales...")
    ticket_sales = generate_ticket_sales(games, attendance, promotions)
    ticket_sales.to_csv(DATA_SIMULATED_DIR / "ticket_sales.csv", index=False)
    print(f"  ticket_sales.csv: {len(ticket_sales)} rows")

    print("Generating concessions...")
    concessions = generate_concessions(games, attendance, promotions)
    concessions.to_csv(DATA_SIMULATED_DIR / "concessions.csv", index=False)
    print(f"  concessions.csv: {len(concessions)} rows")

    print("Generating merchandise...")
    merchandise = generate_merchandise(games, attendance, promotions, teams)
    merchandise.to_csv(DATA_SIMULATED_DIR / "merchandise.csv", index=False)
    print(f"  merchandise.csv: {len(merchandise)} rows")

    print("Generating fan profiles...")
    fan_profiles = generate_fan_profiles()
    fan_profiles.to_csv(DATA_SIMULATED_DIR / "fan_profiles.csv", index=False)
    print(f"  fan_profiles.csv: {len(fan_profiles)} rows")

    print("Generating fan transactions...")
    fan_transactions = generate_fan_transactions(fan_profiles, games, attendance, promotions)
    fan_transactions.to_csv(DATA_SIMULATED_DIR / "fan_transactions.csv", index=False)
    print(f"  fan_transactions.csv: {len(fan_transactions)} rows")

    print("Generating model prediction shell...")
    model_preds = generate_model_prediction_shell(games)
    model_preds.to_csv(DATA_SIMULATED_DIR / "model_predictions.csv", index=False)
    print(f"  model_predictions.csv: {len(model_preds)} rows")

    print("\nData generation complete.")
    print(f"All files saved to: {DATA_SIMULATED_DIR}")


if __name__ == "__main__":
    main()
