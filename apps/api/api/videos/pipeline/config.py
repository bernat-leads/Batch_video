"""Pipeline configuration — model defaults and TTS costs.

LLM and image generation costs are fetched live via LiteLLM (see costs.py).
TTS costs are hardcoded here — no live pricing source available.
"""

# ── ElevenLabs TTS ────────────────────────────────────────────────────
ELEVENLABS_TTS_COST_PER_CHAR = 0.00003  # ~$0.30 per 10K chars
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# ── OpenAI TTS ────────────────────────────────────────────────────────
OPENAI_TTS_COST_PER_CHAR = 0.000012  # $12 per 1M chars
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"

# ── Segmentation (Claude) ────────────────────────────────────────────
SEGMENTATION_MAX_TOKENS = 16384
SEGMENTATION_MODEL = "claude-sonnet-4-20250514"

# ── Image generation (Gemini Imagen) ─────────────────────────────────
IMAGEN_MODEL = "imagen-4.0-fast-generate-001"

# ── Storage ───────────────────────────────────────────────────────────
PRESIGNED_URL_EXPIRY = 7 * 24 * 3600  # 7 days
