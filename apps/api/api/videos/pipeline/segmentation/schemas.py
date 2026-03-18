"""Segmentation schemas."""

import json
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
    """Ken Burns pan/zoom camera movement for a segment image."""

    type: Literal["ken_burns"] = Field(
        default="ken_burns", description="Always 'ken_burns'"
    )
    direction: KenBurnsDirection = Field(description="Camera movement direction")
    scale: float = Field(description="Zoom scale factor, ideally between 1.1 and 1.4")


# When adding new effect types, change this to a discriminated union:
# AnySegmentEffect = Annotated[Union[KenBurnsEffect, NewEffect], Discriminator("type")]
AnySegmentEffect = KenBurnsEffect


# ── Segmentation I/O ─────────────────────────────────────────────────


class SegmentResult(BaseModel):
    """A single visual segment of the ad script."""

    order: int = Field(description="Segment number starting from 1")
    text: str = Field(description="The script text spoken during this segment")
    start_time: float = Field(
        description="Start time in seconds from the word timestamps"
    )
    end_time: float = Field(description="End time in seconds from the word timestamps")
    image_prompt: str = Field(
        description="Detailed image generation prompt for this segment's visual"
    )
    effect: KenBurnsEffect = Field(
        description="Ken Burns camera movement effect for this segment"
    )

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

        schema_json = json.dumps(SegmentationOutput.model_json_schema(), indent=2)

        system_prompt = (
            f"{self.prompt}\n\n"
            f"## Required Output Schema\n\n"
            f"You MUST respond with data matching this JSON schema:\n\n"
            f"```json\n{schema_json}\n```"
        )

        messages = [
            ("system", system_prompt.replace("$", "$$")),
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
    """The segmented ad script with visual scene descriptions and camera movements."""

    segments: list[SegmentResult] = Field(
        description="List of visual segments covering the entire script from start to end"
    )
