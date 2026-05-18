"""Test daemon startup and capture errors."""

import asyncio
import sys
import traceback
from pathlib import Path

# Import daemon
from daemon.daemon import Daemon

async def test():
    daemon = Daemon(root_path=Path('.'))
    try:
        # Start daemon, wait briefly, then stop
        task = asyncio.create_task(daemon.start())
        await asyncio.sleep(3)
        await daemon.shutdown()
        await task
        print("Daemon shutdown OK")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
