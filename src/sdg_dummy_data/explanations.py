"""Synthetic token-level SDG explanations in the format of the SDG-Scout SHAP export.

The frontend highlights tokens of the abstract by their score for the selected SDG and looks each token up
in the abstract text, so the tokens are the whitespace-separated words of the abstract.
"""

import random
import re

from .plan import PublicationPlan
from .sdgs import SDGS

_WORD = re.compile(r"\S+")
_STRIP = re.compile(r"[^a-z0-9-]")


def _matches(word: str, keywords: tuple[str, ...]) -> bool:
    clean = _STRIP.sub("", word.lower())
    return any(clean.startswith(keyword) for keyword in keywords)


def build_explanation(plan: PublicationPlan, oai_identifier: str, abstract: str, rng: random.Random) -> dict:
    tokens = _WORD.findall(abstract)
    token_scores = []
    for token in tokens:
        scores = []
        for sdg in SDGS:
            prediction = plan.scores[sdg.id - 1]
            if _matches(token, sdg.keywords):
                scores.append(round(rng.uniform(0.004, 0.05) * prediction, 9))
            else:
                scores.append(round(rng.gauss(0, 0.0004), 9))
        token_scores.append(scores)

    return {
        "_id": {"$oid": "%024x" % rng.getrandbits(96)},
        "id": oai_identifier,
        "input_tokens": tokens,
        "token_scores": token_scores,
        "base_values": [round(rng.uniform(0.01, 0.05), 9) for _ in SDGS],
        "xai_method": "synthetic-keyword",
        "prediction_model": "sdg-dummy-data",
    }
