"""Healthcare Concierge (Orchestrator) - routes queries to specialist agents.

Deployed as an AWS Bedrock AgentCore runtime. Uses Strands Agent with @tool
decorators that call sub-agents via HTTP, following the A2A communication pattern.
Per-session agent instances maintain conversation history.
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

POLICY_AGENT_URL = os.getenv("POLICY_AGENT_URL", "http://policy-agent:8080/invocations")
PROVIDER_AGENT_URL = os.getenv("PROVIDER_AGENT_URL", "http://provider-agent:8080/invocations")
RESEARCH_AGENT_URL = os.getenv("RESEARCH_AGENT_URL", "http://research-agent:8080/invocations")

# ---------------------------------------------------------------------------
# Session management: per-session Agent instances with conversation history
# ---------------------------------------------------------------------------
_session_agents: dict[str, Agent] = {}
_MAX_SESSIONS = 100


def load_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _call_agent(url: str, question: str) -> str:
    """POST to a sub-agent's /invocations endpoint and return the response text."""
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json={"message": question})
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", json.dumps(data))
    except httpx.HTTPStatusError as e:
        logger.error("Sub-agent HTTP error at %s: %s", url, e)
        return f"Error contacting agent: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error("Sub-agent call failed at %s: %s", url, e)
        return f"Error contacting agent: {e}"


@tool
def query_policy(question: str) -> str:
    """Ask the Policy Agent about insurance coverage, copays, coinsurance, deductibles, benefits, and plan details.

    Args:
        question: The policy/coverage question to ask.
    """
    logger.info("Routing to PolicyAgent: %s", question[:100])
    return _call_agent(POLICY_AGENT_URL, question)


@tool
def find_providers(question: str) -> str:
    """Ask the Provider Agent to find in-network healthcare providers by location or specialty.

    Args:
        question: The provider search query including location and/or specialty.
    """
    logger.info("Routing to ProviderAgent: %s", question[:100])
    return _call_agent(PROVIDER_AGENT_URL, question)


@tool
def research_health(question: str) -> str:
    """Ask the Research Agent to look up health information about symptoms, conditions, treatments, or procedures.

    Args:
        question: The health/medical research question.
    """
    logger.info("Routing to ResearchAgent: %s", question[:100])
    return _call_agent(RESEARCH_AGENT_URL, question)


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
    "3. You may call the same tool again with a rephrased question if needed.\n"
    "4. Once you have a satisfactory answer, synthesize a clear, helpful response.\n"
    "5. If unsure what the user needs, ask a clarifying question.\n"
    "6. Never fabricate medical advice — only relay what the tools return."
)


def _get_session_agent(session_id: str) -> Agent:
    """Get or create an Agent for the given session."""
    if session_id not in _session_agents:
        # Evict oldest sessions if at capacity
        if len(_session_agents) >= _MAX_SESSIONS:
            oldest = next(iter(_session_agents))
            del _session_agents[oldest]
            logger.info("Evicted session %s (at capacity %d)", oldest, _MAX_SESSIONS)

        _session_agents[session_id] = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=[query_policy, find_providers, research_health],
            callback_handler=None,
        )
    return _session_agents[session_id]


@app.entrypoint
async def invoke(payload, context):
    message = payload.get("message", "")
    if not message:
        yield "Hi there! I can help navigate benefits, providers, and coverage details. Ask me a healthcare question!"
        return

    session_id = payload.get("session_id") or getattr(context, "session_id", "default")
    logger.info("Orchestrator [session=%s] query: %s", session_id, message[:120])

    agent = _get_session_agent(session_id)
    stream = agent.stream_async(message)
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
