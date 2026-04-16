"""Pydantic schema for features extracted from a free-text query.

The Stage-1 LLM reads a sentence like *"3 bed ranch in OldTown, 2-car
garage, built 1960"* and is asked to return a JSON object matching
this schema. The result is validated and then handed to the sklearn
pipeline for prediction.

Design choices
--------------
* **Every field is ``Optional``.** A short user query may mention only
  two or three attributes; the LLM must not hallucinate the rest. Any
  field left as ``None`` is filled in downstream by the predictor
  using training-set medians/modes.
* **Python snake_case + dataset alias.** Field names follow PEP 8, but
  each field carries an ``alias`` equal to the exact column name used
  during training (``GrLivArea``, ``TotalBsmtSF`` …). Dumping with
  ``by_alias=True`` produces a dict that can be fed straight into
  ``pd.DataFrame([...])`` with no rename step.
* **Range constraints via ``Field``.** ``OverallQual`` and
  ``OverallCond`` are bounded 1–10, counts are non-negative, and
  ``YearBuilt`` is clamped to a sane window. Out-of-range LLM output
  raises ``ValidationError`` and is caught by the Stage-1 chain.
* **``extra="ignore"``.** The LLM occasionally emits stray keys; we
  silently drop them rather than crashing.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExtractedFeatures(BaseModel):
    """Structured features parsed from the user's natural-language query.

    Fields map 1-to-1 onto the 12 columns the sklearn pipeline was
    trained on. ``None`` means *"the LLM did not find this in the
    query"*, not *"this house has zero of it"*.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        str_strip_whitespace=True,
    )

    # --- Numeric features ------------------------------------------------
    gr_liv_area: Optional[float] = Field(
        default=None,
        alias="GrLivArea",
        ge=0,
        description="Above-grade living area in square feet.",
    )
    total_bsmt_sf: Optional[float] = Field(
        default=None,
        alias="TotalBsmtSF",
        ge=0,
        description="Total basement area in square feet.",
    )
    bedroom_abv_gr: Optional[int] = Field(
        default=None,
        alias="BedroomAbvGr",
        ge=0,
        le=20,
        description="Number of above-grade bedrooms.",
    )
    full_bath: Optional[int] = Field(
        default=None,
        alias="FullBath",
        ge=0,
        le=10,
        description="Number of full bathrooms.",
    )
    half_bath: Optional[int] = Field(
        default=None,
        alias="HalfBath",
        ge=0,
        le=10,
        description="Number of half bathrooms.",
    )
    garage_cars: Optional[int] = Field(
        default=None,
        alias="GarageCars",
        ge=0,
        le=10,
        description="Garage capacity measured in cars.",
    )
    year_built: Optional[int] = Field(
        default=None,
        alias="YearBuilt",
        ge=1800,
        le=2030,
        description="Original construction year.",
    )
    fireplaces: Optional[int] = Field(
        default=None,
        alias="Fireplaces",
        ge=0,
        le=10,
        description="Number of fireplaces.",
    )
    overall_qual: Optional[int] = Field(
        default=None,
        alias="OverallQual",
        ge=1,
        le=10,
        description="Overall material and finish quality (1 = poor, 10 = excellent).",
    )
    overall_cond: Optional[int] = Field(
        default=None,
        alias="OverallCond",
        ge=1,
        le=10,
        description="Overall condition rating (1 = poor, 10 = excellent).",
    )

    # --- Categorical features --------------------------------------------
    neighborhood: Optional[str] = Field(
        default=None,
        alias="Neighborhood",
        description="Ames neighborhood code (e.g. 'NAmes', 'OldTown', 'Edwards').",
    )
    house_style: Optional[str] = Field(
        default=None,
        alias="HouseStyle",
        description="Dwelling style (e.g. '1Story', '2Story', 'SLvl').",
    )

    def missing_fields(self) -> list[str]:
        """Return dataset-column names of fields the LLM did not provide.

        The names are the aliases (``GrLivArea`` etc.) so they match
        what the UI and downstream predictor expect.
        """
        dumped = self.model_dump(by_alias=True)
        return [key for key, value in dumped.items() if value is None]

    def present_fields(self) -> list[str]:
        """Return dataset-column names that currently have concrete values."""
        dumped = self.model_dump(by_alias=True)
        return [key for key, value in dumped.items() if value is not None]

    def to_model_input(self) -> dict[str, object]:
        """Serialize with dataset-aligned keys for direct DataFrame use.

        Returns a dict whose keys are the exact training column names,
        so the predictor can call ``pd.DataFrame([features.to_model_input()])``
        without any column renaming.
        """
        return self.model_dump(by_alias=True)
