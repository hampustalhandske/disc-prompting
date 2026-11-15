"""Runner for the DISC-styled question study."""

import os

# Keeps litellm from fetching its model-cost map over the network on import.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
