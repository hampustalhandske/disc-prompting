import json

import pytest
import yaml
from conftest import FIXTURE_TASKS, VERSIONS, model

RECORD_FIELDS = {
    "task_id", "version", "model", "litellm_id", "sample", "temperature",
    "max_tokens", "prompt", "output", "input_tokens", "output_tokens", "timestamp",
}


@pytest.fixture
def fake_completion():
    """A stand-in for litellm.completion that records its calls and returns a canned reply."""
    import litellm

    calls = []

    def completion(**kwargs):
        calls.append(kwargs)
        return litellm.ModelResponse(
            choices=[{"message": {"role": "assistant", "content": "reply"}}],
            usage=litellm.Usage(prompt_tokens=7, completion_tokens=3, total_tokens=10),
        )

    completion.calls = calls
    return completion


def test_run_writes_one_complete_record_per_call_with_only_the_version_text(
    make_config, fake_completion, tmp_path
):
    from disc_mirror import load_config, load_tasks, run

    config = load_config(make_config([model("a", 100), model("b", 200)], [], samples=2))
    out = tmp_path / "runs.jsonl"
    run(load_tasks(FIXTURE_TASKS), config, out, completion=fake_completion)

    records = [json.loads(line) for line in out.read_text().splitlines()]
    # 4 tasks x 5 versions x 2 samples x 2 models
    assert len(records) == 80
    assert len(fake_completion.calls) == 80

    texts = {
        (d["id"], v): d["versions"][v]
        for d in (yaml.safe_load(f.read_text()) for f in FIXTURE_TASKS.glob("*.yaml"))
        for v in VERSIONS
    }
    for r in records:
        assert set(r) == RECORD_FIELDS
        assert r["prompt"] == texts[(r["task_id"], r["version"])]
        assert r["output"] == "reply"
        assert (r["input_tokens"], r["output_tokens"]) == (7, 3)
        assert r["temperature"] == 0.7
        assert r["max_tokens"] == {"a": 100, "b": 200}[r["model"]]
        assert r["litellm_id"] == f"openai/{r['model']}"
    assert {(r["task_id"], r["version"], r["model"], r["sample"]) for r in records} == {
        (t, v, m, s) for (t, v) in texts for m in "ab" for s in (0, 1)
    }

    for call in fake_completion.calls:
        messages = call["messages"]
        assert [m["role"] for m in messages] == ["user"]
        assert messages[0]["content"] in texts.values()


def test_rerun_with_same_out_skips_recorded_calls_and_passes_retries(
    make_config, fake_completion, tmp_path
):
    from disc_mirror.config import load_config
    from disc_mirror.runner import run
    from disc_mirror.tasks import load_tasks

    config = load_config(make_config([model("a", 100)], [], samples=2))
    tasks, out = load_tasks(FIXTURE_TASKS), tmp_path / "runs.jsonl"
    run(tasks, config, out, completion=fake_completion)
    assert {c["num_retries"] for c in fake_completion.calls} == {3}
    lines = out.read_text().splitlines()
    out.write_text("\n".join(lines[:-5]) + "\n")
    fake_completion.calls.clear()
    run(tasks, config, out, completion=fake_completion)
    assert len(fake_completion.calls) == 5
    keys = [(r["task_id"], r["version"], r["model"], r["sample"])
            for r in map(json.loads, out.read_text().splitlines())]
    assert len(keys) == len(set(keys)) == 40


def test_missing_usage_and_content_are_recorded_as_null(make_config, tmp_path):
    import litellm

    from disc_mirror.config import load_config
    from disc_mirror.runner import run
    from disc_mirror.tasks import load_tasks

    def completion(**kwargs):
        resp = litellm.ModelResponse(choices=[{"message": {"role": "assistant", "content": None}}])
        resp.usage = None
        return resp

    config = load_config(make_config([model("a", 100)], [], samples=1))
    out = tmp_path / "runs.jsonl"
    run(load_tasks(FIXTURE_TASKS), config, out, completion=completion)
    for r in map(json.loads, out.read_text().splitlines()):
        assert (r["output"], r["input_tokens"], r["output_tokens"]) == (None, None, None)
