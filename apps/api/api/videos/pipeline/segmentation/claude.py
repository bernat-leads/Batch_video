"""Claude segmentation implementation.

The LLM returns segments with text, timing, image prompts, and Ken Burns
config directly via structured output (tool_use) — no post-processing needed.
"""

import logging

from langchain_anthropic import ChatAnthropic

from api.core.exceptions import PipelineStageError
from api.core.schemas import AICost
from api.settings import settings
from api.videos.pipeline.config import SEGMENTATION_MAX_TOKENS, SEGMENTATION_MODEL
from api.videos.pipeline.costs import get_token_costs
from api.videos.pipeline.segmentation.base import SegmentationService
from api.videos.pipeline.segmentation.schemas import (
    SegmentationInput,
    SegmentationOutput,
    SegmentationResult,
)
from api.videos.utils import pipeline_retry

logger = logging.getLogger(__name__)


class ClaudeSegmentationService(SegmentationService):
    """Claude-powered script segmentation into visual segments."""

    def __init__(self) -> None:
        """Initialize the Claude LLM chain with structured output."""
        self._chain = ChatAnthropic(
            model=SEGMENTATION_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=SEGMENTATION_MAX_TOKENS,
        ).with_structured_output(SegmentationOutput, include_raw=True)

    @pipeline_retry()
    async def segment_script(
        self, segmentation_input: SegmentationInput
    ) -> SegmentationResult:
        """Segment script into visual chunks using Claude."""
        logger.info(
            "Segmentation starting (%d chars, %d words, style=%s)",
            len(segmentation_input.script_text),
            len(segmentation_input.word_timestamps),
            segmentation_input.style or "default",
        )

        prompt_messages = segmentation_input.build_prompt().format_messages()

        try:
            result = await self._chain.ainvoke(prompt_messages)
        except Exception as error:
            raise PipelineStageError(
                "segmentation", f"Claude API call failed: {error}"
            ) from error

        parsed: SegmentationOutput | None = result["parsed"]
        if parsed is None:
            parsing_error = result.get("parsing_error")
            raise PipelineStageError(
                "segmentation",
                f"Structured output validation failed: {parsing_error}",
            )

        input_cost, output_cost = get_token_costs(SEGMENTATION_MODEL)
        cost = AICost.from_chain_result(
            result,
            input_cost_per_token=input_cost,
            output_cost_per_token=output_cost,
        )

        logger.info(
            "Segmentation complete (%d segments, %d tokens, $%.4f)",
            len(parsed.segments),
            cost.token_count,
            cost.cost_usd,
        )

        return SegmentationResult(
            segments=parsed.segments,
            prompt=segmentation_input.prompt,
            cost=cost,
        )
