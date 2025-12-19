#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "${PROJECT_DIR}/.env" ]] && { set -a; source "${PROJECT_DIR}/.env"; set +a; }
AWS_REGION="${AWS_REGION:-us-east-1}" AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?}" ROLE_ARN="${AGENTCORE_ROLE_ARN:?}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-sonnet-4-20250514}" SERPER_API_KEY="${SERPER_API_KEY:-}"
S3_BUCKET="${AGENTCORE_CODE_BUCKET:-agentcore-healthcare-${AWS_ACCOUNT_ID}}" RUNTIME_NAME="healthcare-agent"
echo "==> Packaging agent code..."
aws s3 mb "s3://${S3_BUCKET}" --region "$AWS_REGION" 2>/dev/null || true
TMPDIR=$(mktemp -d) && ZIPFILE="${TMPDIR}/healthcare-agent.zip"
cd "${PROJECT_DIR}/app/HealthcareAgent"
zip -r "$ZIPFILE" main.py pyproject.toml shared/ agents/ data/ -x '**/__pycache__/*' '**/*.pyc'
echo "    Size: $(du -h "$ZIPFILE" | cut -f1)"
aws s3 cp "$ZIPFILE" "s3://${S3_BUCKET}/healthcare-agent/healthcare-agent.zip" --region "$AWS_REGION"
ENV_VARS="{\"BEDROCK_MODEL_ID\":\"${BEDROCK_MODEL_ID}\",\"AWS_REGION\":\"${AWS_REGION}\""
[[ -n "$SERPER_API_KEY" ]] && ENV_VARS="${ENV_VARS},\"SERPER_API_KEY\":\"${SERPER_API_KEY}\""
ENV_VARS="${ENV_VARS}}"
RUNTIME_ID=$(aws bedrock-agentcore-control create-agent-runtime --region "$AWS_REGION" --agent-runtime-name "$RUNTIME_NAME" --agent-runtime-artifact "{\"codeConfiguration\":{\"code\":{\"s3\":{\"bucket\":\"${S3_BUCKET}\",\"prefix\":\"healthcare-agent/\"}},\"runtime\":\"PYTHON_3_12\",\"entryPoint\":[\"python\",\"main.py\"]}}" --role-arn "$ROLE_ARN" --network-configuration '{"networkMode":"PUBLIC"}' --protocol-configuration '{"serverProtocol":"HTTP"}' --environment-variables "$ENV_VARS" --output text --query 'agentRuntimeId')
echo "Runtime: $RUNTIME_ID" && rm -rf "$TMPDIR"
