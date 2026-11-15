# disc-prompting

## Map

Parts
- `src/disc_mirror/tasks.py`: task YAML loader and validation (`load_tasks`)
- `src/disc_mirror/config.py`: model config loader (`load_config`)
- `src/disc_mirror/runner.py`: offline cost estimate (`estimate_cost`) and live LiteLLM runner (`run`)
- `src/disc_mirror/stylecheck.py`: style-only check on rewrites (`check_style_only`)
- `src/disc_mirror/classify.py`: blind DISC style classifier (`classify`, `summarize`)
- `src/disc_mirror/cli.py`: the `disc-run`, `disc-classify` and `disc-grade` commands
- `src/disc_mirror/fetch.py`: the `disc-fetch` command (GloVe and CLIP weights into `data/`)
- `src/disc_mirror/graders/`: `exact.py` (`grade_exact`), `mirror.py` (`text_features`, `mirror_deltas`), `pairwise.py` (`judge_pairs`, `win_rates`), `dat.py` (`known_words`, `dat_score`, `grade_dat`), `svg.py` (`extract_svg`, `check_constraints`, `render_png`, `load_clip`, `grade_svg`)
- `tasks/`: the 21 real tasks (6 correctness, 3 DAT, 6 quality, 6 SVG)
- `config/models.yaml`: tested models, judges, prices, samples, budget
- `paper/draft.md`: paper background and method (m5); its Method must match the code, so update it when graders, tasks or config change
- `tests/fixtures/`: one task per area, and the socket blocker for no-network tests

Contracts (source of truth: docs/MILESTONE.md of m1 at e76a0c2, of m2, m3 and m4)
- Task file: one YAML per task (`id` = file name, `area`, `grader`, `rationale`, `versions` neutral/D/i/S/C, `expected`). Read by the loader and graders.
- Rewrites: only the asker's voice changes; same facts and numbers; `exact_match`, `dat`, `svg` versions end in the identical fixed format line (m2).
- SVG constraints: `element:<tag>`, `count:<tag>:<n>`, `color:<#rrggbb>`, `text:<s>`, `viewbox:<w> <h>`. Written in m2, read by the m4 grader.
- Run record: one JSONL line per call (task_id, version, model, litellm_id, sample, temperature, max_tokens, prompt, output, input_tokens, output_tokens, timestamp). Written by `run`, read by the m3/m4 graders. Resume skips recorded calls and refuses a changed setup.
- Judge record: one JSONL line per judge call (task_id, model, style, sample, judge, litellm_id, styled_first, prompt, output, winner styled/neutral/tie/null, timestamp). Written by `judge_pairs`, read by `win_rates` (m3).
- Local model files (m4): `data/glove/words.txt` + `vectors.npy` (float32, 300-d), `data/clip/` (open_clip cache, ViT-B-32-quickgelu, OpenAI weights). Written by `disc-fetch`, read by the DAT and SVG graders; never committed.
- Graders pair a styled answer with the same model's neutral answer for the same task and sample (`graders.pair_with_neutral`); pairs with a missing partner or a None output are skipped and counted.

Commands
- Test and lint: `uv run ruff check . && uv run pytest -q`
- Dry run: `uv run disc-run --tasks tasks --config config/models.yaml --dry-run`
- Fetch models once: `uv run disc-fetch` (~650 MB into `data/`)
- Grade: `uv run disc-grade exact|mirror|pairwise|dat|svg --runs <jsonl> --tasks tasks [--config config/models.yaml]` (pairwise makes live calls; Hampus runs it)
- Style classifier (Hampus runs it): `uv run disc-classify --tasks tasks --config config/models.yaml --judge claude`

Binding decisions
- The prompt is only the version text: no system prompt, no style instruction.
- The dry run and the tests never touch the network.
- Claude makes no live API calls in v1; Hampus runs them.
- Only `disc-fetch` downloads; graders load local files and fail with "run disc-fetch" when they're missing.
- Keep tests lean (test/prod band 0.5-0.7) without cutting real coverage.
