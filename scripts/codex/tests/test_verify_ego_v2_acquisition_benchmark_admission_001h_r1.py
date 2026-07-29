from __future__ import annotations

import importlib.util
import base64
from collections import deque
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import numpy as np
import pytest

from labs.ego_life_playground_v0 import microworld, predictive_control


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "verify_ego_v2_acquisition_benchmark_admission_001h_r1.py"
)


def _load_module():
    assert SCRIPT_PATH.exists(), "001H-R1 verifier module is not implemented"
    spec = importlib.util.spec_from_file_location("verify_001h_r1", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reference_quotient_removes_both_structural_dependencies():
    module = _load_module()
    full = np.asarray(
        [
            1.0,
            0.45,
            0.62,
            0.50,
            0.43,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.25,
            0.60,
        ],
        dtype=np.float64,
    )

    quotient = module.quotient_features(full)

    assert module.QUOTIENT_FEATURE_NAMES == tuple(
        name
        for name in module.FEATURE_NAMES
        if name not in {"front_occluded", "front_wall"}
    )
    assert quotient.shape == (13,)
    assert quotient.dtype == np.dtype("<f8")
    assert np.array_equal(
        quotient,
        np.delete(
            full,
            [
                module.FEATURE_INDEX["front_wall"],
                module.FEATURE_INDEX["front_occluded"],
            ],
        ),
    )


def test_runtime_receipt_fail_closes_outside_the_pinned_numeric_contract():
    module = _load_module()
    receipt = module.runtime_receipt()

    assert receipt["python_version"] == "3.12.13"
    assert receipt["numpy_version"] == "2.2.6"
    assert receipt["float_dtype"] == "<f8"
    assert receipt["numpy_matrix_rank_tolerance"] == "numpy.linalg.matrix_rank_default"
    assert receipt["contract_satisfied"] is True


def test_fresh_process_digest_receipt_is_process_bound_and_tamper_evident(
    tmp_path: Path,
):
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload = {
        "task_id": "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1",
        "rows": [{"sequence": 1, "selected_action": "rest"}],
    }
    payload_path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    receipt = module.spawn_fresh_digest_probe(payload_path)

    assert receipt["parent_pid"] == os.getpid()
    assert receipt["child_pid"] != os.getpid()
    assert receipt["python_executable"] == sys.executable
    assert receipt["input_sha256"] == module._sha256_file(payload_path)  # noqa: SLF001
    assert receipt["payload_digest"] == module.engine.canonical_hash(payload)
    assert receipt["command"][:3] == [sys.executable, "-I", "-B"]
    assert module.validate_fresh_digest_receipt(payload_path, receipt) is True

    same_process = deepcopy(receipt)
    same_process["child_pid"] = same_process["parent_pid"]
    with pytest.raises(ValueError, match="child process"):
        module.validate_fresh_digest_receipt(payload_path, same_process)

    digest_tampered = deepcopy(receipt)
    digest_tampered["payload_digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        module.validate_fresh_digest_receipt(payload_path, digest_tampered)


def test_context_stage_subprocess_is_bound_and_deterministic_for_control():
    module = _load_module()
    spec = deepcopy(module.FROZEN_CONTEXT_SPECS[0])
    assert "max_life_index" not in spec
    assert "max_respawn_count" not in spec

    first = module.spawn_context_stage("control", spec)
    second = module.spawn_context_stage("control", spec)

    assert first["stage"] == second["stage"] == "control"
    assert first["context_spec"] == second["context_spec"] == spec
    assert first["payload"] == second["payload"]
    assert first["payload"]["prefix"]["action_count"] == 89
    assert first["payload"]["recovery_exact"] is True
    assert first["payload_digest"] == second["payload_digest"]
    assert first["request_digest"] == second["request_digest"]
    assert first["child_pid"] != os.getpid()
    assert second["child_pid"] != os.getpid()
    assert first["child_pid"] != second["child_pid"]
    assert first["runtime_receipt"]["contract_satisfied"] is True
    assert first["command"][:3] == [sys.executable, "-I", "-B"]
    assert module.validate_context_stage_receipt(first) is True
    assert module.validate_context_stage_receipt(second) is True

    tampered = deepcopy(first)
    tampered["payload"]["prefix"]["action_count"] = 88
    with pytest.raises(ValueError, match="stage receipt"):
        module.validate_context_stage_receipt(tampered)

    with pytest.raises(ValueError, match="stage"):
        module.spawn_context_stage("heldout", spec)


def test_fresh_stage_pair_summary_records_process_receipts_and_mismatch():
    module = _load_module()
    payload = {"rows": [{"sequence": 1, "selected_action": "rest"}]}
    first = {
        "child_pid": 101,
        "parent_pid": 99,
        "python_executable": sys.executable,
        "runtime_receipt": module.runtime_receipt(),
        "request_digest": "a" * 64,
        "payload_digest": module.engine.canonical_hash(payload),
        "payload": deepcopy(payload),
    }
    second = {
        **deepcopy(first),
        "child_pid": 102,
        "request_digest": "b" * 64,
    }

    equal = module.summarize_fresh_stage_pair(first, second)

    assert equal["equal"] is True
    assert equal["first_child_pid"] == 101
    assert equal["second_child_pid"] == 102
    assert equal["first_child_pid"] != equal["second_child_pid"]
    assert equal["first_payload_digest"] == equal["second_payload_digest"]
    assert equal["python_executable"] == sys.executable
    assert equal["runtime_receipt"] == module.runtime_receipt()

    second["payload"]["rows"][0]["selected_action"] = "interact"
    second["payload_digest"] = module.engine.canonical_hash(second["payload"])
    mismatch = module.summarize_fresh_stage_pair(first, second)
    assert mismatch["equal"] is False
    assert mismatch["first_payload_digest"] != mismatch["second_payload_digest"]

    same_child = deepcopy(first)
    assert module.summarize_fresh_stage_pair(first, same_child)["equal"] is False


def test_witness_stage_consumes_validated_control_bounds_and_panel_is_fixed():
    module = _load_module()
    spec = deepcopy(module.FROZEN_CONTEXT_SPECS[0])
    control = module.spawn_context_stage("control", spec)

    witness = module.spawn_context_stage(
        "witness",
        spec,
        control_receipt=control,
    )
    assert witness["control_dependency_digest"] == control["payload_digest"]
    assert witness["payload"]["action_count"] == 89
    assert witness["payload"]["max_life_index"] <= control["payload"]["prefix"][
        "max_life_index"
    ]
    assert witness["payload"]["respawn_count"] <= control["payload"]["prefix"][
        "respawn_count"
    ]
    assert module.validate_context_stage_receipt(witness) is True

    panel = module.spawn_context_stage("panel", spec)
    assert panel["payload"]["panel_rollout_ids"] == list(range(9, 17))
    assert panel["payload"]["target_order"] == [
        "v0",
        "v1",
        "v2",
        "v3",
        "v4",
        "empty",
        "wall",
        "empty",
        "wall",
    ]
    assert module.validate_context_stage_receipt(panel) is True

    control_tampered = deepcopy(control)
    control_tampered["payload"]["prefix"]["max_life_index"] = 999
    with pytest.raises(ValueError, match="stage receipt"):
        module.spawn_context_stage(
            "witness",
            spec,
            control_receipt=control_tampered,
        )


def test_artifact_manifest_is_exact_and_rejects_tamper_or_extra_file(tmp_path: Path):
    module = _load_module()
    packet = tmp_path / "packet"
    packet.mkdir()
    (packet / "result.json").write_text('{"verdict":"synthetic"}\n', encoding="utf-8")
    (packet / "claim_ceiling.txt").write_text("bounded test\n", encoding="utf-8")

    manifest = module.build_artifact_manifest(packet)
    (packet / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    assert set(manifest["files"]) == {"claim_ceiling.txt", "result.json"}
    assert module.verify_artifact_manifest(packet) is True

    (packet / "result.json").write_text('{"verdict":"tampered"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        module.verify_artifact_manifest(packet)

    (packet / "result.json").write_text('{"verdict":"synthetic"}\n', encoding="utf-8")
    (packet / "unexpected.txt").write_text("extra\n", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        module.verify_artifact_manifest(packet)


def test_formal_packet_writer_emits_exact_required_negative_artifact_set(
    tmp_path: Path,
):
    module = _load_module()
    context_id = "synthetic:world=52:policy=711"
    control_records = [
        {
            "sequence": 1,
            "transition_kind": "action",
            "selected_action": "rest",
            "life_index": 1,
        }
    ]
    witness_feature = _full_rank_reference_rows(module)[0]
    witness_rows = [
        {
            "context_id": context_id,
            "action_index": 1,
            "global_sequence": 1,
            "transition_kind": "action",
            "life_index": 1,
            "selected_action": "rest",
            "outcome_type": "rested",
            "full_features": witness_feature.tolist(),
            "learner_projection": {
                "front_token": "empty",
                "quotient_features": module.quotient_features(
                    witness_feature
                ).tolist(),
            },
        }
    ]
    witness_support = module._support_counts_from_rows(witness_rows)  # noqa: SLF001
    witness_trajectory_hash = module.engine.canonical_hash(witness_rows)
    floors = {"v0": 8, "v1": 8, "v2": 8, "v3": 8, "v4": 8, "empty": 16, "wall": 16}
    zero_tokens = {token: 0 for token in floors}
    panel_rank_reports = module._rank_reports_from_rows(context_id, [])  # noqa: SLF001
    panel_support = {
        "before_dedupe": deepcopy(zero_tokens),
        "after_dedupe": deepcopy(zero_tokens),
        "required_floors": deepcopy(floors),
        "passed": False,
    }
    panel_cell_support = {
        "cell_counts": {},
        "required_floor_by_cell": {},
        "passed": True,
    }
    panel_rollouts = [
        {"panel_rollout_id": rollout_id, "complete": False}
        for rollout_id in range(9, 17)
    ]
    panel_hash = module.engine.canonical_hash(
        {
            "rollouts": panel_rollouts,
            "retained_checkpoint_hashes": [],
            "rows": [],
            "support_report": panel_support,
            "cell_support_report": panel_cell_support,
            "rank_reports": panel_rank_reports,
            "panel_capacity_admitted": False,
        }
    )
    provenance_document = {
        "schema_version": "ego.v2.001h_r1.pre_run_provenance.v1",
        "task_id": "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1",
        "implementation_commit": "1" * 40,
        "provenance_path": (
            "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/"
            "PRE_RUN_PROVENANCE.json"
        ),
        "runtime_receipt": module.runtime_receipt(),
        "engine_code_path_hash": "f" * 64,
        "context_specs": list(module.FROZEN_CONTEXT_SPECS),
        "source_hashes": {
            path: "a" * 64 for path in module.REQUIRED_PROVENANCE_SOURCE_PATHS
        },
        "input_hashes": {
            path: "b" * 64 for path in module.REQUIRED_PROVENANCE_INPUT_PATHS
        },
        "dependency_hashes": {
            path: "c" * 64
            for path in module.REQUIRED_PROVENANCE_DEPENDENCY_PATHS
        },
    }
    bundle = {
        "contexts": {
            context_id: {
                    "control": {
                        "prefix_records": control_records,
                        "prefix": module.summarize_control_prefix(
                            control_records, action_budget=1
                        ),
                },
                "witness": {
                    "rows": witness_rows,
                    "support_report": {
                        "stratum_counts": witness_support,
                        "all_supported": False,
                    },
                    "rank_reports": {},
                    "control_envelope_comparable": True,
                    "witness_found": False,
                    "ablation_report": {
                        "reorder_count": 0,
                        "trajectory_hash_changed": False,
                        "main_trajectory_hash": witness_trajectory_hash,
                        "no_cause_trajectory_hash": witness_trajectory_hash,
                    },
                },
                "panel": {
                    "rows": [],
                    "panel_rollout_ids": list(range(9, 17)),
                    "target_order": [
                        "v0",
                        "v1",
                        "v2",
                        "v3",
                        "v4",
                        "empty",
                        "wall",
                        "empty",
                        "wall",
                    ],
                    "rollouts": panel_rollouts,
                    "raw_checkpoints": [],
                    "retained_checkpoints": [],
                    "support_report": panel_support,
                    "cell_support_report": panel_cell_support,
                    "rank_reports": panel_rank_reports,
                    "construction_complete": False,
                    "panel_capacity_admitted": False,
                    "panel_hash": panel_hash,
                },
            }
        },
        "provenance_report": {"passed": True, "provenance_commit": "2" * 40},
        "provenance_document": provenance_document,
        "pre_run_observation": {
            "head": "2" * 40,
            "head_parent": "1" * 40,
            "source_hashes": deepcopy(provenance_document["source_hashes"]),
            "input_hashes": deepcopy(provenance_document["input_hashes"]),
            "dependency_hashes": deepcopy(provenance_document["dependency_hashes"]),
        },
        "leakage_report": {
            "all_clean": True,
            "all_positive_controls_detected": True,
        },
        "independent_reports": {
            context_id: {
                "reported_values_match": True,
                "producer_receipts_valid": True,
                "hashes_valid": True,
                "check_map": {
                    "control_envelope_comparable": True,
                    "privileged_support_witness_found": False,
                    "deterministic_panel_capacity_admitted": False,
                },
            }
        },
        "fresh_recompute_report": {"equal": True},
        "tamper_report": {"all_tamper_controls_rejected": True},
        "validity": {
            "pre_run_provenance_valid": True,
            "runtime_contract_satisfied": True,
            "source_hashes_match": True,
            "leakage_clean": True,
            "positive_controls_detected": True,
            "fresh_process_recompute_equal": True,
            "all_tamper_controls_rejected": True,
        },
        "adjudication": {
            "provenance_clean": True,
            "control_envelope_comparable": True,
            "privileged_support_witness_found": False,
            "deterministic_panel_capacity_admitted": False,
            "verdict": "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND",
            "failure_reasons": ["privileged_support_witness_not_found"],
        },
    }
    packet = tmp_path / "packet"

    result = module.write_formal_packet(packet, bundle)

    expected = {
        "result.json",
        "control_rows.jsonl",
        "privileged_witness_rows.jsonl",
        "panel_rows.jsonl",
        "support_report.json",
        "panel_manifest.json",
        "ablation_report.json",
        "leakage_report.json",
        "recompute_report.json",
        "failure_manifest.json",
        "claim_ceiling.txt",
        "artifact_manifest.json",
    }
    assert {path.name for path in packet.iterdir()} == expected
    assert result["verdict"] == "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    assert result["model_training_executed"] is False
    assert result["fresh_worlds_consumed"] == []
    assert result["heldout_effect_adjudicated"] is False
    assert module.verify_formal_packet(packet) == result

    recompute = json.loads(
        (packet / "recompute_report.json").read_text(encoding="utf-8")
    )
    assert recompute["provenance_report"] == bundle["provenance_report"]
    assert recompute["tamper_report"] == bundle["tamper_report"]

    semantic_packet = tmp_path / "semantic-packet"
    module.write_formal_packet(semantic_packet, bundle)
    semantic_recompute_path = semantic_packet / "recompute_report.json"
    semantic_recompute = json.loads(
        semantic_recompute_path.read_text(encoding="utf-8")
    )
    semantic_recompute["fresh_recompute_report"]["equal"] = False
    semantic_recompute_path.write_text(
        json.dumps(semantic_recompute, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (semantic_packet / "artifact_manifest.json").write_text(
        json.dumps(
            module.build_artifact_manifest(semantic_packet),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="semantic"):
        module.verify_formal_packet(semantic_packet)

    semantic_tampers = {
        "support": (
            "support_report.json",
            lambda value: value["contexts"][context_id]["witness_support"][
                "stratum_counts"
            ].__setitem__("rest::rested", 999),
        ),
        "support-aggregate": (
            "support_report.json",
            lambda value: value.__setitem__("all_contexts_witness_found", True),
        ),
        "panel": (
            "panel_manifest.json",
            lambda value: value["contexts"][context_id].__setitem__(
                "target_order", list(reversed(value["contexts"][context_id]["target_order"]))
            ),
        ),
        "ablation": (
            "ablation_report.json",
            lambda value: value["contexts"][context_id].__setitem__(
                "main_trajectory_hash", "0" * 64
            ),
        ),
    }
    for tamper_name, (file_name, mutate) in semantic_tampers.items():
        tampered_packet = tmp_path / f"{tamper_name}-semantic-packet"
        module.write_formal_packet(tampered_packet, bundle)
        artifact_path = tampered_packet / file_name
        artifact_value = json.loads(artifact_path.read_text(encoding="utf-8"))
        mutate(artifact_value)
        artifact_path.write_text(
            json.dumps(artifact_value, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (tampered_packet / "artifact_manifest.json").write_text(
            json.dumps(
                module.build_artifact_manifest(tampered_packet),
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="semantic"):
            module.verify_formal_packet(tampered_packet)

    result_tampers = {
        "training": lambda value: value.__setitem__("model_training_executed", True),
        "fresh": lambda value: value.__setitem__("fresh_worlds_consumed", [151]),
        "heldout": lambda value: value.__setitem__("heldout_effect_adjudicated", True),
        "contexts": lambda value: value.__setitem__("context_specs", []),
        "source-hash": lambda value: value["source_hashes"].__setitem__(
            next(iter(value["source_hashes"])), "0" * 64
        ),
    }
    for tamper_name, mutate in result_tampers.items():
        tampered_packet = tmp_path / f"result-{tamper_name}-semantic-packet"
        module.write_formal_packet(tampered_packet, bundle)
        result_path = tampered_packet / "result.json"
        result_value = json.loads(result_path.read_text(encoding="utf-8"))
        mutate(result_value)
        result_path.write_text(
            json.dumps(result_value, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        (tampered_packet / "artifact_manifest.json").write_text(
            json.dumps(
                module.build_artifact_manifest(tampered_packet),
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="semantic"):
            module.verify_formal_packet(tampered_packet)

    (packet / "result.json").write_text('{"verdict":"tampered"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        module.verify_formal_packet(packet)


def test_formal_preconditions_fail_closed_before_any_execution(tmp_path: Path):
    module = _load_module()
    output = tmp_path / "formal-output"
    missing_provenance = tmp_path / "missing-provenance.json"

    with pytest.raises(ValueError, match="pre-run provenance"):
        module.run_formal(
            output_dir=output,
            provenance_path=missing_provenance,
        )
    assert not output.exists()

    output.mkdir()
    (output / "stale.txt").write_text("stale\n", encoding="utf-8")
    provenance = tmp_path / "provenance.json"
    provenance.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="output directory"):
        module.run_formal(output_dir=output, provenance_path=provenance)


def test_collect_pre_run_observation_binds_live_git_hashes_and_output_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = _load_module()
    provenance = tmp_path / "PRE_RUN_PROVENANCE.json"
    provenance.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "formal-output"
    provenance_relpath = (
        "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/"
        "PRE_RUN_PROVENANCE.json"
    )
    git_answers = {
        ("rev-parse", "--show-toplevel"): REPO_ROOT.as_posix(),
        ("branch", "--show-current"): "codex/ego-v2-bayesian-active-identification-001h",
        ("rev-parse", "HEAD"): "2" * 40,
        ("rev-parse", "HEAD^"): "1" * 40,
        ("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"): provenance_relpath,
        ("status", "--porcelain"): "",
    }

    def fake_git_stdout(*args):
        return git_answers[tuple(args)]

    monkeypatch.setattr(module, "_git_stdout", fake_git_stdout)
    monkeypatch.setattr(module, "_git_success", lambda *_args: True)
    monkeypatch.setattr(module, "_sha256_file", lambda path: "a" * 64)
    monkeypatch.setattr(
        module,
        "runtime_receipt",
        lambda: {
            "python_version": "3.12.13",
            "numpy_version": "2.2.6",
            "float_dtype": "<f8",
            "numpy_matrix_rank_tolerance": "numpy.linalg.matrix_rank_default",
            "contract_satisfied": True,
        },
    )
    monkeypatch.setattr(module.engine, "compute_code_path_hash", lambda: "f" * 64)

    observation = module.collect_pre_run_observation(
        output_dir=output,
        provenance_path=provenance,
    )

    assert observation["repository_root"] == REPO_ROOT.as_posix()
    assert observation["head"] == "2" * 40
    assert observation["head_parent"] == "1" * 40
    assert observation["head_changed_paths"] == [provenance_relpath]
    assert observation["worktree_clean"] is True
    assert observation["index_clean"] is True
    assert observation["provenance_tracked_at_head"] is True
    assert observation["output_absent_or_empty"] is True
    assert set(observation["source_hashes"]) == set(
        module.REQUIRED_PROVENANCE_SOURCE_PATHS
    )
    assert set(observation["input_hashes"]) == set(
        module.REQUIRED_PROVENANCE_INPUT_PATHS
    )
    assert set(observation["dependency_hashes"]) == set(
        module.REQUIRED_PROVENANCE_DEPENDENCY_PATHS
    )


def test_run_formal_orchestrates_two_fresh_stage_passes_before_one_packet_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = _load_module()
    output = tmp_path / "formal-output"
    provenance = tmp_path / "PRE_RUN_PROVENANCE.json"
    provenance.write_text(
        json.dumps({"source_hashes": {"source.py": "a" * 64}}) + "\n",
        encoding="utf-8",
    )
    observation = {"runtime_receipt": {"contract_satisfied": True}}
    monkeypatch.setattr(
        module,
        "collect_pre_run_observation",
        lambda **_kwargs: deepcopy(observation),
    )
    monkeypatch.setattr(
        module,
        "validate_pre_run_provenance_document",
        lambda _document, _observation: {"passed": True},
    )

    calls = []

    def fake_stage(stage, spec, control_receipt=None):
        calls.append((stage, spec["context_id"], control_receipt is not None))
        if stage == "control":
            payload = {"prefix_records": [], "prefix": {"action_count": 89}}
        elif stage == "witness":
            assert control_receipt is not None
            payload = {
                "rows": [{"learner_projection": {"observation": "public"}}],
                "support_report": {},
                "control_envelope_comparable": True,
                "witness_found": False,
                "ablation_report": {},
            }
        else:
            payload = {
                "rows": [
                    {
                        "learner_projection": {
                            "observation": "public",
                            "panel_public": True,
                        }
                    }
                ],
                "panel_capacity_admitted": False,
            }
        return {
            "stage": stage,
            "context_spec": deepcopy(spec),
            "payload": payload,
            "payload_digest": module.engine.canonical_hash(payload),
            "child_pid": 1000 + len(calls),
            "parent_pid": os.getpid(),
            "python_executable": sys.executable,
            "runtime_receipt": {"contract_satisfied": True},
            "request_digest": f"{len(calls):064x}",
        }

    monkeypatch.setattr(module, "spawn_context_stage", fake_stage)
    monkeypatch.setattr(module, "validate_context_stage_receipt", lambda _receipt: True)
    context_report = {
        "reported_values_match": True,
        "producer_receipts_valid": True,
        "hashes_valid": True,
        "check_map": {
            "control_envelope_comparable": True,
            "privileged_support_witness_found": False,
            "deterministic_panel_capacity_admitted": False,
        },
    }
    monkeypatch.setattr(
        module,
        "independent_reduce_context",
        lambda **_kwargs: deepcopy(context_report),
    )
    monkeypatch.setattr(
        module, "scan_learner_projection", lambda _row: {"clean": True, "findings": []}
    )
    monkeypatch.setattr(
        module,
        "run_leakage_positive_controls",
        lambda _row: {"all_positive_controls_detected": True, "controls": {}},
    )
    monkeypatch.setattr(
        module,
        "run_tamper_controls",
        lambda **_kwargs: {"all_tamper_controls_rejected": True, "controls": {}},
    )
    adjudication = {
        "provenance_clean": True,
        "control_envelope_comparable": True,
        "privileged_support_witness_found": False,
        "deterministic_panel_capacity_admitted": False,
        "verdict": "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND",
        "failure_reasons": ["false:privileged_support_witness_found"],
    }
    validity_seen = {}

    def fake_adjudication(reports, validity):
        assert set(reports) == {
            spec["context_id"] for spec in module.FROZEN_CONTEXT_SPECS
        }
        validity_seen.update(validity)
        return deepcopy(adjudication)

    monkeypatch.setattr(module, "derive_adjudication", fake_adjudication)
    bundle_seen = {}

    def fake_write(packet, bundle):
        bundle_seen.update(deepcopy(bundle))
        Path(packet).mkdir()
        result = {"verdict": adjudication["verdict"]}
        (Path(packet) / "result.json").write_text(
            json.dumps(result) + "\n", encoding="utf-8"
        )
        return result

    monkeypatch.setattr(module, "write_formal_packet", fake_write)
    monkeypatch.setattr(
        module,
        "verify_formal_packet",
        lambda packet: json.loads((Path(packet) / "result.json").read_text()),
    )

    result = module.run_formal(output_dir=output, provenance_path=provenance)

    assert result["verdict"] == "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    assert len(calls) == len(module.FROZEN_CONTEXT_SPECS) * 3 * 2
    for context_id in {spec["context_id"] for spec in module.FROZEN_CONTEXT_SPECS}:
        assert calls.count(("control", context_id, False)) == 2
        assert calls.count(("witness", context_id, True)) == 2
        assert calls.count(("panel", context_id, False)) == 2
    assert bundle_seen["fresh_recompute_report"]["equal"] is True
    for context_report in bundle_seen["fresh_recompute_report"]["contexts"].values():
        for stage_report in context_report.values():
            assert stage_report["equal"] is True
            assert stage_report["first_child_pid"] != stage_report["second_child_pid"]
    assert bundle_seen["leakage_report"]["scanned_row_count"] == 4
    assert bundle_seen["leakage_report"]["clean_row_count"] == 4
    assert len(bundle_seen["leakage_report"]["row_scans"]) == 4
    assert bundle_seen["leakage_report"]["positive_control_report"] == {
        "all_positive_controls_detected": True,
        "controls": {},
    }
    assert len(
        bundle_seen["leakage_report"][
            "positive_control_reports_by_projection_schema"
        ]
    ) == 2
    assert validity_seen == {
        "pre_run_provenance_valid": True,
        "runtime_contract_satisfied": True,
        "source_hashes_match": True,
        "leakage_clean": True,
        "positive_controls_detected": True,
        "fresh_process_recompute_equal": True,
        "all_tamper_controls_rejected": True,
    }


def test_pre_run_provenance_document_binds_parent_bytes_and_heldout_firewall():
    module = _load_module()
    assert module.REQUIRED_PROVENANCE_SOURCE_PATHS == (
        "docs/codex/tasks/EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H.md",
        "docs/codex/tasks/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1.md",
        (
            "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/"
            "COLLISION_RECORD.md"
        ),
        (
            "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/"
            "IMPLEMENTATION_PLAN.md"
        ),
        "scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py",
        (
            "scripts/codex/tests/"
            "test_verify_ego_v2_acquisition_benchmark_admission_001h_r1.py"
        ),
        "labs/ego_life_playground_v0/engine.py",
        "labs/ego_life_playground_v0/microworld.py",
        "labs/ego_life_playground_v0/predictive_control.py",
        "labs/ego_life_playground_v0/store.py",
    )
    assert module.REQUIRED_PROVENANCE_INPUT_PATHS == (
        "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/result.json",
        (
            "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/"
            "smoke_p0_cross_v1.sqlite3"
        ),
        (
            "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/"
            "smoke_p2_vertical_v1.sqlite3"
        ),
        (
            "artifacts/EGO-V2-P1-ADDITIVE-PREDICTION-HEADROOM-DIAGNOSTIC-001C-R4/"
            "result.json"
        ),
    )
    assert module.REQUIRED_PROVENANCE_DEPENDENCY_PATHS == (
        "requirements-ego-v2.txt",
    )
    provenance_relpath = (
        "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/"
        "PRE_RUN_PROVENANCE.json"
    )
    output_relpath = (
        "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1"
    )
    source_hashes = {
        path: f"{index + 1:x}" * 64
        for index, path in enumerate(module.REQUIRED_PROVENANCE_SOURCE_PATHS)
    }
    input_hashes = {
        path: f"{index + 10:x}"[-1] * 64
        for index, path in enumerate(module.REQUIRED_PROVENANCE_INPUT_PATHS)
    }
    dependency_hashes = {
        path: "e" * 64 for path in module.REQUIRED_PROVENANCE_DEPENDENCY_PATHS
    }
    document = {
        "schema_version": "ego.v2.001h_r1.pre_run_provenance.v1",
        "task_id": "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1",
        "repository_root": REPO_ROOT.as_posix(),
        "branch": "codex/ego-v2-bayesian-active-identification-001h",
        "implementation_commit": "1" * 40,
        "provenance_path": provenance_relpath,
        "output_dir": output_relpath,
        "runtime_receipt": module.runtime_receipt(),
        "engine_code_path_hash": "f" * 64,
        "source_hashes": source_hashes,
        "input_hashes": input_hashes,
        "dependency_hashes": dependency_hashes,
        "context_specs": list(module.FROZEN_CONTEXT_SPECS),
        "heldout_firewall": {
            "contaminated_world_interval_inclusive": [30, 150],
            "future_fresh_world_must_be_greater_than": 150,
            "fresh_worlds_consumed": [],
            "forbidden_reuse_as_fresh_policy_seeds": [721, 722],
            "model_training_executed": False,
        },
        "output_precondition": "absent_or_empty",
    }
    observation = {
        "repository_root": REPO_ROOT.as_posix(),
        "branch": document["branch"],
        "head": "2" * 40,
        "head_parent": document["implementation_commit"],
        "head_changed_paths": [provenance_relpath],
        "worktree_clean": True,
        "index_clean": True,
        "provenance_tracked_at_head": True,
        "runtime_receipt": deepcopy(document["runtime_receipt"]),
        "engine_code_path_hash": document["engine_code_path_hash"],
        "source_hashes": deepcopy(source_hashes),
        "input_hashes": deepcopy(input_hashes),
        "dependency_hashes": deepcopy(dependency_hashes),
        "output_dir": output_relpath,
        "output_absent_or_empty": True,
    }

    report = module.validate_pre_run_provenance_document(document, observation)
    assert report["passed"] is True
    assert report["failure_reasons"] == []
    assert report["provenance_commit"] == observation["head"]

    source_tampered = deepcopy(observation)
    first_source = next(iter(source_tampered["source_hashes"]))
    source_tampered["source_hashes"][first_source] = "0" * 64
    with pytest.raises(ValueError, match="source hash"):
        module.validate_pre_run_provenance_document(document, source_tampered)

    extra_change = deepcopy(observation)
    extra_change["head_changed_paths"].append("labs/ego_life_playground_v0/engine.py")
    with pytest.raises(ValueError, match="provenance commit"):
        module.validate_pre_run_provenance_document(document, extra_change)

    dirty = deepcopy(observation)
    dirty["worktree_clean"] = False
    with pytest.raises(ValueError, match="worktree"):
        module.validate_pre_run_provenance_document(document, dirty)

    heldout_tampered = deepcopy(document)
    heldout_tampered["context_specs"][0]["world_seed"] = 160
    with pytest.raises(ValueError, match="context specs"):
        module.validate_pre_run_provenance_document(heldout_tampered, observation)

    output_tampered = deepcopy(document)
    output_tampered["output_dir"] = "artifacts/wrong-output"
    with pytest.raises(ValueError, match="output directory"):
        module.validate_pre_run_provenance_document(output_tampered, observation)


def _full_rank_reference_rows(module):
    rows = []
    baseline = np.zeros(len(module.FEATURE_NAMES), dtype=np.float64)
    baseline[module.FEATURE_INDEX["bias"]] = 1.0
    baseline[module.FEATURE_INDEX["front_wall"]] = 1.0
    rows.append(baseline)
    for name in (
        "energy",
        "safety",
        "connection",
        "stimulation",
        "known_cell_fraction",
        "known_object_fraction",
    ):
        row = baseline.copy()
        row[module.FEATURE_INDEX[name]] = 1.0
        rows.append(row)
    for name in (
        "front_empty",
        "front_v0",
        "front_v1",
        "front_v2",
        "front_v3",
        "front_v4",
    ):
        row = baseline.copy()
        row[module.FEATURE_INDEX["front_wall"]] = 0.0
        row[module.FEATURE_INDEX[name]] = 1.0
        rows.append(row)
    return rows


def test_rank_reports_are_context_action_local_and_gate_thirteen_columns():
    module = _load_module()
    full_rank = _full_rank_reference_rows(module)
    rows = [
        {"context_id": "c1", "action": "rest", "features": row.tolist()}
        for row in full_rank
    ]
    rows.extend(
        {"context_id": "c2", "action": "rest", "features": row.tolist()}
        for row in full_rank[:-1]
    )

    report = module.rank_reports_by_context_action(rows)

    assert report["c1::rest"]["rank"] == 13
    assert report["c1::rest"]["full_rank"] is True
    assert len(report["c1::rest"]["singular_values"]) == 13
    assert report["c2::rest"]["rank"] == 12
    assert report["c2::rest"]["full_rank"] is False
    dependencies = module.structural_feature_checks(full_rank)
    assert dependencies == {
        "front_occluded_always_zero": True,
        "bias_equals_reachable_front_sum": True,
        "raw_rank_at_most_13_after_constant_drop": True,
    }


def test_control_prefix_uses_action_budget_and_derives_lifecycle_bounds():
    module = _load_module()
    records = [
        {"sequence": 1, "transition_kind": "action", "selected_action": "rest", "life_index": 1},
        {"sequence": 2, "transition_kind": "respawn", "selected_action": None, "life_index": 2},
        {"sequence": 3, "transition_kind": "action", "selected_action": "turn_left", "life_index": 2},
        {"sequence": 4, "transition_kind": "action", "selected_action": "move_forward", "life_index": 2},
        {"sequence": 5, "transition_kind": "action", "selected_action": "interact", "life_index": 2},
    ]

    summary = module.summarize_control_prefix(records, action_budget=3)

    assert summary["action_sequences"] == [1, 3, 4]
    assert summary["action_count"] == 3
    assert summary["max_life_index"] == 2
    assert summary["respawn_count"] == 1
    assert summary["last_consumed_sequence"] == 4


def test_leakage_scan_detects_direct_and_base64_private_controls():
    module = _load_module()
    clean = {
        "observation": {"visual": [["empty"]]},
        "organism_before": {"energy": 0.4},
        "action": "rest",
        "front_token": "empty",
        "outcome_type": "rested",
    }
    encoded = base64.b64encode(b'{"cause":"food"}').decode("ascii")

    assert module.scan_learner_projection(clean)["clean"] is True
    direct = module.scan_learner_projection({**clean, "nested": {"objects_by_cause": {}}})
    assert direct["clean"] is False
    assert any("objects_by_cause" in item for item in direct["findings"])
    indirect = module.scan_learner_projection({**clean, "opaque": encoded})
    assert indirect["clean"] is False
    assert any("base64" in item for item in indirect["findings"])


def test_leakage_positive_controls_cover_every_frozen_private_category():
    module = _load_module()
    clean = {
        "observation": {"schema_version": "public.v1", "visual": [["empty"]]},
        "organism_before": dict(module.engine.INITIAL_ORGANISM),
        "selected_action": "rest",
        "front_token": "empty",
        "outcome_type": "rested",
        "actual_delta": {key: 0.0 for key in module.engine.STATE_KEYS},
        "terminal_receipt": None,
        "public_relative_belief": {
            "relative_pose": [0, 0],
            "relative_facing": "N",
            "known_cell_count": 1,
            "known_object_count": 0,
            "front_token": "empty",
            "token_counts": {f"v{i}": 0 for i in range(5)},
        },
        "quotient_features": [0.0] * 13,
    }

    report = module.run_leakage_positive_controls(clean)

    assert report["clean_scan"]["clean"] is True
    assert set(report["positive_controls"]) == {
        "cause_identity",
        "private_position",
        "private_map",
        "objects_by_cause",
        "token_mapping",
        "target_reason",
        "private_path",
        "world_id",
        "policy_id",
        "run_id",
        "future_observation",
        "panel_truth",
        "loss",
        "verdict",
        "file_path",
        "artifact_hash",
    }
    assert all(
        item["direct_detected"] and item["base64_detected"]
        for item in report["positive_controls"].values()
    )
    assert report["all_positive_controls_detected"] is True


def test_verdict_priority_is_fail_closed_and_exhaustive():
    module = _load_module()
    assert module.dispatch_verdict(False, True, True, True) == (
        "BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE"
    )
    assert module.dispatch_verdict(True, False, True, True) == (
        "BLOCKED_CONTROL_ENVELOPE_INCOMPARABLE"
    )
    assert module.dispatch_verdict(True, True, False, True) == (
        "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    )
    assert module.dispatch_verdict(True, True, True, False) == (
        "DETERMINISTIC_PANEL_CAPACITY_NOT_ADMITTED"
    )
    assert module.dispatch_verdict(True, True, True, True) == (
        "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"
    )


def test_adjudication_hard_gates_independent_recompute_and_all_validity_inputs():
    module = _load_module()
    context_reports = {
        "c1": {
            "check_map": {
                "control_envelope_comparable": True,
                "privileged_support_witness_found": True,
                "deterministic_panel_capacity_admitted": True,
            },
            "reported_values_match": True,
            "producer_receipts_valid": True,
            "hashes_valid": True,
        },
        "c2": {
            "check_map": {
                "control_envelope_comparable": True,
                "privileged_support_witness_found": True,
                "deterministic_panel_capacity_admitted": True,
            },
            "reported_values_match": True,
            "producer_receipts_valid": True,
            "hashes_valid": True,
        },
    }
    validity = {
        "pre_run_provenance_valid": True,
        "runtime_contract_satisfied": True,
        "source_hashes_match": True,
        "leakage_clean": True,
        "positive_controls_detected": True,
        "fresh_process_recompute_equal": True,
        "all_tamper_controls_rejected": True,
    }

    admitted = module.derive_adjudication(context_reports, validity)
    assert admitted["provenance_clean"] is True
    assert admitted["verdict"] == (
        "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"
    )

    independent_mismatch = deepcopy(context_reports)
    independent_mismatch["c2"]["reported_values_match"] = False
    blocked = module.derive_adjudication(independent_mismatch, validity)
    assert blocked["provenance_clean"] is False
    assert blocked["verdict"] == "BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE"

    for key in validity:
        invalid = dict(validity)
        invalid[key] = False
        blocked = module.derive_adjudication(context_reports, invalid)
        assert blocked["provenance_clean"] is False
        assert blocked["verdict"] == (
            "BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE"
        )


def test_source_hash_and_verdict_validation_reject_well_formed_substitution():
    module = _load_module()
    expected_hashes = {
        "labs/ego_life_playground_v0/engine.py": "1" * 64,
        "labs/ego_life_playground_v0/microworld.py": "2" * 64,
    }
    assert module.validate_exact_source_hashes(
        expected_hashes, deepcopy(expected_hashes)
    ) is True
    substituted = deepcopy(expected_hashes)
    substituted["labs/ego_life_playground_v0/engine.py"] = "3" * 64
    with pytest.raises(ValueError, match="source hash"):
        module.validate_exact_source_hashes(expected_hashes, substituted)

    expected_verdict = "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND"
    assert module.validate_reported_verdict(expected_verdict, expected_verdict) is True
    with pytest.raises(ValueError, match="verdict"):
        module.validate_reported_verdict(
            expected_verdict,
            "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT",
        )


@pytest.mark.parametrize(
    "database_name,total_actions",
    [
        ("smoke_p0_cross_v1.sqlite3", 89),
        ("smoke_p2_vertical_v1.sqlite3", 115),
    ],
)
def test_banked_control_recovery_extracts_the_same_first_89_action_envelope(
    database_name: str, total_actions: int
):
    module = _load_module()
    database = (
        REPO_ROOT
        / "artifacts"
        / "EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F"
        / database_name
    )

    report = module.extract_banked_control(database, action_budget=89)

    assert report["recovery_exact"] is True
    assert report["available_action_count"] == total_actions
    assert report["prefix"]["action_count"] == 89
    assert len(report["prefix"]["action_sequences"]) == 89
    assert report["prefix"]["max_life_index"] >= 1
    assert report["prefix"]["respawn_count"] == report["prefix"]["max_life_index"] - 1
    assert report["prefix_records"][-1]["sequence"] == report["prefix"][
        "last_consumed_sequence"
    ]
    assert sum(
        row["transition_kind"] == "action" for row in report["prefix_records"]
    ) == 89
    assert sum(
        row["transition_kind"] == "respawn" for row in report["prefix_records"]
    ) == report["prefix"]["respawn_count"]
    assert [row["sequence"] for row in report["prefix_records"]] == list(
        range(1, report["prefix"]["last_consumed_sequence"] + 1)
    )
    assert len(report["database_sha256"]) == 64


def test_banked_control_recovery_is_read_only_and_does_not_bypass_metadata_gates(
    monkeypatch: pytest.MonkeyPatch,
):
    module = _load_module()
    database = (
        REPO_ROOT
        / "artifacts"
        / "EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F"
        / "smoke_p0_cross_v1.sqlite3"
    )
    before_bytes = database.read_bytes()
    before_stat = database.stat()

    recover_calls = 0
    metadata_verify_calls = 0
    store_hash_calls = 0
    original_recover = module.v2_store.SQLiteEventStore.recover_run
    original_verify = module.engine._verify_run_metadata
    original_store_hash = module.v2_store.compute_code_path_hash

    def forbid_writable_constructor(self, path):
        raise AssertionError("banked database must not enter the writable store constructor")

    def counted_recover(self, run_id):
        nonlocal recover_calls
        recover_calls += 1
        return original_recover(self, run_id)

    def counted_verify(run_meta, current_code_hash):
        nonlocal metadata_verify_calls
        metadata_verify_calls += 1
        return original_verify(run_meta, current_code_hash)

    def counted_store_hash():
        nonlocal store_hash_calls
        store_hash_calls += 1
        return original_store_hash()

    monkeypatch.setattr(module.v2_store.SQLiteEventStore, "__init__", forbid_writable_constructor)
    monkeypatch.setattr(module.v2_store.SQLiteEventStore, "recover_run", counted_recover)
    monkeypatch.setattr(module.engine, "_verify_run_metadata", counted_verify)
    monkeypatch.setattr(module.v2_store, "compute_code_path_hash", counted_store_hash)

    report = module.extract_banked_control(database, action_budget=89)

    after_stat = database.stat()
    assert report["open_mode"] == "sqlite_uri_mode_ro_immutable_1"
    assert recover_calls == 1
    assert metadata_verify_calls > 0
    assert store_hash_calls > 0
    assert database.read_bytes() == before_bytes
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def _independent_shortest_front_path(module, world, target_front_token: str):
    queue = deque([(deepcopy(world), ())])
    seen = {module.engine.canonical_hash(world)}
    while queue:
        candidate, actions = queue.popleft()
        observation = microworld.policy_observation(candidate, occlusion=True)
        if observation["visual"][1][2] == target_front_token:
            return actions
        for action in (
            "turn_left",
            "turn_right",
            "move_forward",
            "interact",
            "rest",
        ):
            successor, _transition = microworld.transition_world(candidate, action)
            key = module.engine.canonical_hash(successor)
            if key in seen:
                continue
            seen.add(key)
            queue.append((successor, (*actions, action)))
    raise AssertionError(f"independent BFS found no path to {target_front_token}")


@pytest.mark.parametrize(
    "layout,world_seed",
    [("p0_cross_v1", 52), ("p2_vertical_v1", 54)],
)
def test_private_bfs_is_shortest_deterministic_and_uses_only_navigation_actions(
    layout: str, world_seed: int
):
    module = _load_module()
    world = microworld.initial_world_state(
        seed=world_seed, layout_id=layout, life_index=1
    )
    frozen_world = deepcopy(world)

    for target in ("v0", "v1", "v2", "v3", "v4", "empty", "wall"):
        expected = _independent_shortest_front_path(module, world, target)
        receipt = module.private_shortest_front_path(world, target)

        assert tuple(receipt["actions"]) == expected
        assert receipt["distance"] == len(expected)
        assert set(receipt["actions"]) <= {
            "turn_left",
            "turn_right",
            "move_forward",
            "interact",
            "rest",
        }
        assert receipt["target_front_token"] == target
        assert receipt["front_token_after"] == target
        assert receipt["start_world_hash"] == module.engine.canonical_hash(world)
        assert receipt["end_world_hash"] == module.engine.canonical_hash(
            receipt["end_world"]
        )
        assert world == frozen_world

    with pytest.raises(ValueError, match="target front token"):
        module.private_shortest_front_path(world, "occluded")


def test_public_checkpoint_matches_live_predictor_input_and_exact_dedupe_projection():
    module = _load_module()
    world = microworld.initial_world_state(
        seed=52, layout_id="p0_cross_v1", life_index=9
    )
    organism = dict(module.engine.INITIAL_ORGANISM)
    predictive_state = predictive_control.reset_for_respawn(
        predictive_control.empty_state(), episode_index=8
    )
    frozen_world = deepcopy(world)
    frozen_organism = deepcopy(organism)
    frozen_predictive_state = deepcopy(predictive_state)

    observation = microworld.policy_observation(world, occlusion=True)
    expected_state, expected_observe_receipt = predictive_control.observe_belief(
        predictive_state,
        observation=observation,
        episode_index=8,
        mode="relative",
    )
    expected_payload = predictive_control.predictor_input_snapshot(
        expected_state,
        observation=observation,
        organism=organism,
        relative_map_mode="relative",
    )
    expected_features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
        organism=expected_payload["organism"],
        summary=expected_payload["belief_summary"],
    )

    checkpoint = module.build_public_checkpoint(
        world=world,
        organism=organism,
        predictive_state=predictive_state,
        episode_index=8,
    )

    assert checkpoint["observation"] == observation
    assert checkpoint["predictor_input"] == expected_payload
    assert checkpoint["prepared_predictive_state"] == expected_state
    assert checkpoint["observe_belief_receipt"] == expected_observe_receipt
    assert np.array_equal(checkpoint["full_features"], expected_features)
    assert np.array_equal(
        checkpoint["quotient_features"], module.quotient_features(expected_features)
    )
    assert checkpoint["front_token"] == observation["visual"][1][2]
    assert set(checkpoint["dedupe_projection"]) == {
        "observation",
        "organism",
        "public_relative_belief",
        "quotient_features",
    }
    assert checkpoint["checkpoint_hash"] == module.engine.canonical_hash(
        checkpoint["dedupe_projection"]
    )
    assert module.scan_learner_projection(checkpoint["dedupe_projection"])["clean"] is True
    assert world == frozen_world
    assert organism == frozen_organism
    assert predictive_state == frozen_predictive_state


@pytest.mark.parametrize(
    "action",
    ["turn_left", "turn_right", "move_forward", "interact", "rest"],
)
def test_forced_action_truth_invokes_live_reducer_delta_and_metabolism_once(
    action: str, monkeypatch: pytest.MonkeyPatch
):
    module = _load_module()
    world = microworld.initial_world_state(
        seed=52, layout_id="p0_cross_v1", life_index=9
    )
    organism = dict(module.engine.INITIAL_ORGANISM)
    frozen_world = deepcopy(world)
    frozen_organism = deepcopy(organism)
    run_id = "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1:test"
    run_meta = module.engine.make_run_metadata(run_id, seed=711)
    episode_id = module.engine.episode_id_for(run_id, 8)
    command_hash = module.engine.canonical_hash(
        {"run_id": run_id, "life_index": 9, "sequence": 1, "action": action}
    )

    expected_world, expected_transition = microworld.transition_world(world, action)
    expected_delta = module.engine.compute_actual_delta(
        expected_transition, selected_action=action
    )
    expected_metabolism = module.engine.compute_metabolism_ledger(
        energy_before=float(organism["energy"]),
        selected_action=action,
        world_before=world,
        world_after=expected_world,
        world_transition=expected_transition,
        run_meta=run_meta,
        episode_id=episode_id,
        command_hash=command_hash,
        code_path_hash=module.engine.compute_code_path_hash(),
    )
    expected_delta["energy"] = expected_metabolism["energy_delta"]
    expected_organism = module.engine._apply_delta(organism, expected_delta)  # noqa: SLF001

    calls = {"transition_world": 0, "compute_actual_delta": 0, "metabolism": 0}
    original_transition = module.microworld.transition_world
    original_actual_delta = module.engine.compute_actual_delta
    original_metabolism = module.engine.compute_metabolism_ledger

    def counted_transition(*args, **kwargs):
        calls["transition_world"] += 1
        return original_transition(*args, **kwargs)

    def counted_actual_delta(*args, **kwargs):
        calls["compute_actual_delta"] += 1
        return original_actual_delta(*args, **kwargs)

    def counted_metabolism(*args, **kwargs):
        calls["metabolism"] += 1
        return original_metabolism(*args, **kwargs)

    monkeypatch.setattr(module.microworld, "transition_world", counted_transition)
    monkeypatch.setattr(module.engine, "compute_actual_delta", counted_actual_delta)
    monkeypatch.setattr(module.engine, "compute_metabolism_ledger", counted_metabolism)

    result = module.evaluate_forced_action_truth(
        world=world,
        organism=organism,
        action=action,
        run_meta=run_meta,
        episode_id=episode_id,
        command_hash=command_hash,
        source_sequence=1,
        life_index=9,
        episode_tick_after=1,
    )

    assert calls == {
        "transition_world": 1,
        "compute_actual_delta": 1,
        "metabolism": 1,
    }
    assert result["next_world"] == expected_world
    assert result["next_organism"] == expected_organism
    assert result["truth"]["outcome_type"] == expected_transition["outcome_type"]
    assert result["truth"]["world_transition"] == expected_transition
    assert result["truth"]["actual_delta"] == expected_delta
    assert result["truth"]["metabolism"] == expected_metabolism
    assert result["truth"]["terminal_receipt"] is None
    assert result["callable_receipts"] == {
        "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
        "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
        "compute_metabolism_ledger": (
            "labs.ego_life_playground_v0.engine.compute_metabolism_ledger"
        ),
    }
    assert world == frozen_world
    assert organism == frozen_organism


def test_forced_action_truth_emits_canonical_death_receipt():
    module = _load_module()
    world = microworld.initial_world_state(
        seed=52, layout_id="p0_cross_v1", life_index=3
    )
    organism = dict(module.engine.INITIAL_ORGANISM, energy=0.001)
    run_id = "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1:death"
    run_meta = module.engine.make_run_metadata(run_id, seed=711)
    command_hash = module.engine.canonical_hash({"run_id": run_id, "sequence": 7})

    result = module.evaluate_forced_action_truth(
        world=world,
        organism=organism,
        action="rest",
        run_meta=run_meta,
        episode_id=module.engine.episode_id_for(run_id, 2),
        command_hash=command_hash,
        source_sequence=7,
        life_index=3,
        episode_tick_after=7,
    )

    assert result["next_organism"]["energy"] == 0.0
    assert result["truth"]["terminal_receipt"] == module.engine._life_result(  # noqa: SLF001
        life_index=3,
        survival_ticks=7,
        censored=False,
        termination="death",
    )


def test_evaluator_trajectory_uses_public_belief_and_canonical_natural_respawn():
    module = _load_module()
    run_id = "EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1:trajectory"
    state = module.initialize_evaluator_state(
        layout_id="p0_cross_v1",
        world_seed=52,
        policy_seed=711,
        run_id=run_id,
    )
    canonical = module.engine.initial_state(
        run_id=run_id, seed=52, layout_id="p0_cross_v1"
    )
    initial_model_hash = module.predictive_control.model_hash(
        state["predictive_state"]
    )

    assert state["world"] == canonical["world"]
    assert state["organism"] == canonical["organism"]
    assert state["life_index"] == 1
    assert state["episode_index"] == 0
    assert state["episode_tick"] == 0
    assert state["global_sequence"] == 0
    assert state["action_count"] == 0
    assert state["respawn_count"] == 0
    assert state["awaiting_respawn"] is False

    rows = []
    while not state["awaiting_respawn"]:
        advanced = module.advance_evaluator_action(state, "rest")
        state = advanced["state"]
        row = advanced["row"]
        rows.append(row)
        assert row["selected_action"] == "rest"
        assert row["outcome_type"] == "rested"
        assert module.scan_learner_projection(row["learner_projection"])["clean"] is True
        assert row["producer_receipts"]["predictive_update"]["reason"] == (
            "predictor_updates_frozen"
        )
        assert len(rows) <= module.engine.EPISODE_SPAN_TICKS

    assert state["organism"]["energy"] == 0.0
    assert state["life_index"] == 1
    assert state["action_count"] == len(rows)
    assert state["global_sequence"] == len(rows)
    assert rows[-1]["terminal_receipt"]["termination"] == "death"
    assert module.predictive_control.model_hash(state["predictive_state"]) == (
        initial_model_hash
    )

    before_respawn = deepcopy(state)
    respawned = module.advance_evaluator_respawn(state)

    assert respawned["life_index"] == 2
    assert respawned["episode_index"] == 1
    assert respawned["episode_tick"] == 0
    assert respawned["global_sequence"] == before_respawn["global_sequence"] + 1
    assert respawned["action_count"] == before_respawn["action_count"]
    assert respawned["respawn_count"] == 1
    assert respawned["awaiting_respawn"] is False
    assert respawned["organism"] == dict(module.engine.INITIAL_ORGANISM)
    assert respawned["world"] == microworld.reset_world_for_life(
        before_respawn["world"], 2
    )
    assert respawned["predictive_state"] == module.predictive_control.reset_for_respawn(
        before_respawn["predictive_state"], episode_index=1
    )
    assert state == before_respawn

    with pytest.raises(ValueError, match="awaiting respawn"):
        module.advance_evaluator_respawn(respawned)


def _independent_training_support_counts(module, rows):
    counts = {}
    for stratum in module.TRAINING_SUPPORT_STRATA:
        selected = []
        for row in rows:
            projection = row["learner_projection"]
            if row["selected_action"] != stratum["action"]:
                continue
            if row["outcome_type"] != stratum["outcome_type"]:
                continue
            target = stratum["target_front_token"]
            if target is not None and projection["front_token"] != target:
                continue
            selected.append(row)
        counts[stratum["stratum_id"]] = len(selected)
    return counts


def _independent_action_ranks(module, rows):
    ranks = {}
    for action in module.engine.ACTIONS:
        matrix = np.asarray(
            [
                row["learner_projection"]["quotient_features"]
                for row in rows
                if row["selected_action"] == action
            ],
            dtype=np.float64,
        )
        ranks[action] = 0 if matrix.size == 0 else int(np.linalg.matrix_rank(matrix))
    return ranks


def test_privileged_witness_is_strict_listed_order_budgeted_and_reducible():
    module = _load_module()
    expected_strata = (
        "interact::v0::interacted",
        "interact::v1::interacted",
        "interact::v2::interacted",
        "interact::v3::interacted",
        "interact::v4::interacted",
        "interact::no_object",
        "move_forward::moved",
        "move_forward::blocked",
        "rest::rested",
        "turn_left::turned",
        "turn_right::turned",
    )
    assert tuple(item["stratum_id"] for item in module.TRAINING_SUPPORT_STRATA) == (
        expected_strata
    )

    kwargs = {
        "context_id": "p0_cross_v1:world=52:policy=711",
        "layout_id": "p0_cross_v1",
        "world_seed": 52,
        "policy_seed": 711,
        "action_budget": 89,
        "max_life_index": 4,
        "max_respawn_count": 3,
    }
    first = module.run_privileged_witness(**kwargs)
    second = module.run_privileged_witness(**kwargs)

    assert first["trajectory_hash"] == second["trajectory_hash"]
    assert first["rows"] == second["rows"]
    assert first["action_count"] == len(first["rows"]) == 89
    assert first["max_life_index"] <= 4
    assert first["respawn_count"] <= 3
    assert first["control_envelope_comparable"] is True
    assert all(row["transition_kind"] == "action" for row in first["rows"])
    assert [row["action_index"] for row in first["rows"]] == list(range(1, 90))
    assert [row["global_sequence"] for row in first["rows"]] == sorted(
        row["global_sequence"] for row in first["rows"]
    )
    assert all(
        module.scan_learner_projection(row["learner_projection"])["clean"]
        for row in first["rows"]
    )

    counts = _independent_training_support_counts(module, first["rows"])
    ranks = _independent_action_ranks(module, first["rows"])
    assert first["support_report"]["stratum_counts"] == counts
    assert first["support_report"]["all_supported"] is all(
        value >= 4 for value in counts.values()
    )
    assert {
        action: first["rank_reports"][f"{kwargs['context_id']}::{action}"]["rank"]
        for action in module.engine.ACTIONS
    } == ranks
    assert first["all_action_ranks_full"] is all(value == 13 for value in ranks.values())
    assert first["witness_found"] is (
        first["control_envelope_comparable"]
        and first["action_count"] == 89
        and first["support_report"]["all_supported"]
        and first["all_action_ranks_full"]
    )
    assert first["planner_contract"] == {
        "support_order": "strict_first_deficient_stratum_in_frozen_order",
        "cause_reorder": "disabled_unfrozen_cause_order",
        "rank_search": "current_checkpoint_only",
    }
    assert first["ablation_report"]["reorder_count"] == 0
    assert first["ablation_report"]["trajectory_hash_changed"] is False
    assert first["ablation_report"]["main_trajectory_hash"] == first["trajectory_hash"]
    assert first["ablation_report"]["no_cause_trajectory_hash"] == first["trajectory_hash"]


def test_witness_does_not_respawn_after_the_budget_terminal_action(
    monkeypatch: pytest.MonkeyPatch,
):
    module = _load_module()
    original_initialize = module.initialize_evaluator_state

    def low_energy_initialize(**kwargs):
        state = original_initialize(**kwargs)
        state["organism"]["energy"] = 0.001
        return state

    monkeypatch.setattr(module, "initialize_evaluator_state", low_energy_initialize)
    report = module.run_privileged_witness(
        context_id="p0_cross_v1:world=52:policy=711:budget-terminal",
        layout_id="p0_cross_v1",
        world_seed=52,
        policy_seed=711,
        action_budget=1,
        max_life_index=4,
        max_respawn_count=3,
    )

    assert report["action_count"] == 1
    assert report["rows"][-1]["terminal_receipt"]["termination"] == "death"
    assert report["respawn_count"] == 0
    assert report["max_life_index"] == 1


def test_deterministic_panel_uses_independent_resets_dedupes_then_expands_truths():
    module = _load_module()
    context_id = "p0_cross_v1:world=52:policy=711"
    panel = module.build_deterministic_panel(
        context_id=context_id,
        layout_id="p0_cross_v1",
        world_seed=52,
        policy_seed=711,
        panel_rollout_ids=tuple(range(9, 17)),
    )

    assert panel["panel_rollout_ids"] == list(range(9, 17))
    assert panel["target_order"] == [
        "v0",
        "v1",
        "v2",
        "v3",
        "v4",
        "empty",
        "wall",
        "empty",
        "wall",
    ]
    assert [item["panel_rollout_id"] for item in panel["rollouts"]] == list(
        range(9, 17)
    )
    for rollout in panel["rollouts"]:
        k = rollout["panel_rollout_id"]
        expected_world = microworld.initial_world_state(
            seed=52, layout_id="p0_cross_v1", life_index=k
        )
        assert rollout["initial_world_hash"] == module.engine.canonical_hash(
            expected_world
        )
        assert rollout["initial_organism_hash"] == module.engine.canonical_hash(
            dict(module.engine.INITIAL_ORGANISM)
        )
        reached = rollout["reached_target_order"]
        assert reached == panel["target_order"][: len(reached)]
        assert rollout["respawn_count"] == 0
        assert rollout["complete"] is (len(reached) == len(panel["target_order"]))
        if rollout["complete"]:
            assert rollout["failure_reason"] is None
            assert rollout["failed_target"] is None
        else:
            assert rollout["failure_reason"] in {
                "natural_terminal_before_ninth_target",
                "private_shortest_path_not_found",
            }
            assert rollout["failed_target"] == panel["target_order"][len(reached)]

    raw_counts = {
        token: sum(
            checkpoint["front_token"] == token
            for checkpoint in panel["raw_checkpoints"]
        )
        for token in ("v0", "v1", "v2", "v3", "v4", "empty", "wall")
    }
    retained_counts = {
        token: sum(
            checkpoint["front_token"] == token
            for checkpoint in panel["retained_checkpoints"]
        )
        for token in ("v0", "v1", "v2", "v3", "v4", "empty", "wall")
    }
    assert panel["support_report"]["before_dedupe"] == raw_counts
    assert panel["support_report"]["after_dedupe"] == retained_counts
    assert len({item["checkpoint_hash"] for item in panel["retained_checkpoints"]}) == (
        len(panel["retained_checkpoints"])
    )
    assert len(panel["rows"]) == len(panel["retained_checkpoints"]) * 5

    actions_by_checkpoint = {}
    for row in panel["rows"]:
        actions_by_checkpoint.setdefault(row["checkpoint_hash"], []).append(
            row["selected_action"]
        )
        assert module.scan_learner_projection(row["learner_projection"])["clean"]
        assert row["producer_receipts"] == {
            "transition_world": (
                "labs.ego_life_playground_v0.microworld.transition_world"
            ),
            "compute_actual_delta": (
                "labs.ego_life_playground_v0.engine.compute_actual_delta"
            ),
            "compute_metabolism_ledger": (
                "labs.ego_life_playground_v0.engine.compute_metabolism_ledger"
            ),
        }
        assert row["base_checkpoint_hash_before_truth"] == (
            row["base_checkpoint_hash_after_truth"]
        )
    assert all(
        sorted(actions) == sorted(module.engine.ACTIONS)
        for actions in actions_by_checkpoint.values()
    )

    ranks = _independent_action_ranks(module, panel["rows"])
    assert {
        action: panel["rank_reports"][f"{context_id}::{action}"]["rank"]
        for action in module.engine.ACTIONS
    } == ranks
    floors = {"v0": 8, "v1": 8, "v2": 8, "v3": 8, "v4": 8, "empty": 16, "wall": 16}
    support_pass = all(
        raw_counts[token] >= floor and retained_counts[token] >= floor
        for token, floor in floors.items()
    )
    assert panel["support_report"]["required_floors"] == floors
    assert panel["support_report"]["passed"] is support_pass
    cell_counts = {}
    for row in panel["rows"]:
        key = "::".join(
            (
                context_id,
                row["selected_action"],
                row["front_token"],
                row["outcome_type"],
            )
        )
        cell_counts[key] = cell_counts.get(key, 0) + 1
    assert panel["cell_support_report"]["cell_counts"] == cell_counts
    assert panel["cell_support_report"]["required_floor_by_cell"] == {
        key: floors[key.split("::")[-2]] for key in cell_counts
    }
    assert panel["cell_support_report"]["passed"] is all(
        count >= floors[key.split("::")[-2]] for key, count in cell_counts.items()
    )
    assert panel["construction_complete"] is all(
        item["complete"] for item in panel["rollouts"]
    )
    assert panel["panel_capacity_admitted"] is (
        panel["construction_complete"]
        and support_pass
        and panel["cell_support_report"]["passed"]
        and all(rank == 13 for rank in ranks.values())
    )
    assert panel["panel_hash"] == module.engine.canonical_hash(
        {
            "rollouts": panel["rollouts"],
            "retained_checkpoint_hashes": [
                item["checkpoint_hash"] for item in panel["retained_checkpoints"]
            ],
            "rows": panel["rows"],
            "support_report": panel["support_report"],
            "cell_support_report": panel["cell_support_report"],
            "rank_reports": panel["rank_reports"],
            "panel_capacity_admitted": panel["panel_capacity_admitted"],
        }
    )


def test_independent_row_reducer_recomputes_control_witness_panel_and_check_map(
    monkeypatch: pytest.MonkeyPatch,
):
    module = _load_module()
    context_id = "p0_cross_v1:world=52:policy=711"
    basis = _full_rank_reference_rows(module)
    expected_forced_receipts = {
        "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
        "compute_actual_delta": (
            "labs.ego_life_playground_v0.engine.compute_actual_delta"
        ),
        "compute_metabolism_ledger": (
            "labs.ego_life_playground_v0.engine.compute_metabolism_ledger"
        ),
    }
    control_records = [
        {
            "sequence": sequence,
            "transition_kind": "action",
            "selected_action": "rest",
            "life_index": 1,
        }
        for sequence in range(1, 90)
    ]
    control = {
        "recovery_exact": True,
        "open_mode": "sqlite_uri_mode_ro_immutable_1",
        "prefix_records": control_records,
        "prefix": module.summarize_control_prefix(control_records, action_budget=89),
    }

    witness_specs = []
    for token in ("v0", "v1", "v2", "v3", "v4"):
        witness_specs.extend([("interact", token, "interacted")] * 4)
    witness_specs.extend([("interact", "empty", "no_object")] * 4)
    witness_specs.extend([("move_forward", "empty", "moved")] * 9)
    witness_specs.extend([("move_forward", "wall", "blocked")] * 4)
    witness_specs.extend([("rest", "empty", "rested")] * 26)
    witness_specs.extend([("turn_left", "empty", "turned")] * 13)
    witness_specs.extend([("turn_right", "empty", "turned")] * 13)
    assert len(witness_specs) == 89
    action_feature_index = {action: 0 for action in module.engine.ACTIONS}
    witness_rows = []
    for index, (action, token, outcome) in enumerate(witness_specs, start=1):
        feature = basis[action_feature_index[action] % len(basis)]
        action_feature_index[action] += 1
        witness_rows.append(
            {
                "context_id": context_id,
                "action_index": index,
                "global_sequence": index,
                "transition_kind": "action",
                "life_index": 1,
                "selected_action": action,
                "outcome_type": outcome,
                "full_features": feature.tolist(),
                "learner_projection": {
                    "front_token": token,
                    "quotient_features": module.quotient_features(feature).tolist(),
                },
                "producer_receipts": {
                    "forced_truth": deepcopy(expected_forced_receipts),
                    "predictive_update": {
                        "producer_function": (
                            "ego_life_playground_v0.predictive_control."
                            "update_after_transition"
                        ),
                        "reason": "predictor_updates_frozen",
                    },
                },
            }
        )
    witness_support = _independent_training_support_counts(module, witness_rows)
    witness_rank_reports = module._rank_reports_from_rows(  # noqa: SLF001
        context_id, witness_rows
    )
    witness = {
        "rows": witness_rows,
        "trajectory_hash": module.engine.canonical_hash(witness_rows),
        "action_count": 89,
        "max_life_index": 1,
        "respawn_count": 0,
        "control_envelope_comparable": True,
        "support_report": {
            "stratum_counts": witness_support,
            "all_supported": True,
        },
        "rank_reports": witness_rank_reports,
        "all_action_ranks_full": True,
        "witness_found": True,
    }

    floors = {
        "v0": 8,
        "v1": 8,
        "v2": 8,
        "v3": 8,
        "v4": 8,
        "empty": 16,
        "wall": 16,
    }
    retained = []
    for token, count in floors.items():
        for token_index in range(count):
            feature = basis[token_index % len(basis)]
            retained.append(
                {
                    "checkpoint_hash": module.engine.canonical_hash(
                        {"token": token, "index": token_index}
                    ),
                    "front_token": token,
                    "full_features": feature.tolist(),
                    "quotient_features": module.quotient_features(feature).tolist(),
                }
            )
    panel_rows = []
    for checkpoint in retained:
        for action in module.engine.ACTIONS:
            panel_rows.append(
                {
                    "context_id": context_id,
                    "checkpoint_hash": checkpoint["checkpoint_hash"],
                    "selected_action": action,
                    "front_token": checkpoint["front_token"],
                    "outcome_type": f"{action}_{checkpoint['front_token']}",
                    "full_features": checkpoint["full_features"],
                    "learner_projection": {
                        "front_token": checkpoint["front_token"],
                        "quotient_features": checkpoint["quotient_features"],
                    },
                    "producer_receipts": deepcopy(expected_forced_receipts),
                }
            )
    cell_counts = {}
    for row in panel_rows:
        key = "::".join(
            (
                context_id,
                row["selected_action"],
                row["front_token"],
                row["outcome_type"],
            )
        )
        cell_counts[key] = cell_counts.get(key, 0) + 1
    panel_rank_reports = module._rank_reports_from_rows(  # noqa: SLF001
        context_id, panel_rows
    )
    panel = {
        "rollouts": [
            {"panel_rollout_id": rollout_id, "complete": True}
            for rollout_id in range(9, 17)
        ],
        "raw_checkpoints": deepcopy(retained),
        "retained_checkpoints": deepcopy(retained),
        "rows": panel_rows,
        "support_report": {
            "before_dedupe": dict(floors),
            "after_dedupe": dict(floors),
            "required_floors": dict(floors),
            "passed": True,
        },
        "cell_support_report": {
            "cell_counts": cell_counts,
            "required_floor_by_cell": {
                key: floors[key.split("::")[-2]] for key in cell_counts
            },
            "passed": True,
        },
        "rank_reports": panel_rank_reports,
        "construction_complete": True,
        "panel_capacity_admitted": True,
    }
    panel["panel_hash"] = module.engine.canonical_hash(
        {
            "rollouts": panel["rollouts"],
            "retained_checkpoint_hashes": [
                item["checkpoint_hash"] for item in panel["retained_checkpoints"]
            ],
            "rows": panel["rows"],
            "support_report": panel["support_report"],
            "cell_support_report": panel["cell_support_report"],
            "rank_reports": panel["rank_reports"],
            "panel_capacity_admitted": panel["panel_capacity_admitted"],
        }
    )

    def forbidden_primary_helper(*_args, **_kwargs):
        raise AssertionError("independent reducer called a primary reducer")

    monkeypatch.setattr(module, "summarize_control_prefix", forbidden_primary_helper)
    monkeypatch.setattr(module, "_support_counts_from_rows", forbidden_primary_helper)
    monkeypatch.setattr(module, "_rank_reports_from_rows", forbidden_primary_helper)
    monkeypatch.setattr(module, "rank_reports_by_context_action", forbidden_primary_helper)
    monkeypatch.setattr(module, "dispatch_verdict", forbidden_primary_helper)

    report = module.independent_reduce_context(
        context_id=context_id,
        control=control,
        witness=witness,
        panel=panel,
    )

    assert report["independence_boundary"] == (
        "separate reducer implementation in the same verifier process and "
        "same Codex/model lineage; not external independent audit"
    )
    assert report["control"]["action_count"] == 89
    assert report["control"]["max_life_index"] == control["prefix"][
        "max_life_index"
    ]
    assert report["control"]["respawn_count"] == control["prefix"][
        "respawn_count"
    ]
    assert report["witness"]["stratum_counts"] == witness["support_report"][
        "stratum_counts"
    ]
    assert report["witness"]["action_ranks"] == {
        action: witness["rank_reports"][f"{context_id}::{action}"]["rank"]
        for action in module.engine.ACTIONS
    }
    assert report["witness"]["witness_found"] is witness["witness_found"]
    assert report["panel"]["before_dedupe"] == panel["support_report"][
        "before_dedupe"
    ]
    assert report["panel"]["after_dedupe"] == panel["support_report"][
        "after_dedupe"
    ]
    assert report["panel"]["cell_counts"] == panel["cell_support_report"][
        "cell_counts"
    ]
    assert report["panel"]["action_ranks"] == {
        action: panel["rank_reports"][f"{context_id}::{action}"]["rank"]
        for action in module.engine.ACTIONS
    }
    assert report["panel"]["panel_capacity_admitted"] is panel[
        "panel_capacity_admitted"
    ]
    assert report["check_map"] == {
        "control_envelope_comparable": witness["control_envelope_comparable"],
        "privileged_support_witness_found": witness["witness_found"],
        "deterministic_panel_capacity_admitted": panel[
            "panel_capacity_admitted"
        ],
    }
    assert report["reported_values_match"] is True
    assert report["producer_receipts_valid"] is True
    assert report["hashes_valid"] is True

    lifecycle_tampered = deepcopy(witness)
    lifecycle_tampered["rows"][-1]["life_index"] = 2
    lifecycle_tampered["control_envelope_comparable"] = True
    lifecycle_report = module.independent_reduce_context(
        context_id=context_id,
        control=control,
        witness=lifecycle_tampered,
        panel=panel,
    )
    assert lifecycle_report["check_map"]["control_envelope_comparable"] is False
    assert lifecycle_report["reported_values_match"] is False

    omitted_cell_panel = deepcopy(panel)
    omitted_cell_panel["support_report"]["required_floors"] = {
        token: 0 for token in floors
    }
    omitted_cell_panel["rows"] = [
        row
        for row in omitted_cell_panel["rows"]
        if not (row["selected_action"] == "rest" and row["front_token"] == "v0")
    ]
    omitted_cell_report = module.independent_reduce_context(
        context_id=context_id,
        control=control,
        witness=witness,
        panel=omitted_cell_panel,
    )
    assert omitted_cell_report["panel"]["required_floors"] == floors
    assert omitted_cell_report["panel"]["complete_action_expansion"] is False
    assert omitted_cell_report["panel"]["panel_capacity_admitted"] is False
    assert omitted_cell_report["reported_values_match"] is False

    producer_tampered = deepcopy(witness)
    producer_tampered["rows"][0]["producer_receipts"]["forced_truth"][
        "transition_world"
    ] = "fake.transition_world"
    producer_report = module.independent_reduce_context(
        context_id=context_id,
        control=control,
        witness=producer_tampered,
        panel=panel,
    )
    assert producer_report["producer_receipts_valid"] is False
    assert producer_report["reported_values_match"] is False

    row_tampered = deepcopy(witness)
    row_tampered["rows"][0]["outcome_type"] = "tampered"
    row_report = module.independent_reduce_context(
        context_id=context_id,
        control=control,
        witness=row_tampered,
        panel=panel,
    )
    assert row_report["hashes_valid"] is False
    assert row_report["reported_values_match"] is False

    tamper_report = module.run_tamper_controls(
        contexts={
            context_id: {
                "control": control,
                "witness": witness,
                "panel": panel,
            }
        },
        source_hashes={"labs/example.py": "1" * 64},
        reported_verdict=(
            "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"
        ),
    )
    assert set(tamper_report["controls"]) == {
        "row",
        "lifecycle",
        "panel",
        "producer",
        "source_hash",
        "verdict",
    }
    assert all(
        item["tampered_digest"] != item["baseline_digest"]
        and item["failed_closed"]
        and item["failure_reasons"]
        for item in tamper_report["controls"].values()
    )
    assert tamper_report["all_tamper_controls_rejected"] is True

    monkeypatch.undo()
    second_context_id = "synthetic-b:world=54:policy=711"
    second = deepcopy({"control": control, "witness": witness, "panel": panel})
    for row in second["witness"]["rows"]:
        row["context_id"] = second_context_id
    second["witness"]["rank_reports"] = module._rank_reports_from_rows(  # noqa: SLF001
        second_context_id, second["witness"]["rows"]
    )
    second["witness"]["trajectory_hash"] = module.engine.canonical_hash(
        second["witness"]["rows"]
    )
    for row in second["panel"]["rows"]:
        row["context_id"] = second_context_id
    second["panel"]["rank_reports"] = module._rank_reports_from_rows(  # noqa: SLF001
        second_context_id, second["panel"]["rows"]
    )
    second_cell_counts = {}
    for row in second["panel"]["rows"]:
        key = "::".join(
            (
                second_context_id,
                row["selected_action"],
                row["front_token"],
                row["outcome_type"],
            )
        )
        second_cell_counts[key] = second_cell_counts.get(key, 0) + 1
    second["panel"]["cell_support_report"] = {
        "cell_counts": second_cell_counts,
        "required_floor_by_cell": {
            key: floors[key.split("::")[-2]] for key in second_cell_counts
        },
        "passed": True,
    }
    second["panel"]["panel_hash"] = module.engine.canonical_hash(
        {
            "rollouts": second["panel"]["rollouts"],
            "retained_checkpoint_hashes": [
                item["checkpoint_hash"]
                for item in second["panel"]["retained_checkpoints"]
            ],
            "rows": second["panel"]["rows"],
            "support_report": second["panel"]["support_report"],
            "cell_support_report": second["panel"]["cell_support_report"],
            "rank_reports": second["panel"]["rank_reports"],
            "panel_capacity_admitted": second["panel"]["panel_capacity_admitted"],
        }
    )
    multi_context_tamper = module.run_tamper_controls(
        contexts={
            context_id: {"control": control, "witness": witness, "panel": panel},
            second_context_id: second,
        },
        source_hashes={"labs/example.py": "1" * 64},
        reported_verdict=(
            "ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT"
        ),
    )
    for tamper_name in ("row", "lifecycle", "panel", "producer"):
        assert set(multi_context_tamper["controls"][tamper_name]["contexts"]) == {
            context_id,
            second_context_id,
        }
        assert all(
            item["failed_closed"]
            for item in multi_context_tamper["controls"][tamper_name][
                "contexts"
            ].values()
        )
    assert multi_context_tamper["all_tamper_controls_rejected"] is True
