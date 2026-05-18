"""Test agent subprocess launching."""

import asyncio
from pathlib import Path
from daemon.supervisor import Supervisor

async def main():
    sup = Supervisor(Path('.'))
    await sup.registry.load()
    
    print("Launching agents...")
    for agent_type in ['main', 'researcher', 'coder', 'strategist']:
        await sup._launch_agent(agent_type, sup.registry.agents[agent_type])
    
    print(f"Running agents: {list(sup.agents.keys())}")
    
    # Wait a moment for agents to initialize
    await asyncio.sleep(1)
    
    # Send a test message to main agent
    print("\nSending test message to main agent...")
    task = {"type": "user_message", "content": "Hello Custo!"}
    
    await sup._send_to_agent("main", task)
    print("Message sent, waiting for response...")
    
    # Read response from stdout
    proc = sup.agents["main"]
    response_line = await proc.stdout.readline()
    if response_line:
        response = response_line.decode().strip()
        print(f"Response: {response}")
    else:
        print("No response received")
    
    # Give time for response
    await asyncio.sleep(1)
    
    print("\nAgent status:")
    for name, proc in sup.agents.items():
        print(f"  {name}: PID={proc.pid}, returncode={proc.returncode}")
    
    # Shutdown
    print("\nStopping agents...")
    await sup.stop()

asyncio.run(main())
