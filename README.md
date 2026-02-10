# Skill-enabled Multi-Agent System

A multi-agent system based on LangGraph, integrated with a Claude-style Skill mechanism featuring lazy loading. Exposed as an **A2A (Agent-to-Agent) protocol** service built on **SAP Application Foundation** for deployment on SAP App Foundation runtime.

## Features

- **A2A Protocol**: Agent-to-Agent communication via the A2A SDK, exposable as a standard A2A service
- **Application Foundation**: SAP AI Core integration for LLM access and managed runtime deployment
- **Skill System**: Claude Code-style skill mechanism, defining agent capabilities through SKILL.md files
- **Multi-Skill per Agent**: Each agent can have multiple skills organised in per-skill subdirectories
- **Lazy Loading**: Only skill headers (name, description, tags) are loaded at init; full body content is loaded on demand via the `load_skill` tool when the LLM determines a skill is needed
- **Multi-Agent Collaboration**: Router → Proposal → Executor three-layer architecture
- **LangGraph Integration**: Uses LangGraph for state management and workflow orchestration with `StateGraph`
- **Conversation Memory**: Multi-turn conversation support via `MemorySaver` checkpointer, keyed by `context_id`
- **State Management**: `AgentState` with `add_messages` reducer for automatic message accumulation
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

## Multi-Turn Conversation Memory

The system uses LangGraph's `MemorySaver` checkpointer to maintain conversation history across requests:

```bash
Request 1 (context_id="user-123")
  └─> Creates new conversation thread
  └─> User: "What is machine learning?"
  └─> Agent response saved to thread

Request 2 (same context_id="user-123")
  └─> Retrieves conversation history from thread
  └─> User: "Can you give me an example?"
  └─> Agent knows context from previous message
  └─> Updated history saved back to thread
```

Key implementation details:

- **Context ID**: Each unique `context_id` maintains a separate conversation thread
- **State Reducer**: `AgentState.messages` uses `add_messages` reducer to append new messages to history
- **Reset per Run**: Routing decisions (`route`), proposals, and execution results are reset for each workflow invocation, while message history persists
- **Thread Isolation**: Different `context_id` values create completely independent conversation histories

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

# Run tests (workflow creation, skill loading, prompt generation)
uv run python src/app/main.py --test

# Single query
uv run python src/app/main.py "How to optimize database performance?"

# Quick import validation (verify project structure after changes)
uv run python -c "import src.main; import src.graph; import src.agents; import src.skills"
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

### Three-Layer Agent Pipeline

Requests flow through a LangGraph `StateGraph` defined in `src/graph/workflow.py`:

```bash
User Request
    |
    v
+-------------------+
|   Router Agent    | <- Analyzes intent, returns routing decision
+--------+----------+   (proposal / executor / direct_response)
         |
    /    |    \
   /     |     \
  v      v      v
+------+ +------+ +--------+
|Propo-| |Execu-| |Direct  |
|sal   | |tor   | |Response|
|Agent | |Agent | |        |
+------+ +------+ +--------+
| Deep | |Execu-| |Quick   |
|analy-| |tes   | |answer  |
|sis   | |tasks | |        |
+------+ +------+ +--------+
  |        |           |
  +--------+-----------+
           |
           v
    +------------+
    |  Finalize  | <- Selects final response
    +------------+
           |
           v
    Final Response
```

**Agent Responsibilities**:

1. **RouterAgent** (`src/agents/router/`) — Analyzes user intent and returns a JSON routing decision
2. **ProposalAgent** (`src/agents/proposal/`) — Deep analysis with `<thinking>` tags, generates solution proposals. Has a `search_system_tool` (currently a stub)
3. **ExecutorAgent** (`src/agents/executor/`) — Executes operations based on proposals, reports step-by-step results

**State Management**:

- `AgentState` (`src/graph/state.py`) uses LangGraph's `add_messages` reducer for message accumulation
- Fields: `messages`, `current_agent`, `route`, `task`, `proposal`, `execution_result`, `final_response`, `error`
- Workflow state persists across nodes via conditional edges
- All paths converge at the `finalize` node which selects the final response

### Key Components

**Skill System**:
- `SkillLoader` (`src/skills/loader.py`) — Parses SKILL.md frontmatter, creates `Skill` objects, provides `create_load_skill_tool` factory
- `SkillRegistry` (`src/skills/registry.py`) — Central registry for skill lookup, tag indexing, and prompt generation
- `BaseAgent` (`src/agents/base.py`) — Abstract base with tool-call loop, auto-registers `load_skill` tool, max 10 tool iterations

**A2A Service Layer** (`src/app/`):
- `main.py` — Click CLI, builds `AgentCard` with skills, starts uvicorn server
- `agent.py` — `SampleAgent` wraps multi-agent workflow with `MemorySaver` checkpointer for multi-turn conversations
- `agent_executor.py` — A2A `AgentExecutor` adapter that streams workflow results as A2A task events

**LLM Integration**:
- Uses `ChatLiteLLM` with model prefix `sap/` (e.g., `sap/anthropic--claude-4.5-sonnet`)
- LLM calls go through SAP AI Core via LiteLLM proxy
- Tools use LangChain's `@tool` decorator and are registered via `BaseAgent.register_tools()`

## Extending

### Adding a New Agent

1. Create `src/agents/<name>/` with `__init__.py`, `agent.py`, and `skills/<skill_name>/SKILL.md`
2. Subclass `BaseAgent` — implement `agent_name`, `default_skills`, `base_system_prompt`, `process`
3. In `__init__`, call `SkillLoader.load_agent_skills()` and register skills with the registry:

```python
from pathlib import Path
from src.agents.base import BaseAgent
from src.skills.loader import SkillLoader

class MyAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "my_agent"

    @property
    def default_skills(self) -> list[str]:
        return ["my_skill"]

    def __init__(self, skill_registry, **kwargs):
        agent_dir = Path(__file__).parent
        skills = SkillLoader.load_agent_skills(agent_dir)
        for skill in skills:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

        # Register tools if needed
        # from .skills.my_skill.tools.my_tool import my_tool
        # self.register_tools([my_tool])

    def process(self, state) -> dict:
        # Agent logic here
        return {"my_result": "..."}
```

4. Export from `src/agents/__init__.py`
5. Add node + edges in `src/graph/workflow.py`
6. Update `RouterAgent.VALID_ROUTES`, its system prompt, and `route_decision()` if the router should route to it

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

## Development

### Quick Validation After Changes

```bash
# Import check - verify all modules load correctly
uv run python -c "import src.main; import src.graph; import src.agents; import src.skills"

# Run tests - workflow creation, skill loading, prompt generation
uv run python src/app/main.py --test

# List skills - verify new skills are registered
uv run python src/app/main.py --list-skills
```

### Common Development Tasks

```bash
# Update dependencies
uv sync

# Export requirements.txt (needed for Docker builds)
uv export --format requirements-txt > requirements.txt

# Visualize workflow graph
uv run python visualize_graph.py

# Run with debug logging
uv run python src/main.py --log-level DEBUG "test query"
```

### Key Conventions

- Python 3.13, managed with `uv`
- LLM calls use `ChatLiteLLM` with model prefix `sap/` (e.g., `sap/anthropic--claude-4.5-sonnet`)
- Tools use LangChain's `@tool` decorator
- The `process()` method on each agent returns a dict with agent-specific keys
- Each agent's `default_skills` property lists skills to include in the system prompt summary

## License

MIT
