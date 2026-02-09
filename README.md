# Skill-enabled Multi-Agent System

基于 LangGraph 的多 Agent 系统，集成 Claude-style Skill 机制。

## 特性

- **Skill 系统**：类似 Claude Code 的 skill 机制，通过 SKILL.md 文件定义 Agent 能力
- **多 Agent 协作**：Router → Proposal → Executor 三层架构
- **LangGraph 集成**：使用 LangGraph 进行状态管理和流程编排
- **动态 Skill 加载**：运行时加载和切换 skills

## 项目结构

```
.
├── pyproject.toml          # 依赖配置
├── src/
│   ├── main.py             # 入口
│   ├── skills/
│   │   ├── loader.py       # Skill 加载器
│   │   └── registry.py     # Skill 注册中心
│   ├── agents/
│   │   ├── base.py         # 基础 Agent
│   │   ├── router.py       # 路由 Agent
│   │   ├── proposal.py     # 提案 Agent
│   │   └── executor.py     # 执行 Agent
│   └── graph/
│       ├── state.py        # 状态定义
│       └── workflow.py     # 工作流
└── skills/                  # Skill 定义
    ├── routing/
    │   └── SKILL.md
    ├── analysis/
    │   └── SKILL.md
    └── execution/
        └── SKILL.md
```

## 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -e .
```

## 配置

创建 `.env` 文件：

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## 使用

### 列出可用 Skills

```bash
python -m src.main --list-skills
```

### 运行测试

```bash
python -m src.main --test
```

### 交互模式

```bash
python -m src.main
```

### 单次查询

```bash
python -m src.main "如何优化数据库性能？"
```

## 创建自定义 Skill

在 `skills/` 目录下创建新文件夹，添加 `SKILL.md`：

```markdown
---
name: my_skill
description: 我的自定义 skill
tags: [custom, example]
---

# Skill 内容

详细的指令说明...
```

## 架构说明

```
用户请求
    ↓
┌─────────────────┐
│  Router Agent   │ ← routing skill
└────────┬────────┘
         │
    ↙    ↓    ↘
┌────┐ ┌────┐ ┌────┐
│ P  │ │ E  │ │ D  │
│ r  │ │ x  │ │ i  │
│ o  │ │ e  │ │ r  │
│ p  │ │ c  │ │ e  │
│ o  │ │ u  │ │ c  │
│ s  │ │ t  │ │ t  │
│ a  │ │ o  │ │    │
│ l  │ │ r  │ │ R  │
└────┘ └────┘ │ e  │
   ↓     ↓    │ s  │
   └──→──┘    │ p  │
       ↓      └────┘
┌─────────────────┐
│    最终响应      │
└─────────────────┘
```

## 扩展

### 添加新 Agent

1. 继承 `BaseAgent` 类
2. 实现 `agent_name`, `default_skills`, `base_system_prompt`, `process` 方法
3. 在 `workflow.py` 中添加节点和边

### 添加 Tools（工具调用）

可以扩展 `BaseAgent` 以支持 tool calling：

```python
from langchain_core.tools import tool

@tool
def query_database(query: str) -> str:
    """查询数据库"""
    # 实现...

class MyAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(...)
        self._llm = self._llm.bind_tools([query_database])
```

## License

MIT
