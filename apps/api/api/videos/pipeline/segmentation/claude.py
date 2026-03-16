"""Claude segmentation implementation.

The LLM groups words into visual segments by index range and generates
image prompts + Ken Burns config. Timing comes directly from the TTS
word timestamps — just a lookup, no fuzzy matching needed.
"""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import (
    HEIGHT,
    SEGMENTATION_INPUT_TOKEN_COST,
    SEGMENTATION_MAX_TOKENS,
    SEGMENTATION_OUTPUT_TOKEN_COST,
    WIDTH,
)
from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.segmentation.schemas import (
    SegmentationOutput,
    SegmentationResult,
    SegmentResult,
    SegmentWithTiming,
)
from api.videos.pipeline.tts.schemas import WordTimestamp
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class ClaudeSegmentationService(SegmentationService):
    """Claude-powered script segmentation into visual segments."""

    _PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", "{master_prompt}"),
            (
                "human",
                (
                    "Script: {script_text}\n\n"
                    "Numbered word list:\n{timestamps_text}\n\n"
                    "Style/mood: {style}"
                ),
            ),
        ]
    )

    def __init__(self) -> None:
        self._chain = ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=SEGMENTATION_MAX_TOKENS,
        ).with_structured_output(SegmentationOutput, include_raw=True)

    @pipeline_retry()
    async def segment_script(
        self,
        script_text: str,
        word_timestamps: list[WordTimestamp],
        style: str | None,
        prompt: str,
    ) -> SegmentationResult:
        """Segment script into visual chunks using Claude."""
        logger.info(
            "Segmentation starting (%d chars, %d words, style=%s)",
            len(script_text),
            len(word_timestamps),
            style or "default",
        )

        try:
            result = self._chain.invoke(
                self._PROMPT.format_messages(
                    script_text=script_text,
                    timestamps_text=self._format_word_list(word_timestamps),
                    style=style or "cinematic, professional",
                    master_prompt=prompt,
                    width=WIDTH,
                    height=HEIGHT,
                )
            )
        except Exception as e:
            raise PipelineStageError(
                "segmentation", f"Claude API call failed: {e}"
            ) from e

        usage = result["raw"].usage_metadata or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        segments: list[SegmentResult] = result["parsed"].segments
        cost = (
            input_tokens * SEGMENTATION_INPUT_TOKEN_COST
            + output_tokens * SEGMENTATION_OUTPUT_TOKEN_COST
        )

        # Resolve word indices → text + timing from TTS timestamps
        segments_with_timing = _resolve_segments(segments, word_timestamps)

        logger.info(
            "Segmentation complete (%d segments, %d tokens, $%.4f)",
            len(segments_with_timing),
            input_tokens + output_tokens,
            cost,
        )

        return SegmentationResult(
            segments=segments_with_timing,
            prompt=prompt,
            cost=AICost(token_count=input_tokens + output_tokens, cost_usd=cost),
        )

    @staticmethod
    def _format_word_list(word_timestamps: list[WordTimestamp]) -> str:
        """Format words as a numbered list so the LLM can reference by index."""
        return "\n".join(
            f"  [{i}] {wt.word} ({wt.start:.2f}s–{wt.end:.2f}s)"
            for i, wt in enumerate(word_timestamps)
        )


def _resolve_segments(
    segments: list[SegmentResult],
    word_timestamps: list[WordTimestamp],
) -> list[SegmentWithTiming]:
    """Convert LLM word-index segments into timed segments.

    Direct index lookup — no fuzzy matching needed because the LLM
    references the exact word indices from the numbered list it received.
    """
    result: list[SegmentWithTiming] = []

    for seg in segments:
        start_idx = seg.start_word_index
        end_idx = seg.end_word_index

        # Clamp to valid range
        start_idx = max(0, min(start_idx, len(word_timestamps) - 1))
        end_idx = max(start_idx, min(end_idx, len(word_timestamps) - 1))

        text = " ".join(wt.word for wt in word_timestamps[start_idx : end_idx + 1])

        result.append(
            SegmentWithTiming(
                order=seg.order,
                text=text,
                image_prompt=seg.image_prompt,
                ken_burns_config=seg.ken_burns_config,
                start_time=word_timestamps[start_idx].start,
                end_time=word_timestamps[end_idx].end,
            )
        )

    return result
