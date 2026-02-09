"""
Proposal Agent - Analyze problems and generate solution proposals
"""

from pathlib import Path

from langchain_core.messages import BaseMessage, AIMessage

from ..base import BaseAgent
from ...skills.registry import SkillRegistry
from ...skills.loader import SkillLoader
from .tools.search_system import search_system_tool


class ProposalAgent(BaseAgent):
    """
    Proposal Agent

    Performs in-depth analysis and generates detailed solution proposals
    """

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        # Load proposal agent's own skill (SKILL.md at agent root)
        agent_dir = Path(__file__).parent
        skill = SkillLoader.load_skill(agent_dir)
        if skill:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

        # Register search_system tool (auto-binds to LLM with logging support)
        self.register_tools([search_system_tool])

    @property
    def agent_name(self) -> str:
        return "ProposalAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["analysis"]

    @property
    def base_system_prompt(self) -> str:
        return """You are a professional analysis Agent. Your task is to deeply analyze problems and generate detailed solution proposals.

Before your main reply, first output your reasoning using <thinking> tags:

<thinking>
Write your analysis approach here:
- How you understand the user's needs
- What factors you considered
- Why you chose this solution
</thinking>

Then, your formal reply must include the following sections:

## Problem Analysis
- Understand the user's core requirements
- Identify key constraints and limitations
- List factors to consider

## Solution Proposal
- Propose specific solutions
- Explain pros and cons of each solution
- Provide implementation steps

## Required Operations
- List specific operations for the Executor Agent to perform
- Prioritize by importance

Ensure your analysis is comprehensive and your suggestions are specific and actionable.
"""

    def process(self, messages: list[BaseMessage], task: str = "", **kwargs) -> dict:
        """
        Analyze problem and generate proposal

        Args:
            messages: Conversation history
            task: Task description extracted from router

        Returns:
            {
                "thinking": str,
                "analysis": str,
                "needs_execution": bool,
                "execution_tasks": list[str]
            }
        """
        # If there's an extracted task, add it to messages
        if task:
            from langchain_core.messages import HumanMessage
            task_message = HumanMessage(content=f"Please analyze the following task and propose a solution:\n\n{task}")
            messages = messages + [task_message]

        response = self.invoke(messages)

        # Extract thinking content
        import re
        content = response.content
        thinking = ""
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove thinking tags from content, keep formal reply
            analysis = re.sub(r'<thinking>.*?</thinking>\s*', '', content, flags=re.DOTALL).strip()
        else:
            analysis = content

        # Determine if execution is needed
        content_lower = content.lower()
        needs_execution = "execute" in content_lower or "operation" in content_lower

        return {
            "thinking": thinking,
            "analysis": analysis,
            "needs_execution": needs_execution,
            "execution_tasks": [],
            "raw_response": response
        }
