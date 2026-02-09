---
name: create-agent
description: Scaffold a new agent in this multi-agent system following the project skeleton. Use when the user wants to create, add, or scaffold a new agent, or asks about adding agents to the workflow.
---

# Create Agent

Follow this checklist when creating a new agent. Replace `<name>` with the
agent name (lowercase, e.g. `reviewer`) and `<Name>` with the PascalCase class
name (e.g. `ReviewerAgent`).

```
Progress:
- [ ] Step 1: Create directory structure
- [ ] Step 2: Write SKILL.md
- [ ] Step 3: Write agent.py
- [ ] Step 4: Write package __init__.py
- [ ] Step 5: Register in src/agents/__init__.py
- [ ] Step 6: Add to workflow graph
- [ ] Step 7: Update router
- [ ] Step 8: Run verification
```

## Step 1: Create directory structure

```
src/agents/<name>/
├── __init__.py
├── agent.py
└── skills/
    └── <skill_name>/
        ├── SKILL.md
        └── tools/          # optional, only if agent needs tools
            ├── __init__.py
            └── <tool>.py
```

## Step 2: Write SKILL.md

Create `src/agents/<name>/skills/<skill_name>/SKILL.md`:

```markdown
---
name: <skill_name>
description: Brief description of what this skill does
tags: [<tag1>, <tag2>]
---

# <Skill Title>

Detailed instructions the LLM follows when this skill is loaded...
```

## Step 3: Write agent.py

Create `src/agents/<name>/agent.py` following this skeleton:

```python
"""
<Name> Agent - <one-line purpose>
"""

from pathlib import Path

from langchain_core.messages import BaseMessage, AIMessage

from ..base import BaseAgent
from ...skills.registry import SkillRegistry
from ...skills.loader import SkillLoader


class <Name>Agent(BaseAgent):
    """<Name> Agent — <brief description>"""

    def __init__(self, skill_registry: SkillRegistry, **kwargs):
        # Discover and register all skills from skills/ subdirectory
        agent_dir = Path(__file__).parent
        skills = SkillLoader.load_agent_skills(agent_dir, lazy=skill_registry._lazy)
        for skill in skills:
            skill_registry.register(skill)

        super().__init__(skill_registry, **kwargs)

        # If agent has tools, register them here:
        # from .skills.<skill_name>.tools.<tool_module> import <tool>
        # self.register_tools([<tool>])

    @property
    def agent_name(self) -> str:
        return "<Name>Agent"

    @property
    def default_skills(self) -> list[str]:
        return ["<skill_name>"]

    @property
    def base_system_prompt(self) -> str:
        return """<system prompt for this agent>"""

    def process(self, messages: list[BaseMessage], **kwargs) -> dict:
        response = self.invoke(messages)
        content = response.content
        return {
            "result": content,
            "raw_response": response,
        }
```

## Step 4: Write package `__init__.py`

Create `src/agents/<name>/__init__.py`:

```python
"""
<Name> Agent Package
"""

from .agent import <Name>Agent

__all__ = ["<Name>Agent"]
```

## Step 5: Register in `src/agents/__init__.py`

Add the import and export:

```python
from .<name> import <Name>Agent
```

And add `"<Name>Agent"` to the `__all__` list.

## Step 6: Add to workflow graph

Edit `src/graph/workflow.py`:

1. **Import** the new agent class in the imports section.

2. **Instantiate** it in `create_workflow()` alongside the other agents:
   ```python
   <name> = <Name>Agent(skill_registry, **agent_kwargs)
   ```

3. **Define a node function** following the existing pattern:
   ```python
   def <name>_node(state: AgentState) -> dict:
       input_data = {"messages": state["messages"]}
       result = <name>.process(state["messages"])
       output = {
           "current_agent": "<name>",
           # map result keys to AgentState fields as needed
       }
       _log_agent("<Name>Agent", input_data, output)
       return output
   ```

4. **Register the node**:
   ```python
   workflow.add_node("<name>", <name>_node)
   ```

5. **Add edges** — connect the node to the graph with `add_edge` or
   `add_conditional_edges` depending on the routing logic.

6. If the new agent's output needs a new state field, add it to
   `AgentState` in `src/graph/state.py` and to `create_initial_state()`.

## Step 7: Update router

If the router should be able to route to this new agent:

1. Add the new route to `RouterAgent.VALID_ROUTES` in
   `src/agents/router/agent.py`.

2. Add the route description to `RouterAgent.base_system_prompt`.

3. Update `src/agents/router/skills/routing/SKILL.md` with a new section
   describing when to route to this agent.

4. Update `route_decision()` in `src/graph/workflow.py` to handle the
   new route value.

## Step 8: Run verification

Run the verification skill to confirm nothing is broken:

```bash
uv run python -c "import src.main; import src.graph; import src.agents; import src.skills"
uv run python -m src.main --test
```

Expected: "Workflow created successfully", correct skill count, "All tests passed".
