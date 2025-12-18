#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[[ -f "${PROJECT_DIR}/.env" ]] && { set -a; source "${PROJECT_DIR}/.env"; set +a; }
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID in .env}"
ECR_REPO="${ECR_REPO:-healthcare-agentcore/healthcare-agent}"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
echo "==> Authenticating Docker to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URI"
cd "$PROJECT_DIR"
aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION" 2>/dev/null || true
docker build -t "$ECR_REPO:latest" -f Dockerfile .
docker tag "$ECR_REPO:latest" "${ECR_URI}/${ECR_REPO}:latest"
docker push "${ECR_URI}/${ECR_REPO}:latest"
echo "==> Done. Image: ${ECR_URI}/${ECR_REPO}:latest"
