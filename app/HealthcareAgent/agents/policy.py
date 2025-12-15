"""Policy Agent - answers insurance coverage questions using a benefits PDF."""

import logging
from pathlib import Path

from PyPDF2 import PdfReader

from shared.bedrock_client import converse, extract_text

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
    f"{POLICY_TEXT}"
)


def query_policy(question: str) -> str:
    """Answer an insurance coverage question using the policy PDF."""
    logger.info("PolicyAgent query: %s", question[:120])
    messages = [{"role": "user", "content": [{"text": question}]}]
    response = converse(messages, SYSTEM_PROMPT)
    answer = extract_text(response) or "I don't know"
    logger.info("PolicyAgent response length: %d chars", len(answer))
    return answer
