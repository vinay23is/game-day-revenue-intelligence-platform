"""
Database utilities: SQLAlchemy connection, CSV loading, fallback to CSV reads.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import DATABASE_URL, DATA_SIMULATED_DIR, DATA_PROCESSED_DIR


def get_engine(url: str = DATABASE_URL):
    return create_engine(url, pool_pre_ping=True)


def test_connection(url: str = DATABASE_URL) -> bool:
    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def load_csv_to_postgres(table_name: str, csv_path: Path, engine, if_exists: str = "replace"):
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"  Loaded {len(df)} rows into {table_name}")


def load_all_csvs_to_postgres(engine):
    tables = [
        ("teams", DATA_SIMULATED_DIR / "teams.csv"),
        ("games", DATA_SIMULATED_DIR / "games.csv"),
        ("weather", DATA_SIMULATED_DIR / "weather.csv"),
        ("promotions", DATA_SIMULATED_DIR / "promotions.csv"),
        ("attendance", DATA_SIMULATED_DIR / "attendance.csv"),
        ("ticket_segments", DATA_SIMULATED_DIR / "ticket_segments.csv"),
        ("ticket_sales", DATA_SIMULATED_DIR / "ticket_sales.csv"),
        ("concessions", DATA_SIMULATED_DIR / "concessions.csv"),
        ("merchandise", DATA_SIMULATED_DIR / "merchandise.csv"),
        ("fan_profiles", DATA_SIMULATED_DIR / "fan_profiles.csv"),
        ("fan_transactions", DATA_SIMULATED_DIR / "fan_transactions.csv"),
        ("model_predictions", DATA_SIMULATED_DIR / "model_predictions.csv"),
    ]
    for table_name, csv_path in tables:
        if csv_path.exists():
            load_csv_to_postgres(table_name, csv_path, engine)
        else:
            print(f"  WARNING: {csv_path} not found, skipping.")


def read_table(table_name: str, engine=None) -> pd.DataFrame:
    """Read a table from PostgreSQL if available, else fall back to CSV."""
    if engine is not None:
        try:
            return pd.read_sql_table(table_name, engine)
        except Exception:
            pass

    # CSV fallback — try simulated first, then processed
    for folder in [DATA_SIMULATED_DIR, DATA_PROCESSED_DIR]:
        path = folder / f"{table_name}.csv"
        if path.exists():
            return pd.read_csv(path)

    raise FileNotFoundError(
        f"Table '{table_name}' not found in PostgreSQL or CSV directories."
    )


def query(sql: str, engine=None) -> pd.DataFrame:
    if engine is None:
        raise ValueError("A SQLAlchemy engine is required for raw SQL queries.")
    return pd.read_sql(sql, engine)
