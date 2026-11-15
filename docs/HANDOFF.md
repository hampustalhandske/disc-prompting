# m5 handoff: paper draft

Decision: ship. All four review findings (method statements that didn't match the code) are fixed. The code review also turned up issues in m4 code that's already merged. They're listed under Remaining work for a separate fix branch.

## Review in five minutes

**Start here**
1. `paper/draft.md:97` (Limits of DISC): this section rests on one peer-reviewed study, Martinussen et al. (2001), checked against its abstract only.
2. `paper/draft.md:150` (Hypotheses H1-H5): these hypotheses are the study's claims. Every later result gets read against them.
3. `paper/draft.md:179` (Method): it describes the code as built, and each number in it was checked against `tasks/`, `config/models.yaml` and the graders.

**Verify**

    uv run ruff check . && uv run pytest -q

**Needs you**
- Read the draft as its author. Check the voice, and whether the hypotheses are the ones you want to test.
- Decide on the m4 grader fixes under Remaining work: open a `fix/grader-hardening` branch, or leave them.
- `docs/disc_prompting_research_dossier.md` is still untracked in the working tree. Keep it out of the repo, or move it somewhere private.

## Summary

Charter item 1 (Paper: background and method) is done, so every v1 charter item is now built.
- `paper/draft.md` has an introduction, related work and hypotheses H1-H5. The related work covers persona prompting, tone and politeness, mirroring and sycophancy, the limits of DISC, and the measures this study builds on.
- It also has a Method section that matches the code.
- The README links the draft.

## Decisions

- **Writing style:** at Hampus's request, the draft was written to the humanizer skill and given a final pass with it.
- **Dossier:** it was used only as a list of leads and is never committed. A review compared 8-word runs of the draft against it, and the only overlap is one reference title.
- **Citation checks:** a cite-check agent fetched every source and graded 44 claims, with none Inaccurate. A second pass re-checked the seven claims that were fixed. Changes from the checks:
  - "Independent evidence for DISC is thin" was dropped, because one study can't carry it.
  - "small" was dropped from H2.
  - H2 now says "factual and benchmark questions", to match Yin et al.
  - The judge temperature (0) is now described as set in code.
- **Martinussen link:** the DOI plus the PubMed abstract. Both block automated clients, so the claims were checked against the same abstract on the Europe PMC API.
- **Not cited:** Price (2017) and Owen et al., because neither could be read.
- **Review fixes to Method:**
  - The most-constrained SVG task is the traffic light (5 constraints), not the smiley.
  - The skip rule is "neutral missing or either output None", and empty replies are still graded.
  - Graders also read local model files, and pairwise calls the judges.
  - The judge's `WINNER:` reply is one line, and the last one counts.

## Remaining work

- **m4 code-review findings** (merged code, outside this PR):
  1. `graders/dat.py:35` `load_glove` raises a bare FileNotFoundError and doesn't say "run disc-fetch", which the binding decisions require. (Confirmed.)
  2. `graders/svg.py:155` and `grade_dat` score a `None` output (no content from the provider) as a failure instead of skipping and counting it. (Confirmed.)
  3. `graders/svg.py:44` `color:` misses colours set in a `<style>` block, `#f00` shorthand, `rgb()` and named colours.
  4. `graders/dat.py:22`: a one-word preamble such as "Sure!" counts as a DAT word, and non-ASCII words get cut.
  5. Not verified:
     - `fetch.py` writes files without an atomic rename, so an interrupted fetch can leave files that later runs skip.
     - `clip_weights` takes the first snapshot it finds.
     - Constraint grammar is checked at grade time, not by `load_tasks`.
- `tasks/gen-06-smiley.yaml` rationale says it has "the most constraints in the set" and "a curved path". Both are wrong: it has 4 constraints, and `element:path` doesn't check for a curve. I couldn't edit tasks in this milestone.
- Next: v1 is complete. The remaining steps are the live runs Hampus does, then results and discussion (parked).

## Notes

- Wiley, PNAS, AAAI, Springer and PubMed block bots. Europe PMC's REST API serves abstracts and full open-access text.
- When graders, tasks or config change, update `paper/draft.md` Method too. The map in CLAUDE.md says so.

## Numbers

    Branch m5-paper vs b894f99
      Production: +0 -0, net 0 of budget 400
      Tests:      +0 -0, net 0 (test/prod n/a on this branch)
      Repo:       1,129 production lines, 1,069 test lines (test/prod 0.95; band 0.5-0.7)
