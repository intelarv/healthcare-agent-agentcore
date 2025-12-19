#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "${PROJECT_DIR}/.env" ]] && { set -a; source "${PROJECT_DIR}/.env"; set +a; }
AWS_REGION="${AWS_REGION:-us-east-1}" ROLE_NAME="${AGENTCORE_ROLE_NAME:-AgentCoreHealthcareRole}" RUNTIME_NAME="healthcare-agent"
echo "WARNING: This will delete AgentCore runtimes, ECR repos, and IAM roles."
read -rp "Continue? (y/N) " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && { echo "Aborted."; exit 0; }
RUNTIME_ID=$(aws bedrock-agentcore-control list-agent-runtimes --region "$AWS_REGION" --output text --query "agentRuntimes[?agentRuntimeName=='${RUNTIME_NAME}'].agentRuntimeId | [0]" 2>/dev/null || echo "")
[[ -n "$RUNTIME_ID" && "$RUNTIME_ID" != "None" ]] && { echo "Deleting runtime $RUNTIME_ID..."; aws bedrock-agentcore-control delete-agent-runtime --region "$AWS_REGION" --agent-runtime-id "$RUNTIME_ID" 2>/dev/null || true; } || echo "Runtime not found."
ECR_REPO="${ECR_REPO:-healthcare-agentcore/healthcare-agent}"
aws ecr delete-repository --repository-name "$ECR_REPO" --region "$AWS_REGION" --force 2>/dev/null || echo "ECR not found."
POLICIES=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --output text --query 'AttachedPolicies[].PolicyArn' 2>/dev/null || echo "")
for p in $POLICIES; do aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "$p" 2>/dev/null || true; [[ "$p" == *":policy/${ROLE_NAME}"* ]] && aws iam delete-policy --policy-arn "$p" 2>/dev/null || true; done
aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true
cd "$PROJECT_DIR" && docker compose down 2>/dev/null || true
echo "==> Cleanup complete."
