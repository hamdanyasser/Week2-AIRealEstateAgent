"""Stage-2 LLM interpretation chain.

Turns the sklearn model's raw point estimate into a plain-English
explanation grounded in the training-set statistics from Step 4.

Safety invariants
-----------------
1. **Never crash the request.** On any OpenAI error or empty response,
   :func:`interpret_prediction` falls back to a deterministic string
   built from the training stats alone (e.g. *"The model predicts
   $185,000, which is above the training-set median of $160,000."*).
2. **Stats loaded at most once.** We delegate to
   :func:`app.ml.stats.load_stats`, which reads the JSON file from
   disk. Callers can also pass a pre-loaded dict (FastAPI will do this
   in its ``lifespan`` so the file is read exactly once at startup).
3. **Shared OpenAI client.** We reuse :func:`app.chain.stage1.get_client`
   so the whole process has one HTTP client, one API key read.
"""

from __future__ import annotations

from typing import Any

import openai

from app.chain.stage1 import get_client
from app.config import get_settings
from app.ml.stats import load_stats
from app.prompts.interpretation import build_messages
from app.schemas.features import ExtractedFeatures
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _fallback_interpretation(
    predicted_price: float,
    stats: dict[str, Any],
) -> str:
    """Deterministic fallback when the LLM call cannot be made.

    Uses only the training stats to frame the price. Intentionally
    short and unambiguous — it has to be a complete sentence the UI
    can display without apology.
    """
    price_summary = stats.get("price", {}) if isinstance(stats, dict) else {}
    median = price_summary.get("median")
    if median is None:
        return f"The model predicts ${predicted_price:,.0f}."

    if predicted_price > median:
        relation = "above"
    elif predicted_price < median:
        relation = "below"
    else:
        relation = "at"
    return (
        f"The model predicts ${predicted_price:,.0f}, "
        f"{relation} the training-set median of ${median:,.0f}."
    )


def interpret_prediction(
    query: str,
    features: ExtractedFeatures,
    predicted_price: float,
    stats: dict[str, Any] | None = None,
) -> str:
    """Produce a plain-English explanation of a price prediction.

    Args:
        query: Original free-text user query.
        features: The validated Stage-1 output, carrying both the
            feature values and the list of missing fields.
        predicted_price: Point estimate from :func:`predict_price`.
        stats: Optional pre-loaded training-stats dict. If ``None``,
            the stats are loaded from ``models/training_stats.json``.

    Returns:
        A short plain-English paragraph describing the prediction.
        Falls back to a deterministic string on any LLM failure.
    """
    if stats is None:
        try:
            stats = load_stats()
        except FileNotFoundError as exc:
            logger.warning("Training stats not found, using empty dict: %s", exc)
            stats = {}

    missing_fields = features.missing_fields()
    features_dict = features.to_model_input()
    messages = build_messages(
        query=query,
        features=features_dict,
        predicted_price=predicted_price,
        stats=stats,
        missing_count=len(missing_fields),
    )

    settings = get_settings()
    client = get_client()

    try:
        response = client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0,
        )
    except openai.APIError as exc:
        logger.error("OpenAI API error during interpretation: %s", exc)
        return _fallback_interpretation(predicted_price, stats)

    text = (response.choices[0].message.content or "").strip()
    if not text:
        logger.warning("Stage-2 returned empty content; using fallback")
        return _fallback_interpretation(predicted_price, stats)

    logger.info("Stage-2 interpretation ok (%d chars)", len(text))
    return text
