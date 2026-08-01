from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from labs.ego_life_playground_v0.causal_sprout import CausalSproutConfig
from scripts.codex.verify_ego_v2_causal_sprout_demo_001a import (
    HeldoutAlreadyRevealedError,
    REQUIRED_ARTIFACTS,
    generate_evidence,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_test_packet_generates_complete_hash_bound_evidence_and_refuses_second_reveal(tmp_path: Path):
    output = tmp_path / "evidence"
    dev = CausalSproutConfig(
        namespace_prefix="causal_sprout_dev_verifier_unit",
        split="dev",
        context_count=4,
        steps_per_context=8,
        hidden_size=24,
        bptt_steps=4,
        learning_rate=0.015,
        correlation_probability=0.9,
        seed=1911,
    )
    heldout = CausalSproutConfig(
        namespace_prefix="causal_sprout_heldout_verifier_unit",
        split="heldout",
        context_count=3,
        steps_per_context=8,
        hidden_size=24,
        bptt_steps=4,
        learning_rate=0.015,
        correlation_probability=0.1,
        seed=2911,
    )
    result = generate_evidence(output, dev_config=dev, heldout_config=heldout, test_only=True)
    assert set(REQUIRED_ARTIFACTS).issubset({path.name for path in output.iterdir()})
    assert result["test_only"] is True
    assert result["heldout_reveal_count"] == 1

    manifest = json.loads((output / "artifact_manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["artifacts"]:
        path = output / entry["path"]
        assert path.exists()
        assert _sha256(path) == entry["sha256"]

    freeze = json.loads((output / "freeze_manifest.json").read_text(encoding="utf-8"))
    commitment = json.loads((output / "heldout_commitment.json").read_text(encoding="utf-8"))
    assert freeze["development_completed_before_freeze"] is True
    assert len(freeze["dev_run_trace_hash"]) == 64
    assert commitment["freeze_hash"] == freeze["freeze_hash"]

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    row_recompute = json.loads((output / "row_recompute_report.json").read_text(encoding="utf-8"))
    leakage = json.loads((output / "leakage_report.json").read_text(encoding="utf-8"))
    assert replay["stored_action_used_as_input"] is False
    assert replay["exact_recompute"] is True
    assert row_recompute["all_rows_match"] is True
    assert leakage["positive_controls_rejected"] is True

    with pytest.raises(HeldoutAlreadyRevealedError):
        generate_evidence(output, dev_config=dev, heldout_config=heldout, test_only=True)


def test_failure_packet_keeps_negative_result_and_failure_manifest(tmp_path: Path):
    output = tmp_path / "negative"
    config = CausalSproutConfig(
        namespace_prefix="causal_sprout_dev_negative_unit",
        split="dev",
        context_count=2,
        steps_per_context=5,
        hidden_size=24,
        bptt_steps=3,
        learning_rate=0.0,
        correlation_probability=0.9,
        seed=19,
    )
    heldout = CausalSproutConfig(
        namespace_prefix="causal_sprout_heldout_negative_unit",
        split="heldout",
        context_count=2,
        steps_per_context=5,
        hidden_size=24,
        bptt_steps=3,
        learning_rate=0.0,
        correlation_probability=0.1,
        seed=29,
    )
    result = generate_evidence(output, dev_config=config, heldout_config=heldout, test_only=True)
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert result["verdict"] != "BOUNDED_CAUSAL_REGULARITY_LEARNED"
    assert failure["failure_count"] > 0
    assert failure["failures"]
    assert "not prove" in (output / "claim_ceiling.txt").read_text(encoding="utf-8").lower()
