"""
Visualize the LangGraph workflow as an image
"""

from src.graph.workflow import create_workflow
from src.skills import SkillRegistry


def main():
    # Initialize skill registry
    registry = SkillRegistry("./skills")
    
    # Create the workflow
    workflow = create_workflow(registry)
    
    # Get the graph visualization as PNG
    # LangGraph provides get_graph() method which returns a drawable graph
    graph = workflow.get_graph()
    
    # Option 1: Generate PNG image using draw_mermaid_png (requires internet for mermaid.ink)
    try:
        png_data = graph.draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        print("✅ Graph saved as 'workflow_graph.png'")
    except Exception as e:
        print(f"⚠️ draw_mermaid_png failed: {e}")
        print("Trying ASCII visualization instead...")
        
        # Option 2: Print Mermaid diagram code (can be rendered online)
        mermaid_code = graph.draw_mermaid()
        print("\n📊 Mermaid Diagram Code:")
        print("-" * 40)
        print(mermaid_code)
        print("-" * 40)
        print("\n💡 Tip: Copy the above code and paste it at https://mermaid.live to visualize")
        
        # Save mermaid code to file
        with open("workflow_graph.mmd", "w") as f:
            f.write(mermaid_code)
        print("✅ Mermaid code saved as 'workflow_graph.mmd'")
    
    # Option 3: Print ASCII representation
    try:
        ascii_graph = graph.draw_ascii()
        print("\n📊 ASCII Graph Representation:")
        print("-" * 40)
        print(ascii_graph)
        print("-" * 40)
    except Exception as e:
        print(f"ASCII visualization not available: {e}")


if __name__ == "__main__":
    main()
