"""Cost estimate and live runner. Prompts are exactly the version text, with no system message."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import litellm

from disc_mirror.config import Config, ModelSpec
from disc_mirror.tasks import VERSIONS, Task

STYLES = VERSIONS[1:]


@dataclass(frozen=True)
class Estimate:
    prompts: dict[str, int]  # model name -> number of calls
    model_usd: dict[str, float]  # model name -> generation cost
    judge_usd: float

    @property
    def total_usd(self) -> float:
        return sum(self.model_usd.values()) + self.judge_usd


def _tokens(text: str) -> int:
    """Estimates tokens with litellm's bundled tiktoken encoding, whatever the model.

    Model-specific tokenizers can download files, so every model is counted the same local way.
    """
    return litellm.token_counter(model="gpt-4", text=text)


def _usd(spec: ModelSpec, tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * spec.price_in_per_mtok + tokens_out * spec.price_out_per_mtok) / 1e6


def estimate_cost(tasks: list[Task], config: Config) -> Estimate:
    """Estimates generation and pairwise-judge cost locally, without any API call.

    Judge input is the neutral prompt plus two answers of the tested model's max_tokens.
    """
    prompts, model_usd = {}, {}
    for m in config.models:
        prompts[m.name] = len(tasks) * len(VERSIONS) * config.samples
        model_usd[m.name] = sum(
            _usd(m, _tokens(t.versions[v]), m.max_tokens) * config.samples
            for t in tasks
            for v in VERSIONS
        )
    judge_usd = 0.0
    for t in (t for t in tasks if t.grader == "pairwise"):
        for m in config.models:
            for j in config.judges:
                tokens_in = _tokens(t.versions["neutral"]) + 2 * m.max_tokens
                calls = len(STYLES) * config.samples * 2
                judge_usd += calls * _usd(j, tokens_in, j.max_tokens)
    return Estimate(prompts, model_usd, judge_usd)


def load_jsonl(path: Path) -> list[dict]:
    """Reads an append-only JSONL file; [] when it doesn't exist.

    A last line with no newline was cut off by a crash: it is removed from the file and
    ignored, so the next append starts on a fresh line. Blank lines are skipped.
    """
    if not path.exists():
        return []
    text = path.read_text()
    if text and not text.endswith("\n"):
        text = text[: text.rfind("\n") + 1]
        path.write_text(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def run(
    tasks: list[Task], config: Config, out: str | Path, completion: Callable = litellm.completion
):
    """Calls every task x version x model x sample and appends one JSONL record per call to out.

    Calls already recorded in out are skipped, so rerunning with the same out resumes the run.
    Raises ValueError when a recorded call used another litellm_id, temperature, max_tokens or
    prompt than the current config and tasks, so one out never mixes two setups.
    """
    out = Path(out)
    setup = {
        (t.id, v, m.name): (m.litellm_id, config.temperature, m.max_tokens, t.versions[v])
        for t in tasks
        for v in VERSIONS
        for m in config.models
    }
    done = set()
    for r in load_jsonl(out):
        key = (r["task_id"], r["version"], r["model"])
        if key in setup and setup[key] != (
            r["litellm_id"], r["temperature"], r["max_tokens"], r["prompt"]
        ):
            raise ValueError(f"{out}: {key} was recorded with another setup; use a new --out")
        done.add((*key, r["sample"]))
    with out.open("a") as f:
        for t in tasks:
            for v in VERSIONS:
                prompt = t.versions[v]
                for m in config.models:
                    for sample in range(config.samples):
                        if (t.id, v, m.name, sample) in done:
                            continue
                        resp = completion(
                            model=m.litellm_id,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=config.temperature,
                            max_tokens=m.max_tokens,
                            num_retries=3,
                        )
                        usage = resp.usage
                        record = {
                            "task_id": t.id,
                            "version": v,
                            "model": m.name,
                            "litellm_id": m.litellm_id,
                            "sample": sample,
                            "temperature": config.temperature,
                            "max_tokens": m.max_tokens,
                            "prompt": prompt,
                            "output": resp.choices[0].message.content,
                            "input_tokens": usage.prompt_tokens if usage else None,
                            "output_tokens": usage.completion_tokens if usage else None,
                            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                        f.write(json.dumps(record) + "\n")
                        f.flush()
