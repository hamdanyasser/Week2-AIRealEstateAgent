"""Stage-1 prompt comparison benchmark: v1 vs v2.

Runs every query in :data:`BENCHMARK_CASES` through both extraction
prompts, scores each extraction against a manually-labeled ground
truth, and writes a full log plus an aggregate summary to
``prompt_logs/comparison.json``.

Scoring rules
-------------
For each of the 12 fields in :class:`ExtractedFeatures`, one outcome
per query, per version:

* **correct** — expected is non-null and actual matches (exact for
  strings/ints, ±2 for OverallQual / OverallCond since quality words
  like *"good"* reasonably map to 6–8).
* **incorrect** — expected is non-null and actual is a different
  non-null value.
* **missed** — expected is non-null but actual is null.
* **hallucinated** — expected is null (the query did not mention it)
  but actual is non-null.
* **true-null** — expected is null and actual is null (correct handling,
  rolled into the accuracy numerator).

Per-query accuracy = ``(correct + true_nulls) / 12``. Mean accuracy
across cases picks the winner. Counts of each error category are also
persisted so the reviewer can defend the choice.

Reproduce with::

    python -m app.prompts.comparison
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.chain.stage1 import extract_features
from app.schemas.features import ExtractedFeatures
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_OUTPUT_PATH = Path("prompt_logs/comparison.json")
TOTAL_FIELDS = 12

# Ground truth: what a careful human reader would expect an ideal
# extractor to return for each query. Fields omitted here are absent
# from the query text; an extractor inventing them counts as a
# hallucination in the score.
BENCHMARK_CASES: list[dict[str, Any]] = [
    {
        "query": "3 bedroom ranch in OldTown, 2-car garage, built 1960",
        "expected": {
            "BedroomAbvGr": 3,
            "GarageCars": 2,
            "YearBuilt": 1960,
            "Neighborhood": "OldTown",
            "HouseStyle": "1Story",  # "ranch" maps to 1Story
        },
    },
    {
        "query": (
            "Large 2-story home in NridgHt, 4 beds 2.5 baths, "
            "excellent quality, 1800 sqft above grade, fireplace, built 2005"
        ),
        "expected": {
            "GrLivArea": 1800,
            "BedroomAbvGr": 4,
            "FullBath": 2,
            "HalfBath": 1,
            "Fireplaces": 1,
            "YearBuilt": 2005,
            "OverallQual": 9,  # "excellent" ~= 9 per the v2 few-shot
            "Neighborhood": "NridgHt",
            "HouseStyle": "2Story",
        },
    },
    {
        "query": "Small older house, bad shape, 2 bedrooms, needs renovation",
        "expected": {
            "BedroomAbvGr": 2,
            "OverallCond": 3,  # "bad" ~= 3
        },
    },
    {
        "query": (
            "1.5 story in CollgCr, good quality, 3 bed 2 bath, "
            "1 fireplace, built 1998"
        ),
        "expected": {
            "BedroomAbvGr": 3,
            "FullBath": 2,
            "Fireplaces": 1,
            "OverallQual": 7,  # "good" ~= 7
            "YearBuilt": 1998,
            "Neighborhood": "CollgCr",
            "HouseStyle": "1.5Fin",
        },
    },
    {
        "query": "Big luxury home",
        "expected": {},  # deliberately vague; ideal extractor returns all nulls
    },
]

# Tolerance for numeric fields where the mapping from words to numbers
# is inherently fuzzy. "Good" might reasonably be 6, 7, or 8.
NUMERIC_TOLERANCE: dict[str, int] = {
    "OverallQual": 2,
    "OverallCond": 2,
}


def _matches(field: str, expected: Any, actual: Any) -> bool:
    """Return True iff ``actual`` is close enough to ``expected`` to count."""
    if expected is None:
        return actual is None
    if actual is None:
        return False
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        tol = NUMERIC_TOLERANCE.get(field, 0)
        return abs(actual - expected) <= tol
    return str(expected) == str(actual)


def score_extraction(
    expected: dict[str, Any],
    extracted: dict[str, Any],
) -> dict[str, Any]:
    """Score one extraction against its ground truth.

    Args:
        expected: Fields the query actually specifies. Missing keys
            are treated as *"must be null in the extraction"*.
        extracted: Alias-keyed dict from :meth:`ExtractedFeatures.to_model_input`.

    Returns:
        Dict with per-outcome counts and a 0-1 accuracy score.
    """
    correct = 0
    incorrect = 0
    missed = 0
    hallucinated = 0

    for field, actual in extracted.items():
        if field in expected:
            exp = expected[field]
            if _matches(field, exp, actual):
                correct += 1
            elif actual is None:
                missed += 1
            else:
                incorrect += 1
        else:
            if actual is not None:
                hallucinated += 1

    true_nulls = TOTAL_FIELDS - len(expected) - hallucinated
    accuracy = (correct + true_nulls) / TOTAL_FIELDS

    return {
        "correct": correct,
        "incorrect": incorrect,
        "missed": missed,
        "hallucinated": hallucinated,
        "accuracy": round(accuracy, 3),
    }


def run_one(query: str, version: str) -> dict[str, Any]:
    """Run a single extraction and capture the log fields for it.

    Returns a dict with timestamp, prompt version, input query, the
    full extracted dict, a validation flag, a fallback flag
    (all-null often means the LLM or parser failed and we fell back),
    and an elapsed time in milliseconds.
    """
    start = time.perf_counter()
    features: ExtractedFeatures = extract_features(query, prompt_version=version)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    extracted_dict = features.to_model_input()
    # extract_features already catches ValidationError internally and
    # returns an empty ExtractedFeatures(). An all-null result thus
    # either means the LLM genuinely found nothing OR the fallback
    # kicked in. We flag it so the reviewer can tell which.
    all_null = all(value is None for value in extracted_dict.values())

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": version,
        "query": query,
        "extracted": extracted_dict,
        "validation_passed": True,  # we only get here if model_validate accepted
        "all_null_fallback": all_null,
        "elapsed_ms": round(elapsed_ms, 1),
    }


def run_benchmark(
    cases: list[dict[str, Any]] | None = None,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    """Run every case against v1 and v2, score, save to JSON, return payload.

    Args:
        cases: Benchmark cases to run. Defaults to :data:`BENCHMARK_CASES`.
        output_path: Destination JSON file. Parent dirs are created.

    Returns:
        The same payload dict that was written to disk.
    """
    test_cases = cases if cases is not None else BENCHMARK_CASES
    runs: list[dict[str, Any]] = []

    totals: dict[str, dict[str, float]] = {
        version: {
            "correct": 0,
            "incorrect": 0,
            "missed": 0,
            "hallucinated": 0,
            "accuracy_sum": 0.0,
            "elapsed_ms_sum": 0.0,
            "fallback_count": 0,
        }
        for version in ("v1", "v2")
    }

    for case in test_cases:
        query = case["query"]
        expected = case["expected"]
        for version in ("v1", "v2"):
            logger.info("Running %s on: %s", version, query[:60])
            run = run_one(query, version)
            score = score_extraction(expected, run["extracted"])
            run["expected"] = expected
            run["score"] = score
            runs.append(run)

            t = totals[version]
            t["correct"] += score["correct"]
            t["incorrect"] += score["incorrect"]
            t["missed"] += score["missed"]
            t["hallucinated"] += score["hallucinated"]
            t["accuracy_sum"] += score["accuracy"]
            t["elapsed_ms_sum"] += run["elapsed_ms"]
            if run["all_null_fallback"]:
                t["fallback_count"] += 1

    n = len(test_cases)
    summary: dict[str, dict[str, Any]] = {}
    for version, t in totals.items():
        summary[version] = {
            "mean_accuracy": round(t["accuracy_sum"] / n, 3) if n else 0.0,
            "total_correct": int(t["correct"]),
            "total_incorrect": int(t["incorrect"]),
            "total_missed": int(t["missed"]),
            "total_hallucinated": int(t["hallucinated"]),
            "mean_elapsed_ms": round(t["elapsed_ms_sum"] / n, 1) if n else 0.0,
            "fallback_count": int(t["fallback_count"]),
        }

    winner = max(summary, key=lambda v: summary[v]["mean_accuracy"])
    loser = "v2" if winner == "v1" else "v1"
    winner_reason = (
        f"{winner} wins on mean accuracy "
        f"({summary[winner]['mean_accuracy']:.3f} vs "
        f"{summary[loser]['mean_accuracy']:.3f}); "
        f"correct={summary[winner]['total_correct']} vs "
        f"{summary[loser]['total_correct']}, "
        f"hallucinations={summary[winner]['total_hallucinated']} vs "
        f"{summary[loser]['total_hallucinated']}"
    )

    payload = {
        "benchmark_run_at": datetime.now(timezone.utc).isoformat(),
        "n_cases": n,
        "total_fields_per_query": TOTAL_FIELDS,
        "runs": runs,
        "summary": summary,
        "winner": winner,
        "winner_reason": winner_reason,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
    logger.info("Saved benchmark results to %s", output_path)
    logger.info("Winner: %s", winner_reason)

    return payload


if __name__ == "__main__":
    run_benchmark()
