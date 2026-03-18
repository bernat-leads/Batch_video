"""Live cost lookup for pipeline AI services via LiteLLM.

Usage counts (tokens, characters, images) come from API responses.
Dollar rates come from LiteLLM's pricing database — returns 0 if not found.
"""

import logging
from functools import lru_cache

from litellm import model_cost

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def get_token_costs(model: str) -> tuple[float, float]:
    """Get (input_cost_per_token, output_cost_per_token) for a model.

    Returns (0.0, 0.0) if model not found in LiteLLM pricing.
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
    Returns 0.0 if not found.
    """
    for key in (model, f"gemini/{model}"):
        pricing = model_cost.get(key)
        if pricing:
            return pricing.get("output_cost_per_image", 0.0)

    logger.warning("Model %s not found in LiteLLM pricing database", model)
    return 0.0


@lru_cache(maxsize=32)
def get_tts_char_cost(model: str) -> float:
    """Get per-character cost for a TTS model.

    Tries the model name directly, then with 'elevenlabs/' prefix.
    Returns 0.0 if not found.
    """
    for key in (model, f"elevenlabs/{model}"):
        pricing = model_cost.get(key)
        if pricing:
            return pricing.get("input_cost_per_character", 0.0)

    logger.warning("TTS model %s not found in LiteLLM pricing database", model)
    return 0.0
