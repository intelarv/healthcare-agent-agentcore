#!/usr/bin/env bash
set -euo pipefail
MESSAGE="${1:?Usage: invoke.sh <message> [endpoint_url]}"
ENDPOINT="${2:-http://localhost:8080/invocations}"
echo "==> POST $ENDPOINT"
echo "    Message: $MESSAGE"
echo ""
RESPONSE=$(curl -s -X POST "$ENDPOINT" -H "Content-Type: application/json" -d "{\"message\": $(printf '%s' "$MESSAGE" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
