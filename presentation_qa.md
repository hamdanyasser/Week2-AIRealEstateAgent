# Q&A prep — likely review questions, short answers

Read this once before the session. Each answer is short on purpose — speak it, don't recite it. If you don't know something, say *"I don't know — here's how I'd find out,"* and name the file you'd open. That's a stronger answer than a guess.

---

### 1. How did you prevent data leakage?

I split the dataset 70/15/15 before anything else. The imputer, scaler, and one-hot encoder all live inside a `ColumnTransformer` *inside* the sklearn Pipeline, so they only ever see training rows during `.fit()`. The test set was scored exactly once, after I'd chosen Random Forest over Ridge on the validation set.

---

### 2. Why two LLMs? Why not just ask GPT to price the house?

Because GPT doesn't know *this* market. It knows real estate in general. If I asked GPT for a price, it would hallucinate a plausible number with no grounding in the two thousand Ames sales the model actually learned from. So GPT only does what GPT is good at — reading messy text and explaining numbers. The pricing itself is done by a model trained on real data.

---

### 3. Why Random Forest instead of Ridge?

I trained both. On the validation set, Random Forest reached R² 0.889 against Ridge's 0.848 — so it generalised better on the same split. I picked the winner on validation, then scored it on test once, which gave R² 0.896. If Ridge had won, I'd have shipped Ridge.

---

### 4. What happens if the LLM returns garbage JSON?

Two layers catch it. First, I set `response_format={"type": "json_object"}` on the OpenAI call, which forces valid JSON at the API level. Second, Stage 1 validates the parsed JSON against a Pydantic schema, and catches `JSONDecodeError`, `ValidationError`, and `openai.APIError` specifically. On any of those, the pipeline falls back to an empty features object — the request never crashes.

---

### 5. How do you handle missing features?

Every field in the extraction schema is `Optional`, because a user can say just "three bedrooms" and mean it. Missing fields come through as `None`, become `NaN` in the dataframe, and are filled by the imputer that was fitted on the *training* data — medians for numerics, modes for categoricals. That same imputer is inside the saved Pipeline, so inference and training use identical defaults. The UI also tells the user which features were imputed, so they can refine the sentence if they want.

---

### 6. What did v1-vs-v2 actually show? Why did v2 win?

The few-shot examples in v2 show the model the exact CamelCase key format it needs to emit — `GrLivArea`, `OverallQual`, and so on. v1 described the keys in prose and the model kept returning its own snake_case variants, which Pydantic's `extra="ignore"` silently dropped. So v1 returned all-null on every query. On the labeled benchmark, v2 scored 0.983 mean accuracy against v1's 0.617. The lesson: when you need a specific output shape, show it — don't describe it.

---

### 7. How do you know the price is good?

Test R² 0.896 and RMSE $25,652 on a held-out test set that the model and the preprocessor never saw during training. For an Ames dataset where prices range from $12K to $755K, an RMSE of $26K is a reasonable error band. I'd want more evaluation before shipping to real users — per-neighborhood error, residual analysis — and that's on the roadmap.

---

### 8. How do you know the *explanation* isn't hallucinated?

Stage 2 is grounded in real numbers from the training set — the median, quartiles, and per-neighborhood averages computed in `app/ml/stats.py`. Those numbers are passed into the prompt, and the instruction is to reference *them*, not generic real estate knowledge. It's not a full guarantee — an LLM can still drift — but the structured grounding dramatically reduces the space in which it can make things up.

---

### 9. Why pin dependencies so tightly?

Because LLMs + sklearn + FastAPI is a notoriously fragile stack. During Step 9 I hit exactly this — `openai==1.51.0` passes `proxies=` to httpx, and `httpx>=0.28` removed that kwarg. One unpinned upgrade would have broken the whole Stage 1 pipeline. Pinning is a cheap insurance policy.

---

### 10. What would you build next, realistically?

Three things, in order. First, a confidence interval on every price — the Random Forest can give me one essentially for free via the variance across trees. Second, a "comparable sales" panel — show the three nearest training-set homes to the one being priced, so the estimate has receipts. Third, fine-tune the extraction prompt on a larger labeled set — the current 5-case benchmark is enough to pick v2 over v1, but not enough to trust the number in production.

---

### 11. Is this production-ready?

Honestly, no — and I'd say that in the interview too. It's demo-ready and code-review-ready. For production you'd want: authentication, rate limiting on the OpenAI calls, a monitoring layer for the prompt outputs, a retraining pipeline, and a much larger evaluation set. What I've built is the right shape for all of that to slot into later.

---

### 12. What's the one thing you're proudest of?

That the imputer lives inside the Pipeline. It's a one-line design choice that eliminates an entire class of bug — training-serving skew — without me having to remember to keep two dicts in sync. It's the difference between "I hope the defaults match" and "they cannot, by construction, differ."

---

### 13. What's the one thing you'd change?

The Stage 2 prompt is a single version. I benchmarked v1-vs-v2 for extraction, but I didn't do the same for interpretation. Before a real release I'd run the same comparison on the explanation LLM — measure specificity, groundedness, and length — and pick a winner the same way.

---

### 14. Why not Streamlit? The plan said Streamlit.

The project spec called for a premium, storytelling UI — something that would feel like a real product, not a form. Streamlit is excellent for quick internal tools, but it fights you the moment you want editorial typography, custom motion, and a specific narrative flow. React + Vite + Framer Motion gave me exactly the surface I needed for about a day's extra work. The backend didn't change — FastAPI is still the headless API, and the frontend is just a viewer.
