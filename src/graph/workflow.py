"""
Workflow - LangGraph multi-agent workflow
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END # type: ignore[import-unresolved]
from langchain_core.messages import AIMessage # type: ignore[import-unresolved]

from .state import AgentState
from ..agents import RouterAgent, ProposalAgent, ExecutorAgent
from ..skills import SkillRegistry

logger = logging.getLogger(__name__)


def create_workflow(skill_registry: SkillRegistry, checkpointer=None, **agent_kwargs):
    """
    Create multi-agent workflow

    Args:
        skill_registry: Skill registry
        checkpointer: Optional LangGraph checkpointer for conversation memory.
                       When provided, the workflow persists state across invocations
                       keyed by thread_id, enabling multi-turn conversations.
        **agent_kwargs: Extra arguments passed to agents (e.g. model, temperature)

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize Agents
    router = RouterAgent(skill_registry, **agent_kwargs)
    proposal = ProposalAgent(skill_registry, **agent_kwargs)
    executor = ExecutorAgent(skill_registry, **agent_kwargs)

    # Logging helper
    def _log_agent(agent_name: str, input_data: dict, output_data: dict):
        """Log agent invocation"""
        # Build INPUT section
        input_lines = []
        if "messages" in input_data:
            for i, msg in enumerate(input_data["messages"]):
                role = getattr(msg, "type", "unknown") if hasattr(msg, "type") else "unknown"
                content = getattr(msg, "content", str(msg))
                if len(content) > 500:
                    content = content[:500] + "..."
                input_lines.append(f"  [{i}] {role}: {content}")
        for key, value in input_data.items():
            if key != "messages" and value:
                val_str = str(value)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                input_lines.append(f"  {key}: {val_str}")

        logger.info("AGENT: %s | INPUT:\n%s", agent_name, "\n".join(input_lines))

        # Log THINKING (if present)
        if "thinking" in output_data and output_data["thinking"]:
            thinking = output_data["thinking"]
            if len(thinking) > 800:
                thinking = thinking[:800] + "..."
            thinking_lines = "\n".join(f"  {line}" for line in thinking.split("\n"))
            logger.debug("AGENT: %s | THINKING:\n%s", agent_name, thinking_lines)

        # Build OUTPUT section
        output_lines = []
        for key, value in output_data.items():
            if key in ("thinking", "raw_response"):
                continue
            if value is not None:
                val_str = str(value)
                if len(val_str) > 500:
                    val_str = val_str[:500] + "..."
                output_lines.append(f"  {key}: {val_str}")

        logger.info("AGENT: %s | OUTPUT:\n%s", agent_name, "\n".join(output_lines))

    # Define node functions
    def route_node(state: AgentState) -> dict:
        """Router node"""
        input_data = {"messages": state["messages"]}

        result = router.process(state["messages"])

        output = {
            "current_agent": "router",
            "thinking": result.get("thinking", ""),
            "route": result.get("route"),
            "task": result.get("extracted_task"),
            "final_response": result.get("direct_response") if result.get("route") == "direct_response" else None,
        }

        _log_agent("RouterAgent", input_data, output)
        return output

    def proposal_node(state: AgentState) -> dict:
        """Proposal node"""
        input_data = {
            "messages": state["messages"],
            "task": state.get("task", "")
        }

        result = proposal.process(
            state["messages"],
            task=state.get("task", "")
        )

        output = {
            "current_agent": "proposal",
            "thinking": result.get("thinking", ""),
            "proposal": result.get("analysis"),
            "messages": [AIMessage(content=result.get("analysis", ""))],
        }

        _log_agent("ProposalAgent", input_data, output)
        return output

    def executor_node(state: AgentState) -> dict:
        """Executor node"""
        input_data = {
            "messages": state["messages"],
            "proposal": state.get("proposal", "")
        }

        result = executor.process(
            state["messages"],
            proposal=state.get("proposal", ""),
            tasks=[]
        )

        output = {
            "current_agent": "executor",
            "thinking": result.get("thinking", ""),
            "execution_result": result.get("execution_log"),
            "final_response": result.get("execution_log"),
            "messages": [AIMessage(content=result.get("execution_log", ""))],
        }

        _log_agent("ExecutorAgent", input_data, output)
        return output

    def finalize_node(state: AgentState) -> dict:
        """Final output node"""
        # Use final_response if available, otherwise fall back to proposal or execution_result
        final = (
            state.get("final_response") or
            state.get("execution_result") or
            state.get("proposal") or
            "Unable to process this request"
        )
        return {
            "final_response": final,
        }

    # Route condition functions
    def route_decision(state: AgentState) -> Literal["proposal", "executor", "finalize"]:
        """Select next node based on routing decision"""
        route = state.get("route", "proposal")
        if route == "direct_response":
            return "finalize"
        elif route == "executor":
            return "executor"
        else:
            return "proposal"

    def proposal_decision(state: AgentState) -> Literal["executor", "finalize"]:
        """Decide whether execution is needed"""
        # Simplified logic: check if proposal mentions execution-related keywords
        proposal = state.get("proposal", "")
        if "execute" in proposal.lower() or "operation" in proposal.lower():
            return "executor"
        return "finalize"

    # Build Graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", route_node)
    workflow.add_node("proposal", proposal_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "proposal": "proposal",
            "executor": "executor",
            "finalize": "finalize",
        }
    )

    workflow.add_conditional_edges(
        "proposal",
        proposal_decision,
        {
            "executor": "executor",
            "finalize": "finalize",
        }
    )

    # Regular edges
    workflow.add_edge("executor", "finalize")
    workflow.add_edge("finalize", END)

    # Compile (with optional checkpointer for conversation memory)
    return workflow.compile(checkpointer=checkpointer)


def run_workflow(
    user_input: str,
    registry: SkillRegistry = None,
    **agent_kwargs
) -> str:
    """
    Convenience function: run the workflow

    Args:
        user_input: User input
        registry: SkillRegistry instance; if None, an empty registry is created
        **agent_kwargs: Agent parameters

    Returns:
        Final response string
    """
    from .state import create_initial_state

    # If no registry provided, create empty one (agents will self-load their skills)
    if registry is None:
        registry = SkillRegistry()

    # Create and run workflow
    workflow = create_workflow(registry, **agent_kwargs)
    initial_state = create_initial_state(user_input)

    final_state = workflow.invoke(initial_state)

    return final_state.get("final_response", "")
