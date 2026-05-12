"""
TUI - Text-based User Interface

Interactive terminal chat interface for Custo.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from agents.main.agent import MainAgent
from sessions.manager import SessionManager


class ChatTUI:
    """Simple text-based chat interface."""

    def __init__(self):
        self.running = False
        self.history = []
        self.session_id = None
        # G:\Custo\interfaces\terminal\tui.py -> project root is 3 levels up
        self.root = Path(__file__).parent.parent.parent
        self.agent = None

    async def run(self):
        """Run the chat loop."""
        self.running = True
        
        # Initialize main agent
        self.agent = MainAgent(self.root)
        await self.agent.start()
        
        print("=" * 60)
        print("  Custo - Autonomous Digital Operator")
        print("  Type 'exit' or 'quit' to end session")
        print("  Type 'help' for commands")
        print("=" * 60)
        print()
        
        # Create initial session
        await self._ensure_session()
        
        while self.running:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ('exit', 'quit'):
                    print("\nGoodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'history':
                    self._show_history()
                    continue
                elif user_input.lower() == 'new':
                    await self._start_new_session()
                    print(f"Started new session: {self.session_id}")
                    continue

                # Process input via main agent
                response = await self._process_message(user_input)
                print(f"\nCusto: {response}\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except EOFError:
                break
        
        await self.agent.stop()

    async def _ensure_session(self):
        """Ensure we have an active session."""
        session_mgr = SessionManager(self.root)
        today_sessions = session_mgr.get_today_sessions()
        if today_sessions:
            # Continue most recent
            self.session_id = today_sessions[0]["id"]
        else:
            session = session_mgr.create_session()
            self.session_id = session["id"]

    async def _start_new_session(self):
        """Start a fresh session."""
        session_mgr = SessionManager(self.root)
        session = session_mgr.create_session()
        self.session_id = session["id"]

    async def _process_message(self, message: str) -> str:
        """Process a user message through the main agent."""
        if not self.session_id:
            await self._ensure_session()
        
        # Build task for main agent
        task = {
            "type": "user_message",
            "content": message,
            "session_id": self.session_id
        }
        
        try:
            result = await self.agent.process_task(task)
            response = result.get("content", "")
            
            # Record in history
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "session": self.session_id,
                "user": message,
                "assistant": response
            })
            
            return response
        except Exception as e:
            return f"Error processing message: {e}"

    def _show_help(self):
        """Show available commands."""
        print("\nAvailable commands:")
        print("  exit/quit - End session")
        print("  new       - Start a fresh session")
        print("  help      - Show this help")
        print("  history   - Show conversation history")
        print("  <text>    - Send message to Custo")
        print()

    def _show_history(self):
        """Show conversation history."""
        if not self.history:
            print("\nNo conversation history yet.")
            return

        print("\nConversation History:")
        for entry in self.history[-10:]:
            print(f"  [{entry['timestamp']}] You: {entry['user']}")
            print(f"           Custo: {entry['assistant']}")
        print()


if __name__ == "__main__":
    tui = ChatTUI()
    asyncio.run(tui.run())
