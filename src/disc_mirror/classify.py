"""Style classifier: can a judge model tell which DISC style a question was written in?"""

import json
import random
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import litellm

from disc_mirror.config import ModelSpec
from disc_mirror.tasks import VERSIONS, Task

_PROMPT = """Below is a question. It was written in one of five styles:
- neutral: plain and factual, no personal voice
- D: brief, outcome-first, impatient with preamble
- i: warm, enthusiastic, personal, with social context
- S: calm, patient, considerate, reassuring
- C: precise, structured, concerned with correctness and sources

Question:
{question}

Reply with one line: STYLE: <neutral|D|i|S|C>"""

_LABEL = re.compile(r"STYLE:\s*(neutral|D|i|S|C)\b")


def classify(
    tasks: list[Task],
    judge: ModelSpec,
    out: str | Path,
    completion: Callable = litellm.completion,
    seed: int = 0,
) -> list[dict]:
    """Asks the judge to label every task x version, in a seeded shuffled order.

    Appends one JSONL record per call to out and returns the records. The prompt holds only the
    style descriptions and the question text. `label` is None when the reply has no STYLE: line.
    """
    pairs = [(t, v) for t in tasks for v in VERSIONS]
    random.Random(seed).shuffle(pairs)
    records = []
    with Path(out).open("a") as f:
        for t, v in pairs:
            prompt = _PROMPT.format(question=t.versions[v])
            resp = completion(
                model=judge.litellm_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=judge.max_tokens,
            )
            output = resp.choices[0].message.content
            match = _LABEL.search(output or "")
            record = {
                "task_id": t.id,
                "version": v,
                "judge": judge.name,
                "litellm_id": judge.litellm_id,
                "prompt": prompt,
                "output": output,
                "label": match.group(1) if match else None,
                "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            f.write(json.dumps(record) + "\n")
            f.flush()
            records.append(record)
    return records


def summarize(records: list[dict]) -> dict[str, float]:
    """Returns, per version, the share of records whose label equals the version."""
    totals: dict[str, list[int]] = {}
    for r in records:
        hit = totals.setdefault(r["version"], [0, 0])
        hit[0] += r["label"] == r["version"]
        hit[1] += 1
    return {v: hits / n for v, (hits, n) in totals.items()}
