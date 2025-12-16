"""Provider Agent - finds in-network healthcare providers by location/specialty."""

import json
import logging
from pathlib import Path

from shared.bedrock_client import converse_with_tools

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "doctors.json"
DOCTORS: list[dict] = json.loads(DATA_PATH.read_text())
logger.info("Loaded %d providers from doctors.json", len(DOCTORS))

TOOLS = [
    {
        "toolSpec": {
            "name": "list_doctors",
            "description": (
                "Search the provider database for doctors by state and/or city. "
                "At least one of state or city must be provided. "
                "State should be a two-letter code (e.g. 'TX'). City is the city name (e.g. 'Austin')."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "Two-letter state code (e.g. 'CA', 'TX', 'FL')",
                        },
                        "city": {
                            "type": "string",
                            "description": "City name (e.g. 'Houston', 'Miami')",
                        },
                    },
                }
            },
        }
    }
]

SYSTEM_PROMPT = (
    "You are a healthcare provider lookup agent. Your task is to find and list "
    "in-network healthcare providers using the list_doctors tool. "
    "Always call the tool to retrieve providers — do not fabricate results. "
    "Present the results clearly, including name, specialty, address, phone, "
    "hospital affiliations, insurance accepted, and whether they accept new patients."
)


def _list_doctors(state: str | None = None, city: str | None = None) -> str:
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


def _handle_tool(name: str, tool_input: dict) -> str:
    if name == "list_doctors":
        return _list_doctors(tool_input.get("state"), tool_input.get("city"))
    return f"Unknown tool: {name}"


def find_providers(question: str) -> str:
    """Find in-network providers matching the query."""
    logger.info("ProviderAgent query: %s", question[:120])
    messages = [{"role": "user", "content": [{"text": question}]}]
    answer = converse_with_tools(messages, SYSTEM_PROMPT, TOOLS, _handle_tool)
    logger.info("ProviderAgent response length: %d chars", len(answer))
    return answer
