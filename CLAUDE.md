# disc-prompting

## Map

Parts
- `src/disc_mirror/tasks.py`: task YAML loader and validation (`load_tasks`)
- `src/disc_mirror/config.py`: model config loader (`load_config`)
- `src/disc_mirror/runner.py`: offline cost estimate (`estimate_cost`) and live LiteLLM runner (`run`)
- `src/disc_mirror/stylecheck.py`: style-only check on rewrites (`check_style_only`)
- `src/disc_mirror/classify.py`: blind DISC style classifier (`classify`, `summarize`)
- `src/disc_mirror/cli.py`: the `disc-run` and `disc-classify` commands
- `tasks/`: the 21 real tasks (6 correctness, 3 DAT, 6 quality, 6 SVG)
- `config/models.yaml`: tested models, judges, prices, samples, budget
- `tests/fixtures/`: one task per area, and the socket blocker for no-network tests

Contracts (source of truth: docs/MILESTONE.md of m1 at e76a0c2, and of m2)
- Task file: one YAML per task (`id` = file name, `area`, `grader`, `rationale`, `versions` neutral/D/i/S/C, `expected`). Read by the loader and graders.
- Rewrites: only the asker's voice changes; same facts and numbers; `exact_match`, `dat`, `svg` versions end in the identical fixed format line (m2).
- SVG constraints: `element:<tag>`, `count:<tag>:<n>`, `color:<#rrggbb>`, `text:<s>`, `viewbox:<w> <h>`. Written in m2, read by the m4 grader.
- Run record: one JSONL line per call (task_id, version, model, litellm_id, sample, temperature, max_tokens, prompt, output, input_tokens, output_tokens, timestamp). Written by `run`, read by the m3/m4 graders.

Commands
- Test and lint: `uv run ruff check . && uv run pytest -q`
- Dry run: `uv run disc-run --tasks tasks --config config/models.yaml --dry-run`
- Style classifier (Hampus runs it): `uv run disc-classify --tasks tasks --config config/models.yaml --judge claude`

Binding decisions
- The prompt is only the version text: no system prompt, no style instruction.
- The dry run and the tests never touch the network.
- Claude makes no live API calls in v1; Hampus runs them.
- Keep tests lean (test/prod band 0.5-0.7) without cutting real coverage.
