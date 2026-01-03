"""Provider Agent - finds in-network healthcare providers by location/specialty.

Uses a Strands Agent with a @tool-decorated list_doctors function.
"""

import json
import logging
from pathlib import Path

from strands import Agent, tool

from shared.model import load_model

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "doctors.json"
DOCTORS: list[dict] = json.loads(DATA_PATH.read_text())
logger.info("Loaded %d providers from doctors.json", len(DOCTORS))

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
    """Get or create the singleton provider agent."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=[list_doctors],
            callback_handler=None,
        )
    return _agent


def find_providers(question: str) -> str:
    """Find in-network providers matching the query."""
    logger.info("ProviderAgent query: %s", question[:120])
    agent = get_agent()
    result = agent(question)
    answer = str(result)
    logger.info("ProviderAgent response length: %d chars", len(answer))
    return answer
