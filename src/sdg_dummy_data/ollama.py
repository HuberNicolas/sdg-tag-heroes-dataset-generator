"""Let a local model write fictional titles and abstracts with Ollama (--mode ollama).

Free and offline: needs a running Ollama (https://ollama.com) and a pulled model, e.g. `ollama pull llama3.2`.
Small local models are more reliable with one paper per request, so each paper is its own request, with a JSON
schema for the answer. Only the standard library is used.
"""

import json
import urllib.error
import urllib.request

from .llm import SYSTEM_PROMPT
from .papers import PaperSpec, PaperText

# Short abstracts are enough for the classifier and the topics, and keep local generation fast
OLLAMA_SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    "an English abstract of 150 to 220 words", "an English abstract of 60 to 110 words"
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "abstract": {"type": "string"}},
    "required": ["title", "abstract"],
}


def _describe(spec: PaperSpec) -> str:
    return (
        f"Write one paper in the field {spec.field}, published {spec.year}. "
        f"Primary topic: {spec.primary_topic} (SDG: {spec.primary_sdg_name}). "
        f"Secondary topic: {spec.secondary_topic} (SDG: {spec.secondary_sdg_name}). "
        "Answer with JSON containing title and abstract."
    )


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
        body = {
            "model": self.model,
            "stream": False,
            "think": False,  # reasoning models (e.g. deepseek-r1) would otherwise think before every abstract
            "format": RESPONSE_SCHEMA,
            # The seed per paper makes a rerun write the same text (given the same model and Ollama version)
            "options": {"temperature": 0.8, "seed": self.seed + spec.publication_id},
            "messages": [
                {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
                {"role": "user", "content": _describe(spec)},
            ],
        }
        request = urllib.request.Request(
            self.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            answer = json.load(response)
        if "error" in answer:
            raise RuntimeError(f"Ollama: {answer['error']}")
        paper = json.loads(answer["message"]["content"])
        return PaperText(paper["title"].strip(), paper["abstract"].strip())

    def write_batch(self, specs: list[PaperSpec]) -> dict[int, PaperText]:
        return {spec.publication_id: self.write(spec) for spec in specs}
