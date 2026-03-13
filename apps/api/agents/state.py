"""Chat graph state schema."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from copilotkit import CopilotKitState
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from api.core.schemas import Locale


class NodeID(StrEnum):
    CONVERSATION = "conversation"
    TOOLS = "tools"


class ChatState(CopilotKitState):
    """State for the conversational agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    locale: Locale = Locale.EN
    user_id: UUID
    user_name: str = ""
