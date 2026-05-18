"""Test daemon components step by step."""

import asyncio
import traceback
from pathlib import Path

from daemon.supervisor import Supervisor
from daemon.workers import WorkerManager
from daemon.scheduler import Scheduler
from daemon.heartbeat import Heartbeat

async def test_step(name, coro):
    print(f"[TEST] {name}...")
    try:
        await coro
        print(f"[TEST] OK: {name}")
    except Exception as e:
        print(f"[TEST] FAIL: {name} - {e}")
        traceback.print_exc()
        return False
    return True

async def main():
    root = Path('.')
    
    sup = Supervisor(root)
    await test_step("Load registry", sup.registry.load())
    print(f"  Agents: {list(sup.registry.agents.keys())}")
    
    wk = WorkerManager(root)
    await test_step("Start workers", wk.start())
    print(f"  Workers: {list(wk.workers.keys())}")
    
    sched = Scheduler(root)
    await test_step("Start scheduler", sched.start())
    
    hb = Heartbeat(root)
    await test_step("Start heartbeat", hb.start())
    await asyncio.sleep(1)
    print(f"  HB status: {hb.get_status()}")
    await hb.stop()

asyncio.run(main())
