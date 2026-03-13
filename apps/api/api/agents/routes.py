"""Agent routes — CopilotKit / AG-UI endpoints."""

import logging

from ag_ui.core.types import RunAgentInput
from ag_ui.encoder import EventEncoder
from copilotkit import LangGraphAGUIAgent
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from agents.checkpointer import CheckpointerDep
from agents.graph import build_graph
from api.core.schemas import Locale
from api.deps.auth import User, get_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["agents"])


@router.post("/copilotkit/agent")
async def agent_endpoint(
    checkpointer: CheckpointerDep,
    input_data: RunAgentInput,
    request: Request,
    user: User = Depends(get_user),
):
    """CopilotKit / AG-UI streaming endpoint for the agent.

    Auth is enforced via get_user (Bearer JWT validated against Better Auth JWKS).
    The verified user.id is injected into state, overriding any client-supplied value.
    """
    state = dict(input_data.state) if isinstance(input_data.state, dict) else {}
    state["user_id"] = user.id
    state["user_name"] = user.name or ""

    # Locale from X-Locale header (set by Next.js CopilotKit route from NEXT_LOCALE cookie).
    raw_locale = request.headers.get("x-locale", "").strip().lower()[:2]
    state["locale"] = (
        raw_locale if raw_locale in Locale.__members__.values() else Locale.EN
    )

    modified_input = input_data.model_copy(update={"state": state})
    accept_header = request.headers.get("accept")
    encoder = EventEncoder(accept=accept_header)

    agent = LangGraphAGUIAgent(
        name="agent",
        description="AI assistant agent.",
        graph=build_graph(checkpointer),
    )

    async def event_generator():
        async for event in agent.run(modified_input):
            yield encoder.encode(event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type(),
    )
