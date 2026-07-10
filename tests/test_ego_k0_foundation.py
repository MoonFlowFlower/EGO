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
from typing import Any, Mapping

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
    PostCommitTraceDeliveryError,
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
    AtomicStepCommitError,
    DuplicateRecordError,
    SequenceConflictError,
    SQLiteEventStore,
    WritesFrozenError,
)
import scripts.run_ego_k0_foundation_validation as foundation_runner  # noqa: E402
from scripts.run_ego_k0_foundation_validation import (  # noqa: E402
    CLAIM_CEILING,
    REQUIRED_FORMAL_GATE_NAMES,
    TASK_ID,
    CollectingTraceSink,
    DeterministicProbePolicy,
    _checkpoint,
    _observation,
    _require_clean_repo,
    _require_direct_child,
    _require_exact_changed_paths,
    _verify_canonical_route_index,
    _verify_git_object_pin,
    _verify_git_working_file,
    _verify_itl_authority,
    resolve_foundation_verdict,
    run_evidence_producer,
    run_validation,
    scan_forbidden_package_imports,
)


def _tree_snapshot(target: Path) -> dict[str, Any]:
    files = sorted(
        (path for path in target.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(target).as_posix(),
    )
    return {
        "exists": target.exists(),
        "files": tuple(
            (
                path.relative_to(target).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in files
        ),
    }


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
    canonical_artifact = REPO_ROOT / "artifacts" / "ego_k0_foundation_001a"
    canonical_artifact_before = _tree_snapshot(canonical_artifact)
    report = run_validation(output_dir=output, run_id="pytest-validation")
    assert report["task_local_implementation_acceptance"] is True
    assert report["status"] == "implementation_validation_ok"
    assert report["foundation_task_final_acceptance"] == "NOT_ADJUDICATED"
    assert report["official_evidence_bank"] is False
    assert report["claim_ceiling"] == CLAIM_CEILING
    assert all(item["ok"] for item in report["per_gate_outcomes"].values())
    original_gate_names = {
        "typed_schema_contracts",
        "canonical_fresh_process_stability",
        "restart_recovery",
        "fresh_process_replay_x2",
        "mid_chain_checkpoint_resume",
        "stored_action_removal_recomputes",
        "event_tamper_positive_control",
        "sqlite_metadata_tamper_positive_controls",
        "corrupt_state_trace_hash_positive_controls",
        "nested_trace_schema_positive_control",
        "freeze_writes_intervention",
        "sequence_duplicate_fail_closed",
        "package_import_leakage_scan",
        "forbidden_input_leakage_positive_controls",
        "import_without_cli_side_effect_free",
        "adapter_capability_fail_closed",
        "byte_independent_store_records",
        "trace_sink_no_same_round_feedback",
    }
    assert len(original_gate_names) == 18
    assert original_gate_names.issubset(report["per_gate_outcomes"])
    assert {
        "canonical_transactional_trace_outbox",
        "atomic_second_write_rollback",
        "post_commit_trace_delivery_recovery",
    }.issubset(report["per_gate_outcomes"])
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
    assert _tree_snapshot(canonical_artifact) == canonical_artifact_before


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


def test_atomic_step_rolls_back_event_and_trace_when_second_write_fails(
    tmp_path: Path,
) -> None:
    database = tmp_path / "atomic-second-write.sqlite3"
    with SQLiteEventStore(database):
        pass
    connection = sqlite3.connect(str(database))
    try:
        connection.execute(
            """
            CREATE TRIGGER force_trace_outbox_failure
            BEFORE INSERT ON trace_outbox
            BEGIN
                SELECT RAISE(ROLLBACK, 'forced second write failure');
            END;
            """
        )
        connection.commit()
    finally:
        connection.close()

    episode_id = "atomic-rollback-episode"
    sink = CollectingTraceSink()
    with SQLiteEventStore(database) as store:
        with pytest.raises(AtomicStepCommitError) as captured:
            execute_observation(
                state=initial_state(episode_id, seed=101),
                observation=_observation(episode_id, 1),
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=sink,
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="atomic-rollback-test",
                code_path_hash="a" * 64,
                contract_hash="b" * 64,
            )
        assert captured.value.committed is False
        assert store.read_events(episode_id, 0) == ()
        assert store.read_trace_rows(episode_id, 0) == ()
    assert sink.rows == []


def test_atomic_step_wraps_non_integrity_second_write_failure_as_not_committed(
    tmp_path: Path,
) -> None:
    database = tmp_path / "atomic-operational-failure.sqlite3"
    with SQLiteEventStore(database):
        pass
    connection = sqlite3.connect(str(database))
    try:
        connection.execute(
            """
            CREATE TRIGGER force_trace_outbox_operational_failure
            BEFORE INSERT ON trace_outbox
            BEGIN
                SELECT no_such_function();
            END;
            """
        )
        connection.commit()
    finally:
        connection.close()

    episode_id = "atomic-operational-failure-episode"
    with SQLiteEventStore(database) as store:
        with pytest.raises(AtomicStepCommitError) as captured:
            execute_observation(
                state=initial_state(episode_id, seed=102),
                observation=_observation(episode_id, 1),
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=CollectingTraceSink(),
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="atomic-operational-failure-test",
                code_path_hash="a" * 64,
                contract_hash="b" * 64,
            )
        assert isinstance(captured.value.__cause__, sqlite3.OperationalError)
        assert captured.value.committed is False
        assert store.read_events(episode_id, 0) == ()
        assert store.read_trace_rows(episode_id, 0) == ()


def test_throwing_sink_exposes_committed_receipt_recovery_replay_and_retry_guard(
    tmp_path: Path,
) -> None:
    class ThrowingSink:
        def append(self, row: TraceRow) -> None:
            raise RuntimeError(f"forced sink failure for {row.trace_hash}")

    database = tmp_path / "throwing-sink.sqlite3"
    episode_id = "throwing-sink-episode"
    state = initial_state(episode_id, seed=103)
    observation = _observation(episode_id, 1)
    initial = _checkpoint(state, 0, "throwing-sink")
    with SQLiteEventStore(database) as store:
        with pytest.raises(PostCommitTraceDeliveryError) as captured:
            execute_observation(
                state=state,
                observation=observation,
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=ThrowingSink(),
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="throwing-sink-test",
                code_path_hash="a" * 64,
                contract_hash="b" * 64,
            )
        receipt = captured.value
        events = store.read_events(episode_id, 0)
        traces = store.read_trace_rows(episode_id, 0)
        with pytest.raises(SequenceConflictError):
            execute_observation(
                state=state,
                observation=observation,
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=CollectingTraceSink(),
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="throwing-sink-retry-test",
                code_path_hash="a" * 64,
                contract_hash="b" * 64,
            )
    assert isinstance(receipt.__cause__, RuntimeError)
    assert receipt.committed is True
    assert receipt.committed_sequence == 1
    assert receipt.step_id == 1
    assert len(events) == len(traces) == 1
    assert receipt.trace_hash == traces[0].trace_hash
    replay = replay_from_checkpoint(
        checkpoint=initial,
        events=events,
        policy=DeterministicProbePolicy(),
        task_id=TASK_ID,
        run_id="throwing-sink-recovery-replay",
        code_path_hash="a" * 64,
        contract_hash="b" * 64,
        context_ids=("throwing_sink_recovery",),
        expected_traces=[traces[0].to_dict()],
    )
    assert replay.ok


def test_formal_verdict_resolver_uses_computed_pass_fail_and_detector_mutations() -> None:
    passing = {name: {"ok": True} for name in REQUIRED_FORMAL_GATE_NAMES}
    for detector, fields in foundation_runner.DETECTOR_POSITIVE_CONTROL_FIELDS.items():
        passing[detector].update({field: True for field in fields})
    assert resolve_foundation_verdict(passing) == "foundation_engineering_pass"
    missing_gate = dict(passing)
    missing_gate.pop("restart_recovery")
    assert resolve_foundation_verdict(missing_gate) == (
        "foundation_engineering_fail_missing_gate_restart_recovery"
    )

    ordinary_failure = {**passing, "typed_schema_contracts": {"ok": False}}
    assert resolve_foundation_verdict(ordinary_failure) == (
        "foundation_engineering_fail_typed_schema_contracts"
    )

    blind_detector = {
        **ordinary_failure,
        "event_tamper_positive_control": {"ok": False, "detector_fired": False},
    }
    assert resolve_foundation_verdict(blind_detector) == (
        "foundation_instrument_invalid_event_tamper_positive_control"
    )

    inconsistent_blind_detector = {
        **passing,
        "event_tamper_positive_control": {"ok": True, "detector_fired": False},
    }
    assert resolve_foundation_verdict(inconsistent_blind_detector) == (
        "foundation_instrument_invalid_event_tamper_positive_control"
    )

    live_detector_with_engineering_failure = {
        **passing,
        "package_import_leakage_scan": {
            "ok": False,
            "actual_scan_clean": False,
            "positive_control_fired": True,
        },
    }
    assert resolve_foundation_verdict(live_detector_with_engineering_failure) == (
        "foundation_engineering_fail_package_import_leakage_scan"
    )


def test_callable_gate_mutations_rerun_validation_and_drive_resolver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as ordinary_mutation:
        ordinary_mutation.setattr(
            foundation_runner,
            "_typed_contract_gate",
            lambda: {"ok": False, "forced_mutation": "typed_contract_gate"},
        )
        ordinary_report = run_validation(
            output_dir=tmp_path / "ordinary-gate-mutation",
            run_id="ordinary-gate-mutation",
        )
    assert ordinary_report["task_local_implementation_acceptance"] is False
    assert resolve_foundation_verdict(ordinary_report["per_gate_outcomes"]) == (
        "foundation_engineering_fail_typed_schema_contracts"
    )

    with monkeypatch.context() as detector_mutation:
        detector_mutation.setattr(
            foundation_runner,
            "_import_leakage_gate",
            lambda: {
                "ok": False,
                "actual_findings": [],
                "actual_scan_clean": True,
                "positive_control_fired": False,
                "positive_control_findings": [],
                "forced_mutation": "blind_positive_control",
            },
        )
        detector_report = run_validation(
            output_dir=tmp_path / "detector-gate-mutation",
            run_id="detector-gate-mutation",
        )
    assert detector_report["task_local_implementation_acceptance"] is False
    assert resolve_foundation_verdict(detector_report["per_gate_outcomes"]) == (
        "foundation_instrument_invalid_package_import_leakage_scan"
    )


def _git_command(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def _init_git_fixture(
    tmp_path: Path,
    relative_path: str,
    content: str,
    *,
    autocrlf: str = "false",
    suffix: str = "",
) -> tuple[Path, str]:
    identity = f"{relative_path}:{suffix}"
    repo = tmp_path / f"git-fixture-{hashlib.sha256(identity.encode()).hexdigest()[:8]}"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "core.autocrlf", autocrlf], check=True
    )
    path = repo / Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))
    subprocess.run(["git", "-C", str(repo), "add", "--", relative_path], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "fixture"], check=True
    )
    head = _git_command(repo, "rev-parse", "HEAD")
    path.write_bytes(
        subprocess.check_output(["git", "-C", str(repo), "show", f"{head}:{relative_path}"])
    )
    return repo, head


def _commit_fixture_files(repo: Path, files: Mapping[str, str], message: str) -> str:
    for relative_path, content in files.items():
        path = repo / Path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
    subprocess.run(
        ["git", "-C", str(repo), "add", "--", *files.keys()], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", message], check=True
    )
    return _git_command(repo, "rev-parse", "HEAD")


def test_git_provenance_helpers_fail_closed_on_wrong_parent_untracked_and_semantic_change(
    tmp_path: Path,
) -> None:
    repo, head = _init_git_fixture(tmp_path, "source.py", "print('clean')\n")
    (repo / "second.txt").write_text("second\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "--", "second.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "second"], check=True
    )
    head = _git_command(repo, "rev-parse", "HEAD")
    _require_clean_repo(repo)
    verified_file = _verify_git_working_file(repo, "source.py", head=head)
    assert verified_file["raw_sha256_parity"] is True
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="wrong direct parent"):
        _require_direct_child(repo, head, "0" * 40)

    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="dirty"):
        _require_clean_repo(repo)
    (repo / "dirty.txt").unlink()

    (repo / "source.py").write_text("print('tampered')\n", encoding="utf-8")
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="working bytes"
    ):
        _verify_git_working_file(repo, "source.py", head=head)


def test_git_eol_materialization_uses_clean_filter_parity_and_rejects_semantic_change(
    tmp_path: Path,
) -> None:
    repo, head = _init_git_fixture(
        tmp_path,
        "source.py",
        "print('clean')\n",
        autocrlf="true",
        suffix="eol",
    )
    source = repo / "source.py"
    canonical_bytes = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{head}:source.py"]
    )
    assert b"\r\n" not in canonical_bytes

    source.write_bytes(canonical_bytes.replace(b"\n", b"\r\n"))
    semantic_status = _require_clean_repo(repo)
    verified = _verify_git_working_file(repo, "source.py", head=head)
    assert semantic_status["index_semantically_clean"] is True
    assert semantic_status["worktree_semantically_clean"] is True
    assert verified["hash_object_parity"] is True
    assert verified["raw_sha256_parity"] is False
    assert verified["working_representation_differs"] is True
    assert verified["raw_working_sha256"] != verified["canonical_git_blob_sha256"]

    source.write_bytes(b"print('semantic mutation')\r\n")
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="working bytes"
    ):
        _verify_git_working_file(repo, "source.py", head=head)
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="dirty"):
        _require_clean_repo(repo)


def test_direct_child_requires_exactly_one_parent(tmp_path: Path) -> None:
    repo, root = _init_git_fixture(
        tmp_path, "base.txt", "base\n", suffix="parents"
    )
    child = _commit_fixture_files(repo, {"child.txt": "child\n"}, "child")
    _require_direct_child(repo, child, root)
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="wrong direct parent"):
        _require_direct_child(repo, child, "0" * 40)

    tree = _git_command(repo, "rev-parse", f"{child}^{{tree}}")
    merge = subprocess.check_output(
        [
            "git",
            "-C",
            str(repo),
            "commit-tree",
            tree,
            "-p",
            child,
            "-p",
            root,
        ],
        input="synthetic merge\n",
        text=True,
    ).strip()
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="wrong direct parent"):
        _require_direct_child(repo, merge, child)


def test_intermediate_topology_paths_object_pins_and_canonical_index_fail_closed(
    tmp_path: Path,
) -> None:
    repo, base = _init_git_fixture(
        tmp_path, "base.txt", "base\n", suffix="route-scope"
    )
    route_paths = {
        "docs/task/ADDENDUM.md": "# addendum\n",
        "docs/task/SCOPE.yaml": "scope: exact\n",
        "docs/TASK_LANE_INDEX.md": "# canonical index\n",
    }
    intermediate = _commit_fixture_files(repo, route_paths, "intermediate")
    final = _commit_fixture_files(repo, {"producer.py": "print('final')\n"}, "final")
    _require_direct_child(repo, intermediate, base)
    _require_direct_child(repo, final, intermediate)
    _require_exact_changed_paths(
        repo,
        intermediate,
        tuple(route_paths),
        label="route/provenance scope-repair commit",
    )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="path set drifted"):
        _require_exact_changed_paths(
            repo,
            intermediate,
            (*route_paths, "unexpected.txt"),
            label="route/provenance scope-repair commit",
        )
    drift_commit = _commit_fixture_files(
        repo, {"unexpected.txt": "unexpected path\n"}, "intermediate path drift"
    )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="path set drifted"):
        _require_exact_changed_paths(
            repo,
            drift_commit,
            tuple(route_paths),
            label="route/provenance scope-repair commit",
        )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="wrong direct parent"):
        _require_direct_child(repo, final, base)
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="wrong direct parent"):
        _require_direct_child(repo, intermediate, "0" * 40)

    pins = []
    for path in route_paths:
        raw = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{intermediate}:{path}"]
        )
        pins.append(
            {
                "commit": intermediate,
                "path": path,
                "blob": _git_command(repo, "rev-parse", f"{intermediate}:{path}"),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    for pin in pins:
        verified = _verify_git_object_pin(
            repo,
            head=final,
            commit=intermediate,
            path=pin["path"],
            expected_blob=pin["blob"],
            expected_sha256=pin["sha256"],
        )
        assert verified["ancestor_of_head"] is True
        with pytest.raises(foundation_runner.EvidenceProvenanceError, match="pin mismatch"):
            _verify_git_object_pin(
                repo,
                head=final,
                commit=intermediate,
                path=pin["path"],
                expected_blob="0" * 40,
                expected_sha256=pin["sha256"],
            )

    index_pin = next(
        item for item in pins if item["path"] == "docs/TASK_LANE_INDEX.md"
    )
    index = _verify_canonical_route_index(
        repo,
        head=final,
        intermediate_commit=intermediate,
        pin=index_pin,
        renderer=lambda: route_paths["docs/TASK_LANE_INDEX.md"],
    )
    assert index["renderer_matches_pinned_bytes"] is True
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="renderer output"):
        _verify_canonical_route_index(
            repo,
            head=final,
            intermediate_commit=intermediate,
            pin=index_pin,
            renderer=lambda: "# tampered renderer output\n",
        )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="intermediate commit"):
        _verify_canonical_route_index(
            repo,
            head=final,
            intermediate_commit=base,
            pin=index_pin,
            renderer=lambda: route_paths["docs/TASK_LANE_INDEX.md"],
        )
    tampered_head = _commit_fixture_files(
        repo,
        {"docs/TASK_LANE_INDEX.md": "# committed index tamper\n"},
        "tamper canonical index",
    )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="no longer inherits"):
        _verify_canonical_route_index(
            repo,
            head=tampered_head,
            intermediate_commit=intermediate,
            pin=index_pin,
            renderer=lambda: route_paths["docs/TASK_LANE_INDEX.md"],
        )


def test_card_object_pin_fails_closed_on_wrong_blob_and_ancestry(tmp_path: Path) -> None:
    repo, head = _init_git_fixture(tmp_path, "card.md", "# card\n")
    blob = _git_command(repo, "rev-parse", f"{head}:card.md")
    raw = subprocess.check_output(["git", "-C", str(repo), "show", f"{head}:card.md"])
    sha256 = hashlib.sha256(raw).hexdigest()
    verified = _verify_git_object_pin(
        repo,
        head=head,
        commit=head,
        path="card.md",
        expected_blob=blob,
        expected_sha256=sha256,
    )
    assert verified["ancestor_of_head"] is True
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="pin mismatch"):
        _verify_git_object_pin(
            repo,
            head=head,
            commit=head,
            path="card.md",
            expected_blob="0" * 40,
            expected_sha256=sha256,
        )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="not an ancestor"):
        _verify_git_object_pin(
            repo,
            head="0" * 40,
            commit=head,
            path="card.md",
            expected_blob=blob,
            expected_sha256=sha256,
        )


def _foundation_route_payload() -> dict[str, Any]:
    blocked = {
        "ITL-K0-H0-H1-INSTRUMENT-001A:H0": False,
        "EGO-K0-REFERENCE-KERNEL-001A": False,
        "ITL-K0-H0-H1-INSTRUMENT-001A:H1": False,
        "K0-IMMUTABLE-FREEZE-001A": False,
        "ITL-K0-FORMAL-EVIDENCE-001A": False,
    }
    return {
        "implementation_authorized": True,
        "authorized_implementation_targets": [TASK_ID],
        "authorizations": {"foundation_implementation": True, "formal_run": False},
        "child_authorizations": {TASK_ID: True, **blocked},
        "current_state": "READY_TO_IMPLEMENT",
    }


def _itl_fixture(
    tmp_path: Path, *, suffix: str, route: Mapping[str, Any] | None = None
) -> tuple[Path, str, str, dict[str, str]]:
    route_path = (
        "artifacts/ROUTE-STATE-MACHINE-001A/routes/"
        "K0-DUAL-TRACK-SUPERSESSION-001A/state.json"
    )
    route_text = json.dumps(route or _foundation_route_payload(), sort_keys=True) + "\n"
    repo, authority_commit = _init_git_fixture(
        tmp_path, route_path, route_text, suffix=suffix
    )
    canonical = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{authority_commit}:{route_path}"]
    )
    pins = {
        "authority_commit": authority_commit,
        "route_path": route_path,
        "route_blob": _git_command(repo, "rev-parse", f"{authority_commit}:{route_path}"),
        "route_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    return repo, authority_commit, route_path, pins


def test_itl_authority_accepts_unrelated_descendant_and_untracked_context(
    tmp_path: Path,
) -> None:
    repo, authority_commit, _, pins = _itl_fixture(
        tmp_path, suffix="unrelated-context"
    )
    initial = _verify_itl_authority(repo, pins)
    descendant = _commit_fixture_files(
        repo, {"docs/unrelated.md": "unrelated descendant\n"}, "unrelated descendant"
    )
    untracked = repo / "docs" / "codex" / "tasks" / "UNRELATED.md"
    untracked.parent.mkdir(parents=True, exist_ok=True)
    untracked.write_text("unrelated untracked\n", encoding="utf-8")
    verified = _verify_itl_authority(repo, pins)
    assert verified["authority_commit"] == authority_commit
    assert verified["live_head"] == descendant
    assert verified["authority_commit_ancestor_of_live_head"] is True
    assert verified["live_route_blob"] == pins["route_blob"]
    assert "docs/codex/tasks/UNRELATED.md" in verified["unrelated_untracked_paths"]
    assert canonical_hash(verified["authority_hash_material"]) == canonical_hash(
        initial["authority_hash_material"]
    )
    with pytest.raises(foundation_runner.EvidenceProvenanceError, match="path/blob parity"):
        _verify_itl_authority(repo, {**pins, "route_blob": "0" * 40})


def test_itl_authority_rejects_nonancestor_live_route_change_and_dirty_path(
    tmp_path: Path,
) -> None:
    repo, authority_commit, route_path, pins = _itl_fixture(
        tmp_path, suffix="authority-mutations"
    )
    tree = _git_command(repo, "rev-parse", f"{authority_commit}^{{tree}}")
    unrelated_root = subprocess.check_output(
        ["git", "-C", str(repo), "commit-tree", tree],
        input="unrelated root\n",
        text=True,
    ).strip()
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="not an ancestor"
    ):
        _verify_itl_authority(
            repo, {**pins, "authority_commit": unrelated_root}
        )

    changed_route = _foundation_route_payload()
    changed_route["route_id"] = "semantic-route-change"
    _commit_fixture_files(
        repo,
        {route_path: json.dumps(changed_route, sort_keys=True) + "\n"},
        "change live route",
    )
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="path/blob parity"
    ):
        _verify_itl_authority(repo, pins)

    dirty_repo, dirty_commit, dirty_path, dirty_pins = _itl_fixture(
        tmp_path, suffix="dirty-authority"
    )
    canonical = subprocess.check_output(
        ["git", "-C", str(dirty_repo), "show", f"{dirty_commit}:{dirty_path}"]
    )
    (dirty_repo / dirty_path).write_bytes(canonical + b"semantic working mutation\n")
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="path/blob parity"
    ):
        _verify_itl_authority(dirty_repo, dirty_pins)
    (dirty_repo / dirty_path).write_bytes(canonical + b"semantic staged mutation\n")
    subprocess.run(
        ["git", "-C", str(dirty_repo), "add", "--", dirty_path], check=True
    )
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="path/blob parity"
    ):
        _verify_itl_authority(dirty_repo, dirty_pins)


def test_itl_authority_parses_pinned_object_and_rejects_non_foundation_authority(
    tmp_path: Path,
) -> None:
    invalid_route = _foundation_route_payload()
    invalid_route["authorizations"]["formal_run"] = True
    repo, _, _, pins = _itl_fixture(
        tmp_path, suffix="non-foundation", route=invalid_route
    )
    with pytest.raises(
        foundation_runner.EvidenceProvenanceError, match="Foundation-only"
    ):
        _verify_itl_authority(repo, pins)


def test_evidence_producer_exception_always_writes_machine_failure_files(
    tmp_path: Path,
) -> None:
    output = tmp_path / "producer-exception"

    def provenance_stub(**_: Any) -> dict[str, Any]:
        return {"execution_authority_hash": "a" * 64, "verified": True}

    def throwing_validation(**_: Any) -> dict[str, Any]:
        raise RuntimeError("forced producer exception")

    result = run_evidence_producer(
        output_dir=output,
        run_id="producer-exception-test",
        official=False,
        validation_producer=throwing_validation,
        provenance_producer=provenance_stub,
    )
    assert result["producer_completed"] is False
    assert result["official_evidence_bank"] is False
    stored_result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert stored_result["candidate_verdict"] == (
        "foundation_engineering_fail_producer_computed_gates"
    )
    assert failure["exception_type"] == "RuntimeError"
    assert failure["phase"] == "computed_gates"


def test_evidence_producer_setup_exception_writes_machine_failure_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "producer-setup-exception"
    monkeypatch.setattr(
        foundation_runner,
        "_code_path_hash",
        lambda: (_ for _ in ()).throw(RuntimeError("forced setup exception")),
    )
    result = run_evidence_producer(
        output_dir=output,
        run_id="producer-setup-exception-test",
        official=False,
        provenance_producer=lambda **_: {
            "execution_authority_hash": "a" * 64,
            "verified": True,
        },
    )
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert result["candidate_verdict"] == (
        "foundation_engineering_fail_producer_producer_setup"
    )
    assert result["code_path_hash"] == "UNAVAILABLE_DUE_TO_PRODUCER_SETUP_FAILURE"
    assert failure["phase"] == "producer_setup"
    assert failure["exception_type"] == "RuntimeError"


def test_official_producer_rejects_injected_computation_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "official-injection-refusal"
    monkeypatch.setattr(foundation_runner, "OFFICIAL_OUTPUT_DIR", output)
    result = run_evidence_producer(
        output_dir=output,
        run_id="official-injection-refusal-test",
        official=True,
        validation_producer=lambda **_: {"per_gate_outcomes": {}},
        provenance_producer=lambda **_: {
            "execution_authority_hash": "a" * 64,
            "verified": True,
        },
    )
    assert result["producer_completed"] is False
    assert result["official_evidence_bank"] is False
    assert result["candidate_verdict"] == (
        "foundation_engineering_fail_producer_producer_setup"
    )
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert failure["exception_type"] == "EvidenceProvenanceError"
    assert "forbids injected" in failure["exception_message"]


def test_wrong_official_target_writes_machine_failure_without_adjudication(
    tmp_path: Path,
) -> None:
    output = tmp_path / "wrong-official-target"
    result = run_evidence_producer(
        output_dir=output,
        run_id="wrong-official-target-test",
        official=True,
    )
    assert result["producer_completed"] is False
    assert result["official_evidence_bank"] is False
    assert result["candidate_verdict"] == (
        "foundation_engineering_fail_producer_producer_setup"
    )
    stored = json.loads((output / "result.json").read_text(encoding="utf-8"))
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert stored["verdict"] == "NOT_ADJUDICATED_PRODUCER_FAILURE"
    assert stored["foundation_task_final_acceptance"] == "NOT_ADJUDICATED"
    assert failure["phase"] == "producer_setup"
    assert "official evidence target must be" in failure["exception_message"]


def test_evidence_producer_trial_resolves_callable_gates_and_is_not_official(
    tmp_path: Path,
) -> None:
    output = tmp_path / "producer-trial"

    def provenance_stub(**_: Any) -> dict[str, Any]:
        return {"execution_authority_hash": "b" * 64, "verified": True}

    def validation_stub(*, output_dir: Path, run_id: str) -> dict[str, Any]:
        output_dir.mkdir(parents=True)
        gates = {
            name: {"ok": True, "producer": "validation_stub"}
            for name in REQUIRED_FORMAL_GATE_NAMES
        }
        for detector, fields in foundation_runner.DETECTOR_POSITIVE_CONTROL_FIELDS.items():
            gates[detector].update({field: True for field in fields})
        return {
            "episode_ids": ["trial-episode"],
            "context_ids": ["trial-context"],
            "seed_context": {"seed": 1, "used": True},
            "code_path_hash": "c" * 64,
            "contract_hashes": {"trial": "d" * 64},
            "input_artifact_hashes": {"trial": "e" * 64},
            "per_gate_outcomes": gates,
            "run_id": run_id,
        }

    result = run_evidence_producer(
        output_dir=output,
        run_id="producer-trial-test",
        official=False,
        validation_producer=validation_stub,
        provenance_producer=provenance_stub,
    )
    assert result["candidate_verdict"] == "foundation_engineering_pass"
    assert result["verdict"] == "NOT_ADJUDICATED_TRIAL"
    assert result["foundation_task_final_acceptance"] == "NOT_ADJUDICATED"
    assert result["official_evidence_bank"] is False
    assert (output / "result.json").is_file()


def test_official_producer_refuses_existing_output_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "already-exists"
    output.mkdir()
    sentinel = output / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    monkeypatch.setattr(foundation_runner, "OFFICIAL_OUTPUT_DIR", output)
    with pytest.raises(foundation_runner.OutputTargetExistsError, match="will not be overwritten"):
        run_evidence_producer(
            output_dir=output,
            run_id="official-overwrite-refusal",
            official=True,
        )
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert sorted(item.name for item in output.iterdir()) == ["sentinel.txt"]
