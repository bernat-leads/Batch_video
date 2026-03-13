"""Agent graph — conversation loop with optional tools.

Flow:
  START -> conversation -> (tool_calls?) -> tools -> conversation -> ...
                                         -> END
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.nodes.conversation import TOOLS, conversation_node
from agents.state import ChatState, NodeID


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    """Build and compile the agent graph."""
    g = StateGraph(ChatState)

    g.add_node(NodeID.CONVERSATION, conversation_node)

    g.set_entry_point(NodeID.CONVERSATION)

    if TOOLS:
        g.add_node(NodeID.TOOLS, ToolNode(TOOLS))

        g.add_conditional_edges(
            NodeID.CONVERSATION,
            tools_condition,
            {NodeID.TOOLS: NodeID.TOOLS, END: END},
        )
        g.add_edge(NodeID.TOOLS, NodeID.CONVERSATION)
    else:
        g.add_edge(NodeID.CONVERSATION, END)

    return g.compile(checkpointer=checkpointer)
