"""Synchronous subprocess test for agent IPC - drains until JSON response."""
import subprocess
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
agent_script = ROOT / "agents" / "main" / "agent.py"

env = dict(subprocess.os.environ)
env['PYTHONPATH'] = str(ROOT)

proc = subprocess.Popen(
    [sys.executable, str(agent_script)],
    cwd=str(ROOT),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env,
    bufsize=0
)

print(f"[TEST] Spawned PID={proc.pid}", flush=True)

# Drain initial stdout lines (non-blocking-ish) for up to 5 seconds
start = time.time()
initial_lines = []
while time.time() - start < 5:
    # Check if stdout is ready to read using select-like? On Windows use msvcrt?
    # Simpler: use non-blocking reads via communicate? We'll just readline with small timeout via thread?
    # Instead, use proc.stdout.read1 or just read with a timeout using select?
    # For simplicity: use proc.stdout.read1(1024) in try/except?
    pass

# Alternative: just read lines in a loop with reasonable timeout using 'communicate' pattern not possible
# We'll just do blocking reads but with limit - they will block if no data. Use threads? That's heavy.
# Instead use asyncio in this test? Let's switch back to async but correctly parse.

# Let's instead use the async test but with proper line draining.
print("Switch to async test approach...")

import asyncio

async def async_test():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(agent_script),
        cwd=str(ROOT),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    print(f"[ASYNC] Spawned PID={proc.pid}")

    # Drain all pending stdout lines until no more immediate data (with short timeout)
    async def read_until_json():
        lines = []
        while True:
            try:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=3)
                if not line:
                    break
                decoded = line.decode(errors='replace').strip()
                print(f"[ASYNC] Got line: {decoded!r}")
                lines.append(decoded)
                if decoded.startswith('{'):
                    return decoded, lines
            except asyncio.TimeoutError:
                print("[ASYNC] Timeout waiting for more data")
                break
        return None, lines

    # Wait a moment for agent to initialize
    await asyncio.sleep(3)

    # Drain any startup lines
    json_line, all_lines = await read_until_json()
    print(f"[ASYNC] Pre-task lines: {all_lines}")

    if json_line:
        print("[ASYNC] Already got JSON (unexpected)")
        return True

    # Send task
    task = {"type": "user_message", "content": "hello", "session_id": "test-123"}
    msg = (json.dumps(task) + "\n").encode()
    proc.stdin.write(msg)
    await proc.stdin.drain()
    print("[ASYNC] Task sent")

    # Now wait for JSON response (might be after some debug lines)
    json_line, all_lines = await read_until_json()
    print(f"[ASYNC] Response lines: {all_lines}")

    if json_line:
        resp = json.loads(json_line)
        print(f"[ASYNC] Parsed: {resp}")
        assert resp.get("type") == "response"
        print("[ASYNC] PASS")
        return True
    else:
        # Dump stderr for clues
        err = await proc.stderr.read()
        print(f"[ASYNC] Stderr: {err.decode(errors='replace')[:1000]}")
        print("[ASYNC] FAIL - no JSON response")
        return False

result = asyncio.run(async_test())
sys.exit(0 if result else 1)
