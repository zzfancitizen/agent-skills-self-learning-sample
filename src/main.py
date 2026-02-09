"""
Skill-enabled Multi-Agent System

Main entry point
"""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def main():
    """Main entry function"""
    parser = argparse.ArgumentParser(
        description="Skill-enabled Multi-Agent System"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sap/anthropic--claude-4.5-opus",
        help="Model to use"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test mode"
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List all available skills"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        help="User query"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create empty SkillRegistry; skills are self-loaded by each agent
    from src.skills import SkillRegistry
    registry = SkillRegistry()

    # List skills (create agents first to trigger skill loading)
    if args.list_skills:
        from src.agents import RouterAgent, ProposalAgent, ExecutorAgent
        RouterAgent(registry, model=args.model)
        ProposalAgent(registry, model=args.model)
        ExecutorAgent(registry, model=args.model)
        logger.info("Available Skills:\n%s", registry.get_skills_summary())
        return 0

    # Test mode
    if args.test:
        return run_test(registry, args.model)

    # Interactive mode or single query
    if args.query:
        return run_single_query(args.query, registry, args.model)
    else:
        return run_interactive(registry, args.model)


def run_test(registry, model: str) -> int:
    """Run tests"""
    logger.info("=" * 50)
    logger.info("Skill-enabled Multi-Agent System Test")
    logger.info("=" * 50)

    # Test 1: Workflow creation (triggers agent skill loading)
    logger.info("[Test 1] Workflow creation")
    try:
        from src.graph import create_workflow
        workflow = create_workflow(registry, model=model)
        logger.info("  Workflow created successfully")
    except Exception as e:
        logger.error("  Workflow creation failed: %s", e)
        return 1

    # Test 2: Skill loading (agents registered their skills in previous step)
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
            from src.graph import run_workflow
            result = run_workflow(
                "What is machine learning?",
                model=model
            )
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


def run_single_query(query: str, registry, model: str) -> int:
    """Run a single query"""
    from src.graph import run_workflow

    logger.info("Processing query: %s", query)
    result = run_workflow(
        query,
        registry=registry,
        model=model
    )
    logger.info("Query result:\n%s", result)
    return 0


def run_interactive(registry, model: str) -> int:
    """Interactive mode"""
    from src.graph import run_workflow

    logger.info("Skill-enabled Multi-Agent System")
    logger.info("Type 'quit' or 'exit' to quit")
    logger.info("-" * 40)

    while True:
        try:
            query = input("\nYou: ").strip()
            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                logger.info("Goodbye!")
                break

            result = run_workflow(query, registry=registry, model=model)
            logger.info("Agent: %s", result)

        except KeyboardInterrupt:
            logger.info("Goodbye!")
            break
        except Exception as e:
            logger.error("Error: %s", e)

    return 0


if __name__ == "__main__":
    exit(main())
