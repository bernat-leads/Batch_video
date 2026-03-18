"""Pre-built video templates and template registry."""

from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.video_editor.schemas import TextStyle, VideoTemplate

TIKTOK_AD_TEMPLATE = VideoTemplate(
    width=1080,
    height=1920,
    fps=24,
    effect_oversample=1.5,
    image_config=ImageConfig(aspect_ratio="9:16", output_format="image/png", size="1K"),
    caption_style=TextStyle(
        font_size=90,
        color="white",
        stroke_color="black",
        stroke_width=10,
        y_position=0.55,
        max_chars=20,
        max_words=3,
    ),
    top_text_style=TextStyle(
        font_size=56,
        color="yellow",
        stroke_color="black",
        stroke_width=6,
        y_position=0.10,
        max_words=10,
    ),
    template_context="""\
        Video format: 1080x1920 vertical (9:16 portrait, TikTok/Reels/Shorts).
        Each segment gets one AI-generated image with a Ken Burns effect (pan/zoom).
        Large bold captions are burned at 55% from top — keep the bottom 40% clear of important details.
        Top text headline is burned at 10% from top — keep the top 20% clear too.
        Image prompts should describe vivid, full-frame 9:16 portrait scenes with the subject centered in the safe middle zone.
        Captions show 1-3 words at a time in TikTok style.""",
)

# ── Template registry ──────────────────────────────────────────────

TEMPLATES: dict[str, VideoTemplate] = {
    "tiktok_ad": TIKTOK_AD_TEMPLATE,
}

DEFAULT_TEMPLATE_NAME = "tiktok_ad"


def get_template(name: str) -> VideoTemplate:
    """Look up a template by name. Raises ValueError for unknown names."""
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}. Available: {list(TEMPLATES)}")
    return TEMPLATES[name]
