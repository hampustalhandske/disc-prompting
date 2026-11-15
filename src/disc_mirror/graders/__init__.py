"""Text graders: exact match, mirroring counts and blind pairwise judging."""


def pair_with_neutral(records: list[dict], task_ids: set[str]) -> tuple[list[tuple], int]:
    """Pairs each styled record of the given tasks with its neutral record.

    The neutral record is the same model's, for the same task and sample. Returns the
    (styled, neutral) pairs in sorted order, and the count of styled records left out because
    no neutral record exists or either output is None.
    """
    by_key = {
        (r["task_id"], r["version"], r["model"], r["sample"]): r
        for r in records
        if r["task_id"] in task_ids
    }
    pairs, skipped = [], 0
    for (task_id, version, model, sample), styled in sorted(by_key.items()):
        if version == "neutral":
            continue
        neutral = by_key.get((task_id, "neutral", model, sample))
        if neutral is None or styled["output"] is None or neutral["output"] is None:
            skipped += 1
        else:
            pairs.append((styled, neutral))
    return pairs, skipped
