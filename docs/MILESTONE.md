# Milestone 3: text-graders

Serves: charter item 3 (Graders), the three text measures: correctness by exact match,
mirroring by text counts, open-ended quality by blind pairwise judging
Estimate: ~320 net production lines of a 400 budget
Mode: away: open the PR after review and continue with the queue

## Done when

1. `uv run disc-grade exact --runs <jsonl> --tasks tasks` prints accuracy per model × version,
   on a hand-made run file, with no network calls.
2. `uv run disc-grade mirror --runs <jsonl> --tasks tasks` prints, per model × style, each
   feature's mean difference from the same model's neutral answers.
3. `uv run disc-grade pairwise --runs <jsonl> --tasks tasks --config config/models.yaml`
   is one command away from a live judge run; with an injected completion function it
   writes 2 judge records (both orders) per judge × styled answer, and prints win rates
   per model × style, overall and per judge.
4. Each grader has at least one test on a hand-made sample answer with a known score.
5. Each grader's rationale is written down: in its module docstring and in a README
   "Graders" section.
6. `uv run ruff check . && uv run pytest -q` passes.

## Must not

- Add a dependency, service or paid API without asking (vaderSentiment approved by Hampus).
- Make an API call anywhere: tests inject the completion function.
- Change the task-file or run-record contracts, the runner, or the tasks.
- Show the judge which answer is styled, the style name, the task id or the model name.
- Write the DAT or SVG graders (m4).
- Add tests beyond the seams below: the repo's test/prod ratio is 1.49 against a 0.5–0.7 band.

## Contracts

All graders read run records (the m1 shape) from a JSONL file plus the task files. Only
records whose task has the matching `grader` are graded; others are ignored.

### Exact match (task 1, `src/disc_mirror/graders/exact.py`)

```python
extract_answer(output: str | None) -> str | None
    # value after "ANSWER:" on the last non-empty line that has one; None if none
grade_exact(records: list[dict], tasks: list[Task]) -> list[dict]
    # one per exact_match record:
    # {"task_id", "version", "model", "sample", "answer": str | None, "correct": bool}
```

Comparison: both sides stripped, case-folded, trailing `.` removed. A missing answer is wrong.

### Mirroring (task 1, `src/disc_mirror/graders/mirror.py`)

```python
text_features(output: str | None) -> dict[str, float]
    # {"words", "hedges", "exclamations", "directives", "sentiment"}
    # hedges and directives per 100 words, from fixed word lists in the module;
    # exclamations = count of "!"; sentiment = mean VADER compound over sentences, in [-1, 1]
mirror_deltas(records: list[dict], tasks: list[Task]) -> dict[tuple[str, str], dict[str, float]]
    # (model, style) -> feature -> mean over (task, sample) of styled minus neutral
```

Graded on `exact_match` and `pairwise` tasks only (DAT and SVG replies are fixed formats).

### Pairwise judge (task 2, `src/disc_mirror/graders/pairwise.py`)

```python
judge_pairs(records, tasks, judges: list[ModelSpec], out: str | Path,
            completion=litellm.completion) -> list[dict]
win_rates(judgments: list[dict]) -> dict[tuple[str, str, str], float]
    # (model, style, judge or "all") -> styled win rate vs neutral; tie = 0.5;
    # unparsed (winner null) left out of the rate
```

For each `pairwise` task × model × style × sample `s`, the styled answer for sample `s` is
paired with the neutral answer for sample `s`, then judged in both orders by every judge,
at temperature 0. The prompt is one user message: the task's **neutral** question,
`Answer A`, `Answer B`, and `Reply with one line: WINNER: <A|B|TIE>`. Calls already in `out`
are skipped (resume, as in the runner). Record:

```json
{"task_id": "...", "model": "claude", "style": "D", "sample": 0, "judge": "gemini-judge",
 "litellm_id": "...", "styled_first": true, "prompt": "...", "output": "...",
 "winner": "styled", "timestamp": "..."}
```

`winner` is `styled`, `neutral`, `tie` or null when the reply has no `WINNER:` line.

### CLI (task 1, `src/disc_mirror/cli.py`, consumes task 2)

`disc-grade exact|mirror|pairwise --runs FILE --tasks DIR`, plus for pairwise `--config FILE
[--out FILE]` (default `runs/judge-<UTC timestamp>.jsonl`). Prints one table each; pairwise
also prints the count of unparsed judgments.

## Tasks

| # | Owner | Owned paths | Does | Done when |
|---|---|---|---|---|
| 1 | text | src/disc_mirror/graders/__init__.py, graders/exact.py, graders/mirror.py, src/disc_mirror/cli.py, pyproject.toml, uv.lock, README.md, CLAUDE.md | Exact match, mirroring, `disc-grade` with all three subcommands, README "Graders" section, map entries | Done-when 1, 2, 5 |
| 2 | judge | src/disc_mirror/graders/pairwise.py | Pairwise judge and win rates | Done-when 3 |
| 3 | tests | tests/ | Tests at the seams below, on hand-made answers with known scores | They run, and fail only where code is missing |

## Test seams

- `grade_exact`: catches an answer taken from the wrong line, case or a trailing period
  marking a right answer wrong, and a missing `ANSWER:` counted as right.
- `text_features` / `mirror_deltas`: catches a wrong count on a known sentence, and a delta
  taken against another model's neutral or across tasks.
- `judge_pairs` with an injected completion: catches a wrong call count (orders × judges),
  the style, model or task id leaking into the prompt, a styled answer always in slot A,
  A/B mapped to the wrong winner after the swap, and a resumed call made twice.
- `win_rates`: catches a tie not counted as 0.5 and unparsed judgments counted as losses.
- `disc-grade exact` on a fixture run file: catches a missing entry point or table.

## Stop and ask

Every agent stops and reports BLOCKED when:
- a contract needs to change;
- the code or the cause doesn't match this plan;
- the budget checkpoint fires;
- a "Done when" can't be met as written.

## Queue

- m4-embed-graders: ~350 (DAT, SVG render + constraints + CLIP, `disc-fetch` for GloVe and
  CLIP weights) plus the three charter wording edits from the m2 handoff; after m1 only
- m5-paper: background and method draft, ~0 code lines; after m2–m4
