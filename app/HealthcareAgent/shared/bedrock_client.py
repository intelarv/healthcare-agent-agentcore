"""Shared Amazon Bedrock Converse API client used by all agents."""

import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "anthropic.claude-sonnet-4-20250514"
DEFAULT_REGION = "us-east-1"


def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", DEFAULT_REGION),
    )


def converse(
    messages: list[dict],
    system_prompt: str,
    model_id: str | None = None,
    tools: list[dict] | None = None,
    temperature: float = 0,
    max_tokens: int = 4096,
) -> dict:
    """Call the Bedrock Converse API once."""
    client = get_bedrock_client()
    model = model_id or os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL)

    kwargs = {
        "modelId": model,
        "messages": messages,
        "system": [{"text": system_prompt}],
        "inferenceConfig": {"temperature": temperature, "maxTokens": max_tokens},
    }
    if tools:
        kwargs["toolConfig"] = {"tools": tools}

    return client.converse(**kwargs)


def extract_text(response: dict) -> str:
    """Extract the first text block from a Converse response."""
    for block in response["output"]["message"]["content"]:
        if "text" in block:
            return block["text"]
    return ""


def extract_tool_uses(response: dict) -> list[dict]:
    """Extract all toolUse blocks from a Converse response."""
    return [
        block["toolUse"]
        for block in response["output"]["message"]["content"]
        if "toolUse" in block
    ]


def converse_with_tools(
    messages: list[dict],
    system_prompt: str,
    tools: list[dict],
    tool_handler,
    model_id: str | None = None,
    temperature: float = 0,
    max_iterations: int = 10,
) -> str:
    """Run a Bedrock Converse tool-use loop."""
    for _ in range(max_iterations):
        response = converse(messages, system_prompt, model_id=model_id, tools=tools, temperature=temperature)

        stop_reason = response.get("stopReason", "")
        assistant_content = response["output"]["message"]["content"]
        messages.append({"role": "assistant", "content": assistant_content})

        if stop_reason != "tool_use":
            return extract_text(response)

        tool_results = []
        for block in assistant_content:
            if "toolUse" not in block:
                continue
            tool = block["toolUse"]
            logger.info("Tool call: %s(%s)", tool["name"], json.dumps(tool["input"], default=str)[:200])

            try:
                result = tool_handler(tool["name"], tool["input"])
            except Exception as e:
                logger.error("Tool %s failed: %s", tool["name"], e)
                result = f"Error: {e}"

            tool_results.append({
                "toolResult": {
                    "toolUseId": tool["toolUseId"],
                    "content": [{"text": str(result)}],
                }
            })

        messages.append({"role": "user", "content": tool_results})

    return extract_text(response)
