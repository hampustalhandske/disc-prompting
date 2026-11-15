# Milestone 5: paper

Serves: charter item 1 (Paper: background and method): a Markdown draft with an
introduction, related work (persona prompting, tone and politeness studies, the limits of
DISC's validity, with checked citations), hypotheses, and the method as built
Estimate: ~0 net production lines of a 400 budget (Markdown only, ~350 lines of prose)
Mode: away: open the PR after review and continue with the queue

## Done when

1. `paper/draft.md` has the sections Introduction, Related work, Hypotheses and Method.
2. Related work covers persona prompting, tone and politeness studies, and the limits of
   DISC's validity.
3. Method matches the code as built: 21 tasks in 4 areas (6 correctness, 3 DAT, 6 quality,
   6 SVG), style-only rewrites, the prompt is only the version text with no system prompt,
   models, judges, samples and temperature from `config/models.yaml`, and each grader with
   its rationale.
4. Every citation links to a source that resolves and supports the claim it backs, as
   graded by the cite-check agent (every claim Verified).
5. README links the draft; `uv run ruff check . && uv run pytest -q` still passes.

## Must not

- Add a dependency, service or paid API without asking.
- Change code, tasks, config or tests.
- Commit `docs/disc_prompting_research_dossier.md` or copy its text. It may serve only as a
  list of leads; every citation is re-found and read at its primary source.
- Write results, discussion or any claim about findings (not in v1).
- Claim DISC is valid as psychology.
- Use the dossier's parked designs (exaggerated variants, instructing the model to adopt a
  style) as this study's method or hypotheses.

## Tasks

| # | Owner | Owned paths | Does | Done when |
|---|---|---|---|---|
| 1 | paper | paper/draft.md, README.md | Writes the draft from the charter, the code, the tasks and the config; adds a README link | Done when 1-3 and 5 hold; citations ready for cite-check |

## Test seams

- None in code. The cite-check agent checks each citation against its source; the
  orchestrator checks the method's numbers against `tasks/` and `config/models.yaml`.

## Stop and ask

Every agent stops and reports BLOCKED when:
- a contract needs to change;
- the code or the cause doesn't match this plan;
- the budget checkpoint fires;
- a "Done when" can't be met as written.

## Queue

- (empty: v1 is complete after m5)
