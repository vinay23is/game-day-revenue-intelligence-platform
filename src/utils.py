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


def fmt_currency(value: float) -> str:
    """Compact currency: $1.2B / $345M / $12.3K — fits in a Streamlit metric card."""
    abs_v = abs(value)
    if abs_v >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs_v >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def format_currency(value: float) -> str:
    return fmt_currency(value)


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def truncate(text: str, max_len: int = 18) -> str:
    """Truncate a label to fit a metric card without overflow."""
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def append_to_md(path: Path, content: str):
    with open(path, "a") as f:
        f.write(content + "\n")
