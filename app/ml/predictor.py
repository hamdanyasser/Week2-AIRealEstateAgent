"""Inference wrapper around the trained sklearn pipeline.

Responsibilities
----------------
1. Load the serialized pipeline **exactly once** per process
   (:func:`load_model` is ``lru_cache``-wrapped), so no disk I/O
   happens on each ``/predict`` request.
2. Convert an :class:`app.schemas.features.ExtractedFeatures` instance
   into a single-row DataFrame whose columns exactly match the training
   frame (``GrLivArea``, ``Neighborhood``, …). Step 5 set up the Pydantic
   aliases so this is a one-liner.
3. Hand that row to the pipeline. Missing fields (``None``) become
   ``NaN`` in the DataFrame, which the pipeline's own ``SimpleImputer``
   fills with training-set medians / modes. We never impute manually —
   doing so would duplicate logic and invite training/serving skew.

Leakage invariant
-----------------
No inference-time code path computes statistics from user input. Every
median, mode, scaler mean, encoder category comes from the fitted
``ColumnTransformer`` inside the pipeline, which was fitted on the
training split in Step 3. This module is read-only with respect to
the model.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from app.ml.pipeline import (
    CATEGORICAL_FEATURES,
    DEFAULT_MODEL_PATH,
    NUMERIC_FEATURES,
    SELECTED_FEATURES,
)
from app.schemas.features import ExtractedFeatures
from app.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def load_model(path: Path = DEFAULT_MODEL_PATH) -> Pipeline:
    """Load the fitted sklearn pipeline from disk, cached per process.

    Args:
        path: Location of the joblib file produced by
            :func:`app.ml.pipeline.run_training`.

    Returns:
        The fitted :class:`sklearn.pipeline.Pipeline` (preprocessor + model).

    Raises:
        FileNotFoundError: If ``path`` does not exist. Run
            ``python -m app.ml.pipeline`` first to produce it.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"No model at {path}. Run `python -m app.ml.pipeline` first."
        )
    logger.info("Loading sklearn pipeline from %s", path)
    return joblib.load(path)


def features_to_dataframe(features: ExtractedFeatures) -> pd.DataFrame:
    """Convert ``ExtractedFeatures`` into a 1-row DataFrame for the pipeline.

    The returned frame has exactly the 12 training columns in the
    training order. Numeric columns are coerced to a numeric dtype so
    that Python ``None`` becomes ``NaN`` — only ``NaN`` is recognized
    by ``SimpleImputer`` for numeric features.

    Args:
        features: Validated extraction output.

    Returns:
        A 1-row ``pd.DataFrame`` aligned to the training schema.
    """
    row = features.to_model_input()  # alias-keyed dict: {"GrLivArea": ..., ...}
    df = pd.DataFrame([row], columns=SELECTED_FEATURES)

    # Force numeric dtypes. Without this, a numeric column containing
    # only None stays as object dtype, and SimpleImputer(strategy="median")
    # would raise. ``errors="coerce"`` turns any stray non-numeric value
    # (including None) into NaN.
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")

    return df


def predict_price(features: ExtractedFeatures) -> float:
    """Run the trained pipeline on a single extracted-features instance.

    The pipeline's own ``ColumnTransformer`` imputes missing numerics
    with training medians and missing categoricals with training modes,
    one-hot-encodes unknown categories as all-zeros, standard-scales
    numerics, and feeds the result to the winning regressor.

    Args:
        features: Features parsed out of the user query by Stage-1.
            May contain ``None`` for any field the LLM did not extract.

    Returns:
        The predicted sale price in USD as a plain Python float.
    """
    pipeline = load_model()
    df = features_to_dataframe(features)

    logger.debug("Predict input row: %s", df.iloc[0].to_dict())
    raw_prediction = pipeline.predict(df)
    price = float(raw_prediction[0])

    logger.info(
        "Predicted price: %.2f USD (%d missing features filled by imputer)",
        price,
        len(features.missing_fields()),
    )
    return price
