"""Mirroring grader: does the reply take on the style of the question?

Rationale: each DISC style has a surface signature (D: short and directive; i: exclamations
and warm sentiment; S: soft, hedged wording; C: long and careful). Counting these features
in a styled reply and subtracting the same model's neutral reply to the same task and sample
shows which way the style moved the answer, without a judge. Features are words, hedges and
directives per 100 words, exclamation marks, and mean VADER sentence sentiment. Only
exact_match and pairwise tasks are used; DAT and SVG replies have a fixed format.
"""

import re
from collections import defaultdict
from statistics import mean

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from disc_mirror.tasks import Task

HEDGES = (
    "maybe", "perhaps", "possibly", "probably", "might", "could", "seems", "somewhat",
    "generally", "typically", "usually", "likely", "arguably", "i think", "it depends",
    "in some cases", "sort of", "kind of",
)  # fmt: skip
DIRECTIVES = (
    "must", "should", "need to", "do this", "make sure", "ensure", "avoid", "never", "always",
    "immediately", "now", "first", "next", "start", "stop", "use", "ask", "tell", "set", "send",
)  # fmt: skip
GRADED = ("exact_match", "pairwise")

_vader = SentimentIntensityAnalyzer()
_WORD = re.compile(r"[\w']+")
_SENTENCE = re.compile(r"[^.!?\n]+")


def _count(phrases: tuple[str, ...], text: str) -> int:
    return sum(len(re.findall(rf"\b{re.escape(p)}\b", text)) for p in phrases)


def text_features(output: str | None) -> dict[str, float]:
    """Word count, hedges and directives per 100 words, "!" count, mean VADER compound."""
    text = output or ""
    words = len(_WORD.findall(text))
    low = text.lower()
    per100 = 100 / words if words else 0.0
    sentences = [s for s in _SENTENCE.findall(text) if s.strip()]
    return {
        "words": float(words),
        "hedges": _count(HEDGES, low) * per100,
        "exclamations": float(text.count("!")),
        "directives": _count(DIRECTIVES, low) * per100,
        "sentiment": mean(_vader.polarity_scores(s)["compound"] for s in sentences)
        if sentences
        else 0.0,
    }


def mirror_deltas(
    records: list[dict], tasks: list[Task]
) -> dict[tuple[str, str], dict[str, float]]:
    """(model, style) -> feature -> mean over (task, sample) of styled minus neutral."""
    graded = {t.id for t in tasks if t.grader in GRADED}
    feats: dict[tuple[str, str, str, int], dict[str, float]] = {}
    for r in records:
        if r["task_id"] in graded:
            feats[(r["model"], r["version"], r["task_id"], r["sample"])] = text_features(
                r["output"]
            )
    diffs: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for (model, version, task_id, sample), f in feats.items():
        neutral = feats.get((model, "neutral", task_id, sample))
        if version != "neutral" and neutral:
            diffs[(model, version)].append({k: f[k] - neutral[k] for k in f})
    return {key: {k: mean(d[k] for d in ds) for k in ds[0]} for key, ds in diffs.items()}
