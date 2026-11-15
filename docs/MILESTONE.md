# Milestone 4: embed-graders

Serves: charter item 3 (Graders), the local half: creativity by embedding semantic distance
(DAT) and SVG by render, constraint checks and CLIP similarity to the brief; plus the three
charter wording edits from the m2 handoff
Estimate: ~280 net production lines of a 400 budget
Mode: with you: show the review to Hampus before the PR

## Done when

1. `uv sync` installs resvg-py, open_clip_torch and torch with no Homebrew or system libraries.
2. `uv run disc-fetch` downloads GloVe 840B 300d and CLIP ViT-B-32 (QuickGELU, OpenAI weights) into
   `data/`, which git ignores. The tests never call it.
3. `uv run disc-grade dat --runs <jsonl> --tasks tasks` prints the mean DAT score per
   model × version, with the count of replies too short to score.
4. `uv run disc-grade svg --runs <jsonl> --tasks tasks` prints, per model × version, the
   share that renders, the mean share of constraints met and the mean CLIP similarity.
5. Each grader has at least one test on a hand-made answer with a known score, using tiny
   fake vectors and a fake CLIP scorer (no download, no network).
6. Each grader's rationale is in its module docstring and in the README "Graders" section.
7. `docs/CHARTER.md` carries the three wording edits (listed under Contracts), and the README
   says a real run needs `uv sync`, `uv run disc-fetch` and the API keys.
8. The mirroring directive list drops the context-free words "now", "first", "next",
   "start", "stop", "use", "ask", "tell", "set" and "send".
9. `uv run ruff check . && uv run pytest -q` passes.

## Must not

- Add a dependency beyond resvg-py, open_clip_torch and torch (approved by Hampus) without asking.
- Make an API call anywhere. Downloads happen only in `disc-fetch`, which tests never run.
- Commit anything under `data/`.
- Import torch or open_clip when grading anything but SVG (keeps `disc-grade exact` fast).
- Change the task-file, run-record or SVG-constraint contracts, the runner or the tasks.
- Train or fine-tune anything: GloVe and CLIP are used as published.

## Contracts

All graders read run records (the m1 shape) plus the task files, and grade only records
whose task has the matching `grader`. A record with `output: None` scores as unscored
(DAT) or not rendered (SVG).

### Local model files (task 3 writes, tasks 1 and 2 read)

```
data/glove/words.txt     one word per line; lowercase alphabetic words from the first
                         200,000 lines of glove.840B.300d.txt, in file order
data/glove/vectors.npy   float32 array, shape (len(words), 300), row i = words.txt line i
data/clip/               open_clip cache_dir for ViT-B-32-quickgelu, pretrained="openai"
```

### DAT (task 1, `src/disc_mirror/graders/dat.py`)

```python
load_glove(directory="data/glove") -> dict[str, numpy.ndarray]
dat_score(words: list[str], vectors: dict) -> float | None
    # Olson et al. (2021): clean each line (list numbering, bullets, punctuation, case),
    # keep unique words found in vectors, take the first 7; None if fewer than 7. Score = mean cosine distance over all 21 pairs x 100.
grade_dat(records, tasks, vectors) -> list[dict]
    # {"task_id", "version", "model", "sample", "valid_words": int, "score": float | None}
```

### SVG (task 2, `src/disc_mirror/graders/svg.py`)

```python
extract_svg(output: str | None) -> str | None
    # contents of the first ```svg (or ```xml / bare ```) block holding <svg; else the first
    # <svg ...>...</svg> span; None if neither
check_constraints(svg: str, constraints: list[str]) -> list[bool]
    # one bool per constraint, grammar from m2; tags match without namespace; color:
    # matches fill or stroke attributes and fill:/stroke: in style attributes, case-folded;
    # unparsable XML fails every constraint
render_png(svg: str) -> bytes | None        # resvg-py; None when rendering fails
load_clip(cache_dir="data/clip") -> Callable[[bytes, str], float]
    # imports open_clip lazily; returns cosine similarity x 100 of image vs text
grade_svg(records, tasks, clip: Callable[[bytes, str], float]) -> list[dict]
    # {"task_id", "version", "model", "sample", "renders": bool,
    #  "constraints": float (share met, 0 when no svg), "clip": float | None (None unless rendered)}
```

The CLIP text is the task's **neutral** brief without its last (format) line, the same for
all five versions, so every version is scored against the same target.

### CLI (task 3, `src/disc_mirror/cli.py`, consumes tasks 1 and 2)

`disc-grade dat|svg --runs FILE --tasks DIR` (added to the existing subcommands; `--glove`
and `--clip-cache` override the default directories). `disc-fetch [--data DIR]` downloads
both models, skipping any already present, and prints where they went. Fetch code lives in
`src/disc_mirror/fetch.py`.

### Charter wording (task 3, `docs/CHARTER.md`)

1. Item 3: "Every grader reads only the runner's output record and the task file." →
   "Every grader reads only run records (including the same model's neutral answer) and the
   task file."
2. "Reproducible" check: "A fresh clone plus `uv sync` plus your API keys is all a real run
   needs" → "A fresh clone plus `uv sync`, `uv run disc-fetch` (GloVe and CLIP weights) and
   your API keys is all a real run needs".
3. Constraints: "estimates cost as (input tokens + `max_tokens`) × samples" → "estimates cost
   as (input tokens × input price + `max_tokens` × output price) × samples".

## Tasks

| # | Owner | Owned paths | Does | Done when |
|---|---|---|---|---|
| 1 | dat | src/disc_mirror/graders/dat.py | GloVe loading, DAT score, `grade_dat` | Done-when 3, 6 (its part) |
| 2 | svg | src/disc_mirror/graders/svg.py | SVG extraction, constraint checks, render, CLIP, `grade_svg` | Done-when 4, 6 (its part) |
| 3 | cli | src/disc_mirror/cli.py, src/disc_mirror/fetch.py, src/disc_mirror/graders/mirror.py, pyproject.toml, README.md, CLAUDE.md, docs/CHARTER.md | `disc-grade dat\|svg`, `disc-fetch`, charter edits, README, map, directive trim | Done-when 2, 7, 8 |
| 4 | tests | tests/ | Tests at the seams below, with fake vectors and a fake CLIP | They run, and fail only where code is missing |

The orchestrator adds the three dependencies (`uv add`, checked with `uv sync`) on the
branch before the build, so every task builds against them.

## Test seams

- `dat_score` on 3-d fake vectors: catches a wrong pair count or scale, words past the 7th
  used, unknown words counted, and a score given with fewer than 7 valid words.
- `extract_svg`: catches a missed fenced block, prose around the SVG kept, and a reply with
  no SVG returning text.
- `check_constraints`: catches each grammar form wrongly matched (namespaced tags, a colour
  only in `style`, upper-case hex, a `count:` one short, a `viewbox:` mismatch) and
  unparsable XML passing.
- `grade_svg` with a fake CLIP: catches CLIP called on an unrendered SVG, a styled version
  scored against its own text instead of the neutral brief, and the format line in the text.
- `disc-grade dat` on a fixture run file with fake vectors in `tmp_path`: catches a missing
  entry point or table.
- The import guard: catches `disc_mirror.cli` importing torch.

## Stop and ask

Every agent stops and reports BLOCKED when:
- a contract needs to change;
- the code or the cause doesn't match this plan;
- the budget checkpoint fires;
- a "Done when" can't be met as written.

## Queue

- m5-paper: background and method draft, ~0 code lines; after m2–m4
