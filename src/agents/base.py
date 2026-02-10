"""
Base Agent - Base Agent class with Skill support
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from langchain_anthropic import ChatAnthropic # type: ignore[import-unresolved]
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage # type: ignore[import-unresolved]
from langchain_core.tools import BaseTool # type: ignore[import-unresolved]
from langchain_litellm import ChatLiteLLM # type: ignore[import-unresolved]

from ..skills.registry import SkillRegistry
from ..skills.loader import create_load_skill_tool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base Agent with Skill support

    Subclasses must implement:
    - agent_name: Return agent name
    - default_skills: Return default skill name list
    - process: Process messages and return response
    """

    # Max tool call loop iterations to prevent infinite loops
    MAX_TOOL_ITERATIONS = 10

    def __init__(
        self,
        skill_registry: SkillRegistry,
        model: str = "sap/anthropic--claude-4.5-opus",
        temperature: float = 0.0,
        additional_skills: Optional[list[str]] = None,
    ):
        """
        Initialize Agent

        Args:
            skill_registry: Skill registry
            model: Model name to use
            temperature: Temperature parameter
            additional_skills: Additional skill name list
        """
        self.skill_registry = skill_registry
        self.model = model
        self.temperature = temperature

        # Merge default skills and additional skills
        self._active_skills = list(self.default_skills)
        if additional_skills:
            self._active_skills.extend(additional_skills)

        # Tool registry: tool_name -> tool_instance
        self._tools: dict[str, BaseTool] = {}

        # Initialize LLM
        self._llm = ChatLiteLLM(
            model=model,
            temperature=temperature,
            max_tokens=16384,
        )

        # Auto-register the load_skill tool so the LLM can lazily load skill
        # content on demand (system prompt only contains summaries).
        if self._active_skills:
            load_skill_tool = create_load_skill_tool(skill_registry, self._active_skills)
            self.register_tools([load_skill_tool])

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return Agent name"""
        pass

    @property
    @abstractmethod
    def default_skills(self) -> list[str]:
        """Return default skill name list for this Agent"""
        pass

    @property
    @abstractmethod
    def base_system_prompt(self) -> str:
        """Return base system prompt (without skills section)"""
        pass

    def get_system_prompt(self) -> str:
        """
        Build complete system prompt.

        Only skill **summaries** (name + description) are included here.
        The LLM should call the ``load_skill`` tool to obtain the full
        instructions for a skill before performing the related task.
        """
        skills_summary = self.skill_registry.get_skills_summary_for(
            self._active_skills
        )

        return f"""{self.base_system_prompt}

{skills_summary}

When a task relates to one of the skills listed above, use the `load_skill` tool to load the full instructions for that skill before proceeding.
"""

    def add_skill(self, skill_name: str) -> bool:
        """
        Dynamically add a skill

        Returns:
            Whether the skill was successfully added
        """
        if skill_name not in self._active_skills:
            if self.skill_registry.get(skill_name):
                self._active_skills.append(skill_name)
                return True
        return False

    def remove_skill(self, skill_name: str) -> bool:
        """
        Remove a skill

        Returns:
            Whether the skill was successfully removed
        """
        if skill_name in self._active_skills:
            self._active_skills.remove(skill_name)
            return True
        return False

    def register_tools(self, tools: list[BaseTool]) -> None:
        """
        Register tools and bind them to the LLM

        Args:
            tools: List of tool instances
        """
        for tool in tools:
            self._tools[tool.name] = tool
        if self._tools:
            self._llm = self._llm.bind_tools(list(self._tools.values()))

    def _log_tool_call(self, tool_call: dict) -> None:
        """Log tool invocation"""
        tool_name = tool_call.get("name", "unknown")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id", "")

        args_lines = "\n".join(
            f"       {k}: {str(v)[:300] + '...' if len(str(v)) > 300 else v}"
            for k, v in tool_args.items()
        )
        logger.info(
            "TOOL CALL: %s | ID: %s | Agent: %s\n     Args:\n%s",
            tool_name, tool_id, self.agent_name, args_lines
        )

    def _log_tool_result(self, tool_call: dict, result: str) -> None:
        """Log tool execution result"""
        tool_name = tool_call.get("name", "unknown")
        tool_id = tool_call.get("id", "")

        result_str = str(result)
        if len(result_str) > 500:
            result_str = result_str[:500] + "..."
        logger.info(
            "TOOL RESULT: %s | ID: %s | Agent: %s | Result: %s",
            tool_name, tool_id, self.agent_name, result_str
        )

    def _execute_tool(self, tool_call: dict) -> str:
        """
        Execute a single tool call

        Args:
            tool_call: Tool call info {name, args, id}

        Returns:
            Tool execution result string
        """
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})

        tool = self._tools.get(tool_name)
        if tool is None:
            return f"Error: Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}"

        try:
            result = tool.invoke(tool_args)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        """
        Invoke LLM to generate a response, with tool call loop support.

        When the LLM returns tool calls, automatically executes tools, logs results,
        and feeds results back to the LLM until a final text response is produced.

        Args:
            messages: Message list

        Returns:
            AI response message
        """
        system_prompt = self.get_system_prompt()
        system_message = SystemMessage(content=system_prompt)
        full_messages = [system_message] + messages

        # Log the full prompt sent to the LLM on the first iteration
        logger.info(
            "PROMPT -> %s | System prompt (%d chars):\n%s",
            self.agent_name, len(system_prompt), system_prompt,
        )
        for i, msg in enumerate(messages):
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", str(msg))
            preview = content[:500] + "..." if len(content) > 500 else content
            logger.info(
                "PROMPT -> %s | Message[%d] %s: %s",
                self.agent_name, i, role, preview,
            )

        for iteration in range(self.MAX_TOOL_ITERATIONS):
            if iteration > 0:
                # Log follow-up iterations so we can see tool results fed back
                logger.info(
                    "PROMPT -> %s | Tool-loop iteration %d, total messages: %d",
                    self.agent_name, iteration, len(full_messages),
                )
            response = self._llm.invoke(full_messages)

            # Check for tool calls
            tool_calls = getattr(response, "tool_calls", None)
            if not tool_calls:
                return response

            # Tool calls present: log, execute, collect results
            full_messages.append(response)

            for tool_call in tool_calls:
                # Log: tool call
                self._log_tool_call(tool_call)

                # Execute tool
                result = self._execute_tool(tool_call)

                # Log: tool result
                self._log_tool_result(tool_call, result)

                # Build ToolMessage to feed back to LLM
                tool_message = ToolMessage(
                    content=result,
                    tool_call_id=tool_call.get("id", ""),
                )
                full_messages.append(tool_message)

        # Exceeded max iterations, return last response
        logger.warning(
            "%s: Reached max tool iterations (%d)", self.agent_name, self.MAX_TOOL_ITERATIONS
        )
        return response

    @abstractmethod
    def process(self, messages: list[BaseMessage], **kwargs) -> dict:
        """
        Process messages and return results

        Args:
            messages: Input message list
            **kwargs: Extra arguments

        Returns:
            Result dictionary
        """
        pass
