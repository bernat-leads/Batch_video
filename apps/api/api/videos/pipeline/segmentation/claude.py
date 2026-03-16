"""Claude segmentation implementation."""

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
                    "Word timestamps:\n{timestamps_text}\n\n"
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
                    timestamps_text=self._format_timestamps(word_timestamps),
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
        segments = result["parsed"].segments
        cost = (
            input_tokens * SEGMENTATION_INPUT_TOKEN_COST
            + output_tokens * SEGMENTATION_OUTPUT_TOKEN_COST
        )

        logger.info(
            "Segmentation complete (%d segments, %d tokens, $%.4f)",
            len(segments),
            input_tokens + output_tokens,
            cost,
        )

        return SegmentationResult(
            segments=segments,
            prompt=prompt,
            cost=AICost(token_count=input_tokens + output_tokens, cost_usd=cost),
        )

    @staticmethod
    def _format_timestamps(word_timestamps: list[WordTimestamp]) -> str:
        return "\n".join(
            f"  {wt.word}: {wt.start:.2f}s – {wt.end:.2f}s" for wt in word_timestamps
        )
