# Milestone 2: task-set

Serves: charter item 2 (Task set), plus the style-only check from "How we know it works"
Estimate: ~130 net production lines of a 400 budget (task YAMLs don't count)
Mode: away: open the PR after review and continue with the queue (m3 waits for the charter re-approval)

## Done when

1. `tasks/` holds 21 task files that load with `load_tasks("tasks")`: 6 correctness,
   3 creativity, 6 quality, 6 generation. Each has a rationale of at least one full sentence.
2. `check_style_only(load_tasks("tasks"))` returns `[]`, run by `tests/test_task_set.py`.
3. A planted break is caught: a fixture task whose D version changes a number, or whose
   last line differs from neutral's, makes `check_style_only` name that task and version.
4. `uv run disc-classify --help` runs, and with an injected completion function the
   classifier writes one record per task × version, the prompt holds no task id or
   version label, and the printed summary gives accuracy per version.
5. `uv run disc-run --tasks tasks --config config/models.yaml --dry-run` prints a total
   ≤ $50 with no network calls.
6. `uv run ruff check . && uv run pytest -q` passes.
7. Handoff nits: the unused re-exports in `src/disc_mirror/__init__.py` are gone, and
   `test_fixture_tasks_load_one_per_area` checks one task per area.

## Must not

- Add a dependency, service or paid API without asking.
- Make an API call anywhere, including the classifier: tests inject the completion function.
- Tell the model how to answer in any version: no tone, length or "be direct" requests.
  Only the asker's own voice changes. The fixed output-format line is the one exception
  and is identical in all five versions.
- Change the task-file or run-record contracts from m1.
- Write graders (m3, m4).

## Contracts

### Writing the five versions (task 1, read by the classifier in task 2)

The neutral version states the task plainly. Each rewrite is the same request written by
an asker with that style, following `docs/disc_prompting_research_dossier.md` §3
(constructive variants only), turned from instructions into the asker's voice:

- D: brief, outcome-first, impatient with preamble ("I need X. ...").
- i: warm, enthusiastic, personal, social context ("So excited about ...!").
- S: calm, patient, considerate, reassuring ("No rush at all, ...").
- C: precise, structured, cares about correctness and sources ("To be exact: ...").

Same facts, numbers and constraints in all five. The last line of every `exact_match`,
`dat` and `svg` version is the fixed format line, identical across the five:

- exact_match: `End your reply with a last line in the form ANSWER: <answer>` (the
  `<answer>` placeholder may be specialised per task, e.g. `ANSWER: <integer>`, still
  identical across versions). `expected.answer` is the canonical answer.
- dat: `Reply with exactly 10 nouns, one per line, and nothing else.`
- svg: `Reply with one complete SVG document inside a single svg code block.`

### SVG constraints (task 1 writes, m4's grader reads)

Each string in `expected.constraints` is one of:

```
element:<tag>              at least one <tag> element, e.g. element:circle
count:<tag>:<n>            at least n <tag> elements, e.g. count:rect:3
color:<#rrggbb>            some fill or stroke attribute equals this hex, lower case
text:<string>              a <text> element whose content contains <string>
viewbox:<w> <h>            the root viewBox ends in "<w> <h>", e.g. viewbox:200 200
```

Every constraint must be stated in all five versions of the brief, in words.

### `check_style_only(tasks: list[Task]) -> list[str]` (task 2, `src/disc_mirror/stylecheck.py`)

Returns one problem string per failure, `"<task id> <version>: <problem>"`, empty when
all pass. Compares each styled version with neutral:
- every task: the multiset of numbers (regex `\d+(?:[.,]\d+)?`) is equal;
- `exact_match`, `dat`, `svg`: the last non-empty line is identical;
- `exact_match`: that last line contains `ANSWER:`.

### Classifier (task 2, `src/disc_mirror/classify.py`)

```python
classify(tasks, judge: ModelSpec, out: Path, completion=litellm.completion, seed=0) -> list[dict]
summarize(records: list[dict]) -> dict[str, float]   # version -> share labelled correctly
```

One call per task × version, in an order shuffled with `seed`, temperature 0. The prompt
is one user message: a short description of the four styles and neutral, the question
text, and `Reply with one line: STYLE: <neutral|D|i|S|C>`. No task id, version or area.
Record (JSONL, one line per call):

```json
{"task_id": "...", "version": "D", "judge": "claude", "litellm_id": "...",
 "prompt": "...", "output": "...", "label": "D", "timestamp": "..."}
```

`label` is null when the reply has no parseable `STYLE:` line. CLI:
`disc-classify --tasks DIR --config FILE --judge NAME [--out FILE]` picks the judge by name
from `judges:`, writes `runs/classify-<UTC timestamp>.jsonl` by default, prints
`summarize` per version.

## Tasks

| # | Owner | Owned paths | Does | Done when |
|---|---|---|---|---|
| 1 | tasks | tasks/ | Write the 21 task YAMLs with rationales, following the two writing contracts | Done-when 1, 2 |
| 2 | code | src/disc_mirror/, pyproject.toml, README.md | `check_style_only`, the classifier and `disc-classify`, drop unused re-exports, README section on the task set and classifier | Done-when 4, 5 |
| 3 | tests | tests/ | Tests at the seams below, fixtures with planted breaks, fix the misleading test name | They run, and fail only where code is missing |

## Test seams

- `check_style_only` on fixture tasks: catches a changed number, a changed or missing
  format line, and a false alarm on a clean task.
- `check_style_only(load_tasks("tasks"))` and the area counts: catches a real task that
  drifts in content, and a missing area.
- `classify` with an injected completion: catches a leaked task id or version label in
  the prompt, a wrong record count, an unparsed or misparsed label, and a wrong summary.
- `disc-classify --help`: catches a missing entry point.

## Stop and ask

Every agent stops and reports BLOCKED when:
- a contract needs to change;
- the code or the cause doesn't match this plan;
- the budget checkpoint fires;
- a "Done when" can't be met as written.

## Queue

- m3-text-graders: ~350 (exact match, mirroring counts, pairwise judge); after m1 only
- m4-embed-graders: ~350 (DAT, SVG render + constraints + CLIP); after m1 only
- m5-paper: background and method draft, ~0 code lines; after m2–m4
