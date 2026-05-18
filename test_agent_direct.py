"""Minimal test: just start main agent and observe."""

import asyncio
from pathlib import Path
from agents.main.agent import MainAgent

async def main():
    print("Creating agent...")
    agent = MainAgent(Path('.'))
    
    print("Starting agent...")
    await agent.start()
    
    print(f"Agent running: {agent.running}")
    print("Entering message loop in 1 second...")
    await asyncio.sleep(1)
    
    # Run message loop with a task we can cancel
    task = asyncio.create_task(agent._message_loop())
    
    print("Message loop started, waiting 2s...")
    await asyncio.sleep(2)
    
    print("Cancelling message loop...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Loop cancelled")
    
    print("Stopping agent...")
    await agent.stop()

asyncio.run(main())
