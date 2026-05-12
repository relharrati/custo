# CUSTO — System Blueprint & Architecture

## Philosophy

Custo is not a chatbot.

Custo is a persistent autonomous operator that:
- remembers
- plans
- acts
- reflects
- improves

Core loop:

INPUT → UNDERSTAND → PLAN → EXECUTE → REFLECT → UPDATE MEMORY

---

## Full Architecture

```txt
/custo
│
├── system/
│   ├── config.yaml
│   ├── rules.md
│   ├── routing.md
│   ├── permissions.md
│   └── versions.md
│
├── user/
│   ├── profile.md
│   ├── preferences.md
│   ├── behavioral_patterns.md
│   ├── long_memory.md
│   ├── relationships.md
│   └── goals.md
│
├── sessions/
│   ├── daily/
│   │   ├── YYYY-MM-DD/
│   │   │   ├── session_hash.md
│   │   │   └── summary.md
│   ├── index.json
│   └── search.db
│
├── projects/
│   ├── active/
│   │   ├── project_name/
│   │   │   ├── project.md
│   │   │   ├── goals.md
│   │   │   ├── decisions.md
│   │   │   ├── todo/
│   │   │   │   ├── pending.md
│   │   │   │   ├── completed.md
│   │   │   │   └── backlog.md
│   │   │   ├── sessions/
│   │   │   ├── memory.md
│   │   │   └── assets/
│   └── archived/
│
├── memory/
│   ├── inbox/
│   ├── short_term/
│   ├── daily_memory/
│   ├── long_term/
│   │   ├── semantic.md
│   │   ├── episodic.md
│   │   ├── behavioral.md
│   │   └── compressed_memory.md
│   └── reflections/
│
├── agents/
│   ├── registry.json
│   ├── main/
│   ├── researcher/
│   ├── coder/
│   └── strategist/
│
├── skill_factory/
│   ├── templates/
│   ├── generators/
│   ├── validators/
│   └── installed/
│
├── tasks/
│   ├── today.md
│   ├── upcoming.md
│   ├── completed.md
│   ├── recurring.md
│   └── priorities.md
│
├── daemon/
│   ├── daemon.py
│   ├── supervisor.py
│   ├── scheduler.py
│   ├── heartbeat.py
│   ├── workers/
│   ├── jobs/
│   └── pid/
│
├── setup/
│   ├── install.sh
│   ├── bootstrap.py
│   ├── init_config.py
│   ├── env.example
│   ├── dependencies.txt
│   └── first_run.py
│
├── interfaces/
│   ├── terminal/
│   │   ├── cli.py
│   │   ├── commands.py
│   │   └── tui.py
│   │
│   ├── web/
│   │   ├── frontend/
│   │   ├── backend/
│   │   └── public/
│   │
│   └── gateways/
│       ├── base_gateway.py
│       ├── discord/
│       ├── whatsapp/
│       └── registry.json
│
├── integrations/
│   ├── calendar/
│   ├── email/
│   ├── notion/
│   ├── github/
│   └── future/
│
└── logs/
    ├── events.log
    ├── decisions.log
    └── errors.log
```

---

## Core Concepts

### Sessions
Sessions are raw experiences.

Each session file:
```md
<!-- title: session title -->

# Session hash
Date:
Project:

## conversation
## extracted insights
## actions
## linked memories
```

Flow:
session → extraction → memory

---

### Memory Layers

- Short-term = active context
- Daily memory = daily summaries
- Long-term semantic = facts
- Long-term episodic = events
- Behavioral = habits/preferences
- Compressed memory = abstractions

---

### Agents

All agents share:
- user/
- memory/
- projects/

Each agent has unique:
- identity/
- skills/
- selfskills/
- logs/

Agents:
- main
- researcher
- coder
- strategist

---

### Selfskills

Dynamic learned capabilities.

Flow:
observe repeated task
→ detect pattern
→ generate skill
→ validate
→ install

---

### Daemon

Background runtime:
- scheduler
- memory updates
- recurring tasks
- gateway listeners
- reflections

Workers:
- memory_worker
- task_worker
- reflection_worker
- gateway_worker

---

### Interfaces

#### Terminal
Commands:
- custo
- custo chat
- custo memory search
- custo project open

#### Web
Dashboard:
- chat
- projects
- sessions
- memory explorer
- tasks
- settings

#### Gateways
Current:
- Discord
- WhatsApp

Future:
- Telegram
- Slack
- API
- Voice

---

## Runtime Flow

User input
→ gateway/interface
→ daemon receives event
→ create session
→ route to agent
→ update project/memory/tasks
→ respond

---

## Product Positioning

Custo = autonomous digital operator

Not:
- chatbot
- assistant wrapper

Instead:
- persistent intelligence
- project continuity
- behavioral adaptation
- modular agent system
