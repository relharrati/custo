"""End-to-end test: simulate a chat conversation via MainAgent directly."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


async def test_chat_flow():
    """Simulate the full custo chat flow: session creation, message exchange, response."""
    sys.path.insert(0, str(ROOT))

    from agents.main.agent import MainAgent
    from sessions.manager import SessionManager
    from memory.manager import get_memory_manager

    print("[CHAT] Creating MainAgent...")
    agent = MainAgent(ROOT)
    await agent.start()
    print(f"[CHAT] Agent started, running={agent.running}")

    # Create a session (simulating chat start)
    session_mgr = SessionManager(ROOT)
    session = session_mgr.create_session(title="Test Session")
    session_id = session["id"]
    print(f"[CHAT] Created session {session_id}")

    # Send a user message
    message = "hello, how are you?"
    print(f"[CHAT] Sending: '{message}'")
    session_mgr.add_message(session_id, "user", message)

    # Process via agent
    task = {
        "type": "user_message",
        "content": message,
        "session_id": session_id
    }
    result = await agent.process_task(task)

    print(f"[CHAT] Got result type: {result.get('type')}")
    print(f"[CHAT] Response: {result.get('content', '')[:100]}")
    print(f"[CHAT] Session ID: {result.get('session_id')}")

    # Verify response structure
    assert result.get("type") == "response", f"Expected 'response', got {result.get('type')}"
    assert "content" in result, "No content in response"
    assert result.get("session_id") == session_id, "Session mismatch"

    # Store assistant message
    assistant_content = result.get("content", "")
    session_mgr.add_message(session_id, "assistant", assistant_content)

    # Verify memory got updated
    memory = get_memory_manager(ROOT)
    last_msg = memory.short_term_get("last_user_message")
    assert last_msg == message, f"Memory mismatch: {last_msg!r} != {message!r}"
    print(f"[CHAT] Memory OK: last_user_message = '{last_msg}'")

    # Verify session file exists and has messages
    session_file = ROOT / "sessions" / "daily" / session["date"] / f"{session_id}.md"
    assert session_file.exists(), f"Session file missing: {session_file}"
    content = session_file.read_text()
    assert "You" in content and "Custo" in content, "Session file missing message blocks"
    print(f"[CHAT] Session file OK: {session_file.relative_to(ROOT)}")

    # Verify index updated
    index = session_mgr._get_index()
    found = any(s["id"] == session_id for s in index["sessions"])
    assert found, "Session not in index"
    print(f"[CHAT] Index OK: session {session_id} tracked")

    await agent.stop()
    print("[CHAT] Agent stopped")
    print("[CHAT] Full chat flow verified")
    return True


if __name__ == "__main__":
    try:
        ok = asyncio.run(asyncio.wait_for(test_chat_flow(), timeout=15))
        print("\n[RESULT]", "PASS - Chat flow OK" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    except asyncio.TimeoutError:
        print("\n[RESULT] FAIL - timeout")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n[RESULT] FAIL - assertion: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[RESULT] FAIL - {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
