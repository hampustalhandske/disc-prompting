import json
import subprocess
import sys

import numpy as np
import pytest
from conftest import FIXTURE_TASKS, ROOT, VERSIONS, rec, run_cli

X, Y = np.eye(300, dtype=np.float32)[:2]
# Four words point along X, three along Y: 12 of the 21 pairs are orthogonal (distance 1),
# the other 9 are identical (distance 0), so the score is 12 / 21 * 100.
VECTORS = {f"x{c}": X for c in "abcd"} | {f"y{c}": Y for c in "abc"} | {"back": -X}
SEVEN = ["xa", "xb", "xc", "xd", "ya", "yb", "yc"]
SEVEN_SCORE = 12 / 21 * 100


def svg_task(constraints):
    from disc_mirror.tasks import Task

    return Task(
        id="gen-t", area="generation", grader="svg", rationale="Fixture.",
        versions={
            v: ("Draw a red circle.\nUse a 10 by 10 canvas.\nReply with one svg code block."
                if v == "neutral" else f"Style {v}: please draw it.\nReply with an svg block.")
            for v in VERSIONS
        },
        expected={"constraints": constraints},
    )


# DAT

def test_dat_score_uses_21_pairs_first_7_known_words_and_none_below_7():
    from disc_mirror.graders.dat import dat_score

    assert abs(dat_score(SEVEN, VECTORS) - SEVEN_SCORE) < 1e-4
    # numbering, bullets, punctuation, case and padding are cleaned; unknown and repeated
    # words are dropped before taking 7; an 8th word (opposite direction) is never used
    messy = [" 1. XA. ", "nope", "- xb", "XC!", "xa", "2) xd", "zzz", "ya", "**yb**", "yc", "back"]
    assert abs(dat_score(messy, VECTORS) - SEVEN_SCORE) < 1e-4
    assert dat_score(SEVEN[:6] + ["nope", "zzz"], VECTORS) is None


def test_grade_dat_returns_one_row_per_dat_record_with_valid_word_count():
    from disc_mirror.graders.dat import grade_dat
    from disc_mirror.tasks import load_tasks

    tasks = load_tasks(FIXTURE_TASKS)
    records = [
        rec("crea-fix-01", "neutral", "\n".join(SEVEN)),
        rec("crea-fix-01", "D", "\n".join(SEVEN[:6] + ["nope"]), sample=1),
        rec("crea-fix-01", "i", None),
        rec("gen-fix-01", "neutral", "\n".join(SEVEN)),  # not a dat task
    ]
    rows = grade_dat(records, tasks, VECTORS)
    assert [r["version"] for r in rows] == ["neutral", "D", "i"]
    assert abs(rows[0]["score"] - SEVEN_SCORE) < 1e-4 and rows[0]["valid_words"] == 7
    assert rows[1]["score"] is None and rows[1]["valid_words"] == 6
    assert rows[2]["score"] is None


def test_disc_grade_dat_prints_mean_score_and_too_short_count(tmp_path):
    glove = tmp_path / "glove"
    glove.mkdir()
    words = list(VECTORS)
    (glove / "words.txt").write_text("\n".join(words) + "\n")
    np.save(glove / "vectors.npy", np.stack([VECTORS[w] for w in words]))
    runs = tmp_path / "runs.jsonl"
    runs.write_text("\n".join(json.dumps(r) for r in [
        rec("crea-fix-01", "neutral", "\n".join(SEVEN)),
        rec("crea-fix-01", "neutral", "xa\nxb", sample=1),
    ]))
    p = run_cli("dat", "--runs", str(runs), "--tasks", str(FIXTURE_TASKS),
                "--glove", str(glove), cmd="disc-grade", block_network=True)
    assert p.returncode == 0, p.stderr
    line = next(ln for ln in p.stdout.splitlines() if "alpha" in ln)
    assert line.split() == ["alpha", "neutral", "57.14", "1", "1"]  # mean, n, too short


# SVG

def test_extract_svg_takes_fenced_or_bare_svg_only():
    from disc_mirror.graders.svg import extract_svg

    doc = '<svg viewBox="0 0 10 10"><circle r="3"/></svg>'
    assert extract_svg(f"Here you go:\n```svg\n{doc}\n```\nEnjoy!").strip() == doc
    assert extract_svg(f"```xml\n{doc}\n```").strip() == doc
    assert extract_svg(f"```\n{doc}\n```").strip() == doc
    assert extract_svg(f"Sure! {doc} Hope it helps.") == doc
    css = "```css\n/* styles for <svg> */ svg { color: red; }\n```\n"
    assert extract_svg(f"{css}```svg\n{doc}\n```\nnote").strip() == doc  # fences stay paired
    assert extract_svg("I cannot draw that.") is None
    assert extract_svg(None) is None


def test_check_constraints_grammar_forms():
    from disc_mirror.graders.svg import check_constraints

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">'
        '<circle r="3" fill="#FF0000"/><circle r="4" style="fill:#00AA00;stroke:#112233"/>'
        '<text>OPEN today</text></svg>'
    )
    cons = [
        "element:circle", "element:rect",               # tag match through the namespace
        "count:circle:2", "count:circle:3",             # exactly enough, one short
        "color:#ff0000", "color:#00aa00", "color:#112233", "color:#abcdef",  # case, style
        "text:OPEN", "text:Sales",
        "viewbox:300 200", "viewbox:100 100", "viewbox:300.0 200",  # compared as numbers
    ]
    assert check_constraints(svg, cons) == [
        True, False, True, False, True, True, True, False, True, False, True, False, True,
    ]
    with pytest.raises(ValueError, match="colour:#ff0000"):
        check_constraints(svg, ["colour:#ff0000"])
    assert check_constraints("<svg><circle></svg>", ["element:circle", "count:circle:0"]) == [
        False, False,
    ]


def test_grade_svg_scores_clip_only_on_rendered_svg_against_neutral_brief():
    from disc_mirror.graders.svg import grade_svg

    good = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">{}</svg>'
    red = good.format('<circle cx="5" cy="5" r="3" fill="#FF0000"/>')
    styled = good.format('<circle cx="5" cy="5" r="3" style="fill:#ff0000"/>')
    calls = []

    def clip(png, text):
        calls.append((png, text))
        return 31.5

    task = svg_task(["element:circle", "color:#ff0000", "count:circle:2", "element:rect"])
    rows = grade_svg([
        rec("gen-t", "neutral", f"```svg\n{red}\n```"),
        rec("gen-t", "D", f"```svg\n{styled}\n```"),
        rec("gen-t", "i", "No picture, sorry."),
        rec("gen-t", "S", "<svg><circle></svg>"),  # extracted but not renderable
        rec("gen-t", "C", None),
        rec("crea-fix-01", "neutral", f"```svg\n{red}\n```"),  # other task: ignored
    ], [task], clip)

    assert [r["version"] for r in rows] == ["neutral", "D", "i", "S", "C"]
    assert [r["renders"] for r in rows] == [True, True, False, False, False]
    assert [r["constraints"] for r in rows] == [0.5, 0.5, 0, 0, 0]
    assert [r["clip"] for r in rows] == [31.5, 31.5, None, None, None]
    assert len(calls) == 2
    assert all(png[:4] == b"\x89PNG" for png, _ in calls)
    # neutral brief without its format line, identical for every version
    assert {t.strip() for _, t in calls} == {"Draw a red circle.\nUse a 10 by 10 canvas."}


def test_load_clip_without_downloaded_weights_refuses_instead_of_downloading(tmp_path):
    from disc_mirror.graders.svg import load_clip

    (tmp_path / "models--x" / "blobs").mkdir(parents=True)  # an interrupted download
    with pytest.raises(FileNotFoundError, match="disc-fetch"):
        load_clip(tmp_path)


# import guard

def test_cli_import_does_not_load_torch_or_open_clip():
    code = (
        "import sys, disc_mirror.cli\n"
        "sys.exit(any(m.split('.')[0] in ('torch', 'open_clip') for m in sys.modules))"
    )
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT)
    assert p.returncode == 0
