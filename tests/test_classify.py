import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import FIXTURE_TASKS, ROOT, VERSIONS, model

IDS = ["zq-alpha-77", "zq-beta-78", "zq-gamma-79"]


@pytest.fixture
def tasks():
    """Three tasks whose version texts hold neither their id, their area nor a version label."""
    from disc_mirror.tasks import Task

    out = []
    for n, tid in enumerate(IDS):
        texts = {v: f"Question {n} asked in voice {k}." for k, v in enumerate(VERSIONS)}
        out.append(
            Task(
                id=tid, area="quality", grader="pairwise", rationale="Fixture.",
                versions=texts, expected={},
            )
        )
    return out


@pytest.fixture
def judge():
    from disc_mirror.config import ModelSpec

    return ModelSpec(**model("judge-a", 50))


def make_completion(tasks, answer):
    """Fake litellm.completion; `answer(true_version, call_index)` gives the reply text."""
    import litellm

    by_text = {t.versions[v]: v for t in tasks for v in VERSIONS}
    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        prompt = kwargs["messages"][0]["content"]
        true = next(v for text, v in by_text.items() if text in prompt)
        reply = answer(true, len(calls) - 1)
        return litellm.ModelResponse(
            choices=[{"message": {"role": "assistant", "content": reply}}]
        )

    completion.calls = calls
    return completion


def perfect(true, _):
    return f"STYLE: {true}"


def test_one_record_per_task_and_version_with_contract_fields(tasks, judge, tmp_path):
    from disc_mirror.classify import classify

    out = tmp_path / "c.jsonl"
    comp = make_completion(tasks, perfect)
    records = classify(tasks, judge, out, completion=comp)
    assert len(records) == len(comp.calls) == 15
    lines = [json.loads(x) for x in out.read_text().splitlines()]
    assert lines == records
    assert {(r["task_id"], r["version"]) for r in lines} == {
        (t.id, v) for t in tasks for v in VERSIONS
    }
    for r in lines:
        assert set(r) == {
            "task_id", "version", "judge", "litellm_id", "prompt", "output", "label", "timestamp",
        }
        assert r["judge"] == "judge-a" and r["litellm_id"] == "openai/judge-a"
        assert r["label"] == r["version"]


def test_prompt_is_one_user_message_that_leaks_no_id_area_or_version_label(tasks, judge, tmp_path):
    from disc_mirror.classify import classify

    comp = make_completion(tasks, perfect)
    classify(tasks, judge, tmp_path / "c.jsonl", completion=comp)
    questions = {t.versions[v] for t in tasks for v in VERSIONS}
    frames = set()
    for call in comp.calls:
        assert call["temperature"] == 0
        assert call["model"] == "openai/judge-a"
        assert len(call["messages"]) == 1 and call["messages"][0]["role"] == "user"
        prompt = call["messages"][0]["content"]
        assert "STYLE: <neutral|D|i|S|C>" in prompt
        assert not any(tid in prompt for tid in IDS)
        assert "quality" not in prompt and "pairwise" not in prompt
        question = next(q for q in questions if q in prompt)
        frames.add(prompt.replace(question, ""))
    assert len(frames) == 1, "prompt text outside the question differs between calls"


def test_call_order_is_shuffled_and_follows_the_seed(tasks, judge, tmp_path):
    from disc_mirror.classify import classify

    def order(seed):
        comp = make_completion(tasks, perfect)
        recs = classify(tasks, judge, tmp_path / f"{seed}.jsonl", completion=comp, seed=seed)
        return [(r["task_id"], r["version"]) for r in recs]

    sorted_order = [(t.id, v) for t in tasks for v in VERSIONS]
    assert order(0) == order(0)
    assert order(0) != sorted_order
    assert order(0) != order(1)


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("STYLE: S", "S"),
        ("Thinking it over.\nSTYLE: i", "i"),
        ("STYLE: neutral", "neutral"),
        ("It feels warm and personal.", None),
        ("STYLE: formal", None),
    ],
)
def test_label_is_parsed_from_the_style_line_or_null(tasks, judge, tmp_path, reply, expected):
    from disc_mirror.classify import classify

    comp = make_completion(tasks, lambda t, i: reply)
    records = classify(tasks, judge, tmp_path / "c.jsonl", completion=comp)
    assert {r["label"] for r in records} == {expected}
    assert all(r["output"] == reply for r in records)


def test_summary_is_accuracy_per_version_and_counts_unparsed_as_wrong(tasks, judge, tmp_path):
    from disc_mirror.classify import classify, summarize

    def answer(true, _):
        return {
            "D": "STYLE: D",  # 3 of 3
            "i": "STYLE: S",  # 0 of 3
            "S": "no label",  # 0 of 3, unparsed
            "C": "STYLE: C",
            "neutral": "STYLE: neutral",
        }[true]

    comp = make_completion(tasks, answer)
    records = classify(tasks, judge, tmp_path / "c.jsonl", completion=comp)
    assert summarize(records) == {"neutral": 1.0, "D": 1.0, "i": 0.0, "S": 0.0, "C": 1.0}


def test_summary_of_partial_hits():
    from disc_mirror.classify import summarize

    recs = [
        {"version": "D", "label": "D"}, {"version": "D", "label": "i"},
        {"version": "D", "label": None}, {"version": "D", "label": "D"},
    ]
    assert summarize(recs)["D"] == 0.5


def test_disc_classify_entry_point_prints_help():
    exe = Path(sys.executable).parent / "disc-classify"
    proc = subprocess.run([str(exe), "--help"], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "--judge" in proc.stdout and "--tasks" in proc.stdout


def test_classify_main_prints_accuracy_per_version(make_config, tmp_path, monkeypatch, capsys):
    import disc_mirror.cli as cli

    records = [{"version": v, "label": v if v != "i" else None} for v in VERSIONS]
    monkeypatch.setattr(cli, "classify", lambda *a, **k: records)
    config = make_config([model("m", 10)], [model("judge-a", 50)])
    cli.classify_main(
        ["--tasks", str(FIXTURE_TASKS), "--config", str(config), "--judge", "judge-a",
         "--out", str(tmp_path / "c.jsonl")]
    )
    lines = capsys.readouterr().out.splitlines()
    assert "D: 1.00" in lines and "i: 0.00" in lines
