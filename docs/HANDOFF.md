# m2 handoff: task set

Decision: ship. All Must-fix and Should-fix items from the review are applied.

## Review in five minutes

**Start here**
1. `tasks/`: the 21 questions the whole study rests on. Read two or three tasks, comparing the neutral version against D, i, S and C. For example, `tasks/corr-04-train.yaml` and `tasks/qual-01-landlord-email.yaml`.
2. `src/disc_mirror/stylecheck.py:17` (`check_style_only`): the script check that the rewrites keep the same numbers and the same format line as neutral.
3. `src/disc_mirror/classify.py:30` (`classify`): the blind style classifier. It is built and tested with a fake model, and has never been run.

**Verify**

    uv run ruff check . && uv run pytest -q
    uv run disc-run --tasks tasks --config config/models.yaml --dry-run

**Needs you**
- Skim the rewrites once, as the charter's style check asks. Judgement calls the wording sweep left as they are:
  - D openers that restate the question ("I need a pen count", "I need the weekday", "I need a call on this");
  - `corr-01` C: "listed price" and "precisely $14";
  - `qual-05` C: "verified product facts";
  - i versions that add a personal situation (a new flat, a niece, game night).
- Later, run `uv run disc-classify --tasks tasks --config config/models.yaml --judge claude`. It makes about 105 short calls, a few cents. A style with low accuracy needs its rewrites redone before the real run.

## Summary

Charter item 2 (Task set) is done. There are 21 tasks: 6 correctness, 3 DAT, 6 open-ended quality and 6 SVG. Each one has a rationale and neutral, D, i, S and C versions that change only the asker's voice. The "style-only rewrites" check from "How we know it works" runs in the tests (`tests/test_task_set.py`). The blind classifier `disc-classify` is ready for the open question of whether the styles really read as D, i, S and C.

## Decisions

- Creativity has 3 DAT tasks instead of 6, because DAT is a single standard test and more variants would repeat each other. (Hampus approved the plan.)
- The rewrites change only the asker's voice. No version asks for a tone, a length or a form of answer. The fixed format line is the one shared instruction. A review sweep removed seven phrases that added facts or asked for an answer form.
- SVG constraints use a small grammar (`element:`, `count:`, `color:`, `text:`, `viewbox:`). It is a contract that m4's grader reads (docs/MILESTONE.md).
- Classifier calls are left out of the dry-run cost, since they come to a few cents.
- Hampus kept the test lines even though the ratio is high (2.57 on this branch). Later milestones aim for lean tests.
- `disc-classify` lives in `cli.py` next to `disc-run`, and the package re-exports nothing.
- `.claude/settings.json` (which enables the workflow plugin) is committed. The research dossier stays untracked.

## Remaining work

- Next: `fix/runner-hardening`, from the m1 code review that m1 missed. It retries API errors and resumes from an existing `--out`, keeps null replies and survives missing usage, restores `.env*` and a global `*.bin` ignore, rejects duplicate model names and bad config types, refuses a live run over budget, and derives `STYLES` from `VERSIONS`.
- Charter wording to settle before m3 (needs `workflow approve`): graders read the neutral record too; the GloVe/CLIP fetch script in the "Reproducible" check; input and output are priced separately in the cost line.
- Nice-to-have, not applied: five duplicate or dead test inputs (`tests/test_stylecheck.py:44`, `:69`, `:83`; `tests/test_classify.py:110`).
- Then m3-text-graders and m4-embed-graders, in either order.

## Notes

- Correctness answers: corr-01 21, corr-02 Dev, corr-03 Au, corr-04 12:10, corr-05 6, corr-06 Thursday. The weekday and the letter count were checked with Python.
- The dry run on `tasks/` gives 315 prompts per model and a total of $12.68, still at m1's placeholder prices.
- The classifier picks its model from `judges:` by name. Its reply must hold a `STYLE: <label>` line; anything else gets `label: null` and counts as wrong.

## Numbers

    Branch m2-task-set vs f5c29f4
      Production: +145 -17, net 128 of budget 400
      Tests:      +334 -5, net 329 (test/prod 2.57 on this branch)
      Repo:       403 production lines, 601 test lines (test/prod 1.49; band 0.5-0.7)
