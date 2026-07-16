"""Atomic SQLite command/trace store with recomputing recovery."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
from typing import Any

from .engine import (
    EngineInvariantError,
    canonical_hash,
    canonical_json,
    compute_code_path_hash,
    compute_step,
    compute_trace_hash,
)


class RecoveryError(RuntimeError):
    """Raised when persisted commands/traces cannot be independently recovered."""


@dataclass(frozen=True)
class CommitReceipt:
    committed: bool
    run_id: str
    sequence: int
    trace_hash: str | None
    error: str | None = None


@dataclass(frozen=True)
class RecoveryFrame:
    """One independently recomputed point on the durable command timeline."""

    sequence: int
    state: dict[str, Any]
    trace: dict[str, Any] | None


@dataclass(frozen=True)
class RecoveryResult:
    """Recovery output whose state and traces have one frame-derived truth."""

    run_id: str
    run_meta: dict[str, Any]
    frames: tuple[RecoveryFrame, ...]
    recovered: bool

    @property
    def state(self) -> dict[str, Any]:
        return self.frames[-1].state

    @property
    def traces(self) -> list[dict[str, Any]]:
        return [frame.trace for frame in self.frames if frame.trace is not None]

    @property
    def command_count(self) -> int:
        return len(self.frames) - 1


def default_db_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        root = Path(base) / "EgoLifePlaygroundV2"
    else:
        root = Path.home() / ".ego_life_playground_v2"
    return root / "continuity.sqlite3"


class SQLiteEventStore:
    """A run store whose only replay inputs are metadata and commands."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the connection for bounded integrity/tamper tests."""

        return self._connection

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteEventStore":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                run_meta_json TEXT NOT NULL,
                initial_state_json TEXT NOT NULL,
                initial_state_hash TEXT NOT NULL,
                code_path_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS commands (
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                command_json TEXT NOT NULL,
                command_hash TEXT NOT NULL,
                PRIMARY KEY (run_id, sequence),
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );
            CREATE TABLE IF NOT EXISTS traces (
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                trace_json TEXT NOT NULL,
                trace_hash TEXT NOT NULL,
                PRIMARY KEY (run_id, sequence),
                FOREIGN KEY (run_id, sequence) REFERENCES commands(run_id, sequence)
            );
            CREATE INDEX IF NOT EXISTS idx_commands_run_sequence
                ON commands(run_id, sequence);
            CREATE INDEX IF NOT EXISTS idx_traces_run_sequence
                ON traces(run_id, sequence);
            """
        )

    def create_run(self, run_meta: dict[str, Any], state: dict[str, Any]) -> None:
        if run_meta.get("code_path_hash") != compute_code_path_hash():
            raise EngineInvariantError("new run metadata does not match current engine bytes")
        self._connection.execute(
            "INSERT INTO runs(run_id, run_meta_json, initial_state_json, initial_state_hash, code_path_hash) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                run_meta["run_id"],
                canonical_json(run_meta),
                canonical_json(state),
                canonical_hash(state),
                run_meta["code_path_hash"],
            ),
        )

    def run_exists(self, run_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        return row is not None

    def latest_run_id(self) -> str | None:
        row = self._connection.execute(
            "SELECT run_id FROM runs ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return None if row is None else str(row["run_id"])

    def latest_compatible_run_id(self) -> str | None:
        """Return the newest run whose stored producer hash is current.

        This is used only for implicit default selection. An explicitly named
        run still enters ``recover_run`` and fails closed on any drift.
        """

        current = compute_code_path_hash()
        rows = self._connection.execute(
            "SELECT run_id, run_meta_json FROM runs WHERE code_path_hash = ? ORDER BY rowid DESC",
            (current,),
        ).fetchall()
        for row in rows:
            try:
                run_meta = _decode_json(row["run_meta_json"], "run metadata")
            except RecoveryError:
                continue
            if run_meta.get("code_path_hash") == current:
                return str(row["run_id"])
        return None

    def append_step(self, command: dict[str, Any], trace: dict[str, Any]) -> CommitReceipt:
        run_id = str(trace.get("run_id", ""))
        sequence = int(command.get("sequence", -1))
        trace_hash = trace.get("trace_hash")
        try:
            if trace.get("sequence") != sequence:
                raise EngineInvariantError("command/trace sequence mismatch")
            if trace.get("command") != command:
                raise EngineInvariantError("trace does not embed the exact command")
            if trace_hash != compute_trace_hash(trace):
                raise EngineInvariantError("trace hash mismatch before persistence")
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute(
                "INSERT INTO commands(run_id, sequence, command_json, command_hash) VALUES(?, ?, ?, ?)",
                (run_id, sequence, canonical_json(command), command["command_hash"]),
            )
            self._connection.execute(
                "INSERT INTO traces(run_id, sequence, trace_json, trace_hash) VALUES(?, ?, ?, ?)",
                (run_id, sequence, canonical_json(trace), trace_hash),
            )
            self._connection.execute("COMMIT")
            return CommitReceipt(True, run_id, sequence, str(trace_hash), None)
        except Exception as exc:  # typed, fail-closed receipt for UI commit ordering
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            return CommitReceipt(False, run_id, sequence, None, f"{type(exc).__name__}: {exc}")

    def recover_run(self, run_id: str) -> RecoveryResult:
        row = self._connection.execute(
            "SELECT run_meta_json, initial_state_json, initial_state_hash, code_path_hash "
            "FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise RecoveryError(f"unknown run: {run_id}")
        run_meta = _decode_json(row["run_meta_json"], "run metadata")
        initial = _decode_json(row["initial_state_json"], "initial state")
        if canonical_hash(initial) != row["initial_state_hash"]:
            raise RecoveryError("initial state hash mismatch")
        current_code_hash = compute_code_path_hash()
        if row["code_path_hash"] != current_code_hash or run_meta.get("code_path_hash") != current_code_hash:
            raise RecoveryError("engine code-path drift detected")

        command_rows = self._connection.execute(
            "SELECT sequence, command_json, command_hash FROM commands "
            "WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
        trace_count = int(
            self._connection.execute(
                "SELECT COUNT(*) AS count FROM traces WHERE run_id = ?", (run_id,)
            ).fetchone()["count"]
        )
        if trace_count != len(command_rows):
            raise RecoveryError("command/trace row parity mismatch")

        state = initial
        frames = [RecoveryFrame(sequence=0, state=initial, trace=None)]
        for expected_sequence, command_row in enumerate(command_rows, start=1):
            if int(command_row["sequence"]) != expected_sequence:
                raise RecoveryError("persisted command sequence is not contiguous")
            command = _decode_json(command_row["command_json"], "command")
            if command.get("command_hash") != command_row["command_hash"]:
                raise RecoveryError("persisted command column/payload hash mismatch")
            # Crucial ordering: recompute before reading the stored trace row.  The
            # stored selected_action is therefore never an input to behavior.
            try:
                recomputed = compute_step(state, command, run_meta)
            except (EngineInvariantError, KeyError, TypeError, ValueError) as exc:
                raise RecoveryError(f"command recomputation failed: {exc}") from exc

            # Build the candidate frame from recomputation before consulting
            # the stored trace.  A stored action is comparison-only and can
            # never become a replay input or timeline authority.
            recomputed_frame = RecoveryFrame(
                sequence=expected_sequence,
                state=recomputed.next_state,
                trace=recomputed.trace,
            )

            trace_row = self._connection.execute(
                "SELECT trace_json, trace_hash FROM traces WHERE run_id = ? AND sequence = ?",
                (run_id, expected_sequence),
            ).fetchone()
            if trace_row is None:
                raise RecoveryError("missing stored trace row")
            stored_trace = _decode_json(trace_row["trace_json"], "trace")
            if stored_trace.get("trace_hash") != trace_row["trace_hash"]:
                raise RecoveryError("stored trace column/payload hash mismatch")
            if compute_trace_hash(stored_trace) != trace_row["trace_hash"]:
                raise RecoveryError("stored trace content hash mismatch")
            if canonical_json(stored_trace) != canonical_json(recomputed.trace):
                raise RecoveryError("stored trace differs from independent recomputation")
            state = recomputed.next_state
            frames.append(recomputed_frame)

        return RecoveryResult(
            run_id=run_id,
            run_meta=run_meta,
            frames=tuple(frames),
            recovered=True,
        )

    def export_run(self, run_id: str, output_path: str | os.PathLike[str]) -> Path:
        """Export only after a complete recomputation; use an atomic replace."""

        recovered = self.recover_run(run_id)
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
        header = {
            "record_type": "run",
            "producer_function": "ego_life_playground_v0.store.SQLiteEventStore.export_run",
            "input_artifacts": [str(self.path)],
            "run_id": run_id,
            "seed": recovered.run_meta["seed"],
            "episode_id": recovered.state["clock"]["episode_id"],
            "aggregation_rule": "ordered_recomputed_trace_export",
            "code_path_hash": recovered.run_meta["code_path_hash"],
            "command_count": recovered.command_count,
        }
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(canonical_json(header) + "\n")
                for trace in recovered.traces:
                    handle.write(canonical_json({"record_type": "trace", "trace": trace}) + "\n")
            os.replace(temporary, output)
        finally:
            if temporary.exists():
                temporary.unlink()
        return output

    def row_counts(self, run_id: str) -> tuple[int, int]:
        commands = int(
            self._connection.execute(
                "SELECT COUNT(*) AS count FROM commands WHERE run_id = ?", (run_id,)
            ).fetchone()["count"]
        )
        traces = int(
            self._connection.execute(
                "SELECT COUNT(*) AS count FROM traces WHERE run_id = ?", (run_id,)
            ).fetchone()["count"]
        )
        return commands, traces


def _decode_json(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecoveryError(f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"{label} must be a JSON object")
    return value
