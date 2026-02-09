# Skill-enabled Multi-Agent System

A multi-agent system based on LangGraph, integrated with a Claude-style Skill mechanism.

## Features

- **Skill System**: Claude Code-style skill mechanism, defining agent capabilities through SKILL.md files
- **Multi-Agent Collaboration**: Router -> Proposal -> Executor three-layer architecture
- **LangGraph Integration**: Uses LangGraph for state management and workflow orchestration
- **Dynamic Skill Loading**: Load and switch skills at runtime

## Project Structure

```
.
├── pyproject.toml              # Dependency configuration
├── src/
│   ├── main.py                 # Entry point
│   ├── skills/
│   │   ├── loader.py           # Skill loader
│   │   └── registry.py         # Skill registry
│   ├── agents/
│   │   ├── base.py             # Base Agent
│   │   ├── router/             # Router Agent
│   │   │   ├── agent.py
│   │   │   └── SKILL.md
│   │   ├── proposal/           # Proposal Agent
│   │   │   ├── agent.py
│   │   │   ├── SKILL.md
│   │   │   └── tools/
│   │   │       └── search_system.py
│   │   └── executor/           # Executor Agent
│   │       ├── agent.py
│   │       └── SKILL.md
│   └── graph/
│       ├── state.py            # State definition
│       └── workflow.py         # Workflow
├── visualize_graph.py          # Graph visualization
└── workflow_graph.png          # Workflow graph image
```

## Installation

```bash
# Install dependencies with uv
uv sync
```

## Configuration

Create a `.env` file:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### List Available Skills

```bash
uv run src/main.py --list-skills
```

### Run Tests

```bash
uv run src/main.py --test
```

### Interactive Mode

```bash
uv run src/main.py
```

### Single Query

```bash
uv run src/main.py "How to optimize database performance?"
```

### Log Level Control

```bash
uv run src/main.py --log-level DEBUG --test
```

## Creating Custom Skills

Each agent has its own SKILL.md in its directory. To create a new agent with a skill, add a `SKILL.md` file:

```markdown
---
name: my_skill
description: My custom skill
tags: [custom, example]
---

# Skill Content

Detailed instructions...
```

## Architecture

```
User Request
    |
+-------------------+
|   Router Agent    | <- routing skill
+--------+----------+
         |
    /    |    \
+----+ +----+ +------+
| P  | | E  | | D    |
| r  | | x  | | i    |
| o  | | e  | | r    |
| p  | | c  | | e    |
| o  | | u  | | c    |
| s  | | t  | | t    |
| a  | | o  | |      |
| l  | | r  | | R    |
+----+ +----+ | e    |
  |      |    | s    |
  +-->---+    | p    |
      |       +------+
+-------------------+
|  Final Response   |
+-------------------+
```

## Extending

### Adding a New Agent

1. Inherit from `BaseAgent`
2. Implement `agent_name`, `default_skills`, `base_system_prompt`, `process` methods
3. Add a `SKILL.md` file in the agent directory
4. Add nodes and edges in `workflow.py`

### Adding Tools

Extend agents with tool calling using `register_tools`:

```python
from langchain_core.tools import tool

@tool
def query_database(query: str) -> str:
    """Query the database"""
    # Implementation...

class MyAgent(BaseAgent):
    def __init__(self, ...):
        super().__init__(...)
        self.register_tools([query_database])
```

## License

MIT
