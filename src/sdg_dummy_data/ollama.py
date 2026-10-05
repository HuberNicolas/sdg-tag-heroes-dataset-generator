"""Let a local model write fictional titles and abstracts with Ollama (--mode ollama).

Free and offline: needs a running Ollama (https://ollama.com) and a pulled model, e.g. `ollama pull llama3.2`.
Small local models are more reliable with one paper per request, so each paper is its own request, with a JSON
schema for the answer. Only the standard library is used.
"""

import json
import re
import urllib.error
import urllib.request

from .llm import SYSTEM_PROMPT
from .papers import CONTEXTS, METHODS, PaperSpec, PaperText

# Short abstracts are enough for the classifier and the topics, and keep local generation fast
OLLAMA_SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    "an English abstract of 150 to 220 words", "an English abstract of 60 to 110 words"
).replace(
    # Small models copy this example into every abstract; each request names its own setting instead
    'Places may be generic ("a coastal region in West\nAfrica") but no named institutions.',
    "Places must stay generic (no named institutions); use the setting given in the request.",
)
assert "West" not in OLLAMA_SYSTEM_PROMPT

MAX_ATTEMPTS = 3
MAX_TOKENS = 600
REQUEST_TIMEOUT = 180  # seconds

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "abstract": {"type": "string"}},
    "required": ["title", "abstract"],
}


def _describe(spec: PaperSpec) -> str:
    # Small models copy the example place of the prompt into every paper; a setting and a method per paper keep the
    # abstracts (and so the topics) varied. Chosen by publication id, so a rerun gives the same request.
    setting = CONTEXTS[spec.publication_id % len(CONTEXTS)]
    method = METHODS[(spec.publication_id // len(CONTEXTS)) % len(METHODS)]
    return (
        f"Write one paper in the field {spec.field}, published {spec.year}. "
        f"Primary topic: {spec.primary_topic} (SDG: {spec.primary_sdg_name}). "
        f"Secondary topic: {spec.secondary_topic} (SDG: {spec.secondary_sdg_name}). "
        f"Setting: {setting}. Method: {method}. "
        "Answer with JSON containing title and abstract."
    )


def _clean(text: str) -> str:
    """Small models now and then emit a lone UTF-16 surrogate (e.g. \\udfdd), which cannot be written as UTF-8."""
    return re.sub(r"[\ud800-\udfff]", "", text).strip()


class OllamaWriter:
    def __init__(self, model: str, host: str, seed: int):
        self.model = model
        self.url = host.rstrip("/") + "/api/chat"
        self.seed = seed
        self._check(host)

    def _check(self, host: str) -> None:
        try:
            with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=5) as response:
                models = [m["name"] for m in json.load(response)["models"]]
        except (urllib.error.URLError, OSError) as error:
            raise SystemExit(f"Ollama is not reachable at {host}. Start it (ollama serve) and try again.") from error
        if not any(name == self.model or name.split(":")[0] == self.model for name in models):
            raise SystemExit(
                f"Model {self.model} is not pulled. Run: ollama pull {self.model} (installed: {', '.join(models)})"
            )

    def write(self, spec: PaperSpec) -> PaperText:
        # Small models sometimes loop in JSON mode and never stop, or return an empty abstract. Each answer is capped,
        # and a failed one is written again with another seed.
        problem = ""
        for attempt in range(MAX_ATTEMPTS):
            try:
                paper = self._request(spec, seed=self.seed + spec.publication_id + attempt * 100_000)
            except (json.JSONDecodeError, KeyError, TimeoutError, urllib.error.URLError) as error:
                problem = f"{type(error).__name__}: {error}"
                continue
            if len(paper.abstract.split()) >= 40 and paper.title:
                return paper
            problem = f"abstract too short ({len(paper.abstract.split())} words)"
        raise RuntimeError(f"Ollama failed {MAX_ATTEMPTS} times for paper {spec.publication_id}: {problem}")

    def _request(self, spec: PaperSpec, seed: int) -> PaperText:
        body = {
            "model": self.model,
            "stream": False,
            "think": False,  # reasoning models (e.g. deepseek-r1) would otherwise think before every abstract
            "format": RESPONSE_SCHEMA,
            # The seed per paper makes a rerun write the same text (given the same model and Ollama version);
            # num_predict caps the answer, a 110-word abstract needs about 250 tokens
            "options": {"temperature": 0.8, "seed": seed, "num_predict": MAX_TOKENS},
            "messages": [
                {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
                {"role": "user", "content": _describe(spec)},
            ],
        }
        request = urllib.request.Request(
            self.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            answer = json.load(response)
        if "error" in answer:
            raise RuntimeError(f"Ollama: {answer['error']}")
        paper = json.loads(answer["message"]["content"])
        return PaperText(_clean(paper["title"]), _clean(paper["abstract"]))

    def write_batch(self, specs: list[PaperSpec]) -> dict[int, PaperText]:
        return {spec.publication_id: self.write(spec) for spec in specs}
