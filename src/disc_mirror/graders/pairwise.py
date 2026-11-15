"""Blind pairwise judging of open-ended answers: does a styled answer beat the neutral one?

Rationale: open-ended quality has no exact answer, so a judge model compares the styled
answer with the neutral answer for the same task, model and sample. The judge sees only the
neutral question and two anonymous answers, never the style, task id or model name. Each pair
is judged in both orders to cancel position bias, at temperature 0, by every judge. A tie
counts 0.5 in the win rate; replies without a parsable verdict are left out of the rate.
"""

import json
import re
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import litellm

from disc_mirror.config import ModelSpec
from disc_mirror.graders import pair_with_neutral
from disc_mirror.runner import load_jsonl
from disc_mirror.tasks import Task

_PROMPT = """Question:
{question}

Answer A:
{a}

Answer B:
{b}

Which answer is better? Reply with one line: WINNER: <A|B|TIE>"""
_WINNER = re.compile(r"WINNER:\s*(A|B|TIE)\b", re.IGNORECASE)


def _parse(reply: str | None, styled_first: bool) -> str | None:
    """Maps the last `WINNER:` line of a reply to styled, neutral or tie; None if absent."""
    found = _WINNER.findall(reply or "")
    if not found:
        return None
    verdict = found[-1].upper()
    if verdict == "TIE":
        return "tie"
    return "styled" if (verdict == "A") == styled_first else "neutral"


def judge_pairs(
    records: list[dict],
    tasks: list[Task],
    judges: list[ModelSpec],
    out: str | Path,
    completion: Callable = litellm.completion,
) -> list[dict]:
    """Judges each styled answer against the neutral one in both orders and appends to out.

    Styled answers with no neutral partner or a None output are not judged;
    `pair_with_neutral` counts them. Calls already in out are skipped, so rerunning with the
    same out resumes. Returns every judgment in out, including earlier ones.
    """
    out = Path(out)
    judgments = load_jsonl(out)
    done = {
        (j["task_id"], j["model"], j["style"], j["sample"], j["judge"], j["styled_first"])
        for j in judgments
    }
    questions = {t.id: t.versions["neutral"] for t in tasks if t.grader == "pairwise"}
    pairs, _ = pair_with_neutral(records, set(questions))
    with out.open("a") as f:
        for s, n in pairs:
            for judge in judges:
                for styled_first in (True, False):
                    key = (s["task_id"], s["model"], s["version"], s["sample"])
                    if (*key, judge.name, styled_first) in done:
                        continue
                    a, b = (s, n) if styled_first else (n, s)
                    prompt = _PROMPT.format(
                        question=questions[s["task_id"]], a=a["output"], b=b["output"]
                    )
                    resp = completion(
                        model=judge.litellm_id,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=judge.max_tokens,
                        num_retries=3,
                    )
                    output = resp.choices[0].message.content
                    record = {
                        "task_id": s["task_id"],
                        "model": s["model"],
                        "style": s["version"],
                        "sample": s["sample"],
                        "judge": judge.name,
                        "litellm_id": judge.litellm_id,
                        "styled_first": styled_first,
                        "prompt": prompt,
                        "output": output,
                        "winner": _parse(output, styled_first),
                        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                    judgments.append(record)
    return judgments


def win_rates(judgments: list[dict]) -> dict[tuple[str, str, str], float]:
    """Styled win rate vs neutral per (model, style, judge) and (model, style, "all").

    A tie counts 0.5; judgments with winner None are left out.
    """
    points = defaultdict(list)
    for j in judgments:
        if j["winner"] is None:
            continue
        score = {"styled": 1.0, "tie": 0.5, "neutral": 0.0}[j["winner"]]
        points[(j["model"], j["style"], j["judge"])].append(score)
        points[(j["model"], j["style"], "all")].append(score)
    return {k: sum(v) / len(v) for k, v in points.items()}
