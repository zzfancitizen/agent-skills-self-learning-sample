"""
Agent State - LangGraph state definition
"""

from typing import Annotated, TypedDict, Optional, Literal
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


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
    Create initial state

    Args:
        user_message: User input

    Returns:
        Initialized AgentState
    """
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=user_message)],
        "current_agent": "",
        "route": None,
        "task": None,
        "proposal": None,
        "execution_result": None,
        "final_response": None,
        "error": None,
    }
