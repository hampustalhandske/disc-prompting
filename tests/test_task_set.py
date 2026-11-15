import re
from collections import Counter

import pytest
from conftest import ROOT

TASKS = ROOT / "tasks"
FORMAT_LINES = {
    "dat": "Reply with exactly 10 nouns, one per line, and nothing else.",
    "svg": "Reply with one complete SVG document inside a single svg code block.",
}
ANSWER_LINE = re.compile(r"^End your reply with a last line in the form ANSWER: .+")


@pytest.fixture(scope="module")
def tasks():
    from disc_mirror.tasks import load_tasks

    return load_tasks(TASKS)


def test_task_set_has_21_tasks_split_6_3_6_6_by_area(tasks):
    counts = Counter(t.area for t in tasks)
    assert counts == {"correctness": 6, "creativity": 3, "quality": 6, "generation": 6}
    assert len(tasks) == 21


def test_every_rationale_is_a_full_sentence(tasks):
    for t in tasks:
        r = t.rationale.strip()
        assert len(r.split()) >= 4 and r[-1] in ".!?", t.id


def test_real_task_versions_differ_only_in_style(tasks):
    from disc_mirror.stylecheck import check_style_only

    assert check_style_only(tasks) == []


def test_fixed_format_line_is_the_contract_text_in_every_version(tasks):
    checked = 0
    for t in tasks:
        for v, text in t.versions.items():
            last = [ln for ln in text.splitlines() if ln.strip()][-1].strip()
            if t.grader in FORMAT_LINES:
                assert last == FORMAT_LINES[t.grader], f"{t.id} {v}"
                checked += 1
            elif t.grader == "exact_match":
                assert ANSWER_LINE.match(last), f"{t.id} {v}"
                checked += 1
    assert checked > 0
