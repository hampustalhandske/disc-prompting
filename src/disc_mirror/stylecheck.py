"""Checks that styled versions differ from neutral only in voice, not in content."""

import re
from collections import Counter

from disc_mirror.tasks import VERSIONS, Task

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_FORMAT_LINE_GRADERS = ("exact_match", "dat", "svg")


def _last_line(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def check_style_only(tasks: list[Task]) -> list[str]:
    """Returns one "<task id> <version>: <problem>" string per failure; empty when all pass.

    Each styled version must hold the same multiset of numbers as neutral. For exact_match, dat
    and svg tasks its last non-empty line must equal neutral's; for exact_match that line must
    contain "ANSWER:".
    """
    problems = []
    for t in tasks:
        neutral = t.versions["neutral"]
        base_numbers = Counter(_NUMBER.findall(neutral))
        base_last = _last_line(neutral)
        if t.grader == "exact_match" and "ANSWER:" not in base_last:
            problems.append(f"{t.id} neutral: last line lacks 'ANSWER:'")
        for v in VERSIONS[1:]:
            text = t.versions[v]
            if Counter(_NUMBER.findall(text)) != base_numbers:
                problems.append(f"{t.id} {v}: numbers differ from neutral")
            if t.grader in _FORMAT_LINE_GRADERS and _last_line(text) != base_last:
                problems.append(f"{t.id} {v}: last line differs from neutral")
            if t.grader == "exact_match" and "ANSWER:" not in _last_line(text):
                problems.append(f"{t.id} {v}: last line lacks 'ANSWER:'")
    return problems
