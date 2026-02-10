# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A skill-enabled multi-agent system built on LangGraph, exposed as an A2A (Agent-to-Agent) protocol service for SAP App Foundation runtime. Uses lazy-loading SKILL.md files to define agent capabilities, with LLM access via SAP AI Core through LiteLLM.

## Commands

```bash
# Install dependencies (requires SAP Artifactory credentials)
UV_INDEX_SAP_ARTIFACTORY_USERNAME=<i-number> \
UV_INDEX_SAP_ARTIFACTORY_PASSWORD=<token> \
uv sync

# Start A2A server (default mode)
uv run python src/app/main.py --host 0.0.0.0 --port 5000

# Verify agent is running
curl http://localhost:5000/.well-known/agent.json

# Run tests (workflow creation, skill loading, prompt generation)
uv run python src/app/main.py --test

# List all registered skills
uv run python src/app/main.py --list-skills

# Single query via CLI
uv run python src/app/main.py "Your question here"

# Legacy CLI with interactive mode
uv run python src/main.py

# Import check (quick validation after changes)
uv run python -c "import src.main; import src.graph; import src.agents; import src.skills"

# Deploy to App Foundation runtime
appfnd deploy
```

## Architecture

### Three-Layer Agent Pipeline

Requests flow through a LangGraph `StateGraph` defined in `src/graph/workflow.py`:

1. **RouterAgent** (`src/agents/router/`) — Analyzes user intent and returns a JSON routing decision: `proposal`, `executor`, or `direct_response`
2. **ProposalAgent** (`src/agents/proposal/`) — Deep analysis with `<thinking>` tags, generates solution proposals. Has a `search_system_tool` (currently a stub)
3. **ExecutorAgent** (`src/agents/executor/`) — Executes operations based on proposals, reports step-by-step results

The router's conditional edges determine the path. Proposals may skip execution and go directly to the `finalize` node. All paths end at `finalize` which selects the final response.

### Skill System (Lazy Loading)

Skills are defined as `SKILL.md` files with YAML frontmatter under each agent's `skills/` directory. The system only loads frontmatter (name, description, tags) at init. The LLM calls a `load_skill` tool at runtime to get full instructions on demand.

Key classes:
- `SkillLoader` (`src/skills/loader.py`) — Parses SKILL.md frontmatter, creates `Skill` objects, and provides the `create_load_skill_tool` factory
- `SkillRegistry` (`src/skills/registry.py`) — Central registry for skill lookup, tag indexing, and prompt generation
- `BaseAgent` (`src/agents/base.py`) — Abstract base with tool-call loop, auto-registers `load_skill` tool, max 10 tool iterations

### A2A Service Layer

`src/app/` contains the A2A protocol integration:
- `main.py` — Click CLI, builds `AgentCard` with skills, starts uvicorn server. Also supports legacy CLI modes (`--test`, `--list-skills`, positional query)
- `agent.py` — `SampleAgent` wraps the multi-agent workflow with `MemorySaver` checkpointer for multi-turn conversations keyed by `context_id`
- `agent_executor.py` — A2A `AgentExecutor` adapter that streams workflow results as A2A task events

### State Management

`AgentState` (`src/graph/state.py`) uses LangGraph's `add_messages` reducer for message accumulation. Fields: `messages`, `current_agent`, `route`, `task`, `proposal`, `execution_result`, `final_response`, `error`.

## Adding a New Agent

1. Create `src/agents/<name>/` with `__init__.py`, `agent.py`, and `skills/<skill_name>/SKILL.md`
2. Subclass `BaseAgent` — implement `agent_name`, `default_skills`, `base_system_prompt`, `process`
3. In `__init__`, call `SkillLoader.load_agent_skills()` and register skills with the registry
4. Export from `src/agents/__init__.py`
5. Add node + edges in `src/graph/workflow.py`
6. Update `RouterAgent.VALID_ROUTES`, its system prompt, and `route_decision()` if the router should route to it

## Adding a New Skill to an Existing Agent

1. Create `src/agents/<agent>/skills/<skill_name>/SKILL.md` with YAML frontmatter (`name`, `description`, `tags`) and body content
2. Add the skill name to the agent's `default_skills` property
3. If the skill has tools, place them in `skills/<skill_name>/tools/` and register via `self.register_tools()` in the agent's `__init__`

## Key Conventions

- Python 3.13, managed with `uv`
- LLM calls go through `ChatLiteLLM` with model prefix `sap/` (e.g., `sap/anthropic--claude-4.5-sonnet`)
- Tools use LangChain's `@tool` decorator and are registered via `BaseAgent.register_tools()`
- The `process()` method on each agent returns a dict with agent-specific keys (e.g., `route`, `analysis`, `execution_log`)
- Environment variables for AI Core: `AICORE_CLIENT_ID`, `AICORE_CLIENT_SECRET`, `AICORE_AUTH_URL`, `AICORE_BASE_URL`, `AICORE_RESOURCE_GROUP`
- Model selection must be updated in three places: `app.yaml` (models list), `src/app/main.py` (--model default), and agent code
