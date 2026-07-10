"""Callable temporary-output validation runner for EGO-K0-FOUNDATION-001A."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from typing import Any, Mapping, Sequence
import uuid


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = REPO_ROOT / "packages" / "ego_k0_kernel" / "src"
for import_root in (REPO_ROOT, PACKAGE_SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from ego_k0_kernel import (  # noqa: E402
    ActionCandidate,
    ActionProposal,
    AdapterCapabilityManifest,
    CapabilityDeniedError,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    FOUNDATION_CODE_CONTRACT_VERSION,
    HashMismatchError,
    KernelStateRecord,
    ObservationRecord,
    SchemaVersionError,
    TraceRow,
    canonical_hash,
    canonical_json_bytes,
    execute_observation,
    initial_state,
    replay_from_checkpoint,
    stable_id,
)
from ego_k0_kernel.events import observation_to_event  # noqa: E402
from ego_k0_kernel.ports import (  # noqa: E402
    REQUIRED_DENIED_CAPABILITIES,
    assert_capability_allowed,
    validate_adapter_manifest,
)
from scripts.ego_k0_adapters.sqlite_event_store import (  # noqa: E402
    DuplicateRecordError,
    SequenceConflictError,
    SQLiteEventStore,
    WritesFrozenError,
)


TASK_ID = "EGO-K0-FOUNDATION-001A"
IMPLEMENTATION_PARENT = "1e25ddead74da9dad810622a657d82f03564091e"
CLAIM_CEILING = (
    "shared event/state contracts, external persistence-adapter conformance, "
    "serialization, and recomputing trace/replay engineering only; no learned model, "
    "learning/replay/memory contribution, transfer, specialness, initiative, agency, "
    "autonomy, subjectivity, functional-subject status, electronic life, product "
    "benefit, EGO/companion readiness, or mainline effect"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _code_path_hash() -> str:
    paths = sorted(
        [
            *PACKAGE_SRC.joinpath("ego_k0_kernel").glob("*.py"),
            REPO_ROOT / "scripts" / "ego_k0_adapters" / "__init__.py",
            REPO_ROOT / "scripts" / "ego_k0_adapters" / "sqlite_event_store.py",
            Path(__file__).resolve(),
        ],
        key=lambda item: item.relative_to(REPO_ROOT).as_posix(),
    )
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(REPO_ROOT).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _contract_hashes() -> dict[str, str]:
    task_dir = REPO_ROOT / "docs" / "codex" / "tasks" / "ego-k0-foundation-001a"
    return {
        "stage_card": _sha256_file(task_dir / "STAGE_CARD.md"),
        "kernel_adapter_contract": _sha256_file(task_dir / "KERNEL_ADAPTER_CONTRACT.md"),
        "trace_replay_contract": _sha256_file(task_dir / "TRACE_REPLAY_CONTRACT.md"),
        "mutation_scope": _sha256_file(task_dir / "MUTATION_SCOPE.yaml"),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


FORBIDDEN_PACKAGE_IMPORT_ROOTS = frozenset(
    {
        "sqlite3",
        "requests",
        "httpx",
        "http",
        "aiohttp",
        "urllib3",
        "websocket",
        "websockets",
        "socket",
        "ssl",
        "urllib",
        "ftplib",
        "smtplib",
        "telnetlib",
        "grpc",
        "openai",
        "anthropic",
        "litellm",
        "transformers",
        "EgoOperator",
        "EgoDesktop",
        "scripts",
    }
)


def scan_forbidden_package_imports(source: str, *, label: str) -> list[str]:
    """Parse imports; used for both the real tree and a firing positive control."""

    tree = ast.parse(source, filename=label)
    findings: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            root = name.split(".", 1)[0]
            if root in FORBIDDEN_PACKAGE_IMPORT_ROOTS or root.startswith("itl_"):
                findings.append(f"{label}:{node.lineno}:{name}")
    return findings


def _typed_contract_gate() -> dict[str, Any]:
    observation = _observation("typed-runner-episode", 1)
    state = initial_state("typed-runner-episode", seed=11)
    candidate = ActionCandidate("probe.typed", {"weight": 0.5}, True)
    proposal = ActionProposal(
        proposal_id="proposal-typed-runner",
        episode_id="typed-runner-episode",
        step_id=1,
        selected_action_id=candidate.action_id,
        candidates=(candidate,),
        decision_factors={"source": "typed_contract_gate"},
    )
    checkpoint = _checkpoint(state, 0, "typed-runner")
    event = observation_to_event(observation, sequence=1)
    manifest = AdapterCapabilityManifest(
        adapter_id="typed-runner-adapter",
        readable_fields=("events",),
        writable_ports=("append_events",),
        forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
    )
    distinct_count = len(
        {
            type(observation),
            type(event),
            type(state),
            type(candidate),
            type(proposal),
            type(checkpoint),
            type(manifest),
        }
    )
    finite_rejected = False
    schema_rejected = False
    contract_version_rejected = False
    try:
        ObservationRecord("bad-finite", "typed-runner-episode", 1, {"x": float("nan")})
    except ContractValidationError:
        finite_rejected = True
    wrong_schema = event.to_dict()
    wrong_schema["schema_version"] = "ego_k0.event.future"
    try:
        EventRecord.from_dict(wrong_schema)
    except SchemaVersionError:
        schema_rejected = True
    wrong_contract = checkpoint.to_dict()
    wrong_contract["code_contract_version"] = "ego_k0.trace_replay.future"
    try:
        CheckpointRecord.from_dict(wrong_contract)
    except SchemaVersionError:
        contract_version_rejected = True
    ok = (
        distinct_count == 7
        and finite_rejected
        and schema_rejected
        and contract_version_rejected
        and proposal.execution_authority is False
    )
    return {
        "ok": ok,
        "distinct_record_type_count": distinct_count,
        "finite_number_rejected": finite_rejected,
        "schema_mismatch_rejected": schema_rejected,
        "contract_version_mismatch_rejected": contract_version_rejected,
    }


def _forbidden_input_leakage_gate() -> dict[str, Any]:
    state_control_fired = False
    observation_control_fired = False
    try:
        KernelStateRecord(
            episode_id="leakage-positive-control",
            step_id=0,
            substates={"observation_count": 0},
            rng_state={"seed": 1, "draw_count": 0, "family_id": "forbidden"},
        )
    except ContractValidationError:
        state_control_fired = True
    try:
        ObservationRecord(
            observation_id="leakage-observation-control",
            episode_id="leakage-positive-control",
            step_id=1,
            payload={"nested": {"heldout_label": "forbidden"}},
        )
    except ContractValidationError:
        observation_control_fired = True
    return {
        "ok": state_control_fired and observation_control_fired,
        "state_positive_control_fired": state_control_fired,
        "observation_positive_control_fired": observation_control_fired,
    }


def _canonical_fresh_process_gate(output_dir: Path) -> dict[str, Any]:
    payload = {"z": [1, 2.5, "猫"], "a": {"flag": True}}
    expected = canonical_hash(payload)
    program = (
        "from ego_k0_kernel.contracts import canonical_hash; "
        f"print(canonical_hash({payload!r}))"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    probe_dir = output_dir / "canonical_process_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", program],
            cwd=probe_dir,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        outputs.append(completed.stdout.strip() if completed.returncode == 0 else "")
    return {"ok": outputs == [expected, expected], "expected": expected, "observed": outputs}


def _import_leakage_gate() -> dict[str, Any]:
    package_dir = PACKAGE_SRC / "ego_k0_kernel"
    actual_findings: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        actual_findings.extend(
            scan_forbidden_package_imports(
                path.read_text(encoding="utf-8"), label=path.name
            )
        )
    positive_findings = scan_forbidden_package_imports(
        "import sqlite3\nfrom scripts.ego_kernel import state\n",
        label="positive_control.py",
    )
    positive_roots = {finding.rsplit(":", 1)[-1].split(".", 1)[0] for finding in positive_findings}
    return {
        "ok": not actual_findings and {"sqlite3", "scripts"}.issubset(positive_roots),
        "actual_findings": actual_findings,
        "positive_control_findings": positive_findings,
    }


def _import_side_effect_gate(output_dir: Path) -> dict[str, Any]:
    probe_dir = output_dir / "import_side_effect_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(PACKAGE_SRC), str(REPO_ROOT)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    program = (
        "import pathlib; before=sorted(p.name for p in pathlib.Path('.').iterdir()); "
        "import ego_k0_kernel; import scripts.ego_k0_adapters.sqlite_event_store; "
        "after=sorted(p.name for p in pathlib.Path('.').iterdir()); "
        "assert before == after"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=probe_dir,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    residue = sorted(item.name for item in probe_dir.iterdir())
    return {
        "ok": completed.returncode == 0 and not residue,
        "returncode": completed.returncode,
        "residue": residue,
    }


def _adapter_capability_gate() -> dict[str, Any]:
    manifest = validate_adapter_manifest(
        AdapterCapabilityManifest(
            adapter_id="runner-capability-probe",
            readable_fields=("events", "checkpoints"),
            writable_ports=("append_events", "write_checkpoint"),
            forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
        )
    )
    denied = False
    unknown = False
    try:
        assert_capability_allowed(manifest, "execute_action")
    except CapabilityDeniedError:
        denied = True
    try:
        assert_capability_allowed(manifest, "unknown_probe_capability")
    except CapabilityDeniedError:
        unknown = True
    return {"ok": denied and unknown, "deny_control_fired": denied, "unknown_control_fired": unknown}


def _fail_closed_store_gate(output_dir: Path) -> dict[str, Any]:
    database_path = output_dir / "fail_closed_probe.sqlite3"
    episode_id = "fail-closed-runner-episode"
    first = observation_to_event(_observation(episode_id, 1), sequence=1)
    sequence_rejected = False
    duplicate_rejected = False
    with SQLiteEventStore(database_path) as store:
        try:
            store.append_events(1, (first,))
        except SequenceConflictError:
            sequence_rejected = True
        store.append_events(0, (first,))
        duplicate = EventRecord(
            event_id=first.event_id,
            episode_id=episode_id,
            step_id=2,
            sequence=2,
            event_type=first.event_type,
            payload={"observation": _observation(episode_id, 2).to_dict()},
            provenance=first.provenance,
        )
        try:
            store.append_events(1, (duplicate,))
        except DuplicateRecordError:
            duplicate_rejected = True
    return {
        "ok": sequence_rejected and duplicate_rejected,
        "sequence_mismatch_rejected": sequence_rejected,
        "duplicate_id_rejected": duplicate_rejected,
    }


class DeterministicProbePolicy:
    """Validation-only deterministic policy; it cannot execute its proposal."""

    def propose(
        self, state: KernelStateRecord, observation: ObservationRecord
    ) -> ActionProposal:
        decision_digest = canonical_hash(
            {
                "seed": state.rng_state["seed"],
                "draw_count": state.rng_state["draw_count"],
                "observation": observation.to_dict(),
            }
        )
        candidates = (
            ActionCandidate(
                action_id="probe.record",
                typed_parameters={"mode": "record"},
                admissible=True,
            ),
            ActionCandidate(
                action_id="probe.defer",
                typed_parameters={"mode": "defer"},
                admissible=True,
            ),
        )
        selected = candidates[int(decision_digest[-1], 16) % len(candidates)].action_id
        proposal_body = {
            "episode_id": observation.episode_id,
            "step_id": observation.step_id,
            "selected": selected,
            "decision_digest": decision_digest,
        }
        return ActionProposal(
            proposal_id=stable_id("proposal", proposal_body),
            episode_id=observation.episode_id,
            step_id=observation.step_id,
            selected_action_id=selected,
            candidates=candidates,
            decision_factors={
                "probe_policy": "deterministic_sha256_choice",
                "decision_digest": decision_digest,
                "execution_authority": False,
            },
            execution_authority=False,
        )


class CollectingTraceSink:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def append(self, row: object) -> None:
        self.rows.append(row.to_dict())


def _observation(episode_id: str, step_id: int) -> ObservationRecord:
    signals = ("amber", "blue", "green", "violet")
    payload = {
        "signal": signals[(step_id - 1) % len(signals)],
        "magnitude": step_id / 10,
        "note": f"foundation-observation-{step_id}",
    }
    return ObservationRecord(
        observation_id=stable_id(
            "observation", {"episode_id": episode_id, "step_id": step_id, "payload": payload}
        ),
        episode_id=episode_id,
        step_id=step_id,
        payload=payload,
        source_refs=(f"context:foundation:{step_id}",),
    )


def _checkpoint(state: KernelStateRecord, sequence: int, label: str) -> CheckpointRecord:
    return CheckpointRecord(
        checkpoint_id=stable_id(
            "checkpoint",
            {"label": label, "state_hash": state.state_hash, "sequence": sequence},
        ),
        state=state,
        last_event_sequence=sequence,
        code_contract_version=FOUNDATION_CODE_CONTRACT_VERSION,
    )


def _trace_sink_feedback_gate(
    *, output_dir: Path, code_path_hash: str, contract_hash: str
) -> dict[str, Any]:
    class MutatingCopySink:
        def __init__(self) -> None:
            self.captured: dict[str, Any] | None = None

        def append(self, row: TraceRow) -> None:
            self.captured = row.to_dict()
            self.captured["state_after_hash"] = "mutated-sink-copy"
            self.captured["selected_action_proposal"]["selected_action_id"] = "mutated"

    episode_id = "trace-feedback-runner-episode"
    state = initial_state(episode_id, seed=31)
    sink = MutatingCopySink()
    with SQLiteEventStore(output_dir / "trace_feedback_probe.sqlite3") as store:
        result = execute_observation(
            state=state,
            observation=_observation(episode_id, 1),
            policy=DeterministicProbePolicy(),
            event_store=store,
            trace_sink=sink,
            expected_sequence=0,
            task_id=TASK_ID,
            run_id="trace-feedback-probe",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        )
    unaffected = (
        result.state_after.state_hash != "mutated-sink-copy"
        and result.proposal.selected_action_id != "mutated"
        and result.trace_row.state_after_hash == result.state_after.state_hash
    )
    return {
        "ok": unaffected and sink.captured is not None,
        "sink_copy_mutation_observed": sink.captured is not None,
        "same_round_result_unaffected": unaffected,
    }


def run_replay(
    *,
    output_dir: Path,
    database_path: Path,
    checkpoint_path: Path,
    trace_path: Path | None,
    run_id: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = CheckpointRecord.from_dict(
        json.loads(checkpoint_path.read_text(encoding="utf-8"))
    )
    expected_traces = None
    if trace_path is not None:
        expected_traces = json.loads(trace_path.read_text(encoding="utf-8"))
    code_path_hash = _code_path_hash()
    contracts = _contract_hashes()
    contract_hash = canonical_hash(contracts)
    with SQLiteEventStore(database_path) as store:
        events = store.read_events(
            checkpoint.state.episode_id, checkpoint.last_event_sequence
        )
    result = replay_from_checkpoint(
        checkpoint=checkpoint,
        events=events,
        policy=DeterministicProbePolicy(),
        task_id=TASK_ID,
        run_id=run_id,
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
        context_ids=("foundation_probe_v1",),
        expected_traces=expected_traces,
    )
    report = result.to_report()
    _write_json(output_dir / "replay_report.json", report)
    return report


def _run_fresh_replay(
    *,
    output_dir: Path,
    database_path: Path,
    checkpoint_path: Path,
    trace_path: Path,
    run_id: str,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--mode",
        "replay",
        "--output-dir",
        str(output_dir),
        "--database-path",
        str(database_path),
        "--checkpoint-path",
        str(checkpoint_path),
        "--trace-path",
        str(trace_path),
        "--run-id",
        run_id,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"fresh replay failed ({completed.returncode}): "
            f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
    return json.loads((output_dir / "replay_report.json").read_text(encoding="utf-8"))


def run_validation(*, output_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    """Run callable Foundation implementation gates into a caller-supplied directory."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_id or f"foundation-{uuid.uuid4()}"
    episode_id = "foundation-probe-episode-v1"
    code_path_hash = _code_path_hash()
    contract_hashes = _contract_hashes()
    contract_hash = canonical_hash(contract_hashes)
    policy = DeterministicProbePolicy()
    database_path = output_dir / "foundation.sqlite3"
    checkpoint_path = output_dir / "initial_checkpoint.json"
    trace_path = output_dir / "source_traces.json"

    state = initial_state(episode_id, seed=1701)
    initial_checkpoint = _checkpoint(state, 0, "initial")
    mid_checkpoint: CheckpointRecord | None = None
    sink = CollectingTraceSink()
    source_steps = []
    with SQLiteEventStore(database_path) as store:
        store.write_checkpoint(0, initial_checkpoint)
        for step_id in range(1, 5):
            step = execute_observation(
                state=state,
                observation=_observation(episode_id, step_id),
                policy=policy,
                event_store=store,
                trace_sink=sink,
                expected_sequence=step_id - 1,
                task_id=TASK_ID,
                run_id=run_id,
                code_path_hash=code_path_hash,
                contract_hash=contract_hash,
            )
            source_steps.append(step)
            state = step.state_after
            if step_id == 2:
                mid_checkpoint = _checkpoint(state, 2, "mid")
                store.write_checkpoint(2, mid_checkpoint)
    if mid_checkpoint is None:
        raise RuntimeError("mid-chain checkpoint was not created")
    source_final_state_hash = state.state_hash
    source_proposal_hashes = [canonical_hash(item.proposal) for item in source_steps]
    _write_json(checkpoint_path, initial_checkpoint.to_dict())
    _write_json(trace_path, sink.rows)

    fresh_reports = [
        _run_fresh_replay(
            output_dir=output_dir / f"fresh_replay_{index}",
            database_path=database_path,
            checkpoint_path=checkpoint_path,
            trace_path=trace_path,
            run_id=f"{run_id}-fresh-{index}",
        )
        for index in (1, 2)
    ]

    with SQLiteEventStore(database_path) as restarted_store:
        latest = restarted_store.read_latest_checkpoint(episode_id)
        if latest is None:
            raise RuntimeError("restart did not recover a checkpoint")
        remaining = restarted_store.read_events(episode_id, latest.last_event_sequence)
        restarted = replay_from_checkpoint(
            checkpoint=latest,
            events=remaining,
            policy=policy,
            task_id=TASK_ID,
            run_id=f"{run_id}-restart",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
            context_ids=("restart", "mid_checkpoint"),
            expected_traces=sink.rows[latest.state.step_id :],
        )
        all_events = restarted_store.read_events(episode_id, 0)
        independently_read_events = restarted_store.read_events(episode_id, 0)
    event_copy = all_events[0].to_dict()
    event_copy["payload"]["observation"]["payload"]["signal"] = "local-copy-mutation"
    byte_independent_records = (
        all_events[0] is not independently_read_events[0]
        and independently_read_events[0].payload["observation"]["payload"]["signal"]
        != "local-copy-mutation"
    )

    stripped_traces = []
    for row in sink.rows:
        stripped = dict(row)
        stripped.pop("selected_action_proposal", None)
        stripped.pop("action_candidates", None)
        stripped.pop("trace_hash", None)
        stripped_traces.append(stripped)
    action_removed = replay_from_checkpoint(
        checkpoint=initial_checkpoint,
        events=all_events,
        policy=policy,
        task_id=TASK_ID,
        run_id=f"{run_id}-action-removed",
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
        context_ids=("stored_action_removal",),
        expected_traces=stripped_traces,
    )

    source_database_hash_before = _sha256_file(database_path)
    tampered_database = output_dir / "tampered_clone.sqlite3"
    shutil.copy2(database_path, tampered_database)
    tamper_detected = False
    connection = sqlite3.connect(str(tampered_database))
    try:
        row = connection.execute(
            "SELECT event_json FROM events WHERE episode_id = ? AND sequence = 2",
            (episode_id,),
        ).fetchone()
        data = json.loads(bytes(row[0]).decode("utf-8"))
        data["payload"]["observation"]["payload"]["signal"] = "tampered"
        connection.execute(
            "UPDATE events SET event_json = ? WHERE episode_id = ? AND sequence = 2",
            (sqlite3.Binary(canonical_json_bytes(data)), episode_id),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(tampered_database) as tampered_store:
            tampered_store.read_events(episode_id, 0)
    except HashMismatchError:
        tamper_detected = True
    source_unchanged = _sha256_file(database_path) == source_database_hash_before

    metadata_event_detected = False
    metadata_event_database = output_dir / "metadata_event_tampered_clone.sqlite3"
    shutil.copy2(database_path, metadata_event_database)
    connection = sqlite3.connect(str(metadata_event_database))
    try:
        connection.execute(
            "UPDATE events SET sequence = 9 WHERE episode_id = ? AND sequence = 2",
            (episode_id,),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(metadata_event_database) as metadata_event_store:
            metadata_event_store.read_events(episode_id, 0)
    except ContractValidationError:
        metadata_event_detected = True

    metadata_checkpoint_detected = False
    metadata_checkpoint_database = output_dir / "metadata_checkpoint_tampered_clone.sqlite3"
    shutil.copy2(database_path, metadata_checkpoint_database)
    connection = sqlite3.connect(str(metadata_checkpoint_database))
    try:
        connection.execute(
            """
            UPDATE checkpoints SET last_event_sequence = 3
            WHERE episode_id = ? AND last_event_sequence = 2
            """,
            (episode_id,),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(metadata_checkpoint_database) as metadata_checkpoint_store:
            metadata_checkpoint_store.read_latest_checkpoint(episode_id)
    except ContractValidationError:
        metadata_checkpoint_detected = True
    source_unchanged = (
        source_unchanged
        and _sha256_file(database_path) == source_database_hash_before
    )

    corrupt_state_hash_detected = False
    corrupt_checkpoint = initial_checkpoint.to_dict()
    corrupt_checkpoint["state"]["state_hash"] = "0" * 64
    try:
        CheckpointRecord.from_dict(corrupt_checkpoint)
    except HashMismatchError:
        corrupt_state_hash_detected = True
    corrupt_trace_hash_detected = False
    corrupt_traces = [dict(row) for row in sink.rows]
    corrupt_traces[0] = dict(corrupt_traces[0])
    corrupt_traces[0]["state_after_hash"] = "0" * 64
    try:
        replay_from_checkpoint(
            checkpoint=initial_checkpoint,
            events=all_events,
            policy=policy,
            task_id=TASK_ID,
            run_id=f"{run_id}-corrupt-trace",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
            context_ids=("corrupt_trace_positive_control",),
            expected_traces=corrupt_traces,
        )
    except HashMismatchError:
        corrupt_trace_hash_detected = True

    nested_trace_schema_detected = False
    invalid_nested_trace = json.loads(json.dumps(sink.rows[0]))
    invalid_nested_trace["observation"]["schema_version"] = "ego_k0.observation.future"
    invalid_nested_trace_body = dict(invalid_nested_trace)
    invalid_nested_trace_body.pop("trace_hash")
    invalid_nested_trace["trace_hash"] = canonical_hash(invalid_nested_trace_body)
    try:
        TraceRow.from_dict(invalid_nested_trace)
    except SchemaVersionError:
        nested_trace_schema_detected = True

    freeze_blocked = False
    with SQLiteEventStore(database_path) as frozen_store:
        frozen_store.freeze_writes()
        try:
            frozen_store.append_events(4, (observation_to_event(_observation(episode_id, 5), sequence=5),))
        except WritesFrozenError:
            freeze_blocked = True

    fresh_ok = all(
        report["ok"]
        and report["final_state_hash"] == source_final_state_hash
        and report["proposal_hashes"] == source_proposal_hashes
        for report in fresh_reports
    )
    gate_details = {
        "typed_schema_contracts": _typed_contract_gate(),
        "canonical_fresh_process_stability": _canonical_fresh_process_gate(output_dir),
        "restart_recovery": {
            "ok": restarted.ok
            and restarted.final_state.state_hash == source_final_state_hash,
            "mismatch_count": len(restarted.mismatches),
        },
        "fresh_process_replay_x2": {
            "ok": fresh_ok
            and fresh_reports[0]["final_state_hash"]
            == fresh_reports[1]["final_state_hash"],
            "process_count": len(fresh_reports),
        },
        "mid_chain_checkpoint_resume": {
            "ok": restarted.ok
            and latest.last_event_sequence == 2
            and len(remaining) == 2,
            "checkpoint_sequence": latest.last_event_sequence,
            "remaining_event_count": len(remaining),
        },
        "stored_action_removal_recomputes": {
            "ok": action_removed.ok
            and action_removed.final_state.state_hash == source_final_state_hash
            and [canonical_hash(item.proposal) for item in action_removed.steps]
            == source_proposal_hashes,
            "recomputed_proposal_count": len(action_removed.steps),
        },
        "event_tamper_positive_control": {
            "ok": tamper_detected and source_unchanged,
            "detector_fired": tamper_detected,
            "source_store_unchanged": source_unchanged,
        },
        "sqlite_metadata_tamper_positive_controls": {
            "ok": metadata_event_detected
            and metadata_checkpoint_detected
            and source_unchanged,
            "event_metadata_detector_fired": metadata_event_detected,
            "checkpoint_metadata_detector_fired": metadata_checkpoint_detected,
            "source_store_unchanged": source_unchanged,
        },
        "corrupt_state_trace_hash_positive_controls": {
            "ok": corrupt_state_hash_detected and corrupt_trace_hash_detected,
            "state_hash_detector_fired": corrupt_state_hash_detected,
            "trace_hash_detector_fired": corrupt_trace_hash_detected,
        },
        "nested_trace_schema_positive_control": {
            "ok": nested_trace_schema_detected,
            "detector_fired": nested_trace_schema_detected,
        },
        "freeze_writes_intervention": {
            "ok": freeze_blocked,
            "write_blocked": freeze_blocked,
        },
        "sequence_duplicate_fail_closed": _fail_closed_store_gate(output_dir),
        "package_import_leakage_scan": _import_leakage_gate(),
        "forbidden_input_leakage_positive_controls": _forbidden_input_leakage_gate(),
        "import_without_cli_side_effect_free": _import_side_effect_gate(output_dir),
        "adapter_capability_fail_closed": _adapter_capability_gate(),
        "byte_independent_store_records": {
            "ok": byte_independent_records,
            "separate_record_instances": all_events[0] is not independently_read_events[0],
        },
        "trace_sink_no_same_round_feedback": _trace_sink_feedback_gate(
            output_dir=output_dir,
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        ),
    }
    gates = {name: bool(details["ok"]) for name, details in gate_details.items()}
    all_gates_ok = all(gates.values())
    database_hash = _sha256_file(database_path)
    report = {
        "schema_version": "ego_k0.foundation_implementation_validation.v1",
        "producer_function": "scripts.run_ego_k0_foundation_validation.run_validation",
        "input_artifact_hashes": {
            **contract_hashes,
            "initial_checkpoint": canonical_hash(initial_checkpoint),
            "source_event_store": database_hash,
            "source_traces": _sha256_file(trace_path),
            "stored_action_removed_traces": canonical_hash(stripped_traces),
            "fresh_replay_1_report": canonical_hash(fresh_reports[0]),
            "fresh_replay_2_report": canonical_hash(fresh_reports[1]),
            "restart_replay_report": canonical_hash(restarted.to_report()),
            "stored_action_removed_replay_report": canonical_hash(
                action_removed.to_report()
            ),
            "event_tampered_clone": _sha256_file(tampered_database),
            "metadata_event_tampered_clone": _sha256_file(metadata_event_database),
            "metadata_checkpoint_tampered_clone": _sha256_file(
                metadata_checkpoint_database
            ),
            "corrupt_checkpoint_control": canonical_hash(corrupt_checkpoint),
            "corrupt_trace_control": canonical_hash(corrupt_traces),
            "invalid_nested_trace_control": canonical_hash(invalid_nested_trace),
        },
        "task_id": TASK_ID,
        "run_id": run_id,
        "episode_ids": [episode_id],
        "context_ids": ["foundation_probe_v1", "restart", "stored_action_removal"],
        "seed_context": {"seed": 1701, "initial_draw_count": 0},
        "aggregation_rule": "logical AND over independently executed implementation gates",
        "code_path_hash": code_path_hash,
        "contract_hashes": contract_hashes,
        "contract_hash": contract_hash,
        "card_hash": contract_hashes["stage_card"],
        "parent_commit": IMPLEMENTATION_PARENT,
        "parent_hash": IMPLEMENTATION_PARENT,
        "execution_authority_hash": canonical_hash(
            {"execution_authority": False, "runtime_authority": "none"}
        ),
        "per_gate_outcomes": {
            name: {
                **details,
                "outcome": "pass" if details["ok"] else "fail",
            }
            for name, details in gate_details.items()
        },
        "status": "implementation_validation_ok" if all_gates_ok else "implementation_validation_failed",
        "task_local_implementation_acceptance": all_gates_ok,
        "foundation_task_final_acceptance": "NOT_ADJUDICATED",
        "official_evidence_bank": False,
        "mainline_connected": False,
        "enabled": False,
        "runtime_authority": "none",
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "implementation_validation_report.json", report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validate", "replay"), default="validate")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--database-path", type=Path)
    parser.add_argument("--checkpoint-path", type=Path)
    parser.add_argument("--trace-path", type=Path)
    parser.add_argument("--run-id", default=f"foundation-{uuid.uuid4()}")
    args = parser.parse_args(argv)
    if args.mode == "validate":
        report = run_validation(output_dir=args.output_dir, run_id=args.run_id)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if report["task_local_implementation_acceptance"] else 1
    if args.database_path is None or args.checkpoint_path is None:
        parser.error("replay mode requires --database-path and --checkpoint-path")
    report = run_replay(
        output_dir=args.output_dir,
        database_path=args.database_path,
        checkpoint_path=args.checkpoint_path,
        trace_path=args.trace_path,
        run_id=args.run_id,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
