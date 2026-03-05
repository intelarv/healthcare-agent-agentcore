# Healthcare Agent — AWS Bedrock AgentCore

A multi-agent healthcare system deployed on [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html) using the [Strands Agents SDK](https://strandsagents.com). Four specialized agents communicate via A2A-style HTTP to answer insurance questions, find providers, and research health conditions.

## Architecture

### Agents

| Agent | Runtime | Role | Tools |
|---|---|---|---|
| **Healthcare Orchestrator** | `app/HealthcareAgent/` | Routes queries to specialist agents | `@tool` functions that call sub-agents via HTTP |
| **Policy Agent** | `app/PolicyAgent/` | Answers insurance coverage questions | Strands Agent with policy PDF in system prompt |
| **Provider Agent** | `app/ProviderAgent/` | Finds in-network doctors | `@tool list_doctors` over `doctors.json` |
| **Research Agent** | `app/ResearchAgent/` | Provides health info with citations | `@tool web_search` via Serper API |

### How It Works

1. User sends a question to the **Healthcare Orchestrator**
2. Orchestrator's Strands Agent decides which specialist tool(s) to call
3. Each `@tool` function makes an HTTP POST to the sub-agent's `/invocations` endpoint
4. Sub-agents process the query using their own Strands Agent + specialized tools
5. Orchestrator evaluates response quality — if unsatisfactory, routes to a different agent
6. Final answer is streamed back to the user

### Technology Stack

- **[Strands Agents SDK](https://strandsagents.com)** — Agent framework with native Bedrock tool use
- **[Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)** — Managed runtime for AI agents
- **A2A-style communication** — Agents communicate via HTTP POST, following the Agent-to-Agent pattern

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials and Serper API key
```

### 2. Run with docker-compose

```bash
docker compose up --build
```

This starts all four agents. The orchestrator waits for sub-agents to be healthy.

### 3. Test

```bash
./scripts/invoke.sh "I need mental health assistance and live in Austin Texas"
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `BEDROCK_MODEL_ID` | No | `us.anthropic.claude-sonnet-4-20250514-v1:0` | Bedrock model |
| `SERPER_API_KEY` | Yes* | — | Serper API key for Research Agent |
| `POLICY_AGENT_URL` | No | `http://policy-agent:8080/invocations` | Policy Agent endpoint |
| `PROVIDER_AGENT_URL` | No | `http://provider-agent:8080/invocations` | Provider Agent endpoint |
| `RESEARCH_AGENT_URL` | No | `http://research-agent:8080/invocations` | Research Agent endpoint |

## Project Structure

```
healthcare-agent-agentcore/
├── agentcore/
│   ├── agentcore.json              # 4 runtime configs (CodeZip, Python 3.12)
│   └── aws-targets.json
├── app/
│   ├── HealthcareAgent/            # Orchestrator
│   │   ├── main.py                 # Strands Agent + @tool HTTP calls to sub-agents
│   │   └── pyproject.toml
│   ├── PolicyAgent/                # Policy specialist
│   │   ├── main.py                 # Strands Agent with PDF system prompt
│   │   ├── pyproject.toml
│   │   └── data/2026AnthemgHIPSBC.pdf
│   ├── ProviderAgent/              # Provider specialist
│   │   ├── main.py                 # Strands Agent + @tool list_doctors
│   │   ├── pyproject.toml
│   │   └── data/doctors.json
│   └── ResearchAgent/              # Research specialist
│       ├── main.py                 # Strands Agent + @tool web_search
│       └── pyproject.toml
├── scripts/                        # Deployment and testing
├── infrastructure/                 # IAM policies
├── Dockerfile                      # Parameterized (ARG AGENT_DIR)
└── docker-compose.yml              # 4 services
```

## License

Apache 2.0
