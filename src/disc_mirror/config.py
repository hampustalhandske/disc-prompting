"""Model config: budget, sampling settings, tested models and judges."""

from dataclasses import dataclass, fields
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ModelSpec:
    name: str
    litellm_id: str
    max_tokens: int
    price_in_per_mtok: float
    price_out_per_mtok: float


@dataclass(frozen=True)
class Config:
    budget_usd: float
    samples: int
    temperature: float
    models: list[ModelSpec]
    judges: list[ModelSpec]


def load_config(path: str | Path) -> Config:
    """Reads the model config YAML; a missing or unknown key raises ValueError naming the file."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    try:
        unknown = set(raw) - {f.name for f in fields(Config)}
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        samples, temp, budget = raw["samples"], raw["temperature"], raw["budget_usd"]
        if not isinstance(samples, int) or isinstance(samples, bool) or samples < 1:
            raise ValueError("samples must be an integer >= 1")
        if any(isinstance(x, bool) or not isinstance(x, int | float) for x in (temp, budget)):
            raise ValueError("temperature and budget_usd must be numbers")
        for m in raw["models"] + raw["judges"]:
            if not all(isinstance(m[k], str) and m[k] for k in ("name", "litellm_id")):
                raise ValueError("name and litellm_id must be non-empty strings")
            tokens = m["max_tokens"]
            if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 1:
                raise ValueError(f"{m['name']}: max_tokens must be an integer >= 1")
            prices = (m["price_in_per_mtok"], m["price_out_per_mtok"])
            if any(isinstance(x, bool) or not isinstance(x, int | float) for x in prices):
                raise ValueError(f"{m['name']}: prices must be numbers")
        names = [m["name"] for m in raw["models"] + raw["judges"]]
        if len(names) != len(set(names)):
            raise ValueError("duplicate model or judge names")
        return Config(
            budget_usd=raw["budget_usd"],
            samples=raw["samples"],
            temperature=raw["temperature"],
            models=[ModelSpec(**m) for m in raw["models"]],
            judges=[ModelSpec(**m) for m in raw["judges"]],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{path}: invalid model config: {exc!r}") from exc
