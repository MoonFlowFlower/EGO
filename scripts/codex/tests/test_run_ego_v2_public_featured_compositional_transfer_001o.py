from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "codex" / "run_ego_v2_public_featured_compositional_transfer_001o.py"


def _load_subject():
    spec = importlib.util.spec_from_file_location("public_featured_001o_runner", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evaluator_observation_is_deterministic_and_public_only() -> None:
    subject = _load_subject()
    organism = {"energy": 0.5, "safety": 0.5, "target": 0.72}
    first = subject.make_public_observation("search_dev", 12345, 7, organism)
    second = subject.make_public_observation("search_dev", 12345, 7, organism)
    assert first == second
    subject.reference.validate_public_payload(first)
    encoded = subject.reference.canonical_json(first)
    assert "12345" not in encoded
    assert "search_dev" not in encoded


def test_training_receipt_contains_only_public_history_and_recovers_shared_truth() -> None:
    subject = _load_subject()
    packet = [
        {"opaque_world": "T0", "evaluator_seed": 101, "local_mode": "normal"},
        {"opaque_world": "T1", "evaluator_seed": 202, "local_mode": "full_reverse"},
    ]
    result = subject.train_shared_reference(packet, steps=24)
    assert result["public_events"] == 48
    assert result["candidate_private_field_rejections"] == len(
        subject.reference.FORBIDDEN_CANDIDATE_FIELDS
    )
    assert result["shared_probability_at_evaluator_truth"] > 0.5
    assert "evaluator_seed" not in json.dumps(result["candidate_state"])


def test_trajectory_rows_recompute_and_tamper_fail_closed() -> None:
    subject = _load_subject()
    spec = {"opaque_world": "S0", "evaluator_seed": 303, "local_mode": "normal"}
    trained = subject.train_shared_reference(
        [{"opaque_world": "T0", "evaluator_seed": 101, "local_mode": "normal"}],
        steps=24,
    )
    trajectory = subject.run_trajectory(
        "TRANSFER_EXACT_HIERARCHICAL_BAYES",
        "search_dev",
        spec,
        trained["candidate_state"],
        steps=8,
    )
    recomputed = subject.recompute_trajectory(trajectory)
    assert recomputed["match"] is True
    tampered = json.loads(json.dumps(trajectory))
    tampered["rows"][0]["feedback"]["energy_after"] += 0.1
    with pytest.raises(ValueError, match="row hash"):
        subject.recompute_trajectory(tampered)


def test_unseen_feature_surface_lookup_has_no_exact_key() -> None:
    subject = _load_subject()
    table = subject.build_surface_lookup_table()
    for packet in ("search_dev", "qualification", "replication"):
        for combo_index in subject.reference.FEATURE_COMBO_SPLITS[packet]:
            key = subject.surface_key(subject.reference.combo_bits(combo_index))
            assert key not in table


def test_packet_summary_pairs_worlds_and_reports_control_damage() -> None:
    subject = _load_subject()
    trajectories = []
    for index in range(2):
        world = f"W{index}"
        for arm, early in (
            ("PRIVATE_ORACLE", 2.0),
            ("SCRATCH_EXACT_BAYES", 8.0),
            ("TRANSFER_EXACT_HIERARCHICAL_BAYES", 5.0),
            ("NO_UPDATE", 7.0),
            ("CUE_SHUFFLE", 8.5),
            ("FEATURE_ABLATION", 8.0),
            ("HISTORY_SHUFFLE", 7.5),
            ("SURFACE_LOOKUP", 9.0),
            ("UNIFORM_RANDOM", 10.0),
        ):
            trajectories.append(
                {
                    "arm": arm,
                    "opaque_world": world,
                    "local_mode_evaluator_only": "normal",
                    "early_deficit_auc": early,
                    "late_deficit_auc": early,
                    "total_deficit_auc": 2 * early,
                    "effect_sign_accuracy": 0.9 if "TRANSFER" in arm else 0.5,
                    "deaths": 0,
                    "rows": [],
                }
            )
    summary = subject.summarize_packet(trajectories, positive_worlds_min=1)
    assert summary["transfer_gain"] == pytest.approx(3.0)
    assert summary["recovery_fraction"] == pytest.approx(0.5)
    assert summary["positive_worlds"] == 2
    assert summary["controls"]["NO_UPDATE"]["gain_removal_fraction"] > 0.5

