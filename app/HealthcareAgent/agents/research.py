"""Research Agent - provides health information via web search."""

import json
import logging
import os

import httpx

from shared.bedrock_client import converse_with_tools

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "toolSpec": {
            "name": "web_search",
            "description": "Search Google for current health and medical information using the Serper API.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find health information",
                        },
                    },
                    "required": ["query"],
                }
            },
        }
    }
]

SYSTEM_PROMPT = (
    "You are a healthcare research agent. Use the web_search tool to find "
    "current information about health conditions, symptoms, treatments, and procedures. "
    "Always cite your sources with URLs. Present information clearly and accurately. "
    "You may call web_search multiple times with different queries if needed."
)


def _web_search(query: str) -> str:
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


def _handle_tool(name: str, tool_input: dict) -> str:
    if name == "web_search":
        return _web_search(tool_input["query"])
    return f"Unknown tool: {name}"


def research_health(question: str) -> str:
    """Research health information via web search."""
    logger.info("ResearchAgent query: %s", question[:120])
    messages = [{"role": "user", "content": [{"text": question}]}]
    answer = converse_with_tools(messages, SYSTEM_PROMPT, TOOLS, _handle_tool)
    logger.info("ResearchAgent response length: %d chars", len(answer))
    return answer
