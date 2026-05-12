"""Session Indexing Job - updates session search index."""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from daemon.scheduler import ScheduledTask


async def session_indexing(task: ScheduledTask = None) -> dict:
    """
    Rebuild session search index.
    
    This job:
    - Scans all session markdown files
    - Extracts text content
    - Updates SQLite full-text search index
    """
    root = Path(__file__).parent.parent.parent
    logger = logging.getLogger("job.session_indexing")
    sessions_dir = root / "sessions"
    index_db = sessions_dir / "search.db"
    
    logger.info("Starting session indexing")
    
    # Initialize SQLite FTS database
    conn = sqlite3.connect(str(index_db))
    cursor = conn.cursor()
    
    # Create FTS table if it doesn't exist
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts 
        USING fts5(session_id, title, content, date, tokenize='porter')
    """)
    
    # Clear existing index
    cursor.execute("DELETE FROM sessions_fts")
    
    # Load sessions index
    index_path = sessions_dir / "index.json"
    if not index_path.exists():
        return {"status": "skipped", "reason": "no session index"}
    
    sessions_index = json.loads(index_path.read_text())
    count = 0
    
    for session in sessions_index.get("sessions", []):
        session_file = root / session["path"]
        if session_file.exists():
            content = session_file.read_text()
            
            # Basic extraction of conversation content
            # TODO: smarter parsing to get just messages
            
            cursor.execute(
                "INSERT INTO sessions_fts VALUES (?, ?, ?, ?)",
                (
                    session["id"],
                    session.get("title", ""),
                    content[:5000],  # Truncate for now
                    session.get("date", "")
                )
            )
            count += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"Indexed {count} sessions")
    return {"status": "completed", "sessions_indexed": count}
