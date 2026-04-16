"""Pydantic schemas for Stage-1 review and end-to-end prediction.

The brief requires two schema layers:

1. a Stage-1 extraction payload with completeness metadata so the UI
   can stop and let the user review/fill gaps before prediction, and
2. a final prediction payload bundling the full pipeline output.

The React frontend consumes both contracts.

``PredictionResponse`` bundles together the whole LLM-sandwich
pipeline output:

1. what the user asked,
2. what Stage-1 LLM extracted,
3. which fields were missing (so the UI can prompt the user to fill them),
4. what the sklearn model predicted,
5. how Stage-2 LLM interpreted that price in plain English.

Design choices
--------------
* **``extra="forbid"``** — unlike :class:`ExtractedFeatures` (which is
  lenient because LLM output is untrusted), this is *our* output. Any
  unexpected key is a bug on our side, so we fail loudly.
* **``predicted_price`` is non-negative.** A negative house price would
  signal a broken model or bad features; the validator catches it
  before it reaches the UI.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.features import ExtractedFeatures

TOTAL_MODEL_FEATURES = len(ExtractedFeatures.model_fields)


class ExtractionResponse(BaseModel):
    """Stage-1 output plus completeness metadata for the review step."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        description="Original free-text query the user submitted.",
    )
    prompt_version: str = Field(
        ...,
        min_length=2,
        description="Which extraction prompt version produced this payload.",
    )
    extracted_features: ExtractedFeatures = Field(
        ...,
        description="Validated Stage-1 feature extraction.",
    )
    present_features: list[str] = Field(
        default_factory=list,
        description="Dataset keys Stage 1 extracted with concrete values.",
    )
    missing_features: list[str] = Field(
        default_factory=list,
        description="Dataset keys still missing after Stage 1 extraction.",
    )
    completeness_ratio: float = Field(
        ...,
        ge=0,
        le=1,
        description="Share of the 12 model features already available.",
    )
    is_complete: bool = Field(
        ...,
        description="True when all required model features are present.",
    )

    @classmethod
    def from_features(
        cls,
        query: str,
        prompt_version: str,
        features: ExtractedFeatures,
    ) -> "ExtractionResponse":
        """Build an extraction payload from a validated feature object."""
        present = features.present_fields()
        missing = features.missing_fields()
        return cls(
            query=query,
            prompt_version=prompt_version,
            extracted_features=features,
            present_features=present,
            missing_features=missing,
            completeness_ratio=len(present) / TOTAL_MODEL_FEATURES,
            is_complete=not missing,
        )


class PredictionResponse(BaseModel):
    """Full pipeline output returned by ``POST /predict``."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        description="Original free-text query the user submitted.",
    )
    extracted_features: ExtractedFeatures = Field(
        ...,
        description="Features the Stage-1 LLM parsed from the query.",
    )
    missing_features: list[str] = Field(
        default_factory=list,
        description=(
            "Dataset column names the LLM left as None. Filled with "
            "training-set defaults by the predictor, and surfaced to "
            "the UI so the user can optionally supply them."
        ),
    )
    predicted_price: float = Field(
        ...,
        ge=0,
        description="Point estimate in USD from the sklearn pipeline.",
    )
    interpretation: str = Field(
        ...,
        min_length=1,
        description="Plain-English Stage-2 explanation grounded in training stats.",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Which regressor produced the prediction (e.g. 'random_forest').",
    )
