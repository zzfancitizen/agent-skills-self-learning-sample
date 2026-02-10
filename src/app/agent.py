import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Literal

from src.graph.state import create_initial_state
from src.graph.workflow import create_workflow
from src.skills import SkillRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    """Core agent that wraps the existing multi-agent workflow for A2A service."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self, model: str = "sap/anthropic--claude-4.5-sonnet"):
        self.registry = SkillRegistry()
        self.model = model
        self.workflow = create_workflow(self.registry, model=model)

    async def stream(self, query: str, context_id: str) -> AsyncGenerator[dict, None]:
        yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}
        try:
            initial_state = create_initial_state(query)
            final_state = await self.workflow.ainvoke(initial_state)
            response = final_state.get("final_response", "")
            yield {"is_task_complete": True, "require_user_input": False, "content": response}
        except Exception as e:
            logger.exception("Agent stream error")
            yield {"is_task_complete": True, "require_user_input": False, "content": f"Error: {e}"}

    def invoke(self, query: str, context_id: str) -> AgentResponse:
        import asyncio
        try:
            initial_state = create_initial_state(query)
            final_state = asyncio.run(self.workflow.ainvoke(initial_state))
            response = final_state.get("final_response", "")
            return AgentResponse(status="completed", message=response)
        except Exception as e:
            return AgentResponse(status="error", message=f"Error: {e}")
