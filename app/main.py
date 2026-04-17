"""FastAPI backend for the AI Real Estate Agent.

Exposes two user-facing endpoints:

* ``POST /extract`` — Stage 1 only, returning extracted features plus
  completeness metadata so the UI can pause for review.
* ``POST /predict`` — full pipeline, optionally using user-reviewed
  features instead of re-running Stage 1.

Startup / shutdown
------------------
The fitted sklearn pipeline and the training-stats JSON are loaded
**once** in a FastAPI ``lifespan`` context manager and attached to
``app.state``. Every request reads from that shared state — no
per-request disk I/O, no cold starts. The model-name label shown in
the response is also derived once at startup from
``pipeline.named_steps["model"]``, so the handler itself does not
need to touch the pipeline beyond calling ``predict_price``.

Error handling
--------------
Stage 1 and Stage 2 already contain their own safe fallbacks (an
empty :class:`ExtractedFeatures` and a deterministic stats-based
string, respectively), so the endpoint's own ``try / except`` only
needs to catch the residual cases: missing model file on disk
(``FileNotFoundError`` → 503) and any other unexpected error
(→ 500 with a generic detail). Stack traces are written to the
logger, never leaked in the HTTP response body.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.chain.stage1 import extract_features
from app.chain.stage2 import interpret_prediction
from app.ml.predictor import load_model, predict_price
from app.ml.stats import load_stats
from app.schemas.features import ExtractedFeatures
from app.schemas.response import ExtractionResponse, PredictionResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PredictRequest(BaseModel):
    """JSON body shared by ``POST /extract`` and ``POST /predict``.

    Kept inline rather than under ``app/schemas/`` because this shape
    is specific to the HTTP layer and has no reuse value elsewhere.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Free-text description of the house.",
    )
    prompt_version: Literal["v1", "v2"] = Field(
        default="v2",
        description="Stage-1 prompt variant: 'v1' or 'v2'.",
    )
    reviewed_features: ExtractedFeatures | None = Field(
        default=None,
        description=(
            "Optional user-reviewed feature payload. When present, the "
            "API skips Stage 1 and predicts from these values directly."
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Warm up model + stats once per process before accepting traffic."""
    logger.info("Startup: preloading sklearn pipeline and training stats")
    pipeline = load_model()  # fills the lru_cache in app.ml.predictor
    app.state.training_stats = load_stats()

    model_step = pipeline.named_steps.get("model")
    app.state.model_name = (
        type(model_step).__name__ if model_step is not None else None
    )

    logger.info("Startup complete (model=%s)", app.state.model_name)
    try:
        yield
    finally:
        logger.info("Shutdown")


app = FastAPI(
    title="AI Real Estate Agent",
    description=(
        "Natural-language sale-price predictor for the Ames Housing "
        "dataset, with LLM-driven feature extraction and explanation."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Cross-origin setup for deployed environments (e.g. Render static site
# calling the backend web service). Local Docker + Vite dev proxy keep
# requests same-origin, so this only activates in production.
_allowed = os.environ.get("ALLOWED_ORIGINS", "*")
_allowed_origins = (
    ["*"] if _allowed.strip() == "*" else [o.strip() for o in _allowed.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — returns ``{"status": "ok"}`` if the process is up."""
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractionResponse)
async def extract(payload: PredictRequest) -> ExtractionResponse:
    """Run Stage 1 only and return completeness metadata for UI review."""
    try:
        features = payload.reviewed_features or extract_features(
            query=payload.query,
            prompt_version=payload.prompt_version,
        )
    except Exception:
        logger.exception("Unexpected error during /extract")
        raise HTTPException(
            status_code=500,
            detail="Internal error while extracting features.",
        )

    return ExtractionResponse.from_features(
        query=payload.query,
        prompt_version=payload.prompt_version,
        features=features,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictRequest, request: Request) -> PredictionResponse:
    """Run extraction -> prediction -> interpretation and return the bundle."""
    try:
        features = payload.reviewed_features or extract_features(
            query=payload.query,
            prompt_version=payload.prompt_version,
        )
        price = predict_price(features)
        interpretation = interpret_prediction(
            query=payload.query,
            features=features,
            predicted_price=price,
            stats=request.app.state.training_stats,
        )
    except FileNotFoundError:
        # The fitted model or stats file is missing on disk — a 503 is
        # the truthful signal: the service is temporarily unable to
        # answer, not that the caller did something wrong.
        logger.exception("Model or stats file missing at request time")
        raise HTTPException(
            status_code=503,
            detail="Model artifacts not available. Please retry later.",
        )
    except Exception:
        # Catch-all safety net. The specific exception and stack trace
        # are logged; the HTTP response stays generic so we never leak
        # implementation details to the client.
        logger.exception("Unexpected error during /predict")
        raise HTTPException(
            status_code=500,
            detail="Internal error while generating prediction.",
        )

    return PredictionResponse(
        query=payload.query,
        extracted_features=features,
        missing_features=features.missing_fields(),
        predicted_price=price,
        interpretation=interpretation,
        model_name=request.app.state.model_name,
    )
