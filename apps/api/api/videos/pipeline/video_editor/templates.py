"""Pre-built video templates."""

from api.videos.pipeline.image_generation.schemas import ImageConfig
from api.videos.pipeline.video_editor.schemas import TextStyle, VideoTemplate

TIKTOK_AD_TEMPLATE = VideoTemplate(
    width=1080,
    height=1920,
    fps=30,
    effect_oversample=1.5,
    image_config=ImageConfig(aspect_ratio="9:16", output_format="image/png", size="1K"),
    caption_style=TextStyle(
        font_size=180,
        stroke_width=12,
        y_position=0.68,
        max_chars=12,
    ),
    top_text_style=TextStyle(
        font_size=120,
        stroke_width=8,
        y_position=0.08,
    ),
    template_context="""\
        Video format: 1080x1920 vertical (9:16 portrait, TikTok/Reels/Shorts).
        Each segment gets one AI-generated image with a Ken Burns effect (pan/zoom).
        Large bold captions are burned at 68% from top — keep the bottom 35% clear of important details.
        Top text headline is burned at 8% from top — keep the top 15% clear too.
        Image prompts should describe vivid, full-frame 9:16 portrait scenes with the subject centered in the safe middle zone.
        Target 12 characters max per caption group (2-3 words).""",
    )
