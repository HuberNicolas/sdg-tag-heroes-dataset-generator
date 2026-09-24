# SDG Tag Heroes – dataset generator

Generates a **synthetic publication repository** for [SDG Tag Heroes](https://github.com/HuberNicolas/sdg-tag-heroes),
so the application can be built and run without the original data.

The original dataset consists of publications from ZORA, the open repository of the University of Zurich, plus SDG
labels and explanations from SDG-Scout. None of that can be published. This generator writes fictional papers in the
same formats, and SDG Tag Heroes' own pipeline does the rest:

```
 sdg-tag-heroes-dataset-generator                  sdg-tag-heroes
 ────────────────────────────────                  ─────────────────────────────────────────────────────
 fictional papers as OAI-PMH files ─ replaces ZORA ──────▶ collector ▶ SDG predictions ▶ embeddings ▶ maps ▶ topics
 ground-truth labels, explanations ─ replaces SDG-Scout ─▶ label and explanation loaders
 SDG icons, SDG texts, rank tiers  ──────────────────────▶ SDG and rank loaders
```

Everything in the output is made up: paper titles, abstracts, authors, faculties, institutes, journals. The papers
never name real people, institutions, datasets or journals.

## Install

Python 3.10 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

For abstracts written by Claude (`--mode llm`), install the optional dependencies as well:

```bash
uv sync --extra llm
```

## Generate

```bash
uv run sdg-dummy-data --count 600 --out output
```

There are three ways to write the titles and abstracts:

| `--mode`   | Written by                               | Cost | Abstracts                      | Time for 600 papers         |
|------------|------------------------------------------|------|--------------------------------|-----------------------------|
| `template` | Sentence templates (default)             | free | Formulaic, share many phrases  | seconds                     |
| `ollama`   | A local model through [Ollama](https://ollama.com) | free | Realistic, 60–110 words | hours on a laptop CPU (see below) |
| `llm`      | Claude, through the Anthropic API        | paid | Realistic, 150–220 words       | not measured yet            |

The abstracts decide how varied the topics on the SDG Tag Heroes maps are: with template abstracts, BERTopic finds
only a few topics. Everything else (organisation, labels, explanations) is the same in all modes.

| Option          | Default                     | Meaning                                                                 |
|-----------------|-----------------------------|-------------------------------------------------------------------------|
| `--count`       | `600`                       | Number of publications                                                  |
| `--mode`        | `template`                  | `template`, `ollama` or `llm` (see above)                               |
| `--model`       | `llama3.2` / `claude-opus-5` | Model for `--mode ollama` / `--mode llm`                               |
| `--ollama-host` | `$OLLAMA_HOST` or `http://localhost:11434` | Ollama server                                            |
| `--batch-size`  | `10`                        | Papers per Claude request (Ollama writes one paper per request)        |
| `--page-size`   | `100`                       | Records per OAI-PMH page (ZORA uses 100)                                |
| `--seed`        | `31011997`                  | Random seed; the same seed gives the same dataset                       |

Every written paper is cached in `output/cache/papers-<mode>.jsonl`. If a run stops, the next run only writes the
missing papers.

### Abstracts from a local model (free)

1. Install [Ollama](https://ollama.com/download) and start it.
2. Pull a model, for example:

   ```bash
   ollama pull llama3.2
   ```

3. Generate:

   ```bash
   uv run sdg-dummy-data --count 600 --out output --mode ollama
   ```

   With another model, add `--model <name>`, e.g. `--model qwen2.5:7b`.

Local generation is slow on a CPU. With `deepseek-r1:8b` on an Intel MacBook, one paper took about 35 seconds, so 600
papers take about 6 hours; smaller models such as `llama3.2` (3B) are faster. The run shows the remaining time, and
it can be stopped and resumed at any time. For a quick try, use a smaller `--count`, e.g. 200.

### Abstracts written by Claude (paid)

```bash
uv run sdg-dummy-data --count 600 --out output --mode llm
```

This needs the optional dependencies (`uv sync --extra llm`) and Anthropic credentials (`ANTHROPIC_API_KEY`, or a
profile from `ant auth login`). It costs money: roughly 60 requests for 600 papers.

## Output

Copy `output/data/` into the `data/` folder of the SDG Tag Heroes repository.

```
output/
├── data/
│   ├── pipeline/oai/               # the synthetic ZORA (OAI-PMH, Dublin Core)
│   │   ├── ListSets.xml            #   faculty > institute > division
│   │   ├── ListRecords.xml         #   first page of publications
│   │   └── page-0002.xml …         #   next pages, linked by <resumptionToken>
│   ├── db/
│   │   ├── sdg_label_summary.txt   # ground truth: the SDG each paper was written about (by OAI identifier)
│   │   └── explanations/           # token-level SDG explanations for the abstracts
│   ├── icons/                      # placeholder SDG icons, sdg_extras.json (SDG texts)
│   └── ranks/sdg_ranks.json        # rank tiers per SDG
├── cache/                          # generated titles and abstracts per mode
└── manifest.json                   # parameters and counts
```

### How the papers are planned

Each paper has a **primary SDG** (its topic, and its ground-truth label) and one or two **secondary SDGs** it also
touches. Primary SDGs are assigned round-robin, so every SDG gets the same number of papers. The abstract uses the
vocabulary of these SDGs, so an SDG classifier (the pipeline's predictor) recognises them.

The **explanations** stand in for the SHAP explanations of SDG-Scout: words of an abstract that belong to an SDG's
vocabulary get a positive score for that SDG, all others a little noise. They are marked with
`"xai_method": "synthetic-keyword"`.

The **organisation** is a made-up university with 4 faculties, 8 institutes and 16 divisions. Faculties publish
mostly on matching SDGs (e.g. the Faculty of Medicine on SDG 3).

## Load into SDG Tag Heroes

In the SDG Tag Heroes repository, after copying `output/data/` into `data/` and starting the databases, run all
steps (the regular pipeline and loader scripts) with one command:

```bash
PYTHONPATH=. python utils/dummy/load_dummy_dataset.py
```

See "Dummy dataset" in the SDG Tag Heroes README for the Python environment and the Docker commands.

## Development

Lint and format with [Ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`):

```bash
uv run ruff check .
```

```bash
uv run ruff format .
```

## License

The generated data is fictional. The SDG icons in the output are simple placeholders, not the official UN icons.
