"""Conversation node — placeholder for the template.

Replace this with your application's conversation logic.
"""

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.state import ChatState

SYSTEM_PROMPT = """You are a helpful AI assistant. Have a natural conversation with the user.

Keep your responses concise and helpful."""

TOOLS: list = []


async def conversation_node(state: ChatState) -> dict:
    """Main conversation node — sends messages to the LLM and returns the response."""
    model = ChatOpenAI(model="gpt-4o", temperature=0.7)
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    response = await model.ainvoke(messages)

    return {"messages": [response]}
