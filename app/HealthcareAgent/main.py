"""Healthcare Concierge (Orchestrator) - routes queries to specialist agents."""

import logging
import os

from bedrock_agentcore import BedrockAgentCoreApp

from shared.bedrock_client import converse_with_tools
from agents.policy import query_policy
from agents.provider import find_providers
from agents.research import research_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

TOOLS = [
    {"toolSpec": {"name": "query_policy", "description": "Ask about insurance coverage, copays, deductibles, benefits.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The policy question"}}, "required": ["question"]}}}},
    {"toolSpec": {"name": "find_providers", "description": "Find in-network healthcare providers by location or specialty.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The provider search query"}}, "required": ["question"]}}}},
    {"toolSpec": {"name": "research_health", "description": "Look up health information about symptoms, conditions, treatments.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The health research question"}}, "required": ["question"]}}}},
]

SYSTEM_PROMPT = (
    "You are a friendly healthcare concierge. You help users navigate their "
    "insurance benefits, find in-network providers, and understand health conditions.\n\n"
    "You have three specialist tools:\n"
    "- query_policy: For insurance coverage, benefits, copays, deductibles\n"
    "- find_providers: For finding doctors/providers by location or specialty\n"
    "- research_health: For health conditions, symptoms, treatments, medical info\n\n"
    "Choose the tool(s) most relevant to the user's question. "
    "If unsure what the user needs, ask a clarifying question. "
    "Never fabricate medical advice — only relay what the tools return."
)


def handle_tool(name: str, tool_input: dict) -> str:
    question = tool_input.get("question", "")
    if name == "query_policy":
        logger.info("Routing to PolicyAgent: %s", question[:100])
        return query_policy(question)
    elif name == "find_providers":
        logger.info("Routing to ProviderAgent: %s", question[:100])
        return find_providers(question)
    elif name == "research_health":
        logger.info("Routing to ResearchAgent: %s", question[:100])
        return research_health(question)
    return f"Unknown tool: {name}"


@app.entrypoint
async def handle(payload, context):
    message = payload.get("message", "")
    if not message:
        return {"response": "Hi there! Ask me a healthcare question!", "agent": "HealthcareConcierge"}

    logger.info("Orchestrator query: %s", message[:120])
    messages = [{"role": "user", "content": [{"text": message}]}]
    answer = converse_with_tools(messages, SYSTEM_PROMPT, TOOLS, handle_tool)
    logger.info("Orchestrator response length: %d chars", len(answer))
    return {"response": answer, "agent": "HealthcareConcierge"}


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
