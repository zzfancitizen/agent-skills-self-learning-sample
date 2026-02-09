"""
Executor Agent - Execute specific operations
"""

from pathlib import Path

from langchain_core.messages import BaseMessage, AIMessage

from ..base import BaseAgent
from ...skills.registry import SkillRegistry
from ...skills.loader import SkillLoader


class ExecutorAgent(BaseAgent):
    """
    Executor Agent

    Executes specific operations based on proposals
    """

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        # Discover and register all skills from skills/ subdirectory
        agent_dir = Path(__file__).parent
        skills = SkillLoader.load_agent_skills(agent_dir, lazy=skill_registry._lazy)
        for skill in skills:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

    @property
    def agent_name(self) -> str:
        return "ExecutorAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["execution"]

    @property
    def base_system_prompt(self) -> str:
        return """You are an Executor Agent. Your task is to execute specific operations based on a given proposal.

Before your main reply, first output your reasoning using <thinking> tags:

<thinking>
Write your execution approach here:
- Your understanding of the task goal
- How you plan to execute
- Potential issues and contingency plans
</thinking>

Execution principles:
1. Strictly follow the proposal steps
2. Confirm the result of each step
3. Report errors promptly when encountered
4. Record all operations and their results

Your reply format:

## Execution Plan
- List the operations to be executed

## Execution Process
- Record the execution status of each step

## Execution Results
- Summarize the execution results
- List successful and failed operations
- If errors occurred, explain causes and suggestions

Ensure the execution process is transparent and results are clear.
"""

    def process(
        self,
        messages: list[BaseMessage],
        proposal: str = "",
        tasks: list[str] = None,
        **kwargs
    ) -> dict:
        """
        Execute operations

        Args:
            messages: Conversation history
            proposal: Proposal from ProposalAgent
            tasks: List of specific execution tasks

        Returns:
            {
                "thinking": str,
                "execution_log": str,
                "success": bool,
                "results": list[dict]
            }
        """
        from langchain_core.messages import HumanMessage

        # Build execution context
        context_parts = []
        if proposal:
            context_parts.append(f"## Proposal\n{proposal}")
        if tasks:
            context_parts.append(f"## Tasks to Execute\n" + "\n".join(f"- {t}" for t in tasks))

        if context_parts:
            context_message = HumanMessage(
                content="Please execute the following operations based on the information below:\n\n" + "\n\n".join(context_parts)
            )
            messages = messages + [context_message]

        response = self.invoke(messages)

        # Extract thinking content
        import re
        content = response.content
        thinking = ""
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove thinking tags from content
            execution_log = re.sub(r'<thinking>.*?</thinking>\s*', '', content, flags=re.DOTALL).strip()
        else:
            execution_log = content

        # Simple check for execution success
        content_lower = content.lower()
        success = "failed" not in content_lower and "error" not in content_lower

        return {
            "thinking": thinking,
            "execution_log": execution_log,
            "success": success,
            "results": [],
            "raw_response": response
        }
