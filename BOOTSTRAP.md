# Custo Bootstrap Guide

## Quick Start (3 steps)

### Step 1: Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1  # On Windows PowerShell

# Install dependencies (requires PyYAML)
pip install pyyaml
```

### Step 2: Run First-Time Setup (includes LLM wizard)

```bash
python setup/first_run.py
```

The setup wizard will:
1. Verify installation
2. Detect your system RAM
3. Recommend appropriate LLM models from [models.dev](https://models.dev)
4. Let you pick a provider (Ollama / LM Studio / vLLM / Skip)
5. Optionally auto-download the selected model

### Step 3: Start Chatting

```bash
python custo chat
```

---

## Verifying Installation

After bootstrapping, verify core components work:

```bash
# Check version
py custo version

# Search memory (empty on first run)
py custo memory test

# List today's tasks
py custo task --today

# Show project list
py custo project list

# Run full verification suite
py tests/bootstrap_smoke.py
```

Expected: all 6 checks pass (`[OK]` status).

**Note for Windows:** The Python launcher `py` is recommended. The `custo.bat` wrapper also uses `py`.

---

## Running Custo

### Option A: Interactive Chat (TUI) - Recommended for first use

```bash
python custo chat
```

This launches an interactive terminal chat session. The TUI instantiates MainAgent directly (no daemon required for chat).

**Commands in chat:**
- `exit` / `quit` - End session
- `help` - Show help
- `history` - View conversation history  
- `new` - Start a fresh session
- Type any message to talk to Custo

### Option B: Run the Daemon (background service)

```bash
python daemon/daemon.py --foreground
```

Starts all subsystems:
- Supervisor (agent coordination)
- Task/Memory/Reflection workers
- Scheduler (recurring jobs)
- Heartbeat monitoring

The daemon listens for events and handles background operations. Use `--foreground` to see logs. **Note:** The interactive chat (`custo chat`) runs independently of the daemon.

---

## Architecture Overview

```
custo/
├── custo              # CLI entry point (Python)
├── custo.bat          # CLI entry point (Windows)
│
├── system/            # Configuration & rules
├── user/              # Profile, preferences, long-term memory
├── sessions/          # Conversation logs (daily indexed)
├── memory/            # Inbox, short-term, long-term, reflections
├── projects/          # Active & archived projects
├── agents/            # Agent implementations + registry
├── daemon/            # Background runtime
├── tasks/             # Today/upcoming/completed task lists
├── interfaces/        # CLI, web, gateway integrations
├── integrations/      # External service connectors
├── logs/              # Event, decision, error logs
├── setup/             # Install & bootstrap scripts
└── skill_factory/     # Dynamic skill generation (future)

```

## LLM Setup: Automatic Model Selection

Custo can automatically select and download a suitable LLM for you:

1. **On first run** (`setup/first_run.py`) you'll see:
   ```
   System RAM detected: ~15 GB (good)
   
   Choose an LLM provider:
     1) Ollama       — Recommended. Easy setup, auto-download
     2) LM Studio    — GUI app, loads GGUF models
     3) vLLM         — High-throughput server (GPU)
     4) Skip / hardcoded fallback
   ```

2. **Ollama path (recommended):**
   - Install from https://ollama.ai if not already installed
   - The wizard shows models matched to your RAM:
     ```
     [SMALL] Small models (2–8GB RAM)
        1) Qwen Coder 1.5B      ~1.1 GB  — Excellent code
        2) Gemma 3 1B           ~790 MB  — Fast and light
     ```
   - Confirm → model auto-downloads via `ollama pull <model>`
   - Restart Custo — connected!

3. **Without wizard (manual config):**
   Edit `system/config.yaml`:
   ```yaml
   llm:
     provider: ollama        # or "lmstudio", "vllm", "hardcoded"
     model: qwen2.5-coder:1.5b
     auto_download: true     # Ollama will pull if missing
   ```

4. **No external model?** Custo falls back to a hardcoded pattern matcher that handles greetings, help, status queries, and more.

### Models.dev Integration

Model recommendations are fetched from [anomalyco/models.dev](https://models.dev) API and filtered for:
- Local-run capable models (not API-only)
- Size appropriate for available RAM
- Families: Llama, Qwen, Gemma, Phi, Mistral, DeepSeek

To force a refresh: `MODELS_DEV_API_JSON=https://models.dev/api.json py -c "from system.llm.models_db import fetch_models; fetch_models(force_refresh=True)"`

---

## Troubleshooting

### "No module named 'yaml'"
Run: `pip install pyyaml`

### "ModuleNotFoundError" for any custo module
Make sure you're running from the `/custo` directory. The CLI and daemon add the project root to `sys.path`.

### Agent subprocess exits immediately (Windows)
This was a known issue in early builds where the agent's stdin/stdout pipe setup used an async API incompatible with Windows Proactor event loop. This is now fixed using `asyncio.to_thread` for stdin reads. Verify with:
```bash
python tests/async_agent_test.py
```

If agents fail to start, check:
- `logs/agents.log` for agent-specific errors
- `logs/decisions.log` for decision trace
- `logs/events.log` for daemon events

---

## Next Steps After Bootstrap

1. Customize `system/config.yaml` with your preferences
2. Complete your profile in `user/profile.md`
3. Set up integration tokens in `setup/env.example` (copy to `.env`)
4. Review `tasks/upcoming.md` for planned work
5. Consult `custo_architecture_blueprint.md` for full system design

---

## Key Conventions

- **Sessions**: Markdown files in `sessions/YYYY-MM-DD/`, indexed in `sessions/index.json`
- **Memory layers**:
  - `inbox/` - raw unprocessed items
  - `short_term/` - active working memory (TTL 24h)
  - `daily_memory/` - end-of-day summaries
  - `long_term/` - permanent semantic memory (`semantic.md`)
  - `reflections/` - agent-generated insights
- **Task routing**: Based on `type` field → `system/routing.py`
- **IPC**: JSON lines on stdin/stdout between daemon and agents
- **Logging**: Structured logs in `logs/` directory
