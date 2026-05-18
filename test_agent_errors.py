"""Check agent error output."""

import asyncio
from pathlib import Path
from daemon.supervisor import Supervisor

async def main():
    sup = Supervisor(Path('.'))
    await sup.registry.load()
    
    print("Launching agents...")
    for agent_type in ['main']:
        await sup._launch_agent(agent_type, sup.registry.agents[agent_type])
    
    proc = sup.agents['main']
    
    # Read stderr
    stderr_data = await proc.stderr.read()
    print(f"STDERR: {stderr_data.decode()}")
    
    stdout_data = await proc.stdout.read()
    print(f"STDOUT: {stdout_data.decode()}")
    
    print(f"Return code: {proc.returncode}")
    
    await proc.wait()

asyncio.run(main())
