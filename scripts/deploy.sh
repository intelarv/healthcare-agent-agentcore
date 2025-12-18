#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
echo "============================================"
echo "  Healthcare AgentCore - Full Deployment"
echo "============================================"
for cmd in aws docker; do command -v "$cmd" &>/dev/null || { echo "ERROR: '$cmd' required."; exit 1; }; done
[[ -f "${PROJECT_DIR}/.env" ]] || { echo "ERROR: .env not found."; exit 1; }
set -a; source "${PROJECT_DIR}/.env"; set +a
: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}" "${AWS_REGION:=us-east-1}"
echo "AWS Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION"
if [[ -z "${AGENTCORE_ROLE_ARN:-}" ]]; then
  echo "Step 1/3: Creating IAM role..."
  bash "$SCRIPT_DIR/create-iam-role.sh"
  AGENTCORE_ROLE_ARN=$(aws iam get-role --role-name "${AGENTCORE_ROLE_NAME:-AgentCoreHealthcareRole}" --output text --query 'Role.Arn')
  export AGENTCORE_ROLE_ARN
else echo "Step 1/3: IAM role: $AGENTCORE_ROLE_ARN"; fi
echo "Step 2/3: Building and pushing Docker image..."
bash "$SCRIPT_DIR/build-and-push.sh"
echo "Step 3/3: Creating AgentCore runtime..."
bash "$SCRIPT_DIR/create-runtimes.sh"
