"""Stage-1 extraction prompts.

Two versions of the same task — *"read a free-text house description
and return structured JSON"* — are kept side-by-side so Step 9 can
benchmark them on real queries.

* ``SYSTEM_PROMPT_V1`` — straightforward instructions, no examples.
* ``SYSTEM_PROMPT_V2`` — same instructions plus two worked examples
  (few-shot). Usually lifts extraction accuracy on ambiguous queries.

Both prompts insist on:

* **Exact field names** matching the training dataset columns
  (``GrLivArea``, ``OverallQual``, …). A mismatch here would cause
  ``ExtractedFeatures`` validation to silently drop the value.
* **``null`` for anything not stated.** The single most important rule:
  never invent a number. Missing values are filled downstream with
  training-set medians; hallucinated values can't be undone.
"""

from __future__ import annotations

_SCHEMA_REMINDER = """\
Return a single JSON object with EXACTLY these keys (use null for any
attribute the user does not mention — never guess):

Numeric (numbers or null):
  - GrLivArea        above-grade living area in square feet
  - TotalBsmtSF      total basement area in square feet
  - BedroomAbvGr     above-grade bedroom count (integer 0-20)
  - FullBath         full bathroom count (integer 0-10)
  - HalfBath         half bathroom count (integer 0-10)
  - GarageCars       garage capacity in cars (integer 0-10)
  - YearBuilt        original construction year (integer 1800-2030)
  - Fireplaces       fireplace count (integer 0-10)
  - OverallQual      material/finish quality, integer 1-10
  - OverallCond      overall condition, integer 1-10

Categorical (strings or null):
  - Neighborhood     Ames neighborhood code, e.g. "NAmes", "OldTown",
                     "Edwards", "CollgCr", "NridgHt", "Somerst".
                     Use the official code when you recognise one;
                     otherwise null.
  - HouseStyle       one of "1Story", "2Story", "1.5Fin", "1.5Unf",
                     "2.5Fin", "2.5Unf", "SFoyer", "SLvl", or null.

Rules:
  1. If the user does not mention an attribute, output null for it.
  2. Never guess or invent numbers to fill gaps.
  3. Quality/condition words map to OverallQual/OverallCond:
     "poor"~3, "average"~5, "good"~7, "excellent"~9.
  4. Output valid JSON only. No prose, no markdown, no comments.
"""

SYSTEM_PROMPT_V1 = f"""\
You extract structured house features from a short free-text description
written by a home buyer. The output is fed into a machine-learning model
trained on the Ames Housing dataset.

{_SCHEMA_REMINDER}"""


_FEW_SHOT_EXAMPLES = """\
Example 1
User: "3 bedroom ranch in OldTown, 2-car garage, built 1960, decent shape"
JSON: {"GrLivArea": null, "TotalBsmtSF": null, "BedroomAbvGr": 3,
       "FullBath": null, "HalfBath": null, "GarageCars": 2,
       "YearBuilt": 1960, "Fireplaces": null, "OverallQual": null,
       "OverallCond": 5, "Neighborhood": "OldTown", "HouseStyle": "1Story"}

Example 2
User: "Large 2-story home in NridgHt, 4 beds 2.5 baths, excellent quality,
       1800 sqft above grade, fireplace, built 2005"
JSON: {"GrLivArea": 1800, "TotalBsmtSF": null, "BedroomAbvGr": 4,
       "FullBath": 2, "HalfBath": 1, "GarageCars": null,
       "YearBuilt": 2005, "Fireplaces": 1, "OverallQual": 9,
       "OverallCond": null, "Neighborhood": "NridgHt", "HouseStyle": "2Story"}
"""

SYSTEM_PROMPT_V2 = f"""\
You extract structured house features from a short free-text description
written by a home buyer. The output is fed into a machine-learning model
trained on the Ames Housing dataset.

{_SCHEMA_REMINDER}
{_FEW_SHOT_EXAMPLES}"""


PROMPT_VERSIONS: dict[str, str] = {
    "v1": SYSTEM_PROMPT_V1,
    "v2": SYSTEM_PROMPT_V2,
}


def build_messages(query: str, version: str = "v2") -> list[dict[str, str]]:
    """Build the OpenAI ``messages`` list for a given query and prompt version.

    Args:
        query: Raw user query (free text).
        version: Either ``"v1"`` or ``"v2"``. Defaults to the few-shot
            variant which currently wins on ambiguous queries.

    Returns:
        A list of ``{"role", "content"}`` dicts ready to pass to
        ``client.chat.completions.create``.

    Raises:
        KeyError: If ``version`` is not a registered prompt version.
    """
    system_prompt = PROMPT_VERSIONS[version]
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]
