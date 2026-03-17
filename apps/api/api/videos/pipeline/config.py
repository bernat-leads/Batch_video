"""Pipeline configuration — costs and model defaults."""

# ── ElevenLabs TTS ────────────────────────────────────────────────────
ELEVENLABS_TTS_COST_PER_CHAR = 0.00003  # ~$0.30 per 10K chars
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# ── OpenAI TTS ────────────────────────────────────────────────────────
OPENAI_TTS_COST_PER_CHAR = 0.000012  # $12 per 1M chars
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"

# ── Segmentation (Claude) ────────────────────────────────────────────
SEGMENTATION_MAX_TOKENS = 4096
SEGMENTATION_INPUT_TOKEN_COST = 0.003 / 1000  # per token
SEGMENTATION_OUTPUT_TOKEN_COST = 0.015 / 1000  # per token
SEGMENTATION_MODEL = "claude-sonnet-4-20250514"

# ── Image generation (Gemini Imagen) ─────────────────────────────────
IMAGEN_COST_PER_IMAGE = 0.02  # $0.02 per image (fast tier)
IMAGEN_MODEL = "imagen-4.0-fast-generate-001"

# ── Storage ───────────────────────────────────────────────────────────
PRESIGNED_URL_EXPIRY = 7 * 24 * 3600  # 7 days
