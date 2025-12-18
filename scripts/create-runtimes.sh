#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "${PROJECT_DIR}/.env" ]] && { set -a; source "${PROJECT_DIR}/.env"; set +a; }
AWS_REGION="${AWS_REGION:-us-east-1}" AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?}" ECR_REPO="${ECR_REPO:-healthcare-agentcore/healthcare-agent}"
ROLE_ARN="${AGENTCORE_ROLE_ARN:?}" SERPER_API_KEY="${SERPER_API_KEY:-}" BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-sonnet-4-20250514}"
RUNTIME_NAME="healthcare-agent" ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ENV_VARS="{\"BEDROCK_MODEL_ID\":\"${BEDROCK_MODEL_ID}\",\"AWS_REGION\":\"${AWS_REGION}\""
[[ -n "$SERPER_API_KEY" ]] && ENV_VARS="${ENV_VARS},\"SERPER_API_KEY\":\"${SERPER_API_KEY}\""
ENV_VARS="${ENV_VARS}}"
RUNTIME_ID=$(aws bedrock-agentcore-control create-agent-runtime --region "$AWS_REGION" --agent-runtime-name "$RUNTIME_NAME" --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${ECR_URI}/${ECR_REPO}:latest\"}}" --role-arn "$ROLE_ARN" --network-configuration '{"networkMode":"PUBLIC"}' --protocol-configuration '{"serverProtocol":"HTTP"}' --environment-variables "$ENV_VARS" --output text --query 'agentRuntimeId')
echo "Runtime ID: $RUNTIME_ID"
echo "Waiting for ACTIVE..." && while true; do STATUS=$(aws bedrock-agentcore-control get-agent-runtime --region "$AWS_REGION" --agent-runtime-id "$RUNTIME_ID" --output text --query 'status' 2>/dev/null || echo "CREATING"); [[ "$STATUS" == "ACTIVE" ]] && break; echo "  $STATUS..."; sleep 10; done
echo "Creating endpoint..."
ENDPOINT_ID=$(aws bedrock-agentcore-control create-agent-runtime-endpoint --region "$AWS_REGION" --agent-runtime-id "$RUNTIME_ID" --name "${RUNTIME_NAME}-endpoint" --agent-runtime-version "1" --output text --query 'agentRuntimeEndpointId' 2>/dev/null || echo "")
[[ -n "$ENDPOINT_ID" ]] && { echo "Endpoint: $ENDPOINT_ID"; while true; do EP=$(aws bedrock-agentcore-control get-agent-runtime-endpoint --region "$AWS_REGION" --agent-runtime-id "$RUNTIME_ID" --agent-runtime-endpoint-id "$ENDPOINT_ID" --output text --query 'status' 2>/dev/null || echo "CREATING"); [[ "$EP" == "ACTIVE" ]] && break; sleep 10; done; ENDPOINT_URL=$(aws bedrock-agentcore-control get-agent-runtime-endpoint --region "$AWS_REGION" --agent-runtime-id "$RUNTIME_ID" --agent-runtime-endpoint-id "$ENDPOINT_ID" --output text --query 'endpointUrl' 2>/dev/null || echo ""); }
echo ""; echo "Deployment Complete. Runtime: $RUNTIME_ID, Endpoint: ${ENDPOINT_URL:-N/A}"
