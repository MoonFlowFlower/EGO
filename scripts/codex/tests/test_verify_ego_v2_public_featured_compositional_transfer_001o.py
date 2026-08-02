from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
VERIFIER = ROOT / "scripts" / "codex" / "verify_ego_v2_public_featured_compositional_transfer_001o.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verifier_is_independent_of_producer_modules() -> None:
    source = VERIFIER.read_text(encoding="utf-8")
    assert "public_featured_transfer" not in source
    assert "run_ego_v2_public_featured" not in source


def test_independent_row_check_accepts_real_row_and_rejects_tamper() -> None:
    runner = _load(
        ROOT / "scripts" / "codex" / "run_ego_v2_public_featured_compositional_transfer_001o.py",
        "runner_for_verifier_test",
    )
    verifier = _load(VERIFIER, "independent_verifier")
    trained = runner.train_shared_reference(
        [{"opaque_world": "T", "evaluator_seed": 901, "local_mode": "normal"}],
        steps=8,
    )
    trajectory = runner.run_trajectory(
        "SCRATCH_EXACT_BAYES",
        "search_dev",
        {"opaque_world": "S", "evaluator_seed": 902, "local_mode": "normal"},
        trained["candidate_state"],
        steps=4,
    )
    assert verifier.verify_row_integrity(trajectory["rows"][0])["pass"] is True
    tampered = json.loads(json.dumps(trajectory["rows"][0]))
    tampered["deficit_loss"] += 0.01
    with pytest.raises(ValueError, match="hash"):
        verifier.verify_row_integrity(tampered)


def test_private_field_positive_control_fails_even_after_rehash() -> None:
    verifier = _load(VERIFIER, "independent_verifier_private")
    row = {
        "candidate_observation": {
            "organism": {"energy": 0.5, "safety": 0.5, "target": 0.72},
            "slots": [{"features": [0, 0, 0, 0, 0]}] * 3,
            "previous": None,
            "seed": 123,
        },
        "candidate_input_receipt": "unused",
        "feedback": {
            "energy_before": 0.5,
            "safety_before": 0.5,
            "energy_after": 0.5,
            "safety_after": 0.5,
            "died": False,
        },
        "deficit_loss": 0.44,
    }
    row["candidate_input_receipt"] = verifier.canonical_hash(row["candidate_observation"])
    row["row_hash"] = verifier.canonical_hash(row)
    with pytest.raises(ValueError, match="private candidate field"):
        verifier.verify_row_integrity(row)

