"""Command lines: `disc-run`, `disc-classify` (style classifier) and `disc-grade` (text graders)."""

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from disc_mirror.classify import classify, summarize
from disc_mirror.config import load_config
from disc_mirror.graders import pair_with_neutral
from disc_mirror.graders.exact import grade_exact
from disc_mirror.graders.mirror import GRADED, mirror_deltas
from disc_mirror.graders.pairwise import judge_pairs, win_rates
from disc_mirror.runner import estimate_cost, run
from disc_mirror.tasks import load_tasks


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="disc-run", description="`disc-run` command line.")
    ap.add_argument("--tasks", required=True, type=Path, help="directory of task YAML files")
    ap.add_argument("--config", required=True, type=Path, help="model config YAML")
    ap.add_argument("--out", type=Path, help="JSONL output (default runs/<timestamp>.jsonl)")
    ap.add_argument("--dry-run", action="store_true", help="print the cost estimate, call nothing")
    args = ap.parse_args(argv)

    tasks = load_tasks(args.tasks)
    config = load_config(args.config)

    est = estimate_cost(tasks, config)
    if args.dry_run:
        for name, n in est.prompts.items():
            print(f"{name}: {n} prompts, ${est.model_usd[name]:.4f}")
        print(f"judges: ${est.judge_usd:.4f}")
        print(f"total: ${est.total_usd:.4f} (budget ${config.budget_usd:.2f})")
    if est.total_usd > config.budget_usd:
        raise SystemExit(
            f"estimated ${est.total_usd:.4f} exceeds budget ${config.budget_usd:.2f}"
        )
    if args.dry_run:
        return

    out = args.out or Path("runs") / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    run(tasks, config, out)
    print(f"wrote {out}")


def classify_main(argv: list[str] | None = None) -> None:
    """Run the judge over every task x version and print accuracy per version."""
    ap = argparse.ArgumentParser(prog="disc-classify", description="`disc-classify` command line.")
    ap.add_argument("--tasks", required=True, type=Path, help="directory of task YAML files")
    ap.add_argument("--config", required=True, type=Path, help="model config YAML")
    ap.add_argument("--judge", required=True, help="judge name from `judges:` in the config")
    ap.add_argument(
        "--out", type=Path, help="JSONL output (default runs/classify-<timestamp>.jsonl)"
    )
    args = ap.parse_args(argv)

    tasks = load_tasks(args.tasks)
    judges = {j.name: j for j in load_config(args.config).judges}
    if args.judge not in judges:
        ap.error(f"unknown judge {args.judge!r}; choose from {sorted(judges)}")

    out = args.out or Path("runs") / f"classify-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    records = classify(tasks, judges[args.judge], out)
    for version, accuracy in summarize(records).items():
        print(f"{version}: {accuracy:.2f}")
    print(f"wrote {out}")


def grade_main(argv: list[str] | None = None) -> None:
    """Grade a run file with `exact`, `mirror`, `pairwise`, `dat` or `svg` and print one table."""
    ap = argparse.ArgumentParser(prog="disc-grade", description="`disc-grade` command line.")
    ap.add_argument("grader", choices=["exact", "mirror", "pairwise", "dat", "svg"])
    ap.add_argument("--runs", required=True, type=Path, help="run-record JSONL file")
    ap.add_argument("--tasks", required=True, type=Path, help="directory of task YAML files")
    ap.add_argument("--config", type=Path, help="model config YAML (pairwise)")
    ap.add_argument("--out", type=Path, help="judge JSONL (default runs/judge-<timestamp>.jsonl)")
    ap.add_argument("--glove", type=Path, default=Path("data/glove"), help="GloVe directory (dat)")
    ap.add_argument("--clip-cache", type=Path, default=Path("data/clip"), help="CLIP cache (svg)")
    args = ap.parse_args(argv)
    if args.grader == "pairwise" and not args.config:
        ap.error("pairwise needs --config")

    tasks = load_tasks(args.tasks)
    records = [json.loads(line) for line in args.runs.read_text().splitlines() if line.strip()]

    if args.grader == "exact":
        hits = defaultdict(list)
        for g in grade_exact(records, tasks):
            hits[(g["model"], g["version"])].append(g["correct"])
        print("model\tversion\taccuracy\tn")
        for (model, version), ok in sorted(hits.items()):
            print(f"{model}\t{version}\t{sum(ok) / len(ok):.2f}\t{len(ok)}")
    elif args.grader == "dat":
        from disc_mirror.graders.dat import grade_dat, load_glove

        scores = defaultdict(list)
        for g in grade_dat(records, tasks, load_glove(args.glove)):
            scores[(g["model"], g["version"])].append(g["score"])
        print("model\tversion\tmean_dat\tn\ttoo_short")
        for (model, version), vals in sorted(scores.items()):
            scored = [v for v in vals if v is not None]
            mean_dat = f"{sum(scored) / len(scored):.2f}" if scored else "n/a"
            print(f"{model}\t{version}\t{mean_dat}\t{len(scored)}\t{len(vals) - len(scored)}")
    elif args.grader == "svg":
        from disc_mirror.graders.svg import grade_svg, load_clip

        rows = defaultdict(list)
        for g in grade_svg(records, tasks, load_clip(args.clip_cache)):
            rows[(g["model"], g["version"])].append(g)
        print("model\tversion\trenders\tconstraints\tclip\tn")
        for (model, version), gs in sorted(rows.items()):
            clips = [g["clip"] for g in gs if g["clip"] is not None]
            clip = f"{sum(clips) / len(clips):.2f}" if clips else "n/a"
            print(
                f"{model}\t{version}\t{sum(g['renders'] for g in gs) / len(gs):.2f}"
                f"\t{sum(g['constraints'] for g in gs) / len(gs):.2f}\t{clip}\t{len(gs)}"
            )
    elif args.grader == "mirror":
        deltas = mirror_deltas(records, tasks)
        features = next(iter(deltas.values()), {})
        print("model\tstyle\t" + "\t".join(features))
        for (model, style), d in sorted(deltas.items()):
            print(f"{model}\t{style}\t" + "\t".join(f"{v:+.2f}" for v in d.values()))
        _, skipped = pair_with_neutral(records, {t.id for t in tasks if t.grader in GRADED})
        print(f"skipped (no neutral or no output): {skipped}")
    else:
        out = args.out or Path("runs") / f"judge-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        judgments = judge_pairs(records, tasks, load_config(args.config).judges, out)
        print("model\tstyle\tjudge\twin_rate")
        for (model, style, judge), rate in sorted(win_rates(judgments).items()):
            print(f"{model}\t{style}\t{judge}\t{rate:.2f}")
        print(f"unparsed: {sum(j['winner'] is None for j in judgments)}")
        _, skipped = pair_with_neutral(records, {t.id for t in tasks if t.grader == "pairwise"})
        print(f"skipped (no neutral or no output): {skipped}")
        print(f"wrote {out}")
