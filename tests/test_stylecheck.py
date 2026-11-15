import dataclasses

import pytest

FORMAT = "End your reply with a last line in the form ANSWER: <integer>"


def make_task(**versions):
    """An exact_match task whose five versions share numbers and the format line."""
    from disc_mirror.tasks import Task

    base = {
        "neutral": f"Add 12 and 30.5 for me.\n{FORMAT}",
        "D": f"I need 12 plus 30.5. Now.\n{FORMAT}",
        "i": f"So excited to add 12 and 30.5!\n{FORMAT}",
        "S": f"No rush at all, add 12 and 30.5.\n{FORMAT}",
        "C": f"To be exact: add 12 and 30.5.\n{FORMAT}",
    }
    base.update(versions)
    return Task(
        id="t-one", area="correctness", grader="exact_match",
        rationale="Fixture.", versions=base, expected={"answer": "42"},
    )


def check(task):
    from disc_mirror.stylecheck import check_style_only

    return check_style_only([task])


def test_clean_task_raises_no_false_alarm():
    # Different wording, reordered numbers and trailing blank lines are all allowed.
    task = make_task(D=f"30.5 and 12, summed. Quick.\n{FORMAT}\n\n")
    assert check(task) == []


def test_changed_number_names_task_and_version():
    problems = check(make_task(D=f"I need 12 plus 31.5. Now.\n{FORMAT}"))
    assert len(problems) == 1
    assert problems[0].startswith("t-one D:")


def test_dropped_number_is_caught():
    problems = check(make_task(S=f"No rush at all, add 12.\n{FORMAT}"))
    assert [p.split(":")[0] for p in problems] == ["t-one S"]


def test_changed_format_line_is_caught():
    problems = check(make_task(C="To be exact: add 12 and 30.5.\nANSWER: <integer>"))
    assert [p.split(":")[0] for p in problems] == ["t-one C"]


def test_missing_format_line_is_caught():
    problems = check(make_task(i="So excited to add 12 and 30.5!"))
    assert problems and {p.split(":")[0] for p in problems} == {"t-one i"}


def test_exact_match_last_line_without_answer_marker_is_caught():
    bare = "Reply with the sum."
    task = make_task(
        neutral=f"Add 12 and 30.5.\n{bare}", D=f"12 plus 30.5.\n{bare}",
        i=f"Add 12 and 30.5!\n{bare}", S=f"Add 12 and 30.5.\n{bare}",
        C=f"Add 12 and 30.5.\n{bare}",
    )
    assert check(task) != []
    assert all(p.startswith("t-one") for p in check(task))


def test_pairwise_task_may_end_differently():
    task = dataclasses.replace(
        make_task(D="Write 3 lines on rain. Go."),
        grader="pairwise", expected={},
        versions={
            "neutral": "Write 3 lines on rain.", "D": "Write 3 lines on rain. Go.",
            "i": "Write 3 lines on rain, so fun!", "S": "No rush, write 3 lines on rain.",
            "C": "To be exact: write 3 lines on rain.",
        },
    )
    assert check(task) == []


@pytest.mark.parametrize("grader", ["dat", "svg"])
def test_dat_and_svg_need_identical_last_line(grader):
    fmt = "Reply with exactly 10 nouns, one per line, and nothing else."
    versions = {v: f"Words, {v}.\n{fmt}" for v in ["neutral", "D", "i", "S", "C"]}
    task = dataclasses.replace(
        make_task(), grader=grader, expected={}, versions=versions
    )
    if grader == "svg":
        task = dataclasses.replace(task, expected={"constraints": ["element:circle"]})
    # The words contain no digits, but "10" appears in the shared format line.
    assert check(task) == []
    versions["S"] = "Words, S.\nReply with 10 nouns."
    problems = check(dataclasses.replace(task, versions=versions))
    assert [p.split(":")[0] for p in problems] == ["t-one S"]
