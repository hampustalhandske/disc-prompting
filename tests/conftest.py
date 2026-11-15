import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Keeps litellm from fetching its model-cost map when a test imports it before disc_mirror.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_TASKS = ROOT / "tests" / "fixtures" / "tasks"
NETBLOCK = ROOT / "tests" / "fixtures" / "netblock"
VERSIONS = ["neutral", "D", "i", "S", "C"]


def rec(tid, version, output, model_name="alpha", sample=0):
    """A run record (m1 shape) with fixed filler for every field the graders don't read."""
    return {
        "task_id": tid, "version": version, "model": model_name, "litellm_id": "x/y",
        "sample": sample, "temperature": 0.7, "max_tokens": 10, "prompt": "p",
        "output": output, "input_tokens": 1, "output_tokens": 1, "timestamp": "t",
    }


@pytest.fixture
def make_config(tmp_path):
    """Write a models.yaml with the given fields and return its path."""

    def make(models, judges, samples=2):
        path = tmp_path / "models.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "budget_usd": 50,
                    "samples": samples,
                    "temperature": 0.7,
                    "models": models,
                    "judges": judges,
                }
            )
        )
        return path

    return make


def model(name, max_tokens, price_in=0.0, price_out=0.0):
    return {
        "name": name,
        "litellm_id": f"openai/{name}",
        "max_tokens": max_tokens,
        "price_in_per_mtok": price_in,
        "price_out_per_mtok": price_out,
    }


@pytest.fixture
def task_dir_with(tmp_path):
    """Copy the fixture tasks to a temp dir, apply `mutate(dict)` to one, return dir and file."""

    def make(mutate, task_id="corr-fix-01"):
        d = tmp_path / "tasks"
        shutil.copytree(FIXTURE_TASKS, d)
        f = d / f"{task_id}.yaml"
        data = yaml.safe_load(f.read_text())
        mutate(data)
        f.write_text(yaml.safe_dump(data))
        return d, f

    return make


def run_cli(*args, block_network=False, net_log=None, cmd="disc-run"):
    """Run an installed command (`disc-run` by default) from the repo root; return the process."""
    env = dict(os.environ)
    if block_network:
        env["PYTHONPATH"] = str(NETBLOCK)
        if net_log:
            env["NETBLOCK_LOG"] = str(net_log)
            env["NETBLOCK_LOADED"] = f"{net_log}.loaded"
    exe = Path(sys.executable).parent / cmd
    return subprocess.run(
        [str(exe), *args], cwd=ROOT, env=env, capture_output=True, text=True
    )
