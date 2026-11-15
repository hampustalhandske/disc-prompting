import json

import pytest
from conftest import FIXTURE_TASKS, VERSIONS, model, rec, run_cli


def task(tid, grader, expected=None, tag="q"):
    from disc_mirror.tasks import Task

    return Task(
        id=tid, area="quality", grader=grader, rationale="Fixture.",
        versions={v: f"Question {tag} in voice {v}." for v in VERSIONS},
        expected=expected or {},
    )


# exact match

def test_exact_match_reads_last_answer_line_and_ignores_case_period_and_missing():
    from disc_mirror.graders.exact import extract_answer, grade_exact

    assert extract_answer("ANSWER: 1\nthinking\nANSWER: 42\n\n") == "42"
    assert extract_answer("the answer is 42") is None
    assert extract_answer(None) is None

    tasks = [task("t-num", "exact_match", {"answer": "42"}),
             task("t-word", "exact_match", {"answer": "Paris"}),
             task("t-other", "pairwise")]
    records = [
        rec("t-num", "neutral", "ANSWER: 1\nANSWER: 42\n", sample=0),  # last line wins
        rec("t-num", "neutral", "ANSWER: 42\nANSWER: 1\n", sample=1),  # first line is wrong
        rec("t-num", "neutral", "It is 42, no marker.", sample=2),     # missing is wrong
        rec("t-num", "neutral", None, sample=3),
        rec("t-word", "D", "ANSWER:  paris. ", sample=0),              # case, spaces, period
        rec("t-other", "D", "ANSWER: whatever"),                       # other grader ignored
    ]
    graded = grade_exact(records, tasks)
    assert [(g["task_id"], g["sample"], g["answer"], g["correct"]) for g in graded] == [
        ("t-num", 0, "42", True), ("t-num", 1, "1", False),
        ("t-num", 2, None, False), ("t-num", 3, None, False),
        ("t-word", 0, "paris.", True),
    ]
    assert {"task_id", "version", "model", "sample", "answer", "correct"} == set(graded[0])


# mirroring

def test_text_features_count_a_known_sentence():
    from disc_mirror.graders.mirror import text_features

    f = text_features("Perhaps this works. You must go!")
    assert f["words"] == 6
    assert f["exclamations"] == 1
    assert f["hedges"] == pytest.approx(100 / 6)
    assert f["directives"] == pytest.approx(100 / 6)
    assert f["sentiment"] == 0  # neither sentence carries VADER sentiment
    assert text_features("I love this. It is wonderful!")["sentiment"] > 0.5


def test_mirror_delta_uses_own_model_neutral_per_task_and_sample():
    from disc_mirror.graders.mirror import mirror_deltas

    def words(n):
        return "w " * n

    tasks = [task("t1", "exact_match", {"answer": "1"}), task("t2", "pairwise")]
    records = [
        rec("t1", "neutral", words(2), "A"), rec("t1", "D", words(4), "A"),
        rec("t2", "neutral", words(10), "A"), rec("t2", "D", words(11), "A"),
        rec("t1", "neutral", words(6), "B"), rec("t1", "D", words(7), "B"),
    ]
    deltas = mirror_deltas(records, tasks)
    assert deltas[("A", "D")]["words"] == pytest.approx(1.5)  # mean of +2 and +1
    assert deltas[("B", "D")]["words"] == pytest.approx(1.0)


# pairwise judge

STYLED, NEUTRAL = "STYLEDANSWERTEXT", "PLAINANSWERTEXT"


@pytest.fixture
def pair_setup():
    from disc_mirror.config import ModelSpec

    tasks = [task("zq-pair-91", "pairwise", tag="pairq")]
    records = [rec("zq-pair-91", "neutral", NEUTRAL, "claudeqx"),
               rec("zq-pair-91", "D", STYLED, "claudeqx")]
    judges = [ModelSpec(**model("judge-a", 50)), ModelSpec(**model("judge-b", 50))]
    return tasks, records, judges


def make_completion(pick):
    """Fake completion; `pick` is "styled", "neutral" or "tie" and the reply names the slot."""
    import litellm

    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        prompt = kwargs["messages"][0]["content"]
        styled_slot = "A" if prompt.index(STYLED) < prompt.index(NEUTRAL) else "B"
        other = "B" if styled_slot == "A" else "A"
        reply = {"styled": styled_slot, "neutral": other, "tie": "TIE"}[pick]
        return litellm.ModelResponse(
            choices=[{"message": {"role": "assistant", "content": f"WINNER: {reply}"}}]
        )

    completion.calls = calls
    return completion


def test_judge_pairs_calls_both_orders_per_judge_without_leaks_and_maps_winner(
    pair_setup, tmp_path
):
    from disc_mirror.graders.pairwise import judge_pairs

    tasks, records, judges = pair_setup
    comp = make_completion("styled")
    out = tmp_path / "j.jsonl"
    result = judge_pairs(records, tasks, judges, out, completion=comp)

    assert len(comp.calls) == 4 == len(result)  # 2 orders x 2 judges
    assert [json.loads(x) for x in out.read_text().splitlines()] == result
    assert {(r["judge"], r["styled_first"]) for r in result} == {
        (j, o) for j in ("judge-a", "judge-b") for o in (True, False)
    }
    assert all(r["winner"] == "styled" for r in result)  # A/B mapped through the swap
    for call in comp.calls:
        assert call["temperature"] == 0
        assert len(call["messages"]) == 1 and call["messages"][0]["role"] == "user"
        prompt = call["messages"][0]["content"]
        assert tasks[0].versions["neutral"] in prompt
        assert tasks[0].versions["D"] not in prompt
        for leak in ("claudeqx", "zq-pair-91"):
            assert leak not in prompt
        assert "WINNER: <A|B|TIE>" in prompt


def test_judge_pairs_never_judges_a_missing_output(pair_setup, tmp_path):
    from disc_mirror.graders.pairwise import judge_pairs

    tasks, records, judges = pair_setup
    records = [dict(r, output=None) if r["version"] != "neutral" else r for r in records]
    comp = make_completion("styled")
    assert judge_pairs(records, tasks, judges, tmp_path / "j.jsonl", completion=comp) == []
    assert comp.calls == []


def test_judge_pairs_skips_calls_already_in_the_out_file(pair_setup, tmp_path):
    from disc_mirror.graders.pairwise import judge_pairs

    tasks, records, judges = pair_setup
    out = tmp_path / "j.jsonl"
    judge_pairs(records, tasks, judges, out, completion=make_completion("tie"))
    comp = make_completion("tie")
    judge_pairs(records, tasks, judges, out, completion=comp)
    assert comp.calls == []
    assert len(out.read_text().splitlines()) == 4


def test_win_rates_count_tie_as_half_and_leave_unparsed_out():
    from disc_mirror.graders.pairwise import win_rates

    def j(judge, winner, sample):
        return {"task_id": "t", "model": "m", "style": "D", "sample": sample,
                "judge": judge, "winner": winner}

    rates = win_rates([
        j("a", "styled", 0), j("a", "tie", 1), j("a", None, 2),
        j("b", "neutral", 0), j("b", "styled", 1),
    ])
    assert rates[("m", "D", "a")] == pytest.approx(0.75)   # (1 + 0.5) / 2, null left out
    assert rates[("m", "D", "b")] == pytest.approx(0.5)
    assert rates[("m", "D", "all")] == pytest.approx(0.625)  # 2.5 / 4


# CLI

def test_disc_grade_exact_prints_accuracy_per_model_and_version(tmp_path):
    runs = tmp_path / "runs.jsonl"
    runs.write_text("\n".join(json.dumps(r) for r in [
        rec("corr-fix-01", "neutral", "ANSWER: 42"),
        rec("corr-fix-01", "D", "ANSWER: 7"),
    ]))
    net_log = tmp_path / "net.log"
    p = run_cli(
        "exact", "--runs", str(runs), "--tasks", str(FIXTURE_TASKS),
        cmd="disc-grade", block_network=True, net_log=net_log,
    )
    assert p.returncode == 0, p.stderr
    rows = {tuple(x.split("\t")[:2]): x.split("\t")[2] for x in p.stdout.splitlines()}
    assert rows[("alpha", "neutral")] == "1.00"
    assert rows[("alpha", "D")] == "0.00"
    assert not net_log.exists() or net_log.read_text() == ""
