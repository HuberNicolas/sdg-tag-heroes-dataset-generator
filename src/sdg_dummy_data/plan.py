"""Decide, per publication, which SDGs it is about and how strongly the (fake) model predicts them.

SDG Tag Heroes groups publications per SDG into three levels by prediction score
(`ReducerSettings.FILTER_RANGES` in the main repository):

    level 1: 0.98 < score <= 1.0
    level 2: 0.90 < score <= 0.98
    level 3: 0.70 < score <= 0.90

The UMAP step needs at least ~16 publications per SDG and level, so primary SDGs and levels are
assigned round-robin and every publication gets one or two secondary SDGs on top.
"""

import random
from dataclasses import dataclass, field

from .sdgs import SDGS

LEVEL_RANGES = {1: (0.981, 0.999), 2: (0.905, 0.979), 3: (0.705, 0.899)}


@dataclass
class PublicationPlan:
    publication_id: int
    primary_sdg: int
    primary_level: int
    secondary_sdgs: list[int]
    # One score per SDG, index 0 = SDG 1
    scores: list[float] = field(default_factory=list)


def _score_for_level(rng: random.Random, level: int) -> float:
    low, high = LEVEL_RANGES[level]
    return round(rng.uniform(low, high), 6)


def plan_publications(count: int, rng: random.Random) -> list[PublicationPlan]:
    plans = []
    sdg_ids = [sdg.id for sdg in SDGS]

    for index in range(count):
        publication_id = index + 1
        primary = sdg_ids[index % len(sdg_ids)]
        primary_level = (index // len(sdg_ids)) % 3 + 1

        others = [s for s in sdg_ids if s != primary]
        secondary = rng.sample(others, k=rng.choice((1, 2)))

        scores = [round(rng.uniform(0.001, 0.35), 6) for _ in sdg_ids]
        scores[primary - 1] = _score_for_level(rng, primary_level)
        for position, sdg in enumerate(secondary):
            # Rotate the secondary levels as well, so every SDG/level bin fills up
            level = (index + position) % 3 + 1
            scores[sdg - 1] = _score_for_level(rng, level)

        plans.append(PublicationPlan(publication_id, primary, primary_level, secondary, scores))

    return plans
