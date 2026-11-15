"""Divergent Association Task (DAT) grader for creativity tasks.

Rationale: a creativity task asks for 10 unrelated words. Following Olson et al. (2021), the
grader cleans each line (drops list numbering, bullets and surrounding punctuation, and
lowercases), keeps the unique words found in the GloVe 840B 300d vocabulary, takes the
first 7, and scores the mean cosine distance over all 21 pairs times 100.
A higher score means the words are semantically further apart. A reply with fewer than 7
known words has no score (None) and is counted as too short to score. The measure is
embedding distance only: it needs no judge model, so it carries no judge bias.
"""

import re
from itertools import combinations
from pathlib import Path

import numpy as np

from disc_mirror.tasks import Task

WORDS_NEEDED = 7
_MARKER = re.compile(r"^\s*(?:\d+\s*[.):]|[-*+\u2022])\s*")
_EDGES = re.compile(r"^[^a-z]+|[^a-z]+$")


def known_words(lines: list[str], vectors: dict) -> list[str]:
    """Cleaned, unique words of `lines` that have a vector, in order of first appearance.

    Cleaning drops a leading list number or bullet ("1.", "2)", "-", "*"), lowercases, and
    strips non-letters from both ends, so "1. Apple." becomes "apple".
    """
    cleaned = (_EDGES.sub("", _MARKER.sub("", line).lower()) for line in lines)
    return list(dict.fromkeys(w for w in cleaned if w in vectors))


def load_glove(directory: str | Path = "data/glove") -> dict[str, np.ndarray]:
    """Map each word in `words.txt` to its row of `vectors.npy`."""
    directory = Path(directory)
    words = directory.joinpath("words.txt").read_text(encoding="utf-8").splitlines()
    matrix = np.load(directory / "vectors.npy")
    return dict(zip(words, matrix, strict=True))


def dat_score(words: list[str], vectors: dict) -> float | None:
    """Mean pairwise cosine distance x 100 of the first 7 known words; None if under 7."""
    chosen = known_words(words, vectors)[:WORDS_NEEDED]
    if len(chosen) < WORDS_NEEDED:
        return None
    unit = [np.asarray(vectors[w], dtype=np.float64) for w in chosen]
    unit = [v / np.linalg.norm(v) for v in unit]
    distances = [1.0 - float(a @ b) for a, b in combinations(unit, 2)]
    return float(np.mean(distances) * 100)


def grade_dat(records: list[dict], tasks: list[Task], vectors: dict) -> list[dict]:
    """One result per record whose task is graded by DAT; one word per output line."""
    dat_ids = {t.id for t in tasks if t.grader == "dat"}
    results = []
    for r in records:
        if r["task_id"] not in dat_ids:
            continue
        lines = (r["output"] or "").splitlines()
        valid = known_words(lines, vectors)
        results.append(
            {
                "task_id": r["task_id"],
                "version": r["version"],
                "model": r["model"],
                "sample": r["sample"],
                "valid_words": len(valid),
                "score": dat_score(lines, vectors),
            }
        )
    return results
