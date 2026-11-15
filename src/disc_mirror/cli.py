"""Command lines: `disc-run` (dry run or live run) and `disc-classify` (style classifier)."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from disc_mirror.classify import classify, summarize
from disc_mirror.config import load_config
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

    if args.dry_run:
        est = estimate_cost(tasks, config)
        for name, n in est.prompts.items():
            print(f"{name}: {n} prompts, ${est.model_usd[name]:.4f}")
        print(f"judges: ${est.judge_usd:.4f}")
        print(f"total: ${est.total_usd:.4f} (budget ${config.budget_usd:.2f})")
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
