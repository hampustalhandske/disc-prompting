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
