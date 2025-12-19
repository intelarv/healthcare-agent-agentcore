#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
echo "==> Starting agent..."
docker compose up -d --build
echo "==> Waiting for health..."
for i in $(seq 1 30); do curl -s "http://localhost:8080/ping" >/dev/null 2>&1 && { echo "    Ready."; break; }; [[ $i -eq 30 ]] && { echo "    FAILED"; exit 1; }; sleep 2; done
echo ""
for q in "What is my copay for office visits?" "Find doctors in Houston TX" "What are the symptoms of diabetes?"; do
  echo "--- Query: $q ---"
  bash "$SCRIPT_DIR/invoke.sh" "$q" "http://localhost:8080/invocations"
  echo ""
done
echo "==> Done. Stop with: docker compose down"
