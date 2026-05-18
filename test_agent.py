"""Quick sanity test for agent startup."""

import asyncio
from pathlib import Path
from agents.main.agent import MainAgent

async def test():
    agent = MainAgent(Path('.'))
    await agent.start()
    print('MainAgent started OK')
    await agent.stop()
    print('MainAgent stopped OK')

if __name__ == '__main__':
    asyncio.run(test())
