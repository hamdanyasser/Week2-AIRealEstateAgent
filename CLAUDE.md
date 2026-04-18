# CLAUDE.md

Project context for future sessions. Read this first.

## Project

**AI Real Estate Agent** — SE Factory AIE Bootcamp Week 2 project.

A natural-language property price predictor for the Ames Housing dataset. The user types a free-form description ("3 bed ranch in good neighborhood, 2-car garage"); an LLM extracts structured features; an sklearn model predicts the sale price; a second LLM call interprets the result in plain English ("above median for the area, driven by quality score").

Owner is a Computing for Data Science student. **Must understand the code, not just run it.** Code review on Friday.

## Architecture

```
user query (text)
   │
   ▼
Stage 1 — LLM extraction (OpenAI)
  prompts/extraction.py + chain/stage1.py
  → ExtractedFeatures (Pydantic)
   │
   ▼
ML prediction (sklearn Pipeline)
  ml/pipeline.py (training) + ml/predictor.py (inference)
  → predicted_price: float
   │
   ▼
Stage 2 — LLM interpretation (OpenAI)
  prompts/interpretation.py + chain/stage2.py
  + ml/stats.py (training-set summary)
  → interpretation: str
   │
   ▼
PredictionResponse (Pydantic) → FastAPI → React/Vite frontend
```

## Coding rules

1. **Explain before coding.** For every new file: what it does, why it exists, what to internalize for review. Never generate code without the teaching layer.
2. **One step at a time.** Work through the 14-step plan in order. User says "next" to advance. Do not skip ahead.
3. **No vibe coding.** Every design choice must have a reason the user can defend in review. If there's a subtle trade-off, name it.
4. **Modular structure.** Follow the `app/` layout exactly — `ml/`, `prompts/`, `chain/`, `schemas/`, `utils/`. Do not create files outside the agreed structure.
5. **Simple and readable.** Clear names, small functions, comments only where the *why* is non-obvious. Clarity beats cleverness.
6. **Code-review questions.** After each file, produce 2–3 likely review questions with short answers.
7. **Must-understand vs boilerplate.** Explicitly tag what the user has to internalize vs what they just need to recognize.
8. **Bootcamp style guide.** PEP 8, snake_case, type hints on every function, Google-style docstrings on public functions, specific exception handling (never bare `except`), `logging` not `print`, pinned dependencies.
9. **Git workflow.** One branch per step: `feature/step-N-description`. Conventional commit messages: `feat(ml): ...`, `chore: ...`, etc. Never commit secrets.

## Tech stack

| Layer | Library | Pinned version |
|---|---|---|
| Backend | FastAPI + uvicorn | 0.115.0 / 0.30.6 |
| ML | scikit-learn, pandas, numpy, joblib | 1.5.2 / 2.2.3 / 2.1.1 / 1.4.2 |
| LLM | openai (`gpt-4o-mini` for cost) | 1.51.0 |
| Schemas | Pydantic v2 + pydantic-settings | 2.9.2 / 2.5.2 |
| UI | React + Vite + Tailwind + Framer Motion | 18.3.1 / 5.4.8 / 3.4.13 / 11.11.1 |
| Deployment | Docker + docker-compose | — |
| Dataset | Kaggle "House Prices — Advanced Regression Techniques" (Ames) | — |

Python 3.11. All runtime deps in [requirements.txt](requirements.txt), dev deps in [requirements-dev.txt](requirements-dev.txt).

## Build plan — 14 steps

| # | Step | Deliverable |
|---|---|---|
| 1 | Scaffolding | Folder tree, `.gitignore`, `.env.example`, pinned `requirements.txt`, [app/config.py](app/config.py), [app/utils/logger.py](app/utils/logger.py) |
| 2 | EDA & feature selection | [notebooks/eda_and_training.ipynb](notebooks/eda_and_training.ipynb) — 12 features chosen at the intersection of high correlation and natural-language reachability |
| 3 | ML pipeline | [app/ml/pipeline.py](app/ml/pipeline.py) — 70/15/15 stratified split, `ColumnTransformer`, ridge + random forest, saves `models/model.joblib` |
| 4 | Training stats | [app/ml/stats.py](app/ml/stats.py) — medians, quartiles, per-neighborhood prices from the **training set only**, saved to `models/training_stats.json` |
| 5 | Pydantic schemas | [app/schemas/features.py](app/schemas/features.py), [app/schemas/response.py](app/schemas/response.py) — all feature fields `Optional` (LLM may not extract everything) |
| 6 | Stage 1 extraction | [app/prompts/extraction.py](app/prompts/extraction.py) (v1 straightforward, v2 few-shot), [app/chain/stage1.py](app/chain/stage1.py) — OpenAI call, Pydantic validation, fallback on failure |
| 7 | Predictor | [app/ml/predictor.py](app/ml/predictor.py) — loads joblib once at import, fills missing features with training-set defaults |
| 8 | Stage 2 interpretation | [app/prompts/interpretation.py](app/prompts/interpretation.py), [app/chain/stage2.py](app/chain/stage2.py) — receives features + price + stats, returns plain-English explanation |
| 9 | Prompt versioning | `prompt_logs/comparison.json` — run v1 vs v2 on 3+ queries, log extraction accuracy, pick winner with evidence |
| 10 | FastAPI backend | [app/main.py](app/main.py) — `POST /predict`, model loaded in `lifespan`, no stack traces in error responses |
| 11 | Frontend UI | [frontend/src/App.jsx](frontend/src/App.jsx) — narrative React UI with staged pipeline reveal, feature display, missing-field feedback, and re-predict flow |
| 12 | Docker | `Dockerfile` (python:3.11-slim, layered COPY for cache) + `docker-compose.yml` (API + UI services) |
| 13 | Tests | [tests/test_schemas.py](tests/test_schemas.py), [tests/test_predictor.py](tests/test_predictor.py), [tests/test_chain.py](tests/test_chain.py) — mocked LLM calls, deliberate garbage-JSON failure demo |
| 14 | README + presentation | Architecture diagram, setup, run instructions; Friday talking points (problem → architecture → demo → lessons) |

## Key constraints — things the user **must** get right

1. **Prevent data leakage.** `.fit()` is called on training data only, inside the sklearn Pipeline. The `ColumnTransformer` holds the imputer + scaler + one-hot encoder so their statistics come from training rows exclusively. The test set is scored **exactly once**, after the validation winner is chosen. Review sentence: *"I split first, fit the preprocessor only on training, the ColumnTransformer inside my Pipeline guarantees imputers/scaler/encoder never see val or test during fitting, and I score on test once."*
2. **Validate LLM output with Pydantic.** Never trust raw JSON from `gpt-4o-mini`. Stage 1 parses the response into `ExtractedFeatures` and returns a safe fallback on any `ValidationError` or `JSONDecodeError`. Never crash on malformed LLM output.
3. **Handle missing features.** LLM extraction is incomplete by design (a user may say only "3 bed"). Every field in `ExtractedFeatures` is `Optional`. The predictor fills missing values with **training-set medians/modes** — never made-up numbers, never zeros. Missing features are reported back to the UI so the user can fill them in and re-predict.
4. **Log errors properly.** Use [`app.utils.logger.get_logger(__name__)`](app/utils/logger.py) everywhere. Never `print()`. Use specific exception types (`JSONDecodeError`, `ValidationError`, `openai.APIError`, `FileNotFoundError`), never bare `except:`. Don't expose stack traces in HTTP responses.
5. **No secrets in code.** `OPENAI_API_KEY` only via environment variables, loaded through [`app/config.py`](app/config.py) using `pydantic-settings.BaseSettings`. `.env` is gitignored. `.env.example` is committed as documentation.

## Working directory

`c:\Users\hamda\Desktop\Week2-AIRealEstateAgent` on Windows 11 + PowerShell. Use forward slashes in paths inside code; outside code use either.

## User Goal

- Understand at least 70% of the code
- Prefer short explanations unless concept is complex
- Avoid long theoretical explanations
- Focus on what is needed for code review

## Response Style

- Keep explanations concise (max 5–8 lines unless asked)
- Focus on practical understanding
- Avoid unnecessary theory

## UI Goal (later stages)

The UI must feel like a premium AI product, not a student project.

Goals:
- Visually impressive, modern, and highly polished
- Unique and memorable (not generic dashboard templates)
- Designed for non-technical users — everything must be intuitive and self-explanatory
- Must clearly communicate the AI pipeline step-by-step

Design principles:
- The UI should tell a story: input → extraction → prediction → explanation
- Each stage of the AI pipeline should be visually separated and progressively revealed
- Use motion/animation to simulate the AI “thinking process” (e.g., loading states, progressive reveal, transitions)
- Highlight key outputs (price, missing features, explanation) with strong visual hierarchy
- Prefer clarity + storytelling over unnecessary visual complexity

Constraints:
- Avoid over-engineered frontend complexity; keep the current React/Vite frontend simple, presentation-friendly, and easy to explain
- Animations should be lightweight and purposeful (no heavy 3D or performance-heavy elements)
- The design must remain easy to understand and explain in a code review

Creative direction:
- Feel like an intelligent assistant, not a static form
- Use progressive disclosure (show results step-by-step instead of all at once)
- Make the system feel interactive and responsive to user input
- Emphasize trust and transparency (show what the AI extracted and how it decided)

Success criteria:
- A non-technical user can understand what the AI is doing without explanation
- The demo feels engaging and “alive”
- The UI supports a strong storytelling flow for presentation

## Current Status

- Step 1 completed
- Step 2 completed
- Step 3 completed
- Step 4 completed
- Step 5 completed
- Step 6 completed
- Step 7 completed
- Step 8 completed
- Step 9 completed
- Step 10 completed
- Step 11 completed
- Step 12 completed (Docker verified locally: backend + frontend images build, `docker compose up --build -d` works, and the stack is reachable on `:8000` and `:3000`)
- Step 13 completed (pytest suite: 10 passed, 0 failed — schemas, predictor, chain fallbacks, `/health` + `/extract` + `/predict`)
- Step 14 completed (README + presentation deck + speaker notes + Q&A prep + publish checklist)
- **Final submission state: repo is clean, committed, and safe to push.**
- Real dataset added at data/train.csv
- Trained model saved at models/model.joblib
- Training stats saved at models/training_stats.json
- Step 3 results:
  - Ridge val RMSE: 33569.17, R2: 0.8481
  - Random Forest val RMSE: 28671.57, R2: 0.8892
  - Winner: random_forest
  - Test RMSE: 25652.40, R2: 0.8957
- Step 4 results:
  - Stats computed from 2051 training rows only (val/test discarded)
  - Price: median 160000, Q1 129000, Q3 212999.5, min 12789, max 755000
  - Avg sqft (GrLivArea): 1495.49
  - Per-neighborhood avg price dict with 27 neighborhoods
  - [app/ml/stats.py](app/ml/stats.py) exposes `compute_training_stats`, `save_stats`, `load_stats`, `run_stats`
- Step 5 results:
  - [app/schemas/features.py](app/schemas/features.py) — `ExtractedFeatures` with all 12 fields `Optional`, range constraints via `Field(ge=..., le=...)`, `extra="ignore"` so stray LLM keys are dropped
  - Python snake_case field names + dataset `alias` (`GrLivArea`, etc.) so `model_dump(by_alias=True)` feeds directly into `pd.DataFrame([...])` with zero rename
  - Helper methods: `missing_fields()` returns alias names of unset fields; `to_model_input()` returns the alias-keyed dict for the predictor
  - [app/schemas/response.py](app/schemas/response.py) — `PredictionResponse` with `extra="forbid"` (our own output, fail loud on bugs), `predicted_price >= 0`, fields: `query`, `extracted_features`, `missing_features`, `predicted_price`, `interpretation`, `model_name`
  - Smoke-tested: partial extraction, extra-key ignore, out-of-range `ValidationError`, response `extra="forbid"` all behave as designed

Key design decision (Step 5):
- Schema field names are snake_case (PEP 8) but carry dataset-column `alias`es. This avoids a separate rename layer between LLM output and the sklearn pipeline while keeping Python code idiomatic. Defend in review as: *"Python stays PEP 8, and `model_dump(by_alias=True)` gives me a dict whose keys already match the training DataFrame columns."*
- Lenient on LLM input (`extra="ignore"`), strict on API output (`extra="forbid"`). Input is untrusted, output is ours.

- Step 6 results:
  - [app/prompts/extraction.py](app/prompts/extraction.py) — two prompt versions (`SYSTEM_PROMPT_V1` straightforward, `SYSTEM_PROMPT_V2` few-shot with 2 worked examples). Both enumerate the 12 exact dataset keys, state ranges, and demand `null` for anything not mentioned. `build_messages(query, version)` returns the OpenAI-shaped messages list.
  - [app/chain/stage1.py](app/chain/stage1.py) — `extract_features(query, prompt_version="v2")` calls `gpt-4o-mini` with `response_format={"type": "json_object"}` and `temperature=0`. Parses + validates into `ExtractedFeatures`. Catches `openai.APIError`, `JSONDecodeError`, `ValidationError` specifically and returns an empty `ExtractedFeatures()` on any failure — pipeline never crashes.
  - `get_client()` is `lru_cache`d so the OpenAI client and API key load exactly once per process.
  - Verified (mocked API): happy path, empty query, malformed JSON fallback, out-of-range validation fallback, `APIError` fallback — all behave as designed.
  - Runtime deps `openai==1.51.0` and `pydantic-settings==2.5.2` were pinned in requirements.txt but missing from the local env; installed both during Step 6.

Key design decision (Step 6):
- Lenient on LLM output at two layers: (a) `response_format="json_object"` forces valid JSON at the API level, (b) Pydantic validation + specific-exception fallbacks stop any remaining garbage from crashing the pipeline. The LLM is treated as an untrusted parser, never a source of truth.
- `temperature=0` chosen for determinism so the Step 9 v1-vs-v2 benchmark is reproducible.

- Step 7 results:
  - [app/ml/predictor.py](app/ml/predictor.py) — `load_model()` joblib-loads the pipeline once per process via `lru_cache`; `features_to_dataframe()` turns `ExtractedFeatures` into a 1-row frame with exact training column names; `predict_price()` runs the pipeline and returns a float.
  - **No manual imputation.** `None` fields become `NaN` (via explicit `pd.to_numeric` coercion on numeric columns) and are filled by the pipeline's own fitted `SimpleImputer` — training medians for numerics, modes for categoricals. Single source of defaults, no training/serving skew.
  - Smoke-tested on the real trained model: rich NridgHt 2-story = $300,691; sparse (3 bed, OldTown) = $167,887; fully empty = $169,030 (near training median $160K, confirming the imputer fallback is working).

Key design decision (Step 7):
- The pipeline *is* the defaults store. We delegate to its `ColumnTransformer` instead of loading `training_stats.json` and filling values manually. Defend in review as: *"The imputer was fitted on training data inside the same Pipeline the model trained on. Using it at inference time guarantees the exact same medians and modes are applied — zero chance of training/serving skew."*
- No clamp on negative predictions. The Pydantic `ge=0` on `PredictionResponse.predicted_price` is the real safety net; silently clamping here would hide a broken model.
- Explicit `pd.to_numeric(errors="coerce")` on numeric columns is required because a DataFrame column of pure Python `None`s lands as object dtype, which `SimpleImputer(strategy="median")` would reject.

- Step 8 results:
  - [app/prompts/interpretation.py](app/prompts/interpretation.py) — single `SYSTEM_PROMPT` (no v1/v2; Step 9 benchmarks Stage 1 only). `build_messages(query, features, predicted_price, stats, missing_count)` injects the original query, the extracted features dict, the price, the training median / Q1 / Q3, and the neighborhood average (when the LLM gave us a known neighborhood) into a structured user turn.
  - [app/chain/stage2.py](app/chain/stage2.py) — `interpret_prediction(query, features, predicted_price, stats=None)` optionally loads stats from disk via `load_stats()`, calls `gpt-4o-mini` with `temperature=0` (deterministic demo), catches `openai.APIError` specifically. Reuses `stage1.get_client` so only one HTTP client exists per process.
  - `_fallback_interpretation(price, stats)` is a deterministic string builder used on LLM failure or empty response: *"The model predicts $300,691, above the training-set median of $160,000."* On at-median, it says "at". With no stats, it degrades to just the price.
  - Verified (mocked API): happy path, `APIError` fallback, empty-response fallback, missing-stats-file + APIError fallback, at-median edge case — all behave as designed.

Key design decision (Step 8):
- **Ground the LLM in training stats.** Without grounding, GPT would reference pretraining knowledge about real estate generally — which has nothing to do with the Ames training set our model was fitted on. Injecting median, quartiles, and the neighborhood average forces commentary to reference the exact numbers the model itself learned. Defend in review as: *"Training stats and the model are a matched pair — both derived from the same training rows in Step 3 / Step 4 — so the Stage-2 prose is talking about the same distribution the sklearn model is."*
- **Deterministic fallback on failure.** Stage 2 must never crash the request; a broken OpenAI call still needs to return *something* for the UI to display. The fallback is computed from the stats dict alone and is deliberately boring — the user knows they're seeing a minimal explanation.
- `temperature=0` chosen for consistency with Stage 1 — the whole demo is deterministic, so the same query produces the same answer every time.

- Step 9 results (infrastructure):
  - [app/prompts/comparison.py](app/prompts/comparison.py) — runnable with `python -m app.prompts.comparison`. 5 realistic `BENCHMARK_CASES` with manually-labeled ground-truth dicts: bedroom ranch in OldTown, NridgHt 2-story luxury, "small old house, bad shape", CollgCr 1.5 story, and a deliberately vague "Big luxury home" (expected = all nulls).
  - For every (case × version) the run logs: `timestamp`, `prompt_version`, `query`, full `extracted` dict, `validation_passed`, `all_null_fallback` flag, `elapsed_ms`, plus `expected` + `score`. Writes everything to `prompt_logs/comparison.json`.
  - Scoring categories per field: **correct** (matches expected, ±2 tolerance for `OverallQual` / `OverallCond`), **incorrect**, **missed**, **hallucinated**, with **true-null** (expected null, extracted null) rolled into the accuracy numerator. Per-query accuracy = `(correct + true_nulls) / 12`; winner = higher mean accuracy, with evidence (correct count, hallucination count) in `winner_reason`.
  - Sanity-verified on a mocked run against a simulated gap (v2 knows "ranch→1Story" and "excellent→9", v1 doesn't): winner=v2, v2 mean=1.0, v1 mean=0.9, v1 hallucinations=1 — mechanics and aggregation confirmed. The dry-run output was written to a scratch path, **not** to `prompt_logs/comparison.json`, so that file still does not exist until a real run.
  - **Real benchmark completed.** Winner: **v2** (few-shot). Mean accuracy: v2=0.983 vs v1=0.617. v2 got 23/23 expected fields correct with 1 hallucination. v1 got 0/23 correct — it returned all-null on every query because the LLM used key names that didn't match the CamelCase aliases, and `extra="ignore"` silently dropped them. The few-shot examples in v2 are the critical difference: they show the exact key format the LLM must emit.
  - Dependency fix applied during Step 9: `pip install 'httpx<0.28'` (now on 0.27.2) — `openai==1.51.0` passes `proxies=` to httpx, but `httpx>=0.28` removed that kwarg. It is now pinned in `requirements.txt` as `httpx<0.28`.

Key design decision (Step 9):
- Scoring is mechanical, not opinion-based. The winner is whichever prompt produces more correct extractions on the same manually-labeled cases. A tolerance of ±2 on quality/condition prevents unfair losses when "good" is mapped to 6 vs 7 — both are defensible readings.
- The `all_null_fallback` flag conflates two states: (a) the stage-1 pipeline fell back on an OpenAI / parse / validation error, and (b) the LLM correctly returned nothing for a genuinely vague query ("Big luxury home"). Reviewer should read the `validation_passed` field alongside it to distinguish the two.
- Benchmark cases are frozen in the source file rather than loaded from a separate YAML, so the review artifact and the scoring code are diffable together.

- Step 10 results:
  - [app/main.py](app/main.py) — FastAPI app with one real endpoint `POST /predict` and a `/health` liveness probe. Inline `PredictRequest(BaseModel)` with `extra="forbid"`, `query` is `min_length=1, max_length=1000`, `prompt_version` defaults to `"v2"`.
  - **Lifespan warm-up.** `lifespan()` calls `load_model()` (populates the predictor's `lru_cache`), then `load_stats()`, then derives `model_name` once from `pipeline.named_steps["model"]` and stashes it on `app.state`. Every request reads from `app.state.training_stats` / `app.state.model_name`. No disk I/O per request, no cold starts.
  - **Error handling without leaks.** Two `except` branches: `FileNotFoundError` → 503 "Model artifacts not available" (missing joblib / stats file), catch-all `Exception` → 500 "Internal error while generating prediction." Both use `logger.exception` so the stack trace hits the logs, never the response body. Stage 1 and Stage 2 already handle their own API failures internally, so the endpoint only has to catch the residual cases.
  - Verified via `TestClient`: `/health` → 200; happy-path `/predict` → 200 with $297,105 + RandomForestRegressor + 6 imputed features (Stages 1/2 mocked to avoid the quota-blocked live API); empty body / missing field / extra field → 422 from Pydantic; simulated `RuntimeError` inside `predict_price` → 500 with generic detail and the word "boom" absent from the response body (trace present only in the logs).

Key design decision (Step 10):
- **Preload in `lifespan`, not at import.** Importing `app.main` shouldn't load the model — tests, CI, and `uvicorn --reload` all benefit from fast imports. Lifespan is the canonical FastAPI hook for "do this once before taking traffic," and `app.state` is the canonical place to stash shared objects. Defend in review as: *"Tests that don't need a model can import `app.main` freely; the model is only loaded when the process actually starts serving, via the lifespan context manager."*
- **Inline request schema.** `PredictRequest` is HTTP-specific (has `prompt_version`, not a modelling concept) and has no reuse value elsewhere, so it lives next to the endpoint instead of under `app/schemas/`. Keeping it inline means the request contract and the handler sit in one file.
- **Generic error details.** Never leak implementation details — the 500 body says only "Internal error while generating prediction." The full trace is written via `logger.exception`, which operators read, not clients.

- Step 11 results:
  - **Stack.** React 18 + Vite 5 + Tailwind 3 + Framer Motion 11. Lucide-react for icons. No Streamlit. Frontend lives in its own [frontend/](frontend/) tree, entirely separate from `app/` — backend stays a headless FastAPI service.
  - **Dev wiring.** Vite dev server on `:5173` proxies `/predict` and `/health` to `http://localhost:8000` (see [frontend/vite.config.js](frontend/vite.config.js)). Two terminals: `uvicorn app.main:app --reload` and `npm run dev` inside `frontend/`. No CORS config needed in dev; for prod, `VITE_API_URL` in `.env` points at the public backend.
  - **Design system.** Colors tokenised in Tailwind config (`canvas #F6F1E8`, `surface #EFE7DA`, `ink #2F3A39`, `muted #6B756F`, `teal`, `terracotta`, `brass`, `seam`). Typography: Fraunces (display serif) + Inter (UI) + IBM Plex Mono (numbers), loaded from Google Fonts. Paper-grain overlay is a fixed radial-gradient layer at 4% opacity — subtle texture without images.
  - **Four-movement story UI.** Hero (editorial headline + stats) → description composer (textarea + 4 example chips + terracotta CTA) → three-stage thinking sequence (one row per pipeline stage, pulsing ring on the active stage, teal dot on complete) → four numbered result sections: `01 Signal` (feature grid, faded cards + "inferred" tag for nulls), `02 Assumptions` (line-list of imputed fields), `03 Estimate` (animated count-up to the price, clamp(4rem, 18vw, 15rem) type size), `04 Reasoning` (serif pull-quote with oversized opening quote). Reset button at the bottom loops back to idle.
  - **State machine.** [frontend/src/App.jsx](frontend/src/App.jsx) is the single source of truth: `idle | thinking | result | error`. `AnimatePresence mode="wait"` handles transitions. A `Promise.all([analyzeProperty(...), setTimeout(2000)])` race gives the thinking sequence a minimum play time so warm-cached requests still feel deliberate instead of skipped.
  - **API contract alignment.** Verified live with `TestClient`: `extracted_features` serializes with CamelCase alias keys (`GrLivArea`, `Neighborhood`, …) — matching `missing_features` — so [frontend/src/lib/featureMeta.js](frontend/src/lib/featureMeta.js) uses the alias form for both lookups. [frontend/src/lib/api.js](frontend/src/lib/api.js) is the only place that talks to FastAPI; it parses the JSON `detail` from error bodies and surfaces it on the `ErrorState` card.
  - **Responsiveness.** All sections use `max-w-6xl` with `px-6`; grid collapses 3→2→1 on narrower breakpoints; price type scales via `clamp(4rem, 18vw, 15rem)`. Tested at desktop widths; mobile layout is readable but the desktop demo is the hero surface.

Key design decisions (Step 11):
- **Editorial aesthetic, not dashboard aesthetic.** A premium real-estate product reads like architecture editorial — warm paper, confident serif, generous whitespace — not like a neon AI console. Every visual choice (Fraunces display, cream/terracotta palette, numbered eyebrows, hairline rules) is in service of that register. Defend in review as: *"This needs to feel like a thoughtful product a non-technical person would trust, so I borrowed the grammar of a printed editorial page instead of a SaaS dashboard."*
- **Make the pipeline visible.** The three-stage thinking sequence isn't cosmetic — it maps directly onto Stage 1 / predictor / Stage 2, so during the demo the UI tells the architecture story for me. Same reason the results are **four numbered sections** instead of one big card: each movement corresponds to a talking point ("Here's what we understood… here's what we had to infer… the estimate… why this number").
- **Backend stays headless.** The frontend talks to `/predict` through a single `analyzeProperty()` function. No feature logic, no pricing logic, no stats, no prompts on the client. This keeps the whole pipeline — including its fallbacks — in Python where it was tested, and lets the UI be redesigned freely without touching the model. Defend in review as: *"Business logic lives once, in FastAPI. The frontend is a viewer."*
- **Alias-based keys across the app.** Because `missing_features` already ships CamelCase and `extracted_features` serializes to CamelCase too, I standardised `FEATURE_META` on the dataset aliases. One lookup key everywhere, no conversion layer.
- **Minimum animation time.** Without the 2-second floor, a warm backend resolving in ~200ms would blow past the thinking sequence before it could tell its story. This is intentional theatre, not a network hack — it exists purely so the pipeline visualization has room to breathe during a live demo.

- Step 12 results:
  - [Dockerfile](Dockerfile) — `python:3.11-slim`, copies `requirements.txt` plus the repo-local `wheels/` wheelhouse, installs fully offline via `pip install --no-index --find-links=/tmp/wheels -r requirements.txt`, then copies `app/` + `models/`. No `apt-get` needed — the manylinux wheels cover the Python/ML runtime.
  - [frontend/Dockerfile](frontend/Dockerfile) — single-stage `node:20-alpine`. It copies the prebuilt `dist/` bundle plus [frontend/serve.cjs](frontend/serve.cjs), so the frontend image builds without `npm install` or network access.
  - [frontend/serve.cjs](frontend/serve.cjs) — tiny zero-dependency Node server built on `http`/`fs`/`path`. It serves the static frontend and proxies `/predict` + `/health` to `http://backend:8000` over Docker Compose DNS.
  - [docker-compose.yml](docker-compose.yml) — two services. `backend` exposes `:8000`, reads `.env` via `env_file`, has a healthcheck on `/health`. `frontend` exposes `:3000→80`, `depends_on` backend with `condition: service_healthy` so it waits for the backend to be ready.
  - `.dockerignore` (root): excludes `.env`, `frontend/`, `tests/`, `notebooks/`, `data/`, `prompt_logs/`, `.git/` — backend image only gets `app/`, `models/`, and `requirements.txt`.
  - `frontend/.dockerignore`: excludes `node_modules`, `dist`, `.env`, `.vite`.
  - **Verified end-to-end on this machine.** `docker build -t week2-backend .`, `docker build -t week2-frontend ./frontend`, and `docker compose up --build -d` all succeeded after freeing host ports `3000` / `8000`. `http://localhost:8000/health` and `http://localhost:3000/health` return `{"status":"ok"}`, and `/predict` works through the frontend proxy.

Key design decisions (Step 12):
- **Offline wheelhouse over normal pip installs.** This machine's network was too unreliable for Docker-time dependency downloads, so the backend image resolves only against repo-local Linux `cp311` wheels. Defend in review as: *"Same pinned requirements, but vendored locally so the Docker build doesn't depend on flaky network access."*
- **Prebuilt frontend bundle, zero-install runtime image.** The frontend is built once on the host, then Docker just copies `dist/` and starts a tiny proxy server. That keeps Step 12 practical on this machine and avoids extra npm network work inside Docker.
- **No secrets in images.** `.env` is in both `.dockerignore` files. The API key is injected at runtime via `env_file: .env` in `docker-compose.yml`. The image itself has zero secrets.
- **Healthcheck before frontend starts.** `depends_on: backend: condition: service_healthy` prevents the frontend container from accepting traffic before the backend's model is loaded. The backend's healthcheck calls `/health` with Python's `urllib` (no extra deps).

- Step 13 results:
  - [tests/test_schemas.py](tests/test_schemas.py) — Pydantic contracts: `ExtractedFeatures` accepts partials, ignores stray LLM keys, rejects out-of-range values, and `missing_fields()` / `to_model_input()` helpers return the right alias keys. `PredictionResponse` and `ExtractionResponse` reject extra fields (`extra="forbid"`).
  - [tests/test_predictor.py](tests/test_predictor.py) — `features_to_dataframe` produces the 12-column, alias-keyed shape the pipeline expects; `predict_price` returns a float for fully-populated, partially-populated, and fully-empty inputs (the imputer fills `NaN`s from training medians/modes).
  - [tests/test_chain.py](tests/test_chain.py) — Stage 1 and Stage 2 with the OpenAI client mocked: happy path, malformed JSON → empty-features fallback, Pydantic validation failure → fallback, `openai.APIError` → fallback, empty-response in Stage 2 → deterministic stats-based string. Proves the pipeline never crashes on LLM failure.
  - [tests/test_main.py](tests/test_main.py) — `/health`, `/extract` (completeness metadata shape), and `/predict` (happy path + reviewed-features bypass path, 422 on extra keys, 500 on unexpected errors with no stack-trace leak). Stages 1/2 are mocked so the suite runs without an API key.
  - **Result:** `pytest -q` → 10 passed, 0 failed. Deliberate garbage-JSON demo lives in `test_chain.py::test_extract_features_malformed_json_returns_empty`.

Key design decision (Step 13):
- **Mocked LLM, real sklearn.** The tests patch `openai` at the client boundary but let the real joblib pipeline run. That means the ML half is tested with actual model I/O (catching joblib/feature-name drift), while the LLM half is tested for the behavior we care about — fallback paths — without spending tokens or depending on network. Defend in review as: *"Every LLM failure mode is exercised deterministically because the client is mocked; the model side is exercised for real because swapping in a fake would let broken feature shapes through."*

- Step 14 results:
  - [README.md](README.md) — architecture diagram, demo flow, project structure, compliance highlights, local + Docker run instructions, API route examples (including the `POST /extract` → review → `POST /predict` flow), and safety notes pointing at `PUBLISH_CHECKLIST.md`.
  - [Real_Estate_Pricing_Intelligence_v2.pptx](Real_Estate_Pricing_Intelligence_v2.pptx) — final editorial deck used in the Friday review.
  - [PUBLISH_CHECKLIST.md](PUBLISH_CHECKLIST.md) — pre-push safety script: verify `.env` ignored + untracked, grep for secrets, rebuild, retest.

Final submission state:
- **All 14 steps complete.** Working LLM → ML → LLM chain, served by FastAPI, consumed by a React/Vite UI, packaged with Docker Compose, covered by `pytest`, with a versioned prompt benchmark and a reproducible deck.
- **Routes:** `GET /health`, `POST /extract` (Stage 1 + completeness metadata), `POST /predict` (either raw query or user-reviewed features → full pipeline).
- **Two-phase UI flow:** user types description → `/extract` shows what the LLM understood + which fields are missing → user reviews/fills gaps → `/predict` reveals price + grounded interpretation. This satisfies the brief's "UI lets the user review and fill gaps before prediction runs" requirement.
- **Tests:** 10 passed. `pytest -q` runs in ~13s, no API key needed.
- **Docker:** `docker compose up --build` brings up backend (`:8000`) + frontend (`:3000`). Backend image built offline from `wheels/`; frontend image serves the prebuilt `dist/` via a zero-dep Node proxy.
- **Artifacts on disk:** `models/model.joblib`, `models/training_stats.json`, `prompt_logs/comparison.json`, `data/train.csv`, `notebooks/eda_and_training.ipynb` — all committed so a grader can rebuild, retest, or rerun without any external fetch.

GitHub safety notes:
- `.env` is gitignored (`.gitignore:21`) and verified **not tracked** (`git ls-files .env` returns nothing). The real `OPENAI_API_KEY` only exists on disk in `.env`, never in source, commits, or history.
- `.env.example` contains placeholder values only — committed as documentation.
- No `sk-` prefixed strings appear anywhere in tracked files or `git log -p`.
- The backend image excludes `.env` via `.dockerignore` and receives the key at runtime through `docker-compose.yml`'s `env_file: .env`. Images carry zero secrets.
- `wheels/` (91 MB of Linux wheels for the Docker offline install) is gitignored but kept locally — regenerate with `pip download -r requirements.txt -d wheels/ --platform manylinux2014_x86_64 --python-version 3.11 --only-binary=:all:` if needed.

Repo organization (final):
- Root: `README.md`, `CLAUDE.md`, `PUBLISH_CHECKLIST.md`, `Dockerfile`, `docker-compose.yml`, `requirements*.txt`, `.env.example`, `.gitignore`, `.dockerignore`, `Real_Estate_Pricing_Intelligence_v2.pptx`, `render.yaml`.
- `app/` — FastAPI backend (`main.py`, `chain/`, `ml/`, `prompts/`, `schemas/`, `utils/`).
- `frontend/` — React/Vite app + `dist/` build + `Dockerfile` + `serve.cjs`.
- `models/`, `data/`, `notebooks/`, `prompt_logs/` — artifacts and deliverables.
- `tests/` — pytest suite.
- Final cleanup (2026-04-18): removed the old `AI_Real_Estate_Agent.pptx` + `make_deck.py` + `presentation_*.md` drafts, dropped the `Real_Estate_Pricing_Intelligence.pptx` v1 and unrelated scratch (`cheatsheet.tex`, `make_hanan_deck.py`). Only `Real_Estate_Pricing_Intelligence_v2.pptx` remains as the canonical deck. `.claude/` is now gitignored alongside `.pytest_cache/`.
