"""SVG grader for generation tasks.

Rationale: an SVG brief can fail in three separable ways, so three measures are reported.
Whether the image renders at all (resvg) shows if the model produced usable markup.
The share of the task's structural constraints met (elements, counts, colours, text,
viewBox) is a deterministic check of the brief's explicit demands. CLIP similarity between
the rendered image and the brief (x100) is a soft check that the picture looks like what was
asked. The CLIP text is the task's neutral brief without its format line, the same for every
style version, so a style is never scored against its own wording.

Constraint grammar: `element:<tag>` (at least one), `count:<tag>:<n>` (at least n),
`color:<#hex>` (a fill or stroke, as attribute or in `style`, case-insensitive),
`text:<string>` (a text element containing it), `viewbox:<w> <h>`.
"""

import io
import re
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

from disc_mirror.tasks import Task

_FENCE = re.compile(r"```(?:svg|xml)?[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)
_SPAN = re.compile(r"<svg\b.*?</svg\s*>", re.DOTALL | re.IGNORECASE)
_PAINT = re.compile(r"(?:^|;)\s*(?:fill|stroke)\s*:\s*([^;]+)", re.IGNORECASE)


def extract_svg(output: str | None) -> str | None:
    """SVG markup from a fenced block holding `<svg`, else the first `<svg>...</svg>` span."""
    text = output or ""
    for block in _FENCE.findall(text):
        if "<svg" in block.lower():
            return block.strip()
    match = _SPAN.search(text)
    return match.group(0) if match else None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _paints(root: ET.Element) -> set[str]:
    found = set()
    for el in root.iter():
        for key in ("fill", "stroke"):
            if key in el.attrib:
                found.add(el.attrib[key].strip().casefold())
        found.update(m.strip().casefold() for m in _PAINT.findall(el.get("style", "")))
    return found


def _holds(root: ET.Element, constraint: str) -> bool:
    kind, _, arg = constraint.partition(":")
    tags = [_local(el.tag) for el in root.iter()]
    if kind == "element":
        return arg in tags
    if kind == "count":
        tag, _, n = arg.rpartition(":")
        return tags.count(tag) >= int(n)
    if kind == "color":
        return arg.casefold() in _paints(root)
    if kind == "text":
        return any(_local(el.tag) == "text" and arg in "".join(el.itertext()) for el in root.iter())
    if kind == "viewbox":
        box = root.get("viewBox", "").replace(",", " ").split()
        return len(box) == 4 and box[2:] == arg.split()
    return False


def check_constraints(svg: str, constraints: list[str]) -> list[bool]:
    """One bool per constraint; unparsable XML fails every constraint."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return [False] * len(constraints)
    return [_holds(root, c) for c in constraints]


def render_png(svg: str) -> bytes | None:
    """PNG bytes of the SVG rendered by resvg; None when rendering fails."""
    import resvg_py

    try:
        return bytes(resvg_py.svg_to_bytes(svg_string=svg, background="#ffffff"))
    except ValueError:
        return None


def load_clip(cache_dir: str | Path = "data/clip") -> Callable[[bytes, str], float]:
    """CLIP ViT-B-32 (OpenAI weights) as a scorer: cosine similarity x 100 of image vs text.

    torch and open_clip are imported here, so other graders never load them.
    """
    import open_clip
    import torch
    from PIL import Image

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai", cache_dir=str(cache_dir)
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()

    def score(png: bytes, text: str) -> float:
        image = preprocess(Image.open(io.BytesIO(png)).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            img = model.encode_image(image)
            txt = model.encode_text(tokenizer([text]))
        return float(torch.nn.functional.cosine_similarity(img, txt).item() * 100)

    return score


def _brief(task: Task) -> str:
    """The neutral brief without its last (format) line."""
    return "\n".join(task.versions["neutral"].strip().splitlines()[:-1]).strip()


def grade_svg(
    records: list[dict], tasks: list[Task], clip: Callable[[bytes, str], float]
) -> list[dict]:
    """One result per record whose task is graded by svg; CLIP runs only on rendered images."""
    by_id = {t.id: t for t in tasks if t.grader == "svg"}
    results = []
    for r in records:
        task = by_id.get(r["task_id"])
        if task is None:
            continue
        svg = extract_svg(r["output"])
        cons = task.expected["constraints"]
        met = check_constraints(svg, cons) if svg else []
        png = render_png(svg) if svg else None
        results.append(
            {
                "task_id": r["task_id"],
                "version": r["version"],
                "model": r["model"],
                "sample": r["sample"],
                "renders": png is not None,
                "constraints": sum(met) / len(cons) if svg else 0.0,
                "clip": clip(png, _brief(task)) if png is not None else None,
            }
        )
    return results
