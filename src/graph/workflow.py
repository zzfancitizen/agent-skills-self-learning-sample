"""
Workflow - LangGraph 多 Agent 工作流
"""

from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from .state import AgentState
from ..agents import RouterAgent, ProposalAgent, ExecutorAgent
from ..skills import SkillRegistry


def create_workflow(skill_registry: SkillRegistry, **agent_kwargs):
    """
    创建多 Agent 工作流
    
    Args:
        skill_registry: Skill 注册中心
        **agent_kwargs: 传递给 agent 的额外参数（如 model, temperature）
        
    Returns:
        编译后的 LangGraph 工作流
    """
    # 初始化 Agents
    router = RouterAgent(skill_registry, **agent_kwargs)
    proposal = ProposalAgent(skill_registry, **agent_kwargs)
    executor = ExecutorAgent(skill_registry, **agent_kwargs)

    # 日志辅助函数
    def _log_agent(agent_name: str, input_data: dict, output_data: dict):
        """打印 agent 调用日志"""
        print("\n" + "=" * 60)
        print(f"🤖 AGENT: {agent_name}")
        print("=" * 60)
        
        print("\n📥 INPUT:")
        print("-" * 40)
        # 打印消息内容
        if "messages" in input_data:
            for i, msg in enumerate(input_data["messages"]):
                role = getattr(msg, "type", "unknown") if hasattr(msg, "type") else "unknown"
                content = getattr(msg, "content", str(msg))
                # 截断过长的内容
                if len(content) > 500:
                    content = content[:500] + "..."
                print(f"  [{i}] {role}: {content}")
        # 打印其他输入参数
        for key, value in input_data.items():
            if key != "messages" and value:
                val_str = str(value)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                print(f"  {key}: {val_str}")
        
        # 打印 THINKING（如果存在）
        if "thinking" in output_data and output_data["thinking"]:
            print("\n💭 THINKING:")
            print("-" * 40)
            thinking = output_data["thinking"]
            if len(thinking) > 800:
                thinking = thinking[:800] + "..."
            # 缩进每一行
            for line in thinking.split("\n"):
                print(f"  {line}")
        
        print("\n📤 OUTPUT:")
        print("-" * 40)
        for key, value in output_data.items():
            if key == "thinking":  # 已经单独打印
                continue
            if key == "raw_response":  # 跳过原始响应
                continue
            if value is not None:
                val_str = str(value)
                if len(val_str) > 500:
                    val_str = val_str[:500] + "..."
                print(f"  {key}: {val_str}")
        print("=" * 60 + "\n")

    # 定义节点函数
    def route_node(state: AgentState) -> dict:
        """路由节点"""
        input_data = {"messages": state["messages"]}
        
        result = router.process(state["messages"])
        
        output = {
            "current_agent": "router",
            "thinking": result.get("thinking", ""),
            "route": result.get("route"),
            "task": result.get("extracted_task"),
            "final_response": result.get("direct_response") if result.get("route") == "direct_response" else None,
        }
        
        _log_agent("RouterAgent", input_data, output)
        return output

    def proposal_node(state: AgentState) -> dict:
        """提案节点"""
        input_data = {
            "messages": state["messages"],
            "task": state.get("task", "")
        }
        
        result = proposal.process(
            state["messages"],
            task=state.get("task", "")
        )
        
        output = {
            "current_agent": "proposal",
            "thinking": result.get("thinking", ""),
            "proposal": result.get("analysis"),
            "messages": [AIMessage(content=result.get("analysis", ""))],
        }
        
        _log_agent("ProposalAgent", input_data, output)
        return output

    def executor_node(state: AgentState) -> dict:
        """执行节点"""
        input_data = {
            "messages": state["messages"],
            "proposal": state.get("proposal", "")
        }
        
        result = executor.process(
            state["messages"],
            proposal=state.get("proposal", ""),
            tasks=[]
        )
        
        output = {
            "current_agent": "executor",
            "thinking": result.get("thinking", ""),
            "execution_result": result.get("execution_log"),
            "final_response": result.get("execution_log"),
            "messages": [AIMessage(content=result.get("execution_log", ""))],
        }
        
        _log_agent("ExecutorAgent", input_data, output)
        return output

    def finalize_node(state: AgentState) -> dict:
        """最终输出节点"""
        # 如果有 final_response 直接使用，否则使用最后的 proposal 或 execution_result
        final = (
            state.get("final_response") or
            state.get("execution_result") or
            state.get("proposal") or
            "无法处理该请求"
        )
        return {
            "final_response": final,
        }

    # 路由条件函数
    def route_decision(state: AgentState) -> Literal["proposal", "executor", "finalize"]:
        """根据路由决策选择下一个节点"""
        route = state.get("route", "proposal")
        if route == "direct_response":
            return "finalize"
        elif route == "executor":
            return "executor"
        else:
            return "proposal"

    def proposal_decision(state: AgentState) -> Literal["executor", "finalize"]:
        """决定是否需要执行"""
        # 简化逻辑：总是进入 finalize
        # 可以根据 proposal 内容判断是否需要 executor
        proposal = state.get("proposal", "")
        if "执行" in proposal.lower() or "操作" in proposal.lower():
            return "executor"
        return "finalize"

    # 构建 Graph
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("router", route_node)
    workflow.add_node("proposal", proposal_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("finalize", finalize_node)

    # 设置入口
    workflow.set_entry_point("router")

    # 添加条件边
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "proposal": "proposal",
            "executor": "executor",
            "finalize": "finalize",
        }
    )

    workflow.add_conditional_edges(
        "proposal",
        proposal_decision,
        {
            "executor": "executor",
            "finalize": "finalize",
        }
    )

    # 普通边
    workflow.add_edge("executor", "finalize")
    workflow.add_edge("finalize", END)

    # 编译
    return workflow.compile()


def run_workflow(
    user_input: str,
    skills_dir: str = "./skills",
    **agent_kwargs
) -> str:
    """
    便捷函数：运行工作流
    
    Args:
        user_input: 用户输入
        skills_dir: skills 目录路径
        **agent_kwargs: agent 参数
        
    Returns:
        最终响应字符串
    """
    from .state import create_initial_state
    
    # 加载 skills
    registry = SkillRegistry(skills_dir)
    
    # 创建并运行工作流
    workflow = create_workflow(registry, **agent_kwargs)
    initial_state = create_initial_state(user_input)
    
    final_state = workflow.invoke(initial_state)
    
    return final_state.get("final_response", "")
