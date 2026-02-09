"""
Base Agent - 带 Skill 支持的基础 Agent 类
"""

from abc import ABC, abstractmethod
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_litellm import ChatLiteLLM

from ..skills.registry import SkillRegistry


class BaseAgent(ABC):
    """
    带 Skill 支持的基础 Agent
    
    子类需要实现:
    - agent_name: 返回 agent 名称
    - default_skills: 返回默认 skill 列表
    - process: 处理消息并返回响应
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        model: str = "sap/anthropic--claude-4.5-opus",
        temperature: float = 0.0,
        additional_skills: Optional[list[str]] = None,
    ):
        """
        初始化 Agent
        
        Args:
            skill_registry: Skill 注册中心
            model: 使用的模型名称
            temperature: 温度参数
            additional_skills: 额外的 skill 名称列表
        """
        self.skill_registry = skill_registry
        self.model = model
        self.temperature = temperature
        
        # 合并默认 skills 和额外 skills
        self._active_skills = list(self.default_skills)
        if additional_skills:
            self._active_skills.extend(additional_skills)
        
        # 初始化 LLM
        self._llm = ChatLiteLLM(
            model=model,
            temperature=temperature,
            max_tokens=4096,
        )

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """返回 Agent 名称"""
        pass

    @property
    @abstractmethod
    def default_skills(self) -> list[str]:
        """返回该 Agent 默认使用的 skill 名称列表"""
        pass

    @property
    @abstractmethod
    def base_system_prompt(self) -> str:
        """返回基础 system prompt（不含 skills 部分）"""
        pass

    def get_system_prompt(self) -> str:
        """
        构建完整的 system prompt（包含 skills）
        """
        skills_prompt = self.skill_registry.get_skills_prompt(self._active_skills)
        
        return f"""{self.base_system_prompt}

{skills_prompt}

当任务与上述 skills 相关时，你必须严格按照 skill 中的指令执行。
"""

    def add_skill(self, skill_name: str) -> bool:
        """
        动态添加 skill
        
        Returns:
            是否成功添加
        """
        if skill_name not in self._active_skills:
            if self.skill_registry.get(skill_name):
                self._active_skills.append(skill_name)
                return True
        return False

    def remove_skill(self, skill_name: str) -> bool:
        """
        移除 skill
        
        Returns:
            是否成功移除
        """
        if skill_name in self._active_skills:
            self._active_skills.remove(skill_name)
            return True
        return False

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        """
        调用 LLM 生成响应
        
        Args:
            messages: 消息列表
            
        Returns:
            AI 响应消息
        """
        system_message = SystemMessage(content=self.get_system_prompt())
        full_messages = [system_message] + messages
        
        response = self._llm.invoke(full_messages)
        return response

    @abstractmethod
    def process(self, messages: list[BaseMessage], **kwargs) -> dict:
        """
        处理消息并返回结果
        
        Args:
            messages: 输入消息列表
            **kwargs: 额外参数
            
        Returns:
            处理结果字典
        """
        pass
