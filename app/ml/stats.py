"""Training-set descriptive statistics for grounding LLM explanations.

These stats are computed from the **training split only** and saved to
``models/training_stats.json``. They are later loaded at inference time
and handed to the Stage-2 LLM so it can frame a raw price prediction in
market context ("above the median", "typical for Edwards", etc.).

Leakage invariant
-----------------
This module never touches the validation or test splits. It reuses
``load_and_split_data`` from :mod:`app.ml.pipeline` and discards
everything except ``x_train`` and ``y_train``. Any stat computed here
must be derivable from training data alone.

Run standalone from the project root::

    python -m app.ml.stats
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.ml.pipeline import load_and_split_data
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_STATS_PATH = Path("models/training_stats.json")


def compute_training_stats(
    x_train: pd.DataFrame,
    y_train: pd.Series,
) -> dict[str, object]:
    """Compute descriptive stats from the training split.

    Args:
        x_train: Training features. Must contain ``Neighborhood`` and
            ``GrLivArea`` columns.
        y_train: Training target (sale price).

    Returns:
        Dict with price summary, per-neighborhood average price, and
        average living area. All values are plain Python floats / ints
        so the dict is JSON-serializable.
    """
    price_summary = {
        "median": float(y_train.median()),
        "min": float(y_train.min()),
        "max": float(y_train.max()),
        "q1": float(y_train.quantile(0.25)),
        "q3": float(y_train.quantile(0.75)),
    }

    # Join target onto features so we can group prices by neighborhood
    # without mutating the caller's frames.
    joined = x_train.assign(_price=y_train.values)
    avg_price_by_neighborhood = (
        joined.groupby("Neighborhood")["_price"].mean().round(2).to_dict()
    )
    avg_price_by_neighborhood = {
        name: float(price) for name, price in avg_price_by_neighborhood.items()
    }

    avg_sqft = float(x_train["GrLivArea"].mean())

    return {
        "n_train_rows": int(len(x_train)),
        "price": price_summary,
        "avg_price_by_neighborhood": avg_price_by_neighborhood,
        "avg_sqft": avg_sqft,
    }


def save_stats(stats: dict[str, object], path: Path = DEFAULT_STATS_PATH) -> None:
    """Serialize stats to a JSON file, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, sort_keys=True)
    logger.info("Saved training stats to %s", path)


def load_stats(path: Path = DEFAULT_STATS_PATH) -> dict[str, object]:
    """Load previously saved training stats from disk.

    Raises:
        FileNotFoundError: If ``path`` does not exist. Run this module
            as a script first to generate it.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"No stats file at {path}. Run `python -m app.ml.stats` first."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_stats(stats_output_path: Path = DEFAULT_STATS_PATH) -> dict[str, object]:
    """End-to-end: load split, compute stats on train only, save."""
    x_train, _x_val, _x_test, y_train, _y_val, _y_test = load_and_split_data()
    logger.info("Computing stats from %d training rows", len(x_train))
    stats = compute_training_stats(x_train, y_train)
    save_stats(stats, stats_output_path)
    return stats


if __name__ == "__main__":
    summary = run_stats()
    logger.info("Training stats summary: %s", summary)
