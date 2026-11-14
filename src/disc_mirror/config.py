"""Model config: budget, sampling settings, tested models and judges."""

from dataclasses import dataclass
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
    """Reads the model config YAML; a missing key raises KeyError naming it."""
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    try:
        return Config(
            budget_usd=raw["budget_usd"],
            samples=raw["samples"],
            temperature=raw["temperature"],
            models=[ModelSpec(**m) for m in raw["models"]],
            judges=[ModelSpec(**m) for m in raw["judges"]],
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"{path}: invalid model config: {exc!r}") from exc
