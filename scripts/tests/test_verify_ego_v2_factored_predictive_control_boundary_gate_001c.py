from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex import (  # type: ignore[attr-defined]
    verify_ego_v2_factored_predictive_control_boundary_gate_001c as target,
)


def test_capture_baseline_emits_deterministic_four_life_fixture(tmp_path, monkeypatch):
    calls: list[dict[str, object]] = []
    original_dispatch = target.PlaygroundController.dispatch

    def recording_dispatch(self, interventions=None, **kwargs):
        calls.append(
            {
                "trigger_source": kwargs.get("trigger_source"),
                "predictive_control_mode": (
                    None if interventions is None else interventions.get("predictive_control_mode")
                ),
            }
        )
        return original_dispatch(self, interventions, **kwargs)

    monkeypatch.setattr(target.PlaygroundController, "dispatch", recording_dispatch)

    output_a = tmp_path / "capture-a"
    output_b = tmp_path / "capture-b"
    fixture_a = target.capture_prechange_baseline(output_a)
    bytes_a = (output_a / target.FIXTURE_NAME).read_bytes()
    fixture_b = target.capture_prechange_baseline(output_b)
    bytes_b = (output_b / target.FIXTURE_NAME).read_bytes()

    assert fixture_a == fixture_b
    assert bytes_a == bytes_b
    assert fixture_a["context_ids"] == [
        "p0_cross_v1:world=52:policy=711",
        "p2_vertical_v1:world=54:policy=711",
    ]
    assert fixture_a["fresh_effect_seeds_consumed"] is False
    assert fixture_a["steps"]
    assert fixture_a["producer_function"] == (
        "verify_ego_v2_factored_predictive_control_boundary_gate_001c.capture_prechange_baseline"
    )
    assert fixture_a["aggregation_rule"] == "ordered_committed_controller_steps_until_four_completed_lives_per_context"
    assert fixture_a["input_source_hashes"]
    assert fixture_a["code_path_hash"]

    required_step_keys = {
        "run_id",
        "context_id",
        "seed",
        "world_seed",
        "life",
        "sequence",
        "command_hash",
        "code_path_hash",
        "trigger_source",
        "selected_action",
        "world_transition",
        "food_gain",
        "metabolism",
        "goal_progress",
        "lifecycle",
        "predictive_selection",
        "predictions_by_action",
        "candidate_values",
        "beam_receipt",
        "action_exposure_counts",
        "token_interaction_counts",
    }

    per_context_lives: dict[str, set[int]] = defaultdict(set)
    for step in fixture_a["steps"]:
        assert required_step_keys <= set(step)
        per_context_lives[step["context_id"]].add(step["life"])
        assert step["trigger_source"] == "ui_run_button"
        assert step["predictive_selection"]["mode"] == "factored_mpc"
        assert step["predictive_selection"]["selection_mode"]
        assert set(step["predictions_by_action"]) == set(target.engine.ACTIONS)
        assert set(step["candidate_values"]) == set(target.engine.ACTIONS)
        assert step["beam_receipt"]["root_actions_by_depth"]

    assert {context_id: sorted(lives) for context_id, lives in per_context_lives.items()} == {
        "p0_cross_v1:world=52:policy=711": [1, 2, 3, 4],
        "p2_vertical_v1:world=54:policy=711": [1, 2, 3, 4],
    }
    assert Counter(call["trigger_source"] for call in calls) == {"ui_run_button": len(calls)}
    assert Counter(call["predictive_control_mode"] for call in calls) == {
        "factored_mpc": len(calls)
    }
