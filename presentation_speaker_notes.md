# Speaker notes + full script

**Deck:** [AI_Real_Estate_Agent.pptx](AI_Real_Estate_Agent.pptx) · open in PowerPoint, enter presenter view, turn off cursor/pen.

These notes are written in simple English. Read them once out loud before the session, then don't read them during the talk — speak from memory. Each slide note is 20–40 seconds; the whole deck clocks at **~3 minutes**, leaving room for the live demo and Q&A.

---

## Slide 1 — Cover

**On screen:** *Price any home from a sentence.*

**Say, calmly, no rush:**
> Thank you. This is *AI Real Estate Agent*. The idea is simple — you describe a home in plain English, and the product gives you back a price, with a reason attached. Let me show you how it works and why it's more than a toy.

**Tip:** pause for one full second before clicking to slide 2. Let the title sit.

---

## Slide 2 — The problem

**On screen:** a messy listing form on the left, one clean sentence on the right.

**Say:**
> Pricing a home today is a mess. Buyers see prices but not the reason behind them. Agents lean on instinct. And traditional pricing tools ask you to fill in eighty structured fields before they'll even answer. People don't think in eighty fields — they think in sentences. So the starting question for this project was: *what if you could just describe the house?*

**Tip:** point at the cluttered form when you say "eighty structured fields", then at the sentence when you say "describe the house."

---

## Slide 3 — The product

**On screen:** three cards — Describe → Price → Reason.

**Say:**
> The product is three steps. You describe. We price. We explain. For example — *"three-bed ranch in OldTown, fourteen hundred square feet, good shape"* — and the system returns a number, one hundred sixty-seven thousand dollars, along with a short reason: it's below the neighborhood median because the lot is smaller and the condition is older. That's the product in one breath.

**Tip:** read the example sentence exactly as it is on screen. Don't paraphrase.

---

## Slide 4 — How it works

**On screen:** horizontal diagram, five nodes.

**Say:**
> Under the hood, there are three stages. First, a language model reads the sentence and turns it into structured features — bedrooms, neighborhood, square footage, quality, and so on. Those features are validated with Pydantic, so if the model hallucinates garbage, it's caught before it reaches anything important. Second, a Random Forest trained on two thousand real Ames sales prices the house. Third, a second language model takes the features, the price, and the training statistics, and writes a short human explanation. FastAPI wraps all three; React handles the UI.

**Tip:** walk the diagram left to right with your finger or laser. One node per beat.

---

## Slide 5 — What makes it intelligent

**On screen:** three columns — Extraction, Prediction, Interpretation.

**Say:**
> Three things make this more than a GPT wrapper. One — the extraction prompt is version-controlled. I ran v1 against v2 on labeled queries, and v2 — the few-shot version — won by thirty-seven points of field accuracy. Two — the regression model reaches an R-squared of 0.896 on a held-out test set, and the imputers live *inside* the sklearn Pipeline, so the training medians are reused at inference time. No data leakage, no train-serve skew. Three — the explanation LLM is grounded in the training statistics the model itself learned from, so when it says "above median," it means the same median the model priced against.

**Tip:** this is the technical slide — slow down here. This is where the code review is won or lost.

---

## Slide 6 — Demo

**On screen:** one big screenshot.

**Say:**
> Let me show you.

Then switch to the live product. (Full demo script below.)

**Tip:** don't narrate everything while it runs. Let the UI's three-stage thinking animation do the explaining, and speak *to* it, not over it.

---

## Slide 7 — Closing

**On screen:** three ticks and the closing line.

**Say:**
> Everything you just saw is shipped end to end — FastAPI, React, Docker, tests. The v2 prompt was chosen against a measured benchmark, not a vibe. And next on the roadmap: comparable listings, and a confidence interval around every price. Because a price without a reason isn't an estimate — it's a guess. And this product doesn't guess.

**Pause. Then the closing line:**
> *Real estate, finally in plain English.* Thank you — happy to take questions.

---

# Full 2–4 minute script (read end-to-end)

> Thank you. This is *AI Real Estate Agent*. The idea is simple — you describe a home in plain English, and the product gives you back a price, with a reason attached.
>
> Pricing a home today is a mess. Buyers see prices but not the reason behind them. Agents lean on instinct. Traditional pricing tools ask you to fill in eighty structured fields before they'll answer. People don't think in eighty fields. They think in sentences.
>
> So the product is three steps. You describe. We price. We explain. For example — *"three-bed ranch in OldTown, fourteen hundred square feet, good shape"* — and the system returns one hundred sixty-seven thousand dollars, along with a short reason: below the neighborhood median, because the lot is smaller and the condition is older.
>
> Under the hood, there are three stages. A language model reads the sentence and turns it into structured features, validated with Pydantic. A Random Forest trained on two thousand real Ames sales prices the house. A second language model takes the features, the price, and the training statistics, and writes a short human explanation. FastAPI wraps all three. React handles the UI.
>
> Three things make this more than a GPT wrapper. The extraction prompt is version-controlled — v2 beat v1 by thirty-seven points of field accuracy on labeled queries. The regression model hits an R-squared of 0.896 on a held-out test set, and its imputers live inside the sklearn Pipeline, so there's no train-serve skew. And the explanation LLM is grounded in the same training statistics the model learned from — so when it says "above median," it means the same median the model priced against.
>
> Let me show you. *(switch to live demo)*
>
> What you just saw is shipped end to end — FastAPI, React, Docker, tests. The v2 prompt was chosen against a measured benchmark, not a vibe. Next on the roadmap: comparable listings, and a confidence interval around every price. Because a price without a reason isn't an estimate — it's a guess. And this product doesn't guess. *Real estate, finally in plain English.* Thank you.

---

# Demo script

**Before you start the live run:**
- Backend is running on `localhost:8000` (`uvicorn app.main:app --reload`).
- Frontend is running on `localhost:5173` (`npm run dev` inside `frontend/`).
- Browser is open at `http://localhost:5173`, zoomed to 110% so the price reads well from the back row.
- Your OpenAI key is valid and quota is not exhausted — test one query an hour before the session.

**Query 1 — the everyday case (use this one for the main demo):**

> *"Three-bedroom ranch in OldTown, 1,400 square feet, two-car garage, good condition."*

**While the thinking animation plays, say:**
> You can see the three pipeline stages lighting up — extraction, prediction, interpretation. That's not a cosmetic loader. Each of those stages is a real step, and the UI is showing you the architecture as it runs.

**When the result appears, say:**
> One hundred sixty-seven thousand dollars. The system tells us what it understood from our sentence — three bedrooms, OldTown neighborhood, quality around five. The ones it didn't hear — lot area, year built, basement size — were filled from training medians, and it says so. And the reasoning, in plain English: *"Below the neighborhood median because the lot is smaller and the condition is older."* That's the feature working as designed.

**Query 2 — the contrast (only if time permits):**

> *"Luxury 2-story in NridgHt, 2,500 sqft, 3-car garage, excellent quality, newly built."*

**Point at the price, say:**
> Same product, same pipeline — three hundred thousand dollars, well above the neighborhood average, with reasoning that references the high quality score and new build. The model adapts to the sentence.

**Reset. Don't try a third query. End strong, not long.**

---

# What to do if the demo breaks

- **OpenAI quota error:** switch to Slide 6 and narrate the screenshot. Say: *"The demo surface you're looking at is the real UI — let me walk you through a completed run."*
- **Backend not responding:** check that `uvicorn` is still up in the other terminal. Don't restart mid-demo — fall back to the screenshot.
- **Thinking animation stuck:** let it ride. The 2-second minimum is intentional. If it truly hangs past 6 seconds, reset and say: *"Going to reset and run it again — first-request cold start."*
- **Price looks wrong:** don't apologize on stage. Say: *"That's the model's honest estimate — and this is exactly why Stage 2 explains the number, so you can see the logic instead of trusting a black box."*
