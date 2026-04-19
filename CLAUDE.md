# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent healthcare system on AWS Bedrock AgentCore using the Strands Agents SDK. An orchestrator agent routes queries to three specialist agents (policy, provider, research) via HTTP, following the A2A (Agent-to-Agent) communication pattern.

## Build and Run

```bash
# Local development (Docker)
docker compose up --build

# Deploy to AWS — code deployment (no Docker)
./scripts/deploy-code.sh

# Deploy via AgentCore CLI
cd agentcore && agentcore deploy

# Test
./scripts/invoke.sh "I need help in Austin TX" http://localhost:8080/invocations

# Full test suite
./scripts/test-local.sh

# Tear down
./scripts/cleanup.sh
```

## Architecture

Each agent is a standalone AgentCore runtime in its own directory under `app/`:

- **app/HealthcareAgent/main.py**: Orchestrator. Strands Agent with `@tool`-decorated functions that HTTP POST to sub-agent `/invocations` endpoints. Per-session Agent instances maintain conversation history. Streams responses via `agent.stream_async()`.
- **app/PolicyAgent/main.py**: Strands Agent with policy PDF embedded in system prompt. No tools — pure prompt-based Q&A. Exports `query_policy()` at `/invocations`.
- **app/ProviderAgent/main.py**: Strands Agent with `@tool list_doctors` that filters `doctors.json` by state/city. Exports `find_providers()` at `/invocations`.
- **app/ResearchAgent/main.py**: Strands Agent with `@tool web_search` that calls Serper API. Exports `research_health()` at `/invocations`.

## Key Patterns

- **Strands Agent + @tool**: Each agent uses `strands.Agent` with `@tool`-decorated functions. The SDK handles the Bedrock Converse API tool-use loop automatically.
- **A2A-style HTTP**: Orchestrator calls sub-agents via `httpx.post(url, json={"message": ...})`. Sub-agent URLs configured via env vars (`POLICY_AGENT_URL`, etc.).
- **BedrockAgentCoreApp**: Each agent has its own `@app.entrypoint`. Payload format: `{"message": "..."}` → response `{"response": "...", "agent": "..."}`.
- **AgentCore config**: `agentcore/agentcore.json` defines 4 runtimes, each pointing to its `app/*/` code location.
- **Parameterized Dockerfile**: Single Dockerfile with `ARG AGENT_DIR` builds any agent. Docker-compose passes the correct `AGENT_DIR` per service.

## Environment Variables

Required: `AWS_REGION`, AWS credentials (or IAM role), `SERPER_API_KEY` (for research agent).
Optional: `BEDROCK_MODEL_ID` (default: `us.anthropic.claude-sonnet-4-20250514-v1:0`), sub-agent URLs.
