"""
Router Agent - 路由请求到合适的处理 Agent
"""

from typing import Literal
import json
import re

from langchain_core.messages import BaseMessage, AIMessage

from .base import BaseAgent
from ..skills.registry import SkillRegistry


class RouterAgent(BaseAgent):
    """
    路由 Agent
    
    分析用户请求，决定应该由哪个 Agent 处理
    """

    VALID_ROUTES = ["proposal", "executor", "direct_response"]

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        super().__init__(skill_registry, **kwargs)

    @property
    def agent_name(self) -> str:
        return "RouterAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["routing"]

    @property
    def base_system_prompt(self) -> str:
        return f"""你是一个智能路由 Agent。你的任务是分析用户请求，并决定应该由哪个 Agent 处理。

可用的路由目标：
- proposal: 需要分析问题并提出方案建议的请求
- executor: 需要执行具体操作的请求
- direct_response: 简单的问答，可以直接回复

你必须以 JSON 格式返回路由决策：
```json
{{
    "thinking": "你的思考过程，分析用户意图、考虑的因素等",
    "route": "proposal|executor|direct_response",
    "reason": "选择该路由的原因",
    "extracted_task": "从用户请求中提取的核心任务描述",
    "direct_response": "如果 route 是 direct_response，这里是回复内容"
}}
```
"""

    def process(self, messages: list[BaseMessage], **kwargs) -> dict:
        """
        分析请求并返回路由决策
        
        Returns:
            {
                "route": str,
                "reason": str,
                "extracted_task": str,
                "direct_response": Optional[str]
            }
        """
        response = self.invoke(messages)
        
        # 解析 JSON 响应
        try:
            # 尝试从响应中提取 JSON
            content = response.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
            
            # 验证路由
            if result.get("route") not in self.VALID_ROUTES:
                result["route"] = "proposal"  # 默认路由
            
            # 确保 thinking 字段存在
            if "thinking" not in result:
                result["thinking"] = result.get("reason", "")
            
            return result
        except json.JSONDecodeError:
            # 解析失败时的默认行为
            return {
                "thinking": "无法解析 LLM 响应",
                "route": "proposal",
                "reason": "无法解析路由决策，默认使用 proposal",
                "extracted_task": messages[-1].content if messages else "",
                "direct_response": None
            }
