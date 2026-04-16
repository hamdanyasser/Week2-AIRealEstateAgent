"""Stage-2 interpretation prompt.

Takes the structured features, the sklearn model's point estimate,
and the training-set summary statistics produced in Step 4, and asks
the LLM to write a short plain-English explanation grounded in those
stats.

Why ground in training stats?
-----------------------------
Without grounding, the LLM can say things like *"this is a typical
price for a neighborhood like that"* based on its own pretraining
knowledge — which has nothing to do with the actual Ames training
set the model was fitted on. Feeding it the training median, quartiles,
and the neighborhood average forces its commentary to reference the
numbers the model itself actually learned from. This is also why the
stats file lives next to the model (Step 4) — they are a matched pair.

Only one prompt version here (no v1/v2). Step 9's prompt comparison
targets Stage 1 specifically.
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """\
You are a concise real-estate analyst. You will receive:
  - the user's original natural-language query,
  - a dict of structured house features the extractor parsed out of it,
  - a predicted sale price (USD) from a scikit-learn model,
  - summary statistics computed from the TRAINING split of the
    Ames Housing dataset.

Write a plain-English explanation of the prediction in 3 to 5 short
sentences. Follow these rules strictly:
  1. State the predicted price once, in USD with commas (e.g. $185,000).
  2. Compare it to the training median, and to the neighborhood average
     if one is provided. Use words like "above", "below", or "near".
  3. Name one or two features from the extracted dict that plausibly
     drove the result (e.g. quality score, living area, neighborhood,
     year built). Do not invent features that are not in the dict.
  4. If many features were missing, note briefly that the estimate
     leans on training-set defaults for those fields.
  5. Do not use markdown, bullet points, or headings. One short
     paragraph only. Do not quote raw JSON. Do not list every feature.
"""


def build_messages(
    query: str,
    features: dict[str, Any],
    predicted_price: float,
    stats: dict[str, Any],
    missing_count: int,
) -> list[dict[str, str]]:
    """Build the OpenAI ``messages`` list for Stage-2 interpretation.

    Args:
        query: Original free-text user query.
        features: Alias-keyed features dict (from
            ``ExtractedFeatures.to_model_input()``).
        predicted_price: Point estimate from the sklearn pipeline.
        stats: Training-set summary (from ``app.ml.stats.load_stats``).
        missing_count: How many features the LLM left as ``None``.

    Returns:
        A list of ``{"role", "content"}`` dicts ready for
        ``client.chat.completions.create``.
    """
    price_summary = stats.get("price", {}) if isinstance(stats, dict) else {}
    avg_by_nbhd = (
        stats.get("avg_price_by_neighborhood", {}) if isinstance(stats, dict) else {}
    )

    neighborhood = features.get("Neighborhood")
    nbhd_avg = avg_by_nbhd.get(neighborhood) if neighborhood else None

    feature_lines = "\n".join(f"  {key}: {value}" for key, value in features.items())

    stats_lines = [
        f"  Training median price: ${price_summary.get('median', 0):,.0f}",
        f"  Training Q1 / Q3: ${price_summary.get('q1', 0):,.0f} / "
        f"${price_summary.get('q3', 0):,.0f}",
        f"  Average training GrLivArea: {stats.get('avg_sqft', 0):.0f} sqft",
    ]
    if nbhd_avg is not None:
        stats_lines.append(
            f"  Average training price in {neighborhood}: ${nbhd_avg:,.0f}"
        )
    stats_block = "\n".join(stats_lines)

    user_content = (
        f'Original query: "{query}"\n\n'
        f"Predicted price: ${predicted_price:,.0f}\n\n"
        f"Extracted features:\n{feature_lines}\n\n"
        f"Missing features (filled with training defaults): {missing_count}\n\n"
        f"Training statistics:\n{stats_block}\n"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
