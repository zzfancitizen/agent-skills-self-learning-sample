"""
Proposal Agent - 分析问题并生成方案建议
"""

from langchain_core.messages import BaseMessage, AIMessage

from .base import BaseAgent
from ..skills.registry import SkillRegistry


class ProposalAgent(BaseAgent):
    """
    提案 Agent
    
    深入分析问题，生成详细的方案建议
    """

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        super().__init__(skill_registry, **kwargs)

    @property
    def agent_name(self) -> str:
        return "ProposalAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["analysis"]

    @property
    def base_system_prompt(self) -> str:
        return """你是一个专业的分析 Agent。你的任务是深入分析问题，并生成详细的方案建议。

在开始你的回复前，请先用 <thinking> 标签输出你的思考过程：

<thinking>
在这里写下你的分析思路：
- 你是如何理解用户需求的
- 你考虑了哪些因素
- 为什么选择这个方案
</thinking>

然后，你的正式回复必须包含以下部分：

## 问题分析
- 理解用户的核心需求
- 识别关键约束和限制
- 列出需要考虑的因素

## 方案建议
- 提出具体的解决方案
- 说明方案的优缺点
- 给出实施步骤

## 需要执行的操作
- 列出需要 Executor Agent 执行的具体操作
- 按优先级排序

请确保你的分析全面、建议具体可行。
"""

    def process(self, messages: list[BaseMessage], task: str = "", **kwargs) -> dict:
        """
        分析问题并生成方案
        
        Args:
            messages: 对话历史
            task: 从路由提取的任务描述
            
        Returns:
            {
                "thinking": str,
                "analysis": str,
                "needs_execution": bool,
                "execution_tasks": list[str]
            }
        """
        # 如果有提取的任务，添加到消息中
        if task:
            from langchain_core.messages import HumanMessage
            task_message = HumanMessage(content=f"请分析以下任务并提出方案：\n\n{task}")
            messages = messages + [task_message]
        
        response = self.invoke(messages)
        
        # 提取 thinking 内容
        import re
        content = response.content
        thinking = ""
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # 从内容中移除 thinking 标签部分，保留正式回复
            analysis = re.sub(r'<thinking>.*?</thinking>\s*', '', content, flags=re.DOTALL).strip()
        else:
            analysis = content
        
        # 判断是否需要执行
        content_lower = content.lower()
        needs_execution = "执行" in content_lower or "操作" in content_lower
        
        return {
            "thinking": thinking,
            "analysis": analysis,
            "needs_execution": needs_execution,
            "execution_tasks": [],
            "raw_response": response
        }
