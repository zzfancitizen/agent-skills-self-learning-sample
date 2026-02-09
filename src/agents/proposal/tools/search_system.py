"""
Search System Tool - Search system data for generating proposals

This tool is exclusively for ProposalAgent use, to query system data for analysis and recommendations.
"""

from langchain_core.tools import tool


@tool
def search_system_tool(query: str) -> str:
    """
    Search system data to obtain information for generating proposals.

    This tool allows ProposalAgent to query system data for information
    needed to generate solution proposals.

    Args:
        query: Search query string describing the information to find

    Returns:
        System data relevant to the query
    """
    # TODO: Implement actual search logic
    # Currently returns a placeholder result; concrete implementation to be added later
    return f"[search_system] No results found for query: '{query}'. (Search not yet implemented)"
