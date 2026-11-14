"""Task files: one YAML per task, validated on load."""

from dataclasses import dataclass
from pathlib import Path

import yaml

AREAS = ("correctness", "creativity", "quality", "generation")
GRADERS = ("exact_match", "dat", "pairwise", "svg")
VERSIONS = ("neutral", "D", "i", "S", "C")


@dataclass(frozen=True)
class Task:
    id: str
    area: str
    grader: str
    rationale: str
    versions: dict[str, str]
    expected: dict


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse(path: Path) -> Task:
    """Builds one Task; raises ValueError naming the file and the bad field."""

    def fail(field: str, problem: str) -> ValueError:
        return ValueError(f"{path}: field '{field}' {problem}")

    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    if raw.get("id") != path.stem:
        raise fail("id", f"must equal the file name {path.stem!r}, got {raw.get('id')!r}")
    if raw.get("area") not in AREAS:
        raise fail("area", f"must be one of {AREAS}, got {raw.get('area')!r}")
    if raw.get("grader") not in GRADERS:
        raise fail("grader", f"must be one of {GRADERS}, got {raw.get('grader')!r}")
    if not _nonempty_str(raw.get("rationale")):
        raise fail("rationale", "must be a non-empty string")
    versions = raw.get("versions")
    if not isinstance(versions, dict):
        raise fail("versions", "must be a mapping")
    for v in VERSIONS:
        if not _nonempty_str(versions.get(v)):
            raise fail(f"versions.{v}", "must be a non-empty string")

    grader = raw["grader"]
    expected = raw.get("expected") or {}
    if grader == "exact_match":
        if set(expected) != {"answer"} or not _nonempty_str(expected["answer"]):
            raise fail("expected", "for exact_match must be {answer: <non-empty string>}")
    elif grader == "svg":
        cons = expected.get("constraints") if set(expected) == {"constraints"} else None
        if not cons or not isinstance(cons, list) or not all(_nonempty_str(c) for c in cons):
            raise fail("expected", "for svg must be {constraints: [<non-empty string>, ...]}")
    elif expected:
        raise fail("expected", f"for {grader} must be empty or omitted")

    return Task(
        id=raw["id"],
        area=raw["area"],
        grader=grader,
        rationale=raw["rationale"],
        versions={v: versions[v] for v in VERSIONS},
        expected=expected,
    )


def load_tasks(directory: str | Path) -> list[Task]:
    """Loads every *.yaml task in a directory, sorted by file name."""
    return [_parse(p) for p in sorted(Path(directory).glob("*.yaml"))]
