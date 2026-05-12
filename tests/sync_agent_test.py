"""Synchronous subprocess test for agent IPC."""
import subprocess
import json
import sys
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
    bufsize=0  # Unbuffered
)

print(f"[TEST] Spawned PID={proc.pid}")

# Read initial lines without blocking indefinitely
import time
start = time.time()
initial_lines = []
while time.time() - start < 3:
    # Check if there's data available to read
    # Use non-blocking approach: poll with select? For Windows use msvcrt? 
    # Simpler: readline with small timeout via communicate?
    pass

# Just read a couple of lines
line1 = proc.stdout.readline()
print(f"[TEST] Line1: {line1!r}")
line2 = proc.stdout.readline()
print(f"[TEST] Line2: {line2!r}")
line3 = proc.stdout.readline()
print(f"[TEST] Line3: {line3!r}")

print(f"[TEST] Sending task...")
task = {"type": "user_message", "content": "hello", "session_id": "test-123"}
proc.stdin.write((json.dumps(task) + "\n").encode())
proc.stdin.flush()

print("[TEST] Waiting for response...")
response_line = proc.stdout.readline()
print(f"[TEST] Response: {response_line!r}")

if response_line:
    resp = json.loads(response_line.decode().strip())
    print(f"[TEST] Parsed response: {resp}")
    assert resp.get("type") == "response"
    print("[TEST] PASS")
else:
    print("[TEST] FAIL - no response")
    # Print any stderr
    err = proc.stderr.read()
    if err:
        print(f"[TEST] Stderr: {err.decode()[:500]}")

proc.stdin.close()
proc.stdout.close()
proc.stderr.close()
proc.wait()
print(f"[TEST] Exit code: {proc.returncode}")
