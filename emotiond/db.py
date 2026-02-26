"""
Database operations for emotiond
"""
import aiosqlite
import os
import time
from typing import Dict, Any, List
from emotiond.config import DB_PATH


async def init_db():
    """Initialize database tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Create state table (single row)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                valence REAL DEFAULT 0.0,
                arousal REAL DEFAULT 0.0,
                subjective_time INTEGER DEFAULT 0,
                last_meaningful_contact REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create relationships table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                bond REAL DEFAULT 0.0,
                grudge REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create events table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                actor TEXT NOT NULL,
                target TEXT NOT NULL,
                text TEXT,
                meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert initial state if not exists
        await db.execute("""
            INSERT OR IGNORE INTO state (id, valence, arousal, subjective_time, last_meaningful_contact)
            VALUES (1, 0.0, 0.0, 0, ?)
        """, (time.time(),))
        
        await db.commit()


async def get_state() -> Dict[str, Any]:
    """Get current emotional state"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT valence, arousal, subjective_time, last_meaningful_contact FROM state WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:
            # This should not happen as we always insert initial state
            return {"valence": 0.0, "arousal": 0.0, "subjective_time": 0, "last_meaningful_contact": time.time()}
        return {"valence": row[0], "arousal": row[1], "subjective_time": row[2], "last_meaningful_contact": row[3]}


async def update_state(valence: float, arousal: float, subjective_time: int):
    """Update emotional state"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE state SET valence = ?, arousal = ?, subjective_time = ? WHERE id = 1",
            (valence, arousal, subjective_time)
        )
        await db.commit()


async def update_meaningful_contact_time():
    """Update the last meaningful contact time to current time"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE state SET last_meaningful_contact = ? WHERE id = 1",
            (time.time(),)
        )
        await db.commit()


async def get_relationships() -> List[Dict[str, Any]]:
    """Get all relationships"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT target, bond, grudge FROM relationships")
        rows = await cursor.fetchall()
        return [{"target": row[0], "bond": row[1], "grudge": row[2]} for row in rows]


async def update_relationship(target: str, bond: float, grudge: float):
    """Update relationship for a specific target"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO relationships (target, bond, grudge) VALUES (?, ?, ?)",
            (target, bond, grudge)
        )
        await db.commit()


async def add_event(event: Dict[str, Any]):
    """Add event to events table"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO events (type, actor, target, text, meta) VALUES (?, ?, ?, ?, ?)",
            (event.get("type"), event.get("actor"), event.get("target"), 
             event.get("text"), str(event.get("meta", {})))
        )
        await db.commit()