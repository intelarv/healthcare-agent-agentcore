#!/usr/bin/env bash
# Deploys all agents to AgentCore using code deployment (S3 ZIP, no Docker).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "${PROJECT_DIR}/.env" ]] && { set -a; source "${PROJECT_DIR}/.env"; set +a; }
AWS_REGION="${AWS_REGION:-us-east-1}" AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?}" ROLE_ARN="${AGENTCORE_ROLE_ARN:?}"
S3_BUCKET="${AGENTCORE_CODE_BUCKET:-agentcore-healthcare-${AWS_ACCOUNT_ID}}"
aws s3 mb "s3://${S3_BUCKET}" --region "$AWS_REGION" 2>/dev/null || true

for AGENT_DIR in HealthcareAgent PolicyAgent ProviderAgent ResearchAgent; do
  echo "==> Packaging $AGENT_DIR..."
  TMPDIR=$(mktemp -d) && ZIPFILE="${TMPDIR}/${AGENT_DIR}.zip"
  cd "${PROJECT_DIR}/app/${AGENT_DIR}"
  zip -r "$ZIPFILE" . -x '**/__pycache__/*' '**/*.pyc' '**/.venv/*'
  echo "    Size: $(du -h "$ZIPFILE" | cut -f1)"
  aws s3 cp "$ZIPFILE" "s3://${S3_BUCKET}/${AGENT_DIR}/${AGENT_DIR}.zip" --region "$AWS_REGION"
  rm -rf "$TMPDIR"
  echo "    Uploaded to s3://${S3_BUCKET}/${AGENT_DIR}/"
done

echo ""
echo "==> All agents packaged and uploaded. Use 'agentcore deploy' or create runtimes manually."
