"""Let Claude write fictional titles and abstracts (--mode llm).

Needs `pip install ".[llm]"` and Anthropic credentials (ANTHROPIC_API_KEY or `ant auth login`).
Papers are requested in batches; each batch is one Messages API call with a JSON schema for the answer.
"""

import json

from .papers import PaperSpec, PaperText

SYSTEM_PROMPT = """You write fictional scientific publications for a demo dataset of a research labeling game.

For each requested paper, write a title and an English abstract of 150 to 220 words, in the style of a real
journal abstract (background, method, results with plausible numbers, conclusion).

The papers must be clearly fictional: do not name real people, real universities, real datasets, real
projects or real journals, and do not cite real studies. Places may be generic ("a coastal region in West
Africa") but no named institutions.

Each paper is mainly about its primary topic and also touches its secondary topic. Use vocabulary a researcher
in the given field would use, so a classifier could recognise the related Sustainable Development Goals."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "papers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "publication_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "abstract": {"type": "string"},
                },
                "required": ["publication_id", "title", "abstract"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["papers"],
    "additionalProperties": False,
}


def _describe(spec: PaperSpec) -> str:
    return (
        f"- publication_id {spec.publication_id}: field {spec.field}, published {spec.year}. "
        f"Primary topic: {spec.primary_topic} (SDG: {spec.primary_sdg_name}). "
        f"Secondary topic: {spec.secondary_topic} (SDG: {spec.secondary_sdg_name})."
    )


# Models that support server-side refusal fallbacks
MODELS_WITH_FALLBACKS = {"claude-opus-5", "claude-fable-5-1"}


class ClaudeWriter:
    def __init__(self, model: str):
        try:
            import anthropic
        except ImportError as error:
            raise SystemExit('--mode llm needs the optional dependencies: pip install ".[llm]"') from error

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def write_batch(self, specs: list[PaperSpec]) -> dict[int, PaperText]:
        request = "Write these papers:\n" + "\n".join(_describe(spec) for spec in specs)

        params = dict(
            model=self.model,
            max_tokens=64000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": request}],
            output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
        )
        if self.model in MODELS_WITH_FALLBACKS:
            # If the model declines a batch, the API retries it on a fallback model within the same call
            params.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")

        # Streaming avoids HTTP timeouts on long outputs; the final message is the same as with create()
        with self.client.beta.messages.stream(**params) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the batch starting at publication {specs[0].publication_id}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response was cut off (max_tokens); use a smaller --batch-size")

        text = next(block.text for block in response.content if block.type == "text")
        papers = json.loads(text)["papers"]
        written = {p["publication_id"]: PaperText(p["title"].strip(), p["abstract"].strip()) for p in papers}

        missing = [spec.publication_id for spec in specs if spec.publication_id not in written]
        if missing:
            raise RuntimeError(f"Claude did not return papers {missing}")
        return written
