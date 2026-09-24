"""Generate a synthetic publication repository for SDG Tag Heroes.

    sdg-dummy-data --count 600 --out output                 # offline, template abstracts
    sdg-dummy-data --count 600 --out output --mode ollama   # abstracts written by a local model (free)
    sdg-dummy-data --count 600 --out output --mode llm      # abstracts written by Claude (paid)

Output (copy output/data/ into the data/ folder of the SDG Tag Heroes repository):
    output/data/pipeline/oai/   OAI-PMH responses that replace ZORA (collector.py --from-dir data/pipeline/oai)
    output/data/db/             ground-truth labels and explanations (what SDG-Scout used to provide)
    output/data/icons, ranks/   SDG icons (placeholders), SDG texts and rank tiers
"""

import argparse
import json
import os
import random
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from faker import Faker

from . import oai
from .explanations import build_explanation
from .icons import goal_icon
from .organizations import divisions_for_sdg
from .papers import PaperText, build_specs, write_from_template
from .plan import plan_publications
from .sdgs import SDGS

STATIC = Path(__file__).parent / "static"
OAI_PREFIX = "oai:dummy.sdg-tag-heroes:"
DEFAULT_MODELS = {"ollama": "llama3.2", "llm": "claude-opus-5"}
EXPLANATIONS_PER_FILE = 10_000  # same split size as utils/mongodb/sdg-explanation-splitter.sh


def _write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _authors(faker: Faker, count: int) -> list[str]:
    """Author names in the ZORA format "Lastname, Firstname" (the Author model splits them at the comma)."""
    names = {f"{faker.last_name()}, {faker.first_name()}" for _ in range(count * 2)}
    return sorted(names)[:count]


def write_papers(args, plans, specs, rng) -> dict[int, PaperText]:
    """Write titles and abstracts. Results are cached per mode, so a rerun only writes the missing papers."""
    cache_path = Path(args.out) / "cache" / f"papers-{args.mode}.jsonl"
    cached = {row["publication_id"]: PaperText(row["title"], row["abstract"]) for row in _read_jsonl(cache_path)}
    plans_by_id = {plan.publication_id: plan for plan in plans}
    todo = [spec for spec in specs if spec.publication_id not in cached]

    if args.mode == "template":
        for spec in todo:
            cached[spec.publication_id] = write_from_template(spec, plans_by_id[spec.publication_id], rng)
        _write_jsonl(cache_path, ({"publication_id": pid, **asdict(p)} for pid, p in sorted(cached.items())))
        return cached

    if args.mode == "ollama":
        from .ollama import OllamaWriter

        writer, batch_size = OllamaWriter(args.model, args.ollama_host, args.seed), 1
    else:
        from .llm import ClaudeWriter

        writer, batch_size = ClaudeWriter(args.model), args.batch_size

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    for start in range(0, len(todo), batch_size):
        batch = todo[start : start + batch_size]
        written = writer.write_batch(batch)
        done = start + len(batch)
        remaining = (time.time() - started) / done * (len(todo) - done)
        print(
            f"{args.model}: papers {batch[0].publication_id}-{batch[-1].publication_id} ({done}/{len(todo)}, "
            f"about {remaining / 60:.0f} min left)",
            flush=True,
        )
        with cache_path.open("a", encoding="utf-8") as f:
            for spec in batch:
                paper = written[spec.publication_id]
                cached[spec.publication_id] = paper
                f.write(json.dumps({"publication_id": spec.publication_id, **asdict(paper)}, ensure_ascii=False) + "\n")
    return cached


def generate(args) -> None:
    rng = random.Random(args.seed)
    faker = Faker(["en_US", "de_CH", "fr_FR", "it_IT"])
    faker.seed_instance(args.seed)

    out = Path(args.out)
    plans = plan_publications(args.count, rng)

    author_pool = _authors(faker, max(40, args.count // 3))
    divisions = {plan.publication_id: rng.choice(divisions_for_sdg(plan.primary_sdg)) for plan in plans}
    years = {plan.publication_id: rng.randint(2005, 2024) for plan in plans}
    fields = {pid: division.faculty.name.removeprefix("Faculty of ") for pid, division in divisions.items()}

    specs = build_specs(plans, fields, years, rng)
    papers = write_papers(args, plans, specs, rng)

    publications, explanations = [], []
    for plan in plans:
        pid = plan.publication_id
        oai_identifier = f"{OAI_PREFIX}{pid}"
        publications.append(
            {
                "oai_identifier": oai_identifier,
                "title": papers[pid].title,
                "description": papers[pid].abstract,
                "authors": rng.sample(author_pool, k=rng.randint(1, 5)),
                "publisher": "Synthetic Academic Press",
                "date": f"{years[pid]}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
                "source": f"Journal of Synthetic Sustainability Research, vol. {years[pid] - 2000}",
                "language": "eng",
                "format": "text",
                "set_spec": divisions[pid].set_spec,
            }
        )
        explanations.append(build_explanation(plan, oai_identifier, papers[pid].abstract, rng))

    data = out / "data"

    # data/pipeline/oai: the synthetic ZORA
    oai_dir = data / "pipeline" / "oai"
    shutil.rmtree(oai_dir, ignore_errors=True)
    oai_dir.mkdir(parents=True)
    oai.write_list_sets(oai_dir)
    pages = oai.write_list_records(oai_dir, publications, args.page_size)

    # data/db/sdg_label_summary.txt: ground truth (the SDG each paper was written about),
    # read by load_mariadb_sdg_label_summaries.py; keyed by OAI identifier
    (data / "db").mkdir(parents=True, exist_ok=True)
    with (data / "db" / "sdg_label_summary.txt").open("w") as f:
        for plan in plans:
            labels = ", ".join("1" if sdg.id == plan.primary_sdg else "0" for sdg in SDGS)
            f.write(f"('{OAI_PREFIX}{plan.publication_id}', {labels}),\n")

    # data/db/explanations: token-level explanations, read by load_mongodb_explanations.py
    explanations_dir = data / "db" / "explanations"
    shutil.rmtree(explanations_dir, ignore_errors=True)
    for part, start in enumerate(range(0, len(explanations), EXPLANATIONS_PER_FILE)):
        _write_jsonl(
            explanations_dir / f"split_part_{part:03d}.json", explanations[start : start + EXPLANATIONS_PER_FILE]
        )

    # data/icons and data/ranks: placeholder SDG icons, SDG texts and rank tiers
    (data / "icons").mkdir(parents=True, exist_ok=True)
    for sdg in SDGS:
        (data / "icons" / f"Color_Goal_{sdg.id}.svg").write_text(goal_icon(sdg))
    shutil.copy(STATIC / "sdg_extras.json", data / "icons" / "sdg_extras.json")
    (data / "ranks").mkdir(parents=True, exist_ok=True)
    shutil.copy(STATIC / "sdg_ranks.json", data / "ranks" / "sdg_ranks.json")

    manifest = {
        "generator": "sdg-dummy-data",
        "seed": args.seed,
        "count": args.count,
        "mode": args.mode,
        "model": args.model if args.mode != "template" else None,
        "oai_pages": pages,
        "authors": len(author_pool),
        # What the generator intended; the pipeline's predictor decides the actual predictions
        "papers_per_primary_sdg": {f"sdg{s.id}": sum(p.primary_sdg == s.id for p in plans) for s in SDGS},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {args.count} publications: {pages} OAI pages in {oai_dir}, labels and explanations in {data}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic publication repository for SDG Tag Heroes.")
    parser.add_argument("--count", type=int, default=600, help="number of publications (default: 600)")
    parser.add_argument("--out", default="output", help="output folder (default: output)")
    parser.add_argument("--seed", type=int, default=31011997, help="random seed (default: 31011997)")
    parser.add_argument(
        "--mode",
        choices=["template", "ollama", "llm"],
        default="template",
        help="template: offline sentence templates; ollama: a local model (free); llm: Claude (paid)",
    )
    parser.add_argument(
        "--model",
        help=f"model for --mode ollama (default: {DEFAULT_MODELS['ollama']}) or llm ({DEFAULT_MODELS['llm']})",
    )
    parser.add_argument(
        "--ollama-host",
        default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        help="Ollama server (default: $OLLAMA_HOST or http://localhost:11434)",
    )
    parser.add_argument("--batch-size", type=int, default=10, help="papers per Claude request (default: 10)")
    parser.add_argument("--page-size", type=int, default=100, help="records per OAI page (default: 100, like ZORA)")
    args = parser.parse_args()
    args.model = args.model or DEFAULT_MODELS.get(args.mode)
    if not args.ollama_host.startswith("http"):
        args.ollama_host = "http://" + args.ollama_host  # OLLAMA_HOST is often given without a scheme
    generate(args)


if __name__ == "__main__":
    main()
