# ============================================================
# tools/tavily_search.py — Web Search Tool for Research Agent
# ============================================================
# This file gives our Research Agent the ability to search
# the real internet using Tavily's AI-optimized search API.
# ============================================================

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
import requests

# Load API keys from .env file into environment
load_dotenv()

# Read Tavily API key from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@tool
def search_company_info(query: str) -> str:
    """
    Search the internet for real-time company information.
    Use this to find news, financials, and developments.

    Args:
        query: The search query string about a company

    Returns:
        A string containing search results from the web
    """

    try:
        # Call Tavily API directly — most reliable method
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5
            }
        )

        # Parse the JSON response into a Python dictionary
        data = response.json()

        # Extract the results list from response
        results = data.get("results", [])

        if not results:
            return "No search results found for this query."

        # Format results into clean readable text
        formatted_results = ""
        for i, result in enumerate(results, 1):
            formatted_results += f"\n--- Result {i} ---\n"
            formatted_results += f"Title: {result.get('title', 'No title')}\n"
            formatted_results += f"Content: {result.get('content', 'No content')}\n"
            formatted_results += f"Source: {result.get('url', 'No URL')}\n"

        return formatted_results

    except Exception as e:
        # If anything fails, return error instead of crashing
        return f"Search failed: {str(e)}"


# ============================================================
# TEST BLOCK — only runs when this file is run directly
# ============================================================
if __name__ == "__main__":
    print("Testing Tavily Search Tool...")
    print("-" * 50)
    result = search_company_info.invoke("Tesla recent news 2025")
    print(result)