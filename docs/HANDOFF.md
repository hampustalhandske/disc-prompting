# m4 handoff: embedding graders

Decision: ship. Every review finding I agreed with is applied, including Should-fix and Nice-to-have items. Hampus decided the one measurement choice: DAT strips list markup before matching.

## Review in five minutes

**Start here**
1. `src/disc_mirror/graders/dat.py` (`known_words`, `dat_score`): the creativity score. Lines are cleaned ("1. Apple." becomes "apple"), repeats are dropped, and the first 7 known words are scored as mean cosine distance × 100.
2. `src/disc_mirror/graders/svg.py` (`extract_svg`, `_holds`, `load_clip`): what counts as the model's SVG, how each constraint is checked, and CLIP loaded from local weights only.
3. `docs/CHARTER.md` lines 31, 59 and 67: the three wording edits carried over from the m2 handoff.

**Verify**

    uv run ruff check . && uv run pytest -q

**Needs you**
- Re-approve the charter in your terminal, since its wording changed in this PR.
- None of this needs an API key. With `data/` fetched, `uv run disc-grade dat|svg --runs <jsonl> --tasks tasks` grades any run file locally.

## Summary

Charter item 3 (Graders), the local half, is done.
- `disc-grade dat` scores the creativity tasks on GloVe 840B.
- `disc-grade svg` reports, per model × version, whether the SVG renders (resvg), the share of constraints met, and CLIP similarity to the neutral brief.
- `disc-fetch` downloads both models into the git-ignored `data/`.

The charter's wording now matches the code, and mirroring's directive list no longer counts context-free words such as "now" and "use".

## Decisions

- **Dependencies:** resvg-py, open_clip_torch and torch, approved by Hampus. All three install with `uv sync` alone.
- **GloVe:** `disc-fetch` streams the 2 GB zip and stops after 200,000 lines. It keeps 65,608 lowercase words (76 MB).
- **CLIP:** ViT-B-32 with QuickGELU, the activation the OpenAI weights were trained with. The plain ViT-B-32 config gave a mismatch warning and slightly wrong scores. The weights are 577 MB.
- **DAT cleaning (Hampus):** list numbering, bullets, punctuation and case are stripped before matching, as in Olson's reference scorer. Repeated words are dropped.
- **CLIP target:** every version is scored against the same neutral brief, without its format line.
- **`count:<tag>:<n>` means at least n**, per the m2 contract. The first draft said exactly n.
- **No silent downloads:** `disc-grade svg` refuses to download and says to run `disc-fetch`.
- **Unknown constraint kinds:** a kind like `colour:` now raises an error instead of scoring as unmet.
- **Claude ran `disc-fetch` once**, with Hampus's OK, and graded hand-made answers with the real models:
  - DAT: a list of pets scored 39.99, a varied list 84.35, and the same varied list numbered with punctuation also 84.35.
  - CLIP: a correct traffic light scored 37.27 against its brief, a blue square 24.01.

## Remaining work

- Next: m5-paper, the background and method draft (charter item 1). It makes no API calls.
- The test/prod ratio on this branch is 0.48, just under the 0.5–0.7 band. That's the thin side, but every seam in the milestone is covered.

## Notes

- `data/` holds about 650 MB after `disc-fetch`. Rerunning skips each model that's already fully there.
- open_clip warns about an unauthenticated Hugging Face Hub during `disc-fetch` only. Grading loads the weights file directly and needs no network.
- `load_clip` caches the text embedding per brief, so each task's brief is encoded once.

## Numbers

    Branch m4-embed-graders vs 62404dd
      Production: +355 -3, net 352 of budget 400
      Tests:      +179 -9, net 170 (test/prod 0.48 on this branch)
      Repo:       1,129 production lines, 1,069 test lines (test/prod 0.95; band 0.5-0.7)
