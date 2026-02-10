"""
App Foundation Agent - A2A Service Entry Point

This is the latest entry point integrating A2A protocol server
with the existing skill-enabled multi-agent system.
"""

import logging
import os
import sys

# Add project root to path for src.* imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
# Add current dir for local imports (agent_executor, agent)
sys.path.insert(0, os.path.dirname(__file__))

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from agent_executor import AgentExecutor

from application_foundation.aicore import set_aicore_config

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

set_aicore_config()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))


@click.command()
@click.option("--host", default=HOST, help="Host to bind the server")
@click.option("--port", default=PORT, help="Port to bind the server")
@click.option("--model", default="sap/anthropic--claude-4.5-sonnet", help="Model to use")
@click.option("--test", is_flag=True, help="Run test mode")
@click.option("--list-skills", is_flag=True, help="List all available skills")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Log level (default: INFO)",
)
@click.argument("query", required=False)
def main(host: str, port: int, model: str, test: bool, list_skills: bool, log_level: str, query: str):
    """App Foundation Agent - A2A Service with multi-agent workflow.

    Runs the A2A server by default. Use --test, --list-skills, or provide
    a QUERY argument to use legacy CLI modes.
    """
    # Reconfigure logging with requested level
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    # --- Legacy CLI modes (from original src/main.py) ---

    if list_skills:
        _list_skills(model)
        return

    if test:
        exit(_run_test(model))

    if query:
        exit(_run_single_query(query, model))

    # --- Default: A2A server mode ---
    _serve_a2a(host, port)


def _serve_a2a(host: str, port: int):
    """Start the A2A protocol server."""
    routing_skill = AgentSkill(
        id="routing",
        name="Intelligent Routing",
        description="Analyzes user requests and routes them to the most appropriate agent: "
                    "proposal (for analysis & recommendations), executor (for task execution), "
                    "or direct response (for simple Q&A).",
        tags=["router", "orchestration", "routing"],
        examples=[
            "Analyze the pros and cons of microservices vs monolith architecture.",
            "Execute the deployment plan I described above.",
            "What is the difference between REST and GraphQL?",
        ],
    )
    analysis_skill = AgentSkill(
        id="analysis",
        name="Problem Analysis & Solution Proposal",
        description="Performs in-depth problem analysis, decomposes complex issues into sub-problems, "
                    "evaluates multiple solution options with pros/cons, and generates actionable "
                    "implementation plans with prioritized steps.",
        tags=["proposal", "planning", "analysis"],
        examples=[
            "How can I improve my application's performance?",
            "What is the best strategy to migrate our database?",
            "Help me design a caching layer for our API.",
        ],
    )
    execution_skill = AgentSkill(
        id="execution",
        name="Task Execution",
        description="Executes specific operations step-by-step based on a given plan or proposal, "
                    "records results for each step, handles errors, and generates execution reports.",
        tags=["executor", "action", "operation"],
        examples=[
            "Execute the migration steps from the proposal above.",
            "Run the optimization plan we discussed.",
            "Implement the configuration changes listed.",
        ],
    )
    agent_card = AgentCard(
        name="Skill-enabled Multi-Agent System",
        description="A multi-agent system powered by LangGraph and Application Foundation. "
                    "It orchestrates three specialized agents — Router, Proposal, and Executor — "
                    "each equipped with self-loaded skills, to analyze problems, propose solutions, "
                    "and execute tasks end-to-end.",
        url=os.environ.get("AGENT_PUBLIC_URL", f"http://{host}:{port}/"),
        version="0.1.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True, pushNotifications=False),
        skills=[routing_skill, analysis_skill, execution_skill],
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


# ---------------------------------------------------------------------------
# Legacy CLI helpers (integrated from src/main.py)
# ---------------------------------------------------------------------------

def _list_skills(model: str):
    """List all available skills."""
    from src.skills import SkillRegistry
    from src.agents import RouterAgent, ProposalAgent, ExecutorAgent

    registry = SkillRegistry()
    RouterAgent(registry, model=model)
    ProposalAgent(registry, model=model)
    ExecutorAgent(registry, model=model)
    logger.info("Available Skills:\n%s", registry.get_skills_summary())


def _run_test(model: str) -> int:
    """Run tests (from original main.py)."""
    from src.skills import SkillRegistry
    from src.graph import create_workflow, run_workflow

    logger.info("=" * 50)
    logger.info("Skill-enabled Multi-Agent System Test")
    logger.info("=" * 50)

    registry = SkillRegistry()

    # Test 1: Workflow creation
    logger.info("[Test 1] Workflow creation")
    try:
        workflow = create_workflow(registry, model=model)
        logger.info("  Workflow created successfully")
    except Exception as e:
        logger.error("  Workflow creation failed: %s", e)
        return 1

    # Test 2: Skill loading
    logger.info("[Test 2] Skill loading")
    skills = registry.list_skills()
    logger.info("  Loaded %d skills: %s", len(skills), skills)

    # Test 3: Skill prompt generation
    logger.info("[Test 3] Skill prompt generation")
    prompt = registry.get_skills_prompt(["routing"])
    logger.info("  Routing skill prompt length: %d chars", len(prompt))

    # Test 4: End-to-end test (requires API key)
    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("[Test 4] End-to-end test")
        try:
            result = run_workflow("What is machine learning?", model=model)
            logger.info("  Response: %s", result[:200] + "..." if len(result) > 200 else result)
            logger.info("  End-to-end test passed")
        except Exception as e:
            logger.error("  End-to-end test failed: %s", e)
            return 1
    else:
        logger.info("[Test 4] End-to-end test (skipped - ANTHROPIC_API_KEY not set)")

    logger.info("=" * 50)
    logger.info("All tests passed")
    logger.info("=" * 50)
    return 0


def _run_single_query(query: str, model: str) -> int:
    """Run a single query (from original main.py)."""
    from src.skills import SkillRegistry
    from src.graph import run_workflow

    registry = SkillRegistry()
    logger.info("Processing query: %s", query)
    result = run_workflow(query, registry=registry, model=model)
    logger.info("Query result:\n%s", result)
    return 0


if __name__ == "__main__":
    main()
