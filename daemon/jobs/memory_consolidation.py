"""Memory Consolidation Job - runs daily at 2 AM."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from daemon.scheduler import ScheduledTask
from memory.manager import get_memory_manager


async def memory_consolidation(task: ScheduledTask = None) -> dict:
    """
    Consolidate memory: cleanup expired short-term, archive daily entries.
    
    This job runs daily and:
    - Cleans expired short-term memories
    - Archives daily memory to long-term
    - Triggers reflection on past week
    """
    root = Path(__file__).parent.parent.parent
    memory = get_memory_manager(root)
    logger = logging.getLogger("job.memory_consolidation")
    
    logger.info("Starting memory consolidation")
    
    # Clean short-term
    memory.short_term_clear_expired()
    
    # Create end-of-day summary
    today = datetime.now().strftime("%Y-%m-%d")
    daily_entries = memory.daily_get(today)
    
    summary = f"Daily consolidation: {len(daily_entries)} entries processed"
    memory.long_term_append("DailyArchives", summary, source="memory_consolidation_job")
    
    logger.info("Memory consolidation complete")
    return {"status": "completed", "entries_processed": len(daily_entries)}
