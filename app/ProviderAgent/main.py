"""Provider Agent - finds in-network healthcare providers by location/specialty.

Deployed as a standalone AgentCore runtime. Uses a Strands Agent with a
@tool-decorated list_doctors function.
"""

import json
import logging
import os
from pathlib import Path

from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

DATA_PATH = Path(__file__).resolve().parent / "data" / "doctors.json"
DOCTORS: list[dict] = json.loads(DATA_PATH.read_text())
logger.info("Loaded %d providers from doctors.json", len(DOCTORS))


def load_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


SYSTEM_PROMPT = (
    "You are a healthcare provider lookup agent. Your task is to find and list "
    "in-network healthcare providers using the list_doctors tool. "
    "Always call the tool to retrieve providers — do not fabricate results. "
    "Present the results clearly, including name, specialty, address, phone, "
    "hospital affiliations, insurance accepted, and whether they accept new patients."
)


@tool
def list_doctors(state: str = None, city: str = None) -> str:
    """Search the provider database for doctors by state and/or city.

    Args:
        state: Two-letter state code (e.g. 'CA', 'TX', 'FL')
        city: City name (e.g. 'Houston', 'Miami')
    """
    if not state and not city:
        return json.dumps([{"error": "Please provide a state or a city."}])
    target_state = state.strip().lower() if state else None
    target_city = city.strip().lower() if city else None
    results = [
        doc for doc in DOCTORS
        if (not target_state or doc["address"]["state"].lower() == target_state)
        and (not target_city or doc["address"]["city"].lower() == target_city)
    ]
    logger.info("list_doctors(state=%s, city=%s) found %d results", state, city, len(results))
    return json.dumps(results, indent=2)


_agent = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent(model=load_model(), system_prompt=SYSTEM_PROMPT, tools=[list_doctors], callback_handler=None)
    return _agent


@app.entrypoint
async def handle(payload, context):
    message = payload.get("message", "")
    if not message:
        return {"response": "Please provide a query about healthcare providers.", "agent": "ProviderAgent"}

    logger.info("ProviderAgent query: %s", message[:120])
    agent = get_agent()
    result = agent(message)
    answer = str(result)
    logger.info("ProviderAgent response length: %d chars", len(answer))
    return {"response": answer, "agent": "ProviderAgent"}


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
