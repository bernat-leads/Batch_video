"""Segmentation schemas."""

from enum import Enum
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from api.core.schemas import AICost
from api.videos.pipeline.tts.schemas import WordTimestamp


# ── Segment effects ──────────────────────────────────────────────────


class SegmentEffect(BaseModel):
    """Base class for visual effects applied to a segment during video assembly.

    Each segment has exactly one effect that controls how the still image
    is animated over its duration (e.g. Ken Burns pan/zoom, static hold, etc.).
    Subclasses must set a unique `type` literal for discriminated union dispatch.

    The apply_frame() rendering logic lives in the video editor, not here —
    this schema must stay clean for LLM structured output generation.
    """

    type: str


class KenBurnsDirection(str, Enum):
    """Camera movement direction for the Ken Burns pan/zoom effect."""

    zoom_in = "zoom_in"
    zoom_out = "zoom_out"
    pan_left = "pan_left"
    pan_right = "pan_right"
    pan_up = "pan_up"
    pan_down = "pan_down"


class KenBurnsEffect(SegmentEffect):
    """Ken Burns pan/zoom camera movement applied to a still image."""

    type: Literal["ken_burns"] = "ken_burns"
    direction: KenBurnsDirection
    scale: float = Field(description="Zoom scale factor, ideally between 1.1 and 1.4")


# When adding new effect types, change this to a discriminated union:
# AnySegmentEffect = Annotated[Union[KenBurnsEffect, NewEffect], Discriminator("type")]
AnySegmentEffect = KenBurnsEffect


# ── Segmentation I/O ─────────────────────────────────────────────────


class SegmentResult(BaseModel):
    """A single visual segment output by the segmentation LLM.

    Contains timing boundaries, an image generation prompt, and
    the visual effect to apply during video assembly.
    """

    order: int
    text: str
    start_time: float
    end_time: float
    image_prompt: str
    effect: KenBurnsEffect

    model_config = {"frozen": True}


class SegmentationInput(BaseModel):
    """All inputs needed to run the segmentation LLM.

    Bundles the script, word-level timestamps from TTS, style preferences,
    the master prompt, and template constraints into a single object
    that can build the final ChatPromptTemplate.
    """

    script_text: str = Field(min_length=1, description="Script text to segment")
    word_timestamps: list[WordTimestamp]
    style: str | None = None
    prompt: str = ""
    template_context: str = ""

    def build_prompt(self) -> ChatPromptTemplate:
        """Build a structured ChatPromptTemplate for the segmentation LLM."""
        word_list = "\n".join(
            word.to_indexed_str(index)
            for index, word in enumerate(self.word_timestamps)
        )

        messages = [
            ("system", self.prompt),
            (
                "human",
                f"## Script\n\nThe full ad script to segment into visual scenes:\n\n{self.script_text}",
            ),
            (
                "human",
                f"## Word List\n\nWords with TTS timing — use these timestamps for `start_time` and `end_time`:\n\n{word_list}",
            ),
        ]

        if self.style:
            messages.append(
                (
                    "human",
                    f"## Style\n\nVisual style and mood for the image prompts:\n\n**{self.style}**",
                )
            )

        if self.template_context:
            messages.append(
                (
                    "human",
                    f"## Video Template\n\nOutput format constraints — image prompts must respect these safe zones:\n\n{self.template_context}",
                )
            )

        messages.append(
            (
                "human",
                "Now segment the script. Return the result as structured JSON data using the provided tool schema. Do not respond with plain text.",
            )
        )

        return ChatPromptTemplate.from_messages(messages)


class SegmentationResult(BaseModel):
    """Full output from the segmentation stage.

    Contains the list of visual segments, the resolved prompt that was used,
    and the AI cost incurred.
    """

    segments: list[SegmentResult]
    prompt: str
    cost: AICost = AICost()

    model_config = {"frozen": True}


class SegmentationOutput(BaseModel):
    """LLM structured output wrapper for parsing the raw model response."""

    segments: list[SegmentResult]
