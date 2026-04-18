# AI Real Estate Agent

Week 2 project for the SE Factory AIE Bootcamp.

This app predicts an Ames Housing sale price from a plain-English property description. The system uses a two-stage LLM chain around a supervised sklearn model:

1. Stage 1 extracts structured housing features from the user's query.
2. The sklearn pipeline predicts the sale price.
3. Stage 2 explains the prediction in plain English using training-set statistics.

The UI is intentionally narrative. The user writes a description, reviews the extracted features, fills any important missing values, and only then runs the prediction.

## Demo Flow

1. Enter a free-text description such as `3 bedroom ranch in OldTown, built 1960, 1-car garage`.
2. The app runs Stage 1 only and shows the extracted 12 model features.
3. The user reviews any blanks and can fill missing values before pricing.
4. The reviewed feature set is sent to the model.
5. The app reveals the price and a grounded interpretation.

## Architecture

```text
user query
  -> Stage 1 LLM extraction
  -> ExtractionResponse (features + completeness metadata)
  -> user review / fill missing values
  -> sklearn Pipeline prediction
  -> Stage 2 LLM interpretation
  -> PredictionResponse
  -> FastAPI
  -> React/Vite frontend
```

## Project Structure

```text
app/
  chain/        Stage 1 and Stage 2 orchestration
  ml/           sklearn training, stats, and inference
  prompts/      extraction and interpretation prompts
  schemas/      Pydantic contracts
  utils/        logging helpers
frontend/
  src/          React UI
models/
  model.joblib
  training_stats.json
prompt_logs/
  comparison.json
notebooks/
  eda_and_training.ipynb
tests/
  pytest suite for schemas, chains, predictor, and API routes
```

## Brief Compliance Highlights

- ML pipeline with train/validation/test split and leakage-safe preprocessing
- Stage 1 extraction with prompt versioning evidence in `prompt_logs/comparison.json`
- Stage 2 interpretation grounded in training-set statistics
- Pydantic validation, safe fallbacks, and HTTP error handling
- UI flow that lets the user review or fill missing features before prediction runs
- Docker setup for backend + frontend
- Notebook, presentation support files, tests, and serialized artifacts included

## Main Routes

- `GET /health`
- `POST /extract`
- `POST /predict`

`POST /extract` returns the Stage 1 output plus completeness metadata:

```json
{
  "query": "3 bedroom ranch in OldTown",
  "prompt_version": "v2",
  "extracted_features": {
    "BedroomAbvGr": 3,
    "Neighborhood": "OldTown"
  },
  "present_features": ["BedroomAbvGr", "Neighborhood"],
  "missing_features": ["GrLivArea", "TotalBsmtSF", "..."],
  "completeness_ratio": 0.167,
  "is_complete": false
}
```

`POST /predict` accepts either the raw query alone or a reviewed feature payload:

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

## Local Setup

### 1. Create the environment file

```bash
copy .env.example .env
```

Fill in `OPENAI_API_KEY` inside `.env`. Never commit that file.

### 2. Install Python dependencies

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Run the backend

```bash
uvicorn app.main:app --reload
```

Backend health check:

```bash
curl http://localhost:8000/health
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Docker

Run the full stack:

```bash
docker compose up --build
```

Expected ports:

- backend: `http://localhost:8000`
- frontend: `http://localhost:3000`

## Tests

Run the backend tests:

```bash
pytest -q
```

The suite covers:

- schema validation and completeness metadata
- predictor dataframe shaping and inference
- mocked Stage 1 / Stage 2 failure handling
- `/extract` and `/predict` route behavior

## Notebook and Presentation Files

- Notebook: `notebooks/eda_and_training.ipynb`
- Prompt benchmark log: `prompt_logs/comparison.json`
- Slide deck: `Real_Estate_Pricing_Intelligence_v2.pptx`

## Safety Notes

- `.env` is gitignored and must stay local.
- `.env.example` contains placeholders only.
- No real secret belongs in markdown, notebooks, or source files.
- Run the checks in `PUBLISH_CHECKLIST.md` before your first push.
