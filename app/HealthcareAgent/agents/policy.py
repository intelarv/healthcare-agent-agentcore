"""Policy Agent - answers insurance coverage questions using a benefits PDF.

Uses a Strands Agent with the full policy document embedded in the system prompt.
"""

import logging
from pathlib import Path

from PyPDF2 import PdfReader
from strands import Agent

from shared.model import load_model

logger = logging.getLogger(__name__)

PDF_PATH = Path(__file__).resolve().parent.parent / "data" / "2026AnthemgHIPSBC.pdf"


def _load_policy_text() -> str:
    reader = PdfReader(str(PDF_PATH))
    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    text = "\n\n".join(pages)
    logger.info("Loaded policy document: %d characters from %d pages", len(text), len(pages))
    return text


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
    """Get or create the singleton policy agent."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            callback_handler=None,
        )
    return _agent


def query_policy(question: str) -> str:
    """Answer an insurance coverage question using the policy PDF."""
    logger.info("PolicyAgent query: %s", question[:120])
    agent = get_agent()
    result = agent(question)
    answer = str(result)
    logger.info("PolicyAgent response length: %d chars", len(answer))
    return answer
