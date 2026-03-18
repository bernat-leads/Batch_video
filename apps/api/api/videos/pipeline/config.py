"""Pipeline configuration — model defaults.

All costs are fetched live via LiteLLM (see costs.py).
"""

# ── ElevenLabs TTS ────────────────────────────────────────────────────
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"

# ── Segmentation (Claude) ────────────────────────────────────────────
SEGMENTATION_MAX_TOKENS = 16384
SEGMENTATION_MODEL = "claude-sonnet-4-20250514"

# ── Image generation (Gemini Imagen) ─────────────────────────────────
IMAGEN_MODEL = "imagen-4.0-fast-generate-001"

# ── Storage ───────────────────────────────────────────────────────────
PRESIGNED_URL_EXPIRY = 7 * 24 * 3600  # 7 days
