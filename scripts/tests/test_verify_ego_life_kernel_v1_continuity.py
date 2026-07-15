from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "codex" / "verify_ego_life_kernel_v1_continuity.py"
EXACT_PRODUCT_PATHS = [
    "labs/ego_life_playground_v0/__init__.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/store.py",
    "labs/ego_life_playground_v0/app.py",
    "scripts/run_ego_life_playground_v0.py",
    "tests/test_ego_life_playground_v0.py",
]
EXACT_ARTIFACT_NAMES = {
    "continuity.sqlite3",
    "trace.jsonl",
    "product_trigger_receipt.json",
    "baseline_comparison.json",
    "ablation_report.json",
    "replay_report.json",
    "leakage_report.json",
    "failure_manifest.json",
    "claim_ceiling.txt",
    "result.json",
}
REQUIRED_PROVENANCE_FIELDS = {
    "producer_function",
    "input_artifacts",
    "run_id",
    "seed",
    "episode_ids",
    "context_ids",
    "checkpoint_ids",
    "aggregation_rule",
    "code_path_hash",
    "product_code_manifest_hash",
}


def assert_full_provenance(report: dict) -> None:
    assert REQUIRED_PROVENANCE_FIELDS <= set(report)
    assert report["producer_function"]
    assert report["aggregation_rule"]
    assert len(report["code_path_hash"]) == 64
    assert len(report["product_code_manifest_hash"]) == 64
    assert isinstance(report["episode_ids"], list)
    assert isinstance(report["context_ids"], list)
    assert isinstance(report["checkpoint_ids"], list)
    assert report["input_artifacts"]
    for artifact in report["input_artifacts"]:
        assert artifact["path"]
        assert len(artifact["sha256"]) == 64


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _resolve_pointer(document, pointer: str):
    value = document
    if pointer == "":
        return value
    assert pointer.startswith("/")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def independently_audit_refs(output: Path) -> None:
    for artifact_name in (
        "result.json",
        "failure_manifest.json",
        "product_trigger_receipt.json",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "leakage_report.json",
    ):
        root = json.loads((output / artifact_name).read_text(encoding="utf-8"))

        def walk(value):
            if isinstance(value, dict):
                refs = value.get("input_artifacts", [])
                verifier_refs = refs if refs and all(isinstance(item, dict) for item in refs) else []
                for ref in verifier_refs:
                    path = Path(ref["path"])
                    assert path.is_absolute() and path.is_file()
                    assert not ref["path"].startswith(("semantic://", "inline://"))
                    mode = ref["content_mode"]
                    if mode == "raw_file":
                        payload = path.read_bytes()
                        assert ref["json_pointer"] is None
                    else:
                        assert mode == "canonical_json_pointer"
                        document = json.loads(path.read_text(encoding="utf-8"))
                        payload = _canonical_bytes(
                            _resolve_pointer(document, ref["json_pointer"])
                        )
                    assert hashlib.sha256(payload).hexdigest() == ref["sha256"]
                    assert len(payload) == ref["byte_count"]
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(root)


def load_verifier():
    assert SCRIPT.is_file(), f"missing verifier: {SCRIPT}"
    spec = importlib.util.spec_from_file_location(
        "verify_ego_life_kernel_v1_continuity_test", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_headless_run(tmp_path: Path, *, run_id: str = "v1-verifier-test"):
    from labs.ego_life_playground_v0.app import PlaygroundController
    from labs.ego_life_playground_v0.engine import DEFAULT_INTERVENTIONS
    from labs.ego_life_playground_v0.store import SQLiteEventStore

    database = tmp_path / f"{run_id}.sqlite3"
    store = SQLiteEventStore(database)
    controller = PlaygroundController(store, run_id=run_id, seed=17)
    for _ in range(24):
        dispatched = controller.dispatch(
            "novelty",
            trigger_source="headless_acceptance",
            interventions=DEFAULT_INTERVENTIONS,
        )
        assert dispatched.receipt.committed, dispatched.receipt.error
    recovered = controller.recover()
    store.close()
    return database, recovered


def test_product_code_manifest_is_exact_six_file_computation():
    verifier = load_verifier()
    report = verifier.build_product_code_manifest(ROOT)

    assert [entry["path"] for entry in report["files"]] == EXACT_PRODUCT_PATHS
    assert all(len(entry["sha256"]) == 64 and entry["byte_count"] > 0 for entry in report["files"])
    assert len(report["manifest_hash"]) == 64
    assert report["producer_function"].endswith("build_product_code_manifest")
    assert report["aggregation_rule"]


def test_shortcut_baseline_is_independent_callable_and_deterministic(tmp_path: Path):
    verifier = load_verifier()
    from labs.ego_life_playground_v0 import engine

    tree = ast.parse(inspect.getsource(verifier.run_cue_clock_fsm_baseline))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called |= {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not ({"compute_step", "_score_candidate", "compute_trace_hash"} & called)

    state = engine.initial_state(run_id="baseline-independent")
    meta = engine.make_run_metadata("baseline-independent", 17)
    command = engine.make_command(
        sequence=1,
        cue="novelty",
        trigger_source="paired_intervention",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    with verifier.evidence_input_scope(tmp_path / "baseline.json"):
        first = verifier.run_cue_clock_fsm_baseline(state, command, meta)
        second = verifier.run_cue_clock_fsm_baseline(
            deepcopy(state), deepcopy(command), deepcopy(meta)
        )
    assert first == second
    assert first["role"] == "baseline"
    assert first["selected_action"] in engine.ACTIONS
    assert len(first["candidates"]) == len(engine.ACTIONS)


def test_stored_trace_echo_is_explicitly_post_hoc_control(tmp_path: Path):
    verifier = load_verifier()
    _, recovered = build_headless_run(tmp_path, run_id="echo-control")
    with verifier.evidence_input_scope(tmp_path / "echo.json"):
        report = verifier.run_stored_trace_echo_control(list(recovered.traces))

    assert report["role"] == "post_hoc_appearance_control"
    assert report["visible_row_match_rate"] == 1.0
    assert report["included_in_candidate_baseline_score"] is False
    assert report["producer_function"].endswith("run_stored_trace_echo_control")


def test_leakage_scanner_has_clean_case_and_firing_positive_control(tmp_path: Path):
    verifier = load_verifier()
    from labs.ego_life_playground_v0 import engine

    state = engine.initial_state(run_id="leakage")
    command = engine.make_command(
        sequence=1,
        cue="novelty",
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    with verifier.evidence_input_scope(tmp_path / "leakage.json"):
        clean = verifier.scan_for_leakage(
            {"command": command, "state": state}, inject_positive_control=False
        )
        positive = verifier.scan_for_leakage(
            {"command": command, "state": state}, inject_positive_control=True
        )
        leaky_command = deepcopy(command)
        leaky_command["selected_action"] = "rest"
        leaky = verifier.scan_for_leakage(
            {"command": leaky_command, "state": state}, inject_positive_control=False
        )

    assert clean["findings"] == []
    assert positive["positive_control_injected"] is True
    assert positive["positive_control_fired"] is True
    assert positive["findings"]
    assert any("selected_action" in item["path"] for item in leaky["findings"])


def test_paired_interventions_share_checkpoint_observation_and_report_real_effects(tmp_path: Path):
    verifier = load_verifier()
    _, recovered = build_headless_run(tmp_path, run_id="paired")
    with verifier.evidence_input_scope(tmp_path / "ablation.json"):
        checkpoint = verifier.select_intervention_checkpoint(
            list(recovered.frames), minimum_global_tick=16
        )
        report = verifier.run_paired_interventions(
            checkpoint["state"], recovered.run_meta, cue="novelty"
        )

    assert report["checkpoint_id"] == checkpoint["checkpoint_id"]
    assert len(report["observation_id"]) == 64
    assert set(report["cases"]) == {
        "canonical",
        "memory_off",
        "freeze_updates",
        "shuffle_provenance",
    }
    assert {case["checkpoint_id"] for case in report["cases"].values()} == {
        report["checkpoint_id"]
    }
    assert {case["observation_id"] for case in report["cases"].values()} == {
        report["observation_id"]
    }
    assert report["cases"]["memory_off"]["memory_read_count"] == 0
    assert report["cases"]["freeze_updates"]["model_bytes_unchanged"] is True
    assert report["cases"]["freeze_updates"]["memory_bytes_unchanged"] is True
    assert isinstance(report["blocking_failures"], list)


def test_replay_controls_recompute_and_tamper_fail_closed(tmp_path: Path):
    verifier = load_verifier()
    database, recovered = build_headless_run(tmp_path, run_id="replay-controls")
    with verifier.evidence_input_scope(tmp_path / "replay.json"):
        report = verifier.run_replay_checks(database, recovered.run_id)

    request = report["fresh_process_protocol"]["request"]
    assert request["prepare_pid"] == os.getpid()
    assert request["run_id"] == recovered.run_id
    assert len(request["challenge"]) == 64
    assert request["challenge"] in request["pipe_name"]
    assert report["fresh_recovery"]["status"] == "external_probe_required"
    assert "fresh_process_probe_receipt_absent" in report["blocking_failures"]
    for name in (
        "stored_action_rehashed",
        "command_payload",
        "initial_state",
        "code_path_hash",
    ):
        assert report["tamper_controls"][name]["failed_closed"] is True
        assert report["tamper_controls"][name]["expected_failure_class"] == "RecoveryError"
        assert report["tamper_controls"][name]["observed_failure_class"] == "RecoveryError"
        assert report["tamper_controls"][name]["expected_reason_substring"]
        assert report["tamper_controls"][name]["expected_reason_matched"] is True


def test_baseline_and_echo_deletion_and_tamper_controls_are_executed(tmp_path: Path):
    verifier = load_verifier()
    database, recovered = build_headless_run(tmp_path, run_id="baseline-controls")
    manifest = verifier.build_product_code_manifest(ROOT)
    with verifier.evidence_input_scope(tmp_path / "baseline-report.json"):
        report = verifier._build_baseline_report(
            recovered, manifest["manifest_hash"], database
        )

    deletion = report["stored_trace_deletion_control"]
    tamper = report["stored_selected_action_tamper_control"]
    assert deletion["independent_baseline"]["recomputable"] is True
    assert deletion["independent_baseline"]["bit_identical"] is True
    assert deletion["echo_control"]["recomputable"] is False
    assert tamper["independent_baseline"]["recomputable"] is True
    assert tamper["independent_baseline"]["bit_identical"] is True
    assert tamper["echo_control"]["recomputable"] is True
    assert tamper["echo_control"]["bit_identical"] is False


def test_opaque_memory_id_rename_positive_control_is_bit_identical(tmp_path: Path):
    verifier = load_verifier()
    _, recovered = build_headless_run(tmp_path, run_id="memory-id-control")
    with verifier.evidence_input_scope(tmp_path / "memory-id.json"):
        checkpoint = verifier.select_intervention_checkpoint(
            list(recovered.frames), minimum_global_tick=16
        )
        report = verifier.run_paired_interventions(
            checkpoint["state"], recovered.run_meta, cue="novelty"
        )

    control = report["opaque_memory_id_rename_positive_control"]
    assert control["renamed_record_count"] > 0
    assert control["semantic_memory_hash_unchanged"] is True
    assert control["candidate_behavior_bit_identical"] is True
    assert control["selected_action_bit_identical"] is True


def test_prepare_probe_finalize_protocol_and_persisted_refs(tmp_path: Path, monkeypatch):
    verifier = load_verifier()
    output = tmp_path / "evidence"
    result = verifier.run_verification(output, write_artifacts=True)

    assert {path.name for path in output.iterdir()} == EXACT_ARTIFACT_NAMES
    persisted = json.loads((output / "result.json").read_text(encoding="utf-8"))
    failures = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert persisted == result
    assert persisted["producer_function"].endswith("run_verification")
    assert len(persisted["product_code_manifest_hash"]) == 64
    assert failures["blocking_failures"] == persisted["blocking_failures"]
    assert persisted["verdict"] == "v1_continuity_product_acceptance_blocked"
    assert "fresh_process_probe_receipt_absent" in persisted["blocking_failures"]
    assert (output / "continuity.sqlite3").stat().st_size > 0
    assert (output / "trace.jsonl").read_text(encoding="utf-8").strip()
    for json_name in EXACT_ARTIFACT_NAMES - {
        "continuity.sqlite3",
        "trace.jsonl",
        "claim_ceiling.txt",
    }:
        raw = (output / json_name).read_bytes()
        assert raw.endswith(b"\n")
        assert b"\r\n" not in raw
    claim_ceiling_bytes = (output / "claim_ceiling.txt").read_bytes()
    assert claim_ceiling_bytes == (verifier.CLAIM_CEILING + "\n").encode("utf-8")
    assert b"\r\n" not in claim_ceiling_bytes

    trigger = json.loads((output / "product_trigger_receipt.json").read_text(encoding="utf-8"))
    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    leakage = json.loads((output / "leakage_report.json").read_text(encoding="utf-8"))
    for report in (trigger, baseline, ablation, replay, leakage):
        assert_full_provenance(report)
    for nested in (
        trigger["continuity_report"],
        trigger["atomic_second_write_control"],
        trigger["route_firewall"],
        trigger["code_surface_report"],
        baseline["post_hoc_appearance_control"],
        leakage["positive_control"],
    ):
        assert_full_provenance(nested)
    independently_audit_refs(output)

    same_pid_receipt = verifier.build_fresh_process_probe_receipt(output)
    rejected = verifier.validate_fresh_process_probe_receipt(
        replay["fresh_process_protocol"]["request"],
        same_pid_receipt,
        {
            "valid": False,
            "server_pid": same_pid_receipt["probe_pid"],
            "finalizer_pid": os.getpid(),
            "blocking_failures": ["server_pid_equals_finalizer_pid"],
        },
    )
    assert rejected["valid"] is False
    assert "probe_pid_equals_prepare_pid" in rejected["blocking_failures"]
    invalid = deepcopy(same_pid_receipt)
    invalid["challenge"] = "0" * 64
    invalid_result = verifier.validate_fresh_process_probe_receipt(
        replay["fresh_process_protocol"]["request"],
        invalid,
        {"valid": False, "server_pid": None, "finalizer_pid": os.getpid(), "blocking_failures": ["pipe_unavailable"]},
    )
    assert invalid_result["valid"] is False
    assert "challenge_mismatch" in invalid_result["blocking_failures"]

    external_receipt = deepcopy(same_pid_receipt)
    external_receipt["probe_pid"] = same_pid_receipt["probe_pid"] + 100000
    external_receipt["probe_pid_claimed"] = external_receipt["probe_pid"]
    receipt_path = tmp_path / "external-probe-receipt.json"
    external_receipt["receipt_path"] = str(receipt_path.resolve())
    external_receipt["binding_hash"] = verifier._hash(
        verifier._handshake_binding(
            replay["fresh_process_protocol"]["request"], external_receipt
        )
    )
    fake_attestation = {
        "valid": True,
        "server_pid": external_receipt["probe_pid"],
        "server_executable": str(Path(sys.executable).resolve()),
        "finalizer_pid": os.getpid() + 200000,
        "challenge_response_valid": True,
        "ack_sent": True,
        "probe_exit_observed": True,
        "probe_exit_code": 0,
        "no_orphan": True,
        "blocking_failures": [],
    }
    monkeypatch.setattr(
        verifier,
        "_perform_named_pipe_attestation",
        lambda request, receipt, receipt_path: deepcopy(fake_attestation),
    )
    receipt_path.write_text(json.dumps(external_receipt), encoding="utf-8")
    finalized = verifier.finalize_verification(output, receipt_path)
    assert finalized["verdict"] == "continuity_only__memory_conditioning_not_observed"
    assert finalized["blocking_failures"] == [
        "hard_requirement_failed:paired_interventions_computed_without_blocker",
        "natural_checkpoint_memory_bias_zero",
    ]
    assert finalized["fresh_process_protocol"]["probe_exit_observed"] is True
    assert finalized["fresh_process_protocol"]["probe_exit_code"] == 0
    assert finalized["fresh_process_protocol"]["no_orphan"] is True
    assert finalized["fresh_process_protocol"]["process_boundary"] is True
    independently_audit_refs(output)


def test_write_json_is_platform_independent_lf_bytes(tmp_path: Path):
    verifier = load_verifier()
    path = tmp_path / "lf.json"
    verifier._write_json(path, {"alpha": [1, 2], "unicode": "连续"})
    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r\n" not in raw
    assert json.loads(raw) == {"alpha": [1, 2], "unicode": "连续"}


def test_finalize_blocker_aggregation_preserves_real_tamper_failures():
    verifier = load_verifier()
    receipt_absent = "fresh_process_probe_receipt_absent"
    recovery_hard = "hard_requirement_failed:fresh_recovery_all_causal_hashes_match"
    replay_hard = (
        "hard_requirement_failed:fresh_replay_and_all_tamper_controls_fail_closed"
    )
    natural = [
        "hard_requirement_failed:paired_interventions_computed_without_blocker",
        "natural_checkpoint_memory_bias_zero",
    ]
    clean_controls = {
        name: {"failed_closed": True}
        for name in (
            "stored_action_rehashed",
            "command_payload",
            "initial_state",
            "code_path_hash",
        )
    }

    clean = verifier._aggregate_finalized_replay_state(
        [recovery_hard, replay_hard, receipt_absent, *natural],
        {
            "blocking_failures": [receipt_absent],
            "tamper_controls": deepcopy(clean_controls),
        },
    )
    assert clean["fresh_replay_and_all_tamper_controls_fail_closed"] is True
    assert clean["replay_blocking_failures"] == []
    assert clean["blocking_failures"] == natural
    assert clean["verdict"] == "continuity_only__memory_conditioning_not_observed"

    acceptance = verifier._aggregate_finalized_replay_state(
        [recovery_hard, replay_hard, receipt_absent],
        {
            "blocking_failures": [receipt_absent],
            "tamper_controls": deepcopy(clean_controls),
        },
    )
    assert acceptance["blocking_failures"] == []
    assert acceptance["verdict"] == "local_v1_continuity_product_acceptance"

    tamper_failure = "tamper_control_did_not_fail_closed:stored_action_rehashed"
    failed_controls = deepcopy(clean_controls)
    failed_controls["stored_action_rehashed"]["failed_closed"] = False
    tampered = verifier._aggregate_finalized_replay_state(
        [recovery_hard, replay_hard, receipt_absent, *natural],
        {
            # Regression: even a stale/incorrect blocker list cannot hide a
            # real failed tamper-control report during finalization.
            "blocking_failures": [receipt_absent],
            "tamper_controls": failed_controls,
        },
    )
    assert tampered["fresh_replay_and_all_tamper_controls_fail_closed"] is False
    assert tampered["replay_blocking_failures"] == [tamper_failure]
    assert replay_hard in tampered["blocking_failures"]
    assert tamper_failure in tampered["blocking_failures"]
    assert receipt_absent not in tampered["blocking_failures"]
    assert recovery_hard not in tampered["blocking_failures"]
    assert tampered["verdict"] == "v1_continuity_product_acceptance_blocked"

    finalize_source = inspect.getsource(verifier.finalize_verification)
    assert finalize_source.count("_aggregate_finalized_replay_state") == 1


def test_forged_or_nonexistent_probe_pid_cannot_pass_without_live_pipe_attestation(tmp_path: Path):
    verifier = load_verifier()
    output = tmp_path / "evidence"
    verifier.run_verification(output, write_artifacts=True)
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    same_process = verifier.build_fresh_process_probe_receipt(output)
    same_result = verifier.validate_fresh_process_probe_receipt(
        request,
        same_process,
        {
            "valid": False,
            "server_pid": os.getpid(),
            "finalizer_pid": os.getpid(),
            "blocking_failures": ["server_pid_equals_finalizer_pid"],
        },
    )
    assert same_result["valid"] is False
    assert "probe_pid_equals_prepare_pid" in same_result["blocking_failures"]
    assert "live_pipe_attestation_failed" in same_result["blocking_failures"]

    nonexistent = deepcopy(same_process)
    nonexistent["probe_pid"] = 0x7FFFFFFE
    nonexistent_result = verifier.validate_fresh_process_probe_receipt(
        request,
        nonexistent,
        {
            "valid": False,
            "server_pid": None,
            "finalizer_pid": os.getpid(),
            "blocking_failures": ["named_pipe_server_not_found"],
        },
    )
    assert nonexistent_result["valid"] is False
    assert "live_pipe_attestation_failed" in nonexistent_result["blocking_failures"]
    assert "named_pipe_server_not_found" in nonexistent_result["attestation_blocking_failures"]


def test_validator_requires_attested_server_pid_to_equal_receipt_probe_pid(tmp_path: Path):
    verifier = load_verifier()
    output = tmp_path / "evidence"
    verifier.run_verification(output, write_artifacts=True)
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    receipt = verifier.build_fresh_process_probe_receipt(output)
    receipt["probe_pid"] += 100000
    receipt["probe_pid_claimed"] = receipt["probe_pid"]
    receipt["binding_hash"] = verifier._hash(
        verifier._handshake_binding(request, receipt)
    )
    result = verifier.validate_fresh_process_probe_receipt(
        request,
        receipt,
        {
            "valid": True,
            "server_pid": receipt["probe_pid"] + 1,
            "finalizer_pid": os.getpid() + 200000,
            "blocking_failures": [],
        },
    )
    assert result["valid"] is False
    assert "attested_server_pid_mismatch" in result["blocking_failures"]


def test_real_tk_run_stops_at_exactly_24_from_widget_callback_repeated(tmp_path: Path):
    verifier = load_verifier()
    for repetition in range(3):
        report, blockers = verifier._drive_real_tk_run(
            tmp_path / f"widget-run-{repetition}.sqlite3",
            f"widget-run-{repetition}",
        )
        if report.get("mode") != "real_tk_widget_path":
            pytest.skip("real Tk widget path unavailable on this host")
        assert report["run_button_invoked"] is True
        assert report["pause_button_invoked"] is True
        assert report["pause_invoked_from_commit_callback"] is True
        assert report["command_count_at_pause_request"] == 24
        assert report["command_count"] == 24
        assert report["committed_callback_count"] == 24
        assert report["committed_callback_sequences"] == list(range(1, 25))
        assert report["latest_trigger_source"] == "ui_run_button"
        assert not any(
            item.startswith("real_tk_run_command_count_not_24")
            for item in blockers
        )


def test_named_pipe_server_uses_fail_closed_current_operator_sid_acl():
    verifier = load_verifier()
    operator_sid = verifier._current_process_user_sid()
    assert operator_sid.startswith("S-1-")
    sddl = verifier._operator_only_pipe_sddl(operator_sid)
    assert sddl == f"D:P(A;;GA;;;{operator_sid})"

    pipe_name = rf"\\.\pipe\EgoV1AclTest-{verifier.secrets.token_hex(32)}"
    handle = verifier._create_named_pipe_server(pipe_name, operator_sid)
    try:
        assert handle not in (None, verifier._INVALID_HANDLE_VALUE)
    finally:
        verifier._kernel32().CloseHandle(handle)

    wrong_sid = "S-1-0-0" if operator_sid != "S-1-0-0" else "S-1-5-18"
    with pytest.raises(PermissionError, match="operator SID"):
        verifier._create_named_pipe_server(
            rf"\\.\pipe\EgoV1AclReject-{verifier.secrets.token_hex(32)}",
            wrong_sid,
        )
    source = SCRIPT.read_text(encoding="utf-8")
    assert "ConvertStringSecurityDescriptorToSecurityDescriptorW" in source
    assert "_SecurityAttributes" in source
    create_source = inspect.getsource(verifier._create_named_pipe_server)
    assert "security_attributes" in create_source
    assert "PIPE_REJECT_REMOTE_CLIENTS" in create_source


def test_process_boundary_requires_probe_exit_zero_after_ack(tmp_path: Path):
    verifier = load_verifier()
    output = tmp_path / "evidence"
    verifier.run_verification(output, write_artifacts=True)
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    request = replay["fresh_process_protocol"]["request"]
    receipt = verifier.build_fresh_process_probe_receipt(output)
    receipt["probe_pid"] += 100000
    receipt["probe_pid_claimed"] = receipt["probe_pid"]
    receipt["binding_hash"] = verifier._hash(
        verifier._handshake_binding(request, receipt)
    )
    result = verifier.validate_fresh_process_probe_receipt(
        request,
        receipt,
        {
            "valid": True,
            "server_pid": receipt["probe_pid"],
            "finalizer_pid": os.getpid() + 200000,
            "ack_sent": True,
            "probe_exit_observed": False,
            "probe_exit_code": verifier._STILL_ACTIVE,
            "no_orphan": False,
            "blocking_failures": [],
        },
    )
    assert result["valid"] is False
    assert result["process_boundary"] is False
    assert "probe_exit_not_observed_after_ack" in result["blocking_failures"]
    assert "probe_exit_code_not_zero" in result["blocking_failures"]
    assert "probe_orphan_not_ruled_out" in result["blocking_failures"]

    attestation_source = inspect.getsource(verifier._perform_named_pipe_attestation)
    assert "_PROCESS_SYNCHRONIZE" in attestation_source
    ack_offset = attestation_source.index(
        "_pipe_write_frame(pipe_handle, acknowledgement)"
    )
    exit_wait_offset = attestation_source.index("_wait_for_process_exit")
    assert ack_offset < exit_wait_offset
    assert "GetExitCodeProcess" in inspect.getsource(verifier._wait_for_process_exit)


def test_verifier_source_has_no_internal_process_launcher():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported |= {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not ({"subprocess", "multiprocessing"} & imported)
    assert not ({"spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe"} & called)
    source = SCRIPT.read_text(encoding="utf-8")
    assert "GetNamedPipeServerProcessId" in source
    assert "FILE_FLAG_FIRST_PIPE_INSTANCE | FILE_FLAG_OVERLAPPED" in source
    for native_deadline_api in (
        "WaitForSingleObject",
        "CancelIoEx",
        "GetOverlappedResult",
    ):
        assert native_deadline_api in source
    verifier = load_verifier()
    assert 0 < verifier._PIPE_TIMEOUT_MS <= 30000
    for operation in (
        verifier._connect_named_pipe_server,
        verifier._pipe_read_frame,
        verifier._pipe_write_frame,
    ):
        assert "_PIPE_TIMEOUT_MS" in inspect.getsource(operation)
    finalize_tree = ast.parse(inspect.getsource(verifier.finalize_verification))
    attest_calls = [
        node
        for node in ast.walk(finalize_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_perform_named_pipe_attestation"
    ]
    assert len(attest_calls) == 1
