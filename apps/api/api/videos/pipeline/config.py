"""Pipeline configuration — costs, dimensions, and model defaults."""

# ── Video output ──────────────────────────────────────────────────────
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# ── TTS ───────────────────────────────────────────────────────────────
TTS_COST_PER_CHAR = 0.00003  # ~$0.30 per 10K chars

# ── Segmentation (Claude) ────────────────────────────────────────────
SEGMENTATION_MAX_TOKENS = 4096
SEGMENTATION_INPUT_TOKEN_COST = 0.003 / 1000  # per token
SEGMENTATION_OUTPUT_TOKEN_COST = 0.015 / 1000  # per token

# ── Image generation (Gemini Imagen 3) ─────────────────────────────
IMAGEN_COST_PER_IMAGE = 0.04  # $0.04 per image (standard tier)

# ── Assembly ──────────────────────────────────────────────────────────
KEN_BURNS_OVERSAMPLE = 1.5  # scale factor for source image

# ── Storage ───────────────────────────────────────────────────────────
PRESIGNED_URL_EXPIRY = 7 * 24 * 3600  # 7 days
