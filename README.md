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

Python 3.10 or newer.

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -e .
```

For abstracts written by Claude (`--mode llm`), install the optional dependencies:

```bash
.venv/bin/pip install -e ".[llm]"
```

## Generate

```bash
.venv/bin/sdg-dummy-data --count 600 --out output
```

| Option         | Default         | Meaning                                                                         |
|----------------|-----------------|---------------------------------------------------------------------------------|
| `--count`      | `600`           | Number of publications                                                          |
| `--mode`       | `template`      | `template`: offline sentence templates. `llm`: titles and abstracts by Claude    |
| `--model`      | `claude-opus-5` | Claude model for `--mode llm`                                                   |
| `--batch-size` | `10`            | Papers per Claude request                                                       |
| `--page-size`  | `100`           | Records per OAI-PMH page (ZORA uses 100)                                        |
| `--seed`       | `31011997`      | Random seed; the same seed gives the same dataset                               |

### Abstracts written by Claude

`--mode template` is free and fast, but the abstracts read like fill-in-the-blanks text. `--mode llm` asks Claude to
write realistic, clearly fictional abstracts (150–220 words) for the same topics:

```bash
.venv/bin/sdg-dummy-data --count 600 --out output --mode llm
```

It needs Anthropic credentials (`ANTHROPIC_API_KEY`, or a profile from `ant auth login`) and costs money: roughly
60 requests for 600 papers. Every finished paper is cached in `output/cache/papers-llm.jsonl`; if a run stops, the
next run only writes the missing papers.

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

In the SDG Tag Heroes repository, after copying `output/data/` into `data/`:

```bash
PYTHONPATH=. python utils/dummy/load_dummy_dataset.py --phase pipeline
```

```bash
PYTHONPATH=. python utils/dummy/load_dummy_dataset.py --phase app
```

See "Dummy dataset" in the SDG Tag Heroes README for the environments and the Docker commands.

## License

The generated data is fictional. The SDG icons in the output are simple placeholders, not the official UN icons.
