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

session_histories: dict[str, list[dict]] = {}

TOOLS = [
    {"toolSpec": {"name": "query_policy", "description": "Ask about insurance coverage, copays, coinsurance, deductibles, benefits, and plan details.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The policy/coverage question to ask"}}, "required": ["question"]}}}},
    {"toolSpec": {"name": "find_providers", "description": "Find in-network healthcare providers by location or specialty.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The provider search query including location and/or specialty"}}, "required": ["question"]}}}},
    {"toolSpec": {"name": "research_health", "description": "Look up health information about symptoms, conditions, treatments, procedures, or general medical knowledge.", "inputSchema": {"json": {"type": "object", "properties": {"question": {"type": "string", "description": "The health/medical research question"}}, "required": ["question"]}}}},
]

SYSTEM_PROMPT = (
    "You are a friendly healthcare concierge. You help users navigate their "
    "insurance benefits, find in-network providers, and understand health conditions.\n\n"
    "You have three specialist tools:\n"
    "- query_policy: For insurance coverage, benefits, copays, deductibles\n"
    "- find_providers: For finding doctors/providers by location or specialty\n"
    "- research_health: For health conditions, symptoms, treatments, medical info\n\n"
    "ROUTING RULES:\n"
    "1. Choose the tool(s) most relevant to the user's question.\n"
    "2. After receiving a tool result, evaluate its quality:\n"
    "   - If the result is vague, unhelpful, says \"I don't know\", or fails to "
    "answer the question, call a DIFFERENT tool to get a better answer.\n"
    "   - For example, if query_policy returns \"I don't know\" for a benefits "
    "question, try research_health to find general information instead.\n"
    "   - If find_providers returns no matching doctors, try a broader search "
    "or inform the user with what you do know.\n"
    "3. You may call the same tool again with a rephrased question if you "
    "believe the original query was too narrow.\n"
    "4. Once you have a satisfactory answer (or have exhausted alternatives), "
    "synthesize everything into a clear, helpful response.\n"
    "5. If unsure what the user needs, ask a clarifying question.\n"
    "6. Never fabricate medical advice — only relay what the tools return."
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
        return {
            "response": "Hi there! I can help navigate benefits, providers, and coverage details. Ask me a healthcare question!",
            "agent": "HealthcareConcierge",
        }

    session_id = payload.get("session_id") or getattr(context, "session_id", "default")
    if session_id not in session_histories:
        session_histories[session_id] = []
    history = session_histories[session_id]

    logger.info("Orchestrator [session=%s] query: %s", session_id, message[:120])

    messages = list(history)
    messages.append({"role": "user", "content": [{"text": message}]})
    answer = converse_with_tools(messages, SYSTEM_PROMPT, TOOLS, handle_tool)

    history.append({"role": "user", "content": [{"text": message}]})
    history.append({"role": "assistant", "content": [{"text": answer}]})
    if len(history) > 40:
        session_histories[session_id] = history[-40:]

    logger.info("Orchestrator response length: %d chars", len(answer))
    return {"response": answer, "agent": "HealthcareConcierge"}


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
