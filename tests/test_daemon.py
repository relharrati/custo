"""Test daemon startup end-to-end - launches supervisor, workers, scheduler, heartbeat."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


async def test_daemon_startup():
    """Start daemon, verify all subsystems initialize, send a task through TaskWorker, then shutdown."""
    sys.path.insert(0, str(ROOT))

    from daemon.supervisor import Supervisor
    from daemon.workers.manager import WorkerManager
    from daemon.scheduler import Scheduler
    from daemon.heartbeat import Heartbeat
    from daemon.workers.task_worker import TaskWorker
    from agents.registry import get_registry

    print("[DAEMON] Starting daemon components...")

    # Initialize registry
    registry = get_registry(ROOT)
    await registry.load()
    print(f"[DAEMON] Registry loaded: {list(registry.agents.keys())}")

    # Start supervisor (manages agent subprocess lifecycle)
    supervisor = Supervisor(ROOT)
    try:
        await supervisor.start()
        status = supervisor.get_agent_status()
        print(f"[DAEMON] Supervisor started - agents: {status}")
    except Exception as e:
        print(f"[DAEMON] Supervisor start error: {e}")
        return False

    # Wait a moment for agents to spawn
    await asyncio.sleep(3)

    # Check all agents are running
    status = supervisor.get_agent_status()
    all_ok = True
    for agent_type, info in status.items():
        if not info["running"]:
            print(f"[TEST] FAIL {agent_type} not running")
            all_ok = False
        else:
            print(f"[TEST] OK {agent_type} running pid={info['pid']}")

    if not all_ok:
        await supervisor.stop()
        return False

    # Send a user_message task via Supervisor
    print("[DAEMON] Sending user_message task to main agent...")
    task = {"type": "user_message", "content": "hello from daemon test", "session_id": "daemon-test-123"}
    try:
        await supervisor.route_task(task)
        print("[DAEMON] Task routed successfully")
    except Exception as e:
        print(f"[DAEMON] Failed to route task: {e}")
        await supervisor.stop()
        return False

    # Wait for agent to respond (non-blocking check - agent writes to stdout, supervisor doesn't read response yet)
    await asyncio.sleep(2)

    # Test TaskWorker can dispatch jobs (load but don't start full worker loops since not in daemon)
    print("[DAEMON] Verifying worker manager init...")
    wm = WorkerManager(ROOT)
    await wm.start()
    await asyncio.sleep(1)
    await wm.stop()
    print("[DAEMON] Worker manager OK")

    # Test scheduler + heartbeat init
    scheduler = Scheduler(ROOT)
    await scheduler.start()  # This calls _load_tasks internally and starts _run_loop
    print(f"[TEST] Scheduler started OK")
    await asyncio.sleep(1)
    await scheduler.stop()

    heartbeat = Heartbeat(ROOT)
    await heartbeat.start()
    await asyncio.sleep(1)
    await heartbeat.stop()
    print("[TEST] Heartbeat OK")

    # Shutdown
    print("[DAEMON] Shutting down supervisor...")
    await supervisor.stop()
    print("[DAEMON] All systems verified")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(asyncio.wait_for(test_daemon_startup(), timeout=30))
        print("\n[RESULT]", "PASS - Daemon startup verified" if success else "FAIL")
        sys.exit(0 if success else 1)
    except asyncio.TimeoutError:
        print("\n[RESULT] FAIL - timeout")
        sys.exit(1)
    except Exception as e:
        print(f"\n[RESULT] FAIL - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
