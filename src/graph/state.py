"""
Agent State - LangGraph state definition
"""

from typing import Annotated, TypedDict, Optional, Literal
from langgraph.graph import add_messages # type: ignore[import-unresolved]
from langchain_core.messages import BaseMessage # type: ignore[import-unresolved]


class AgentState(TypedDict):
    """
    Multi-Agent workflow state

    Attributes:
        messages: Conversation message history (auto-accumulated via add_messages reducer)
        current_agent: Name of the currently active agent
        route: Routing decision
        task: Extracted task description
        proposal: Proposal from ProposalAgent
        execution_result: Execution result
        final_response: Final response
        error: Error message
    """
    # Message history - uses Annotated to support message accumulation
    messages: Annotated[list[BaseMessage], add_messages]

    # Flow control
    current_agent: str
    route: Optional[str]

    # Agent outputs
    task: Optional[str]
    proposal: Optional[str]
    execution_result: Optional[str]
    final_response: Optional[str]

    # Error handling
    error: Optional[str]


def create_initial_state(user_message: str) -> AgentState:
    """
    Create initial state for a new workflow invocation.

    When used with a checkpointer (conversation memory), the ``messages``
    field uses the ``add_messages`` reducer so the new HumanMessage is
    **appended** to existing conversation history rather than replacing it.
    All other fields are explicitly reset so each workflow run starts with
    a clean slate for routing, proposals, and execution.

    Args:
        user_message: User input

    Returns:
        Initialized AgentState
    """
    from langchain_core.messages import HumanMessage # type: ignore[import-unresolved]

    return {
        "messages": [HumanMessage(content=user_message)],
        # Reset workflow-specific fields for this run
        "current_agent": "",
        "route": None,
        "task": None,
        "proposal": None,
        "execution_result": None,
        "final_response": None,
        "error": None,
    }
