"""
Executor Agent - 执行具体操作
"""

from langchain_core.messages import BaseMessage, AIMessage

from .base import BaseAgent
from ..skills.registry import SkillRegistry


class ExecutorAgent(BaseAgent):
    """
    执行 Agent
    
    根据方案执行具体操作
    """

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        super().__init__(skill_registry, **kwargs)

    @property
    def agent_name(self) -> str:
        return "ExecutorAgent"

    @property
    def default_skills(self) -> list[str]:
        return ["execution"]

    @property
    def base_system_prompt(self) -> str:
        return """你是一个执行 Agent。你的任务是根据给定的方案执行具体操作。

在开始你的回复前，请先用 <thinking> 标签输出你的思考过程：

<thinking>
在这里写下你的执行思路：
- 你理解的任务目标
- 你计划如何执行
- 可能遇到的问题和应对方案
</thinking>

执行原则：
1. 严格按照方案步骤执行
2. 每一步操作都要确认结果
3. 遇到错误时及时报告
4. 记录所有执行的操作和结果

你的回复格式：

## 执行计划
- 列出将要执行的操作

## 执行过程
- 记录每一步的执行情况

## 执行结果
- 总结执行结果
- 列出成功和失败的操作
- 如有错误，说明原因和建议

请确保执行过程透明、结果清晰。
"""

    def process(
        self,
        messages: list[BaseMessage],
        proposal: str = "",
        tasks: list[str] = None,
        **kwargs
    ) -> dict:
        """
        执行操作
        
        Args:
            messages: 对话历史
            proposal: 来自 ProposalAgent 的方案
            tasks: 具体的执行任务列表
            
        Returns:
            {
                "thinking": str,
                "execution_log": str,
                "success": bool,
                "results": list[dict]
            }
        """
        from langchain_core.messages import HumanMessage
        
        # 构建执行上下文
        context_parts = []
        if proposal:
            context_parts.append(f"## 方案\n{proposal}")
        if tasks:
            context_parts.append(f"## 待执行任务\n" + "\n".join(f"- {t}" for t in tasks))
        
        if context_parts:
            context_message = HumanMessage(
                content="请根据以下信息执行操作：\n\n" + "\n\n".join(context_parts)
            )
            messages = messages + [context_message]
        
        response = self.invoke(messages)
        
        # 提取 thinking 内容
        import re
        content = response.content
        thinking = ""
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', content, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # 从内容中移除 thinking 标签部分
            execution_log = re.sub(r'<thinking>.*?</thinking>\s*', '', content, flags=re.DOTALL).strip()
        else:
            execution_log = content
        
        # 简单判断执行是否成功
        content_lower = content.lower()
        success = "失败" not in content_lower and "错误" not in content_lower
        
        return {
            "thinking": thinking,
            "execution_log": execution_log,
            "success": success,
            "results": [],
            "raw_response": response
        }
