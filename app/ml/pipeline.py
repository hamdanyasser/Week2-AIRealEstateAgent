"""Training pipeline for the Ames Housing price predictor.

This module builds, trains, and serializes a scikit-learn pipeline
consisting of a ``ColumnTransformer`` (numeric + categorical paths) and
a swappable regressor (ridge or random forest).

Leakage invariant
-----------------
``.fit(...)`` is called on the training set **only**. Validation and
test sets are accessed via ``.predict(...)`` (which internally calls
``.transform(...)`` on the preprocessor) and never contribute to any
statistic used by the imputers, scaler, or model. The final test set
is scored exactly once, after the winning model is chosen on the
validation set.

Run end-to-end from the project root::

    python -m app.ml.pipeline
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.utils.logger import get_logger

logger = get_logger(__name__)

RANDOM_STATE = 42

# Numeric features. Ordinals (OverallQual, OverallCond) live here too:
# they are bounded integers 1..10, so standard-scaling preserves their
# monotonic meaning. One-hot encoding them would destroy the ordering.
NUMERIC_FEATURES: list[str] = [
    "GrLivArea",
    "TotalBsmtSF",
    "BedroomAbvGr",
    "FullBath",
    "HalfBath",
    "GarageCars",
    "YearBuilt",
    "Fireplaces",
    "OverallQual",
    "OverallCond",
]

CATEGORICAL_FEATURES: list[str] = [
    "Neighborhood",
    "HouseStyle",
]

SELECTED_FEATURES: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET: str = "SalePrice"

ModelType = Literal["ridge", "random_forest"]

DEFAULT_DATA_PATH = Path("data/train.csv")
DEFAULT_MODEL_PATH = Path("models/model.joblib")


def load_and_split_data(
    data_path: Path = DEFAULT_DATA_PATH,
    features: list[str] | None = None,
    target: str = TARGET,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Load the Ames Housing CSV and produce a 70/15/15 stratified split.

    The split is stratified on quantile bins of the target so that every
    subset contains a similar mix of low-, mid-, and high-priced homes.
    This prevents pathological splits (e.g. a test set of all luxury
    homes) that would make RMSE wildly unstable.

    Args:
        data_path: Path to the Ames Housing CSV. Accepts either the
            Kaggle ``train.csv`` or the original De Cock file; column
            names are normalized by stripping spaces.
        features: Optional override for the feature list. Defaults to
            ``SELECTED_FEATURES``.
        target: Target column name. Defaults to ``"SalePrice"``.
        random_state: Seed for reproducibility.

    Returns:
        Tuple of ``(X_train, X_val, X_test, y_train, y_val, y_test)``.

    Raises:
        FileNotFoundError: If ``data_path`` does not exist.
        ValueError: If any expected feature or target column is missing
            from the loaded file.
    """
    if not data_path.exists():
        raise FileNotFoundError(
            f"No dataset found at {data_path}. Download the Kaggle "
            "'House Prices - Advanced Regression Techniques' train.csv "
            "and save it there."
        )

    feature_list = list(features) if features is not None else SELECTED_FEATURES

    logger.info("Loading data from %s", data_path)
    df = pd.read_csv(data_path)
    df.columns = [c.replace(" ", "") for c in df.columns]

    missing = set(feature_list + [target]) - set(df.columns)
    if missing:
        raise ValueError(
            f"Expected columns missing from {data_path}: {sorted(missing)}"
        )

    x_all = df[feature_list]
    y_all = df[target]

    # Continuous targets cannot be stratified directly. Bin into
    # quintiles and stratify on the bin id instead.
    strat_bins = pd.qcut(y_all, q=5, labels=False, duplicates="drop")

    x_train, x_temp, y_train, y_temp, strat_train, strat_temp = train_test_split(
        x_all,
        y_all,
        strat_bins,
        test_size=0.30,
        random_state=random_state,
        stratify=strat_bins,
    )
    del strat_train  # unused, explicit to document we split on strat_temp next

    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.50,
        random_state=random_state,
        stratify=strat_temp,
    )

    logger.info(
        "Split sizes: train=%d val=%d test=%d (total=%d)",
        len(x_train),
        len(x_val),
        len(x_test),
        len(df),
    )
    return x_train, x_val, x_test, y_train, y_val, y_test


def build_pipeline(
    model_type: ModelType,
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Build an unfitted sklearn Pipeline: preprocessor + regressor.

    The preprocessor is a ``ColumnTransformer`` with two branches:

    * Numeric: ``SimpleImputer(strategy="median")`` then ``StandardScaler``.
    * Categorical: ``SimpleImputer(strategy="most_frequent")`` then
      ``OneHotEncoder(handle_unknown="ignore")`` so unseen neighborhood
      names at inference time do not blow up.

    Args:
        model_type: Either ``"ridge"`` or ``"random_forest"``.
        numeric_features: Numeric column list. Defaults to ``NUMERIC_FEATURES``.
        categorical_features: Categorical column list. Defaults to
            ``CATEGORICAL_FEATURES``.
        random_state: Seed passed to the random forest.

    Returns:
        An unfitted ``sklearn.pipeline.Pipeline``.

    Raises:
        ValueError: If ``model_type`` is not a supported value.
    """
    num_cols = list(numeric_features) if numeric_features is not None else NUMERIC_FEATURES
    cat_cols = (
        list(categorical_features)
        if categorical_features is not None
        else CATEGORICAL_FEATURES
    )

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, num_cols),
            ("cat", categorical_pipe, cat_cols),
        ]
    )

    if model_type == "ridge":
        model = Ridge(alpha=1.0)
    elif model_type == "random_forest":
        model = RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(
            f"Unknown model_type: {model_type!r}. Expected 'ridge' or 'random_forest'."
        )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


def train_and_evaluate(
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_val: pd.DataFrame,
    y_val: pd.Series,
) -> dict[str, float]:
    """Fit the pipeline on training data, score it on validation data.

    This is the **only** function in the module that calls ``.fit()``.
    Validation data is used exclusively for scoring.

    Args:
        pipeline: An unfitted pipeline from ``build_pipeline``.
        x_train: Training features.
        y_train: Training target.
        x_val: Validation features.
        y_val: Validation target.

    Returns:
        Dict with ``"rmse"`` and ``"r2"`` measured on the validation set.
    """
    logger.info("Fitting pipeline on %d training rows", len(x_train))
    pipeline.fit(x_train, y_train)

    val_preds = pipeline.predict(x_val)
    rmse = float(root_mean_squared_error(y_val, val_preds))
    r2 = float(r2_score(y_val, val_preds))

    logger.info("Validation metrics: RMSE=%.2f R2=%.4f", rmse, r2)
    return {"rmse": rmse, "r2": r2}


def final_evaluation(
    pipeline: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """Score the chosen fitted pipeline on the held-out test set.

    Call this **exactly once**, after the winning model has been
    selected on the validation set. Scoring on test repeatedly and
    then tuning based on the result turns the test set into a second
    validation set and leaks information.

    Args:
        pipeline: A fitted pipeline (already trained).
        x_test: Test features.
        y_test: Test target.

    Returns:
        Dict with ``"rmse"`` and ``"r2"`` measured on the test set.
    """
    test_preds = pipeline.predict(x_test)
    rmse = float(root_mean_squared_error(y_test, test_preds))
    r2 = float(r2_score(y_test, test_preds))

    logger.info("TEST metrics (held-out, scored once): RMSE=%.2f R2=%.4f", rmse, r2)
    return {"rmse": rmse, "r2": r2}


def run_training(
    data_path: Path = DEFAULT_DATA_PATH,
    model_output_path: Path = DEFAULT_MODEL_PATH,
    random_state: int = RANDOM_STATE,
) -> dict[str, object]:
    """End-to-end training: split, train candidates, pick winner, save.

    Trains both ridge and random forest on the same training set,
    scores each on the validation set, picks the lower-RMSE model as
    the winner, evaluates the winner once on the test set, and
    serializes the fitted winner pipeline to ``model_output_path``.

    Args:
        data_path: Source CSV path.
        model_output_path: Destination for the serialized winner.
        random_state: Seed for reproducibility.

    Returns:
        Dict with keys ``"val"`` (per-candidate val metrics),
        ``"winner"`` (name + metrics), and ``"test"`` (held-out metrics).
    """
    x_train, x_val, x_test, y_train, y_val, y_test = load_and_split_data(
        data_path=data_path, random_state=random_state
    )

    val_results: dict[str, dict[str, float]] = {}
    fitted: dict[str, Pipeline] = {}

    for model_type in ("ridge", "random_forest"):
        logger.info("=== Training candidate: %s ===", model_type)
        pipe = build_pipeline(model_type=model_type, random_state=random_state)
        val_results[model_type] = train_and_evaluate(
            pipe, x_train, y_train, x_val, y_val
        )
        fitted[model_type] = pipe

    winner_name = min(val_results, key=lambda name: val_results[name]["rmse"])
    winner_pipe = fitted[winner_name]
    logger.info(
        "Winner on validation: %s (RMSE=%.2f)",
        winner_name,
        val_results[winner_name]["rmse"],
    )

    test_metrics = final_evaluation(winner_pipe, x_test, y_test)

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(winner_pipe, model_output_path)
    logger.info("Saved fitted pipeline to %s", model_output_path)

    return {
        "val": val_results,
        "winner": {"name": winner_name, "val_metrics": val_results[winner_name]},
        "test": test_metrics,
    }


if __name__ == "__main__":
    summary = run_training()
    logger.info("Training summary: %s", summary)
