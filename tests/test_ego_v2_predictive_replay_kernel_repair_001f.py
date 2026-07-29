from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control
from labs.ego_life_playground_v0.microworld import policy_observation


def _plan_kwargs() -> dict:
    state = engine.initial_state(
        run_id="001f-kernel-equivalence",
        seed=711,
        layout_id="p2_vertical_v1",
    )
    return {
        "state": state["predictive_control"],
        "observation": policy_observation(state["world"]),
        "organism": state["organism"],
        "active_goal": "energy",
        "heuristic_scores": {action: 0.0 for action in engine.ACTIONS},
        "horizon": predictive_control.HORIZON,
        "beam_width": predictive_control.BEAM_WIDTH,
        "discount": predictive_control.DISCOUNT,
        "relative_map_mode": "relative",
        "goal_value_mode": "contextual",
        "action_costs": engine.ACTION_COSTS,
        "run_seed": 711,
        "episode_index": 0,
        "sequence": 1,
    }


def _projection_report() -> dict:
    return {
        key: {
            "nlms_denominator": 3.25 + index,
            "nlms_step": -0.001 * index,
            "projection_mean": 0.0001 * index,
            "raw_conditionals_hash": f"{index + 1:064x}",
            "projected_conditionals_hash": f"{index + 11:064x}",
            "projection_max_abs_difference": 0.0,
            "projection_preserved_conditionals": True,
        }
        for index, key in enumerate(predictive_control.STATE_KEYS)
    }


def test_exact_prewarm_plan_matches_callable_scalar_reference_bit_for_bit():
    kwargs = _plan_kwargs()

    optimized = predictive_control.plan_action(**deepcopy(kwargs))
    scalar = predictive_control.plan_action_scalar_reference(**deepcopy(kwargs))

    assert optimized == scalar


def test_batched_prediction_vectors_equal_scalar_rows_with_nonzero_offsets():
    rng = np.random.default_rng(711)
    packed_rows = rng.normal(
        0.0,
        0.3,
        size=(9, len(predictive_control.OUTCOMES) + len(predictive_control.STATE_KEYS) + 2),
    ).astype(predictive_control.NUMERIC_DTYPE)
    offsets = rng.normal(
        0.0,
        0.04,
        size=(len(predictive_control.OUTCOMES), len(predictive_control.STATE_KEYS)),
    ).astype(predictive_control.NUMERIC_DTYPE)
    visit_counts = list(range(9))
    actual = predictive_control._batch_planning_prediction_vectors(  # noqa: SLF001
        packed_rows,
        delta_outcome_offsets=offsets,
        visit_counts=visit_counts,
    )
    expected = []
    for index, row in enumerate(packed_rows):
        state = predictive_control.empty_state()
        organism = {
            "energy": float(0.05 + index * 0.1),
            "safety": 0.5,
            "connection": 0.5,
            "stimulation": 0.5,
        }
        payload = {
            "observation": None,
            "organism": organism,
            "belief_summary": {
                "relative_pose": [0, 0],
                "relative_facing": "N",
                "known_cell_count": 1,
                "known_object_count": index,
                "front_token": "empty",
                "token_counts": {f"v{item}": 0 for item in range(5)},
            },
        }
        key = predictive_control._visit_key("move_forward", payload)  # noqa: SLF001
        state["model"]["visit_counts"][key] = visit_counts[index]
        expected.append(
            predictive_control._planning_prediction_vector_from_packed(  # noqa: SLF001
                state,
                payload=payload,
                action="move_forward",
                packed_values=row,
                delta_outcome_offsets=offsets,
                visit_key_cache={},
            )
        )

    assert actual == expected


def test_compact_projection_receipt_is_losslessly_expandable_and_fails_closed():
    projection = _projection_report()
    compact = engine._compact_predictive_update(  # noqa: SLF001
        {
            "schema_version": predictive_control.UPDATE_SCHEMA_VERSION,
            "applied": True,
            "delta_projection_by_state": projection,
        }
    )

    assert "delta_projection_by_state" not in compact
    assert compact["delta_projection_receipt"]["schema_version"].endswith(".v1")
    assert set(compact["delta_projection_receipt"]) == {
        "schema_version",
        "source_hash",
        "dictionary",
        "rows",
    }
    assert engine.expand_compact_predictive_update(compact)[
        "delta_projection_by_state"
    ] == projection

    corrupted = deepcopy(compact)
    corrupted["delta_projection_receipt"]["rows"][0].pop()
    with pytest.raises(engine.EngineInvariantError, match="projection receipt"):
        engine.expand_compact_predictive_update(corrupted)


def test_compact_candidate_values_are_losslessly_expandable_and_keep_ui_total():
    plan = predictive_control.plan_action(**_plan_kwargs())
    compact = engine._compact_predictive_plan(plan)  # noqa: SLF001

    assert compact is not None
    assert set(compact["candidate_value_receipt"]) == {
        "schema_version",
        "source_hash",
    }
    assert all(
        "total" in value for value in compact["candidate_values"].values()
    )
    assert any(
        "homeostatic_value" not in value
        for value in compact["candidate_values"].values()
    )
    expanded = engine.expand_compact_predictive_plan(compact)
    assert expanded["candidate_values"] == plan["candidate_values"]

    corrupted = deepcopy(compact)
    corrupted["candidate_values"][engine.ACTIONS[0]]["breakdown"].pop()
    with pytest.raises(engine.EngineInvariantError, match="candidate receipt"):
        engine.expand_compact_predictive_plan(corrupted)


def test_code_path_manifest_binds_predictive_control_source():
    manifest = engine.compute_code_path_manifest()
    paths = [item["path"] for item in manifest["files"]]

    assert paths.count("predictive_control.py") == 1
