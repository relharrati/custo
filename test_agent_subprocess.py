"""Test agent via actual subprocess with pipes."""

import asyncio
import json
import sys
import os
from pathlib import Path
import subprocess

async def test_subprocess():
    """Test agent by running it as a subprocess."""
    root = Path('.')
    agent_script = root / "agents" / "main" / "agent.py"
    
    env = dict(os.environ)
    pythonpath = str(root)
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = pythonpath + (';' + existing if existing else '')
    
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
    
    # Read stderr in background
    stderr_lines = []
    async def read_stderr():
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            stderr_lines.append(line.decode().strip())
    stderr_task = asyncio.create_task(read_stderr())
    
    # Also read stdout in background
    stdout_lines = []
    async def read_stdout():
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            stdout_lines.append(line.decode().strip())
    stdout_task = asyncio.create_task(read_stdout())
    
    await asyncio.sleep(0.5)  # Let agent log
    
    # Send a message
    task_msg = {"type": "user_message", "content": "Hello from subprocess test!"}
    msg_bytes = (json.dumps(task_msg) + "\n").encode()
    print(f"Sending {len(msg_bytes)} bytes: {msg_bytes}")
    proc.stdin.write(msg_bytes)
    await proc.stdin.drain()
    print("Message sent, waiting for response...")
    
    # Wait for response or timeout
    try:
        await asyncio.wait_for(asyncio.sleep(2))
    except asyncio.TimeoutError:
        pass
    
    # Close stdin to signal end
    proc.stdin.close()
    
    # Wait for exit
    await proc.wait()
    
    # Cancel readers
    stdout_task.cancel()
    stderr_task.cancel()
    try:
        await stdout_task
    except asyncio.CancelledError:
        pass
    try:
        await stderr_task
    except asyncio.CancelledError:
        pass
    
    print(f"\nExit code: {proc.returncode}")
    
    if stdout_lines:
        print(f"STDOUT lines:")
        for line in stdout_lines:
            print(f"  {line}")
    
    if stderr_lines:
        print(f"STDERR lines:")
        for line in stderr_lines:
            print(f"  {line}")

asyncio.run(test_subprocess())
