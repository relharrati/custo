"""
Main Agent - Orchestrator

The main agent handles user interactions and delegates tasks to specialist agents.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from agents.base_agent import BaseAgent
from memory.manager import get_memory_manager
from sessions.manager import SessionManager


class MainAgent(BaseAgent):
    """Main orchestrator agent."""

    def __init__(self, root_path: Path, registry=None):
        super().__init__("main", root_path, registry)
        self.llm_provider = None  # set in start()

    async def start(self):
        """Start the main agent."""
        await super().start()
        self._init_llm_provider()
        self.log_decision("Agent started", {"component": "main"})

    def _init_llm_provider(self):
        """Initialize the configured LLM provider (if any)."""
        try:
            from system.llm import get_provider
            self.llm_provider = get_provider(root_path=self.root_path)
            self.logger.info(f"LLM provider: {self.llm_provider.provider_name} ({self.llm_provider.model_name})")
        except Exception as e:
            self.logger.warning(f"LLM provider unavailable: {e}")
            self.llm_provider = None

    async def process_task(self, task: dict) -> dict:
        """Process a task by handling internally."""
        task_type = task.get("type", "default")

        if task_type == "user_message":
            return await self._handle_user_message(task)
        elif task_type == "create_session":
            return await self._create_session(task)
        elif task_type == "reflect":
            return await self._reflect(task)
        else:
            return {"status": "unknown_task_type", "type": task_type}

    async def _handle_user_message(self, task: dict) -> dict:
        """Handle an incoming user message."""
        content = task.get("content", "")
        session_id = task.get("session_id")

        # Get or create session
        session_mgr = SessionManager(self.root_path)

        if not session_id:
            session = session_mgr.create_session()
            session_id = session["id"]
        else:
            session = session_mgr.get_session(session_id)
            if not session:
                session = session_mgr.create_session()
                session_id = session["id"]

        # Store user message in session
        session_mgr.add_message(session_id, "user", content)

        # Store in short-term memory
        memory = get_memory_manager(self.root_path)
        memory.short_term_set(f"last_user_message", content)
        memory.inbox_add({"type": "user_message", "content": content, "session_id": session_id})

        # Generate response
        response = await self._generate_response(content, session_id)

        # Store assistant message in session
        session_mgr.add_message(session_id, "assistant", response)

        # Log
        self.log_decision("User message processed", {"session_id": session_id})

        return {
            "type": "response",
            "session_id": session_id,
            "content": response,
            "timestamp": datetime.now().isoformat()
        }

    async def _generate_response(self, message: str, session_id: str) -> str:
        """Generate a response using LLM provider when available, otherwise fallback patterns."""
        message_lower = message.lower()

        # Fast-path: simple patterns handled inline (no LLM call)
        if any(w in message_lower for w in ("hello", "hi", "hey", "greetings")):
            return "Hello! I'm Custo, your autonomous digital operator. I remember, plan, act, reflect, and improve. How can I help you today?"
        if "help" in message_lower:
            return ("I can help you with:\n"
                    "- Task management and planning\n"
                    "- Memory and information retrieval\n"
                    "- Code implementation and debugging\n"
                    "- Research and documentation\n"
                    "- Project coordination")
        if "status" in message_lower:
            return f"I'm operational. Session: {session_id}. All systems running normally."
        if any(p in message_lower for p in ["who are you", "what are you", "your name"]):
            return "I'm Custo — an AI-augmented operator designed to remember, plan, act, reflect, and improve over time."

        # Check if we have a real LLM (not hardcoded bootstrap)
        from system.llm.hardcoded import HardcodedProvider
        is_hardcoded = isinstance(self.llm_provider, HardcodedProvider)

        if self.llm_provider is None or is_hardcoded:
            if is_hardcoded:
                # Let hardcoded provider give its informative fallback
                return await self.llm_provider.generate(message)
            return (f"I received: '{message}'. "
                    "(No LLM configured — set up a provider in system/config.yaml "
                    "or run `py setup/init_config.py --wizard` for guided setup.)")

        # Build prompt with system context and session memory
        prompt = self._build_llm_prompt(message, session_id)

        try:
            response = await self.llm_provider.generate(prompt)
            return response.strip() or f"I processed '{message[:50]}' (LLM returned empty)"
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return f"[LLM error: {e}] I can still help via my built-in task and memory systems."

    # -----------------------------------------------------------------------
    # LLM prompting
    # -----------------------------------------------------------------------

    def _build_llm_prompt(self, user_message: str, session_id: str) -> str:
        """Build system prompt with conversation history and memory context."""
        # Fetch recent session messages (last 6 exchanges = 12 messages)
        session_mgr = SessionManager(self.root_path)
        session = session_mgr.get_session(session_id)
        history = ""

        if session:
            # Read session markdown to extract conversation
            session_file = self.root_path / session.get("path", "")
            if session_file.exists():
                lines = session_file.read_text().splitlines()
                # Extract the conversation lines
                conv_start = 0
                for i, line in enumerate(lines):
                    if line.strip() == "## Conversation":
                        conv_start = i + 1
                        break
                if conv_start:
                    history_lines = lines[conv_start:]
                    history = "\n".join(history_lines[-20:])  # last ~20 lines

        # Short-term memory context
        memory = get_memory_manager(self.root_path)
        facts = memory.short_term_get("facts") or ""
        last_topic = memory.short_term_get("last_topic") or ""

        # Build full prompt
        system_prompt = (
            "You are Custo, an autonomous digital operator.\n"
            "Your traits:\n"
            "- Remember important details from past conversations\n"
            "- Plan actions and follow through\n"
            "- Reflect on outcomes and improve\n"
            "- Be concise, helpful, and proactive\n\n"
            f"Short-term memory / context: {facts}\n"
            f"Last topic discussed: {last_topic}\n"
        )

        if history:
            system_prompt += f"\nRecent conversation:\n{history}\n"

        system_prompt += f"\nUser: {user_message}\n\nCusto:"

        return system_prompt

    async def _create_session(self, task: dict) -> dict:
        from sessions.manager import SessionManager
        session_mgr = SessionManager(self.root_path)
        session = session_mgr.create_session(title=task.get("title"))
        return {"session_id": session["id"], "status": "created"}

    async def _reflect(self, task: dict) -> dict:
        insights = []
        return {"insights": insights, "count": len(insights)}


# Subprocess instantiates Agent class
class Agent(MainAgent):
    """Alias for subprocess entrypoint."""
    pass


if __name__ == "__main__":
    import asyncio
    from agents.base_agent import main as agent_main
    asyncio.run(agent_main())
