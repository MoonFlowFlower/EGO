"""
Database operations for emotiond
"""
import json
import aiosqlite
import os
import time
from typing import Dict, Any, List, Optional


def get_db_path():
    """Get database path from environment (dynamic)"""
    return os.getenv("EMOTIOND_DB_PATH", "./data/emotiond.db")


async def init_db():
    """Initialize database tables"""
    db_path = get_db_path()
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # Create state table (single row)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                valence REAL DEFAULT 0.0,
                arousal REAL DEFAULT 0.0,
                subjective_time INTEGER DEFAULT 0,
                last_meaningful_contact REAL DEFAULT 0.0,
                prediction_error REAL DEFAULT 0.0,
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
            INSERT OR IGNORE INTO state (id, valence, arousal, subjective_time, last_meaningful_contact, prediction_error)
            VALUES (1, 0.0, 0.0, 0, ?, 0.0)
        """, (time.time(),))
        
        # Add new columns if they don't exist (migration-safe)
        try:
            await db.execute("ALTER TABLE relationships ADD COLUMN trust REAL DEFAULT 0.0")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        try:
            await db.execute("ALTER TABLE relationships ADD COLUMN repair_bank REAL DEFAULT 0.0")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        try:
            await db.execute("ALTER TABLE state ADD COLUMN regulation_budget REAL DEFAULT 1.0")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise
        
        await db.commit()


async def get_state() -> Dict[str, Any]:
    """Get current emotional state"""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute("SELECT valence, arousal, subjective_time, last_meaningful_contact, prediction_error, regulation_budget FROM state WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:
            return {"valence": 0.0, "arousal": 0.0, "subjective_time": 0, "last_meaningful_contact": time.time(), "prediction_error": 0.0, "regulation_budget": 1.0}
        return {
            "valence": row[0], 
            "arousal": row[1], 
            "subjective_time": row[2], 
            "last_meaningful_contact": row[3], 
            "prediction_error": row[4],
            "regulation_budget": row[5] if len(row) > 5 else 1.0
        }


async def update_state(valence: float, arousal: float, subjective_time: int, prediction_error: float = 0.0, regulation_budget: Optional[float] = None):
    """Update emotional state"""
    async with aiosqlite.connect(get_db_path()) as db:
        if regulation_budget is not None:
            await db.execute(
                "UPDATE state SET valence = ?, arousal = ?, subjective_time = ?, prediction_error = ?, regulation_budget = ? WHERE id = 1",
                (valence, arousal, subjective_time, prediction_error, regulation_budget)
            )
        else:
            await db.execute(
                "UPDATE state SET valence = ?, arousal = ?, subjective_time = ?, prediction_error = ? WHERE id = 1",
                (valence, arousal, subjective_time, prediction_error)
            )
        await db.commit()


async def update_meaningful_contact_time():
    """Update the last meaningful contact time to current time"""
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "UPDATE state SET last_meaningful_contact = ? WHERE id = 1",
            (time.time(),)
        )
        await db.commit()


async def get_relationships() -> List[Dict[str, Any]]:
    """Get all relationships"""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute("SELECT target, bond, grudge, trust, repair_bank FROM relationships")
        rows = await cursor.fetchall()
        return [{
            "target": row[0], 
            "bond": row[1], 
            "grudge": row[2],
            "trust": row[3] if len(row) > 3 else 0.0,
            "repair_bank": row[4] if len(row) > 4 else 0.0
        } for row in rows]


async def update_relationship(target: str, bond: float, grudge: float, trust: Optional[float] = None, repair_bank: Optional[float] = None):
    """Update relationship for a specific target"""
    async with aiosqlite.connect(get_db_path()) as db:
        # Check if relationship exists and get current values
        cursor = await db.execute(
            "SELECT trust, repair_bank FROM relationships WHERE target = ?",
            (target,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            current_trust = trust if trust is not None else (existing[0] if existing[0] is not None else 0.0)
            current_repair_bank = repair_bank if repair_bank is not None else (existing[1] if existing[1] is not None else 0.0)
            await db.execute(
                "UPDATE relationships SET bond = ?, grudge = ?, trust = ?, repair_bank = ? WHERE target = ?",
                (bond, grudge, current_trust, current_repair_bank, target)
            )
        else:
            current_trust = trust if trust is not None else 0.0
            current_repair_bank = repair_bank if repair_bank is not None else 0.0
            await db.execute(
                "INSERT INTO relationships (target, bond, grudge, trust, repair_bank) VALUES (?, ?, ?, ?, ?)",
                (target, bond, grudge, current_trust, current_repair_bank)
            )
        await db.commit()


async def add_event(event: Dict[str, Any]):
    """Add event to events table"""
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "INSERT INTO events (type, actor, target, text, meta) VALUES (?, ?, ?, ?, ?)",
            (event.get("type"), event.get("actor"), event.get("target"), 
             event.get("text"), json.dumps(event.get("meta", {})))
        )
        await db.commit()


async def get_recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent events ordered by creation time"""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "SELECT type, actor, target, text, meta, created_at FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [{
            "type": row[0],
            "actor": row[1],
            "target": row[2],
            "text": row[3],
            "meta": json.loads(row[4]) if row[4] else {},
            "created_at": row[5]
        } for row in rows]


async def close_db():
    """Close any active database connections"""
    pass


async def get_events_by_target(target: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events for a specific target"""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "SELECT type, actor, target, text, meta, created_at FROM events WHERE target = ? ORDER BY id DESC LIMIT ?",
            (target, limit)
        )
        rows = await cursor.fetchall()
        return [{
            "type": row[0],
            "actor": row[1],
            "target": row[2],
            "text": row[3],
            "meta": json.loads(row[4]) if row[4] else {},
            "created_at": row[5]
        } for row in rows]


async def get_events_by_type(event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events of a specific type"""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "SELECT type, actor, target, text, meta, created_at FROM events WHERE type = ? ORDER BY id DESC LIMIT ?",
            (event_type, limit)
        )
        rows = await cursor.fetchall()
        return [{
            "type": row[0],
            "actor": row[1],
            "target": row[2],
            "text": row[3],
            "meta": json.loads(row[4]) if row[4] else {},
            "created_at": row[5]
        } for row in rows]
