"""
Router Agent - Route requests to the appropriate handling Agent
"""

from pathlib import Path
from typing import Literal
import json
import re

from langchain_core.messages import BaseMessage, AIMessage

from ..base import BaseAgent
from ...skills.registry import SkillRegistry
from ...skills.loader import SkillLoader


class RouterAgent(BaseAgent):
    """
    Router Agent

    Analyzes user requests and decides which Agent should handle them
    """

    VALID_ROUTES = ["proposal", "executor", "direct_response"]

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        # Load router agent's own skill (SKILL.md at agent root)
        agent_dir = Path(__file__).parent
        skill = SkillLoader.load_skill(agent_dir)
        if skill:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

    @property
    def agent_name(self) -> str:
        return "RouterAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["routing"]

    @property
    def base_system_prompt(self) -> str:
        return f"""You are an intelligent routing Agent. Your task is to analyze user requests and decide which Agent should handle them.

Available routing targets:
- proposal: Requests that require analyzing problems and proposing solutions
- executor: Requests that require executing specific operations
- direct_response: Simple Q&A that can be answered directly

You must return your routing decision in JSON format:
```json
{{
    "thinking": "Your reasoning process, analyzing user intent, factors considered, etc.",
    "route": "proposal|executor|direct_response",
    "reason": "Reason for choosing this route",
    "extracted_task": "Core task description extracted from the user request",
    "direct_response": "If route is direct_response, the reply content goes here"
}}
```
"""

    def process(self, messages: list[BaseMessage], **kwargs) -> dict:
        """
        Analyze request and return routing decision

        Returns:
            {
                "route": str,
                "reason": str,
                "extracted_task": str,
                "direct_response": Optional[str]
            }
        """
        response = self.invoke(messages)

        # Parse JSON response
        try:
            # Attempt to extract JSON from response
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)

            # Validate route
            if result.get("route") not in self.VALID_ROUTES:
                result["route"] = "proposal"  # Default route

            # Ensure thinking field exists
            if "thinking" not in result:
                result["thinking"] = result.get("reason", "")

            return result
        except json.JSONDecodeError:
            # Default behavior on parse failure
            return {
                "thinking": "Failed to parse LLM response",
                "route": "proposal",
                "reason": "Could not parse routing decision, defaulting to proposal",
                "extracted_task": messages[-1].content if messages else "",
                "direct_response": None
            }
