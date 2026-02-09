# Skill-enabled Multi-Agent System

A multi-agent system based on LangGraph, integrated with a Claude-style Skill mechanism featuring lazy loading.

## Features

- **Skill System**: Claude Code-style skill mechanism, defining agent capabilities through SKILL.md files
- **Multi-Skill per Agent**: Each agent can have multiple skills organised in per-skill subdirectories
- **Lazy Loading**: Only skill headers (name, description, tags) are loaded at init; full body content is loaded on demand via the `load_skill` tool when the LLM determines a skill is needed
- **Multi-Agent Collaboration**: Router -> Proposal -> Executor three-layer architecture
- **LangGraph Integration**: Uses LangGraph for state management and workflow orchestration
- **Tool Co-location**: Tools live alongside the skill that uses them

## Project Structure

```
.
├── pyproject.toml              # Dependency configuration
├── src/
│   ├── main.py                 # Entry point
│   ├── skills/
│   │   ├── loader.py           # Skill loader & load_skill tool factory
│   │   └── registry.py         # Skill registry
│   ├── agents/
│   │   ├── base.py             # Base Agent (auto-registers load_skill tool)
│   │   ├── router/             # Router Agent
│   │   │   ├── agent.py
│   │   │   └── skills/
│   │   │       └── routing/
│   │   │           └── SKILL.md
│   │   ├── proposal/           # Proposal Agent
│   │   │   ├── agent.py
│   │   │   └── skills/
│   │   │       └── analysis/
│   │   │           ├── SKILL.md
│   │   │           └── tools/
│   │   │               └── search_system.py
│   │   └── executor/           # Executor Agent
│   │       ├── agent.py
│   │       └── skills/
│   │           └── execution/
│   │               └── SKILL.md
│   └── graph/
│       ├── state.py            # State definition
│       └── workflow.py         # Workflow
├── visualize_graph.py          # Graph visualization
└── workflow_graph.png          # Workflow graph image
```

## How Lazy Loading Works

```
Agent init
  └─> scan skills/ directory
  └─> read ONLY YAML frontmatter (name, description, tags)
  └─> body content: NOT loaded

User query arrives
  └─> system prompt includes skill SUMMARIES only (name + description)
  └─> LLM sees available skills and the user query
  └─> LLM calls load_skill("analysis") tool to get full instructions
  └─> tool reads SKILL.md body from disk (first access, then cached)
  └─> content returned as ToolMessage
  └─> LLM uses full skill instructions to produce response
```

Key points:
- The system prompt never contains full skill content -- only lightweight summaries
- The `load_skill` tool is auto-registered on every agent via `BaseAgent`
- Skill body content is read from disk on first access and cached for subsequent calls
- If the LLM does not need a skill, its content is never loaded

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
# See full system prompts, tool calls, and lazy loading in action
uv run src/main.py --log-level INFO "What is machine learning?"
```

## Creating Custom Skills

Each agent can have multiple skills. To add a new skill to an agent:

1. Create a directory under the agent's `skills/` folder:

```
src/agents/proposal/skills/my_new_skill/
├── SKILL.md
└── tools/              # optional: co-located tools
    ├── __init__.py
    └── my_tool.py
```

2. Write the `SKILL.md` with YAML frontmatter:

```markdown
---
name: my_new_skill
description: Brief description of what this skill does
tags: [tag1, tag2]
---

# Skill Content

Detailed instructions the LLM will follow when this skill is loaded...
```

3. Add the skill name to the agent's `default_skills` property so it appears in the summary.

4. If the skill has tools, import and register them in the agent's `__init__`:

```python
from .skills.my_new_skill.tools.my_tool import my_tool
self.register_tools([my_tool])
```

## Architecture

```
User Request
    |
+-------------------+
|   Router Agent    | <- routing skill (loaded on demand)
+--------+----------+
         |
    /    |    \
+------+ +------+ +--------+
|Propo-| |Execu-| |Direct  |
|sal   | |tor   | |Response|
|Agent | |Agent | |        |
+------+ +------+ +--------+
  |        |           |
  +---->---+           |
       |               |
+-------------------+  |
|  Final Response   |<-+
+-------------------+
```

## Extending

### Adding a New Agent

1. Inherit from `BaseAgent`
2. Implement `agent_name`, `default_skills`, `base_system_prompt`, `process` methods
3. Create a `skills/` directory with one or more skill subdirectories, each containing a `SKILL.md`
4. Use `SkillLoader.load_agent_skills(agent_dir)` in `__init__` to discover and register all skills
5. Add nodes and edges in `workflow.py`

### Adding Tools to a Skill

Place tools inside the skill directory for co-location:

```python
# src/agents/my_agent/skills/my_skill/tools/my_tool.py
from langchain_core.tools import tool

@tool
def query_database(query: str) -> str:
    """Query the database"""
    # Implementation...
```

Then register in the agent:

```python
class MyAgent(BaseAgent):
    def __init__(self, skill_registry, **kwargs):
        agent_dir = Path(__file__).parent
        skills = SkillLoader.load_agent_skills(agent_dir)
        for skill in skills:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

        # Pre-register tools so they are available when the LLM loads the skill
        from .skills.my_skill.tools.my_tool import query_database
        self.register_tools([query_database])
```

## License

MIT
