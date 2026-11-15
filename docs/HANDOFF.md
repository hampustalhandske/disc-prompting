# m1 handoff: scaffold and runner

## Review in five minutes

**Start here**
1. `src/disc_mirror/runner.py:40` (`estimate_cost`): the dry-run cost math that guards the $50 budget.
2. `src/disc_mirror/runner.py:63` (`run`): the live path. The prompt is exactly the version text as one user message, with no system prompt. It has never been run.
3. `src/disc_mirror/tasks.py:27` (`_parse`): the task-file contract every later milestone writes against.

**Verify**

    uv sync && uv run ruff check . && uv run pytest -q
    uv run disc-run --tasks tests/fixtures/tasks --config config/models.yaml --dry-run

**Needs you**
- Before any live run, set the real model ids and prices in `config/models.yaml`. The current values are placeholders written from memory.

## Summary

Charter item 4 (Runner) is done, along with the task-file contract from item 2. Task YAML is loaded and validated, cost is estimated fully offline, LiteLLM runs every task × version × model × sample into JSONL run records, and the `disc-run` command wraps it all.

## Decisions

- Hatchling is the build backend, approved by Hampus during review. It's needed only to install the `disc-run` command.
- Dry-run token counts use litellm's bundled tiktoken encoding for every model. Model-specific tokenizers downloaded files from Hugging Face.
- The judge-cost estimate uses the neutral prompt's tokens plus two answers at the tested model's `max_tokens`.
- `--out` stays on the CLI (one line); the default is `runs/<UTC timestamp>.jsonl`.
- `.claude/never-push` holds Hampus's email and is gitignored, so it never reaches the repo.
- The research dossier and the local `.claude/` workflow files stay untracked until Hampus decides.

## Remaining work

- Nice-to-have, not applied:
  - drop the unused re-exports in `src/disc_mirror/__init__.py` (-4 lines);
  - the test name `test_fixture_tasks_load_one_per_area` promises a per-area check it doesn't make.
- Charter wording to settle, which needs a re-approval:
  - Graders need the neutral answer's record too, not "only the runner's output record". Pairwise judging and mirroring both compare against neutral.
  - The local GloVe and CLIP downloads conflict with "fresh clone + `uv sync` + keys is all a real run needs". The fix is either a fetch script named in that check or a reworded check.
  - The cost line "(input tokens + `max_tokens`) × samples" reads as one price. The code prices input and output separately, which is correct.
- Next charter item: m2-task-set, about 6 tasks per area, 3 samples, plus an LLM style-classifier script that is built but not run.

## Notes

- `tests/fixtures/netblock/sitecustomize.py` blocks sockets in the `disc-run` subprocess and logs each attempt. The test fails if the blocker didn't load or any connection was attempted.
- `LITELLM_LOCAL_MODEL_COST_MAP` is set in `disc_mirror/__init__.py` and `tests/conftest.py`, so litellm stays offline on import.
- The README example `--tasks tasks` errors until m2 adds `tasks/`.
- Decisions for later milestones, from Hampus:
  - the open-weights model runs through OpenRouter;
  - Claude and Gemini are the judges;
  - GloVe and CLIP run locally;
  - the style check is a classifier plus Hampus's once-over;
  - Claude makes no API calls in v1.

## Numbers

    Branch m1-scaffold-runner vs 85abefa
      Production: +275 -0, net 275 of budget 800
      Tests:      +272 -0, net 272 (test/prod 0.99 on this branch)
      Repo:       275 production lines, 272 test lines (test/prod 0.99; band 0.5-0.7)
