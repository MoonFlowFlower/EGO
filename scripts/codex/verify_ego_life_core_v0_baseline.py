#!/usr/bin/env python3
"""Verify the immutable EGO Life Core V0 Git boundary and exported trigger.

The validator deliberately reads the frozen implementation from Git objects,
not from the six live worktree paths.  A later descendant may edit those paths
without changing the historical baseline.  The authoritative replay input is a
durable SQLite artifact: the validator loads the pinned package into a temporary
directory, recovers serialized initial state plus typed commands from a copy of
that database, re-exports through the committed store, and byte-compares JSONL.
Direct engine replay remains a supplemental cross-check.

This is local product-engineering boundary and trigger evidence only.  Product
lineage authority is established by a separate route synchronization; this
validator does not adjudicate the mechanism or grant runtime authority.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Iterator, Mapping, Sequence


SCHEMA_VERSION = "ego.life_core_v0_baseline_manifest.v1"
REPORT_SCHEMA_VERSION = "ego.life_core_v0_baseline_validation.v1"
TASK_ID = "EGO-VISIBLE-LIFE-PROXY-V0-CORE-ADOPTION-001A"
BASELINE_ID = "EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A"
EXPECTED_BASELINE_COMMIT = "546e3639299d7b11b599df3d00645666a6953bac"
EXPECTED_BASELINE_PARENT = "d5d98ac0783a7e67b6d003b460470bdf4350d4bd"
EXPECTED_BASELINE_TREE = "fe79061dca2991c822cf2b0b5547a08d9b4682f9"
EXPECTED_PATHS = (
    "labs/ego_life_playground_v0/__init__.py",
    "labs/ego_life_playground_v0/app.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/store.py",
    "scripts/run_ego_life_playground_v0.py",
    "tests/test_ego_life_playground_v0.py",
)
ENGINE_PATH = "labs/ego_life_playground_v0/engine.py"
STORE_PATH = "labs/ego_life_playground_v0/store.py"
INIT_PATH = "labs/ego_life_playground_v0/__init__.py"
MANIFEST_PRODUCER = {
    "producer_function": (
        "verify_ego_life_core_v0_baseline.build_manifest_from_git_objects"
    ),
    "input_artifacts": [f"git:commit:{EXPECTED_BASELINE_COMMIT}"],
    "aggregation_rule": (
        "exact_commit_parent_tree_change_set_and_per_blob_payload_pins"
    ),
}
EXPECTED_DEVELOPMENT_BOUNDARY = {
    "product_development_core": "ego_life_playground_v0",
    "runtime_mainline_connected": False,
    "runtime_authority": "none",
    "default_enabled": False,
    "science_weight": 0,
    "fair_baseline_disclosure": (
        "deterministic_deficit_controller_plus_cue_action_fsm_lookup"
    ),
}
CLAIM_CEILING = (
    "Immutable local Git-object boundary and replayable Ego-local product "
    "trigger for the V0 visible-life engineering candidate only; product-lineage "
    "authority comes only from separate route synchronization; no "
    "runtime-mainline or mechanism claim."
)
TRACE_HEADER_PRODUCER = (
    "ego_life_playground_v0.store.SQLiteEventStore.export_run"
)
TRACE_HEADER_AGGREGATION = "ordered_recomputed_trace_export"
TRACE_PRODUCER = "ego_life_playground_v0.engine.compute_step"
TRACE_AGGREGATION = "single_step_deterministic_one_step_argmax"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    REPO_ROOT
    / "artifacts"
    / BASELINE_ID
    / "core_baseline_manifest.json"
)
DEFAULT_TRACE = (
    REPO_ROOT
    / "artifacts"
    / BASELINE_ID
    / "core_trigger_trace.jsonl"
)


class GitObjectReadError(RuntimeError):
    """Raised when a required committed Git object cannot be read."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def _run_git(
    repo_root: Path,
    args: Sequence[str],
    *,
    command_log: list[dict[str, Any]] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if command_log is not None:
        command_log.append(
            {
                "argv": ["git", *args],
                "returncode": process.returncode,
            }
        )
    return process


def _git_bytes(
    repo_root: Path,
    args: Sequence[str],
    *,
    command_log: list[dict[str, Any]] | None = None,
) -> bytes:
    process = _run_git(repo_root, args, command_log=command_log)
    if process.returncode != 0:
        stderr = process.stderr.decode("utf-8", errors="replace").strip()
        raise GitObjectReadError(f"git {' '.join(args)} failed: {stderr}")
    return process.stdout


def _git_text(
    repo_root: Path,
    args: Sequence[str],
    *,
    command_log: list[dict[str, Any]] | None = None,
) -> str:
    return _git_bytes(repo_root, args, command_log=command_log).decode(
        "utf-8", errors="strict"
    ).strip()


def _parse_diff_tree(payload: str) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for line in payload.splitlines():
        if not line:
            continue
        status, separator, path = line.partition("\t")
        if not separator or not status or not path:
            raise GitObjectReadError(f"unparseable diff-tree record: {line!r}")
        changes.append({"status": status, "path": path})
    return changes


def _parse_ls_tree(payload: str, expected_path: str) -> dict[str, str]:
    metadata, separator, path = payload.partition("\t")
    fields = metadata.split()
    if not separator or path != expected_path or len(fields) != 3:
        raise GitObjectReadError(f"unparseable ls-tree record for {expected_path}")
    mode, object_type, blob_oid = fields
    if object_type != "blob":
        raise GitObjectReadError(
            f"expected blob at {expected_path}, observed {object_type!r}"
        )
    return {"mode": mode, "blob_oid": blob_oid}


def _inspect_commit(
    repo_root: Path,
    commit: str,
    *,
    command_log: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    commit_oid = _git_text(
        repo_root,
        ["rev-parse", "--verify", f"{commit}^{{commit}}"],
        command_log=command_log,
    )
    parent_oid = _git_text(
        repo_root,
        ["rev-parse", f"{commit_oid}^"],
        command_log=command_log,
    )
    tree_oid = _git_text(
        repo_root,
        ["rev-parse", f"{commit_oid}^{{tree}}"],
        command_log=command_log,
    )
    changes = _parse_diff_tree(
        _git_text(
            repo_root,
            [
                "-c",
                "core.quotePath=false",
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-status",
                "--no-renames",
                "-r",
                commit_oid,
            ],
            command_log=command_log,
        )
    )
    files: list[dict[str, Any]] = []
    for change in sorted(changes, key=lambda item: item["path"]):
        path = change["path"]
        object_spec = f"{commit_oid}:{path}"
        tree_entry = _parse_ls_tree(
            _git_text(
                repo_root,
                ["-c", "core.quotePath=false", "ls-tree", "--full-tree", commit_oid, "--", path],
                command_log=command_log,
            ),
            path,
        )
        rev_parse_blob = _git_text(
            repo_root,
            ["rev-parse", object_spec],
            command_log=command_log,
        )
        if rev_parse_blob != tree_entry["blob_oid"]:
            raise GitObjectReadError(f"rev-parse/ls-tree blob disagreement: {path}")
        payload = _git_bytes(
            repo_root,
            ["cat-file", "blob", object_spec],
            command_log=command_log,
        )
        declared_size = int(
            _git_text(
                repo_root,
                ["cat-file", "-s", object_spec],
                command_log=command_log,
            )
        )
        if declared_size != len(payload):
            raise GitObjectReadError(f"cat-file size/payload disagreement: {path}")
        files.append(
            {
                "path": path,
                "mode": tree_entry["mode"],
                "blob_oid": tree_entry["blob_oid"],
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return {
        "commit_oid": commit_oid,
        "parent_oid": parent_oid,
        "tree_oid": tree_oid,
        "required_change_status": "A",
        "expected_change_count": len(changes),
        "changes": sorted(changes, key=lambda item: item["path"]),
        "files": files,
    }


def build_manifest_from_git_objects(
    *,
    repo_root: Path,
    baseline_commit: str = EXPECTED_BASELINE_COMMIT,
) -> dict[str, Any]:
    """Build the frozen manifest only from the authorized committed boundary."""

    repo_root = Path(repo_root).resolve()
    if baseline_commit != EXPECTED_BASELINE_COMMIT:
        raise ValueError("baseline commit differs from the operator-authorized pin")
    source = _inspect_commit(repo_root, baseline_commit)
    expected_changes = [
        {"status": "A", "path": path} for path in EXPECTED_PATHS
    ]
    if source["commit_oid"] != EXPECTED_BASELINE_COMMIT:
        raise GitObjectReadError("baseline commit object does not match the frozen commit")
    if source["parent_oid"] != EXPECTED_BASELINE_PARENT:
        raise GitObjectReadError("baseline parent does not match the frozen parent")
    if source["tree_oid"] != EXPECTED_BASELINE_TREE:
        raise GitObjectReadError("baseline tree does not match the frozen tree")
    if source["changes"] != expected_changes:
        raise GitObjectReadError("baseline commit is not the exact six-file addition")
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "baseline_id": BASELINE_ID,
        "producer": dict(MANIFEST_PRODUCER),
        "source": source,
        "development_boundary": dict(EXPECTED_DEVELOPMENT_BOUNDARY),
        "claim_ceiling": CLAIM_CEILING,
    }


@contextmanager
def _committed_package_modules(
    payloads: Mapping[str, bytes],
) -> Iterator[tuple[ModuleType, ModuleType, Path]]:
    init_payload = payloads.get(INIT_PATH)
    engine_payload = payloads.get(ENGINE_PATH)
    store_payload = payloads.get(STORE_PATH)
    if init_payload is None or engine_payload is None or store_payload is None:
        raise GitObjectReadError("committed package payloads are unavailable")
    with tempfile.TemporaryDirectory(prefix="ego_life_core_v0_replay_") as directory:
        root = Path(directory)
        payload_hash = hashlib.sha256(
            init_payload + engine_payload + store_payload
        ).hexdigest()[:12]
        package_name = f"_ego_life_core_v0_{payload_hash}"
        package_root = root / package_name
        package_root.mkdir()
        init_path = package_root / "__init__.py"
        engine_path = package_root / "engine.py"
        store_path = package_root / "store.py"
        init_path.write_bytes(init_payload)
        engine_path.write_bytes(engine_payload)
        store_path.write_bytes(store_payload)
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            init_path,
            submodule_search_locations=[str(package_root)],
        )
        if package_spec is None or package_spec.loader is None:
            raise RuntimeError("cannot load committed baseline package")
        package_module = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package_module
        try:
            package_spec.loader.exec_module(package_module)
            engine_module = sys.modules[f"{package_name}.engine"]
            store_spec = importlib.util.spec_from_file_location(
                f"{package_name}.store",
                store_path,
            )
            if store_spec is None or store_spec.loader is None:
                raise RuntimeError("cannot load committed baseline store")
            store_module = importlib.util.module_from_spec(store_spec)
            sys.modules[store_spec.name] = store_module
            store_spec.loader.exec_module(store_module)
            yield engine_module, store_module, root
        finally:
            for module_name in list(sys.modules):
                if module_name == package_name or module_name.startswith(package_name + "."):
                    sys.modules.pop(module_name, None)


def _load_committed_payloads(
    repo_root: Path,
    source: Mapping[str, Any],
    *,
    command_log: list[dict[str, Any]],
) -> dict[str, bytes]:
    commit = str(source["commit_oid"])
    payloads: dict[str, bytes] = {}
    for entry in source["files"]:
        path = str(entry["path"])
        payloads[path] = _git_bytes(
            repo_root,
            ["cat-file", "blob", f"{commit}:{path}"],
            command_log=command_log,
        )
    return payloads


def _validate_trace(
    trace_bytes: bytes,
    *,
    trace_path: str,
    database_bytes: bytes,
    database_path: str,
    committed_payloads: Mapping[str, bytes],
    add_error,
) -> dict[str, Any]:
    trace_sha256 = hashlib.sha256(trace_bytes).hexdigest()
    database_sha256 = hashlib.sha256(database_bytes).hexdigest()
    resolved_database_path = str(Path(database_path).resolve())
    validation_errors: list[str] = []
    direct_replay_errors: list[str] = []
    database_provenance_status = "FAIL"
    sqlite_recovery_status = "FAIL"
    sqlite_export_status = "FAIL"
    serialized_initial_state_status = "FAIL"
    replay_input = "serialized_initial_state_and_typed_commands_from_sqlite_artifact"

    def fail(
        code: str,
        message: str,
        *,
        expected: Any = None,
        actual: Any = None,
        replay: bool = False,
        blocks_replay: bool = False,
    ) -> None:
        add_error(code, message, expected=expected, actual=actual)
        (direct_replay_errors if replay else validation_errors).append(code)
        if blocks_replay and code not in direct_replay_errors:
            direct_replay_errors.append(code)

    def result(
        *,
        header: Mapping[str, Any] | None,
        record_count: int,
        trace_validation_status: str,
        direct_engine_replay_status: str,
    ) -> dict[str, Any]:
        return {
            "trace_payload_sha256": trace_sha256,
            "trace_path": trace_path,
            "trace_header": header,
            "trace_record_count": record_count,
            "trace_validation_status": trace_validation_status,
            "database_path": resolved_database_path,
            "database_payload_sha256": database_sha256,
            "database_provenance_status": database_provenance_status,
            "sqlite_recovery_status": sqlite_recovery_status,
            "sqlite_export_status": sqlite_export_status,
            "serialized_initial_state_status": serialized_initial_state_status,
            "direct_engine_replay_status": direct_engine_replay_status,
            "trace_replay_status": (
                "PASS"
                if sqlite_recovery_status == "PASS" and sqlite_export_status == "PASS"
                else "FAIL"
            ),
            "trace_replay_input": replay_input,
        }

    try:
        text = trace_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        fail("trace_utf8_invalid", str(exc))
        return result(
            header=None,
            record_count=0,
            trace_validation_status="FAIL",
            direct_engine_replay_status="FAIL",
        )

    records: list[Any] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            fail(
                "trace_blank_record",
                "trace contains an empty JSONL record",
                actual=line_number,
                blocks_replay=True,
            )
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            fail(
                "trace_json_invalid",
                "trace contains invalid JSON",
                actual={"line": line_number, "error": str(exc)},
                blocks_replay=True,
            )
    if not records:
        fail("trace_records_missing", "trace contains no records")
        return result(
            header=None,
            record_count=0,
            trace_validation_status="FAIL",
            direct_engine_replay_status="FAIL",
        )

    header = records[0] if isinstance(records[0], dict) else {}
    trace_records = records[1:]
    expected_header_keys = {
        "record_type",
        "producer_function",
        "input_artifacts",
        "run_id",
        "seed",
        "episode_id",
        "aggregation_rule",
        "code_path_hash",
        "command_count",
    }
    if set(header) != expected_header_keys:
        fail(
            "trace_header_schema_mismatch",
            "trace run header keys differ from the committed export contract",
            expected=sorted(expected_header_keys),
            actual=sorted(header),
        )
    if header.get("record_type") != "run":
        fail("trace_header_record_type_mismatch", "first record is not a run header")
    if header.get("producer_function") != TRACE_HEADER_PRODUCER:
        fail(
            "trace_header_producer_mismatch",
            "trace header producer_function is not the committed exporter",
            expected=TRACE_HEADER_PRODUCER,
            actual=header.get("producer_function"),
        )
    input_artifacts = header.get("input_artifacts")
    if not (
        isinstance(input_artifacts, list)
        and input_artifacts
        and all(isinstance(item, str) and item for item in input_artifacts)
    ):
        fail("trace_header_input_artifacts_invalid", "trace input_artifacts are invalid")
    if input_artifacts != [resolved_database_path]:
        fail(
            "trace_header_database_provenance_mismatch",
            "trace header does not name the authoritative durable SQLite artifact",
            expected=[resolved_database_path],
            actual=input_artifacts,
        )
    else:
        database_provenance_status = "PASS"
    run_id = header.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        fail("trace_header_run_id_invalid", "trace run_id must be a non-empty string")
    seed = header.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        fail("trace_header_seed_invalid", "trace seed must be an integer")
    episode_id = header.get("episode_id")
    if not isinstance(episode_id, str) or not episode_id:
        fail("trace_header_episode_id_invalid", "trace episode_id must be non-empty")
    if header.get("aggregation_rule") != TRACE_HEADER_AGGREGATION:
        fail(
            "trace_header_aggregation_rule_mismatch",
            "trace header aggregation rule differs from the committed exporter",
            expected=TRACE_HEADER_AGGREGATION,
            actual=header.get("aggregation_rule"),
        )
    command_count = header.get("command_count")
    if (
        isinstance(command_count, bool)
        or not isinstance(command_count, int)
        or command_count <= 0
        or command_count != len(trace_records)
    ):
        fail(
            "trace_header_command_count_mismatch",
            "trace command_count must be positive and equal the trace-record count",
            expected=len(trace_records),
            actual=command_count,
        )

    with _committed_package_modules(committed_payloads) as (
        engine,
        store_module,
        temporary_root,
    ):
        expected_code_path_hash = engine.compute_code_path_hash()
        if header.get("code_path_hash") != expected_code_path_hash:
            fail(
                "trace_header_code_path_hash_mismatch",
                "trace code_path_hash differs from committed engine/store payloads",
                expected=expected_code_path_hash,
                actual=header.get("code_path_hash"),
            )

        database_copy = temporary_root / "database-copy.sqlite3"
        database_copy.write_bytes(database_bytes)
        store = None
        recovered = None
        try:
            store = store_module.SQLiteEventStore(database_copy)
            run_rows = store.connection.execute(
                "SELECT run_id FROM runs ORDER BY run_id"
            ).fetchall()
            database_run_ids = [str(row["run_id"]) for row in run_rows]
            if len(database_run_ids) != 1:
                fail(
                    "database_run_inventory_mismatch",
                    "authoritative database must contain exactly one run",
                    expected=1,
                    actual=database_run_ids,
                )
            else:
                database_run_id = database_run_ids[0]
                if run_id != database_run_id:
                    fail(
                        "database_trace_run_id_mismatch",
                        "trace run_id differs from the sole authoritative database run",
                        expected=database_run_id,
                        actual=run_id,
                    )
                try:
                    recovered = store.recover_run(database_run_id)
                    sqlite_recovery_status = "PASS"
                    serialized_initial_state_status = "PASS"
                except Exception as exc:
                    fail(
                        "sqlite_recovery_failed",
                        "committed SQLiteEventStore.recover_run rejected the database copy",
                        actual=f"{type(exc).__name__}: {exc}",
                    )
        except Exception as exc:
            fail(
                "sqlite_recovery_failed",
                "committed SQLiteEventStore could not open the database copy",
                actual=f"{type(exc).__name__}: {exc}",
            )

        if recovered is not None and store is not None:
            expected_run_metadata = {
                "run_id": run_id,
                "seed": seed,
                "episode_id": episode_id,
                "producer_function": TRACE_PRODUCER,
                "aggregation_rule": TRACE_AGGREGATION,
                "code_path_hash": expected_code_path_hash,
                "science_weight": 0,
            }
            for field, expected_value in expected_run_metadata.items():
                actual_value = recovered.run_meta.get(field)
                if actual_value != expected_value or type(actual_value) is not type(
                    expected_value
                ):
                    fail(
                        f"database_run_metadata_mismatch:{field}",
                        "serialized run metadata differs from trace/committed contract",
                        expected=expected_value,
                        actual=actual_value,
                    )
            if recovered.command_count != len(trace_records):
                fail(
                    "database_command_count_mismatch",
                    "recovered typed-command count differs from trace records",
                    expected=len(trace_records),
                    actual=recovered.command_count,
                )
            try:
                # Recovery/export operate on the copied bytes.  Rebinding only the
                # provenance label makes the committed exporter name the durable
                # source artifact rather than the ephemeral validation copy.
                store.path = Path(resolved_database_path)
                exported_path = store.export_run(
                    recovered.run_id,
                    temporary_root / "committed-reexport.jsonl",
                )
                exported_bytes = exported_path.read_bytes()
                if exported_bytes == trace_bytes:
                    sqlite_export_status = "PASS"
                else:
                    fail(
                        "sqlite_export_trace_mismatch",
                        "committed export from recovered SQLite bytes is not byte-identical to trace",
                        expected=hashlib.sha256(exported_bytes).hexdigest(),
                        actual=trace_sha256,
                    )
            except Exception as exc:
                fail(
                    "sqlite_export_failed",
                    "committed SQLiteEventStore.export_run failed after recovery",
                    actual=f"{type(exc).__name__}: {exc}",
                )

        run_meta = {
            "run_id": run_id,
            "seed": seed,
            "episode_id": episode_id,
            "producer_function": TRACE_PRODUCER,
            "aggregation_rule": TRACE_AGGREGATION,
            "code_path_hash": expected_code_path_hash,
            "science_weight": 0,
        }
        state = engine.initial_state()
        for expected_sequence, outer in enumerate(trace_records, start=1):
            if not isinstance(outer, dict) or set(outer) != {"record_type", "trace"}:
                fail(
                    f"trace_record_schema_mismatch:{expected_sequence}",
                    "trace outer record differs from the committed export contract",
                    blocks_replay=True,
                )
                continue
            if outer.get("record_type") != "trace" or not isinstance(
                outer.get("trace"), dict
            ):
                fail(
                    f"trace_record_type_mismatch:{expected_sequence}",
                    "trace record is not a typed trace mapping",
                    blocks_replay=True,
                )
                continue
            trace = outer["trace"]
            observed_sequence = trace.get("sequence")
            if observed_sequence != expected_sequence:
                fail(
                    f"trace_sequence_mismatch:{expected_sequence}",
                    "trace sequences are not contiguous from one",
                    expected=expected_sequence,
                    actual=observed_sequence,
                    blocks_replay=True,
                )
            if trace.get("run_id") != run_id:
                fail(
                    f"trace_run_id_mismatch:{expected_sequence}",
                    "trace run_id does not match the run header",
                )
            if trace.get("seed") != seed:
                fail(
                    f"trace_seed_mismatch:{expected_sequence}",
                    "trace seed does not match the run header",
                )
            if trace.get("episode_id") != episode_id:
                fail(
                    f"trace_episode_id_mismatch:{expected_sequence}",
                    "trace episode_id does not match the run header",
                )
            if trace.get("producer_function") != TRACE_PRODUCER:
                fail(
                    f"trace_producer_mismatch:{expected_sequence}",
                    "trace producer_function differs from compute_step",
                )
            if trace.get("aggregation_rule") != TRACE_AGGREGATION:
                fail(
                    f"trace_aggregation_rule_mismatch:{expected_sequence}",
                    "trace aggregation rule differs from compute_step",
                )
            if trace.get("code_path_hash") != expected_code_path_hash:
                fail(
                    f"trace_code_path_hash_mismatch:{expected_sequence}",
                    "trace code_path_hash differs from committed payloads",
                )
            observed_trace_hash = trace.get("trace_hash")
            recomputed_trace_hash = engine.compute_trace_hash(trace)
            if observed_trace_hash != recomputed_trace_hash:
                fail(
                    f"trace_hash_mismatch:{expected_sequence}",
                    "trace_hash does not recompute from trace content",
                    expected=recomputed_trace_hash,
                    actual=observed_trace_hash,
                )
            command = trace.get("command")
            if not isinstance(command, dict):
                fail(
                    f"trace_command_missing:{expected_sequence}",
                    "trace does not contain a serialized command",
                    blocks_replay=True,
                )
                continue
            try:
                recomputed = engine.compute_step(state, command, run_meta)
            except Exception as exc:  # committed engine supplies typed invariants
                fail(
                    f"trace_replay_error:{expected_sequence}",
                    "committed engine could not recompute the serialized command",
                    actual=f"{type(exc).__name__}: {exc}",
                    replay=True,
                )
                continue
            if engine.canonical_json(recomputed.trace) != engine.canonical_json(trace):
                fail(
                    f"trace_replay_mismatch:{expected_sequence}",
                    "stored trace differs from committed-engine recomputation",
                    replay=True,
                )
            state = recomputed.next_state

        if store is not None:
            store.close()

    return result(
        header=header,
        record_count=len(trace_records),
        trace_validation_status="PASS" if not validation_errors else "FAIL",
        direct_engine_replay_status=(
            "PASS" if not direct_replay_errors else "FAIL"
        ),
    )


def validate_baseline(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path,
    head_ref: str = "HEAD",
    manifest_bytes: bytes | None = None,
    trace_bytes: bytes | None = None,
    trace_path: str | Path | None = None,
    database_bytes: bytes | None = None,
    database_path: str | Path | None = None,
    require_trace: bool = False,
    require_database: bool = False,
) -> dict[str, Any]:
    """Return a fully computed, fail-closed validation report."""

    repo_root = Path(repo_root).resolve()
    if manifest_bytes is None:
        manifest_bytes = canonical_json_bytes(manifest)
    errors: list[dict[str, Any]] = []
    command_log: list[dict[str, Any]] = []

    def add_error(
        code: str,
        message: str,
        *,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        entry: dict[str, Any] = {"code": code, "message": message}
        if expected is not None:
            entry["expected"] = expected
        if actual is not None:
            entry["actual"] = actual
        errors.append(entry)

    if manifest.get("schema_version") != SCHEMA_VERSION:
        add_error("manifest_schema_mismatch", "manifest schema_version differs")
    if manifest.get("task_id") != TASK_ID:
        add_error("manifest_task_id_mismatch", "manifest task_id differs")
    if manifest.get("baseline_id") != BASELINE_ID:
        add_error("manifest_baseline_id_mismatch", "manifest baseline_id differs")
    if manifest.get("producer") != MANIFEST_PRODUCER:
        add_error("manifest_producer_mismatch", "manifest producer contract differs")
    if manifest.get("claim_ceiling") != CLAIM_CEILING:
        add_error("manifest_claim_ceiling_mismatch", "manifest claim ceiling differs")
    boundary = manifest.get("development_boundary")
    if not isinstance(boundary, dict):
        add_error("development_boundary_invalid", "development boundary is not a mapping")
        boundary = {}
    if set(boundary) != set(EXPECTED_DEVELOPMENT_BOUNDARY):
        add_error(
            "development_boundary_key_set_mismatch",
            "development boundary keys differ from the exact local product-evidence firewall",
            expected=sorted(EXPECTED_DEVELOPMENT_BOUNDARY),
            actual=sorted(boundary),
        )
    for field, expected in EXPECTED_DEVELOPMENT_BOUNDARY.items():
        actual = boundary.get(field)
        if actual != expected or type(actual) is not type(expected):
            add_error(
                f"development_boundary_mismatch:{field}",
                "development boundary field differs from the frozen firewall",
                expected=expected,
                actual=actual,
            )

    source = manifest.get("source")
    if not isinstance(source, dict):
        add_error("manifest_source_invalid", "manifest source is not a mapping")
        source = {}
    if source.get("commit_oid") != EXPECTED_BASELINE_COMMIT:
        add_error(
            "baseline_commit_pin_mismatch",
            "manifest baseline commit differs from the operator-authorized pin",
            expected=EXPECTED_BASELINE_COMMIT,
            actual=source.get("commit_oid"),
        )

    actual_source: dict[str, Any] | None = None
    committed_payloads: dict[str, bytes] = {}
    try:
        actual_source = _inspect_commit(
            repo_root,
            EXPECTED_BASELINE_COMMIT,
            command_log=command_log,
        )
        committed_payloads = _load_committed_payloads(
            repo_root,
            actual_source,
            command_log=command_log,
        )
    except (GitObjectReadError, UnicodeError, ValueError) as exc:
        add_error(
            "baseline_git_object_read_failed",
            "committed baseline objects could not be recomputed",
            actual=f"{type(exc).__name__}: {exc}",
        )

    expected_changes = [{"status": "A", "path": path} for path in EXPECTED_PATHS]
    if source.get("parent_oid") != EXPECTED_BASELINE_PARENT:
        add_error(
            "baseline_parent_oid_mismatch",
            "manifest baseline parent differs from the frozen parent",
            expected=EXPECTED_BASELINE_PARENT,
            actual=source.get("parent_oid"),
        )
    if source.get("tree_oid") != EXPECTED_BASELINE_TREE:
        add_error(
            "baseline_tree_oid_mismatch",
            "manifest baseline tree differs from the frozen tree",
            expected=EXPECTED_BASELINE_TREE,
            actual=source.get("tree_oid"),
        )
    if source.get("required_change_status") != "A":
        add_error("baseline_required_status_mismatch", "required change status is not A")
    if source.get("expected_change_count") != len(EXPECTED_PATHS):
        add_error("baseline_change_count_mismatch", "expected change count is not six")
    if source.get("changes") != expected_changes:
        add_error(
            "baseline_change_set_manifest_mismatch",
            "manifest change set is not the exact six additions",
            expected=expected_changes,
            actual=source.get("changes"),
        )

    manifest_files = source.get("files")
    if not isinstance(manifest_files, list):
        add_error("baseline_files_invalid", "manifest source files are not a list")
        manifest_files = []
    manifest_paths = [
        entry.get("path") for entry in manifest_files if isinstance(entry, dict)
    ]
    if (
        len(manifest_paths) != len(EXPECTED_PATHS)
        or len(set(manifest_paths)) != len(manifest_paths)
        or sorted(manifest_paths) != sorted(EXPECTED_PATHS)
    ):
        add_error(
            "baseline_path_set_mismatch",
            "manifest file paths are not the exact six-path set",
            expected=list(EXPECTED_PATHS),
            actual=manifest_paths,
        )
    manifest_by_path = {
        entry["path"]: entry
        for entry in manifest_files
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }

    exact_change_set_verified = False
    if actual_source is not None:
        if actual_source["commit_oid"] != EXPECTED_BASELINE_COMMIT:
            add_error("baseline_commit_object_mismatch", "resolved commit object differs")
        if actual_source["parent_oid"] != EXPECTED_BASELINE_PARENT:
            add_error("baseline_parent_object_mismatch", "resolved parent object differs")
        if actual_source["tree_oid"] != EXPECTED_BASELINE_TREE:
            add_error("baseline_tree_object_mismatch", "resolved tree object differs")
        exact_change_set_verified = actual_source["changes"] == expected_changes
        if not exact_change_set_verified:
            add_error(
                "baseline_exact_change_set_mismatch",
                "git diff-tree does not show the exact six additions",
                expected=expected_changes,
                actual=actual_source["changes"],
            )
        actual_by_path = {entry["path"]: entry for entry in actual_source["files"]}
        for path in EXPECTED_PATHS:
            manifest_entry = manifest_by_path.get(path)
            actual_entry = actual_by_path.get(path)
            if manifest_entry is None or actual_entry is None:
                add_error(
                    f"file_pin_missing:{path}",
                    "required file pin or committed blob is missing",
                )
                continue
            for field, code in (
                ("mode", "file_mode_mismatch"),
                ("blob_oid", "file_blob_oid_mismatch"),
                ("byte_count", "file_byte_count_mismatch"),
                ("sha256", "file_sha256_mismatch"),
            ):
                expected = actual_entry[field]
                actual = manifest_entry.get(field)
                if actual != expected or type(actual) is not type(expected):
                    add_error(
                        f"{code}:{path}",
                        f"manifest {field} differs from committed Git-object readback",
                        expected=expected,
                        actual=actual,
                    )

    head_oid: str | None = None
    head_descends = False
    head_path_parity = False
    try:
        head_oid = _git_text(
            repo_root,
            ["rev-parse", "--verify", f"{head_ref}^{{commit}}"],
            command_log=command_log,
        )
        ancestry = _run_git(
            repo_root,
            ["merge-base", "--is-ancestor", EXPECTED_BASELINE_COMMIT, head_oid],
            command_log=command_log,
        )
        if ancestry.returncode == 0:
            head_descends = True
        elif ancestry.returncode == 1:
            add_error(
                "head_not_descendant_of_baseline",
                "selected HEAD is neither the baseline nor its descendant",
                expected=EXPECTED_BASELINE_COMMIT,
                actual=head_oid,
            )
        else:
            add_error(
                "head_ancestry_check_failed",
                "git merge-base could not evaluate baseline ancestry",
                actual=ancestry.stderr.decode("utf-8", errors="replace").strip(),
            )
        if actual_source is not None:
            actual_by_path = {entry["path"]: entry for entry in actual_source["files"]}
            parity: list[bool] = []
            for path in EXPECTED_PATHS:
                process = _run_git(
                    repo_root,
                    ["rev-parse", f"{head_oid}:{path}"],
                    command_log=command_log,
                )
                observed = (
                    process.stdout.decode("utf-8", errors="strict").strip()
                    if process.returncode == 0
                    else None
                )
                parity.append(observed == actual_by_path[path]["blob_oid"])
            head_path_parity = all(parity)
    except (GitObjectReadError, UnicodeError) as exc:
        add_error(
            "head_ref_unavailable",
            "selected HEAD could not be resolved",
            actual=f"{type(exc).__name__}: {exc}",
        )

    resolved_database_path = (
        None if database_path is None else str(Path(database_path).resolve())
    )
    database_sha256 = (
        None if database_bytes is None else hashlib.sha256(database_bytes).hexdigest()
    )
    trace_result: dict[str, Any] = {
        "trace_payload_sha256": None,
        "trace_path": None if trace_path is None else str(trace_path),
        "trace_header": None,
        "trace_record_count": 0,
        "trace_validation_status": "NOT_REQUESTED",
        "database_path": resolved_database_path,
        "database_payload_sha256": database_sha256,
        "database_provenance_status": "NOT_REQUESTED",
        "sqlite_recovery_status": "NOT_REQUESTED",
        "sqlite_export_status": "NOT_REQUESTED",
        "serialized_initial_state_status": "NOT_REQUESTED",
        "direct_engine_replay_status": "NOT_REQUESTED",
        "trace_replay_status": "NOT_REQUESTED",
        "trace_replay_input": None,
    }
    database_missing = database_bytes is None or resolved_database_path is None
    if require_database and database_missing:
        add_error(
            "database_required_missing",
            "required durable SQLite replay artifact is unavailable",
        )
        trace_result.update(
            {
                "database_provenance_status": "FAIL",
                "sqlite_recovery_status": "FAIL",
                "sqlite_export_status": "FAIL",
                "serialized_initial_state_status": "FAIL",
                "trace_replay_status": "FAIL",
            }
        )
    if trace_bytes is not None:
        if not committed_payloads:
            add_error(
                "trace_replay_baseline_unavailable",
                "trace cannot be replayed without committed engine/store payloads",
            )
            trace_result["trace_validation_status"] = "FAIL"
            trace_result["trace_replay_status"] = "FAIL"
        elif database_missing:
            if not require_database:
                add_error(
                    "database_required_missing",
                    "trace evidence requires a durable SQLite replay artifact",
                )
            trace_result.update(
                {
                    "trace_payload_sha256": hashlib.sha256(trace_bytes).hexdigest(),
                    "trace_validation_status": "FAIL",
                    "database_provenance_status": "FAIL",
                    "sqlite_recovery_status": "FAIL",
                    "sqlite_export_status": "FAIL",
                    "serialized_initial_state_status": "FAIL",
                    "direct_engine_replay_status": "NOT_REQUESTED",
                    "trace_replay_status": "FAIL",
                }
            )
        else:
            try:
                trace_result = _validate_trace(
                    trace_bytes,
                    trace_path=str(trace_path or "<bytes>"),
                    database_bytes=database_bytes,
                    database_path=resolved_database_path,
                    committed_payloads=committed_payloads,
                    add_error=add_error,
                )
            except Exception as exc:
                add_error(
                    "trace_validation_internal_error",
                    "committed trace validation failed closed",
                    actual=f"{type(exc).__name__}: {exc}",
                )
                trace_result.update(
                    {
                        "trace_payload_sha256": hashlib.sha256(trace_bytes).hexdigest(),
                        "trace_validation_status": "FAIL",
                        "database_provenance_status": "FAIL",
                        "sqlite_recovery_status": "FAIL",
                        "sqlite_export_status": "FAIL",
                        "serialized_initial_state_status": "FAIL",
                        "direct_engine_replay_status": "FAIL",
                        "trace_replay_status": "FAIL",
                    }
                )
    elif require_trace:
        add_error("trace_required_missing", "required core trigger trace is unavailable")
        trace_result["trace_validation_status"] = "FAIL"
        trace_result["trace_replay_status"] = "FAIL"

    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    validator_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    check_digest = canonical_hash(
        {
            "errors": errors,
            "head_oid": head_oid,
            "head_descends": head_descends,
            "head_path_parity": head_path_parity,
            "trace_payload_sha256": trace_result["trace_payload_sha256"],
            "database_payload_sha256": trace_result["database_payload_sha256"],
            "sqlite_recovery_status": trace_result["sqlite_recovery_status"],
            "sqlite_export_status": trace_result["sqlite_export_status"],
        }
    )
    run_id = "ego-life-core-v0-baseline-" + canonical_hash(
        {
            "manifest_sha256": manifest_sha256,
            "validator_hash": validator_hash,
            "head_oid": head_oid,
            "check_digest": check_digest,
        }
    )[:20]
    command_families = sorted(
        {
            next(
                (
                    token
                    for token in record["argv"][1:]
                    if token in {"rev-parse", "diff-tree", "ls-tree", "cat-file", "merge-base"}
                ),
                "other",
            )
            for record in command_log
        }
    )
    trace_header = trace_result.get("trace_header") or {}
    provenance = {
        "producer_function": "verify_ego_life_core_v0_baseline.validate_baseline",
        "input_artifacts": [
            {
                "kind": "git_commit",
                "oid": EXPECTED_BASELINE_COMMIT,
            },
            {
                "kind": "manifest",
                "sha256": manifest_sha256,
            },
            *(
                [
                    {
                        "kind": "trace_jsonl",
                        "path": trace_result["trace_path"],
                        "sha256": trace_result["trace_payload_sha256"],
                    }
                ]
                if trace_result["trace_payload_sha256"] is not None
                else []
            ),
            *(
                [
                    {
                        "kind": "sqlite_database",
                        "path": trace_result["database_path"],
                        "sha256": trace_result["database_payload_sha256"],
                    }
                ]
                if trace_result["database_payload_sha256"] is not None
                else []
            ),
        ],
        "run_id": run_id,
        "seed": trace_header.get("seed"),
        "context_ids": [BASELINE_ID],
        "episode_ids": (
            [trace_header["episode_id"]]
            if isinstance(trace_header.get("episode_id"), str)
            and trace_header.get("episode_id")
            else []
        ),
        "aggregation_rule": (
            "PASS iff every required Git-object, ancestry, firewall, trace-hash, "
            "serialized-SQLite recovery, committed export byte comparison, and "
            "supplemental committed-engine replay check passes; head_path_parity "
            "is informational"
        ),
        "producer_code_path": "scripts/codex/verify_ego_life_core_v0_baseline.py",
        "producer_code_path_hash": validator_hash,
        "manifest_sha256": manifest_sha256,
        "git_command_families": command_families,
    }
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "baseline_id": BASELINE_ID,
        "computed_verdict": "PASS" if not errors else "FAIL",
        "baseline_commit": (
            actual_source.get("commit_oid") if actual_source else None
        ),
        "baseline_parent": (
            actual_source.get("parent_oid") if actual_source else None
        ),
        "baseline_tree": actual_source.get("tree_oid") if actual_source else None,
        "exact_change_set_verified": exact_change_set_verified,
        "head_ref": head_ref,
        "head_oid": head_oid,
        "head_descends_from_baseline": head_descends,
        "head_path_parity": head_path_parity,
        "head_path_parity_required_for_verdict": False,
        "head_path_parity_scope": "informational_current_live_path_comparison",
        **trace_result,
        "provenance": provenance,
        "git_command_log": command_log,
        "errors": errors,
        "claim_ceiling": CLAIM_CEILING,
        "what_this_does_not_prove": [
            "product-lineage authority",
            "learning generalization",
            "mechanism validity",
            "runtime-mainline integration",
            "default enablement",
            "initiative or agency",
            "subjectivity or consciousness",
        ],
    }


def _write_bytes(path: Path, payload: bytes) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument(
        "--database",
        type=Path,
        required=True,
        help="durable SQLite artifact used as authoritative replay input",
    )
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument(
        "--output",
        type=Path,
        help="optional path for the computed validation report",
    )
    parser.add_argument(
        "--build-manifest",
        action="store_true",
        help="materialize --manifest from committed Git objects before validation",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="validate the Git boundary without requiring --trace",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve()
    if args.build_manifest:
        manifest = build_manifest_from_git_objects(repo_root=repo_root)
        manifest_bytes = pretty_json_bytes(manifest)
        _write_bytes(manifest_path, manifest_bytes)
    else:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)

    trace_bytes: bytes | None = None
    require_trace = not args.manifest_only
    if require_trace and args.trace.is_file():
        trace_bytes = args.trace.read_bytes()
    database_bytes = args.database.read_bytes() if args.database.is_file() else None
    report = validate_baseline(
        manifest,
        repo_root=repo_root,
        head_ref=args.head_ref,
        manifest_bytes=manifest_bytes,
        trace_bytes=trace_bytes,
        trace_path=args.trace,
        database_bytes=database_bytes,
        database_path=args.database,
        require_trace=require_trace,
        require_database=True,
    )
    output = pretty_json_bytes(report)
    if args.output is not None:
        _write_bytes(args.output, output)
    sys.stdout.buffer.write(output)
    return 0 if report["computed_verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
