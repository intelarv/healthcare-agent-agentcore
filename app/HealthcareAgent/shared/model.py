"""Shared Bedrock model loader for Strands agents."""

import os

from strands.models.bedrock import BedrockModel

DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"
DEFAULT_REGION = "us-east-1"


def load_model() -> BedrockModel:
    """Create a Bedrock model instance for use with Strands agents."""
    model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL)
    return BedrockModel(
        model_id=model_id,
        region_name=os.getenv("AWS_REGION", DEFAULT_REGION),
    )
