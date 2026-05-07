"""Stage-1 LLM extraction chain.

Takes a free-text user query, calls the OpenAI chat completions API
with one of the Stage-1 prompts, parses the returned JSON, and
validates it into an :class:`ExtractedFeatures` instance.

Safety invariants
-----------------
1. **Never crash the pipeline.** The LLM may return malformed JSON or
   out-of-range values, or the OpenAI API itself may fail. All three
   failure modes are caught specifically (``JSONDecodeError``,
   ``ValidationError``, ``openai.APIError``) and collapsed into a safe
   fallback: an empty :class:`ExtractedFeatures` whose fields are all
   ``None``. The predictor will fill those with training-set defaults.

2. **JSON mode on.** We pass ``response_format={"type": "json_object"}``
   so the model is forced to return parseable JSON. ``temperature=0``
   makes the extraction deterministic across runs (important for
   prompt comparison in Step 9).

3. **Client cached.** ``get_client`` is wrapped in ``lru_cache`` so the
   HTTP client — and its API key — is constructed exactly once per
   process.
"""

from __future__ import annotations

import json
from functools import lru_cache

import openai
from openai import OpenAI
from pydantic import ValidationError

from app.config import get_settings
from app.prompts.extraction import build_messages
from app.schemas.features import ExtractedFeatures
from app.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Return a cached OpenAI client built from settings.

    The key is read via :func:`app.config.get_settings`, which itself
    caches a :class:`Settings` instance — so the API key is loaded
    from the environment exactly once per process.
    """
    settings = get_settings()
    kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def extract_features(
    query: str,
    prompt_version: str = "v2",
) -> ExtractedFeatures:
    """Extract structured features from a natural-language query.

    Args:
        query: Raw user query, e.g. "3 bed ranch in OldTown, 2-car garage".
        prompt_version: Which Stage-1 prompt to use (``"v1"`` or ``"v2"``).
            Defaults to the few-shot variant.

    Returns:
        A validated :class:`ExtractedFeatures`. On any LLM, parsing, or
        validation failure, returns an empty instance (all fields
        ``None``) rather than raising. The caller can inspect
        ``result.missing_fields()`` to see what the LLM did not provide.
    """
    if not query or not query.strip():
        logger.warning("extract_features called with empty query")
        return ExtractedFeatures()

    client = get_client()
    settings = get_settings()
    messages = build_messages(query=query, version=prompt_version)

    try:
        response = client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
    except openai.APIError as exc:
        logger.error("OpenAI API error during extraction: %s", exc)
        return ExtractedFeatures()

    raw_content = response.choices[0].message.content or ""
    logger.debug("Stage-1 raw LLM output: %s", raw_content)

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        logger.error("Stage-1 returned non-JSON content: %s", exc)
        return ExtractedFeatures()

    try:
        features = ExtractedFeatures.model_validate(parsed)
    except ValidationError as exc:
        logger.error("Stage-1 JSON failed schema validation: %s", exc)
        return ExtractedFeatures()

    logger.info(
        "Stage-1 extraction ok (prompt=%s, missing=%d fields)",
        prompt_version,
        len(features.missing_fields()),
    )
    return features
