# disc-mirror

Do LLMs mirror how you ask? Each task has a neutral question and D, i, S, C rewrites; the
runner sends each version, unchanged and with no system prompt, to the configured models.

The paper draft (background, hypotheses and method) is in [paper/draft.md](paper/draft.md).

## Setup

    uv sync
    uv run disc-fetch

`disc-fetch` downloads GloVe 840B 300d (first 200,000 lines, lowercase words) and CLIP
ViT-B-32 (QuickGELU, OpenAI weights) into `data/`, which git ignores; it skips what is already there.
A real run needs `uv sync`, `uv run disc-fetch` and the API keys in the environment
(`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`). The tests need none of it.

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

## Graders

    uv run disc-grade exact    --runs <jsonl> --tasks tasks
    uv run disc-grade mirror   --runs <jsonl> --tasks tasks
    uv run disc-grade pairwise --runs <jsonl> --tasks tasks --config config/models.yaml
    uv run disc-grade dat      --runs <jsonl> --tasks tasks
    uv run disc-grade svg      --runs <jsonl> --tasks tasks

Each reads run records and the task files, and grades only tasks whose `grader` matches.
`mirror` and `pairwise` skip a styled answer with no neutral partner or no output, and print
how many they skipped.

- **exact** (correctness tasks): the value after the last `ANSWER:` line is compared with the
  task's expected answer, ignoring case, space and a trailing period. A missing `ANSWER:` is
  wrong. A string match is the least biased measure when there is one right answer. Prints
  accuracy per model x version.
- **mirror** (exact_match and pairwise tasks): counts words, hedges and directives per 100
  words, exclamation marks and mean VADER sentence sentiment, then prints per model x style
  the mean difference from the same model's neutral answer to the same task and sample. It
  shows whether the style moved the reply in the direction the style predicts, with no judge.
- **pairwise** (quality tasks): each styled answer is paired with the neutral answer for the
  same sample and shown to every judge in both orders (A/B), at temperature 0. The judge sees
  only the neutral question and the two answers, never the style, task id or model name, so
  it picks on quality alone; running both orders cancels position bias. Prints the styled win
  rate (tie = 0.5) per model x style, overall and per judge, and the count of unparsed
  judgments. This makes live API calls; the default output is `runs/judge-<timestamp>.jsonl`.
- **dat** (creativity tasks): the Divergent Association Task (Olson et al., 2021). Each reply
  line is cleaned (list numbering, bullets, punctuation, case), and the first seven unique
  words found in GloVe 840B are scored as the mean cosine distance over all 21
  pairs x 100; a higher score means more semantically distant words. Replies with fewer than
  seven known words are not scored and are counted. Prints the mean per model x version.
- **svg** (svg tasks): the first SVG in the reply is checked against the task's constraints
  (share met), rendered with resvg, and compared with the neutral brief (without its format
  line) by CLIP ViT-B-32 (QuickGELU) cosine similarity x 100, the same text for all five versions. Prints
  per model x version the share that renders, the mean share of constraints met and the mean
  CLIP similarity. Needs `disc-fetch` first.
