"""Visual effect renderers for video assembly."""

from abc import ABC, abstractmethod

import cv2
import numpy as np

from api.videos.pipeline.segmentation.schemas import KenBurnsEffect, SegmentEffect


class EffectService(ABC):
    """Abstract effect service — applies visual effects to still images."""

    @abstractmethod
    def apply(
        self,
        effect: SegmentEffect,
        source_image: np.ndarray,
        progress: float,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Apply the effect to a source image at the given animation progress."""
        ...


class NumpyEffectService(EffectService):
    """Effect service using numpy/cv2 for image manipulation."""

    def apply(
        self,
        effect: SegmentEffect,
        source_image: np.ndarray,
        progress: float,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        match effect.type:
            case "ken_burns":
                return self._ken_burns(effect, source_image, progress, output_width, output_height)
            case _:
                raise ValueError(f"Unknown effect type: {effect.type}")

    @staticmethod
    def _ken_burns(
        effect: KenBurnsEffect,
        source_image: np.ndarray,
        progress: float,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        """Apply Ken Burns pan/zoom crop and resize."""
        source_height, source_width = source_image.shape[:2]
        center_x = source_width // 2
        center_y = source_height // 2
        direction = effect.direction.value

        if direction == "zoom_in":
            current_scale = 1.0 + (effect.scale - 1.0) * progress
        elif direction == "zoom_out":
            current_scale = effect.scale - (effect.scale - 1.0) * progress
        else:
            current_scale = effect.scale

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

        x_start = max(0, center_x - crop_width // 2)
        y_start = max(0, center_y - crop_height // 2)
        cropped = source_image[y_start:y_start + crop_height, x_start:x_start + crop_width]
        return cv2.resize(cropped, (output_width, output_height), interpolation=cv2.INTER_LINEAR)
