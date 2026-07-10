"""External SQLite implementation of only the K0 EventStorePort."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Sequence

from ego_k0_kernel.contracts import (
    AdapterCapabilityManifest,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    canonical_json_bytes,
)
from ego_k0_kernel.ports import (
    REQUIRED_DENIED_CAPABILITIES,
    assert_capability_allowed,
    validate_adapter_manifest,
)
from ego_k0_kernel.trace import TraceRow


class EventStoreError(RuntimeError):
    """Base external persistence adapter error."""


class SequenceConflictError(EventStoreError):
    """The caller's expected sequence does not match committed storage."""


class DuplicateRecordError(EventStoreError):
    """An append tried to reuse a stable record id."""


class WritesFrozenError(EventStoreError):
    """The validation freeze intervention blocks further writes."""


class AtomicStepCommitError(EventStoreError):
    """The event/trace pair failed and the transaction was rolled back."""

    committed = False


class SQLiteEventStore:
    """Caller-path SQLite adapter with append-only public persistence methods."""

    def __init__(self, database_path: str | Path) -> None:
        if database_path is None:
            raise ContractValidationError("database_path must be caller supplied")
        self.database_path = Path(database_path)
        if not self.database_path.parent.exists():
            raise ContractValidationError("database parent directory must already exist")
        self._writes_frozen = False
        self._connection = sqlite3.connect(str(self.database_path), isolation_level=None)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()
        self.manifest = validate_adapter_manifest(
            AdapterCapabilityManifest(
                adapter_id="ego_k0.sqlite_event_store.v1",
                readable_fields=("events", "trace_rows", "checkpoints"),
                writable_ports=("append_events", "append_step", "write_checkpoint"),
                forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
            )
        )

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                episode_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                schema_version TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                event_json BLOB NOT NULL,
                PRIMARY KEY (episode_id, sequence)
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT NOT NULL PRIMARY KEY,
                episode_id TEXT NOT NULL,
                last_event_sequence INTEGER NOT NULL,
                schema_version TEXT NOT NULL,
                checkpoint_hash TEXT NOT NULL,
                checkpoint_json BLOB NOT NULL,
                UNIQUE (episode_id, last_event_sequence)
            );
            CREATE INDEX IF NOT EXISTS checkpoints_episode_sequence
            ON checkpoints (episode_id, last_event_sequence DESC, checkpoint_id DESC);
            CREATE TABLE IF NOT EXISTS trace_outbox (
                episode_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                step_id INTEGER NOT NULL,
                schema_version TEXT NOT NULL,
                trace_hash TEXT NOT NULL UNIQUE,
                trace_json BLOB NOT NULL,
                PRIMARY KEY (episode_id, sequence),
                FOREIGN KEY (episode_id, sequence)
                    REFERENCES events (episode_id, sequence) ON DELETE RESTRICT
            );
            """
        )

    def __enter__(self) -> "SQLiteEventStore":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def freeze_writes(self) -> None:
        """One-way validation intervention; not part of EventStorePort."""

        self._writes_frozen = True

    def _ensure_writable(self) -> None:
        if self._writes_frozen:
            raise WritesFrozenError("event-store writes are frozen")

    def _current_sequence(self, episode_id: str) -> int:
        row = self._connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) FROM events WHERE episode_id = ?",
            (episode_id,),
        ).fetchone()
        return int(row[0])

    def _rollback_step_if_active(self) -> None:
        if self._connection.in_transaction:
            self._connection.execute("ROLLBACK")

    def append_events(
        self, expected_sequence: int, events: Sequence[EventRecord]
    ) -> int:
        assert_capability_allowed(self.manifest, "append_events")
        self._ensure_writable()
        records = tuple(events)
        if not records:
            raise ContractValidationError("append_events requires at least one event")
        if any(not isinstance(item, EventRecord) for item in records):
            raise ContractValidationError("append_events accepts only EventRecord values")
        episode_id = records[0].episode_id
        if any(item.episode_id != episode_id for item in records):
            raise ContractValidationError("one append cannot cross episode boundaries")
        expected_event_sequences = tuple(
            range(expected_sequence + 1, expected_sequence + len(records) + 1)
        )
        if tuple(item.sequence for item in records) != expected_event_sequences:
            raise SequenceConflictError("event records do not carry the expected sequence")

        try:
            self._connection.execute("BEGIN IMMEDIATE")
            current = self._current_sequence(episode_id)
            if current != expected_sequence:
                raise SequenceConflictError(
                    f"expected sequence {expected_sequence}, committed sequence is {current}"
                )
            for event in records:
                self._connection.execute(
                    """
                    INSERT INTO events (
                        episode_id, sequence, event_id, schema_version, event_hash, event_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.episode_id,
                        event.sequence,
                        event.event_id,
                        event.schema_version,
                        event.event_hash,
                        canonical_json_bytes(event),
                    ),
                )
            self._connection.execute("COMMIT")
        except SequenceConflictError:
            self._connection.execute("ROLLBACK")
            raise
        except sqlite3.IntegrityError as exc:
            self._connection.execute("ROLLBACK")
            raise DuplicateRecordError(str(exc)) from exc
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        return expected_sequence + len(records)

    def append_step(
        self,
        expected_sequence: int,
        source_event: EventRecord,
        trace_row: TraceRow,
    ) -> int:
        """Atomically append one source event and its canonical trace row."""

        assert_capability_allowed(self.manifest, "append_step")
        self._ensure_writable()
        if not isinstance(source_event, EventRecord):
            raise ContractValidationError("append_step requires one EventRecord")
        if not isinstance(trace_row, TraceRow):
            raise ContractValidationError("append_step requires one TraceRow")
        committed_sequence = expected_sequence + 1
        source_observation = source_event.payload.get("observation")
        if (
            source_event.sequence != committed_sequence
            or trace_row.episode_id != source_event.episode_id
            or trace_row.step_id != source_event.step_id
            or trace_row.event_sequence_before != expected_sequence
            or trace_row.event_sequence_after != committed_sequence
            or source_observation != trace_row.observation
        ):
            raise ContractValidationError(
                "source event and canonical trace do not describe one atomic step"
            )

        try:
            self._connection.execute("BEGIN IMMEDIATE")
            current = self._current_sequence(source_event.episode_id)
            if current != expected_sequence:
                raise SequenceConflictError(
                    f"expected sequence {expected_sequence}, committed sequence is {current}"
                )
            self._connection.execute(
                """
                INSERT INTO events (
                    episode_id, sequence, event_id, schema_version, event_hash, event_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_event.episode_id,
                    source_event.sequence,
                    source_event.event_id,
                    source_event.schema_version,
                    source_event.event_hash,
                    canonical_json_bytes(source_event),
                ),
            )
            self._connection.execute(
                """
                INSERT INTO trace_outbox (
                    episode_id, sequence, step_id, schema_version, trace_hash, trace_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_row.episode_id,
                    trace_row.event_sequence_after,
                    trace_row.step_id,
                    trace_row.schema_version,
                    trace_row.trace_hash,
                    canonical_json_bytes(trace_row.to_dict()),
                ),
            )
            self._connection.execute("COMMIT")
        except SequenceConflictError:
            self._rollback_step_if_active()
            raise
        except sqlite3.IntegrityError as exc:
            self._rollback_step_if_active()
            raise AtomicStepCommitError(str(exc)) from exc
        except Exception as exc:
            self._rollback_step_if_active()
            raise AtomicStepCommitError(str(exc)) from exc
        return committed_sequence

    def read_events(self, episode_id: str, after_sequence: int) -> tuple[EventRecord, ...]:
        assert_capability_allowed(self.manifest, "read_events")
        rows = self._connection.execute(
            """
            SELECT episode_id, sequence, event_id, schema_version, event_hash, event_json
            FROM events
            WHERE episode_id = ? AND sequence > ?
            ORDER BY sequence ASC
            """,
            (episode_id, after_sequence),
        ).fetchall()
        records = []
        for (
            row_episode_id,
            row_sequence,
            row_event_id,
            schema_version,
            event_hash,
            event_json,
        ) in rows:
            record = EventRecord.from_dict(json.loads(bytes(event_json).decode("utf-8")))
            if (
                record.episode_id != row_episode_id
                or record.sequence != row_sequence
                or record.event_id != row_event_id
                or record.schema_version != schema_version
                or record.event_hash != event_hash
            ):
                raise ContractValidationError("event metadata does not match canonical bytes")
            records.append(record)
        return tuple(records)

    def read_trace_rows(
        self, episode_id: str, after_sequence: int
    ) -> tuple[TraceRow, ...]:
        assert_capability_allowed(self.manifest, "read_trace_rows")
        rows = self._connection.execute(
            """
            SELECT episode_id, sequence, step_id, schema_version, trace_hash, trace_json
            FROM trace_outbox
            WHERE episode_id = ? AND sequence > ?
            ORDER BY sequence ASC
            """,
            (episode_id, after_sequence),
        ).fetchall()
        records = []
        for (
            row_episode_id,
            row_sequence,
            row_step_id,
            schema_version,
            trace_hash,
            trace_json,
        ) in rows:
            record = TraceRow.from_dict(json.loads(bytes(trace_json).decode("utf-8")))
            if (
                record.episode_id != row_episode_id
                or record.event_sequence_after != row_sequence
                or record.step_id != row_step_id
                or record.schema_version != schema_version
                or record.trace_hash != trace_hash
            ):
                raise ContractValidationError(
                    "trace metadata does not match canonical bytes"
                )
            records.append(record)
        return tuple(records)

    def write_checkpoint(
        self, expected_sequence: int, checkpoint: CheckpointRecord
    ) -> str:
        assert_capability_allowed(self.manifest, "write_checkpoint")
        self._ensure_writable()
        if not isinstance(checkpoint, CheckpointRecord):
            raise ContractValidationError("write_checkpoint requires CheckpointRecord")
        if checkpoint.last_event_sequence != expected_sequence:
            raise SequenceConflictError("checkpoint sequence does not match caller expectation")
        if checkpoint.state.step_id != expected_sequence:
            raise SequenceConflictError("checkpoint state step does not match event sequence")

        try:
            self._connection.execute("BEGIN IMMEDIATE")
            current = self._current_sequence(checkpoint.state.episode_id)
            if current != expected_sequence:
                raise SequenceConflictError(
                    f"expected sequence {expected_sequence}, committed sequence is {current}"
                )
            self._connection.execute(
                """
                INSERT INTO checkpoints (
                    checkpoint_id, episode_id, last_event_sequence, schema_version,
                    checkpoint_hash, checkpoint_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.state.episode_id,
                    checkpoint.last_event_sequence,
                    checkpoint.schema_version,
                    checkpoint.checkpoint_hash,
                    canonical_json_bytes(checkpoint),
                ),
            )
            self._connection.execute("COMMIT")
        except SequenceConflictError:
            self._connection.execute("ROLLBACK")
            raise
        except sqlite3.IntegrityError as exc:
            self._connection.execute("ROLLBACK")
            raise DuplicateRecordError(str(exc)) from exc
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        return checkpoint.checkpoint_id

    def read_latest_checkpoint(self, episode_id: str) -> CheckpointRecord | None:
        assert_capability_allowed(self.manifest, "read_latest_checkpoint")
        row = self._connection.execute(
            """
            SELECT checkpoint_id, episode_id, last_event_sequence, schema_version,
                   checkpoint_hash, checkpoint_json
            FROM checkpoints
            WHERE episode_id = ?
            ORDER BY last_event_sequence DESC, checkpoint_id DESC
            LIMIT 1
            """,
            (episode_id,),
        ).fetchone()
        if row is None:
            return None
        (
            row_checkpoint_id,
            row_episode_id,
            row_last_event_sequence,
            schema_version,
            checkpoint_hash,
            checkpoint_json,
        ) = row
        checkpoint = CheckpointRecord.from_dict(
            json.loads(bytes(checkpoint_json).decode("utf-8"))
        )
        if (
            checkpoint.checkpoint_id != row_checkpoint_id
            or checkpoint.state.episode_id != row_episode_id
            or checkpoint.last_event_sequence != row_last_event_sequence
            or checkpoint.schema_version != schema_version
            or checkpoint.checkpoint_hash != checkpoint_hash
        ):
            raise ContractValidationError(
                "checkpoint metadata does not match canonical bytes"
            )
        return checkpoint
