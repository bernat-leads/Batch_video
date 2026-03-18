"""Claude segmentation implementation.

Uses LangChain's with_structured_output which passes the Pydantic schema
as a tool definition — Claude returns validated structured data directly.
"""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.exceptions import OutputParserException
from langchain_core.outputs import LLMResult
from pydantic import ValidationError

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


class _UsageCallback(BaseCallbackHandler):
    """Captures token usage from the LLM response."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        for generations in response.generations:
            for gen in generations:
                usage = getattr(gen, "generation_info", {}) or {}
                usage_meta = usage.get("usage_metadata") or {}
                self.input_tokens += usage_meta.get("input_tokens", 0)
                self.output_tokens += usage_meta.get("output_tokens", 0)


class ClaudeSegmentationService(SegmentationService):
    """Claude-powered script segmentation into visual segments."""

    def __init__(self) -> None:
        """Initialize the Claude LLM with structured output (no include_raw)."""
        self._chain = ChatAnthropic(
            model=SEGMENTATION_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=SEGMENTATION_MAX_TOKENS,
        ).with_structured_output(SegmentationOutput)

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

        prompt_messages = segmentation_input.build_messages()
        usage_cb = _UsageCallback()

        try:
            parsed: SegmentationOutput = await self._chain.ainvoke(
                prompt_messages, config={"callbacks": [usage_cb]}
            )
        except (OutputParserException, ValidationError):
            raise  # Retryable — let tenacity handle it
        except Exception as error:
            raise PipelineStageError(
                "segmentation", f"Claude API call failed: {error}"
            ) from error

        input_cost, output_cost = get_token_costs(SEGMENTATION_MODEL)
        total_tokens = usage_cb.input_tokens + usage_cb.output_tokens
        cost = AICost(
            token_count=total_tokens,
            cost_usd=(
                usage_cb.input_tokens * input_cost
                + usage_cb.output_tokens * output_cost
            ),
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
