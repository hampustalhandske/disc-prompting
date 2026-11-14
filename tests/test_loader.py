import pytest

from conftest import FIXTURE_TASKS

BAD_TASKS = {
    "missing_version_key": (lambda d: d["versions"].pop("S"), "S"),
    "empty_version_text": (lambda d: d["versions"].update(C=""), "C"),
    "missing_area": (lambda d: d.pop("area"), "area"),
    "unknown_area": (lambda d: d.update(area="poetry"), "area"),
    "missing_grader": (lambda d: d.pop("grader"), "grader"),
    "unknown_grader": (lambda d: d.update(grader="vibes"), "grader"),
    "missing_rationale": (lambda d: d.pop("rationale"), "rationale"),
    "exact_match_without_answer": (lambda d: d.update(expected={}), "expected"),
    "svg_constraints_not_a_list": (
        lambda d: d.update(grader="svg", expected={"answer": "42"}),
        "expected",
    ),
}


def test_fixture_tasks_load_one_per_area():
    from disc_mirror import load_tasks

    tasks = load_tasks(FIXTURE_TASKS)
    assert len(tasks) == 4


@pytest.mark.parametrize("mutate,field", BAD_TASKS.values(), ids=BAD_TASKS.keys())
def test_invalid_task_fails_loading_naming_file_and_field(task_dir_with, mutate, field):
    from disc_mirror import load_tasks

    d, f = task_dir_with(mutate)
    with pytest.raises(Exception) as err:
        load_tasks(d)
    assert f.name in str(err.value)
    assert field in str(err.value)
