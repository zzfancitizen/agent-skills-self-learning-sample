---
name: appfnd-agent-bootstrap
description: Bootstrap a complete App Foundation agent project. Use when the user wants to create a new AI agent for deployment on SAP App Foundation runtime, or asks to create an agent. 
---

# App Foundation Agent Bootstrap

This skill creates a complete, ready-to-deploy AI agent project for SAP App Foundation managed runtime. It includes A2A protocol, LangGraph-based agent architecture, SAP AI Core integration, App Foundation Python SDK, as well as ci/cd pipeline via github actions.

## Project Structure

Create the following files in the current working directory:

```
./
├── app.yaml              # App Foundation workload configuration
├── Dockerfile            # Container build configuration
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore patterns
├── README.md            # Project documentation
└── app/
    ├── __init__.py      # Package marker
    ├── main.py          # A2A server entry point
    ├── agent_executor.py # Request handler
    ├── agent.py         # Core agent logic
    └── .env.example     # Environment variables for running locally
```

## Step 1: Create app.yaml

This is the App Foundation workload configuration that defines how the agent is deployed.

```yaml
apiVersion: workload.appfnd.sap/v1
kind: Agent
metadata:
  name: sample-agent
  namespace: sample-agent
spec:
  container:
    buildPath: .
    port: 5000
  resources:
    requests:
      memory: "256Mi"
      cpu: "50m"
    limits:
      memory: "512Mi"
      cpu: "200m"
  service:
    apiAuth:
      path: /*
      type: jwt
  models:
  - executableId: aws-bedrock
    name: anthropic--claude-4.5-sonnet
    version: latest
```

**Key configuration options:**
- `metadata.name`: The agent's unique identifier (dev should renamed it)
- `metadata.namespace`: Kubernetes namespace for deployment - usually the same as name
- `spec.container.port`: The port the agent listens on (default: 5000)
- `spec.resources`: CPU and memory limits
- `spec.models`: SAP AI Core LLM models the agent can access

## Step 2: Create Dockerfile

```dockerfile
FROM docker-hub.common.cdn.repositories.cloud.sap/python:3.13

ARG ARTIFACTORY_USER
ARG ARTIFACTORY_TOKEN

ENV ARTIFACTORY_URL="https://common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python"
ENV ARTIFACTORY_USER=${ARTIFACTORY_USER}
ENV ARTIFACTORY_TOKEN=${ARTIFACTORY_TOKEN}

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    mkdir -p /root/.pip && \
    printf "[global]\n\
index-url = https://%s:%s@common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python/simple\n\
extra-index-url = https://pypi.org/simple\n" \
    "$ARTIFACTORY_USER" "$ARTIFACTORY_TOKEN" > /root/.pip/pip.conf && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.pip

COPY app/ ./app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

CMD ["python", "app/main.py", "--host", "0.0.0.0", "--port", "5000"]
```

**Notes:**
- Uses SAP's internal Python image
- Requires Artifactory credentials for private packages (automatically binded during deployment)
- Installs Application Foundation SDK from internal repository 

## Step 3: Create requirements.txt

```text
litellm==1.81.0
rich==14.2.0
langchain==1.2.6
langchain-core==1.2.7
langchain-litellm==0.3.5
langgraph==1.0.6
a2a-sdk[all]==0.3.22
uvicorn==0.40.0
httpx==0.28.1
python-dotenv==1.2.1
click==8.3.1
application-foundation-sdk-python==1.1.3+aicore
```

## Step 4: Create .gitignore

```gitignore
.env
.idea/
app/__pycache__/
app/.env
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.DS_Store
```

## Step 5: Create README.md

```markdown
# Sample Agent

An AI agent built with Application Foundation for SAP App Foundation runtime.

## Overview

This agent uses:
- **A2A Protocol**: For agent-to-agent communication
- **LangGraph**: For agent orchestration
- **LiteLLM**: For model abstraction
- **Application Foundation SDK**: For SAP AI Core integration

## Project Structure

- `app.yaml` - App Foundation workload configuration
- `Dockerfile` - Container build configuration
- `app/main.py` - A2A server entry point
- `app/agent_executor.py` - Request handling
- `app/agent.py` - Core agent logic

## Local Development

Running locally requires SAP Artifactory credentials and AI Core configuration due to internal SDK dependencies.

**For detailed local development instructions, use the `appfnd-agent-run-local` skill.**

Quick overview:
1. Set up `app/.env.local` with Artifactory and AI Core credentials
2. Install dependencies using SAP Artifactory index
3. Export environment variables and run the agent

## Deployment

Deploy to App Foundation runtime using the CLI:
```bash
appfnd deploy
```

## Configuration

### Model Selection

The default model is `anthropic--claude-4.5-sonnet`. To change it, update:
1. `app.yaml` - Add the model to the `models` list
2. `app/agent.py` - Update the `ChatLiteLLM` model parameter

### Resource Limits

Adjust CPU and memory in `app.yaml` under `spec.resources`.
```

## Step 6: Create app/__init__.py

Create an empty file to mark the directory as a Python package:

```python
# App Foundation Agent
```

## Step 7: Create app/main.py

```python
import json
import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import AgentExecutor

from application_foundation.aicore import set_aicore_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

set_aicore_config()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


@click.command()
@click.option("--host", default=HOST)
@click.option("--port", default=PORT)
def main(host: str, port: int):
    skill = AgentSkill(
        id="sample-agent",
        name="Sample Agent",
        description="A sample AI agent built with LangGraph and Application Foundation.",
        tags=["sample", "langgraph", "application-foundation"],
        examples=["Hello, how can you help me?", "What can you do?"],
    )
    agent_card = AgentCard(
        name="Sample Agent",
        description="A sample AI agent demonstrating Application Foundation Agent capabilities.",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        skills=[skill],
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=AgentExecutor(),
            task_store=InMemoryTaskStore(),
        ),
    )
    logger.info(f"Starting A2A server at http://{host}:{port}")
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
```

**Key components:**
- `AgentSkill`: Defines what the agent can do
- `AgentCard`: Agent metadata for discovery
- `A2AStarletteApplication`: A2A protocol server
- `set_aicore_config()`: Configures SAP AI Core integration

## Step 8: Create app/agent_executor.py

```python
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import InternalError, Part, TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from agent import SampleAgent

logger = logging.getLogger(__name__)


class AgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = SampleAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        try:
            async for item in self.agent.stream(query, task.context_id):
                if not item["is_task_complete"] and not item["require_user_input"]:
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(item["content"], task.context_id, task.id),
                    )
                elif item["require_user_input"]:
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(item["content"], task.context_id, task.id),
                        final=True,
                    )
                    break
                else:
                    await updater.add_artifact([Part(root=TextPart(text=item["content"]))], name="agent_result")
                    await updater.complete()
                    break
        except Exception as e:
            logger.exception("Agent execution error")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
```

**Key components:**
- `AgentExecutor`: Handles incoming requests
- `TaskUpdater`: Manages task state and streaming
- `TaskState`: working, input_required, completed

## Step 9: Create app/agent.py

```python
import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_litellm import ChatLiteLLM
from langgraph.graph import START, MessagesState, StateGraph

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful AI assistant built with Application Foundation.
You can help users with general questions and tasks. Be friendly, concise, and helpful."""


@dataclass
class AgentResponse:
    status: Literal["input_required", "completed", "error"]
    message: str


class SampleAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.llm = ChatLiteLLM(model="sap/anthropic--claude-4.5-sonnet")
        self.graph = self._build_graph()

    def _build_graph(self):
        async def call_model(state: MessagesState):
            response = await self.llm.ainvoke(state["messages"])
            return {"messages": [response]}

        builder = StateGraph(MessagesState)
        builder.add_node("model", call_model)
        builder.add_edge(START, "model")
        return builder.compile()

    async def stream(self, query: str, context_id: str) -> AsyncGenerator[dict, None]:
        yield {"is_task_complete": False, "require_user_input": False, "content": "Processing..."}
        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=query)]
            result = await self.graph.ainvoke({"messages": messages})
            response = result["messages"][-1].content
            yield {"is_task_complete": True, "require_user_input": False, "content": response}
        except Exception as e:
            yield {"is_task_complete": True, "require_user_input": False, "content": f"Error: {e}"}

    def invoke(self, query: str, context_id: str) -> AgentResponse:
        import asyncio
        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=query)]
            result = asyncio.run(self.graph.ainvoke({"messages": messages}))
            response = result["messages"][-1].content
            return AgentResponse(status="completed", message=response)
        except Exception as e:
            return AgentResponse(status="error", message=f"Error: {e}")
```

**Key components:**
- `SampleAgent`: Core agent class
- `ChatLiteLLM`: LLM abstraction layer
- `StateGraph`: LangGraph for agent orchestration
- `SYSTEM_PROMPT`: Customize agent behavior here

## Step 10: Create app/.env.example if you want to run locally (not needed on deployment)

```env
# ARTIFACTORY_USER=
# ARTIFACTORY_TOKEN=

# AICORE_SERVICE_URL=
# AICORE_CLIENT_ID=
# AICORE_CLIENT_SECRET=
# AICORE_AUTH_URL=
```

## Customization Points

After creating the project, you can customize:

1. **Agent Name**: Update `metadata.name` in `app.yaml` and the skill/card definitions in `main.py`
2. **System Prompt**: Modify `SYSTEM_PROMPT` in `agent.py` to change agent behavior
3. **Model**: Change the model in `app.yaml` and `agent.py`
4. **Skills**: Add more `AgentSkill` definitions in `main.py`
5. **Tools**: Extend the LangGraph in `agent.py` to add tool capabilities

## Next Steps

After creating the project:

1. Review and customize the configuration
2. **Run locally**: Use the `appfnd-agent-run-local` skill for detailed instructions on setting up credentials and running the agent locally
3. Deploy to App Foundation runtime

> **Note**: Running locally requires SAP Artifactory credentials for installing the Application Foundation SDK. Simple `pip install` and `python app/main.py` will not work without proper Artifactory configuration.
