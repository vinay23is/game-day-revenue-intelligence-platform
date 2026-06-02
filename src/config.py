import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_SIMULATED_DIR = BASE_DIR / "data" / "simulated"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
SQL_DIR = BASE_DIR / "sql"

for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SIMULATED_DIR, MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/gameday_revenue"
)

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "gameday_revenue"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

NUM_TEAMS = 30
NUM_SEASONS = 5
SEASONS = [2019, 2020, 2021, 2022, 2023]
NUM_FAN_PROFILES = 12000
NUM_FAN_TRANSACTIONS = 120000

TICKET_SEGMENTS = [
    {"segment_id": 1, "segment_name": "Premium Courtside", "avg_base_price": 450.0, "price_tier": "Ultra Premium"},
    {"segment_id": 2, "segment_name": "Lower Bowl", "avg_base_price": 185.0, "price_tier": "Premium"},
    {"segment_id": 3, "segment_name": "Club Level", "avg_base_price": 220.0, "price_tier": "Premium"},
    {"segment_id": 4, "segment_name": "Upper Bowl", "avg_base_price": 65.0, "price_tier": "Value"},
    {"segment_id": 5, "segment_name": "Family Pack", "avg_base_price": 55.0, "price_tier": "Value"},
    {"segment_id": 6, "segment_name": "Student Promo", "avg_base_price": 30.0, "price_tier": "Discount"},
    {"segment_id": 7, "segment_name": "Group Sales", "avg_base_price": 72.0, "price_tier": "Mid-Tier"},
    {"segment_id": 8, "segment_name": "Season Ticket", "avg_base_price": 140.0, "price_tier": "Mid-Tier"},
    {"segment_id": 9, "segment_name": "Corporate Partner Allocation", "avg_base_price": 310.0, "price_tier": "Premium"},
]

PROMOTION_TYPES = [
    "None", "Family Night", "Student Discount", "Merchandise Giveaway",
    "Food Voucher", "Theme Night", "Corporate Partner Night",
    "Community Night", "Premium Experience"
]

CONCESSION_CATEGORIES = ["Food", "Beverage", "Snacks", "Combo Meals", "Premium Dining"]
MERCHANDISE_CATEGORIES = ["Jerseys", "Hats", "T-Shirts", "Collectibles", "Game-Day Specials"]

LOYALTY_STATUSES = [
    "New Fan", "Casual Fan", "Repeat Buyer",
    "Season Ticket Holder", "Premium Member", "Corporate Guest"
]
