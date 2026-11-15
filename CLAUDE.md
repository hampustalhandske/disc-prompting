# disc-prompting

## Map

Parts
- `src/disc_mirror/tasks.py`: task YAML loader and validation (`load_tasks`)
- `src/disc_mirror/config.py`: model config loader (`load_config`)
- `src/disc_mirror/runner.py`: offline cost estimate (`estimate_cost`) and live LiteLLM runner (`run`)
- `src/disc_mirror/cli.py`: the `disc-run` command
- `config/models.yaml`: tested models, judges, prices, samples, budget
- `tests/fixtures/`: one task per area, and the socket blocker for no-network tests

Contracts (source of truth: docs/MILESTONE.md of m1)
- Task file: one YAML per task (`id` = file name, `area`, `grader`, `rationale`, `versions` neutral/D/i/S/C, `expected`). Written by m2, read by the loader and graders.
- Run record: one JSONL line per call (task_id, version, model, litellm_id, sample, temperature, max_tokens, prompt, output, input_tokens, output_tokens, timestamp). Written by `run`, read by the m3/m4 graders.

Commands
- Test and lint: `uv run ruff check . && uv run pytest -q`
- Dry run: `uv run disc-run --tasks <dir> --config config/models.yaml --dry-run`

Binding decisions
- The prompt is only the version text: no system prompt, no style instruction.
- The dry run and the tests never touch the network.
- Claude makes no live API calls in v1; Hampus runs them.
