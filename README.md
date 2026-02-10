# Skill-enabled Multi-Agent System

A multi-agent system based on LangGraph, integrated with a Claude-style Skill mechanism featuring lazy loading. Exposed as an **A2A (Agent-to-Agent) protocol** service built on **SAP Application Foundation** for deployment on SAP App Foundation runtime.

## Features

- **A2A Protocol**: Agent-to-Agent communication via the A2A SDK, exposable as a standard A2A service
- **Application Foundation**: SAP AI Core integration for LLM access and managed runtime deployment
- **Skill System**: Claude Code-style skill mechanism, defining agent capabilities through SKILL.md files
- **Multi-Skill per Agent**: Each agent can have multiple skills organised in per-skill subdirectories
- **Lazy Loading**: Only skill headers (name, description, tags) are loaded at init; full body content is loaded on demand via the `load_skill` tool when the LLM determines a skill is needed
- **Multi-Agent Collaboration**: Router -> Proposal -> Executor three-layer architecture
- **LangGraph Integration**: Uses LangGraph for state management and workflow orchestration
- **Tool Co-location**: Tools live alongside the skill that uses them

## Project Structure

```bash
.
├── app.yaml                    # App Foundation workload configuration
├── Dockerfile                  # Container build configuration
├── requirements.txt            # Python dependencies (exported from pyproject.toml)
├── pyproject.toml              # Dependency & project configuration
├── src/
│   ├── main.py                 # Legacy CLI entry point
│   ├── app/                    # A2A service entry point (latest)
│   │   ├── __init__.py
│   │   ├── main.py             # A2A server + integrated CLI modes
│   │   ├── agent_executor.py   # A2A request handler
│   │   ├── agent.py            # Core agent wrapping multi-agent workflow
│   │   └── .env.example        # Environment variable template
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

```bash
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
# Install dependencies with uv (requires SAP Artifactory credentials for application-foundation-sdk)
UV_INDEX_SAP_ARTIFACTORY_USERNAME=<your-i-number> \
UV_INDEX_SAP_ARTIFACTORY_PASSWORD=<your-artifactory-token> \
uv sync
```

## Configuration

Create a `.env` file with SAP AI Core credentials:

```bash
ARTIFACTORY_USER=<your-i-number>
ARTIFACTORY_TOKEN=<your-artifactory-token>

AICORE_CLIENT_ID=<your-client-id>
AICORE_CLIENT_SECRET=<your-client-secret>
AICORE_AUTH_URL=<your-auth-url>
AICORE_BASE_URL=<your-base-url>
AICORE_RESOURCE_GROUP=<your-resource-group>
```

## Usage

### A2A Server (Default — Latest Entry Point)

Start the A2A protocol server:

```bash
uv run python src/app/main.py --host 0.0.0.0 --port 5000
```

Verify the agent is running:

```bash
curl http://localhost:5000/.well-known/agent.json
```

Send a message via A2A protocol:

```bash
curl --request POST \
  --url http://localhost:5000/ \
  --header 'content-type: application/json' \
  --data '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "test-1",
  "params": {
    "message": {
      "messageId": "msg-001",
      "role": "user",
      "parts": [{"kind": "text", "text": "Hello, what can you help me with?"}]
    }
  }
}'
```

### CLI Modes (via A2A entry point)

The A2A entry point also supports the legacy CLI modes:

```bash
# List available skills
uv run python src/app/main.py --list-skills

# Run tests
uv run python src/app/main.py --test

# Single query
uv run python src/app/main.py "How to optimize database performance?"
```

### Legacy CLI Entry Point

The original CLI-only entry point is still available:

```bash
# Interactive mode
uv run python src/main.py

# Single query
uv run python src/main.py "What is machine learning?"

# Log level control
uv run python src/main.py --log-level DEBUG "What is machine learning?"
```

## Deployment

### App Foundation Runtime

Deploy to SAP App Foundation runtime:

```bash
appfnd deploy
```

Configuration is defined in `app.yaml`:

- **`metadata.name`** — Agent identifier (`skill-agents`)
- **`spec.container.port`** — Server port (`5000`)
- **`spec.resources`** — CPU and memory limits
- **`spec.models`** — SAP AI Core LLM models the agent can access

### Docker (Local)

Build and run the container locally:

```bash
docker build \
  --build-arg ARTIFACTORY_USER=<your-i-number> \
  --build-arg ARTIFACTORY_TOKEN=<your-token> \
  -t skill-agents .

docker run -p 5000:5000 \
  -e AICORE_CLIENT_ID=<id> \
  -e AICORE_CLIENT_SECRET=<secret> \
  -e AICORE_AUTH_URL=<url> \
  -e AICORE_BASE_URL=<url> \
  -e AICORE_RESOURCE_GROUP=<group> \
  skill-agents
```

### Model Selection

The default model is `anthropic--claude-4.5-sonnet`. To change it, update:

1. `app.yaml` — Add the model to the `models` list
2. `src/app/main.py` — Update the `--model` default
3. Agent code in `src/agents/` — Update the model parameter

## Creating Custom Skills

Each agent can have multiple skills. To add a new skill to an agent:

1. Create a directory under the agent's `skills/` folder:

```bash
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

```bash
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
