"""Research Agent - provides health information via web search.

Uses a Strands Agent with a @tool-decorated web_search function
that calls the Serper API.
"""

import json
import logging
import os

import httpx
from strands import Agent, tool

from shared.model import load_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a healthcare research agent. Use the web_search tool to find "
    "current information about health conditions, symptoms, treatments, and procedures. "
    "Always cite your sources with URLs. Present information clearly and accurately. "
    "You may call web_search multiple times with different queries if needed."
)


@tool
def web_search(query: str) -> str:
    """Search Google for current health and medical information using the Serper API.

    Args:
        query: The search query to find health information.
    """
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        return json.dumps({"error": "SERPER_API_KEY not configured"})

    with httpx.Client(timeout=15.0) as client:
        response = client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 8},
        )
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
        })
    return json.dumps(results, indent=2)


_agent = None


def get_agent() -> Agent:
    """Get or create the singleton research agent."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=[web_search],
            callback_handler=None,
        )
    return _agent


def research_health(question: str) -> str:
    """Research health information via web search."""
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        return "Error: SERPER_API_KEY environment variable is required."

    logger.info("ResearchAgent query: %s", question[:120])
    agent = get_agent()
    result = agent(question)
    answer = str(result)
    logger.info("ResearchAgent response length: %d chars", len(answer))
    return answer
