"""Runner for the DISC-styled question study."""

import os

# Keeps litellm from fetching its model-cost map over the network on import.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from disc_mirror.config import load_config  # noqa: E402
from disc_mirror.runner import run  # noqa: E402
from disc_mirror.tasks import load_tasks  # noqa: E402

__all__ = ["load_config", "load_tasks", "run"]
