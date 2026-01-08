"""Policy Agent - answers insurance coverage questions using a benefits PDF.

Deployed as a standalone AgentCore runtime. Uses a Strands Agent with the
full policy document embedded in the system prompt.
"""

import logging
import os
from pathlib import Path

from PyPDF2 import PdfReader
from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

PDF_PATH = Path(__file__).resolve().parent / "data" / "2026AnthemgHIPSBC.pdf"


def _load_policy_text() -> str:
    reader = PdfReader(str(PDF_PATH))
    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    text = "\n\n".join(pages)
    logger.info("Loaded policy document: %d characters from %d pages", len(text), len(pages))
    return text


def load_model() -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


POLICY_TEXT = _load_policy_text()

SYSTEM_PROMPT = (
    "You are an expert insurance agent designed to assist with coverage queries. "
    "Use the provided policy document to answer questions about insurance policies. "
    'If the information is not available in the documents, respond with "I don\'t know".\n\n'
    "--- POLICY DOCUMENT ---\n"
    f"{POLICY_TEXT}\n"
    "--- END POLICY DOCUMENT ---"
)

_agent = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent(model=load_model(), system_prompt=SYSTEM_PROMPT, callback_handler=None)
    return _agent


@app.entrypoint
async def handle(payload, context):
    message = payload.get("message", "")
    if not message:
        return {"response": "Please provide a question about your policy.", "agent": "PolicyAgent"}

    logger.info("PolicyAgent query: %s", message[:120])
    agent = get_agent()
    result = agent(message)
    answer = str(result)
    logger.info("PolicyAgent response length: %d chars", len(answer))
    return {"response": answer, "agent": "PolicyAgent"}


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "8080")))
