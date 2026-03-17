"""Pipeline configuration — costs and model defaults."""

# ── TTS ───────────────────────────────────────────────────────────────
ELEVENLABS_TTS_COST_PER_CHAR = 0.00003  # ~$0.30 per 10K chars
OPENAI_TTS_COST_PER_CHAR = 0.000012  # $12 per 1M chars

# ── Segmentation (Claude) ────────────────────────────────────────────
SEGMENTATION_MAX_TOKENS = 4096
SEGMENTATION_INPUT_TOKEN_COST = 0.003 / 1000  # per token
SEGMENTATION_OUTPUT_TOKEN_COST = 0.015 / 1000  # per token

# ── Image generation (Gemini Imagen 3) ─────────────────────────────
IMAGEN_COST_PER_IMAGE = 0.04  # $0.04 per image (standard tier)

# ── Storage ───────────────────────────────────────────────────────────
PRESIGNED_URL_EXPIRY = 7 * 24 * 3600  # 7 days
