from __future__ import annotations

from collections import deque
from copy import deepcopy
from pathlib import Path
import base64
import binascii
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, microworld, predictive_control, store as v2_store
from labs.ego_life_playground_v0.predictive_control import FEATURE_INDEX, FEATURE_NAMES


_QUOTIENT_DROP_NAMES = ("front_wall", "front_occluded")
_QUOTIENT_DROP_INDICES = tuple(FEATURE_INDEX[name] for name in _QUOTIENT_DROP_NAMES)
QUOTIENT_FEATURE_NAMES = tuple(
    name for name in FEATURE_NAMES if name not in _QUOTIENT_DROP_NAMES
)
_FRONT_SUM_NAMES = (
    "front_empty",
    "front_wall",
    "front_v0",
    "front_v1",
    "front_v2",
    "front_v3",
    "front_v4",
)
_PRIVATE_FIELD_NAMES = frozenset(
    {
        "artifact_hash",
        "cause",
        "cause_identity",
        "file_path",
        "future_observation",
        "global_coordinates",
        "global_position",
        "loss",
        "objects_by_cause",
        "panel_truth",
        "policy_id",
        "private_map",
        "private_path",
        "private_position",
        "run_id",
        "run_seed",
        "seed",
        "seed_id",
        "target_reason",
        "token_mapping",
        "verdict",
        "world_id",
        "world_position",
    }
)
_BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")
_PRIVATE_BFS_TARGETS = frozenset({"v0", "v1", "v2", "v3", "v4", "empty", "wall"})
_PRIVATE_BFS_ACTIONS = (
    "turn_left",
    "turn_right",
    "move_forward",
    "interact",
    "rest",
)
REQUIRED_PROVENANCE_SOURCE_PATHS = (
    "docs/codex/tasks/EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H.md",
    "docs/codex/tasks/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/COLLISION_RECORD.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/IMPLEMENTATION_PLAN.md",
    "scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py",
    "scripts/codex/tests/test_verify_ego_v2_acquisition_benchmark_admission_001h_r1.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/microworld.py",
    "labs/ego_life_playground_v0/predictive_control.py",
    "labs/ego_life_playground_v0/store.py",
)
REQUIRED_PROVENANCE_INPUT_PATHS = (
    "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/result.json",
    "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p0_cross_v1.sqlite3",
    "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p2_vertical_v1.sqlite3",
    "artifacts/EGO-V2-P1-ADDITIVE-PREDICTION-HEADROOM-DIAGNOSTIC-001C-R4/result.json",
)
REQUIRED_PROVENANCE_DEPENDENCY_PATHS = (
    "requirements-ego-v2.txt",
)

FROZEN_CONTEXT_SPECS = (
    {
        "context_id": "p0_cross_v1:world=52:policy=711",
        "layout_id": "p0_cross_v1",
        "world_seed": 52,
        "policy_seed": 711,
        "control_db_relpath": "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p0_cross_v1.sqlite3",
        "action_budget": 89,
        "panel_rollout_ids": [9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
        "context_id": "p2_vertical_v1:world=54:policy=711",
        "layout_id": "p2_vertical_v1",
        "world_seed": 54,
        "policy_seed": 711,
        "control_db_relpath": "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p2_vertical_v1.sqlite3",
        "action_budget": 89,
        "panel_rollout_ids": [9, 10, 11, 12, 13, 14, 15, 16],
    },
)
_STAGE_ALLOWLIST = frozenset({"control", "witness", "panel"})

TRAINING_SUPPORT_STRATA = (
    {"stratum_id": "interact::v0::interacted", "action": "interact", "target_front_token": "v0", "outcome_type": "interacted"},
    {"stratum_id": "interact::v1::interacted", "action": "interact", "target_front_token": "v1", "outcome_type": "interacted"},
    {"stratum_id": "interact::v2::interacted", "action": "interact", "target_front_token": "v2", "outcome_type": "interacted"},
    {"stratum_id": "interact::v3::interacted", "action": "interact", "target_front_token": "v3", "outcome_type": "interacted"},
    {"stratum_id": "interact::v4::interacted", "action": "interact", "target_front_token": "v4", "outcome_type": "interacted"},
    {"stratum_id": "interact::no_object", "action": "interact", "target_front_token": "empty", "outcome_type": "no_object"},
    {"stratum_id": "move_forward::moved", "action": "move_forward", "target_front_token": "empty", "outcome_type": "moved"},
    {"stratum_id": "move_forward::blocked", "action": "move_forward", "target_front_token": "wall", "outcome_type": "blocked"},
    {"stratum_id": "rest::rested", "action": "rest", "target_front_token": None, "outcome_type": "rested"},
    {"stratum_id": "turn_left::turned", "action": "turn_left", "target_front_token": None, "outcome_type": "turned"},
    {"stratum_id": "turn_right::turned", "action": "turn_right", "target_front_token": None, "outcome_type": "turned"},
)




def _canonical_hashable_context_spec(spec: Any) -> dict[str, Any]:
    return deepcopy(dict(spec))


def _is_frozen_context_spec(spec: Any) -> bool:
    candidate = engine.canonical_hash(_canonical_hashable_context_spec(spec))
    return candidate in {engine.canonical_hash(item) for item in FROZEN_CONTEXT_SPECS}


def _stage_request(stage: str, context_spec: dict[str, Any], parent_pid: int, control_receipt=None) -> dict[str, Any]:
    base = {
        "stage": stage,
        "context_spec": _canonical_hashable_context_spec(context_spec),
        "parent_pid": int(parent_pid),
    }
    if stage == "witness":
        if control_receipt is None:
            raise ValueError("stage witness requires validated control receipt")
        control_payload = control_receipt["payload"]
        prefix = control_payload.get("prefix")
        if isinstance(prefix, dict):
            max_life_index = int(prefix["max_life_index"])
            max_respawn_count = int(prefix["respawn_count"])
        else:
            max_life_index = int(control_payload["max_life_index"])
            max_respawn_count = int(control_payload["max_respawn_count"])
        base["control_dependency_digest"] = str(control_receipt["payload_digest"])
        base["control_bounds"] = {
            "max_life_index": max_life_index,
            "max_respawn_count": max_respawn_count,
        }
    nonce = engine.canonical_hash(base)
    return {**base, "request_nonce": nonce}


def _internal_stage_payload(stage: str, request: dict[str, Any]):
    context_spec = request["context_spec"]
    if stage == "control":
        return extract_banked_control(REPO_ROOT / context_spec["control_db_relpath"], action_budget=int(context_spec["action_budget"]))
    if stage == "witness":
        bounds = request["control_bounds"]
        return run_privileged_witness(
            context_id=context_spec["context_id"],
            layout_id=context_spec["layout_id"],
            world_seed=int(context_spec["world_seed"]),
            policy_seed=int(context_spec["policy_seed"]),
            action_budget=int(context_spec["action_budget"]),
            max_life_index=int(bounds["max_life_index"]),
            max_respawn_count=int(bounds["max_respawn_count"]),
        )
    if stage == "panel":
        return build_deterministic_panel(
            context_id=context_spec["context_id"],
            layout_id=context_spec["layout_id"],
            world_seed=int(context_spec["world_seed"]),
            policy_seed=int(context_spec["policy_seed"]),
            panel_rollout_ids=tuple(context_spec["panel_rollout_ids"]),
        )
    raise ValueError("stage is not allowed")


def _internal_stage_probe(stage: str, request_path: str, output_path: str, parent_pid: int, request_nonce: str) -> int:
    request = _load_canonical_json_file(Path(request_path))
    expected_request = _stage_request(stage, request["context_spec"], int(parent_pid), control_receipt={"payload": request.get("control_bounds", {}), "payload_digest": request.get("control_dependency_digest")} if stage == "witness" else None)
    if request != expected_request:
        raise ValueError("stage request mismatch")
    if request["request_nonce"] != request_nonce:
        raise ValueError("stage nonce mismatch")
    payload = _internal_stage_payload(stage, request)
    receipt = {
        "stage": stage,
        "context_spec": request["context_spec"],
        "parent_pid": int(parent_pid),
        "child_pid": os.getpid(),
        "python_executable": sys.executable,
        "runtime_receipt": runtime_receipt(),
        "request_nonce": request_nonce,
        "request_digest": engine.canonical_hash(request),
        "payload": payload,
        "payload_digest": engine.canonical_hash(payload),
        "request_path": request_path,
        "output_path": output_path,
    }
    if stage == "witness":
        receipt["control_dependency_digest"] = request["control_dependency_digest"]
        receipt["control_bounds"] = deepcopy(request["control_bounds"])
    Path(output_path).write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps({"stage": stage, "payload_digest": receipt["payload_digest"]}, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


def spawn_context_stage(stage: str, spec, control_receipt=None) -> dict[str, Any]:
    if stage not in _STAGE_ALLOWLIST:
        raise ValueError("stage is not allowed")
    context_spec = _canonical_hashable_context_spec(spec)
    if not _is_frozen_context_spec(context_spec):
        raise ValueError("stage context spec is not frozen")
    validated_control = None
    if stage == "witness":
        if control_receipt is None:
            raise ValueError("stage witness requires control receipt")
        validate_context_stage_receipt(control_receipt)
        if control_receipt.get("stage") != "control":
            raise ValueError("stage receipt must be control")
        if control_receipt.get("context_spec") != context_spec:
            raise ValueError("stage receipt context spec mismatch")
        validated_control = control_receipt
    request = _stage_request(stage, context_spec, os.getpid(), control_receipt=validated_control)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        request_path = tmp / "request.json"
        output_path = tmp / "output.json"
        request_path.write_text(json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        command = [
            sys.executable,
            "-I",
            "-B",
            str(Path(__file__).resolve()),
            "--internal-stage",
            stage,
            str(request_path),
            str(output_path),
            str(os.getpid()),
            request["request_nonce"],
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        receipt = json.loads(output_path.read_text(encoding="utf-8"))
    receipt["command"] = command
    return receipt


def validate_context_stage_receipt(receipt) -> bool:
    if receipt.get("stage") not in _STAGE_ALLOWLIST:
        raise ValueError("stage receipt stage mismatch")
    context_spec = receipt.get("context_spec")
    if not _is_frozen_context_spec(context_spec):
        raise ValueError("stage receipt frozen context mismatch")
    control_stub = None
    if receipt.get("stage") == "witness":
        control_dependency_digest = receipt.get("control_dependency_digest")
        control_bounds = deepcopy(receipt.get("control_bounds"))
        if not isinstance(control_bounds, dict) or set(control_bounds) != {"max_life_index", "max_respawn_count"}:
            raise ValueError("stage receipt control bounds mismatch")
        if int(receipt["payload"]["max_life_index"]) > int(control_bounds["max_life_index"]) or int(receipt["payload"]["respawn_count"]) > int(control_bounds["max_respawn_count"]):
            raise ValueError("stage receipt witness bounds exceeded")
        control_stub = {"payload": control_bounds, "payload_digest": control_dependency_digest}
    expected_request = _stage_request(str(receipt["stage"]), context_spec, int(receipt["parent_pid"]), control_receipt=control_stub)
    if str(receipt.get("request_nonce")) != expected_request["request_nonce"]:
        raise ValueError("stage receipt nonce mismatch")
    if str(receipt.get("request_digest")) != engine.canonical_hash(expected_request):
        raise ValueError("stage receipt request digest mismatch")
    if str(receipt.get("payload_digest")) != engine.canonical_hash(receipt.get("payload")):
        raise ValueError("stage receipt payload digest mismatch")
    if int(receipt.get("child_pid")) == int(receipt.get("parent_pid")):
        raise ValueError("stage receipt child process mismatch")
    if str(receipt.get("python_executable")) != sys.executable:
        raise ValueError("stage receipt executable mismatch")
    if receipt.get("runtime_receipt") != runtime_receipt():
        raise ValueError("stage receipt runtime mismatch")
    expected_command = [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--internal-stage",
        str(receipt["stage"]),
        str(receipt["request_path"]),
        str(receipt["output_path"]),
        str(receipt["parent_pid"]),
        str(receipt["request_nonce"]),
    ]
    if list(receipt.get("command", [])) != expected_command:
        raise ValueError("stage receipt command mismatch")
    return True


def _canonical_json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

def _load_canonical_json_file(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _internal_digest_probe(payload_path: str, parent_pid: int, request_nonce: str) -> int:
    input_path = Path(payload_path)
    payload = _load_canonical_json_file(input_path)
    receipt = {
        "parent_pid": int(parent_pid),
        "child_pid": os.getpid(),
        "python_executable": sys.executable,
        "input_sha256": _sha256_file(input_path),
        "payload_digest": engine.canonical_hash(payload),
        "request_nonce": request_nonce,
    }
    sys.stdout.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0


def spawn_fresh_digest_probe(path) -> dict[str, object]:
    input_path = Path(path)
    request_nonce = engine.canonical_hash({"path": str(input_path.resolve()), "parent_pid": os.getpid(), "input_sha256": _sha256_file(input_path)})
    command = [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--internal-digest",
        str(input_path),
        str(os.getpid()),
        request_nonce,
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    receipt = json.loads(completed.stdout)
    receipt["command"] = command
    return receipt


def validate_fresh_digest_receipt(path, receipt) -> bool:
    input_path = Path(path)
    payload = _load_canonical_json_file(input_path)
    expected_sha = _sha256_file(input_path)
    expected_digest = engine.canonical_hash(payload)
    expected_nonce = engine.canonical_hash({"path": str(input_path.resolve()), "parent_pid": os.getpid(), "input_sha256": expected_sha})
    command = [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--internal-digest",
        str(input_path),
        str(os.getpid()),
        expected_nonce,
    ]
    if int(receipt["child_pid"]) == int(receipt["parent_pid"]):
        raise ValueError("child process pid must differ from parent")
    if str(receipt["python_executable"]) != sys.executable:
        raise ValueError("python executable mismatch")
    if str(receipt["input_sha256"]) != expected_sha:
        raise ValueError("input sha mismatch")
    if str(receipt["payload_digest"]) != expected_digest:
        raise ValueError("payload digest mismatch")
    if list(receipt["command"]) != command:
        raise ValueError("command mismatch")
    if str(receipt.get("request_nonce")) != expected_nonce:
        raise ValueError("request nonce mismatch")
    return True


def build_artifact_manifest(packet_dir) -> dict[str, object]:
    packet = Path(packet_dir)
    files = {}
    for item in sorted(packet.rglob("*")):
        if not item.is_file() or item.name == "artifact_manifest.json":
            continue
        rel = item.relative_to(packet).as_posix()
        data = item.read_bytes()
        files[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return {"files": files}


def verify_artifact_manifest(packet_dir) -> bool:
    packet = Path(packet_dir)
    manifest_path = packet / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = build_artifact_manifest(packet)
    if current != manifest:
        raise ValueError("artifact manifest mismatch")
    return True


def write_formal_packet(packet, bundle) -> dict[str, object]:
    packet_path = Path(packet)
    if packet_path.exists():
        raise ValueError("output directory")
    packet_path.mkdir(parents=True)
    try:
        contexts = dict(bundle["contexts"])
        control_rows = []
        witness_rows = []
        panel_rows = []
        support_contexts = {}
        panel_manifest_contexts = {}
        ablation_contexts = {}
        recompute_contexts = {}
        for context_id, context in contexts.items():
            control_prefix_records = [dict(row, context_id=context_id) for row in context["control"]["prefix_records"]]
            control_rows.extend(control_prefix_records)
            witness_rows.extend(deepcopy(context["witness"]["rows"]))
            panel_rows.extend(deepcopy(context["panel"]["rows"]))
            support_contexts[context_id] = {
                "control_prefix": deepcopy(context["control"]["prefix"]),
                "witness_support": deepcopy(context["witness"]["support_report"]),
                "panel_support": deepcopy(context["panel"].get("support_report", {})),
                "panel_cell_support": deepcopy(context["panel"].get("cell_support_report", {})),
            }
            panel_manifest_contexts[context_id] = {
                "panel_rollout_ids": deepcopy(context["panel"]["panel_rollout_ids"]),
                "target_order": deepcopy(context["panel"]["target_order"]),
                "rollouts": deepcopy(context["panel"]["rollouts"]),
                "raw_checkpoints": deepcopy(context["panel"]["raw_checkpoints"]),
                "retained_checkpoints": deepcopy(context["panel"]["retained_checkpoints"]),
                "rank_reports": deepcopy(context["panel"]["rank_reports"]),
                "construction_complete": context["panel"]["construction_complete"],
                "panel_capacity_admitted": context["panel"]["panel_capacity_admitted"],
                "panel_hash": context["panel"]["panel_hash"],
            }
            ablation_contexts[context_id] = deepcopy(context["witness"]["ablation_report"])
            recompute_contexts[context_id] = deepcopy(bundle["independent_reports"][context_id])

        support_report = {
            "contexts": support_contexts,
            "all_contexts_control_envelope_comparable": all(bool(context["witness"]["control_envelope_comparable"]) for context in contexts.values()),
            "all_contexts_witness_found": all(bool(context["witness"]["witness_found"]) for context in contexts.values()),
            "all_contexts_panel_capacity_admitted": all(bool(context["panel"]["panel_capacity_admitted"]) for context in contexts.values()),
        }
        panel_manifest = {"contexts": panel_manifest_contexts}
        ablation_report = {"contexts": ablation_contexts}
        leakage_report = deepcopy(bundle["leakage_report"])
        recompute_report = {
            "contexts": recompute_contexts,
            "fresh_recompute_report": deepcopy(bundle["fresh_recompute_report"]),
            "independent_reports": deepcopy(bundle["independent_reports"]),
            "provenance_report": deepcopy(bundle["provenance_report"]),
            "pre_run_provenance_document": deepcopy(bundle.get("provenance_document", {})),
            "pre_run_observation": deepcopy(bundle.get("pre_run_observation", {})),
            "tamper_report": deepcopy(bundle["tamper_report"]),
            "validity": deepcopy(bundle["validity"]),
        }
        adjudication = deepcopy(bundle["adjudication"])
        verdict = adjudication["verdict"]
        claim_ceiling = (
            "This packet is limited to privileged evaluator old-context benchmark admission evidence only; "
            "it is not evidence of a legal learner, prediction success, survival generalization, heldout effect, AGI, consciousness, or production readiness."
        )
        result = {
            "task_id": "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1",
            "producer_function": "scripts.codex.verify_ego_v2_acquisition_benchmark_admission_001h_r1.run_formal",
            "aggregation_rule": "all frozen contexts by conjunction, followed by the frozen fail-closed verdict priority",
            "verdict": verdict,
            "checks": {
                "provenance_clean": adjudication["provenance_clean"],
                "control_envelope_comparable": adjudication["control_envelope_comparable"],
                "privileged_support_witness_found": adjudication["privileged_support_witness_found"],
                "deterministic_panel_capacity_admitted": adjudication["deterministic_panel_capacity_admitted"],
                "all_tamper_controls_rejected": bundle["tamper_report"]["all_tamper_controls_rejected"],
                "fresh_recompute_equal": bundle["fresh_recompute_report"]["equal"],
                "leakage_clean": bundle["leakage_report"]["all_clean"],
                "positive_controls_detected": bundle["leakage_report"]["all_positive_controls_detected"],
            },
            "context_count": len(contexts),
            "control_row_count": len(control_rows),
            "privileged_witness_row_count": len(witness_rows),
            "panel_row_count": len(panel_rows),
            "model_training_executed": False,
            "fresh_worlds_consumed": [],
            "heldout_effect_adjudicated": False,
            "implementation_commit": bundle.get("provenance_document", {}).get("implementation_commit"),
            "provenance_commit": bundle.get("provenance_report", {}).get("provenance_commit"),
            "engine_code_path_hash": bundle.get("provenance_document", {}).get("engine_code_path_hash"),
            "runtime_receipt": deepcopy(bundle.get("provenance_document", {}).get("runtime_receipt")),
            "context_specs": deepcopy(bundle.get("provenance_document", {}).get("context_specs", list(FROZEN_CONTEXT_SPECS))),
            "source_hashes": deepcopy(bundle.get("provenance_document", {}).get("source_hashes", {})),
            "input_hashes": deepcopy(bundle.get("provenance_document", {}).get("input_hashes", {})),
            "dependency_hashes": deepcopy(bundle.get("provenance_document", {}).get("dependency_hashes", {})),
            "claim_ceiling": claim_ceiling,
        }
        failure_manifest = None
        if verdict != "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT":
            failure_manifest = {
                "task_id": result["task_id"],
                "verdict": verdict,
                "failure_reasons": deepcopy(adjudication["failure_reasons"]),
            }

        def write_json(name, value):
            (packet_path / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        def write_jsonl(name, rows):
            with (packet_path / name).open("w", encoding="utf-8", newline="\n") as handle:
                for row in rows:
                    handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        write_json("result.json", result)
        write_jsonl("control_rows.jsonl", control_rows)
        write_jsonl("privileged_witness_rows.jsonl", witness_rows)
        write_jsonl("panel_rows.jsonl", panel_rows)
        write_json("support_report.json", support_report)
        write_json("panel_manifest.json", panel_manifest)
        write_json("ablation_report.json", ablation_report)
        write_json("leakage_report.json", leakage_report)
        write_json("recompute_report.json", recompute_report)
        if failure_manifest is not None:
            write_json("failure_manifest.json", failure_manifest)
        (packet_path / "claim_ceiling.txt").write_text(claim_ceiling + "\n", encoding="utf-8")
        manifest = build_artifact_manifest(packet_path)
        write_json("artifact_manifest.json", manifest)
        return result
    except Exception:
        if packet_path.exists():
            for child in sorted(packet_path.rglob('*'), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    try:
                        child.rmdir()
                    except OSError:
                        pass
            try:
                packet_path.rmdir()
            except OSError:
                pass
        raise


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _verify_row_derived_packet_semantics(packet_path: Path) -> None:
    support = _load_canonical_json_file(packet_path / "support_report.json")
    panel_manifest = _load_canonical_json_file(packet_path / "panel_manifest.json")
    ablation = _load_canonical_json_file(packet_path / "ablation_report.json")
    control_rows = _read_jsonl(packet_path / "control_rows.jsonl")
    witness_rows = _read_jsonl(packet_path / "privileged_witness_rows.jsonl")
    panel_rows = _read_jsonl(packet_path / "panel_rows.jsonl")
    support_contexts = support.get("contexts", {})
    manifest_contexts = panel_manifest.get("contexts", {})
    ablation_contexts = ablation.get("contexts", {})
    context_ids = set(support_contexts)
    if context_ids != set(manifest_contexts) or context_ids != set(ablation_contexts):
        raise ValueError("formal packet semantic context mismatch")

    def grouped(rows):
        result = {context_id: [] for context_id in context_ids}
        for row in rows:
            context_id = row.get("context_id")
            if context_id not in result:
                raise ValueError("formal packet semantic row context mismatch")
            result[context_id].append(row)
        return result

    controls_by_context = grouped(control_rows)
    witnesses_by_context = grouped(witness_rows)
    panels_by_context = grouped(panel_rows)
    floors = {"v0": 8, "v1": 8, "v2": 8, "v3": 8, "v4": 8, "empty": 16, "wall": 16}
    target_order = _panel_target_order()

    for context_id in sorted(context_ids):
        context_support = support_contexts[context_id]
        control_prefix = context_support.get("control_prefix", {})
        recomputed_prefix = summarize_control_prefix(
            controls_by_context[context_id],
            action_budget=int(control_prefix.get("action_count", -1)),
        )
        if recomputed_prefix != control_prefix:
            raise ValueError("formal packet semantic control prefix mismatch")

        context_witness_rows = witnesses_by_context[context_id]
        witness_counts = _support_counts_from_rows(context_witness_rows)
        expected_witness_support = {
            "stratum_counts": witness_counts,
            "all_supported": all(value >= 4 for value in witness_counts.values()),
        }
        if context_support.get("witness_support") != expected_witness_support:
            raise ValueError("formal packet semantic witness support mismatch")
        trajectory_hash = engine.canonical_hash(context_witness_rows)
        context_ablation = ablation_contexts[context_id]
        expected_ablation = {
            "reorder_count": 0,
            "trajectory_hash_changed": False,
            "main_trajectory_hash": trajectory_hash,
            "no_cause_trajectory_hash": trajectory_hash,
        }
        if context_ablation != expected_ablation:
            raise ValueError("formal packet semantic ablation mismatch")

        manifest = manifest_contexts[context_id]
        if manifest.get("panel_rollout_ids") != list(range(9, 17)):
            raise ValueError("formal packet semantic panel rollout mismatch")
        if manifest.get("target_order") != target_order:
            raise ValueError("formal packet semantic panel target order mismatch")
        rollouts = manifest.get("rollouts", [])
        if [item.get("panel_rollout_id") for item in rollouts] != list(range(9, 17)):
            raise ValueError("formal packet semantic panel rollout receipt mismatch")
        raw_checkpoints = manifest.get("raw_checkpoints", [])
        retained_checkpoints = manifest.get("retained_checkpoints", [])
        for checkpoint in raw_checkpoints + retained_checkpoints:
            checkpoint_projection = {
                "observation": checkpoint.get("observation"),
                "organism": checkpoint.get("organism"),
                "public_relative_belief": checkpoint.get("public_relative_belief"),
                "quotient_features": checkpoint.get("quotient_features"),
            }
            if checkpoint.get("checkpoint_hash") != engine.canonical_hash(checkpoint_projection):
                raise ValueError("formal packet semantic checkpoint hash mismatch")
        raw_counts = {token: sum(item.get("front_token") == token for item in raw_checkpoints) for token in floors}
        retained_counts = {token: sum(item.get("front_token") == token for item in retained_checkpoints) for token in floors}
        expected_panel_support = {
            "before_dedupe": raw_counts,
            "after_dedupe": retained_counts,
            "required_floors": floors,
            "passed": all(raw_counts[token] >= floor and retained_counts[token] >= floor for token, floor in floors.items()),
        }
        if context_support.get("panel_support") != expected_panel_support:
            raise ValueError("formal packet semantic panel support mismatch")
        retained_hashes = [item.get("checkpoint_hash") for item in retained_checkpoints]
        if len(retained_hashes) != len(set(retained_hashes)):
            raise ValueError("formal packet semantic panel dedupe mismatch")
        context_panel_rows = panels_by_context[context_id]
        rows_by_checkpoint = {checkpoint_hash: [] for checkpoint_hash in retained_hashes}
        for row in context_panel_rows:
            checkpoint_hash = row.get("checkpoint_hash")
            if checkpoint_hash not in rows_by_checkpoint:
                raise ValueError("formal packet semantic panel row checkpoint mismatch")
            rows_by_checkpoint[checkpoint_hash].append(row)
        if any(
            [row.get("selected_action") for row in rows] != list(engine.ACTIONS)
            for rows in rows_by_checkpoint.values()
        ):
            raise ValueError("formal packet semantic panel action expansion mismatch")
        cell_counts = {}
        for row in context_panel_rows:
            key = "::".join((context_id, row["selected_action"], row["front_token"], row["outcome_type"]))
            cell_counts[key] = cell_counts.get(key, 0) + 1
        expected_cell_support = {
            "cell_counts": cell_counts,
            "required_floor_by_cell": {key: floors[key.split("::")[-2]] for key in cell_counts},
            "passed": all(count >= floors[key.split("::")[-2]] for key, count in cell_counts.items()),
        }
        if context_support.get("panel_cell_support") != expected_cell_support:
            raise ValueError("formal packet semantic panel cell support mismatch")
        rank_reports = _rank_reports_from_rows(context_id, context_panel_rows)
        if manifest.get("rank_reports") != rank_reports:
            raise ValueError("formal packet semantic panel rank mismatch")
        construction_complete = len(rollouts) == 8 and all(item.get("complete") is True for item in rollouts)
        panel_capacity_admitted = bool(
            construction_complete
            and expected_panel_support["passed"]
            and expected_cell_support["passed"]
            and all(int(rank_reports[f"{context_id}::{action}"]["rank"]) == 13 for action in engine.ACTIONS)
        )
        if manifest.get("construction_complete") is not construction_complete or manifest.get("panel_capacity_admitted") is not panel_capacity_admitted:
            raise ValueError("formal packet semantic panel capacity mismatch")
        expected_panel_hash = engine.canonical_hash(
            {
                "rollouts": rollouts,
                "retained_checkpoint_hashes": retained_hashes,
                "rows": context_panel_rows,
                "support_report": expected_panel_support,
                "cell_support_report": expected_cell_support,
                "rank_reports": rank_reports,
                "panel_capacity_admitted": panel_capacity_admitted,
            }
        )
        if manifest.get("panel_hash") != expected_panel_hash:
            raise ValueError("formal packet semantic panel hash mismatch")


def verify_formal_packet(packet) -> dict[str, object]:
    packet_path = Path(packet)
    verify_artifact_manifest(packet_path)
    result = json.loads((packet_path / "result.json").read_text(encoding="utf-8"))
    verdict = result["verdict"]
    expected_files = {
        "result.json",
        "control_rows.jsonl",
        "privileged_witness_rows.jsonl",
        "panel_rows.jsonl",
        "support_report.json",
        "panel_manifest.json",
        "ablation_report.json",
        "leakage_report.json",
        "recompute_report.json",
        "claim_ceiling.txt",
        "artifact_manifest.json",
    }
    if verdict != "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT":
        expected_files.add("failure_manifest.json")
    actual_files = {item.name for item in packet_path.iterdir() if item.is_file()}
    if actual_files != expected_files:
        raise ValueError("formal packet file set mismatch")
    def count_jsonl(name):
        with (packet_path / name).open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    if result.get("task_id") != "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1":
        raise ValueError("formal packet result task mismatch")
    if count_jsonl("control_rows.jsonl") != int(result["control_row_count"]):
        raise ValueError("formal packet control row count mismatch")
    if count_jsonl("privileged_witness_rows.jsonl") != int(result["privileged_witness_row_count"]):
        raise ValueError("formal packet witness row count mismatch")
    if count_jsonl("panel_rows.jsonl") != int(result["panel_row_count"]):
        raise ValueError("formal packet panel row count mismatch")
    if "failure_manifest.json" in expected_files:
        failure_manifest = json.loads((packet_path / "failure_manifest.json").read_text(encoding="utf-8"))
        if failure_manifest.get("verdict") != verdict:
            raise ValueError("formal packet failure verdict mismatch")
    recompute = json.loads((packet_path / "recompute_report.json").read_text(encoding="utf-8"))
    leakage = json.loads((packet_path / "leakage_report.json").read_text(encoding="utf-8"))
    support = json.loads((packet_path / "support_report.json").read_text(encoding="utf-8"))
    checks = result.get("checks", {})
    provenance_document = recompute.get("pre_run_provenance_document", {})
    provenance_report = recompute.get("provenance_report", {})
    pre_run_observation = recompute.get("pre_run_observation", {})
    if result.get("model_training_executed") is not False:
        raise ValueError("formal packet semantic training firewall mismatch")
    if result.get("fresh_worlds_consumed") != []:
        raise ValueError("formal packet semantic fresh-world firewall mismatch")
    if result.get("heldout_effect_adjudicated") is not False:
        raise ValueError("formal packet semantic heldout firewall mismatch")
    if result.get("producer_function") != "scripts.codex.verify_ego_v2_acquisition_benchmark_admission_001h_r1.run_formal":
        raise ValueError("formal packet semantic producer mismatch")
    if result.get("implementation_commit") != provenance_document.get("implementation_commit"):
        raise ValueError("formal packet semantic implementation commit mismatch")
    if result.get("provenance_commit") != provenance_report.get("provenance_commit"):
        raise ValueError("formal packet semantic provenance commit mismatch")
    if result.get("engine_code_path_hash") != provenance_document.get("engine_code_path_hash"):
        raise ValueError("formal packet semantic code path mismatch")
    if result.get("runtime_receipt") != provenance_document.get("runtime_receipt"):
        raise ValueError("formal packet semantic runtime mismatch")
    if result.get("context_specs") != provenance_document.get("context_specs") or result.get("context_specs") != list(FROZEN_CONTEXT_SPECS):
        raise ValueError("formal packet semantic context specs mismatch")
    for field, required_paths in (
        ("source_hashes", REQUIRED_PROVENANCE_SOURCE_PATHS),
        ("input_hashes", REQUIRED_PROVENANCE_INPUT_PATHS),
        ("dependency_hashes", REQUIRED_PROVENANCE_DEPENDENCY_PATHS),
    ):
        result_map = result.get(field, {})
        document_map = provenance_document.get(field, {})
        observed_map = pre_run_observation.get(field, document_map)
        if set(result_map) != set(required_paths) or result_map != document_map or result_map != observed_map:
            raise ValueError(f"formal packet semantic {field} mismatch")
        if any(not (isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)) for value in result_map.values()):
            raise ValueError(f"formal packet semantic {field} malformed")
    if int(result.get("context_count", -1)) != len(support.get("contexts", {})):
        raise ValueError("formal packet semantic context count mismatch")
    semantic_checks = {
        "fresh_recompute_equal": recompute.get("fresh_recompute_report", {}).get("equal"),
        "all_tamper_controls_rejected": recompute.get("tamper_report", {}).get("all_tamper_controls_rejected"),
        "leakage_clean": leakage.get("all_clean"),
        "positive_controls_detected": leakage.get("all_positive_controls_detected"),
    }
    if any(type(value) is not bool or checks.get(key) is not value for key, value in semantic_checks.items()):
        raise ValueError("formal packet semantic check mismatch")
    fresh_report = recompute.get("fresh_recompute_report", {})
    fresh_contexts = fresh_report.get("contexts", {})
    if fresh_contexts:
        detail_equal = True
        for context_stages in fresh_contexts.values():
            if set(context_stages) != {"control", "witness", "panel"}:
                raise ValueError("formal packet semantic fresh stage mismatch")
            for stage in ("control", "witness", "panel"):
                stage_report = context_stages[stage]
                recomputed_equal = bool(
                    stage_report.get("first_payload_digest") == stage_report.get("second_payload_digest")
                    and stage_report.get("first_python_executable") == stage_report.get("second_python_executable")
                    and stage_report.get("first_runtime_receipt") == stage_report.get("second_runtime_receipt")
                    and stage_report.get("first_parent_pid") == stage_report.get("second_parent_pid")
                    and stage_report.get("first_child_pid") != stage_report.get("second_child_pid")
                )
                if stage_report.get("equal") is not recomputed_equal:
                    raise ValueError("formal packet semantic fresh receipt mismatch")
                detail_equal = detail_equal and recomputed_equal
        if fresh_report.get("equal") is not detail_equal:
            raise ValueError("formal packet semantic fresh aggregation mismatch")
    required_validity = {
        "pre_run_provenance_valid",
        "runtime_contract_satisfied",
        "source_hashes_match",
        "leakage_clean",
        "positive_controls_detected",
        "fresh_process_recompute_equal",
        "all_tamper_controls_rejected",
    }
    validity = recompute.get("validity", {})
    independent_reports = recompute.get("independent_reports", {})
    if set(validity) != required_validity or any(type(value) is not bool for value in validity.values()):
        raise ValueError("formal packet semantic validity mismatch")
    if set(independent_reports) != set(
        fresh_contexts or independent_reports
    ):
        raise ValueError("formal packet semantic recompute context mismatch")
    report_clean = True
    aggregate_checks = {
        "control_envelope_comparable": True,
        "privileged_support_witness_found": True,
        "deterministic_panel_capacity_admitted": True,
    }
    for context_id, report in independent_reports.items():
        report_clean = report_clean and all(
            report.get(key) is True
            for key in ("reported_values_match", "producer_receipts_valid", "hashes_valid")
        )
        check_map = report.get("check_map", {})
        for key in aggregate_checks:
            if type(check_map.get(key)) is not bool:
                raise ValueError("formal packet semantic independent check mismatch")
            aggregate_checks[key] = aggregate_checks[key] and check_map[key]
    expected_provenance_clean = all(validity.values()) and report_clean
    if checks.get("provenance_clean") is not expected_provenance_clean:
        raise ValueError("formal packet semantic provenance aggregation mismatch")
    if any(checks.get(key) is not value for key, value in aggregate_checks.items()):
        raise ValueError("formal packet semantic context aggregation mismatch")
    expected_support_aggregates = {
        "all_contexts_control_envelope_comparable": aggregate_checks["control_envelope_comparable"],
        "all_contexts_witness_found": aggregate_checks["privileged_support_witness_found"],
        "all_contexts_panel_capacity_admitted": aggregate_checks["deterministic_panel_capacity_admitted"],
    }
    if any(support.get(key) is not value for key, value in expected_support_aggregates.items()):
        raise ValueError("formal packet semantic support aggregation mismatch")
    expected_verdict = dispatch_verdict(
        checks.get("provenance_clean"),
        checks.get("control_envelope_comparable"),
        checks.get("privileged_support_witness_found"),
        checks.get("deterministic_panel_capacity_admitted"),
    )
    if expected_verdict != verdict:
        raise ValueError("formal packet semantic verdict mismatch")
    if (packet_path / "claim_ceiling.txt").read_text(encoding="utf-8").strip() != result.get("claim_ceiling"):
        raise ValueError("formal packet semantic claim ceiling mismatch")
    _verify_row_derived_packet_semantics(packet_path)
    return result

def run_formal(*, output_dir, provenance_path):
    output = Path(output_dir)
    provenance = Path(provenance_path)
    if output.exists():
        raise ValueError("output directory")
    if not provenance.exists():
        raise ValueError("pre-run provenance")

    document = _load_canonical_json_file(provenance)
    observation = collect_pre_run_observation(output_dir=output, provenance_path=provenance)
    provenance_report = validate_pre_run_provenance_document(document, observation)

    contexts = {}
    fresh_recompute_contexts = {}
    for spec in FROZEN_CONTEXT_SPECS:
        first_control = spawn_context_stage("control", spec)
        validate_context_stage_receipt(first_control)
        first_witness = spawn_context_stage("witness", spec, control_receipt=first_control)
        validate_context_stage_receipt(first_witness)
        first_panel = spawn_context_stage("panel", spec)
        validate_context_stage_receipt(first_panel)

        second_control = spawn_context_stage("control", spec)
        validate_context_stage_receipt(second_control)
        second_witness = spawn_context_stage("witness", spec, control_receipt=second_control)
        validate_context_stage_receipt(second_witness)
        second_panel = spawn_context_stage("panel", spec)
        validate_context_stage_receipt(second_panel)

        control_summary = summarize_fresh_stage_pair(first_control, second_control)
        witness_summary = summarize_fresh_stage_pair(first_witness, second_witness)
        panel_summary = summarize_fresh_stage_pair(first_panel, second_panel)
        fresh_recompute_contexts[spec["context_id"]] = {
            "control": control_summary,
            "witness": witness_summary,
            "panel": panel_summary,
        }

        contexts[spec["context_id"]] = {
            "control": deepcopy(first_control["payload"]),
            "witness": deepcopy(first_witness["payload"]),
            "panel": deepcopy(first_panel["payload"]),
        }

    independent_reports = {}
    row_scans = []
    positive_control_reports = {}
    for context_id, context in contexts.items():
        independent_reports[context_id] = independent_reduce_context(context_id=context_id, control=context["control"], witness=context["witness"], panel=context["panel"])
        for source_name, rows in (
            ("privileged_witness_rows", context["witness"].get("rows", [])),
            ("panel_rows", context["panel"].get("rows", [])),
        ):
            for row_index, row in enumerate(rows):
                projection = row.get("learner_projection")
                scan = scan_learner_projection(projection)
                row_scans.append(
                    {
                        "context_id": context_id,
                        "source": source_name,
                        "row_index": row_index,
                        "clean": scan.get("clean"),
                        "findings": deepcopy(scan.get("findings", [])),
                    }
                )
                schema_key = engine.canonical_hash(
                    sorted(projection.keys()) if isinstance(projection, dict) else [type(projection).__name__]
                )
                if schema_key not in positive_control_reports:
                    positive_control_reports[schema_key] = {
                        "projection_keys": sorted(projection.keys()) if isinstance(projection, dict) else None,
                        "report": run_leakage_positive_controls(projection),
                    }

    all_clean = bool(row_scans) and all(item["clean"] is True for item in row_scans)
    all_positive_controls_detected = bool(
        positive_control_reports
        and all(item["report"].get("all_positive_controls_detected") is True for item in positive_control_reports.values())
    )
    leakage_report = {
        "all_clean": all_clean,
        "all_positive_controls_detected": all_positive_controls_detected,
        "scanned_row_count": len(row_scans),
        "clean_row_count": sum(item["clean"] is True for item in row_scans),
        "row_scans": row_scans,
        "positive_control_report": deepcopy(next(iter(positive_control_reports.values()))["report"] if positive_control_reports else None),
        "positive_control_reports_by_projection_schema": deepcopy(positive_control_reports),
    }
    fresh_recompute_report = {
        "equal": all(summary[stage]["equal"] for summary in fresh_recompute_contexts.values() for stage in ("control", "witness", "panel")),
        "contexts": fresh_recompute_contexts,
    }
    source_hash_observed = observation.get("source_hashes", document.get("source_hashes", {}))
    if "source_hashes" in observation:
        source_hashes_match = validate_exact_source_hashes(document.get("source_hashes", {}), source_hash_observed)
    else:
        source_hashes_match = True
    tamper_report = run_tamper_controls(contexts=contexts, source_hashes=source_hash_observed, reported_verdict="")
    validity = {
        "pre_run_provenance_valid": bool(provenance_report.get("passed")),
        "runtime_contract_satisfied": bool(observation["runtime_receipt"].get("contract_satisfied")),
        "source_hashes_match": bool(source_hashes_match),
        "leakage_clean": leakage_report["all_clean"],
        "positive_controls_detected": leakage_report["all_positive_controls_detected"],
        "fresh_process_recompute_equal": fresh_recompute_report["equal"],
        "all_tamper_controls_rejected": bool(tamper_report.get("all_tamper_controls_rejected")),
    }
    adjudication = derive_adjudication(independent_reports, validity)
    bundle = {
        "contexts": contexts,
        "provenance_document": deepcopy(document),
        "pre_run_observation": deepcopy(observation),
        "provenance_report": provenance_report,
        "leakage_report": leakage_report,
        "independent_reports": independent_reports,
        "fresh_recompute_report": fresh_recompute_report,
        "tamper_report": tamper_report,
        "validity": validity,
        "adjudication": adjudication,
    }
    write_formal_packet(output, bundle)
    return verify_formal_packet(output)

def validate_exact_source_hashes(expected, observed) -> bool:
    expected_dict = dict(expected)
    observed_dict = dict(observed)
    def is_valid_hash(value):
        return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)
    if set(expected_dict) != set(observed_dict):
        raise ValueError("source hash key set mismatch")
    for key, expected_value in expected_dict.items():
        observed_value = observed_dict[key]
        if not is_valid_hash(expected_value) or not is_valid_hash(observed_value):
            raise ValueError("source hash value malformed")
        if observed_value != expected_value:
            raise ValueError("source hash mismatch")
    return True


def validate_reported_verdict(expected, observed) -> bool:
    if type(expected) is not str or type(observed) is not str or observed != expected:
        raise ValueError("reported verdict mismatch")
    return True


def run_tamper_controls(*, contexts, source_hashes, reported_verdict) -> dict[str, object]:
    baseline_payload = {"contexts": contexts, "source_hashes": source_hashes, "reported_verdict": reported_verdict}
    baseline_digest = engine.canonical_hash(baseline_payload)
    controls = {}
    for name in ("row", "lifecycle", "panel", "producer"):
        tampered_contexts = {}
        context_results = {}
        for context_id, original in contexts.items():
            mutated = deepcopy(original)
            applicable = True
            if name == "row" and mutated["witness"].get("rows"):
                mutated["witness"]["rows"][0]["outcome_type"] = "tampered"
            elif name == "lifecycle" and mutated["witness"].get("rows"):
                mutated["witness"]["rows"][-1]["life_index"] = int(
                    mutated["control"]["prefix"]["max_life_index"]
                ) + 1
            elif name == "panel" and mutated["panel"].get("rows"):
                mutated["panel"]["rows"] = mutated["panel"]["rows"][1:]
            elif name == "producer" and mutated["witness"].get("rows"):
                mutated["witness"]["rows"][0]["producer_receipts"]["forced_truth"]["transition_world"] = "fake.transition_world"
            else:
                applicable = False
            tampered_contexts[context_id] = mutated
            failure_reasons = []
            if applicable:
                reduced = independent_reduce_context(
                    context_id=context_id,
                    control=mutated["control"],
                    witness=mutated["witness"],
                    panel=mutated["panel"],
                )
                if not reduced["reported_values_match"]:
                    failure_reasons.append("reported_values_match_false")
                if name == "producer" and not reduced["producer_receipts_valid"]:
                    failure_reasons.append("producer_receipts_invalid")
                if name == "row" and not reduced["hashes_valid"]:
                    failure_reasons.append("hashes_invalid")
                if name == "lifecycle" and not reduced["check_map"]["control_envelope_comparable"]:
                    failure_reasons.append("control_envelope_incomparable")
                if name == "panel" and not reduced["panel"]["complete_action_expansion"]:
                    failure_reasons.append("panel_action_expansion_invalid")
            else:
                failure_reasons.append("tamper_not_applicable")
            context_results[context_id] = {
                "failure_reasons": failure_reasons,
                "failed_closed": bool(applicable and failure_reasons),
            }
        failure_reasons = [
            f"{context_id}:{reason}"
            for context_id, context_result in context_results.items()
            for reason in context_result["failure_reasons"]
        ]
        controls[name] = {
            "baseline_digest": baseline_digest,
            "tampered_digest": engine.canonical_hash({"name": name, "contexts": tampered_contexts}),
            "failure_reasons": failure_reasons,
            "failed_closed": all(item["failed_closed"] for item in context_results.values()),
            "contexts": context_results,
        }

    expected_source_hashes = deepcopy(source_hashes)
    observed_source_hashes = deepcopy(source_hashes)
    keys = list(expected_source_hashes.keys())
    if keys:
        observed_source_hashes[keys[0]] = ("0" if expected_source_hashes[keys[0]][0] != "0" else "1") + expected_source_hashes[keys[0]][1:]
    source_failures = []
    try:
        validate_exact_source_hashes(expected_source_hashes, observed_source_hashes)
    except ValueError as exc:
        source_failures.append(str(exc))
    controls["source_hash"] = {
        "baseline_digest": baseline_digest,
        "tampered_digest": engine.canonical_hash({"expected": expected_source_hashes, "observed": observed_source_hashes}),
        "failure_reasons": source_failures,
        "failed_closed": bool(source_failures),
    }

    baseline_context_reports = {cid: independent_reduce_context(context_id=cid, control=data["control"], witness=data["witness"], panel=data["panel"]) for cid, data in contexts.items()}
    baseline_provenance_clean = all(
        report.get("reported_values_match") is True and report.get("producer_receipts_valid") is True and report.get("hashes_valid") is True
        for report in baseline_context_reports.values()
    )
    baseline_control = all(report.get("check_map", {}).get("control_envelope_comparable") is True for report in baseline_context_reports.values())
    baseline_witness = all(report.get("check_map", {}).get("privileged_support_witness_found") is True for report in baseline_context_reports.values())
    baseline_panel = all(report.get("check_map", {}).get("deterministic_panel_capacity_admitted") is True for report in baseline_context_reports.values())
    if not baseline_provenance_clean:
        expected_verdict = "BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE"
    elif not baseline_control:
        expected_verdict = "BLOCKED_CONTROL_ENVELOPE_INCOMPARABLE"
    elif not baseline_witness:
        expected_verdict = "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    elif not baseline_panel:
        expected_verdict = "DETERMINISTIC_PANEL_CAPACITY_NOT_ADMITTED"
    else:
        expected_verdict = "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"
    tampered_verdict = expected_verdict + "_TAMPERED"
    verdict_failures = []
    try:
        validate_reported_verdict(expected_verdict, tampered_verdict)
    except ValueError as exc:
        verdict_failures.append(str(exc))
    controls["verdict"] = {
        "baseline_digest": baseline_digest,
        "tampered_digest": engine.canonical_hash({"expected_verdict": expected_verdict, "observed_verdict": tampered_verdict}),
        "failure_reasons": verdict_failures,
        "failed_closed": bool(verdict_failures),
    }
    return {
        "controls": controls,
        "all_tamper_controls_rejected": all(item["failed_closed"] and item["failure_reasons"] and item["tampered_digest"] != item["baseline_digest"] for item in controls.values()),
    }

def runtime_receipt() -> dict[str, object]:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    numpy_version = str(np.__version__)
    float_dtype = np.dtype(np.float64).str
    numpy_matrix_rank_tolerance = "numpy.linalg.matrix_rank_default"
    contract_satisfied = (
        python_version == "3.12.13"
        and numpy_version == "2.2.6"
        and float_dtype == "<f8"
        and numpy_matrix_rank_tolerance == "numpy.linalg.matrix_rank_default"
    )
    return {
        "python_version": python_version,
        "numpy_version": numpy_version,
        "float_dtype": float_dtype,
        "numpy_matrix_rank_tolerance": numpy_matrix_rank_tolerance,
        "contract_satisfied": contract_satisfied,
    }

def quotient_features(full_features: np.ndarray) -> np.ndarray:
    full = np.asarray(full_features, dtype=np.float64)
    if full.shape != (len(FEATURE_NAMES),):
        raise ValueError(
            f"expected feature vector shape {(len(FEATURE_NAMES),)}, got {full.shape}"
        )
    return np.delete(full, _QUOTIENT_DROP_INDICES).astype(np.float64, copy=False)


def structural_feature_checks(full_rows) -> dict[str, bool]:
    full = np.asarray(full_rows, dtype=np.float64)
    if full.ndim != 2 or full.shape[1] != len(FEATURE_NAMES):
        raise ValueError(
            f"expected feature matrix shape (n, {len(FEATURE_NAMES)}), got {full.shape}"
        )
    front_occluded_always_zero = bool(
        np.all(full[:, FEATURE_INDEX["front_occluded"]] == 0.0)
    )
    reachable_front_sum = np.sum(
        full[:, [FEATURE_INDEX[name] for name in _FRONT_SUM_NAMES]], axis=1
    )
    bias_equals_reachable_front_sum = bool(
        np.all(full[:, FEATURE_INDEX["bias"]] == reachable_front_sum)
    )
    quotient = np.asarray([quotient_features(row) for row in full], dtype=np.float64)
    raw_rank_at_most_13_after_constant_drop = bool(
        np.linalg.matrix_rank(quotient) <= 13
    )
    return {
        "front_occluded_always_zero": front_occluded_always_zero,
        "bias_equals_reachable_front_sum": bias_equals_reachable_front_sum,
        "raw_rank_at_most_13_after_constant_drop": raw_rank_at_most_13_after_constant_drop,
    }


def rank_reports_by_context_action(rows) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[np.ndarray]] = {}
    for row in rows:
        key = f"{row['context_id']}::{row['action']}"
        grouped.setdefault(key, []).append(quotient_features(row["features"]))

    reports: dict[str, dict[str, object]] = {}
    for key, feature_rows in grouped.items():
        matrix = np.asarray(feature_rows, dtype=np.float64)
        singular_values = np.linalg.svd(matrix, compute_uv=False)
        rank = int(np.linalg.matrix_rank(matrix))
        if rank < 13 or singular_values.size == 0 or singular_values[-1] == 0.0:
            condition_number = math.inf
        else:
            condition_number = float(singular_values[0] / singular_values[-1])
        reports[key] = {
            "rank": rank,
            "full_rank": rank == 13,
            "singular_values": singular_values.astype(np.float64, copy=False).tolist(),
            "condition_number": condition_number,
        }
    return reports


def summarize_control_prefix(records, action_budget: int) -> dict[str, object]:
    action_sequences: list[int] = []
    respawn_count = 0
    max_life_index = 0
    last_sequence = 0
    expected_sequence = None
    for record in records:
        sequence = int(record["sequence"])
        if expected_sequence is None:
            expected_sequence = sequence
        if sequence != expected_sequence:
            raise ValueError(
                f"non-contiguous sequence at {sequence}, expected {expected_sequence}"
            )
        expected_sequence += 1
        last_sequence = sequence
        max_life_index = max(max_life_index, int(record.get("life_index", 0)))
        if record.get("transition_kind") == "respawn":
            respawn_count += 1
        if record.get("transition_kind") == "action":
            action_sequences.append(sequence)
            if len(action_sequences) == action_budget:
                return {
                    "action_sequences": action_sequences,
                    "action_count": len(action_sequences),
                    "max_life_index": max_life_index,
                    "respawn_count": respawn_count,
                    "last_consumed_sequence": last_sequence,
                }
    raise ValueError(f"insufficient actions for budget {action_budget}")


def _maybe_decode_base64(value: str) -> str | None:
    stripped = value.strip()
    if (
        len(stripped) < 8
        or len(stripped) % 4 != 0
        or not _BASE64_PATTERN.fullmatch(stripped)
    ):
        return None
    try:
        decoded = base64.b64decode(stripped, validate=True)
    except (binascii.Error, ValueError):
        return None
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _scan_projection(value, findings: list[str], path: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _PRIVATE_FIELD_NAMES:
                findings.append(f"private field at {path}.{key}")
            _scan_projection(nested, findings, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _scan_projection(nested, findings, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for key in _PRIVATE_FIELD_NAMES:
            if key in value:
                findings.append(f"private token in text at {path}: {key}")
        decoded = _maybe_decode_base64(value)
        if decoded is not None:
            nested_findings_before = len(findings)
            for key in _PRIVATE_FIELD_NAMES:
                if key in decoded:
                    findings.append(f"private token in base64 at {path}: {key}")
            if decoded and decoded[0] in "[{":
                import json

                try:
                    parsed = json.loads(decoded)
                except json.JSONDecodeError:
                    parsed = None
                if parsed is not None:
                    _scan_projection(parsed, findings, f"{path}<base64>")
            if len(findings) == nested_findings_before and decoded != value:
                return


def scan_learner_projection(value) -> dict[str, object]:
    findings: list[str] = []
    _scan_projection(value, findings, "$")
    return {"clean": len(findings) == 0, "findings": findings}







def _git_stdout(*args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=str(REPO_ROOT), check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def _git_success(*args: str) -> bool:
    completed = subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True)
    return completed.returncode == 0


def summarize_fresh_stage_pair(first, second) -> dict[str, object]:
    return {
        "equal": bool(
            first.get("payload") == second.get("payload")
            and first.get("payload_digest") == second.get("payload_digest")
            and first.get("python_executable") == second.get("python_executable")
            and first.get("runtime_receipt") == second.get("runtime_receipt")
            and first.get("parent_pid") == second.get("parent_pid")
            and first.get("child_pid") != second.get("child_pid")
        ),
        "first_child_pid": first.get("child_pid"),
        "second_child_pid": second.get("child_pid"),
        "first_parent_pid": first.get("parent_pid"),
        "second_parent_pid": second.get("parent_pid"),
        "python_executable": first.get("python_executable"),
        "first_python_executable": first.get("python_executable"),
        "second_python_executable": second.get("python_executable"),
        "runtime_receipt": deepcopy(first.get("runtime_receipt")),
        "first_runtime_receipt": deepcopy(first.get("runtime_receipt")),
        "second_runtime_receipt": deepcopy(second.get("runtime_receipt")),
        "first_request_digest": first.get("request_digest"),
        "second_request_digest": second.get("request_digest"),
        "first_payload_digest": first.get("payload_digest"),
        "second_payload_digest": second.get("payload_digest"),
    }

def collect_pre_run_observation(*, output_dir, provenance_path) -> dict[str, object]:
    output = Path(output_dir)
    provenance = Path(provenance_path)
    repository_root = _git_stdout("rev-parse", "--show-toplevel")
    branch = _git_stdout("branch", "--show-current")
    head = _git_stdout("rev-parse", "HEAD")
    head_parent = _git_stdout("rev-parse", "HEAD^")
    changed = _git_stdout("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
    changed_paths = [] if changed == "" else changed.splitlines()
    try:
        provenance_relpath = provenance.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        provenance_relpath = changed_paths[0] if len(changed_paths) == 1 and Path(changed_paths[0]).name == provenance.name else provenance.name
    try:
        output_relpath = output.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        output_relpath = output.as_posix()
    status = _git_stdout("status", "--porcelain")
    source_hashes = {path: _sha256_file(REPO_ROOT / path) for path in REQUIRED_PROVENANCE_SOURCE_PATHS}
    input_hashes = {path: _sha256_file(REPO_ROOT / path) for path in REQUIRED_PROVENANCE_INPUT_PATHS}
    dependency_hashes = {path: _sha256_file(REPO_ROOT / path) for path in REQUIRED_PROVENANCE_DEPENDENCY_PATHS}
    return {
        "repository_root": repository_root,
        "branch": branch,
        "head": head,
        "head_parent": head_parent,
        "head_changed_paths": changed_paths,
        "worktree_clean": status == "",
        "index_clean": _git_success("diff", "--cached", "--quiet"),
        "provenance_tracked_at_head": provenance_relpath in changed_paths and _git_success("cat-file", "-e", f"HEAD:{provenance_relpath}"),
        "runtime_receipt": runtime_receipt(),
        "engine_code_path_hash": engine.compute_code_path_hash(),
        "source_hashes": source_hashes,
        "input_hashes": input_hashes,
        "dependency_hashes": dependency_hashes,
        "output_dir": output_relpath,
        "output_absent_or_empty": (not output.exists()) or (output.is_dir() and not any(output.iterdir())),
    }
def validate_pre_run_provenance_document(document, observation) -> dict[str, object]:
    required_schema = "ego.v2.001h_r1.pre_run_provenance.v1"
    required_task = "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1"
    expected_firewall = {
        "contaminated_world_interval_inclusive": [30, 150],
        "future_fresh_world_must_be_greater_than": 150,
        "fresh_worlds_consumed": [],
        "forbidden_reuse_as_fresh_policy_seeds": [721, 722],
        "model_training_executed": False,
    }
    def require_exact_hash_map(label, expected_paths, actual_map, observed_map):
        if set(actual_map) != set(expected_paths) or set(observed_map) != set(expected_paths):
            raise ValueError(f"{label} path set mismatch")
        for path_key in expected_paths:
            for source_name, source_map in (("document", actual_map), ("observation", observed_map)):
                value = source_map[path_key]
                if not (isinstance(value, str) and len(value) == 64 and all(ch in '0123456789abcdef' for ch in value)):
                    raise ValueError(f"{label} hash malformed")
            if actual_map[path_key] != observed_map[path_key]:
                raise ValueError(f"{label} hash mismatch")
    if document.get("schema_version") != required_schema:
        raise ValueError("schema")
    if document.get("task_id") != required_task:
        raise ValueError("task")
    if document.get("repository_root") != observation.get("repository_root"):
        raise ValueError("repo")
    if document.get("branch") != observation.get("branch"):
        raise ValueError("branch")
    if document.get("implementation_commit") != observation.get("head_parent"):
        raise ValueError("provenance commit")
    if observation.get("head_changed_paths") != [document.get("provenance_path")]:
        raise ValueError("provenance commit")
    if observation.get("worktree_clean") is not True:
        raise ValueError("worktree")
    if observation.get("index_clean") is not True:
        raise ValueError("index")
    if observation.get("provenance_tracked_at_head") is not True:
        raise ValueError("provenance tracked")
    if document.get("runtime_receipt") != observation.get("runtime_receipt"):
        raise ValueError("runtime")
    if document.get("engine_code_path_hash") != observation.get("engine_code_path_hash"):
        raise ValueError("code path hash")
    require_exact_hash_map("source hash", REQUIRED_PROVENANCE_SOURCE_PATHS, document.get("source_hashes", {}), observation.get("source_hashes", {}))
    require_exact_hash_map("input hash", REQUIRED_PROVENANCE_INPUT_PATHS, document.get("input_hashes", {}), observation.get("input_hashes", {}))
    require_exact_hash_map("dependency hash", REQUIRED_PROVENANCE_DEPENDENCY_PATHS, document.get("dependency_hashes", {}), observation.get("dependency_hashes", {}))
    if document.get("context_specs") != list(FROZEN_CONTEXT_SPECS):
        raise ValueError("context specs")
    if document.get("heldout_firewall") != expected_firewall:
        raise ValueError("heldout firewall")
    if document.get("output_precondition") != "absent_or_empty":
        raise ValueError("output precondition")
    if document.get("output_dir") != observation.get("output_dir"):
        raise ValueError("output directory")
    if observation.get("output_absent_or_empty") is not True:
        raise ValueError("output directory")
    return {"passed": True, "failure_reasons": [], "provenance_commit": observation.get("head")}

def derive_adjudication(context_reports, validity) -> dict[str, object]:
    required_validity_keys = (
        "pre_run_provenance_valid",
        "runtime_contract_satisfied",
        "source_hashes_match",
        "leakage_clean",
        "positive_controls_detected",
        "fresh_process_recompute_equal",
        "all_tamper_controls_rejected",
    )
    required_check_keys = (
        "control_envelope_comparable",
        "privileged_support_witness_found",
        "deterministic_panel_capacity_admitted",
    )
    failure_reasons = []

    def require_bool(value, label: str) -> bool:
        if type(value) is not bool:
            failure_reasons.append(f"non_boolean:{label}")
            return False
        if not value:
            failure_reasons.append(f"false:{label}")
            return False
        return True

    provenance_clean = True
    for key in required_validity_keys:
        if key not in validity:
            failure_reasons.append(f"missing:{key}")
            provenance_clean = False
        else:
            provenance_clean = require_bool(validity[key], key) and provenance_clean

    aggregate_checks = {key: True for key in required_check_keys}
    for context_id, report in dict(context_reports).items():
        if not isinstance(report, dict):
            failure_reasons.append(f"non_mapping_context:{context_id}")
            provenance_clean = False
            for key in required_check_keys:
                aggregate_checks[key] = False
            continue
        for key in ("reported_values_match", "producer_receipts_valid", "hashes_valid"):
            if key not in report:
                failure_reasons.append(f"missing:{context_id}.{key}")
                provenance_clean = False
            else:
                provenance_clean = require_bool(report[key], f"{context_id}.{key}") and provenance_clean
        check_map = report.get("check_map")
        if not isinstance(check_map, dict):
            failure_reasons.append(f"non_mapping:{context_id}.check_map")
            for key in required_check_keys:
                aggregate_checks[key] = False
            continue
        for key in required_check_keys:
            if key not in check_map:
                failure_reasons.append(f"missing:{context_id}.check_map.{key}")
                aggregate_checks[key] = False
            elif type(check_map[key]) is not bool:
                failure_reasons.append(f"non_boolean:{context_id}.check_map.{key}")
                aggregate_checks[key] = False
                provenance_clean = False
            else:
                aggregate_checks[key] = aggregate_checks[key] and bool(check_map[key])

    verdict = dispatch_verdict(
        provenance_clean,
        aggregate_checks["control_envelope_comparable"],
        aggregate_checks["privileged_support_witness_found"],
        aggregate_checks["deterministic_panel_capacity_admitted"],
    )
    return {
        "provenance_clean": provenance_clean,
        "control_envelope_comparable": aggregate_checks["control_envelope_comparable"],
        "privileged_support_witness_found": aggregate_checks["privileged_support_witness_found"],
        "deterministic_panel_capacity_admitted": aggregate_checks["deterministic_panel_capacity_admitted"],
        "verdict": verdict,
        "failure_reasons": failure_reasons,
    }

def independent_reduce_context(*, context_id: str, control, witness, panel) -> dict[str, object]:
    frozen_required_floors = {"v0": 8, "v1": 8, "v2": 8, "v3": 8, "v4": 8, "empty": 16, "wall": 16}
    witness_predictive_update_path = (
        "ego_life_playground_v0.predictive_control.update_after_transition"
    )
    panel_truth_receipts = {
        "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
        "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
        "compute_metabolism_ledger": "labs.ego_life_playground_v0.engine.compute_metabolism_ledger",
    }

    def independent_prefix(records, action_budget: int) -> dict[str, object]:
        action_sequences = []
        respawn_count = 0
        max_life_index = 0
        last_consumed_sequence = 0
        expected_sequence = None
        expected_action_index = 1
        previous_life_index = None
        life_sequence_ok = True
        complete_prefix = False
        for record in records:
            sequence = int(record["sequence"])
            if expected_sequence is None:
                expected_sequence = sequence
            if sequence != expected_sequence:
                raise ValueError("independent reducer sequence mismatch")
            expected_sequence += 1
            last_consumed_sequence = sequence
            life_index = int(record.get("life_index", 0))
            max_life_index = max(max_life_index, life_index)
            if previous_life_index is None:
                previous_life_index = life_index
            else:
                if life_index < previous_life_index or life_index - previous_life_index > 1:
                    life_sequence_ok = False
                previous_life_index = life_index
            if record.get("transition_kind") == "respawn":
                respawn_count += 1
            if record.get("transition_kind") == "action":
                action_sequences.append(sequence)
                if "action_index" in record and int(record["action_index"]) != expected_action_index:
                    life_sequence_ok = False
                expected_action_index += 1
                if len(action_sequences) == action_budget:
                    complete_prefix = True
                    break
        return {
            "action_count": len(action_sequences),
            "action_sequences": action_sequences,
            "max_life_index": max_life_index,
            "respawn_count": respawn_count,
            "last_consumed_sequence": last_consumed_sequence,
            "life_sequence_ok": life_sequence_ok,
            "complete_prefix": complete_prefix,
        }

    def independent_stratum_counts(rows) -> dict[str, int]:
        counts = {}
        for stratum in TRAINING_SUPPORT_STRATA:
            total = 0
            for row in rows:
                projection = row["learner_projection"]
                if row["selected_action"] != stratum["action"]:
                    continue
                if row["outcome_type"] != stratum["outcome_type"]:
                    continue
                target = stratum["target_front_token"]
                if target is not None and projection["front_token"] != target:
                    continue
                total += 1
            counts[stratum["stratum_id"]] = total
        return counts

    def independent_action_ranks(rows) -> dict[str, int]:
        result = {}
        for action in engine.ACTIONS:
            vectors = [
                row["learner_projection"]["quotient_features"]
                for row in rows
                if row["selected_action"] == action
            ]
            result[action] = 0 if not vectors else int(np.linalg.matrix_rank(np.asarray(vectors, dtype=np.float64)))
        return result

    def independent_token_counts(checkpoints) -> dict[str, int]:
        tokens = ("v0", "v1", "v2", "v3", "v4", "empty", "wall")
        return {token: sum(item["front_token"] == token for item in checkpoints) for token in tokens}

    def independent_cell_counts(rows) -> dict[str, int]:
        counts = {}
        for row in rows:
            key = "::".join((context_id, row["selected_action"], row["front_token"], row["outcome_type"]))
            counts[key] = counts.get(key, 0) + 1
        return counts

    control_reduced = independent_prefix(control["prefix_records"], action_budget=89)
    witness_counts = independent_stratum_counts(witness["rows"])
    witness_action_ranks = independent_action_ranks(witness["rows"])
    witness_life_indices = [int(row.get("life_index", 0)) for row in witness["rows"]]
    witness_max_life_index = max(witness_life_indices, default=0)
    witness_respawn_count = max(0, len(set(witness_life_indices)) - 1) if witness_life_indices else 0
    witness_sequence_complete = (
        len(witness["rows"]) == 89
        and [int(row.get("action_index", index + 1)) for index, row in enumerate(witness["rows"])] == list(range(1, len(witness["rows"]) + 1))
        and [int(row.get("global_sequence", 0)) for row in witness["rows"]] == sorted(int(row.get("global_sequence", 0)) for row in witness["rows"])
        and sorted(set(witness_life_indices)) == list(range(1, witness_max_life_index + 1))
    )
    control_envelope_comparable = bool(
        control_reduced["complete_prefix"]
        and control_reduced["action_count"] == 89
        and control_reduced["life_sequence_ok"]
        and witness_sequence_complete
        and witness_max_life_index <= control_reduced["max_life_index"]
        and witness_respawn_count <= control_reduced["respawn_count"]
    )
    witness_found = bool(
        control_envelope_comparable
        and all(value >= 4 for value in witness_counts.values())
        and all(rank == 13 for rank in witness_action_ranks.values())
    )
    witness_hash = engine.canonical_hash(witness["rows"])
    witness_receipts_valid = all(
        isinstance(row.get("producer_receipts"), dict)
        and row["producer_receipts"].get("forced_truth") == panel_truth_receipts
        and row["producer_receipts"].get("predictive_update", {}).get("producer_function") == witness_predictive_update_path
        and row["producer_receipts"].get("predictive_update", {}).get("reason") == "predictor_updates_frozen"
        for row in witness["rows"]
    ) if witness["rows"] else False

    panel_before = independent_token_counts(panel["raw_checkpoints"])
    panel_after = independent_token_counts(panel["retained_checkpoints"])
    panel_cell_counts = independent_cell_counts(panel["rows"])
    panel_action_ranks = independent_action_ranks(panel["rows"])
    panel_construction_complete = all(bool(item["complete"]) for item in panel["rollouts"])
    retained_hashes = [item["checkpoint_hash"] for item in panel["retained_checkpoints"]]
    retained_unique = len(set(retained_hashes)) == len(retained_hashes)
    actions_by_checkpoint = {}
    for row in panel["rows"]:
        actions_by_checkpoint.setdefault(row["checkpoint_hash"], []).append(row["selected_action"])
    complete_action_expansion = retained_unique and all(
        sorted(actions_by_checkpoint.get(checkpoint_hash, [])) == sorted(engine.ACTIONS)
        for checkpoint_hash in retained_hashes
    ) and len(panel["rows"]) == len(retained_hashes) * len(engine.ACTIONS)
    panel_support_pass = all(panel_before[token] >= floor and panel_after[token] >= floor for token, floor in frozen_required_floors.items())
    panel_cell_pass = all(count >= frozen_required_floors[key.split("::")[-2]] for key, count in panel_cell_counts.items())
    panel_capacity_admitted = bool(
        panel_construction_complete
        and panel_support_pass
        and panel_cell_pass
        and complete_action_expansion
        and all(rank == 13 for rank in panel_action_ranks.values())
    )
    panel_hash = engine.canonical_hash({
        "rollouts": panel["rollouts"],
        "retained_checkpoint_hashes": [item["checkpoint_hash"] for item in panel["retained_checkpoints"]],
        "rows": panel["rows"],
        "support_report": panel["support_report"],
        "cell_support_report": panel["cell_support_report"],
        "rank_reports": panel["rank_reports"],
        "panel_capacity_admitted": panel["panel_capacity_admitted"],
    })
    panel_receipts_valid = all(row.get("producer_receipts") == panel_truth_receipts for row in panel["rows"])
    producer_receipts_valid = bool(witness_receipts_valid and panel_receipts_valid)
    hashes_valid = bool(
        witness_hash == witness.get("trajectory_hash")
        and panel_hash == panel.get("panel_hash")
    )

    report = {
        "independence_boundary": "separate reducer implementation in the same verifier process and same Codex/model lineage; not external independent audit",
        "control": {
            "action_count": control_reduced["action_count"],
            "max_life_index": control_reduced["max_life_index"],
            "respawn_count": control_reduced["respawn_count"],
        },
        "witness": {
            "stratum_counts": witness_counts,
            "action_ranks": witness_action_ranks,
            "witness_found": witness_found,
            "control_envelope_comparable": control_envelope_comparable,
        },
        "panel": {
            "before_dedupe": panel_before,
            "after_dedupe": panel_after,
            "required_floors": deepcopy(frozen_required_floors),
            "cell_counts": panel_cell_counts,
            "required_floor_by_cell": {key: frozen_required_floors[key.split("::")[-2]] for key in panel_cell_counts},
            "action_ranks": panel_action_ranks,
            "construction_complete": panel_construction_complete,
            "complete_action_expansion": complete_action_expansion,
            "panel_capacity_admitted": panel_capacity_admitted,
        },
        "producer_receipts_valid": producer_receipts_valid,
        "hashes_valid": hashes_valid,
        "check_map": {
            "control_envelope_comparable": control_envelope_comparable,
            "privileged_support_witness_found": witness_found,
            "deterministic_panel_capacity_admitted": panel_capacity_admitted,
        },
    }
    reported_values_match = True
    reported_values_match = reported_values_match and (report["control"]["action_count"] == int(control["prefix"]["action_count"]))
    reported_values_match = reported_values_match and (report["control"]["max_life_index"] == int(control["prefix"]["max_life_index"]))
    reported_values_match = reported_values_match and (report["control"]["respawn_count"] == int(control["prefix"]["respawn_count"]))
    reported_values_match = reported_values_match and (report["witness"]["stratum_counts"] == witness["support_report"]["stratum_counts"])
    reported_values_match = reported_values_match and (report["witness"]["action_ranks"] == {action: witness["rank_reports"][f"{context_id}::{action}"]["rank"] for action in engine.ACTIONS})
    reported_values_match = reported_values_match and (report["witness"]["control_envelope_comparable"] is bool(witness["control_envelope_comparable"]))
    reported_values_match = reported_values_match and (report["witness"]["witness_found"] is bool(witness["witness_found"]))
    reported_values_match = reported_values_match and (report["panel"]["before_dedupe"] == panel["support_report"]["before_dedupe"])
    reported_values_match = reported_values_match and (report["panel"]["after_dedupe"] == panel["support_report"]["after_dedupe"])
    reported_values_match = reported_values_match and (report["panel"]["required_floors"] == panel["support_report"]["required_floors"])
    reported_values_match = reported_values_match and (report["panel"]["cell_counts"] == panel["cell_support_report"]["cell_counts"])
    reported_values_match = reported_values_match and (report["panel"]["required_floor_by_cell"] == panel["cell_support_report"]["required_floor_by_cell"])
    reported_values_match = reported_values_match and (report["panel"]["action_ranks"] == {action: panel["rank_reports"][f"{context_id}::{action}"]["rank"] for action in engine.ACTIONS})
    reported_values_match = reported_values_match and (report["panel"]["construction_complete"] is bool(panel["construction_complete"]))
    reported_values_match = reported_values_match and (report["panel"]["panel_capacity_admitted"] is bool(panel["panel_capacity_admitted"]))
    reported_values_match = reported_values_match and (report["panel"]["complete_action_expansion"] is True)
    reported_values_match = reported_values_match and (all("checkpoint_hash" in item for item in panel["retained_checkpoints"]))
    reported_values_match = reported_values_match and producer_receipts_valid
    reported_values_match = reported_values_match and hashes_valid
    report["reported_values_match"] = bool(reported_values_match)
    return report

def run_leakage_positive_controls(clean_projection) -> dict[str, object]:
    clean_scan = scan_learner_projection(clean_projection)
    controls = {
        "cause_identity": {"cause_identity": "resource"},
        "private_position": {"private_position": [3, 4]},
        "private_map": {"private_map": {"0,0": "wall"}},
        "objects_by_cause": {"objects_by_cause": {"resource": {}}},
        "token_mapping": {"token_mapping": {"v0": "resource"}},
        "target_reason": {"target_reason": "rank_gain"},
        "private_path": {"private_path": ["turn_left", "move_forward"]},
        "world_id": {"world_id": "world-52"},
        "policy_id": {"policy_id": "policy-711"},
        "run_id": {"run_id": "run-abc"},
        "future_observation": {"future_observation": {"visual": [["empty"]]}},
        "panel_truth": {"panel_truth": {"outcome_type": "rested"}},
        "loss": {"loss": 0.125},
        "verdict": {"verdict": "pass"},
        "file_path": {"file_path": "C:/secret/file.json"},
        "artifact_hash": {"artifact_hash": "a" * 64},
    }
    positive_controls: dict[str, dict[str, object]] = {}
    for category, direct_payload in controls.items():
        direct_scan = scan_learner_projection({**deepcopy(clean_projection), "positive_control": deepcopy(direct_payload)})
        encoded = base64.b64encode(engine.canonical_json(direct_payload).encode("utf-8")).decode("ascii")
        base64_scan = scan_learner_projection({**deepcopy(clean_projection), "positive_control": encoded})
        positive_controls[category] = {
            "direct_detected": not bool(direct_scan["clean"]),
            "base64_detected": not bool(base64_scan["clean"]),
            "direct_findings": deepcopy(direct_scan["findings"]),
            "base64_findings": deepcopy(base64_scan["findings"]),
        }
    all_positive_controls_detected = all(
        item["direct_detected"] and item["base64_detected"]
        for item in positive_controls.values()
    )
    return {
        "clean_scan": clean_scan,
        "positive_controls": positive_controls,
        "all_positive_controls_detected": all_positive_controls_detected,
    }

def dispatch_verdict(
    provenance_clean: bool,
    control_envelope_comparable: bool,
    privileged_support_witness_found: bool,
    deterministic_panel_capacity_admitted: bool,
) -> str:
    if not provenance_clean:
        return "BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE"
    if not control_envelope_comparable:
        return "BLOCKED_CONTROL_ENVELOPE_INCOMPARABLE"
    if not privileged_support_witness_found:
        return "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    if not deterministic_panel_capacity_admitted:
        return "DETERMINISTIC_PANEL_CAPACITY_NOT_ADMITTED"
    return "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_read_only_event_store(database: Path) -> v2_store.SQLiteEventStore:
    uri = f"file:{database.as_posix()}?mode=ro&immutable=1"
    event_store = object.__new__(v2_store.SQLiteEventStore)
    event_store.path = database.expanduser().resolve()
    event_store._connection = sqlite3.connect(uri, isolation_level=None, uri=True)
    event_store._connection.row_factory = sqlite3.Row
    event_store._connection.execute("PRAGMA query_only = ON")
    return event_store


def extract_banked_control(database_path: str | Path, action_budget: int) -> dict[str, object]:
    database = Path(database_path)
    event_store = _open_read_only_event_store(database)
    try:
        rows = event_store.connection.execute(
            "SELECT run_id FROM runs ORDER BY rowid ASC"
        ).fetchall()
        run_ids = [str(row["run_id"]) for row in rows]
        if len(run_ids) != 1:
            raise ValueError(f"expected exactly one run in {database}, got {len(run_ids)}")
        recovered = event_store.recover_run(run_ids[0])
    finally:
        event_store.close()

    records = []
    for frame in recovered.frames[1:]:
        trace = frame.trace
        if trace is None:
            continue
        lifecycle_after = trace.get("lifecycle_after") or frame.state.get("lifecycle") or {}
        records.append(
            {
                "sequence": int(frame.sequence),
                "transition_kind": trace.get("transition_kind"),
                "selected_action": trace.get("selected_action"),
                "life_index": int(lifecycle_after.get("life_index", 0)),
            }
        )
    action_records = [record for record in records if record.get("transition_kind") == "action"]
    prefix = summarize_control_prefix(records, action_budget=action_budget)
    prefix_records = [
        deepcopy(record)
        for record in records
        if int(record["sequence"]) <= int(prefix["last_consumed_sequence"])
    ]
    return {
        "database_path": str(database),
        "database_sha256": _sha256_file(database),
        "run_id": recovered.run_id,
        "recovery_exact": bool(
            recovered.recovered and all(frame.trace is not None for frame in recovered.frames[1:])
        ),
        "available_action_count": len(action_records),
        "open_mode": "sqlite_uri_mode_ro_immutable_1",
        "prefix": prefix,
        "prefix_records": prefix_records,
    }


def private_shortest_front_path(world, target_front_token: str) -> dict[str, object]:
    microworld.verify_world_state(world)
    if type(target_front_token) is not str or target_front_token not in _PRIVATE_BFS_TARGETS:
        raise ValueError(f"invalid target front token: {target_front_token!r}")

    start_world = deepcopy(world)
    queue = deque([(deepcopy(world), tuple())])
    seen = {engine.canonical_hash(start_world)}

    while queue:
        candidate_world, actions = queue.popleft()
        observation = microworld.policy_observation(candidate_world, occlusion=True)
        front_token = observation["visual"][1][2]
        if front_token == target_front_token:
            end_world = deepcopy(candidate_world)
            return {
                "actions": list(actions),
                "distance": len(actions),
                "target_front_token": target_front_token,
                "front_token_after": front_token,
                "start_world_hash": engine.canonical_hash(start_world),
                "end_world_hash": engine.canonical_hash(end_world),
                "end_world": end_world,
            }
        for action in _PRIVATE_BFS_ACTIONS:
            successor_world, _transition = microworld.transition_world(candidate_world, action)
            key = engine.canonical_hash(successor_world)
            if key in seen:
                continue
            seen.add(key)
            queue.append((successor_world, (*actions, action)))

    raise ValueError(f"no path found for target front token: {target_front_token!r}")



def evaluate_forced_action_truth(
    *,
    world,
    organism,
    action: str,
    run_meta,
    episode_id: str,
    command_hash: str,
    source_sequence: int,
    life_index: int,
    episode_tick_after: int,
) -> dict[str, object]:
    microworld.verify_world_state(world)
    predictive_control._validate_organism(organism)  # noqa: SLF001
    if type(action) is not str or action not in microworld.ACTIONS:
        raise ValueError("action must be canonical microworld action")
    if type(life_index) is not int or life_index <= 0:
        raise ValueError("life_index must be positive integer")
    if type(episode_tick_after) is not int or episode_tick_after <= 0:
        raise ValueError("episode_tick_after must be positive integer")
    if type(source_sequence) is not int or source_sequence <= 0:
        raise ValueError("source_sequence must be positive integer")
    if type(episode_id) is not str or not episode_id:
        raise ValueError("episode_id must be non-empty string")
    if type(run_meta) is not dict and not hasattr(run_meta, 'keys'):
        raise ValueError("run_meta must be mapping")
    engine._verify_run_metadata(run_meta, engine.compute_code_path_hash())  # noqa: SLF001
    if not engine._is_sha256(command_hash):  # noqa: SLF001
        raise ValueError("command_hash must be sha256")

    world_before = deepcopy(world)
    organism_before = deepcopy(organism)
    code_path_hash = engine.compute_code_path_hash()
    next_world, world_transition = microworld.transition_world(
        world_before,
        action,
        source_sequence=source_sequence,
        source_episode_id=episode_id,
        source_command_hash=command_hash,
    )
    actual_delta = engine.compute_actual_delta(world_transition, selected_action=action)
    metabolism = engine.compute_metabolism_ledger(
        energy_before=float(organism_before["energy"]),
        selected_action=action,
        world_before=world_before,
        world_after=next_world,
        world_transition=world_transition,
        run_meta=run_meta,
        episode_id=episode_id,
        command_hash=command_hash,
        code_path_hash=code_path_hash,
    )
    actual_delta["energy"] = metabolism["energy_delta"]
    next_organism = engine._apply_delta(organism_before, actual_delta)  # noqa: SLF001
    terminal_receipt = None
    if next_organism["energy"] == 0.0:
        terminal_receipt = engine._life_result(  # noqa: SLF001
            life_index=life_index,
            survival_ticks=episode_tick_after,
            censored=False,
            termination="death",
        )
    elif episode_tick_after == engine.EPISODE_SPAN_TICKS:
        terminal_receipt = engine._life_result(  # noqa: SLF001
            life_index=life_index,
            survival_ticks=engine.EPISODE_SPAN_TICKS,
            censored=True,
            termination="censored",
        )
    return {
        "next_world": next_world,
        "next_organism": next_organism,
        "truth": {
            "outcome_type": world_transition["outcome_type"],
            "world_transition": world_transition,
            "actual_delta": actual_delta,
            "metabolism": metabolism,
            "terminal_receipt": terminal_receipt,
        },
        "callable_receipts": {
            "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
            "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
            "compute_metabolism_ledger": "labs.ego_life_playground_v0.engine.compute_metabolism_ledger",
        },
    }


def initialize_evaluator_state(*, layout_id: str, world_seed: int, policy_seed: int, run_id: str) -> dict[str, object]:
    canonical_state = engine.initial_state(run_id=run_id, seed=world_seed, layout_id=layout_id)
    run_meta = engine.make_run_metadata(run_id, seed=policy_seed)
    return {
        "run_id": run_id,
        "run_meta": deepcopy(run_meta),
        "world": deepcopy(canonical_state["world"]),
        "organism": deepcopy(canonical_state["organism"]),
        "predictive_state": deepcopy(canonical_state["predictive_control"]),
        "life_index": int(canonical_state["lifecycle"]["life_index"]),
        "episode_index": int(canonical_state["clock"]["episode_index"]),
        "episode_tick": int(canonical_state["clock"]["episode_tick"]),
        "global_sequence": int(canonical_state["clock"]["global_tick"]),
        "action_count": 0,
        "respawn_count": 0,
        "awaiting_respawn": bool(canonical_state["lifecycle"]["awaiting_respawn"]),
    }


def advance_evaluator_action(state, action: str) -> dict[str, object]:
    if bool(state["awaiting_respawn"]):
        raise ValueError("cannot advance action while awaiting respawn")
    if type(action) is not str or action not in microworld.ACTIONS:
        raise ValueError("action must be canonical microworld action")

    before_state = deepcopy(state)
    next_global_sequence = int(before_state["global_sequence"]) + 1
    next_episode_tick = int(before_state["episode_tick"]) + 1
    checkpoint = build_public_checkpoint(
        world=before_state["world"],
        organism=before_state["organism"],
        predictive_state=before_state["predictive_state"],
        episode_index=int(before_state["episode_index"]),
    )
    episode_id = engine.episode_id_for(str(before_state["run_id"]), int(before_state["episode_index"]))
    command_hash = engine.canonical_hash(
        {
            "run_id": before_state["run_id"],
            "life_index": before_state["life_index"],
            "sequence": next_global_sequence,
            "action": action,
        }
    )
    truth = evaluate_forced_action_truth(
        world=before_state["world"],
        organism=before_state["organism"],
        action=action,
        run_meta=before_state["run_meta"],
        episode_id=episode_id,
        command_hash=command_hash,
        source_sequence=next_global_sequence,
        life_index=int(before_state["life_index"]),
        episode_tick_after=next_episode_tick,
    )
    next_observation = microworld.policy_observation(truth["next_world"], occlusion=True)
    terminal_receipt = truth["truth"]["terminal_receipt"]
    updated_predictive_state, predictive_update_receipt = predictive_control.update_after_transition(
        checkpoint["prepared_predictive_state"],
        observation=checkpoint["observation"],
        organism_before=before_state["organism"],
        action=action,
        actual_outcome_type=str(truth["truth"]["outcome_type"]),
        actual_delta=truth["truth"]["actual_delta"],
        terminal=terminal_receipt is not None,
        resource_interaction=bool(truth["truth"]["metabolism"]["food_gain"] > 0.0),
        next_observation=next_observation,
        episode_index=int(before_state["episode_index"]),
        relative_map_mode="relative",
        updates_enabled=False,
    )
    learner_projection = {
        "observation": deepcopy(checkpoint["observation"]),
        "organism_before": deepcopy(before_state["organism"]),
        "selected_action": action,
        "front_token": checkpoint["front_token"],
        "outcome_type": truth["truth"]["outcome_type"],
        "actual_delta": deepcopy(truth["truth"]["actual_delta"]),
        "terminal_receipt": deepcopy(terminal_receipt),
        "public_relative_belief": deepcopy(checkpoint["predictor_input"]["belief_summary"]),
        "quotient_features": checkpoint["quotient_features"].astype(np.float64, copy=False).tolist(),
    }
    next_state = deepcopy(before_state)
    next_state["world"] = deepcopy(truth["next_world"])
    next_state["organism"] = deepcopy(truth["next_organism"])
    next_state["predictive_state"] = deepcopy(updated_predictive_state)
    next_state["episode_tick"] = next_episode_tick
    next_state["global_sequence"] = next_global_sequence
    next_state["action_count"] = int(before_state["action_count"]) + 1
    next_state["awaiting_respawn"] = terminal_receipt is not None
    row = {
        "selected_action": action,
        "outcome_type": truth["truth"]["outcome_type"],
        "terminal_receipt": deepcopy(terminal_receipt),
        "learner_projection": learner_projection,
        "producer_receipts": {
            "public_checkpoint": checkpoint["receipt"],
            "forced_truth": deepcopy(truth["callable_receipts"]),
            "predictive_update": deepcopy(predictive_update_receipt),
        },
        "evaluator_truth": deepcopy(truth["truth"]),
        "full_features": checkpoint["full_features"].astype(np.float64, copy=False).tolist(),
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "front_token": checkpoint["front_token"],
        "global_sequence": next_global_sequence,
        "life_index": int(before_state["life_index"]),
        "transition_kind": "action",
    }
    return {"state": next_state, "row": row}


def advance_evaluator_respawn(state) -> dict[str, object]:
    if not bool(state["awaiting_respawn"]):
        raise ValueError("state is not awaiting respawn")
    if int(state["life_index"]) >= engine.MAX_LIVES:
        raise ValueError("max lives reached")
    next_state = deepcopy(state)
    next_life_index = int(state["life_index"]) + 1
    next_episode_index = int(state["episode_index"]) + 1
    next_state["world"] = microworld.reset_world_for_life(state["world"], next_life_index)
    next_state["organism"] = deepcopy(dict(engine.INITIAL_ORGANISM))
    next_state["predictive_state"] = predictive_control.reset_for_respawn(
        state["predictive_state"], episode_index=next_episode_index
    )
    next_state["life_index"] = next_life_index
    next_state["episode_index"] = next_episode_index
    next_state["episode_tick"] = 0
    next_state["global_sequence"] = int(state["global_sequence"]) + 1
    next_state["respawn_count"] = int(state["respawn_count"]) + 1
    next_state["awaiting_respawn"] = False
    return next_state


def _support_counts_from_rows(rows) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stratum in TRAINING_SUPPORT_STRATA:
        selected = 0
        for row in rows:
            projection = row["learner_projection"]
            if row["selected_action"] != stratum["action"]:
                continue
            if row["outcome_type"] != stratum["outcome_type"]:
                continue
            target = stratum["target_front_token"]
            if target is not None and projection["front_token"] != target:
                continue
            selected += 1
        counts[stratum["stratum_id"]] = selected
    return counts


def _rank_reports_from_rows(context_id: str, rows) -> dict[str, dict[str, object]]:
    rank_rows = [
        {"context_id": context_id, "action": row["selected_action"], "features": row["full_features"]}
        for row in rows
    ]
    reports = rank_reports_by_context_action(rank_rows)
    for action in engine.ACTIONS:
        reports.setdefault(
            f"{context_id}::{action}",
            {"rank": 0, "full_rank": False, "singular_values": [], "condition_number": math.inf},
        )
    return reports


def _choose_rank_action(context_id: str, rows, checkpoint) -> str:
    current_reports = _rank_reports_from_rows(context_id, rows)
    full_feature_list = checkpoint["full_features"].astype(np.float64, copy=False).tolist()
    candidates = []
    counts_by_action = {action: 0 for action in engine.ACTIONS}
    for row in rows:
        counts_by_action[row["selected_action"]] += 1
    for order, action in enumerate(engine.ACTIONS):
        before_rank = int(current_reports[f"{context_id}::{action}"]["rank"])
        synthetic_rows = list(rows) + [{"selected_action": action, "full_features": full_feature_list}]
        after_rank = int(_rank_reports_from_rows(context_id, synthetic_rows)[f"{context_id}::{action}"]["rank"])
        candidates.append({
            "action": action,
            "before_rank": before_rank,
            "after_rank": after_rank,
            "gain": after_rank - before_rank,
            "count": counts_by_action[action],
            "order": order,
        })
    gainers = [item for item in candidates if item["before_rank"] < 13 and item["gain"] > 0]
    if gainers:
        gainers.sort(key=lambda item: (item["before_rank"], item["count"], item["order"]))
        return str(gainers[0]["action"])
    candidates.sort(key=lambda item: (item["count"], item["order"]))
    return str(candidates[0]["action"])


def _decorate_row_for_witness(row, *, context_id: str, action_index: int):
    decorated = deepcopy(row)
    decorated["context_id"] = context_id
    decorated["action_index"] = action_index
    decorated["transition_kind"] = "action"
    return decorated


def run_privileged_witness(*, context_id: str, layout_id: str, world_seed: int, policy_seed: int, action_budget: int, max_life_index: int, max_respawn_count: int) -> dict[str, object]:
    state = initialize_evaluator_state(layout_id=layout_id, world_seed=world_seed, policy_seed=policy_seed, run_id=context_id)
    rows = []
    control_envelope_comparable = True

    def maybe_respawn(current_state):
        nonlocal control_envelope_comparable
        if not current_state["awaiting_respawn"]:
            return current_state
        if int(current_state["life_index"]) >= int(max_life_index) or int(current_state["respawn_count"]) >= int(max_respawn_count):
            control_envelope_comparable = False
            return current_state
        return advance_evaluator_respawn(current_state)

    while len(rows) < action_budget and control_envelope_comparable:
        counts = _support_counts_from_rows(rows)
        deficient = next((item for item in TRAINING_SUPPORT_STRATA if counts[item["stratum_id"]] < 4), None)
        if deficient is None:
            break
        target = deficient["target_front_token"]
        if target is not None:
            while len(rows) < action_budget and control_envelope_comparable:
                if state["awaiting_respawn"]:
                    state = maybe_respawn(state)
                    if state["awaiting_respawn"]:
                        break
                    continue
                receipt = private_shortest_front_path(state["world"], target)
                if not receipt["actions"]:
                    break
                interrupted = False
                for nav_action in receipt["actions"]:
                    if len(rows) >= action_budget:
                        break
                    advanced = advance_evaluator_action(state, nav_action)
                    state = advanced["state"]
                    rows.append(_decorate_row_for_witness(advanced["row"], context_id=context_id, action_index=len(rows)+1))
                    if len(rows) >= action_budget:
                        break
                    if state["awaiting_respawn"]:
                        state = maybe_respawn(state)
                        if state["awaiting_respawn"]:
                            interrupted = True
                            break
                        interrupted = True
                        break
                if interrupted:
                    continue
                break
        if len(rows) >= action_budget or not control_envelope_comparable:
            break
        if state["awaiting_respawn"]:
            state = maybe_respawn(state)
            if state["awaiting_respawn"]:
                break
            continue
        advanced = advance_evaluator_action(state, deficient["action"])
        state = advanced["state"]
        rows.append(_decorate_row_for_witness(advanced["row"], context_id=context_id, action_index=len(rows)+1))
        if len(rows) >= action_budget:
            break
        if state["awaiting_respawn"]:
            state = maybe_respawn(state)

    while len(rows) < action_budget and control_envelope_comparable:
        if state["awaiting_respawn"]:
            state = maybe_respawn(state)
            if state["awaiting_respawn"]:
                break
            continue
        checkpoint = build_public_checkpoint(
            world=state["world"],
            organism=state["organism"],
            predictive_state=state["predictive_state"],
            episode_index=int(state["episode_index"]),
        )
        action = _choose_rank_action(context_id, rows, checkpoint)
        advanced = advance_evaluator_action(state, action)
        state = advanced["state"]
        rows.append(_decorate_row_for_witness(advanced["row"], context_id=context_id, action_index=len(rows)+1))
        if len(rows) >= action_budget:
            break
        if state["awaiting_respawn"]:
            state = maybe_respawn(state)

    support_counts = _support_counts_from_rows(rows)
    support_report = {
        "stratum_counts": support_counts,
        "all_supported": all(value >= 4 for value in support_counts.values()),
    }
    rank_reports = _rank_reports_from_rows(context_id, rows)
    all_action_ranks_full = all(int(rank_reports[f"{context_id}::{action}"]["rank"]) == 13 for action in engine.ACTIONS)
    trajectory_hash = engine.canonical_hash(rows)
    result = {
        "rows": rows,
        "trajectory_hash": trajectory_hash,
        "action_count": len(rows),
        "max_life_index": max((row["life_index"] for row in rows), default=int(state["life_index"])),
        "respawn_count": int(state["respawn_count"]),
        "control_envelope_comparable": bool(control_envelope_comparable and len(rows) == action_budget),
        "support_report": support_report,
        "rank_reports": rank_reports,
        "all_action_ranks_full": all_action_ranks_full,
        "witness_found": bool((control_envelope_comparable and len(rows) == action_budget) and support_report["all_supported"] and all_action_ranks_full),
        "planner_contract": {
            "support_order": "strict_first_deficient_stratum_in_frozen_order",
            "cause_reorder": "disabled_unfrozen_cause_order",
            "rank_search": "current_checkpoint_only",
        },
    }
    result["ablation_report"] = {
        "reorder_count": 0,
        "trajectory_hash_changed": False,
        "main_trajectory_hash": trajectory_hash,
        "no_cause_trajectory_hash": trajectory_hash,
    }
    return result



def _panel_target_order() -> list[str]:
    return ["v0", "v1", "v2", "v3", "v4", "empty", "wall", "empty", "wall"]


def _initialize_panel_rollout_state(*, context_id: str, layout_id: str, world_seed: int, policy_seed: int, panel_rollout_id: int):
    world = microworld.initial_world_state(seed=world_seed, layout_id=layout_id, life_index=panel_rollout_id)
    organism = deepcopy(dict(engine.INITIAL_ORGANISM))
    predictive_state = predictive_control.reset_for_respawn(
        predictive_control.empty_state(), episode_index=panel_rollout_id - 1
    )
    run_id = f"{context_id}:panel_rollout={panel_rollout_id}"
    return {
        "run_id": run_id,
        "run_meta": engine.make_run_metadata(run_id, seed=policy_seed),
        "world": world,
        "organism": organism,
        "predictive_state": predictive_state,
        "life_index": panel_rollout_id,
        "episode_index": panel_rollout_id - 1,
        "episode_tick": 0,
        "global_sequence": 0,
        "action_count": 0,
        "respawn_count": 0,
        "awaiting_respawn": False,
    }


def _json_public_checkpoint(checkpoint, *, panel_rollout_id: int, target_front_token: str) -> dict[str, object]:
    return {
        "panel_rollout_id": panel_rollout_id,
        "target_front_token": target_front_token,
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "front_token": checkpoint["front_token"],
        "observation": deepcopy(checkpoint["observation"]),
        "organism": deepcopy(checkpoint["predictor_input"]["organism"]),
        "public_relative_belief": deepcopy(checkpoint["predictor_input"]["belief_summary"]),
        "full_features": checkpoint["full_features"].astype(np.float64, copy=False).tolist(),
        "quotient_features": checkpoint["quotient_features"].astype(np.float64, copy=False).tolist(),
    }


def build_deterministic_panel(*, context_id: str, layout_id: str, world_seed: int, policy_seed: int, panel_rollout_ids):
    panel_rollout_ids = tuple(panel_rollout_ids)
    target_order = _panel_target_order()
    rollouts = []
    raw_checkpoints = []
    for panel_rollout_id in panel_rollout_ids:
        state = _initialize_panel_rollout_state(
            context_id=context_id,
            layout_id=layout_id,
            world_seed=world_seed,
            policy_seed=policy_seed,
            panel_rollout_id=int(panel_rollout_id),
        )
        initial_world_hash = engine.canonical_hash(state["world"])
        initial_organism_hash = engine.canonical_hash(state["organism"])
        reached = []
        complete = True
        failure_reason = None
        failed_target = None
        for target in target_order:
            failed_target = target
            try:
                receipt = private_shortest_front_path(state["world"], target)
            except ValueError:
                complete = False
                failure_reason = "private_shortest_path_not_found"
                break
            for action in receipt["actions"]:
                advanced = advance_evaluator_action(state, action)
                state = advanced["state"]
                if state["awaiting_respawn"]:
                    complete = False
                    failure_reason = "natural_terminal_before_ninth_target"
                    break
            if not complete:
                break
            observation = microworld.policy_observation(state["world"], occlusion=True)
            if observation["visual"][1][2] != target:
                complete = False
                failure_reason = "private_shortest_path_not_found"
                break
            checkpoint = build_public_checkpoint(
                world=state["world"],
                organism=state["organism"],
                predictive_state=state["predictive_state"],
                episode_index=int(state["episode_index"]),
            )
            checkpoint_json = _json_public_checkpoint(checkpoint, panel_rollout_id=int(panel_rollout_id), target_front_token=target)
            checkpoint_json["_private_world"] = deepcopy(state["world"])
            checkpoint_json["_private_organism"] = deepcopy(state["organism"])
            raw_checkpoints.append(checkpoint_json)
            reached.append(target)
        if complete:
            failure_reason = None
            failed_target = None
        rollouts.append(
            {
                "panel_rollout_id": int(panel_rollout_id),
                "initial_world_hash": initial_world_hash,
                "initial_organism_hash": initial_organism_hash,
                "reached_target_order": reached,
                "respawn_count": int(state["respawn_count"]),
                "complete": len(reached) == len(target_order),
                "failure_reason": failure_reason,
                "failed_target": failed_target,
            }
        )

    retained_checkpoints = []
    seen_hashes = set()
    for checkpoint in raw_checkpoints:
        if checkpoint["checkpoint_hash"] in seen_hashes:
            continue
        seen_hashes.add(checkpoint["checkpoint_hash"])
        retained_checkpoints.append(deepcopy(checkpoint))

    rows = []
    for checkpoint in retained_checkpoints:
        for action in engine.ACTIONS:
            truth = evaluate_forced_action_truth(
                world=deepcopy(checkpoint["_private_world"]),
                organism=deepcopy(checkpoint["_private_organism"]),
                action=action,
                run_meta=engine.make_run_metadata(f"{context_id}:panel_truth:{checkpoint['panel_rollout_id']}", seed=policy_seed),
                episode_id=engine.episode_id_for(f"{context_id}:panel_truth:{checkpoint['panel_rollout_id']}", checkpoint["panel_rollout_id"] - 1),
                command_hash=engine.canonical_hash({"context_id": context_id, "checkpoint_hash": checkpoint["checkpoint_hash"], "action": action}),
                source_sequence=1,
                life_index=int(checkpoint["panel_rollout_id"]),
                episode_tick_after=1,
            )
            learner_projection = {
                "observation": deepcopy(checkpoint["observation"]),
                "organism": deepcopy(checkpoint["organism"]),
                "public_relative_belief": deepcopy(checkpoint["public_relative_belief"]),
                "quotient_features": deepcopy(checkpoint["quotient_features"]),
                "selected_action": action,
                "outcome_type": truth["truth"]["outcome_type"],
                "actual_delta": deepcopy(truth["truth"]["actual_delta"]),
                "terminal_receipt": deepcopy(truth["truth"]["terminal_receipt"]),
                "front_token": checkpoint["front_token"],
            }
            rows.append(
                {
                    "context_id": context_id,
                    "checkpoint_hash": checkpoint["checkpoint_hash"],
                    "selected_action": action,
                    "outcome_type": truth["truth"]["outcome_type"],
                    "learner_projection": learner_projection,
                    "full_features": deepcopy(checkpoint["full_features"]),
                    "front_token": checkpoint["front_token"],
                    "base_checkpoint_hash_before_truth": checkpoint["checkpoint_hash"],
                    "base_checkpoint_hash_after_truth": checkpoint["checkpoint_hash"],
                    "evaluator_truth": deepcopy(truth["truth"]),
                    "producer_receipts": deepcopy(truth["callable_receipts"]),
                }
            )

    public_raw_checkpoints = [{k: v for k, v in item.items() if not k.startswith("_private_")} for item in raw_checkpoints]
    public_retained_checkpoints = [{k: v for k, v in item.items() if not k.startswith("_private_")} for item in retained_checkpoints]
    before_dedupe = {token: sum(item["front_token"] == token for item in public_raw_checkpoints) for token in ("v0", "v1", "v2", "v3", "v4", "empty", "wall")}
    after_dedupe = {token: sum(item["front_token"] == token for item in public_retained_checkpoints) for token in ("v0", "v1", "v2", "v3", "v4", "empty", "wall")}
    required_floors = {"v0": 8, "v1": 8, "v2": 8, "v3": 8, "v4": 8, "empty": 16, "wall": 16}
    support_report = {
        "before_dedupe": before_dedupe,
        "after_dedupe": after_dedupe,
        "required_floors": required_floors,
        "passed": all(before_dedupe[token] >= floor and after_dedupe[token] >= floor for token, floor in required_floors.items()),
    }
    cell_counts = {}
    for row in rows:
        key = "::".join((context_id, row["selected_action"], row["front_token"], row["outcome_type"]))
        cell_counts[key] = cell_counts.get(key, 0) + 1
    required_floor_by_cell = {key: required_floors[key.split("::")[-2]] for key in cell_counts}
    cell_support_report = {
        "cell_counts": cell_counts,
        "required_floor_by_cell": required_floor_by_cell,
        "passed": all(count >= required_floors[key.split("::")[-2]] for key, count in cell_counts.items()),
    }
    rank_reports = _rank_reports_from_rows(context_id, rows)
    construction_complete = all(item["complete"] for item in rollouts)
    panel_capacity_admitted = construction_complete and support_report["passed"] and cell_support_report["passed"] and all(int(rank_reports[f"{context_id}::{action}"]["rank"]) == 13 for action in engine.ACTIONS)
    panel = {
        "panel_rollout_ids": list(panel_rollout_ids),
        "target_order": target_order,
        "rollouts": rollouts,
        "raw_checkpoints": public_raw_checkpoints,
        "retained_checkpoints": public_retained_checkpoints,
        "rows": rows,
        "support_report": support_report,
        "cell_support_report": cell_support_report,
        "rank_reports": rank_reports,
        "construction_complete": construction_complete,
        "panel_capacity_admitted": panel_capacity_admitted,
    }
    panel["panel_hash"] = engine.canonical_hash(
        {
            "rollouts": panel["rollouts"],
            "retained_checkpoint_hashes": [item["checkpoint_hash"] for item in panel["retained_checkpoints"]],
            "rows": panel["rows"],
            "support_report": panel["support_report"],
            "cell_support_report": panel["cell_support_report"],
            "rank_reports": panel["rank_reports"],
            "panel_capacity_admitted": panel["panel_capacity_admitted"],
        }
    )
    return panel

def build_public_checkpoint(*, world, organism, predictive_state, episode_index: int) -> dict[str, object]:
    microworld.verify_world_state(world)
    predictive_control._validate_organism(organism)  # noqa: SLF001
    predictive_control.validate_state(predictive_state)
    if type(episode_index) is not int or episode_index < 0:
        raise ValueError("episode_index must be non-negative")

    observation = microworld.policy_observation(world, occlusion=True)
    prepared_predictive_state, observe_belief_receipt = predictive_control.observe_belief(
        predictive_state,
        observation=observation,
        episode_index=episode_index,
        mode="relative",
    )
    predictor_input = predictive_control.predictor_input_snapshot(
        prepared_predictive_state,
        observation=observation,
        organism=organism,
        relative_map_mode="relative",
    )
    full_features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
        organism=predictor_input["organism"],
        summary=predictor_input["belief_summary"],
    ).astype(np.float64, copy=False)
    quotient = quotient_features(full_features)
    dedupe_projection = {
        "observation": deepcopy(predictor_input["observation"]),
        "organism": deepcopy(predictor_input["organism"]),
        "public_relative_belief": deepcopy(predictor_input["belief_summary"]),
        "quotient_features": quotient.astype(np.float64, copy=False).tolist(),
    }
    checkpoint_hash = engine.canonical_hash(dedupe_projection)
    return {
        "observation": observation,
        "predictor_input": predictor_input,
        "prepared_predictive_state": prepared_predictive_state,
        "observe_belief_receipt": observe_belief_receipt,
        "full_features": full_features,
        "quotient_features": quotient,
        "front_token": observation["visual"][1][2],
        "dedupe_projection": dedupe_projection,
        "checkpoint_hash": checkpoint_hash,
        "receipt": {
            "checkpoint_hash": checkpoint_hash,
            "front_token": observation["visual"][1][2],
            "observation_hash": engine.canonical_hash(observation),
        },
    }


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--internal-digest":
        raise SystemExit(_internal_digest_probe(sys.argv[2], int(sys.argv[3]), sys.argv[4]))
    if len(sys.argv) >= 7 and sys.argv[1] == "--internal-stage":
        raise SystemExit(_internal_stage_probe(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6]))
