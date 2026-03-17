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
        font_size=72,
        color="white",
        stroke_color="black",
        stroke_width=4,
        y_position=0.65,
        max_chars=30,
    ),
    top_text_style=TextStyle(
        font_size=72,
        color="yellow",
        stroke_color="black",
        stroke_width=5,
        y_position=0.10,
    ),
    template_context="""\
        Video format: 1080x1920 vertical (9:16 portrait, TikTok/Reels/Shorts).
        Each segment gets one AI-generated image with a Ken Burns effect (pan/zoom).
        Large bold captions are burned at 58% from top — keep the bottom 40% clear of important details.
        Top text headline is burned at 10% from top — keep the top 20% clear too.
        Image prompts should describe vivid, full-frame 9:16 portrait scenes with the subject centered in the safe middle zone.
        Target 10 characters max per caption group (1-2 words).""",
)
