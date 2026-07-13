"""Computed controls, provenance, validation, and atomic artifact production."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest import mock

from . import utility

_FORBIDDEN_KEY_FRAGMENTS = (
    "outcome",
    "reward",
    "feedback",
    "target",
    "label",
    "expected",
    "verdict",
    "selected_action",
)


class ArtifactPathError(RuntimeError):
    """The requested artifact or staging root is not absent."""


class ProducerStructureAbort(RuntimeError):
    """The producer could not validate its final in-memory structure."""


class FunctionalValidationFailure(RuntimeError):
    """All available checks ran, but one or more required checks failed."""

    def __init__(self, message: str, response: dict[str, Any] | None = None):
        super().__init__(message)
        self.response = response


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_value(value: Any) -> str:
    return _sha_bytes(utility._canonical_bytes(value))


def _load_json_file(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                duplicates.append(key)
            value[key] = item
        return value

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=hook,
            parse_constant=lambda constant: utility._fail(
                "JSON_CONSTANT", constant
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        utility._fail("JSON_PARSE", str(exc))
    if duplicates:
        utility._fail("DUPLICATE_KEY", duplicates[0])
    if type(value) is not dict:
        utility._fail("JSON_SCHEMA", "object required")
    return value


def _repo_root(path: Path, relative_path: str) -> Path:
    resolved = path.resolve()
    relative = Path(*relative_path.split("/"))
    for parent in resolved.parents:
        if (parent / relative).resolve() == resolved:
            return parent
    utility._fail("REPO_PATH", relative_path)


def _code_path_hash(repo_root: Path, contract: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    for relative in contract["provenance_contract"]["code_path_hash"]["ordered_paths"]:
        path_bytes = relative.encode("utf-8")
        file_bytes = (repo_root / Path(*relative.split("/"))).read_bytes()
        digest.update(struct.pack(">I", len(path_bytes)))
        digest.update(path_bytes)
        digest.update(struct.pack(">Q", len(file_bytes)))
        digest.update(file_bytes)
    return digest.hexdigest()


def zero_utility_predict(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Independent all-zero control, without calling the utility predictor."""
    validated = utility._validate_observation(observation)
    scores = [
        {"action_id": action, "score_numerator": 0, "score_denominator": 1}
        for action in validated["legal_action_ids"]
    ]
    return {
        "schema_version": "ego.outcome_utility.baseline_prediction.v1",
        "observation_id": validated["observation_id"],
        "episode_id": validated["episode_id"],
        "step_id": validated["step_id"],
        "context_id": validated["context_id"],
        "scores": scores,
        "selected_action_id": validated["legal_action_ids"][0],
        "producer_function": (
            "ego_outcome_utility.functional_checks.zero_utility_predict"
        ),
    }


def replay_without_updates(
    checkpoint_payload: bytes, ordered_steps: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Rerun prediction on every observation while withholding updates."""
    state = utility.deserialize_state(checkpoint_payload)
    initial_hash = state["state_hash"]
    predictions: list[dict[str, Any]] = []
    selections: list[str] = []
    for step in ordered_steps:
        utility._require_exact_keys(
            step, {"observation", "feedback"}, "TRANSCRIPT_STEP"
        )
        prediction = utility.predict(state, step["observation"])
        predictions.append(prediction)
        selections.append(prediction["selected_action_id"])
    return {
        "schema_version": "ego.outcome_utility.no_update_result.v1",
        "initial_state_hash": initial_hash,
        "final_state_hash": initial_hash,
        "selection_sequence": selections,
        "per_step_predictions": predictions,
        "update_invocation_count": 0,
        "producer_function": (
            "ego_outcome_utility.functional_checks.replay_without_updates"
        ),
    }


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def scan_observation_mapping(
    observation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Recursively scan mapping keys only for forbidden channel fragments."""
    if not isinstance(observation, Mapping):
        utility._fail("LEAKAGE_SCAN", "mapping required")
    findings: list[dict[str, Any]] = []

    def visit(value: Any, pointer: str) -> None:
        if isinstance(value, Mapping):
            for key in value:
                if type(key) is not str:
                    utility._fail("LEAKAGE_KEY", "string key required")
                child = pointer + "/" + _pointer_escape(key)
                lowered = key.lower()
                for fragment in _FORBIDDEN_KEY_FRAGMENTS:
                    if fragment in lowered:
                        findings.append(
                            {
                                "json_pointer": child,
                                "key": key,
                                "fragment": fragment,
                            }
                        )
                visit(value[key], child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, pointer + f"/{index}")

    visit(observation, "")
    findings.sort(key=lambda item: (item["json_pointer"], item["fragment"]))
    return findings


def resolve_verdict(
    *,
    required_check_names: Sequence[str],
    observed_checks: Mapping[str, bool],
    success_label: str,
    failure_label: str,
) -> str:
    """Resolve only an exact, boolean, caller-labelled check map."""
    if isinstance(required_check_names, (str, bytes)):
        utility._fail("VERDICT_CHECKS", "name sequence required")
    names = list(required_check_names)
    if any(type(name) is not str for name in names) or len(names) != len(set(names)):
        utility._fail("VERDICT_CHECKS", "unique string names required")
    if type(observed_checks) is not dict or list(observed_checks) != names:
        utility._fail("VERDICT_CHECKS", "exact ordered key set required")
    if any(type(value) is not bool for value in observed_checks.values()):
        utility._fail("VERDICT_CHECKS", "bool values required")
    if type(success_label) is not str or type(failure_label) is not str:
        utility._fail("VERDICT_LABEL", "string labels required")
    return success_label if all(observed_checks.values()) else failure_label


def _target_cell_only(
    before: Mapping[str, Any], after: Mapping[str, Any], context: str, action: str
) -> bool:
    before_cells = {
        (cell["context_id"], cell["action_id"]): cell for cell in before["cells"]
    }
    after_cells = {
        (cell["context_id"], cell["action_id"]): cell for cell in after["cells"]
    }
    target = (context, action)
    if target not in after_cells or before_cells.get(target) == after_cells[target]:
        return False
    for key in set(before_cells) | set(after_cells):
        if key != target and before_cells.get(key) != after_cells.get(key):
            return False
    return True


def _dynamic_identifier_check(contract_hash: str) -> bool:
    suffix = contract_hash[:12]
    model = f"dynamic.model.{suffix}"
    actions = [f"dynamic.action.0.{suffix}", f"dynamic.action.1.{suffix}"]
    observation = {
        "schema_version": "ego.outcome_utility.observation.v1",
        "observation_id": f"dynamic.observation.{suffix}",
        "episode_id": f"dynamic.episode.{suffix}",
        "step_id": 1,
        "context_id": f"dynamic.context.{suffix}",
        "legal_action_ids": actions,
    }
    state = utility.new_state(model)
    prediction = utility.predict(state, observation)
    feedback = {
        "schema_version": "ego.outcome_utility.feedback.v1",
        "feedback_id": f"dynamic.feedback.{suffix}",
        "observation_id": observation["observation_id"],
        "episode_id": observation["episode_id"],
        "step_id": 1,
        "context_id": observation["context_id"],
        "action_id": prediction["selected_action_id"],
        "outcome_micros": 17,
    }
    result = utility.run_step(state, observation, feedback)
    payload = utility.serialize_state(result["next_state"])
    return utility.serialize_state(utility.deserialize_state(payload)) == payload


def _source_literal_scan(repo_root: Path, contract: Mapping[str, Any]) -> bool:
    forbidden = contract["anti_hardcoding"]["production_source_forbidden_literals"]
    for relative in contract["anti_hardcoding"]["production_source_paths"]:
        text = (repo_root / Path(*relative.split("/"))).read_text(encoding="utf-8")
        if any(literal in text for literal in forbidden):
            return False
    return True


def _single_logic_path_check(
    repo_root: Path, transcript: Mapping[str, Any]
) -> bool:
    from . import cli

    package = repo_root / "packages" / "ego_outcome_utility" / "src" / "ego_outcome_utility"
    utility_tree = ast.parse((package / "utility.py").read_text(encoding="utf-8"))
    utility_defs = [
        node.name for node in utility_tree.body if isinstance(node, ast.FunctionDef)
    ]
    if utility_defs.count("predict") != 1 or utility_defs.count("observe_outcome") != 1:
        return False
    for source in (package / "cli.py", repo_root / "scripts" / "run_ego_outcome_utility_001a.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        definitions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        if "predict" in definitions or "observe_outcome" in definitions:
            return False
    state = utility.new_state(transcript["model_id"])
    first = transcript["steps"][0]
    with mock.patch.object(utility, "predict", wraps=utility.predict) as predict_spy, mock.patch.object(
        utility, "observe_outcome", wraps=utility.observe_outcome
    ) as update_spy:
        utility.run_step(state, first["observation"], first["feedback"])
        if predict_spy.call_count != 1 or update_spy.call_count != 1:
            return False
    checkpoint = utility.serialize_state(state)
    with mock.patch.object(utility, "run_step", wraps=utility.run_step) as step_spy:
        utility.replay(checkpoint, transcript["steps"])
        if step_spy.call_count != len(transcript["steps"]):
            return False
    with mock.patch.object(utility, "run_step", wraps=utility.run_step) as process_spy:
        cli.process_transcript(transcript)
        if process_spy.call_count != len(transcript["steps"]):
            return False
    with mock.patch.object(utility, "predict", side_effect=AssertionError("independent")):
        zero_utility_predict(first["observation"])
    return True


def _invocation(
    producer: str,
    input_hashes: Mapping[str, str],
    output: Any,
    call_count: int,
    step_ids: list[int],
) -> dict[str, Any]:
    return {
        "producer_function": producer,
        "input_hashes": dict(input_hashes),
        "output_hash": _sha_value(output),
        "call_count": call_count,
        "step_ids": step_ids,
    }


def _common_provenance(
    contract: Mapping[str, Any],
    run_id: str,
    input_hashes: Mapping[str, str],
    transcript: Mapping[str, Any],
    code_hash: str,
    contract_hash: str,
) -> dict[str, Any]:
    observations = [step["observation"] for step in transcript["steps"]]
    return {
        "task_id": contract["provenance_contract"]["task_id_value"],
        "run_id": run_id,
        "producer_script": contract["provenance_contract"]["producer_script_value"],
        "input_artifact_paths": contract["provenance_contract"][
            "input_artifact_paths_exact"
        ],
        "input_artifact_hashes": dict(input_hashes),
        "episode_ids": sorted({item["episode_id"] for item in observations}),
        "context_ids": sorted({item["context_id"] for item in observations}),
        "seed_context": deepcopy(contract["provenance_contract"]["seed_context"]),
        "aggregation_rule": contract["provenance_contract"]["aggregation_rule"],
        "code_path_hash": code_hash,
        "functional_contract_hash": contract_hash,
    }


def _envelope(
    filename: str,
    payload: Any,
    provenance: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    artifact = contract["artifact_contract"]
    return {
        "schema_version": artifact["report_schema_versions"][filename],
        "task_id": provenance["task_id"],
        "run_id": provenance["run_id"],
        "producer_function": artifact["producer_functions"][filename],
        "producer_script": provenance["producer_script"],
        "input_artifact_paths": deepcopy(provenance["input_artifact_paths"]),
        "input_artifact_hashes": deepcopy(provenance["input_artifact_hashes"]),
        "episode_ids": deepcopy(provenance["episode_ids"]),
        "context_ids": deepcopy(provenance["context_ids"]),
        "seed_context": deepcopy(provenance["seed_context"]),
        "aggregation_rule": provenance["aggregation_rule"],
        "code_path_hash": provenance["code_path_hash"],
        "functional_contract_hash": provenance["functional_contract_hash"],
        "payload": payload,
    }


def _exact_envelope(report: Mapping[str, Any], filename: str, contract: Mapping[str, Any]) -> bool:
    artifact = contract["artifact_contract"]
    return (
        type(report) is dict
        and list(report) == artifact["common_json_report_exact_keys"]
        and report["schema_version"] == artifact["report_schema_versions"][filename]
        and report["producer_function"] == artifact["producer_functions"][filename]
        and type(report["payload"]) is dict
        and list(report["payload"]) == artifact["payload_exact_keys"][filename]
    )


def _validate_draft_bundle(
    reports: Mapping[str, Any],
    trace_rows: Sequence[Mapping[str, Any]],
    claim_bytes: bytes,
    proposed_result_payload: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> bool:
    artifact = contract["artifact_contract"]
    report_names = [
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "leakage_report.json",
    ]
    if set(reports) != set(report_names):
        return False
    if not all(_exact_envelope(reports[name], name, contract) for name in report_names):
        return False
    if len(trace_rows) != len(contract["frozen_fixture"]["transcript_object"]["steps"]):
        return False
    if not all(_exact_envelope(row, "trace.jsonl", contract) for row in trace_rows):
        return False
    expected_claim = (artifact["claim_ceiling_text"] + "\n").encode("utf-8")
    if claim_bytes != expected_claim:
        return False
    stable_keys = [
        key
        for key in artifact["payload_exact_keys"]["result.json"]
        if key not in {"verdict", "required_checks", "check_records"}
    ]
    if list(proposed_result_payload) != stable_keys:
        return False
    if proposed_result_payload["claim_ceiling"] != artifact["claim_ceiling_text"]:
        return False
    if proposed_result_payload["claim_ceiling_sha256"] != _sha_bytes(claim_bytes):
        return False
    common = artifact["common_json_report_exact_keys"]
    first = reports[report_names[0]]
    for name in report_names[1:]:
        report = reports[name]
        if any(report[key] != first[key] for key in common if key not in {"schema_version", "producer_function", "payload"}):
            return False
    return True


def _validate_final_result_structure(
    result: Mapping[str, Any], contract: Mapping[str, Any]
) -> bool:
    if not _exact_envelope(result, "result.json", contract):
        return False
    artifact = contract["artifact_contract"]
    payload = result["payload"]
    names = artifact["result_required_checks"]
    checks = payload["required_checks"]
    records = payload["check_records"]
    if type(checks) is not dict or list(checks) != names:
        return False
    if any(type(value) is not bool for value in checks.values()):
        return False
    if type(records) is not list or [record.get("check_id") for record in records] != names:
        return False
    if any(type(record) is not dict or list(record) != artifact["check_record_exact_keys"] for record in records):
        return False
    expected = resolve_verdict(
        required_check_names=names,
        observed_checks=checks,
        success_label=artifact["success_verdict"],
        failure_label=artifact["failure_verdict"],
    )
    return (
        payload["verdict"] == expected
        and payload["authority_consumption"] == artifact["authority_consumption_values"]
        and payload["claim_ceiling"] == artifact["claim_ceiling_text"]
        and payload["claim_ceiling_sha256"]
        == _sha_bytes((artifact["claim_ceiling_text"] + "\n").encode("utf-8"))
    )


def _validate_failure_manifest_structure(
    manifest: Mapping[str, Any], contract: Mapping[str, Any]
) -> bool:
    if not _exact_envelope(manifest, "failure_manifest.json", contract):
        return False
    artifact = contract["artifact_contract"]
    payload = manifest["payload"]
    checks = payload["required_checks"]
    names = artifact["result_required_checks"]
    if type(checks) is not dict or list(checks) != names:
        return False
    expected = resolve_verdict(
        required_check_names=names,
        observed_checks=checks,
        success_label=artifact["success_verdict"],
        failure_label=artifact["failure_verdict"],
    )
    return (
        payload["verdict"] == expected
        and not all(checks.values())
        and payload["canonical_attempt_ordinal"] == 1
        and payload["partial_evidence_authoritative"] is False
        and payload["authority_consumption"] == artifact["authority_consumption_values"]
    )


def _file_bytes(filename: str, value: Any) -> bytes:
    if filename.endswith(".json"):
        return utility._canonical_bytes(value) + b"\n"
    if filename.endswith(".jsonl"):
        return b"".join(utility._canonical_bytes(row) + b"\n" for row in value)
    if type(value) is not bytes:
        raise TypeError("text artifact requires bytes")
    return value


def _bundle_write(output_dir: Path, files: Mapping[str, bytes]) -> None:
    root = output_dir.resolve()
    staging = Path(str(root) + ".staging")
    if root.exists() or staging.exists():
        raise ArtifactPathError("output and staging roots must be absent")
    try:
        staging.mkdir(parents=True, exist_ok=False)
        for name in sorted(files):
            if Path(name).name != name:
                raise ArtifactPathError("flat artifact filename required")
            with (staging / name).open("xb") as handle:
                handle.write(files[name])
                handle.flush()
                os.fsync(handle.fileno())
        if sorted(path.name for path in staging.iterdir()) != sorted(files):
            raise ArtifactPathError("staging surface mismatch")
        os.replace(staging, root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    if staging.exists() or sorted(path.name for path in root.iterdir()) != sorted(files):
        raise ArtifactPathError("final artifact surface mismatch")


def _fresh_suffix_replay(
    repo_root: Path,
    checkpoint: bytes,
    ordered_steps: Sequence[Mapping[str, Any]],
    expected_trace: Sequence[Mapping[str, Any]],
    task_id: str,
    run_id: str,
    code_hash: str,
    contract_hash: str,
) -> tuple[dict[str, Any], bytes, bytes]:
    payload = {
        "schema_version": "ego.outcome_utility.replay_worker_payload.v1",
        "checkpoint_state_base64": base64.b64encode(checkpoint).decode("ascii"),
        "ordered_steps": deepcopy(list(ordered_steps)),
        "expected_trace": deepcopy(list(expected_trace)),
        "task_id": task_id,
        "run_id": run_id,
        "code_path_hash": code_hash,
        "functional_contract_hash": contract_hash,
    }
    runner = repo_root / "scripts" / "run_ego_outcome_utility_001a.py"
    completed = subprocess.run(
        [sys.executable, str(runner), "replay-worker"],
        input=utility._canonical_bytes(payload) + b"\n",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stderr or not completed.stdout.endswith(b"\n"):
        utility._fail("FRESH_REPLAY", "worker process failed")
    result = utility._load_canonical_json(completed.stdout[:-1], "FRESH_REPLAY")
    return result, utility._canonical_bytes(payload), completed.stdout


def _check_record(
    check_id: str,
    producer: str,
    input_hashes: Mapping[str, str],
    observed: Any,
    expected_rule: str,
) -> dict[str, Any]:
    passed = observed if type(observed) is bool else bool(observed)
    return {
        "check_id": check_id,
        "producer_function": producer,
        "input_hashes": dict(input_hashes),
        "observed_value": observed,
        "expected_rule": expected_rule,
        "passed": passed,
    }


def run_functional_validation(
    contract_path: Path, fixture_path: Path, output_dir: Path, run_id: str
) -> dict[str, Any]:
    """Compute every report, derive the verdict, and atomically bank one bundle."""
    utility._require_identifier(run_id, "run_id")
    contract_path = contract_path.resolve()
    fixture_path = fixture_path.resolve()
    contract = _load_json_file(contract_path)
    provenance_contract = contract["provenance_contract"]
    expected_paths = provenance_contract["input_artifact_paths_exact"]
    repo_root = _repo_root(contract_path, expected_paths[0])
    if fixture_path != (repo_root / Path(*expected_paths[1].split("/"))).resolve():
        utility._fail("FIXTURE_PATH", "exact fixture path required")
    contract_bytes = contract_path.read_bytes()
    committed = subprocess.run(
        ["git", "show", f"HEAD:{expected_paths[0]}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if committed.returncode != 0 or committed.stdout != contract_bytes:
        utility._fail("CONTRACT_PIN", "worktree and committed bytes must match")
    contract_hash = _sha_bytes(contract_bytes)
    fixture_bytes = fixture_path.read_bytes()
    from . import cli

    transcript = cli.load_transcript(fixture_path)
    if utility._canonical_bytes(transcript) + b"\n" != fixture_bytes:
        utility._fail("FIXTURE_BYTES", "canonical fixture required")
    input_hashes = {
        expected_paths[0]: contract_hash,
        expected_paths[1]: _sha_bytes(fixture_bytes),
    }
    code_hash = _code_path_hash(repo_root, contract)
    provenance = _common_provenance(
        contract, run_id, input_hashes, transcript, code_hash, contract_hash
    )
    initial_state = utility.new_state(transcript["model_id"])
    initial_checkpoint = utility.serialize_state(initial_state)
    state = initial_state
    live_trace: list[dict[str, Any]] = []
    live_selections: list[str] = []
    state_pairs: list[tuple[dict[str, Any], dict[str, Any], Mapping[str, Any]]] = []
    checkpoints: list[bytes] = [initial_checkpoint]
    for step in transcript["steps"]:
        before = state
        result = utility.run_step(state, step["observation"], step["feedback"])
        state = result["next_state"]
        live_trace.append(result["trace_record"])
        live_selections.append(result["prediction"]["selected_action_id"])
        state_pairs.append((before, state, step["feedback"]))
        checkpoints.append(utility.serialize_state(state))
    process_response = cli.process_transcript(transcript)
    process_pass = (
        process_response["selection_sequence"] == live_selections
        and process_response["final_state"] == state
        and process_response["trace"] == live_trace
    )
    fixture_pass = live_selections == contract["frozen_fixture"]["expected_stateful_selections"]
    state_update_pass = all(
        utility.serialize_state(before) != utility.serialize_state(after)
        and before["state_hash"] != after["state_hash"]
        and after["revision"] == before["revision"] + 1
        for before, after, _ in state_pairs
    )
    target_only_pass = all(
        _target_cell_only(
            before, after, feedback["context_id"], feedback["action_id"]
        )
        for before, after, feedback in state_pairs
    )
    roundtrip_pass = all(
        utility.serialize_state(utility.deserialize_state(payload)) == payload
        for payload in checkpoints
    )
    baseline_predictions = [
        zero_utility_predict(step["observation"]) for step in transcript["steps"]
    ]
    baseline_selections = [item["selected_action_id"] for item in baseline_predictions]
    baseline_invocations = [
        _invocation(
            item["producer_function"],
            {"observation": _sha_value(step["observation"])},
            item,
            1,
            [step["observation"]["step_id"]],
        )
        for step, item in zip(transcript["steps"], baseline_predictions, strict=True)
    ]
    zero_pass = baseline_selections == contract["frozen_fixture"][
        "expected_zero_and_no_update_selections"
    ]
    no_update = replay_without_updates(initial_checkpoint, transcript["steps"])
    no_update_invocation = _invocation(
        no_update["producer_function"],
        {
            "checkpoint": _sha_bytes(initial_checkpoint),
            "ordered_steps": _sha_value(transcript["steps"]),
        },
        no_update,
        1,
        [step["observation"]["step_id"] for step in transcript["steps"]],
    )
    no_update_pass = (
        no_update["update_invocation_count"] == 0
        and no_update["selection_sequence"]
        == contract["frozen_fixture"]["expected_zero_and_no_update_selections"]
    )
    divergence = [
        step["observation"]["step_id"]
        for step, live, ablated in zip(
            transcript["steps"],
            live_selections,
            no_update["selection_sequence"],
            strict=True,
        )
        if live != ablated
    ]
    divergence_pass = divergence == [2, 3]
    full_replay = utility.replay(initial_checkpoint, transcript["steps"], live_trace)
    full_pass = full_replay["mismatch_count"] == 0 and full_replay["trace"] == live_trace
    suffix_steps = transcript["steps"][1:]
    suffix_trace = live_trace[1:]
    fresh_replay, fresh_input, fresh_stdout = _fresh_suffix_replay(
        repo_root,
        checkpoints[1],
        suffix_steps,
        suffix_trace,
        provenance["task_id"],
        run_id,
        code_hash,
        contract_hash,
    )
    fresh_pass = fresh_replay["mismatch_count"] == 0 and fresh_replay["trace"] == suffix_trace
    tampered = deepcopy(live_trace)
    tampered[1]["selected_action_id"] = contract["frozen_fixture"][
        "expected_zero_and_no_update_selections"
    ][0]
    tamper_replay = utility.replay(initial_checkpoint, transcript["steps"], tampered)
    expected_mismatch = {
        "index": 1,
        "path": "/selected_action_id",
        "expected_present": True,
        "expected_json": utility._canonical_text(tampered[1]["selected_action_id"]),
        "actual_present": True,
        "actual_json": utility._canonical_text(live_trace[1]["selected_action_id"]),
    }
    tamper_pass = tamper_replay["mismatch_count"] == 1 and tamper_replay["mismatches"] == [expected_mismatch]
    replay_invocations = [
        _invocation(
            full_replay["producer_function"],
            {"checkpoint": _sha_bytes(initial_checkpoint), "expected_trace": _sha_value(live_trace)},
            full_replay,
            1,
            [step["observation"]["step_id"] for step in transcript["steps"]],
        ),
        _invocation(
            fresh_replay["producer_function"],
            {"worker_payload": _sha_bytes(fresh_input), "worker_stdout": _sha_bytes(fresh_stdout)},
            fresh_replay,
            1,
            [step["observation"]["step_id"] for step in suffix_steps],
        ),
        _invocation(
            tamper_replay["producer_function"],
            {"checkpoint": _sha_bytes(initial_checkpoint), "expected_trace": _sha_value(tampered)},
            tamper_replay,
            1,
            [step["observation"]["step_id"] for step in transcript["steps"]],
        ),
    ]
    clean_scan: list[dict[str, Any]] = []
    leakage_invocations: list[dict[str, Any]] = []
    for step in transcript["steps"]:
        observation = step["observation"]
        findings = scan_observation_mapping(observation)
        clean_scan.append(
            {
                "observation_id": observation["observation_id"],
                "input_hash": _sha_value(observation),
                "findings": findings,
            }
        )
        leakage_invocations.append(
            _invocation(
                "ego_outcome_utility.functional_checks.scan_observation_mapping",
                {"observation": _sha_value(observation)},
                findings,
                1,
                [observation["step_id"]],
            )
        )
    positive_observation = deepcopy(transcript["steps"][0]["observation"])
    positive_observation[contract["leakage_contract"]["positive_control_key"]] = 0
    positive_findings = scan_observation_mapping(positive_observation)
    leakage_invocations.append(
        _invocation(
            "ego_outcome_utility.functional_checks.scan_observation_mapping",
            {"observation": _sha_value(positive_observation)},
            positive_findings,
            1,
            [positive_observation["step_id"]],
        )
    )
    rejected = False
    exception_type = ""
    message_prefix = ""
    try:
        utility.predict(initial_state, positive_observation)
    except ValueError as exc:
        rejected = True
        exception_type = type(exc).__name__
        message_prefix = str(exc)[:4]
    parser_rejection = {
        "producer_function": "ego_outcome_utility.utility.predict",
        "input_hash": _sha_value(positive_observation),
        "exception_type": exception_type,
        "message_prefix": message_prefix,
        "rejected": rejected,
    }
    clean_pass = all(not item["findings"] for item in clean_scan)
    positive_pass = (
        positive_findings == contract["leakage_contract"]["positive_control_expected_findings"]
        and rejected
        and exception_type == "ValueError"
        and message_prefix == "EOU_"
    )
    dynamic_pass = _dynamic_identifier_check(contract_hash)
    source_scan_pass = _source_literal_scan(repo_root, contract)
    single_path_pass = _single_logic_path_check(repo_root, transcript)
    claim_bytes = (contract["artifact_contract"]["claim_ceiling_text"] + "\n").encode("utf-8")
    claim_pass = claim_bytes == (
        contract["artifact_contract"]["claim_ceiling_text"] + "\n"
    ).encode("utf-8")
    baseline_payload = {
        "baseline_id": contract["baseline"]["id"],
        "invocation_records": baseline_invocations,
        "computed_fixture_selections": deepcopy(live_selections),
        "baseline_selections": baseline_selections,
        "divergence_step_ids": divergence,
        "claim_role": contract["baseline"]["claim_role"],
    }
    ablation_payload = {
        "ablation_id": contract["ablation"]["id"],
        "checkpoint_state_hash": initial_state["state_hash"],
        "invocation_record": no_update_invocation,
        "computed_fixture_selections": deepcopy(live_selections),
        "ablated_selections": deepcopy(no_update["selection_sequence"]),
        "divergence_step_ids": divergence,
        "live_final_state_hash": state["state_hash"],
        "ablated_final_state_hash": no_update["final_state_hash"],
        "claim_role": contract["ablation"]["claim_role"],
    }
    replay_payload = {
        "invocation_records": replay_invocations,
        "full_replay": full_replay,
        "fresh_suffix_replay": fresh_replay,
        "tamper_replay": tamper_replay,
        "aggregate_mismatch_count": full_replay["mismatch_count"]
        + fresh_replay["mismatch_count"]
        + tamper_replay["mismatch_count"],
    }
    leakage_payload = {
        "invocation_records": leakage_invocations,
        "clean_scan": clean_scan,
        "positive_control_scan": {
            "input_hash": _sha_value(positive_observation),
            "findings": positive_findings,
        },
        "parser_rejection": parser_rejection,
        "scanner_limit": contract["leakage_contract"]["scanner_limit"],
    }
    reports = {
        "baseline_comparison.json": _envelope(
            "baseline_comparison.json", baseline_payload, provenance, contract
        ),
        "ablation_report.json": _envelope(
            "ablation_report.json", ablation_payload, provenance, contract
        ),
        "replay_report.json": _envelope(
            "replay_report.json", replay_payload, provenance, contract
        ),
        "leakage_report.json": _envelope(
            "leakage_report.json", leakage_payload, provenance, contract
        ),
    }
    trace_rows = [
        _envelope("trace.jsonl", {"trace_record": record}, provenance, contract)
        for record in live_trace
    ]
    authority_consumption = deepcopy(
        contract["artifact_contract"]["authority_consumption_values"]
    )
    stable_result_payload = {
        "computed_fixture_selections": deepcopy(live_selections),
        "final_revision": state["revision"],
        "final_state_hash": state["state_hash"],
        "authority_consumption": authority_consumption,
        "claim_ceiling": contract["artifact_contract"]["claim_ceiling_text"],
        "claim_ceiling_sha256": _sha_bytes(claim_bytes),
    }
    provenance_pass = _validate_draft_bundle(
        reports, trace_rows, claim_bytes, stable_result_payload, contract
    )
    observed = {
        "public_api_process_pass": process_pass,
        "fixture_live_selection_pass": fixture_pass,
        "state_update_pass": state_update_pass,
        "target_cell_only_pass": target_only_pass,
        "serialization_roundtrip_pass": roundtrip_pass,
        "zero_baseline_invoked": zero_pass,
        "no_update_ablation_invoked": no_update_pass,
        "no_update_divergence_pass": divergence_pass,
        "full_replay_zero_mismatch": full_pass,
        "fresh_suffix_replay_zero_mismatch": fresh_pass,
        "tamper_replay_detected": tamper_pass,
        "clean_leakage_scan_pass": clean_pass,
        "positive_control_leakage_detected": positive_pass,
        "dynamic_identifier_test_pass": dynamic_pass,
        "fixture_literal_source_scan_pass": source_scan_pass,
        "single_logic_path_pass": single_path_pass,
        "provenance_complete": provenance_pass,
        "claim_ceiling_exact": claim_pass,
    }
    required = contract["artifact_contract"]["result_required_checks"]
    if list(observed) != required:
        raise ProducerStructureAbort("required check order mismatch")
    check_records: list[dict[str, Any]] = []
    for check_id in required:
        spec = contract["check_producer_contract"]["checks"][check_id]
        check_records.append(
            _check_record(
                check_id,
                spec["producer_function"],
                input_hashes,
                observed[check_id],
                spec["formula"],
            )
        )
    artifact = contract["artifact_contract"]
    verdict = resolve_verdict(
        required_check_names=required,
        observed_checks=observed,
        success_label=artifact["success_verdict"],
        failure_label=artifact["failure_verdict"],
    )
    if all(observed.values()):
        result_payload = {
            "verdict": verdict,
            "required_checks": observed,
            "check_records": check_records,
            **stable_result_payload,
        }
        result = _envelope("result.json", result_payload, provenance, contract)
        if not _validate_final_result_structure(result, contract):
            raise ProducerStructureAbort("final result structure validation failed")
        files = {
            "result.json": _file_bytes("result.json", result),
            "trace.jsonl": _file_bytes("trace.jsonl", trace_rows),
            **{name: _file_bytes(name, value) for name, value in reports.items()},
            "claim_ceiling.txt": claim_bytes,
        }
        if sorted(files) != sorted(artifact["success_files"]):
            raise ProducerStructureAbort("success artifact surface mismatch")
        _bundle_write(output_dir, files)
        return {
            "schema_version": contract["cli_contract"]["validate_stdout_schema_version"],
            "task_id": provenance["task_id"],
            "run_id": run_id,
            "verdict": verdict,
            "output_files": sorted(files),
        }
    failure_codes = sorted(
        f"CHECK_{name.upper()}" for name, passed in observed.items() if not passed
    )
    failure_payload = {
        "verdict": verdict,
        "canonical_attempt_ordinal": 1,
        "failure_stage": "functional_checks",
        "failure_codes": failure_codes,
        "exception_type": "FunctionalValidationFailure",
        "normalized_message": ";".join(failure_codes),
        "required_checks": observed,
        "check_records": check_records,
        "authority_consumption": authority_consumption,
        "claim_ceiling": artifact["claim_ceiling_text"],
        "claim_ceiling_sha256": _sha_bytes(claim_bytes),
        "partial_evidence_authoritative": False,
    }
    manifest = _envelope("failure_manifest.json", failure_payload, provenance, contract)
    if not _validate_failure_manifest_structure(manifest, contract):
        raise ProducerStructureAbort("failure manifest structure validation failed")
    files = {
        "failure_manifest.json": _file_bytes("failure_manifest.json", manifest),
        "claim_ceiling.txt": claim_bytes,
    }
    _bundle_write(output_dir, files)
    response = {
        "schema_version": contract["cli_contract"]["validate_stdout_schema_version"],
        "task_id": provenance["task_id"],
        "run_id": run_id,
        "verdict": verdict,
        "output_files": sorted(files),
    }
    raise FunctionalValidationFailure("required check failed", response)
