# DISC-Styled Questions: Do LLMs Mirror How You Ask?

## Goal

Hampus gets a ready-to-run, public study, plus the first half of an enjoyable paper, on
whether writing a *question* in a DISC style (D, i, S or C) carries into an LLM's answer
and makes it better. The model is never told to adopt a style. It is built as a GitHub
portfolio piece for research and AI-engineer roles.

## v1 scope

1. **Paper: background and method.** A Markdown draft with an introduction, related work
   (persona prompting, tone and politeness studies, the limits of DISC's validity, with
   checked citations), hypotheses, and the method as built.
2. **Task set.** Each task has a neutral version and D, i, S and C rewrites that keep the
   same content and change only the asker's style. Tasks cover four areas: correctness
   (maths, logic, facts with known answers), creativity (Divergent Association Task),
   open-ended quality (advice, writing, decisions) and generation (SVG image from a brief).
   Each task has a written reason for its inclusion. Each correctness task asks for its
   answer in a fixed format a script can extract (e.g. a last line `ANSWER: <x>`),
   identical across all five versions. Each task is one YAML file with `id`, `area`,
   `grader`, `rationale`, `versions` (neutral, D, i, S, C) and an `expected` block (answer
   for exact match, constraint list for SVG).
3. **Graders.** One script per measure, each with its rationale written down:
   correctness by exact match; creativity by embedding semantic distance; open-ended
   quality as blind pairwise win rate against the neutral answer, judged by two LLMs from
   different families; SVG by whether it renders, constraint checks and CLIP similarity
   to the brief; mirroring by text counts (length, hedges, exclamations, directives,
   sentiment), reported as each style's difference from the same model's neutral answer.
   Pairwise judging runs each pair in both orders; a tie counts 0.5. Every grader reads
   only the runner's output record and the task file. No human grading.
4. **Runner.** A thin script on LiteLLM (no custom provider adapters), driven by a config
   file (Claude, Gemini and one open-weights model, swappable). It writes one JSONL record
   per call: task id, version, model, sample index, prompt, raw output, token counts,
   timestamp. A `--dry-run` builds every prompt and prints a cost estimate without
   calling any API.
5. **Tests.** Each grader is tested on hand-made sample answers whose scores are known.

## Not in v1

- Running the experiment, or the results and discussion sections
- Telling the model to act in a DISC style
- Exaggerated-style variants of the questions
- Human raters or a user study
- Any claim that DISC is valid as psychology
- Multi-turn conversations
- A web app or demo
- Calling a separate image-generation model

## How we know it works

| Check | Passes when |
|---|---|
| Task coverage | Every task file has neutral, D, i, S and C versions and a rationale; all four areas are present |
| Style-only rewrites | For each correctness task, all five versions contain the same numbers, facts and asked-for output format (checked by script) |
| Graders | `uv run pytest` passes; each grader has at least one test on a sample answer with a known score |
| Dry run | `uv run <runner> --dry-run` prints the prompt count per model and a total cost estimate ≤ $50, and makes no network calls; token counts are estimated locally and prices per million tokens come from the model config file |
| Paper draft | The background and method sections exist; every citation links to a source that resolves |
| Reproducible | A fresh clone plus `uv sync` plus your API keys is all a real run needs (README states this) |

## Constraints

- Python 3.13 with uv, on a Mac
- Models are configured in one file; the list (Claude, Gemini, open-weights) may change
- $50 total API budget for later runs, generation and judging included
- Per-model token prices and `max_tokens` live in the model config file; the dry run
  estimates cost as (input tokens + `max_tokens`) × samples, plus judge calls
- Every dependency installs with `uv sync` alone, with no Homebrew or system libraries
  (for example, SVG renders through resvg-py, not cairosvg)
- API keys are provided by Hampus and never committed
- Public repo: nothing private goes in it

## Budget

Start budget: 800
Budget: 400

Net added production lines per milestone; tests don't count. The first milestone gets the
start budget, because it builds the scaffolding; every later one gets the budget. This is a
checkpoint, not a cap: when a milestone reaches it, Claude stops and asks whether to
simplify, split the milestone or raise the budget. To raise it for one milestone, run
`workflow budget N` in your terminal.

## Open questions

- Which open-weights model, and through which provider (OpenRouter, Together, Groq)? Blocks the runner config.
- Embeddings and CLIP: local (GloVe 840B for DAT, open_clip with torch; large downloads, fetched by a script and never committed) or API? Blocks the graders.
- Which two judge models, and can they overlap with the tested models? Blocks the quality grader.
- How many tasks per area, and how many samples per prompt within $50? Blocks the task set's size.
- How are the D, i, S and C rewrites checked to really read as those styles (an LLM classifier, or Hampus reviewing them once)? Blocks the task set.
