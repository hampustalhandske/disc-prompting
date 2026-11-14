# Milestone 1: scaffold-runner

Serves: charter item 4 (Runner) and the task-file contract from item 2
Estimate: ~300 net production lines of an 800 start budget
Mode: away: open the PR after review and continue with the queue

## Done when

1. `uv sync` on a fresh clone installs everything with no Homebrew or system libraries.
2. `uv run ruff check . && uv run pytest -q` passes.
3. `uv run disc-run --tasks tests/fixtures/tasks --config config/models.yaml --dry-run`
   prints prompt count and estimated cost per model, judge cost, and a total, and makes
   no network calls (a test proves this with networking blocked).
4. A task file that misses a version, an `area`, a `grader` or `rationale`, or has an
   `expected` block that doesn't fit its grader, fails loading with a message naming the
   file and the field.
5. A live run (not executed in this milestone) is one command away: the same command
   without `--dry-run` writes one JSONL record per call in the shape below.
6. `.gitignore` and `.claude/never-push` exist.

## Must not

- Add a dependency beyond litellm, pyyaml, pytest and ruff without asking.
- Add a system prompt or any style instruction: the version text is the whole prompt.
- Call any API, in code paths run by tests or by `--dry-run`. Nobody runs a live call in v1: Hampus sets up the endpoints and runs it later.
- Write real tasks (that's m2) or graders (m3, m4).

## Contracts

### Task file (YAML, one task per file)

Produced by m2 authors and test fixtures, consumed by the loader in task 1.

```yaml
id: corr-math-01                 # unique, matches the file name
area: correctness                # correctness | creativity | quality | generation
grader: exact_match              # exact_match | dat | pairwise | svg
rationale: "Why this task is in the set."
versions:                        # all five required, non-empty strings
  neutral: "..."
  D: "..."
  i: "..."
  S: "..."
  C: "..."
expected:                        # exact_match: {answer: str}
  answer: "42"                   # svg: {constraints: [str, ...]}; dat, pairwise: {} or omitted
```

### Model config (`config/models.yaml`)

Produced by task 1, consumed by task 2's tests.

```yaml
budget_usd: 50
samples: 3
temperature: 0.7
models:                          # tested models
  - name: claude
    litellm_id: anthropic/<model-id>
    max_tokens: 1024
    price_in_per_mtok: 0.0       # USD per million input tokens
    price_out_per_mtok: 0.0
judges:                          # same shape; used for pairwise cost only in m1
  - name: ...
```

### Run record (JSONL, one line per call)

Produced by the runner, consumed by every grader in m3 and m4.

```json
{"task_id": "corr-math-01", "version": "D", "model": "claude",
 "litellm_id": "anthropic/...", "sample": 0, "temperature": 0.7, "max_tokens": 1024,
 "prompt": "...", "output": "...", "input_tokens": 41, "output_tokens": 230,
 "timestamp": "2026-11-14T10:00:00Z"}
```

### Dry-run cost

Per model: for every task × 5 versions × `samples`, (local token count of the prompt ×
input price + `max_tokens` × output price). Judges: for every `pairwise` task × tested
model × 4 styles × `samples` × 2 orders × each judge, with input = both answers at
`max_tokens` each plus the prompt, and output = the judge's `max_tokens`. Token counts come
from `litellm.token_counter`, run locally.

## Tasks

| # | Owner | Owned paths | Does | Done when |
|---|---|---|---|---|
| 1 | runner | pyproject.toml, uv.lock, src/disc_mirror/, config/models.yaml, README.md | Task loader + validation, config loader, dry-run cost estimate, live runner on LiteLLM writing run records, `disc-run` CLI | Done-when items 1, 3, 4, 5 |
| 2 | tests | tests/ | Fixture tasks (one per area) and tests at the seams below | They run, and fail only where code is missing |

## Test seams

- `load_tasks(dir)`: catches a missing version, an unknown area or grader, or an `expected` block that doesn't fit its grader, getting through silently.
- `estimate_cost(tasks, config)`: catches wrong multiplication (versions, samples, both orders, judges) and judge cost charged on non-pairwise tasks.
- `disc-run --dry-run`: catches any network call (sockets blocked in the test) and missing totals in the output.
- `run(tasks, config, out, completion=...)`: with an injected completion function, catches a record missing a field, a system message or anything but the version text in the prompt, and a wrong record count.

## Stop and ask

Every agent stops and reports BLOCKED when:
- a contract needs to change;
- the code or the cause doesn't match this plan;
- the budget checkpoint fires;
- a "Done when" can't be met as written.

## Decisions (2026-11-14, from Hampus)

- Open-weights model via OpenRouter (a current Llama or Qwen instruct model).
- Judges: Claude + Gemini; self-preference is reported, not hidden.
- Embeddings and CLIP run locally: GloVe for DAT, open_clip + torch for SVG, fetched by a script, never committed.
- Task set: ~6 tasks per area, 3 samples per prompt.
- Style check: a blind LLM classifier script (built, not run) plus Hampus skimming the rewrites once.
- No API calls are made by Claude anywhere in v1.

## Queue

- m2-task-set: ~150 lines (style-only checker) plus the task YAMLs and rationales; needs the open questions on task count and style check
- m3-text-graders: ~350 (exact match, mirroring counts, pairwise judge); after m1
- m4-embed-graders: ~350 (DAT, SVG render + constraints + CLIP); needs the embeddings/CLIP decision; after m1
- m5-paper: background and method draft, ~0 code lines; after m2–m4
