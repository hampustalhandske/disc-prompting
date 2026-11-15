# disc-mirror

Do LLMs mirror how you ask? Each task has a neutral question and D, i, S, C rewrites; the
runner sends each version, unchanged and with no system prompt, to the configured models.

## Setup

    uv sync

A live run needs API keys in the environment (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`,
`OPENROUTER_API_KEY`). Nothing else is required.

## Use

Estimate cost first (local token counts, no network):

    uv run disc-run --tasks tasks --config config/models.yaml --dry-run

Run for real (writes one JSONL record per call to `runs/<timestamp>.jsonl`):

    uv run disc-run --tasks tasks --config config/models.yaml

Models, prices per million tokens, `max_tokens`, samples and the budget live in
`config/models.yaml`. Tasks are one YAML file each; the format is in `docs/MILESTONE.md`.

## Task set and style check

`tasks/` holds 21 tasks across four areas. `check_style_only(load_tasks("tasks"))`
(`src/disc_mirror/stylecheck.py`) returns a list of problems and `[]` when every styled
version has the same numbers as neutral and, for `exact_match`, `dat` and `svg` tasks, the
same last (format) line.

## Style classifier

Checks that the four styles are distinguishable from the question text alone. A judge model
labels every task x version without seeing the task id or version; the command prints the
share labelled correctly per version and writes one JSONL record per call:

    uv run disc-classify --tasks tasks --config config/models.yaml --judge <name>

The default output is `runs/classify-<timestamp>.jsonl`. This makes live API calls.
