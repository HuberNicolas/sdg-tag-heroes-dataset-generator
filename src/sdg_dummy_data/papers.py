"""Titles and abstracts for synthetic publications.

`template` mode builds them offline from sentence templates and the SDG vocabulary (free, deterministic).
`ollama` mode lets a local model write them (see ollama.py), `llm` mode asks Claude (see llm.py).
"""

import random
from dataclasses import dataclass

from .plan import PublicationPlan
from .sdgs import SDG_BY_ID


@dataclass
class PaperText:
    title: str
    abstract: str


@dataclass(frozen=True)
class PaperSpec:
    """What a paper should be about. Shared by both modes."""

    publication_id: int
    primary_topic: str
    primary_sdg_name: str
    secondary_topic: str
    secondary_sdg_name: str
    field: str
    year: int


CONTEXTS = (
    "three rural districts",
    "a mid-sized European city",
    "coastal communities",
    "a national household panel",
    "twelve low- and middle-income countries",
    "an alpine region",
    "a cohort of 2,400 participants",
    "municipal administrations",
    "smallholder cooperatives",
    "secondary schools in two provinces",
)
METHODS = (
    "a randomised field experiment",
    "a mixed-methods case study",
    "panel regression models",
    "a systematic review and meta-analysis",
    "remote sensing and field surveys",
    "agent-based simulation",
    "semi-structured interviews",
    "a longitudinal cohort design",
    "a spatial econometric model",
)
TITLE_PATTERNS = (
    "{Topic}: evidence from {context}",
    "Assessing {topic} in {context}",
    "The role of {secondary} in {topic}",
    "{Topic} and {secondary}: a study of {context}",
    "Rethinking {topic} through the lens of {secondary}",
)


def _cap(text: str) -> str:
    return text[0].upper() + text[1:]


def build_specs(
    plans: list[PublicationPlan], fields: dict[int, str], years: dict[int, int], rng: random.Random
) -> list[PaperSpec]:
    specs = []
    for plan in plans:
        primary = SDG_BY_ID[plan.primary_sdg]
        secondary = SDG_BY_ID[plan.secondary_sdgs[0]]
        specs.append(
            PaperSpec(
                publication_id=plan.publication_id,
                primary_topic=rng.choice(primary.topics),
                primary_sdg_name=primary.name,
                secondary_topic=rng.choice(secondary.topics),
                secondary_sdg_name=secondary.name,
                field=fields[plan.publication_id],
                year=years[plan.publication_id],
            )
        )
    return specs


def write_from_template(spec: PaperSpec, plan: PublicationPlan, rng: random.Random) -> PaperText:
    primary = SDG_BY_ID[plan.primary_sdg]
    secondary = SDG_BY_ID[plan.secondary_sdgs[0]]
    context = rng.choice(CONTEXTS)
    method = rng.choice(METHODS)

    title = rng.choice(TITLE_PATTERNS).format(
        Topic=_cap(spec.primary_topic),
        topic=spec.primary_topic,
        secondary=spec.secondary_topic,
        context=context,
    )

    k1, k2, k3 = rng.sample(primary.keywords, 3)
    s1 = rng.choice(secondary.keywords)
    effect = rng.randint(8, 41)
    sentences = [
        f"{_cap(spec.primary_topic)} remains a central challenge for {k1} and {k2} in {context}.",
        f"Earlier work has rarely connected it to {spec.secondary_topic}, although {s1} shapes outcomes in many settings.",
        f"This study uses {method} to examine how {k3} changed between {spec.year - rng.randint(4, 12)} and {spec.year - 1}.",
        f"We find that targeted measures improved {k1} outcomes by {effect}% on average, with larger effects where {s1} was addressed at the same time.",
        f"Effects were weaker for the most vulnerable groups, pointing to gaps in {rng.choice(primary.keywords)} and {rng.choice(secondary.keywords)}.",
        f"The results inform {spec.field.lower()} research and policies that link {primary.name.lower()} with {secondary.name.lower()}.",
    ]
    if rng.random() < 0.5:
        sentences.insert(
            4, f"Robustness checks with alternative specifications confirm the direction of the {k2} effect."
        )
    return PaperText(title=title, abstract=" ".join(sentences))
