"""`disc-classify` command line."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from disc_mirror.classify import classify, summarize
from disc_mirror.config import load_config
from disc_mirror.tasks import load_tasks


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="disc-classify", description=__doc__)
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
