"""Research Agent - provides health information via web search.

Deployed as a standalone AgentCore runtime. Uses a Strands Agent with a
@tool-decorated web_search function that calls the Serper API.
"""

import json
import logging
import os

import httpx
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


def load_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


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
    global _agent
    if _agent is None:
        _agent = Agent(model=load_model(), system_prompt=SYSTEM_PROMPT, tools=[web_search], callback_handler=None)
    return _agent


@app.entrypoint
async def handle(payload, context):
    message = payload.get("message", "")
    if not message:
        return {"response": "Please provide a health-related question.", "agent": "ResearchAgent"}

    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        return {"response": "Error: SERPER_API_KEY environment variable is required.", "agent": "ResearchAgent"}

    logger.info("ResearchAgent query: %s", message[:120])
    agent = get_agent()
    result = agent(message)
    answer = str(result)
    logger.info("ResearchAgent response length: %d chars", len(answer))
    return {"response": answer, "agent": "ResearchAgent"}


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
