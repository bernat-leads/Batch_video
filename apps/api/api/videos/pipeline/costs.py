"""Live cost lookup for pipeline AI services via LiteLLM."""

import logging
from functools import lru_cache

from litellm import model_cost

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def get_token_costs(model: str) -> tuple[float, float]:
    """Get (input_cost_per_token, output_cost_per_token) for a model.

    Falls back to zero if model not found in LiteLLM pricing.
    """
    pricing = model_cost.get(model)
    if pricing:
        return (
            pricing.get("input_cost_per_token", 0.0),
            pricing.get("output_cost_per_token", 0.0),
        )

    logger.warning("Model %s not found in LiteLLM pricing database", model)
    return (0.0, 0.0)


@lru_cache(maxsize=32)
def get_image_cost(model: str) -> float:
    """Get per-image cost for an image generation model.

    Tries the model name directly, then with 'gemini/' prefix.
    Falls back to zero if not found.
    """
    for key in (model, f"gemini/{model}"):
        pricing = model_cost.get(key)
        if pricing:
            return pricing.get("output_cost_per_image", 0.0)

    logger.warning("Model %s not found in LiteLLM pricing database", model)
    return 0.0
