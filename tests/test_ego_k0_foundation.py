from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from types import MappingProxyType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = REPO_ROOT / "packages" / "ego_k0_kernel" / "src"
for path in (REPO_ROOT, PACKAGE_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ego_k0_kernel import (  # noqa: E402
    ActionCandidate,
    ActionProposal,
    AdapterCapabilityManifest,
    CapabilityDeniedError,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    HashMismatchError,
    KernelStateRecord,
    ObservationRecord,
    SchemaVersionError,
    TraceRow,
    canonical_hash,
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
from scripts.run_ego_k0_foundation_validation import (  # noqa: E402
    CLAIM_CEILING,
    TASK_ID,
    CollectingTraceSink,
    DeterministicProbePolicy,
    _checkpoint,
    _observation,
    run_validation,
    scan_forbidden_package_imports,
)


def _build_source(tmp_path: Path, *, steps: int = 4) -> dict[str, Any]:
    episode_id = "test-episode"
    database_path = tmp_path / "events.sqlite3"
    policy = DeterministicProbePolicy()
    sink = CollectingTraceSink()
    state = initial_state(episode_id, seed=23)
    initial = _checkpoint(state, 0, "initial-test")
    mid = None
    computations = []
    with SQLiteEventStore(database_path) as store:
        store.write_checkpoint(0, initial)
        for step_id in range(1, steps + 1):
            result = execute_observation(
                state=state,
                observation=_observation(episode_id, step_id),
                policy=policy,
                event_store=store,
                trace_sink=sink,
                expected_sequence=step_id - 1,
                task_id=TASK_ID,
                run_id="test-source",
                code_path_hash="a" * 64,
                contract_hash="b" * 64,
            )
            computations.append(result)
            state = result.state_after
            if step_id == 2:
                mid = _checkpoint(state, 2, "mid-test")
                store.write_checkpoint(2, mid)
    return {
        "episode_id": episode_id,
        "database_path": database_path,
        "initial": initial,
        "mid": mid,
        "state": state,
        "steps": computations,
        "traces": sink.rows,
        "policy": policy,
    }


def _replay(source: dict[str, Any], checkpoint: CheckpointRecord, traces: list[dict[str, Any]]):
    with SQLiteEventStore(source["database_path"]) as store:
        events = store.read_events(source["episode_id"], checkpoint.last_event_sequence)
    return replay_from_checkpoint(
        checkpoint=checkpoint,
        events=events,
        policy=source["policy"],
        task_id=TASK_ID,
        run_id="test-replay",
        code_path_hash="a" * 64,
        contract_hash="b" * 64,
        context_ids=("pytest",),
        expected_traces=traces,
    )


def test_typed_records_are_distinct_and_validate_finite_schema_and_authority() -> None:
    observation = _observation("typed-episode", 1)
    state = initial_state("typed-episode", seed=7)
    candidate = ActionCandidate("probe.one", {"weight": 0.5}, True)
    proposal = ActionProposal(
        proposal_id="proposal-one",
        episode_id="typed-episode",
        step_id=1,
        selected_action_id="probe.one",
        candidates=(candidate,),
        decision_factors={"factor": 1.0},
    )
    event = observation_to_event(observation, sequence=1)
    checkpoint = _checkpoint(state, 0, "typed")
    manifest = AdapterCapabilityManifest(
        adapter_id="typed-adapter",
        readable_fields=("events",),
        writable_ports=("append_events",),
        forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
    )
    assert len(
        {
            type(observation),
            type(state),
            type(candidate),
            type(proposal),
            type(event),
            type(checkpoint),
            type(manifest),
        }
    ) == 7
    assert proposal.execution_authority is False
    assert all(record.to_dict()["schema_version"] for record in (observation, state, event))
    with pytest.raises(ContractValidationError, match="non-finite"):
        ObservationRecord("bad", "typed-episode", 1, {"value": float("nan")})
    with pytest.raises(ContractValidationError, match="forbidden kernel inputs"):
        KernelStateRecord(
            episode_id="typed-episode",
            step_id=0,
            substates={"observation_count": 0},
            rng_state={"seed": 1, "draw_count": 0, "family_id": "leak"},
        )
    with pytest.raises(ContractValidationError, match="cannot execute"):
        ActionProposal(
            proposal_id="bad-proposal",
            episode_id="typed-episode",
            step_id=1,
            selected_action_id="probe.one",
            candidates=(candidate,),
            decision_factors={},
            execution_authority=True,
        )
    wrong_schema = event.to_dict()
    wrong_schema["schema_version"] = "ego_k0.event.v0"
    with pytest.raises(SchemaVersionError):
        EventRecord.from_dict(wrong_schema)
    wrong_contract = checkpoint.to_dict()
    wrong_contract["code_contract_version"] = "ego_k0.trace_replay.future"
    with pytest.raises(SchemaVersionError):
        CheckpointRecord.from_dict(wrong_contract)


def test_canonical_utf8_bytes_and_hash_are_stable_in_fresh_processes(tmp_path: Path) -> None:
    payload = {"z": [1, 2.5, "猫"], "a": {"flag": True}}
    expected = canonical_hash(payload)
    program = (
        "from ego_k0_kernel.contracts import canonical_hash; "
        f"print(canonical_hash({payload!r}))"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    outputs = [
        subprocess.check_output(
            [sys.executable, "-c", program], cwd=tmp_path, env=env, text=True
        ).strip()
        for _ in range(2)
    ]
    assert outputs == [expected, expected]
    assert "猫".encode("utf-8") in json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def test_sqlite_restart_and_mid_checkpoint_recompute_same_state(tmp_path: Path) -> None:
    source = _build_source(tmp_path)
    with SQLiteEventStore(source["database_path"]) as restarted_store:
        latest = restarted_store.read_latest_checkpoint(source["episode_id"])
    assert latest is not None and latest.last_event_sequence == 2
    result = _replay(source, latest, source["traces"][2:])
    assert result.ok
    assert result.final_state.state_hash == source["state"].state_hash


def test_validation_runner_executes_two_fresh_replays_and_computed_provenance(
    tmp_path: Path,
) -> None:
    output = tmp_path / "validation"
    report = run_validation(output_dir=output, run_id="pytest-validation")
    assert report["task_local_implementation_acceptance"] is True
    assert report["status"] == "implementation_validation_ok"
    assert report["foundation_task_final_acceptance"] == "NOT_ADJUDICATED"
    assert report["official_evidence_bank"] is False
    assert report["claim_ceiling"] == CLAIM_CEILING
    assert all(item["ok"] for item in report["per_gate_outcomes"].values())
    assert report["per_gate_outcomes"]["fresh_process_replay_x2"]["ok"]
    for key in (
        "producer_function",
        "input_artifact_hashes",
        "run_id",
        "episode_ids",
        "context_ids",
        "seed_context",
        "aggregation_rule",
        "code_path_hash",
        "contract_hashes",
        "card_hash",
        "parent_hash",
        "execution_authority_hash",
    ):
        assert report[key]
    assert not (REPO_ROOT / "artifacts" / "ego_k0_foundation_001a").exists()


def test_removing_stored_actions_still_recomputes_proposals_and_state(tmp_path: Path) -> None:
    source = _build_source(tmp_path)
    stripped = []
    for row in source["traces"]:
        copy = dict(row)
        copy.pop("selected_action_proposal")
        copy.pop("action_candidates")
        copy.pop("trace_hash")
        stripped.append(copy)
    result = _replay(source, source["initial"], stripped)
    assert result.ok
    assert result.input_artifact_hashes["expected_traces"] == canonical_hash(stripped)
    assert result.final_state.state_hash == source["state"].state_hash
    assert [canonical_hash(item.proposal) for item in result.steps] == [
        canonical_hash(item.proposal) for item in source["steps"]
    ]


def test_cloned_store_event_deletion_diverges_without_mutating_source(tmp_path: Path) -> None:
    source = _build_source(tmp_path)
    source_hash = hashlib.sha256(source["database_path"].read_bytes()).hexdigest()
    clone = tmp_path / "deleted-event-clone.sqlite3"
    shutil.copy2(source["database_path"], clone)
    connection = sqlite3.connect(str(clone))
    try:
        connection.execute(
            "DELETE FROM events WHERE episode_id = ? AND sequence = 2",
            (source["episode_id"],),
        )
        connection.commit()
    finally:
        connection.close()
    with SQLiteEventStore(clone) as clone_store:
        events = clone_store.read_events(source["episode_id"], 0)
    with pytest.raises(ContractValidationError, match="sequence mismatch"):
        replay_from_checkpoint(
            checkpoint=source["initial"],
            events=events,
            policy=source["policy"],
            task_id=TASK_ID,
            run_id="deleted-event",
            code_path_hash="a" * 64,
            contract_hash="b" * 64,
        )
    assert hashlib.sha256(source["database_path"].read_bytes()).hexdigest() == source_hash


def test_corrupt_state_and_trace_hash_positive_controls_fire(tmp_path: Path) -> None:
    source = _build_source(tmp_path, steps=2)
    state_data = source["state"].to_dict()
    state_data["substates"]["observation_count"] = 999
    with pytest.raises(HashMismatchError):
        KernelStateRecord.from_dict(state_data)
    trace_data = dict(source["traces"][0])
    trace_data["state_after_hash"] = "0" * 64
    with pytest.raises(HashMismatchError):
        TraceRow.from_dict(trace_data)
    invalid_nested = json.loads(json.dumps(source["traces"][0]))
    invalid_nested["observation"]["schema_version"] = "ego_k0.observation.future"
    nested_body = dict(invalid_nested)
    nested_body.pop("trace_hash")
    invalid_nested["trace_hash"] = canonical_hash(nested_body)
    with pytest.raises(SchemaVersionError):
        TraceRow.from_dict(invalid_nested)


def test_freeze_writes_intervention_blocks_append_and_checkpoint(tmp_path: Path) -> None:
    database = tmp_path / "frozen.sqlite3"
    state = initial_state("frozen-episode", seed=1)
    with SQLiteEventStore(database) as store:
        store.freeze_writes()
        with pytest.raises(WritesFrozenError):
            store.append_events(
                0, (observation_to_event(_observation("frozen-episode", 1), sequence=1),)
            )
        with pytest.raises(WritesFrozenError):
            store.write_checkpoint(0, _checkpoint(state, 0, "frozen"))


def test_sequence_duplicate_id_and_schema_mismatch_fail_closed(tmp_path: Path) -> None:
    database = tmp_path / "fail-closed.sqlite3"
    first = observation_to_event(_observation("sequence-episode", 1), sequence=1)
    with SQLiteEventStore(database) as store:
        with pytest.raises(SequenceConflictError):
            store.append_events(1, (first,))
        assert store.append_events(0, (first,)) == 1
        duplicate_id = EventRecord(
            event_id=first.event_id,
            episode_id=first.episode_id,
            step_id=2,
            sequence=2,
            event_type=first.event_type,
            payload={"observation": _observation(first.episode_id, 2).to_dict()},
            provenance=first.provenance,
        )
        with pytest.raises(DuplicateRecordError):
            store.append_events(1, (duplicate_id,))
        reread_one = store.read_events(first.episode_id, 0)
        reread_two = store.read_events(first.episode_id, 0)
    assert reread_one[0] is not reread_two[0]
    assert isinstance(reread_one[0].payload, MappingProxyType)
    wrong = first.to_dict()
    wrong["schema_version"] = "ego_k0.event.future"
    with pytest.raises(SchemaVersionError):
        EventRecord.from_dict(wrong)


def test_package_static_import_scan_rejects_adapters_runtime_network_and_llm() -> None:
    package_dir = PACKAGE_SRC / "ego_k0_kernel"
    findings = []
    for path in sorted(package_dir.glob("*.py")):
        findings.extend(
            scan_forbidden_package_imports(
                path.read_text(encoding="utf-8"), label=path.name
            )
        )
    assert findings == []
    positive = scan_forbidden_package_imports(
        "import sqlite3\nfrom scripts.ego_kernel import state\n",
        label="positive_control.py",
    )
    assert any(item.endswith(":sqlite3") for item in positive)
    assert any(item.endswith(":scripts.ego_kernel") for item in positive)


def test_import_without_explicit_cli_has_no_filesystem_or_process_side_effect(
    tmp_path: Path,
) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(PACKAGE_SRC), str(REPO_ROOT)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    program = (
        "import pathlib; before=list(pathlib.Path('.').iterdir()); "
        "import ego_k0_kernel; import scripts.ego_k0_adapters.sqlite_event_store; "
        "after=list(pathlib.Path('.').iterdir()); assert before == after"
    )
    subprocess.run(
        [sys.executable, "-c", program],
        cwd=tmp_path,
        env=env,
        check=True,
        timeout=15,
    )
    assert list(tmp_path.iterdir()) == []


def test_adapter_deny_list_and_unknown_capability_fail_closed(tmp_path: Path) -> None:
    with SQLiteEventStore(tmp_path / "manifest.sqlite3") as store:
        validate_adapter_manifest(store.manifest)
        with pytest.raises(CapabilityDeniedError, match="explicitly denied"):
            assert_capability_allowed(store.manifest, "execute_action")
        with pytest.raises(CapabilityDeniedError, match="unknown"):
            assert_capability_allowed(store.manifest, "invent_capability")
    bad_manifest = AdapterCapabilityManifest(
        adapter_id="bad-manifest",
        readable_fields=("events", "secret_state"),
        writable_ports=("append_events",),
        forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
    )
    with pytest.raises(CapabilityDeniedError, match="unknown adapter surface"):
        validate_adapter_manifest(bad_manifest)


def test_trace_sink_copy_cannot_feed_back_into_same_round(tmp_path: Path) -> None:
    class MutatingCopySink:
        def __init__(self) -> None:
            self.captured = None

        def append(self, row: object) -> None:
            self.captured = row.to_dict()
            self.captured["state_after_hash"] = "mutated-sink-copy"
            self.captured["selected_action_proposal"]["selected_action_id"] = "mutated"

    database = tmp_path / "trace-sink.sqlite3"
    state = initial_state("trace-sink-episode", seed=99)
    sink = MutatingCopySink()
    with SQLiteEventStore(database) as store:
        result = execute_observation(
            state=state,
            observation=_observation("trace-sink-episode", 1),
            policy=DeterministicProbePolicy(),
            event_store=store,
            trace_sink=sink,
            expected_sequence=0,
            task_id=TASK_ID,
            run_id="trace-sink-test",
            code_path_hash="a" * 64,
            contract_hash="b" * 64,
        )
    assert result.state_after.state_hash != "mutated-sink-copy"
    assert result.proposal.selected_action_id != "mutated"
    assert result.trace_row.state_after_hash == result.state_after.state_hash
