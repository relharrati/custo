"""
Web Backend - FastAPI Application

Provides HTTP API endpoints for the Custo system, wired to real sessions,
memory, agents, and daemon state.
"""

import os
import sys
import json
import time
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Add project root to path ─────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Start time for uptime ────────────────────────────────────
START_TIME = time.time()

# ── Import Custo modules ─────────────────────────────────────
try:
    from system.config import load_config
    CONFIG = load_config(ROOT)
except Exception:
    CONFIG = {}

try:
    from sessions.manager import SessionManager
    session_mgr = SessionManager(ROOT)
except Exception as e:
    print(f"[WEB] Session manager init failed: {e}")
    session_mgr = None

try:
    from memory.manager import MemoryManager
    memory_mgr = MemoryManager(ROOT)
except Exception as e:
    print(f"[WEB] Memory manager init failed: {e}")
    memory_mgr = None

try:
    from agents.registry import AgentRegistry
    agent_registry = AgentRegistry(ROOT)
    # Note: agent_registry.load() is async, called in lifespan
except Exception as e:
    print(f"[WEB] Agent registry init failed: {e}")
    agent_registry = None


# ── Pydantic Models ──────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# ── App Lifecycle ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[WEB] Custo Web UI starting on port {app.state.port}")
    print(f"[WEB] Root: {ROOT}")

    # Load agent registry
    if agent_registry:
        await agent_registry.load()
        print(f"[WEB] Agent registry loaded: {list(agent_registry.agents.keys())}")

    yield
    print("[WEB] Shutting down")


app = FastAPI(
    title="Custo Web",
    version=CONFIG.get("version", "1.0.0"),
    lifespan=lifespan,
)

app.state.port = int(os.environ.get("CUSTO_WEB_PORT", 18790))

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files & SPA ───────────────────────────────────────
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
CUSTO_UI_DIST = FRONTEND_DIR / "custo-ui" / "dist"

# Serve the built React app
if CUSTO_UI_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(CUSTO_UI_DIST / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the web UI."""
    # Try the new React app first
    index = CUSTO_UI_DIST / "index.html"
    if index.exists():
        return HTMLResponse(content=index.read_text(encoding="utf-8"))
    # Fall back to old single-file frontend
    old_index = FRONTEND_DIR / "index.html"
    if old_index.exists():
        return HTMLResponse(content=old_index.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


# Serve any other static files from dist (favicons, etc.)
if CUSTO_UI_DIST.exists():
    @app.get("/{path:path}")
    async def serve_static(path: str):
        """Serve static files from the React build."""
        file_path = CUSTO_UI_DIST / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # SPA fallback - serve index.html for client-side routing
        index = CUSTO_UI_DIST / "index.html"
        if index.exists():
            return HTMLResponse(content=index.read_text(encoding="utf-8"))
        raise HTTPException(status_code=404, detail="Not found")


# ── Health & System Info ─────────────────────────────────────
@app.get("/api/health")
async def health_check():
    """System health with real metrics."""
    uptime = time.time() - START_TIME
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)

    # Count today's sessions
    sessions_today = 0
    if session_mgr:
        try:
            sessions = session_mgr.get_today_sessions()
            sessions_today = len(sessions)
        except Exception:
            pass

    # Count memory entries
    memory_entries = 0
    if memory_mgr:
        try:
            inbox = memory_mgr.list_inbox()
            memory_entries = len(inbox) if inbox else 0
        except Exception:
            pass

    # Daemon status
    daemon_running = False
    pid_file = ROOT / "daemon" / "pid" / "custo.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process is running
            if os.name == "nt":
                import subprocess
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True
                )
                daemon_running = str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                daemon_running = True
        except Exception:
            pass

    llm_config = CONFIG.get("llm", {})

    return {
        "status": "ok",
        "service": "custo",
        "version": CONFIG.get("version", "1.0.0"),
        "uptime": f"{hours}h {minutes}m",
        "daemon_status": "Running" if daemon_running else "Stopped",
        "daemon_running": daemon_running,
        "sessions_today": sessions_today,
        "memory_entries": memory_entries,
        "active_tasks": 0,
        "llm_provider": llm_config.get("provider", "Not configured"),
        "llm_model": llm_config.get("model", "Not configured"),
        "port": app.state.port,
    }


# ── Chat ─────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to Custo and get a response."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Create or get session
    session_id = request.session_id
    if not session_id and session_mgr:
        try:
            session = session_mgr.create_session()
            session_id = session["id"]
        except Exception:
            session_id = str(uuid.uuid4())[:8]
    elif not session_id:
        session_id = str(uuid.uuid4())[:8]

    # Try to get response from daemon/agent
    response = await _process_message(request.message, session_id)

    # Save to session
    if session_mgr:
        try:
            session_mgr.add_message(session_id, "user", request.message)
            session_mgr.add_message(session_id, "assistant", response)
        except Exception:
            pass

    return ChatResponse(response=response, session_id=session_id)


async def _process_message(message: str, session_id: str) -> str:
    """Route message to the best available backend."""

    # 1. Try daemon via HTTP gateway
    gateway_config = CONFIG.get("gateway", {})
    gateway_host = gateway_config.get("bind_address", "127.0.0.1")
    gateway_port = gateway_config.get("port", 18789)

    try:
        import urllib.request
        import urllib.error

        url = f"http://{gateway_host}:{gateway_port}/api/chat"
        payload = json.dumps({"message": message, "session_id": session_id}).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("response", data.get("text", "Response received."))
    except Exception:
        pass

    # 2. Try agent registry directly (send message to main agent subprocess)
    if agent_registry:
        try:
            future = agent_registry.send_message("main", {
                "type": "user_message",
                "content": message,
                "session_id": session_id,
            })
            if future:
                result = await future
                if result and result.get("content"):
                    return result["content"]
        except Exception:
            pass

    # 3. Fallback: intelligent hardcoded response
    return _fallback_response(message)


def _fallback_response(message: str) -> str:
    """Generate a contextual fallback when no LLM is available."""
    msg = message.lower()

    if any(w in msg for w in ["hello", "hi ", "hey", "greetings"]):
        return "Hello! I'm Custo, your autonomous operator. I can help with coding, research, task management, and system operations. What would you like to work on?"

    if "help" in msg:
        return "I can help with:\n\n**Chat** — Ask questions, brainstorm ideas\n**Code** — Write, review, and debug code\n**Research** — Gather information on topics\n**Tasks** — Track and manage your work\n**Memory** — Store and retrieve context\n\nTo unlock full capabilities, configure an LLM provider with `custo setup`."

    if any(w in msg for w in ["status", "how are you", "running"]):
        return "I'm running as a web interface. For full autonomous capabilities, start the daemon with `custo daemon start`."

    if any(w in msg for w in ["code", "program", "script", "function"]):
        return "I'd love to help with code! Currently the web UI is in demo mode. Connect an LLM provider via `custo setup` for full code generation capabilities."

    return f"I received your message: \"{message}\"\n\nThe web UI is connected but no LLM provider is configured. Run `custo setup` to configure an LLM provider for full conversational capabilities."


# ── Sessions ─────────────────────────────────────────────────
@app.get("/api/sessions")
async def list_sessions():
    """List all sessions with metadata."""
    if not session_mgr:
        return {"sessions": []}

    try:
        index = session_mgr._get_index()
        sessions = index.get("sessions", [])
        return {"sessions": sessions}
    except Exception as e:
        return {"sessions": [], "error": str(e)}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session with its messages."""
    if not session_mgr:
        raise HTTPException(status_code=503, detail="Session manager unavailable")

    try:
        session = session_mgr.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if not session_mgr:
        raise HTTPException(status_code=503, detail="Session manager unavailable")

    try:
        session_mgr.delete_session(session_id)
        return {"status": "ok", "message": f"Session {session_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions")
async def create_session():
    """Create a new session."""
    if not session_mgr:
        raise HTTPException(status_code=503, detail="Session manager unavailable")

    try:
        session = session_mgr.create_session()
        return {"session_id": session["id"], "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Memory ───────────────────────────────────────────────────
@app.get("/api/memory")
async def get_memory():
    """Get memory overview."""
    if not memory_mgr:
        return {"inbox": [], "short_term": [], "total": 0}

    try:
        inbox = memory_mgr.inbox_get_pending(limit=50)
        return {
            "inbox": inbox or [],
            "short_term_count": len(inbox) if inbox else 0,
            "total": len(inbox) if inbox else 0,
        }
    except Exception as e:
        return {"inbox": [], "error": str(e)}


@app.get("/api/memory/search")
async def search_memory(q: str):
    """Search memory entries."""
    if not memory_mgr:
        return {"query": q, "results": []}

    try:
        inbox = memory_mgr.inbox_get_pending(limit=200) or []
        results = [
            item for item in inbox
            if q.lower() in json.dumps(item).lower()
        ]
        return {"query": q, "results": results, "total": len(results)}
    except Exception as e:
        return {"query": q, "results": [], "error": str(e)}


@app.post("/api/memory")
async def add_memory(entry: dict):
    """Add an entry to memory."""
    if not memory_mgr:
        raise HTTPException(status_code=503, detail="Memory manager unavailable")

    try:
        memory_mgr.inbox_add(entry)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── WebSocket Chat (Streaming) ───────────────────────────────
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()

    session_id = str(uuid.uuid4())[:8]

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                message = payload.get("message", data)
                sid = payload.get("session_id", session_id)
            except json.JSONDecodeError:
                message = data
                sid = session_id

            # Send typing indicator
            await websocket.send_json({"type": "typing"})

            # Process message
            response = await _process_message(message, sid)

            # Stream response in chunks
            chunks = _split_response(response)
            for chunk in chunks:
                await websocket.send_json({
                    "type": "chunk",
                    "text": chunk,
                    "session_id": sid,
                })
                await asyncio.sleep(0.02)

            await websocket.send_json({
                "type": "done",
                "session_id": sid,
            })

            session_id = sid

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


def _split_response(text: str, chunk_size: int = 20) -> list:
    """Split response into streaming chunks."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# ── Config ───────────────────────────────────────────────────
@app.get("/api/config")
async def get_config():
    """Get current configuration (sanitized)."""
    safe_config = {}
    for key, val in CONFIG.items():
        if key == "llm" and isinstance(val, dict):
            safe_config[key] = {
                k: ("***" if "key" in k.lower() or "secret" in k.lower() else v)
                for k, v in val.items()
            }
        else:
            safe_config[key] = val
    return safe_config


# ── Agents ───────────────────────────────────────────────────
@app.get("/api/agents")
async def list_agents():
    """Get status of all registered agents."""
    if not agent_registry:
        return {"agents": []}

    status = agent_registry.get_status()
    return {"agents": status}


# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("CUSTO_WEB_PORT", 18790))
    uvicorn.run(app, host="127.0.0.1", port=port)
