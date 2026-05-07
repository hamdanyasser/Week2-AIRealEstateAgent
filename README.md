# AI Real Estate Agent

A natural-language sale-price estimator for the Ames Housing dataset. The user types a free-text description ("3-bed ranch in OldTown, decent shape, 2-car garage"), an LLM extracts structured features, a scikit-learn model predicts the sale price, and a second LLM call interprets the result against training-set statistics.

**Live demo:** https://ai-real-estate-web.onrender.com (free-tier backend cold-starts; first request may take ~30s)

## Why this exists

Ames Housing is a classic regression dataset, but the standard form-based interface to a price model — fill in 80 columns, click Submit — is hostile to anyone who doesn't already think in feature names. This project tests whether an LLM can bridge the gap: take ambiguous human language, extract just the columns the model needs, and produce a number a non-technical user can trust.

The interesting part isn't the regression (sklearn does the obvious thing). It's the two failure modes around it: an LLM that may hallucinate or omit features, and a price prediction that means nothing without context. The app addresses both — Pydantic validation + safe fallbacks for the first, training-stats-grounded interpretation for the second — and shows its work to the user so they can correct any misreadings before the price is computed.

## Architecture

```text
user query (free text)
  │
  ▼
Stage 1 — LLM extraction (OpenAI-compatible, JSON mode)
  → ExtractedFeatures (Pydantic, all fields Optional)
  │
  ▼
optional user review (UI pause)
  → user fills missing or wrong values
  │
  ▼
sklearn Pipeline prediction
  → ColumnTransformer (impute + scale + one-hot) → RandomForestRegressor
  → predicted_price : float
  │
  ▼
Stage 2 — LLM interpretation (grounded in training stats)
  → plain-English explanation
  │
  ▼
PredictionResponse (Pydantic) → FastAPI → React frontend
```

## Key design choices

1. **Two-stage LLM chain, not one.** Stage 1 is mechanical (parse text → JSON), Stage 2 is interpretive (explain a number). Splitting them lets each prompt stay short and focused, and it puts the deterministic sklearn model in the middle where the actual price is decided. The LLM never picks the price.
2. **The pipeline owns the defaults.** When the LLM omits features, the saved sklearn `Pipeline`'s own fitted `SimpleImputer` fills them with training medians/modes. There is no second copy of "what to fill in" living anywhere else, so there is no chance of training/serving skew.
3. **Lenient on input, strict on output.** `ExtractedFeatures` accepts partials and ignores stray LLM keys (`extra="ignore"`). `PredictionResponse` rejects extras (`extra="forbid"`) — that's the app's own contract, and any drift there is a real bug.
4. **Stage 2 is grounded.** The interpretation prompt receives the predicted price plus the training median, quartiles, and the per-neighborhood average. Without that grounding, GPT would reference its pretraining knowledge of real estate generally — which has nothing to do with the specific Ames training set this model was fitted on.
5. **Two-phase UI flow.** The frontend calls `/extract` first, shows what the LLM understood, lets the user fix anything, and only then calls `/predict`. This keeps silent extraction errors from propagating into the final number.
6. **Pluggable LLM provider.** The OpenAI client honours an optional `OPENAI_BASE_URL`, so the same code works against OpenAI, Groq, or any OpenAI-compatible endpoint with a single env var swap.

## Tech stack

| Layer | Library | Pinned version |
|---|---|---|
| Backend | FastAPI + uvicorn | 0.115.0 / 0.30.6 |
| ML | scikit-learn, pandas, numpy, joblib | 1.5.2 / 2.2.3 / 2.1.1 / 1.4.2 |
| LLM | openai (`gpt-4o-mini` default) | 1.51.0 |
| Schemas | Pydantic v2 + pydantic-settings | 2.9.2 / 2.5.2 |
| UI | React + Vite + Tailwind + Framer Motion | 18.3.1 / 5.4.8 / 3.4.13 / 11.11.1 |
| Deploy | Docker + docker-compose | — |
| Data | Kaggle "House Prices — Advanced Regression Techniques" (Ames) | — |

Python 3.11.

## Project structure

```text
app/
  chain/        Stage 1 + Stage 2 orchestration with safe fallbacks
  ml/           sklearn training, training stats, and inference
  prompts/      v1 / v2 extraction prompts and the interpretation prompt
  schemas/      Pydantic contracts (input lenient, output strict)
  utils/        logging
  main.py       FastAPI app (lifespan-loaded model + stats)
frontend/
  src/          React UI (idle → thinking → result state machine)
  dist/         prebuilt bundle for Docker
models/
  model.joblib
  training_stats.json
prompt_logs/
  comparison.json   v1 vs v2 benchmark output (5 labeled cases)
notebooks/
  eda_and_training.ipynb
tests/
  pytest suite — schemas, predictor, mocked LLM fallbacks, route behaviour
```

## API

| Route | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `POST /extract` | Stage 1 only — returns extracted features + completeness metadata |
| `POST /predict` | Full pipeline — accepts a raw query, or user-reviewed features |

`POST /extract` example:

```json
{
  "query": "3 bedroom ranch in OldTown",
  "prompt_version": "v2",
  "extracted_features": { "BedroomAbvGr": 3, "Neighborhood": "OldTown" },
  "missing_features": ["GrLivArea", "TotalBsmtSF", "..."],
  "completeness_ratio": 0.167,
  "is_complete": false
}
```

`POST /predict` accepts either a raw query (Stage 1 runs) or pre-reviewed features (Stage 1 skipped):

```json
{
  "query": "3 bedroom ranch in OldTown",
  "reviewed_features": {
    "BedroomAbvGr": 3,
    "Neighborhood": "OldTown",
    "GarageCars": 1
  }
}
```

## Local setup

### 1. Environment file

```bash
cp .env.example .env
```

Fill `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL` + `MODEL_NAME` if pointing at a non-OpenAI provider — see `.env.example`).

### 2. Backend

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/extract`, `/predict`, and `/health` to the backend on `:8000`.

## Docker

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Tests

```bash
pytest -q
```

10 tests, runs in ~3 seconds. Covers schema validation, predictor dataframe shaping and inference, mocked LLM failure paths (malformed JSON, validation error, API error), and the FastAPI route behaviour. No API key required.

## Safety notes

- `.env` is gitignored. `.env.example` ships placeholder values only.
- No real key belongs in source, markdown, notebooks, or commits.
- See `PUBLISH_CHECKLIST.md` for a pre-push secret-scanning routine.

## License

MIT — see `LICENSE` if present, otherwise treat as MIT.
