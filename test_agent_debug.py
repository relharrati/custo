"""Capture stderr from agent startup."""

import asyncio
import json
import sys
import os
from pathlib import Path

async def main():
    root = Path('.')
    agent_script = root / "agents" / "main" / "agent.py"
    
    env = dict(os.environ)
    env['PYTHONPATH'] = str(root)
    
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(agent_script),
        cwd=str(root),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    print(f"Agent PID: {proc.pid}")
    
    # Read stderr continuously in background
    stderr_data = bytearray()
    async def read_stderr():
        while True:
            chunk = await proc.stderr.read(1024)
            if not chunk:
                break
            stderr_data.extend(chunk)
    
    stderr_task = asyncio.create_task(read_stderr())
    
    # Give agent a moment to initialize
    await asyncio.sleep(0.5)
    
    # Check if stderr has anything
    if stderr_data:
        print(f"Early stderr: {stderr_data.decode()}")
    
    # Send a message
    task_msg = {"type": "user_message", "content": "Hello"}
    try:
        proc.stdin.write((json.dumps(task_msg) + "\n").encode())
        await proc.stdin.drain()
        print("Message sent")
    except Exception as e:
        print(f"Send failed: {e}")
    
    # Wait a bit for processing
    await asyncio.sleep(1)
    
    # Read whatever stdout we have
    stdout_data = await proc.stdout.read()
    print(f"STDOUT collected: {len(stdout_data)} bytes")
    if stdout_data:
        print(f"STDOUT: {stdout_data.decode()[:200]}")
    
    # Wait for process
    await proc.wait()
    
    await stderr_task
    if stderr_data:
        print(f"STDERR:\n{stderr_data.decode()}")
    print(f"Exit code: {proc.returncode}")

asyncio.run(main())
