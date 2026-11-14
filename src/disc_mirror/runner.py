"""Cost estimate and live runner. Prompts are exactly the version text, with no system message."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import litellm

from disc_mirror.config import Config, ModelSpec
from disc_mirror.tasks import VERSIONS, Task

STYLES = ("D", "i", "S", "C")


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


def run(
    tasks: list[Task], config: Config, out: str | Path, completion: Callable = litellm.completion
):
    """Calls every task x version x model x sample and appends one JSONL record per call to out."""
    with Path(out).open("a") as f:
        for t in tasks:
            for v in VERSIONS:
                prompt = t.versions[v]
                for m in config.models:
                    for sample in range(config.samples):
                        resp = completion(
                            model=m.litellm_id,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=config.temperature,
                            max_tokens=m.max_tokens,
                        )
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
                            "input_tokens": resp.usage.prompt_tokens,
                            "output_tokens": resp.usage.completion_tokens,
                            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        }
                        f.write(json.dumps(record) + "\n")
                        f.flush()
