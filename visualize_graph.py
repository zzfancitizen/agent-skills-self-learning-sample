"""
Visualize the LangGraph workflow as an image
"""

import logging

from src.graph.workflow import create_workflow
from src.skills import SkillRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # Initialize empty skill registry (agents will self-register their skills)
    registry = SkillRegistry()

    # Create the workflow
    logger.info("Creating workflow...")
    workflow = create_workflow(registry)

    # Get the graph visualization
    graph = workflow.get_graph()

    # Option 1: Generate PNG image using draw_mermaid_png (requires internet for mermaid.ink)
    try:
        png_data = graph.draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        logger.info("Graph saved as 'workflow_graph.png'")
    except Exception as e:
        logger.warning("draw_mermaid_png failed: %s", e)
        logger.info("Trying Mermaid code export instead...")

        # Option 2: Export Mermaid diagram code (can be rendered online)
        mermaid_code = graph.draw_mermaid()
        logger.info("Mermaid Diagram Code:\n%s", mermaid_code)
        logger.info("Tip: Copy the above code and paste it at https://mermaid.live to visualize")

        # Save mermaid code to file
        with open("workflow_graph.mmd", "w") as f:
            f.write(mermaid_code)
        logger.info("Mermaid code saved as 'workflow_graph.mmd'")

    # Option 3: ASCII representation
    try:
        ascii_graph = graph.draw_ascii()
        logger.info("ASCII Graph Representation:\n%s", ascii_graph)
    except Exception as e:
        logger.debug("ASCII visualization not available: %s", e)


if __name__ == "__main__":
    main()
