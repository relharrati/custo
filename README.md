# Custo — Autonomous Digital Operator

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-brightgreen.svg)

An AI-augmented personal operator system that remembers, plans, acts, reflects, and improves over time. Custo is a modular Python application with agent-based architecture, designed to be your autonomous digital assistant.

## ✨ Features

- **Multi-Agent Architecture** — 4 specialized agents (Main, Researcher, Coder, Strategist) working in concert
- **Intelligent Memory System** — Inbox, short-term, daily, long-term storage with reflections and learning
- **LLM Provider Flexibility** — Support for Ollama, LM Studio, vLLM, and OpenAI-compatible APIs
- **Interactive TUI Chat** — Rich terminal interface with session tracking and history
- **Daemon Runtime** — Background process with supervisor, workers, scheduler, and heartbeat
- **Comprehensive CLI** — 50+ commands for managing sessions, memory, projects, tasks, and agents
- **Cross-Platform** — Full Windows, macOS, and Linux support
- **Auto Model Selection** — Intelligent model recommendations based on system RAM
- **Session Management** — Daily markdown + JSON indexing for persistence

## 🚀 Quick Start

### Installation

Choose your preferred installation method:

#### Option 1: One-Line Install (Recommended)

**Linux / macOS:**
```bash
curl -fsSL https://github.com/relharrati/custo/raw/master/setup/install.sh | sh
```

**Windows PowerShell:**
```powershell
iwr -UseBasicParsing https://github.com/relharrati/custo/raw/master/setup/install.ps1 | iex
```

#### Option 2: NPM (Requires Python 3.9+)
```bash
npm install -g custo
npx custo chat
```

#### Option 3: Manual Setup
```bash
git clone https://github.com/relharrati/custo.git
cd custo
python -m pip install -e .
```

### First Steps

```bash
# 1. Configure your LLM provider (Ollama, LM Studio, OpenAI, etc.)
custo setup

# 2. Start interactive chat
custo chat

# 3. Check system health
custo doctor
```

## 📊 What's Working

| Component | Status | Description |
|-----------|--------|-------------|
| **Agent IPC** | ✅ | 4 agents (main, researcher, coder, strategist) run as subprocesses |
| **Daemon Runtime** | ✅ | Supervisor, workers, scheduler, and heartbeat fully operational |
| **Session Management** | ✅ | Daily markdown + JSON index with full persistence |
| **Memory System** | ✅ | Inbox, short-term, daily, long-term, and reflections |
| **CLI Commands** | ✅ | 50+ commands covering sessions, memory, projects, tasks, agents, skills, daemon, and config |
| **TUI Chat Interface** | ✅ | Interactive terminal chat with session tracking and history |
| **LLM Provider System** | ✅ | 5 backends (Hardcoded, Ollama, LM Studio, vLLM, Auto-detect) |
| **Auto Model Selection** | ✅ | RAM detection + models.dev API recommendations |
| **Windows Compatibility** | ✅ | Python 3.9+ with Proactor event loop fixes |
| **Cross-Platform Support** | ✅ | Linux, macOS, and Windows fully supported |

## 🏗️ Architecture

```
custo/
├── custo                  # Main CLI entry point
├── custo.bat              # Windows wrapper (py launcher)
├── system/
│   ├── config.py          # YAML configuration with defaults
│   ├── llm/               # LLM provider abstraction layer
│   │   ├── __init__.py         # Factory and provider selection
│   │   ├── hardcoded.py        # Bootstrap fallback provider
│   │   ├── ollama.py           # Ollama integration with auto-download
│   │   ├── openai_compat.py    # LM Studio / vLLM support
│   │   └── models_db.py        # models.dev API + caching
│   ├── rules.py           # System rules and constraints
│   ├── routing.py         # Message routing logic
│   └── versions.py        # Version management
├── agents/                # Specialist agents + registry
│   ├── base_agent.py      # Abstract base class
│   ├── main/              # Orchestrator agent
│   ├── researcher/        # Research specialist
│   ├── coder/             # Coding specialist
│   └── strategist/        # Strategy specialist
├── daemon/                # Background runtime
│   ├── daemon.py          # Main daemon process
│   ├── supervisor.py      # Agent lifecycle management
│   ├── scheduler.py       # Recurring task scheduling
│   ├── heartbeat.py       # Health monitoring
│   └── workers/           # Worker pool
├── sessions/              # Session storage
├── memory/                # Memory subsystem
├── projects/              # Project management
├── tasks/                 # Task tracking
├── interfaces/
│   ├── terminal/          # CLI + TUI chat
│   └── web/               # Web interface (upcoming)
├── integrations/          # External service integrations
├── logs/                  # Application logs
├── setup/                 # Installation & setup
│   ├── init_config.py     # Configuration wizard
│   └── first_run.py       # First-run setup
└── tests/                 # Unit and integration tests
```

## 🛠️ Configuration

### Setup Wizard

Run the interactive setup to configure your LLM provider:

```bash
custo setup
```

This will guide you through:
- LLM provider selection (Ollama, LM Studio, OpenAI, etc.)
- Model selection with RAM recommendations
- API key configuration (if applicable)
- System preferences

### Manual Configuration

Edit `~/.custo/config.yaml`:

```yaml
llm:
  provider: ollama  # or: openai, lm_studio, vllm, hardcoded
  model: neural-chat
  base_url: http://localhost:11434

agents:
  main:
    enabled: true
  researcher:
    enabled: true
  coder:
    enabled: true
  strategist:
    enabled: true
```

## 📖 CLI Commands

### Chat & Interaction
```bash
custo chat              # Start interactive chat
custo ask "question"    # Ask a single question
```

### Session Management
```bash
custo sessions list     # List all sessions
custo sessions view     # View today's session
custo sessions export   # Export sessions
```

### Memory Management
```bash
custo memory inbox      # View inbox
custo memory short      # View short-term memory
custo memory long       # View long-term memory
custo memory reflect    # Trigger reflection
```

### Daemon Control
```bash
custo daemon start      # Start background daemon
custo daemon stop       # Stop daemon
custo daemon status     # Check daemon status
```

### System Utilities
```bash
custo doctor            # Run health check
custo config show       # Display configuration
custo config reset      # Reset to defaults
```

## 🔧 Troubleshooting

### Issue: `custo: command not found`

**Solution:**
```bash
# Reinstall and add to PATH
pip install -e .
export PATH="$HOME/.local/bin:$PATH"
```

### Issue: LLM provider connection fails

**Solution:**
```bash
# Run diagnostics
custo doctor

# Check LLM provider status
custo config show
```

### Issue: Windows command not recognized

**Solution:**
- Ensure Python 3.9+ is installed
- Use PowerShell (not Command Prompt)
- Try: `python -m custo chat`

### Issue: Daemon won't start

**Solution:**
```bash
# Check logs
tail -f ~/.custo/logs/daemon.log

# Reset daemon
custo daemon stop
custo daemon start
```

## 📈 Project Status

### v1.0.0 Bootstrap ✅ Complete

The initial release delivered:

- ✅ Full package structure (14 directories, ~65 files)
- ✅ Agent subprocess IPC with Windows-compatible stdin handling
- ✅ Session and memory persistence layers
- ✅ Interactive TUI chat client
- ✅ Daemon runtime with workers and scheduler
- ✅ CLI with comprehensive command coverage
- ✅ Task and project tracking systems
- ✅ Configuration system with YAML defaults
- ✅ Bootstrap and first-run setup scripts
- ✅ Cross-platform compatibility

### Upcoming Milestones 🚀

- **v1.1.0 — Provider Integration**
  - Full Ollama / LM Studio integration
  - Model auto-download capabilities
  - Provider performance benchmarking

- **v1.2.0 — Agent Skills**
  - Skill registry system
  - Built-in skills (web search, file I/O, etc.)
  - Custom skill framework

- **v1.3.0 — Tool Execution**
  - Sandboxed tool execution
  - Shell command capabilities
  - File system integration

- **v2.0.0 — Web UI & APIs**
  - React-based web interface
  - REST API layer
  - Real-time WebSocket updates

- **v2.1.0 — Integrations**
  - Calendar integration
  - Email integration
  - Slack / Discord connectivity

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/relharrati/custo.git
cd custo
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"
pytest
```

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

- [Architecture Blueprint](custo_architecture_blueprint.md) — Detailed system design
- [Release Notes](CHANGELOG.md) — Version history and updates
- [CLI Reference](docs/cli-reference.md) — Complete command documentation
- [Agent Development Guide](docs/agent-development.md) — Building custom agents

## 🔗 Links

- **GitHub Repository** — [relharrati/custo](https://github.com/relharrati/custo)
- **Latest Release** — [v1.0.0](https://github.com/relharrati/custo/releases/tag/v1.0.0)
- **Bug Reports** — [Issues](https://github.com/relharrati/custo/issues)
- **Feature Requests** — [Discussions](https://github.com/relharrati/custo/discussions)

## 💬 Support & Community

Have questions? Need help?

- 📖 Check the [documentation](docs/)
- 🐛 Search [existing issues](https://github.com/relharrati/custo/issues)
- 💡 Start a [discussion](https://github.com/relharrati/custo/discussions)
- 📧 Open an [issue](https://github.com/relharrati/custo/issues/new)

---

**Made with ❤️ by [relharrati](https://github.com/relharrati)**

*Custo — Your Autonomous Digital Operator*
