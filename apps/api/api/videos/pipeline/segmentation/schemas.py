"""Segmentation schemas."""

from abc import abstractmethod
from enum import Enum
from typing import Literal

import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from PIL import Image
from pydantic import BaseModel, Field

from api.core.schemas import AICost
from api.videos.pipeline.tts.schemas import WordTimestamp


# ── Segment effects ──────────────────────────────────────────────────


class SegmentEffect(BaseModel):
    """Base class for visual effects applied to a segment during video assembly.

    Each segment has exactly one effect that controls how the still image
    is animated over its duration (e.g. Ken Burns pan/zoom, static hold, etc.).
    Subclasses must set a unique `type` literal for discriminated union dispatch
    and implement `apply_frame()`.
    """

    type: str

    @abstractmethod
    def apply_frame(
        self,
        source_image: np.ndarray,
        progress: float,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Transform a source image for the given animation progress (0–1).

        Returns an RGB numpy array of shape (output_height, output_width, 3).
        """
        ...

    model_config = {"arbitrary_types_allowed": True}


class KenBurnsDirection(str, Enum):
    """Camera movement direction for the Ken Burns pan/zoom effect."""

    zoom_in = "zoom_in"
    zoom_out = "zoom_out"
    pan_left = "pan_left"
    pan_right = "pan_right"
    pan_up = "pan_up"
    pan_down = "pan_down"


class KenBurnsEffect(SegmentEffect):
    """Ken Burns pan/zoom camera movement applied to a still image.

    Animates a crop window across an oversampled source image,
    creating the illusion of camera movement over the segment duration.
    """

    type: Literal["ken_burns"] = "ken_burns"
    direction: KenBurnsDirection
    scale: float = Field(ge=1.1, le=1.4)

    def apply_frame(
        self,
        source_image: np.ndarray,
        progress: float,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Apply Ken Burns pan/zoom crop and resize to output dimensions."""
        source_height, source_width = source_image.shape[:2]
        center_x = source_width // 2
        center_y = source_height // 2
        direction = self.direction.value

        if direction == "zoom_in":
            current_scale = 1.0 + (self.scale - 1.0) * progress
        elif direction == "zoom_out":
            current_scale = self.scale - (self.scale - 1.0) * progress
        else:
            current_scale = self.scale

        crop_width = int(source_width / current_scale)
        crop_height = int(source_height / current_scale)
        pan_offset_x = (source_width - crop_width) // 2
        pan_offset_y = (source_height - crop_height) // 2

        if direction == "pan_left":
            center_x += int(pan_offset_x * (1 - progress))
        elif direction == "pan_right":
            center_x -= int(pan_offset_x * (1 - progress))
        elif direction == "pan_up":
            center_y += int(pan_offset_y * (1 - progress))
        elif direction == "pan_down":
            center_y -= int(pan_offset_y * (1 - progress))

        import cv2

        x_start = max(0, center_x - crop_width // 2)
        y_start = max(0, center_y - crop_height // 2)
        cropped = source_image[
            y_start : y_start + crop_height, x_start : x_start + crop_width
        ]
        return cv2.resize(
            cropped, (output_width, output_height), interpolation=cv2.INTER_LINEAR
        )


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
