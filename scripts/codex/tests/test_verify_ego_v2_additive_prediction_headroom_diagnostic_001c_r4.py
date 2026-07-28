from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys

import pytest

from scripts.codex import (
    verify_ego_v2_additive_prediction_headroom_diagnostic_001c_r4 as verifier,
)


def _trace_row(*, model: str, phase: str, context: str, action: str) -> dict:
    probabilities = {
        "moved": 0.5,
        "blocked": 0.1,
        "interacted": 0.1,
        "no_object": 0.1,
        "rested": 0.1,
        "turned": 0.1,
    }
    prediction = {
        "outcome_probabilities": probabilities,
        "predicted_delta": {
            "energy": 0.1,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    }
    truth = {
        "outcome_type": "moved",
        "actual_delta": {
            "energy": 0.0,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    }
    scores = verifier.recompute_score(prediction, truth)
    return {
        "model": model,
        "phase": phase,
        "context_id": context,
        "snapshot_hash": f"{context}:{phase}",
        "sequence": 1 if phase == "early" else 2,
        "action": action,
        "prediction": prediction,
        "truth": truth,
        "scores": scores,
    }


def _test_canonical_hash(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _report_with_auxiliary_rows() -> tuple[dict, list[dict]]:
    rows = [
        _trace_row(model=model, phase=phase, context=context, action=action)
        for phase in ("early", "late")
        for context in ("a", "b")
        for model in ("learned", "no_update")
        for action in ("move_forward", "rest")
    ]
    learned = [row for row in rows if row["model"] == "learned"]
    legacy_rows = [
        {
            "context_id": row["context_id"],
            "sequence": row["sequence"],
            "phase": row["phase"],
            "action": row["action"],
            "outcome_type": row["truth"]["outcome_type"],
            "predicted_delta": dict(row["prediction"]["predicted_delta"]),
            "delta_mae": row["scores"]["delta_mae"],
        }
        for row in learned
    ]
    ablation_rows = {
        mode: json.loads(json.dumps(legacy_rows))
        for mode in ("base_only", "residual_only", "residual_outcome_rotation")
    }
    stratified = {
        model: {
            phase: verifier._stratified_delta(
                [row for row in model_rows if row["phase"] == phase]
            )
            for phase in ("early", "late")
        }
        for model, model_rows in {
            "learned": learned,
            "no_update": [row for row in rows if row["model"] == "no_update"],
            "legacy_unconditional": legacy_rows,
        }.items()
    }
    report = {
        "rows": rows,
        "aggregate_metrics": verifier.recompute_balanced_aggregate(rows),
        "legacy_rows": legacy_rows,
        "hierarchical_ablation_rows": ablation_rows,
        "outcome_stratified_metrics": stratified,
        "legacy_unconditional_metrics": {
            phase: verifier._aggregate_delta(
                [row for row in legacy_rows if row["phase"] == phase]
            )
            for phase in ("early", "late")
        },
        "hierarchical_ablation_metrics": {
            mode: {
                phase: verifier._stratified_delta(
                    [row for row in mode_rows if row["phase"] == phase]
                )
                for phase in ("early", "late")
            }
            for mode, mode_rows in ablation_rows.items()
        },
    }
    training_rows = [
        {
            "action": action,
            "outcome_type": outcome,
            "features": [1.0 if index == row_index % 15 else 0.0 for index in range(15)],
        }
        for row_index, (action, outcome) in enumerate(verifier.REALIZABLE_STRATA)
    ]
    report["training_support_and_rank"] = verifier._recompute_training_support(
        training_rows
    )
    return report, training_rows


def _frozen_report(*failed: str) -> dict:
    checks = {
        name: name not in set(failed) for name in verifier.EXPECTED_FROZEN_CHECKS
    }
    return {
        "checks": checks,
        "failed_checks": sorted(failed),
        "passed": not failed,
    }


def _strict_report() -> tuple[dict, list[dict], dict]:
    report, training_rows = _report_with_auxiliary_rows()
    learned = [row for row in report["rows"] if row["model"] == "learned"]
    report["snapshot_count"] = len({row["snapshot_hash"] for row in learned})
    report["sample_counts_by_action"] = {
        action: sum(row["action"] == action for row in learned)
        for action in verifier.ACTIONS
    }
    base = verifier._recompute_balanced_digest_base(
        report["rows"], report["aggregate_metrics"]
    )
    digest = {"base": base, "code_path_hash": verifier.R2_RUNTIME_CODE_PATH_HASH}
    report["fresh_subprocess_digest_expected"] = digest
    report["fresh_subprocess_digest_actual"] = json.loads(json.dumps(digest))
    first_twenty = list(verifier.ACTIONS) * 4
    report["frozen_update_controls"] = [
        {
            "context_ids": [
                f"{layout}:world={world}:policy={policy}"
            ],
            "world_seed": world,
            "initial_model_hash": f"model-{world}",
            "final_model_hash": f"model-{world}",
            "model_hash_unchanged": True,
            "update_count": 0,
            "first_20_actions": first_twenty,
            "first_20_action_counts": {action: 4 for action in verifier.ACTIONS},
            "first_20_cover_each_action_at_least_four": True,
        }
        for layout, world, policy in verifier.CONTEXTS
    ]
    leakage = {
        "clean_scan": {"clean": True, "findings": []},
        "positive_controls": {
            field: {
                "detected": True,
                "scan": {"findings": [{"field": field}]},
            }
            for field in verifier.LEAKAGE_POSITIVE_CONTROL_FIELDS
        },
        "all_positive_controls_detected": True,
    }
    base_recomputation = verifier.independent_recompute(report, training_rows)
    checks = verifier.independently_derive_frozen_checks(
        report, base_recomputation, leakage
    )
    report["checks"] = checks
    report["failed_checks"] = sorted(name for name, passed in checks.items() if not passed)
    report["passed"] = all(checks.values())
    return report, training_rows, leakage


def test_frozen_contract_has_no_fresh_seed_overlap() -> None:
    assert verifier.ALLOWED_WORLD_SEEDS == {52, 54}
    assert verifier.ALLOWED_POLICY_SEEDS == {711}
    assert not (verifier.ALLOWED_WORLD_SEEDS & verifier.FORBIDDEN_WORLD_SEEDS)
    assert not (verifier.ALLOWED_POLICY_SEEDS & verifier.FORBIDDEN_POLICY_SEEDS)
    assert verifier.FROZEN_SOURCE_COMMIT == "363f6d49cbd54524ce283e7580e23c45ada4b532"
    assert verifier.FROZEN_PYTHON_VERSION == "3.13.7"
    assert verifier.FROZEN_NUMPY_VERSION == "2.2.6"


def test_file_hash_pin_rejects_drift(tmp_path) -> None:
    path = tmp_path / "input.json"
    path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(verifier.HeadroomDiagnosticError, match="SHA-256"):
        verifier.verify_file_hash(path, "0" * 64)


def test_source_authority_rejects_bundle_or_evaluator_pin_drift(monkeypatch) -> None:
    monkeypatch.setattr(verifier, "R3_TESTED_BUNDLE_SHA256", "0" * 64)
    with pytest.raises(verifier.HeadroomDiagnosticError, match="SHA-256"):
        verifier.verify_source_pins()

    monkeypatch.setattr(
        verifier,
        "R3_TESTED_BUNDLE_SHA256",
        "947f66d9bbc91e753d1f073b8c2b372b6e683c8ea814aeb9c995143a48c1104b",
    )
    monkeypatch.setattr(
        verifier,
        "FROZEN_EVALUATOR_BLOBS",
        {
            "scripts/codex/verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2.py": "0"
            * 40
        },
    )
    with pytest.raises(verifier.HeadroomDiagnosticError, match="blob drifted"):
        verifier.verify_source_pins()


def test_actual_sqlite_seed_firewall_rejects_fresh_world(tmp_path) -> None:
    path = tmp_path / "smoke.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE runs(run_id TEXT, run_meta_json TEXT, initial_state_json TEXT)"
    )
    connection.execute(
        "INSERT INTO runs VALUES(?, ?, ?)",
        (
            "run",
            json.dumps({"seed": 711}),
            json.dumps(
                {
                    "world": {
                        "trial": {"seed": 60},
                        "layout": {"layout_id": "p0_cross_v1"},
                    }
                }
            ),
        ),
    )
    connection.commit()
    connection.close()

    with pytest.raises(verifier.HeadroomDiagnosticError, match="fresh-effect"):
        verifier.read_and_validate_db_context(path, "run")


def test_actual_sqlite_layout_is_read_from_db_and_must_match(tmp_path) -> None:
    path = tmp_path / "smoke.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE runs(run_id TEXT, run_meta_json TEXT, initial_state_json TEXT)"
    )
    connection.execute(
        "INSERT INTO runs VALUES(?, ?, ?)",
        (
            "run",
            json.dumps({"seed": 711}),
            json.dumps(
                {
                    "world": {
                        "trial": {"seed": 52},
                        "layout": {"layout_id": "wrong_layout"},
                    }
                }
            ),
        ),
    )
    connection.commit()
    connection.close()

    with pytest.raises(verifier.HeadroomDiagnosticError, match="layout"):
        verifier.read_and_validate_db_context(
            path, "run", expected_layout="p0_cross_v1"
        )


def test_actual_sqlite_receipt_discloses_immutable_read_only_open(tmp_path) -> None:
    path = tmp_path / "smoke.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE runs(run_id TEXT, run_meta_json TEXT, initial_state_json TEXT)"
    )
    connection.execute(
        "INSERT INTO runs VALUES(?, ?, ?)",
        (
            "run",
            json.dumps({"seed": 711}),
            json.dumps(
                {
                    "world": {
                        "trial": {"seed": 52},
                        "layout": {"layout_id": "p0_cross_v1"},
                    }
                }
            ),
        ),
    )
    connection.commit()
    connection.close()

    receipt = verifier.read_and_validate_db_context(
        path, "run", expected_layout="p0_cross_v1"
    )

    assert receipt["layout_id"] == "p0_cross_v1"
    assert receipt["sqlite_open_mode"] == "mode=ro&immutable=1"


def test_packet_tree_manifest_detects_any_file_mutation(tmp_path) -> None:
    (tmp_path / "empty-dir").mkdir()
    file_path = tmp_path / "input.bin"
    file_path.write_bytes(b"before")
    before = verifier.snapshot_packet_tree(tmp_path)

    file_path.write_bytes(b"after")
    after = verifier.snapshot_packet_tree(tmp_path)

    assert before != after
    assert before["directories"] == after["directories"]
    assert before["files"]["input.bin"]["sha256"] != after["files"]["input.bin"][
        "sha256"
    ]


def test_artifact_manifest_hashes_every_final_file_except_itself(tmp_path) -> None:
    (tmp_path / "result.json").write_bytes(b"result\n")
    (tmp_path / "trace.jsonl").write_bytes(b"trace\n")
    (tmp_path / "artifact_manifest.json").write_bytes(b"stale\n")

    manifest = verifier.build_artifact_manifest(tmp_path)

    assert set(manifest["files"]) == {"result.json", "trace.jsonl"}
    assert manifest["files"]["result.json"]["sha256"] == hashlib.sha256(
        b"result\n"
    ).hexdigest()
    assert len(manifest["artifact_set_hash"]) == 64


@pytest.mark.parametrize("evaluator_raises", (False, True))
def test_run_gate_positive_control_detects_source_packet_mutation_even_on_error(
    tmp_path, monkeypatch, evaluator_raises
) -> None:
    source_packet = tmp_path / "source"
    source_packet.mkdir()
    for name in verifier.FROZEN_INPUTS:
        (source_packet / name).write_bytes(f"frozen:{name}".encode("utf-8"))
    output = tmp_path / "output"
    monkeypatch.setattr(verifier, "SOURCE_PACKET", source_packet)
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", output)
    monkeypatch.setattr(
        verifier,
        "collect_contract_manifest",
        lambda **_kwargs: {"clean": True},
    )
    monkeypatch.setattr(verifier, "verify_source_pins", lambda: {"exact": True})
    monkeypatch.setattr(verifier, "verify_frozen_packet", lambda: {"exact": True})

    def mutate_source_packet():
        (source_packet / "smoke_result.json").write_bytes(b"mutated")
        if evaluator_raises:
            raise RuntimeError("simulated evaluator failure")
        return {}, {}, {}

    monkeypatch.setattr(verifier, "_run_frozen_balanced", mutate_source_packet)

    with pytest.raises(verifier.HeadroomDiagnosticError, match="mutated"):
        verifier.run_gate(output)

    assert not output.exists() or not any(output.iterdir())


def test_independent_row_recompute_detects_score_drift_and_rebuilds_macro() -> None:
    rows = [
        _trace_row(model=model, phase=phase, context=context, action=action)
        for model in ("learned", "no_update")
        for phase in ("early", "late")
        for context in ("a", "b")
        for action in ("move_forward", "rest")
    ]
    aggregate = verifier.recompute_balanced_aggregate(rows)
    report = {"rows": rows, "aggregate_metrics": aggregate}

    recomputed = verifier.independent_recompute(report)

    assert recomputed["all_row_scores_exact"] is True
    assert recomputed["aggregate_metrics_exact"] is True
    assert recomputed["row_count"] == 16
    assert recomputed["aggregate_metrics"] == aggregate

    report["rows"][0]["scores"]["delta_mae"] += 0.01
    drifted = verifier.independent_recompute(report)
    assert drifted["all_row_scores_exact"] is False


def test_independent_recompute_rebuilds_and_binds_frozen_balanced_digest() -> None:
    rows = [
        _trace_row(model=model, phase=phase, context=context, action=action)
        for phase in ("early", "late")
        for context in ("a", "b")
        for model in ("learned", "no_update")
        for action in verifier.ACTIONS
    ]
    aggregate = verifier.recompute_balanced_aggregate(rows)
    snapshot_hashes = ["a:early", "b:early", "a:late", "b:late"]
    base = {
        "snapshot_hashes": snapshot_hashes,
        "prediction_rows_hash": _test_canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "model": row["model"],
                    "action": row["action"],
                    "prediction": row["prediction"],
                }
                for row in rows
            ]
        ),
        "truth_rows_hash": _test_canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "action": row["action"],
                    "truth": row["truth"],
                }
                for row in rows
                if row["model"] == "learned"
            ]
        ),
        "aggregate_hash": _test_canonical_hash(aggregate),
        "payload_hash": _test_canonical_hash(
            {
                "snapshot_hashes": snapshot_hashes,
                "rows": rows,
                "aggregate_metrics": aggregate,
            }
        ),
    }
    digest = {"base": base, "code_path_hash": "frozen-evaluator-hash"}
    report = {
        "rows": rows,
        "aggregate_metrics": aggregate,
        "fresh_subprocess_digest_expected": digest,
        "fresh_subprocess_digest_actual": json.loads(json.dumps(digest)),
    }

    exact = verifier.independent_recompute(report)
    assert exact["checks"]["fresh_digest_expected_equals_actual"] is True
    assert exact["checks"]["row_recomputed_digest_matches_expected"] is True
    assert exact["checks"]["row_recomputed_digest_matches_actual"] is True
    assert exact["checks"]["balanced_row_pairing_exact"] is True
    assert exact["all_exact"] is True

    report["fresh_subprocess_digest_actual"]["base"]["aggregate_hash"] = "0" * 64
    drifted = verifier.independent_recompute(report)
    assert drifted["checks"]["fresh_digest_expected_equals_actual"] is False
    assert drifted["checks"]["row_recomputed_digest_matches_actual"] is False
    assert drifted["all_exact"] is False


def test_independent_recompute_rejects_duplicate_or_unpaired_balanced_row() -> None:
    rows = [
        _trace_row(model=model, phase=phase, context="a", action=action)
        for phase in ("early", "late")
        for model in ("learned", "no_update")
        for action in ("move_forward", "rest")
    ]
    report = {
        "rows": rows + [json.loads(json.dumps(rows[0]))],
        "aggregate_metrics": verifier.recompute_balanced_aggregate(rows),
    }

    recomputed = verifier.independent_recompute(report)

    assert recomputed["checks"]["balanced_row_pairing_exact"] is False
    assert recomputed["all_exact"] is False


def test_balanced_pairing_rejects_global_balance_without_per_snapshot_five_actions() -> None:
    rows = []
    for layout, world, policy in verifier.CONTEXTS:
        context = f"{layout}:world={world}:policy={policy}"
        for phase in ("early", "late"):
            for snapshot_index, actions in enumerate(
                (
                    ("turn_right", "turn_right", "move_forward", "interact", "rest"),
                    ("turn_left", "turn_left", "move_forward", "interact", "rest"),
                )
            ):
                for row_index, action in enumerate(actions):
                    for model in ("learned", "no_update"):
                        row = _trace_row(
                            model=model,
                            phase=phase,
                            context=context,
                            action=action,
                        )
                        row["snapshot_hash"] = f"{context}:{phase}:{snapshot_index}"
                        row["sequence"] = 100 * snapshot_index + row_index
                        rows.append(row)

    learned = [row for row in rows if row["model"] == "learned"]
    assert len({row["snapshot_hash"] for row in learned}) == 8
    assert len(set(row["action"] for row in learned)) == len(verifier.ACTIONS)
    assert len(set(
        (row["context_id"], row["phase"], row["action"])
        for row in learned
    )) == len(verifier.CONTEXTS) * 2 * len(verifier.ACTIONS)

    assert verifier._balanced_row_pairing_exact(rows) is False


@pytest.mark.parametrize(
    ("mutation", "failed_check"),
    (
        ("legacy_summary", "legacy_metrics_exact"),
        ("ablation_summary", "ablation_metrics_exact"),
        ("training_support", "training_support_and_rank_exact"),
        ("legacy_row", "auxiliary_delta_scores_exact"),
        ("ablation_row", "auxiliary_delta_scores_exact"),
    ),
)
def test_independent_recompute_detects_auxiliary_or_support_tamper(
    mutation, failed_check
) -> None:
    report, training_rows = _report_with_auxiliary_rows()
    if mutation == "legacy_summary":
        report["legacy_unconditional_metrics"]["early"]["delta_mae"] += 0.1
    elif mutation == "ablation_summary":
        report["hierarchical_ablation_metrics"]["base_only"]["early"][
            "minimum_support"
        ] += 1
    elif mutation == "training_support":
        report["training_support_and_rank"]["minimum_support"] += 1
    elif mutation == "legacy_row":
        report["legacy_rows"][0]["delta_mae"] += 0.1
    else:
        report["hierarchical_ablation_rows"]["base_only"][0]["delta_mae"] += 0.1

    recomputed = verifier.independent_recompute(report, training_rows)

    assert recomputed["checks"][failed_check] is False
    assert recomputed["all_exact"] is False


@pytest.mark.parametrize("mutation", ("drop_legacy", "duplicate_ablation"))
def test_independent_recompute_rejects_unpaired_auxiliary_rows(mutation) -> None:
    report, training_rows = _report_with_auxiliary_rows()
    if mutation == "drop_legacy":
        report["legacy_rows"].pop()
    else:
        report["hierarchical_ablation_rows"]["base_only"].append(
            json.loads(
                json.dumps(report["hierarchical_ablation_rows"]["base_only"][0])
            )
        )

    recomputed = verifier.independent_recompute(report, training_rows)

    assert recomputed["checks"]["auxiliary_row_pairing_exact"] is False
    assert recomputed["all_exact"] is False


@pytest.mark.parametrize(
    "missing",
    (
        "outcome_stratified_metrics",
        "legacy_unconditional_metrics",
        "legacy_rows",
        "hierarchical_ablation_metrics",
        "hierarchical_ablation_rows",
        "training_support_and_rank",
        "fresh_subprocess_digest_expected",
        "fresh_subprocess_digest_actual",
        "frozen_update_controls",
    ),
)
def test_formal_recompute_fails_closed_when_required_section_is_missing(missing) -> None:
    report, training_rows, leakage = _strict_report()
    del report[missing]

    with pytest.raises(verifier.HeadroomDiagnosticError, match="required evidence"):
        verifier.independent_recompute(
            report,
            training_rows,
            leakage=leakage,
            require_complete=True,
        )


def test_formal_recompute_requires_training_rows_and_leakage() -> None:
    report, training_rows, leakage = _strict_report()

    with pytest.raises(verifier.HeadroomDiagnosticError, match="required evidence"):
        verifier.independent_recompute(
            report, None, leakage=leakage, require_complete=True
        )
    with pytest.raises(verifier.HeadroomDiagnosticError, match="required evidence"):
        verifier.independent_recompute(
            report, training_rows, leakage=None, require_complete=True
        )


@pytest.mark.parametrize(
    "tamper",
    ("reported_metric_check", "support_check", "frozen_control", "leakage"),
)
def test_formal_recompute_independently_rejects_frozen_check_truth_tamper(tamper) -> None:
    report, training_rows, leakage = _strict_report()
    if tamper == "reported_metric_check":
        key = "learned_late_macro_delta_mae_below_early"
        report["checks"][key] = not report["checks"][key]
    elif tamper == "support_check":
        key = "training_support_at_least_16_per_declared_stratum"
        report["checks"][key] = not report["checks"][key]
    elif tamper == "frozen_control":
        report["frozen_update_controls"][0]["final_model_hash"] = "tampered"
    else:
        leakage["positive_controls"]["seed"]["scan"]["findings"] = []

    report["failed_checks"] = sorted(
        name for name, passed in report["checks"].items() if not passed
    )
    report["passed"] = all(report["checks"].values())
    recomputed = verifier.independent_recompute(
        report,
        training_rows,
        leakage=leakage,
        require_complete=True,
    )

    assert recomputed["checks"]["frozen_check_truth_exact"] is False
    assert recomputed["all_exact"] is False
    assert verifier.select_verdict(report, recomputed) == verifier.BLOCKED_VERDICT


def test_verdict_priority_blocks_recompute_then_support_then_headroom() -> None:
    positive = _frozen_report()
    exact = {"all_exact": True}
    assert verifier.select_verdict(positive, exact) == (
        "ADDITIVE_DEVELOPMENT_PREDICTION_DIFFERENCE_UNDER_FROZEN_R2_CONTROLS"
    )
    assert verifier.select_verdict(positive, {"all_exact": False}) == (
        "BLOCKED_PROVENANCE_OR_RECOMPUTATION"
    )
    insufficient = _frozen_report(
        "training_support_at_least_16_per_declared_stratum"
    )
    assert verifier.select_verdict(insufficient, exact) == "INSUFFICIENT_OUTCOME_SUPPORT"
    ordinary_failure = _frozen_report(
        "learned_late_macro_delta_mae_below_early"
    )
    assert verifier.select_verdict(ordinary_failure, exact) == (
        "ADDITIVE_NO_DEVELOPMENT_PREDICTION_DIFFERENCE"
    )


def test_validity_failure_is_blocked_not_scientific_no_difference() -> None:
    report = _frozen_report("leakage_clean_and_all_positive_controls_detected")

    assert verifier.select_verdict(report, {"all_exact": True}) == (
        "BLOCKED_PROVENANCE_OR_RECOMPUTATION"
    )


@pytest.mark.parametrize(
    "mutation",
    ("missing_key", "extra_key", "failed_list_mismatch", "passed_mismatch"),
)
def test_frozen_check_contract_fails_closed_on_structural_drift(mutation) -> None:
    report = _frozen_report()
    if mutation == "missing_key":
        report["checks"].pop(next(iter(report["checks"])))
    elif mutation == "extra_key":
        report["checks"]["post_hoc_check"] = True
    elif mutation == "failed_list_mismatch":
        report["failed_checks"] = ["all_five_action_counts_exactly_equal"]
    else:
        report["passed"] = False

    with pytest.raises(verifier.HeadroomDiagnosticError, match="check contract"):
        verifier.validate_frozen_report_contract(report)


def test_blocked_precondition_still_writes_machine_readable_failure(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", tmp_path)
    result = verifier.write_blocked_output(
        tmp_path, verifier.HeadroomDiagnosticError("source pin drift")
    )

    assert result["verdict"] == "BLOCKED_PROVENANCE_OR_RECOMPUTATION"
    assert result["fresh_effect_seeds_consumed"] is False
    assert result["eligible_for_fresh_effect_card"] is False
    assert json.loads((tmp_path / "result.json").read_text())["verdict"] == result["verdict"]
    assert json.loads((tmp_path / "failure_manifest.json").read_text())[
        "error_type"
    ] == "HeadroomDiagnosticError"
    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text())
    assert set(manifest["files"]) == {
        "claim_ceiling.txt",
        "failure_manifest.json",
        "result.json",
    }


def test_transactional_packet_publish_removes_partial_staging_on_mid_write_error(
    tmp_path, monkeypatch
) -> None:
    output = tmp_path / "canonical"
    output.mkdir()
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", output)

    def write_partial(staging):
        verifier._write_json(staging / "partial.json", {"partial": True})
        raise OSError("simulated mid-write failure")

    with pytest.raises(OSError, match="mid-write"):
        verifier._publish_packet_atomically(output, write_partial)

    assert output.is_dir()
    assert not any(output.iterdir())
    assert not any("staging" in path.name for path in tmp_path.iterdir())


def test_transactional_packet_publish_rejects_missing_required_artifact(
    tmp_path, monkeypatch
) -> None:
    output = tmp_path / "canonical"
    output.mkdir()
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", output)

    def omit_trace(staging):
        verifier._write_json(staging / "result.json", {"verdict": "test"})
        return {"verdict": "test"}

    with pytest.raises(verifier.HeadroomDiagnosticError, match="artifact set"):
        verifier._publish_packet_atomically(
            output,
            omit_trace,
            expected_files={"result.json", "trace.jsonl"},
        )

    assert output.is_dir()
    assert not any(output.iterdir())


def test_successor_provenance_names_real_context_and_code_path() -> None:
    receipt = verifier.provenance_receipt(
        "baseline", "same frozen rows", "abc123", inputs=[{"path": "rows.jsonl"}]
    )

    assert receipt["producer_function"].endswith(".baseline")
    assert receipt["seed"] == [711]
    assert receipt["context_ids"] == [
        "p0_cross_v1:world=52:policy=711",
        "p2_vertical_v1:world=54:policy=711",
    ]
    assert receipt["aggregation_rule"] == "same frozen rows"
    assert receipt["code_path_hash"] == "abc123"


def test_contract_manifest_binds_all_r4_authority_files_and_runtime() -> None:
    manifest = verifier.collect_contract_manifest(require_clean=False)

    assert set(manifest["files"]) == set(verifier.R4_CONTRACT_PATHS)
    assert manifest["runtime"]["python_version"] == sys.version.split()[0]
    assert manifest["runtime"]["numpy_version"] == "2.2.6"
    assert all(len(item["sha256"]) == 64 for item in manifest["files"].values())


def test_materialized_runtime_reconstructs_exact_r2_producer_bytes(tmp_path) -> None:
    manifest = verifier._materialize_frozen_source(tmp_path)

    assert manifest["authority"] == "r3_tested_bundle_reverse_delta_to_r2_runtime"
    assert verifier.hash_file(
        tmp_path / "labs/ego_life_playground_v0/engine.py"
    ) == "54190c093a0e0797bbc690c899231ad6b178092ecd4741ce10a925a2ccfe55e5"
    assert verifier.hash_file(
        tmp_path / "labs/ego_life_playground_v0/predictive_control.py"
    ) == "938a4715726d0dacfe0262e2fbd3edae050d22d26e50710935853e36def82edd"
    boundary = (
        "scripts/codex/"
        "verify_ego_v2_factored_predictive_control_boundary_gate_001c.py"
    )
    assert manifest["files"][boundary]["blob_oid"] == (
        "d336be083e20c3fbf8586201397e8fb51a974a57"
    )
    assert manifest["files"][boundary]["authority"] == (
        "git_object_frozen_evaluator_semantics"
    )


def test_materialized_runtime_import_matches_banked_sqlite_code_path(tmp_path) -> None:
    verifier._materialize_frozen_source(tmp_path)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(tmp_path) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json;"
                "from pathlib import Path;"
                "from scripts.codex import verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2 as r2;"
                "from scripts.codex import verify_ego_v2_factored_predictive_control_boundary_gate_001c as boundary;"
                "from labs.ego_life_playground_v0 import engine,predictive_control;"
                "root=Path.cwd().resolve();"
                "print(json.dumps({'engine_code_path_hash':engine.compute_code_path_hash(),"
                "'paths':{name:Path(module.__file__).resolve().relative_to(root).as_posix() "
                "for name,module in {'r2':r2,'boundary':boundary,'engine':engine,'predictive_control':predictive_control}.items()}},sort_keys=True))"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    receipt = json.loads(completed.stdout)
    assert receipt["engine_code_path_hash"] == (
        "b6eadf0c8ba7244ea08cd67eb936438fda182f43e56c65918bde8264fd5b9d29"
    )
    assert receipt["paths"] == {
        "r2": "scripts/codex/verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2.py",
        "boundary": "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py",
        "engine": "labs/ego_life_playground_v0/engine.py",
        "predictive_control": "labs/ego_life_playground_v0/predictive_control.py",
    }


def test_frozen_subprocess_environment_pins_direct_and_nested_numeric_runtime(
    tmp_path,
) -> None:
    probe = tmp_path / "runtime_probe.py"
    probe.write_text(
        """
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np

code = (
    "import json,sys; from pathlib import Path; import numpy as np; "
    "print(json.dumps({'python_version':sys.version.split()[0],"
    "'numpy_version':np.__version__,'no_user_site':bool(sys.flags.no_user_site),"
    "'numpy_module_path':str(Path(np.__file__).resolve())},sort_keys=True))"
)
nested = subprocess.run(
    [sys.executable, "-c", code],
    check=True,
    capture_output=True,
    text=True,
    env=os.environ.copy(),
)
direct = {
    "python_version": sys.version.split()[0],
    "numpy_version": np.__version__,
    "no_user_site": bool(sys.flags.no_user_site),
    "numpy_module_path": str(Path(np.__file__).resolve()),
}
print(json.dumps({"direct": direct, "nested": json.loads(nested.stdout)}, sort_keys=True))
""".strip()
        + "\n",
        encoding="utf-8",
    )
    environment = verifier.frozen_subprocess_environment(tmp_path)

    completed = subprocess.run(
        [sys.executable, str(probe)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    receipt = json.loads(completed.stdout)

    assert receipt["direct"] == receipt["nested"]
    assert receipt["direct"]["python_version"] == "3.13.7"
    assert receipt["direct"]["numpy_version"] == "2.2.6"
    assert receipt["direct"]["no_user_site"] is True
    assert receipt["direct"]["numpy_module_path"] == str(
        verifier.Path(verifier.np.__file__).resolve()
    )


def test_import_receipt_is_bound_to_materialized_files(tmp_path) -> None:
    manifest = verifier._materialize_frozen_source(tmp_path)
    receipt = {
        "modules": {
            name: {
                "path": relative,
                "sha256": manifest["files"][relative]["sha256"],
            }
            for name, relative in {
                "r2": "scripts/codex/verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2.py",
                "boundary": "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py",
                "controller": "labs/ego_life_playground_v0/controller.py",
                "engine": "labs/ego_life_playground_v0/engine.py",
                "microworld": "labs/ego_life_playground_v0/microworld.py",
                "predictive_control": "labs/ego_life_playground_v0/predictive_control.py",
                "store": "labs/ego_life_playground_v0/store.py",
            }.items()
        },
        "engine_code_path_hash": verifier.R2_RUNTIME_CODE_PATH_HASH,
        "numeric_runtime": verifier.expected_numeric_runtime_receipt(),
    }

    verified = verifier.validate_import_receipt(receipt, manifest)
    assert verified["exact"] is True

    receipt["modules"]["engine"]["path"] = (
        "D:/Project/AIProject/MyProject/Ego/labs/ego_life_playground_v0/engine.py"
    )
    with pytest.raises(verifier.HeadroomDiagnosticError, match="import receipt"):
        verifier.validate_import_receipt(receipt, manifest)

    receipt["modules"]["engine"]["path"] = "labs/ego_life_playground_v0/engine.py"
    receipt["numeric_runtime"]["no_user_site"] = False
    with pytest.raises(verifier.HeadroomDiagnosticError, match="numeric runtime"):
        verifier.validate_import_receipt(receipt, manifest)


def test_main_refuses_nonempty_output_without_mutating_it(
    tmp_path, monkeypatch, capsys
) -> None:
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("preserve-me\n", encoding="utf-8")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", tmp_path, raising=False)

    exit_code = verifier.main(["--gate", str(tmp_path)])

    assert exit_code == 1
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    assert not (tmp_path / "result.json").exists()


def test_main_refuses_wrong_empty_output_path_without_creating_it(
    tmp_path, monkeypatch
) -> None:
    canonical = tmp_path / "canonical"
    wrong = tmp_path / "wrong"
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", canonical)

    exit_code = verifier.main(["--gate", str(wrong)])

    assert exit_code == 1
    assert not wrong.exists()
    assert not canonical.exists()


def test_main_refuses_canonical_path_when_it_is_a_file_without_mutation(
    tmp_path, monkeypatch
) -> None:
    canonical = tmp_path / "canonical"
    canonical.write_bytes(b"preserve-me")
    monkeypatch.setattr(verifier, "CANONICAL_OUTPUT_DIR", canonical)

    exit_code = verifier.main(["--gate", str(canonical)])

    assert exit_code == 1
    assert canonical.read_bytes() == b"preserve-me"
