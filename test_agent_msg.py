"""Test agent messaging with full diagnostics."""

import asyncio
from pathlib import Path
from daemon.supervisor import Supervisor

async def main():
    sup = Supervisor(Path('.'))
    await sup.registry.load()
    
    print("Launching agent: main")
    await sup._launch_agent("main", sup.registry.agents["main"])
    
    proc = sup.agents["main"]
    print(f"Agent PID: {proc.pid}")
    
    # Give agent time to start
    await asyncio.sleep(0.5)
    
    print(f"Agent running: {proc.returncode is None}")
    
    # Check stderr early
    stderr_data = await proc.stderr.read()
    if stderr_data:
        print(f"STDERR on startup:\n{stderr_data.decode()}")
    
    print(f"stdin transport: {proc.stdin}")
    print(f"stdout transport: {proc.stdout}")
    
    if proc.stdin is None or proc.stdout is None:
        print("ERROR: Pipes not available")
        return
    
    # Send message
    task = {"type": "user_message", "content": "Hello Custo!"}
    print(f"Sending: {task}")
    await sup._send_to_agent("main", task)
    
    # Read response with timeout
    print("Waiting for response...")
    try:
        response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=2)
        if response_line:
            print(f"Response: {response_line.decode().strip()}")
        else:
            print("Empty response line (EOF)")
    except asyncio.TimeoutError:
        print("TIMEOUT - No response")
    
    # Check stderr now
    stderr_data = await proc.stderr.read()
    if stderr_data:
        print(f"STDERR:\n{stderr_data.decode()}")
    
    # Wait for agent to exit
    await proc.wait()
    print(f"Agent exited with code: {proc.returncode}")

asyncio.run(main())
