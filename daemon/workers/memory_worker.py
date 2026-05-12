"""Memory Worker - handles memory consolidation and maintenance."""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from memory.manager import get_memory_manager


class MemoryWorker:
    """
    Memory worker handles:
    - Inbox item processing
    - Short-term TTL expiration
    - Daily memory summarization
    - Long-term compression
    - Reflection generation
    """
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.memory = get_memory_manager(root_path)
        self.running = False
        self.logger = logging.getLogger("daemon.memory_worker")
        self._consolidation_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the memory worker."""
        self.running = True
        self.logger.info("Memory worker started")
        # Run consolidation every hour
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
    
    async def stop(self):
        """Stop the memory worker."""
        self.running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Memory worker stopped")
    
    async def process_inbox(self):
        """Process pending inbox items."""
        items = self.memory.inbox_get_pending(limit=50)
        
        for item in items:
            item_id = item["id"]
            data = item["data"]
            
            try:
                # Route inbox item appropriately
                item_type = data.get("type", "generic")
                
                if item_type == "user_message":
                    # Store in short-term as conversation context
                    self.memory.short_term_set(
                        f"last_message_{data.get('user_id', 'unknown')}",
                        data.get("content", "")
                    )
                
                elif item_type == "task_result":
                    # Store task results in daily memory
                    self.memory.daily_create(
                        summary=f"Task completed: {data.get('task_type')}",
                        tags=["task", data.get("task_type")]
                    )
                
                # Mark as processed
                self.memory.inbox_mark_processed(item_id)
                self.logger.debug(f"Processed inbox item: {item_id}")
                
            except Exception as e:
                self.logger.error(f"Error processing inbox item {item_id}: {e}")
    
    async def consolidate_short_term(self):
        """Clean up expired short-term memories."""
        self.memory.short_term_clear_expired()
        self.logger.debug("Short-term cleanup complete")
    
    async def create_daily_summary(self):
        """Create end-of-day memory summary."""
        today = datetime.now().strftime("%Y-%m-%d")
        entries = self.memory.daily_get(today)
        
        if entries:
            # Aggregate today's activities
            summary = f"Daily summary for {today}: {len(entries)} events recorded."
            self.memory.long_term_append("DailySummary", summary, source="memory_worker")
            self.logger.info(f"Daily summary created: {len(entries)} entries")
    
    async def _consolidation_loop(self):
        """Periodic consolidation loop - runs every hour."""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 1 hour
                
                if not self.running:
                    break
                
                self.logger.info("Starting memory consolidation")
                
                # 1. Process inbox
                await self.process_inbox()
                
                # 2. Clean short-term
                await self.consolidate_short_term()
                
                # 3. Daily summary at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute < 5:
                    await self.create_daily_summary()
                
                self.logger.info("Memory consolidation complete")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Consolidation error: {e}")
