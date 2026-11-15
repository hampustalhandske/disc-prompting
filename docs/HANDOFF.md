# m3 handoff: text graders

Decision: ship. At Hampus's request, every reviewer finding I agreed with is applied, Should-fix and Nice-to-have included. The few I skipped are listed below with reasons.

## Review in five minutes

**Start here**
1. `src/disc_mirror/graders/pairwise.py` (`judge_pairs`): the blind judge, which spends most of the judging budget. Check that the prompt holds only the neutral question and two answers, and that A/B maps back to styled/neutral after the swap.
2. `src/disc_mirror/graders/mirror.py` (`HEDGES`, `DIRECTIVES`, `text_features`): the word lists behind the mirroring numbers. They are a first choice, not a validated lexicon.
3. `src/disc_mirror/runner.py` (`load_jsonl`, `run`): resume now survives a line cut off by a crash, and refuses to mix two setups in one `--out`.

**Verify**

    uv run ruff check . && uv run pytest -q

**Needs you**
- Skim the hedge and directive lists in `mirror.py`. Common words such as "now", "first", "use" and "set" count as directives, so the directive count will run high on ordinary prose. Trim them if you agree.
- `disc-grade pairwise` has never made a live call. Try it on a small run file before the real run. It makes 2 orders × 2 judges = 4 calls per styled quality answer.

## Summary

Charter item 3 (Graders), the text half:
- `disc-grade exact`: correctness by exact match on the `ANSWER:` line.
- `disc-grade mirror`: words, hedges, directives, exclamations and per-sentence VADER sentiment, as each style's difference from the same model's neutral answer.
- `disc-grade pairwise`: blind judging against the neutral answer, in both orders, by both judges. A tie counts 0.5, and win rates are given overall and per judge.

Each grader has its rationale in its module docstring and in the README.

## Decisions

- Sentiment uses vaderSentiment 3.3.2 (approved by Hampus). Each sentence is scored and the scores are averaged, because the score for a long text as a whole drifts toward ±1.
- The judge sees the neutral question, so it stays blind to style. Styled sample s is paired with neutral sample s.
- Mirroring covers exact_match and pairwise tasks only. DAT and SVG replies have fixed formats.
- Both graders share `graders.pair_with_neutral` (from the quality review). It skips a styled answer that has no neutral partner or a None output, and `disc-grade` prints how many it skipped.
- Review fixes outside the m3 files, applied here at Hampus's request:
  - runner resume survives a partial last line and refuses a changed setup;
  - `load_config` type-checks model and judge fields;
  - classifier calls retry on API errors;
  - a dead parametrize value in `test_dry_run.py` is gone.
- Code-review findings not applied, with reasons:
  - The budget guard charges the full run on resume. This is conservative on purpose, and lowering the budget to resume isn't a real workflow.
  - `.gitignore` uses `.env*` and a global `*.bin`. That was Hampus's decision in PR #3.
  - The runner records a None reply as null. That was kept on purpose in PR #3, and the graders now skip and count those replies.
  - Resume reads the whole file into memory. A full run is about 1,000 short lines.

## Remaining work

- Next: m4-embed-graders, about 350 lines. It covers DAT with GloVe; SVG rendering, constraints and CLIP; and `disc-fetch` for the GloVe and CLIP weights.
- m4 also takes the three charter wording edits from the m2 handoff, which need Hampus's re-approval afterwards:
  - graders read the neutral record too;
  - `disc-fetch` is named in the "Reproducible" check;
  - input and output are priced separately in the cost line.
- Then m5-paper.

## Notes

- `disc-grade` tables are tab-separated. The mirror and pairwise tables end with a `skipped` count, and pairwise also prints an `unparsed` count.
- Before appending, `load_jsonl` trims a last line that has no newline. So if a hand-edited file lacks its final newline, its last record is dropped and that call is made again.
- The m3 `/code-review` reviewed the code merged in PR #3, not this branch. Each of its findings was checked and handled as listed above.

## Numbers

    Branch m3-text-graders vs 42966f5
      Production: +350 -5, net 345 of budget 400
      Tests:      +223 -7, net 216 (test/prod 0.63 on this branch)
      Repo:       777 production lines, 899 test lines (test/prod 1.16; band 0.5-0.7)
