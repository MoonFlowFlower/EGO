"""External adapters for explicit K0 Foundation validation only."""

from .sqlite_event_store import (
    DuplicateRecordError,
    EventStoreError,
    SequenceConflictError,
    SQLiteEventStore,
    WritesFrozenError,
)

__all__ = [
    "DuplicateRecordError",
    "EventStoreError",
    "SequenceConflictError",
    "SQLiteEventStore",
    "WritesFrozenError",
]
