"""Exact-match grader for correctness tasks.

Rationale: a correctness task has one right answer, so a string comparison is the least
biased measure. Each prompt asks for a last line `ANSWER: <value>`; the grader compares that
value with the task's expected answer, ignoring case, surrounding space and a trailing period.
A reply with no `ANSWER:` line counts as wrong, so a style that makes the model ramble or
skip the format shows up as lost accuracy.
"""

from disc_mirror.tasks import Task

MARKER = "ANSWER:"


def extract_answer(output: str | None) -> str | None:
    """Value after `ANSWER:` on the last non-empty line that has one; None if there is none."""
    for line in reversed((output or "").splitlines()):
        if MARKER in line:
            return line.split(MARKER, 1)[1].strip()
    return None


def _norm(text: str) -> str:
    return text.strip().casefold().removesuffix(".")


def grade_exact(records: list[dict], tasks: list[Task]) -> list[dict]:
    """One result per record whose task is graded by exact match."""
    expected = {t.id: t.expected["answer"] for t in tasks if t.grader == "exact_match"}
    results = []
    for r in records:
        if r["task_id"] not in expected:
            continue
        answer = extract_answer(r["output"])
        results.append(
            {
                "task_id": r["task_id"],
                "version": r["version"],
                "model": r["model"],
                "sample": r["sample"],
                "answer": answer,
                "correct": answer is not None and _norm(answer) == _norm(expected[r["task_id"]]),
            }
        )
    return results
