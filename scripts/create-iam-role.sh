#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROLE_NAME="${AGENTCORE_ROLE_NAME:-AgentCoreHealthcareRole}"
echo "==> Creating IAM role: $ROLE_NAME"
aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document "file://${PROJECT_DIR}/infrastructure/trust-policy.json" --description "Role for Healthcare AgentCore runtimes" --output text --query 'Role.Arn'
POLICY_ARN=$(aws iam create-policy --policy-name "${ROLE_NAME}Policy" --policy-document "file://${PROJECT_DIR}/infrastructure/iam-policy.json" --output text --query 'Policy.Arn')
aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "$POLICY_ARN"
echo "==> IAM role created. Set AGENTCORE_ROLE_ARN in .env"
