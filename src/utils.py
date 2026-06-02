"""Shared utility helpers."""

import pandas as pd
import numpy as np
from pathlib import Path


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Expected CSV not found: {path}")
    return pd.read_csv(path)


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def append_to_md(path: Path, content: str):
    with open(path, "a") as f:
        f.write(content + "\n")
