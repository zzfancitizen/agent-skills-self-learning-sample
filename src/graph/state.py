"""
Agent State - LangGraph 状态定义
"""

from typing import Annotated, TypedDict, Optional, Literal
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Multi-Agent 工作流状态
    
    Attributes:
        messages: 对话消息历史（使用 add_messages reducer 自动累积）
        current_agent: 当前处理的 agent 名称
        route: 路由决策
        task: 提取的任务描述
        proposal: 来自 ProposalAgent 的方案
        execution_result: 执行结果
        final_response: 最终响应
        error: 错误信息
    """
    # 消息历史 - 使用 Annotated 以支持消息累积
    messages: Annotated[list[BaseMessage], add_messages]
    
    # 流程控制
    current_agent: str
    route: Optional[str]
    
    # Agent 输出
    task: Optional[str]
    proposal: Optional[str]
    execution_result: Optional[str]
    final_response: Optional[str]
    
    # 错误处理
    error: Optional[str]


def create_initial_state(user_message: str) -> AgentState:
    """
    创建初始状态
    
    Args:
        user_message: 用户输入
        
    Returns:
        初始化的 AgentState
    """
    from langchain_core.messages import HumanMessage
    
    return {
        "messages": [HumanMessage(content=user_message)],
        "current_agent": "",
        "route": None,
        "task": None,
        "proposal": None,
        "execution_result": None,
        "final_response": None,
        "error": None,
    }
