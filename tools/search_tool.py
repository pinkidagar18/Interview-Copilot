# tools/search_tool.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_search_tool():
    """
    Returns the best available search tool.
    Uses Tavily if API key exists, otherwise DuckDuckGo (free).
    Switch happens with zero code changes in agents.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key and tavily_key != "your_tavily_key_here":
        try:
            from langchain_tavily import TavilySearch
            print("🔍 Using Tavily search")
            return TavilySearch(max_results=5)
        except ImportError:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults
                print("🔍 Using Tavily search (legacy)")
                return TavilySearchResults(max_results=5)
            except Exception:
                pass

    # Default: DuckDuckGo (free, no key needed)
    from langchain_community.tools import DuckDuckGoSearchRun
    print("🔍 Using DuckDuckGo search")
    return DuckDuckGoSearchRun()


def search_web(query: str) -> str:
    """
    Simple wrapper — searches web and returns text results.
    """
    tool = get_search_tool()
    try:
        result = tool.run(query)
        return result
    except Exception as e:
        return f"Search failed: {str(e)}"