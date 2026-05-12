# Custo — Autonomous Digital Operator

Custo is an AI-augmented personal operator system that remembers, plans, acts, reflects, and improves over time. Built as a modular Python application with agent-based architecture.

## Status

**Bootstrap phase complete** — core system operational. See `BOOTSTRAP.md` for setup and verification steps.

## What Works (v0.2-llm-ready)

| Component | Status | Description |
|-----------|--------|-------------|
| Agent IPC | ✅ | 4 agents (main, researcher, coder, strategist) run as subprocesses |
| Daemon | ✅ | Supervisor, workers, scheduler, heartbeat operational |
| Sessions | ✅ | Daily markdown + JSON index |
| Memory | ✅ | inbox, short-term, daily, long-term, reflections |
| CLI | ✅ | `custo chat`, `task`, `project`, `memory`, `config`, `version` |
| TUI Chat | ✅ | Interactive terminal chat with session tracking |
| LLM Provider System | ✅ | 5 backends (hardcoded, Ollama, LM Studio, vLLM, auto-detect) |
| Auto Model Selection | ✅ | RAM detection + models.dev API recommendations |
| Windows Compatibility | ✅ | Python 3.14+ Proactor fixes |

## Quick Start

```bash
# 1. Install
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install pyyaml

# 2. Run first-time setup wizard (chooses LLM provider automatically)
py setup/first_run.py

# 3. Start chat
py custo chat
```

See [BOOTSTRAP.md](BOOTSTRAP.md) for full instructions, verification tests, and troubleshooting.

## Architecture

```
custo/
├── custo              # CLI → interfaces/terminal/cli.py
├── custo.bat          # Windows wrapper (py launcher)
├── system/
│   ├── config.py      # YAML loader with defaults (includes llm section)
│   ├── llm/           # LLM provider system
│   │   ├── __init__.py    # get_provider() factory
│   │   ├── hardcoded.py   # Bootstrap fallback (pattern responses)
│   │   ├── ollama.py      # Ollama with auto-download, RAM recommendations
│   │   ├── openai_compat.py  # LM Studio / vLLM (OpenAI-compatible)
│   │   └── models_db.py   # models.dev API integration + caching
│   ├── rules.py
│   ├── routing.py
│   └── versions.py
├── agents/            # 4 specialist agents + registry (JSON IPC)
│   ├── base_agent.py  # Abstract base with Windows-safe _message_loop()
│   ├── main/          # Orchestrator — routes through LLM provider
│   ├── researcher/
│   ├── coder/
│   └── strategist/
├── daemon/            # Background runtime
│   ├── daemon.py
│   ├── supervisor.py  # Agent lifecycle + task routing
│   ├── scheduler.py   # Recurring jobs
│   ├── heartbeat.py
│   └── workers/
├── sessions/          # Daily markdown + index.json
├── memory/
├── projects/
├── tasks/
├── interfaces/
│   ├── terminal/      # TUI chat + CLI commands
│   └── web/
├── integrations/
├── logs/
├── setup/
│   ├── init_config.py   # Includes --wizard for LLM provider setup
│   └── first_run.py     # Triggers LLM wizard if no provider configured
└── tests/             # smoke + unit tests
```

## Project Status

Built from the [Custo Architecture Blueprint](custo_architecture_blueprint.md). The bootstrap phase delivered:

- Full package structure (14 dirs, ~65 files)
- Agent subprocess IPC with Windows-compatible stdin handling
- Session and memory persistence layers
- Interactive TUI chat client
- Daemon runtime with workers and scheduler
- CLI with 6 commands
- Task and project tracking markdown files
- Configuration system with YAML defaults
- Bootstrap and first-run setup scripts

**Next milestones:** provider/model integration (Ollama/LM Studio), agent skill system, tool execution sandbox, web UI, integration gateways.
