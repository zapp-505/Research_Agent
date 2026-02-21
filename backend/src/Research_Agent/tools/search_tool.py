from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode
def search_tool():
    """
    Creates and returns a configured Tavily search tool.
    This tool is used by the agent to perform web searches.
    """
    tool = [TavilySearchResults(max_results=2)]
    return tool

def create_tool_node(tools):
    """
    created and returns a tool node for the specified tools
    """
    return ToolNode(tools=tools)