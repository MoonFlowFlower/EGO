from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "verify_ego_v2_acquisition_capacity_certificate_001h_r2.py"
)


def _load_module():
    assert SCRIPT_PATH.exists(), "001H-R2 verifier module is not implemented"
    spec = importlib.util.spec_from_file_location("verify_001h_r2", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_frozen_contract_matches_authority_and_root_lower_bound_is_76():
    module = _load_module()

    contract = module.build_frozen_contract()

    assert contract["task_id"] == "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2"
    assert [item["context_id"] for item in contract["contexts"]] == [
        "p0_cross_v1:world=52:policy=711",
        "p2_vertical_v1:world=54:policy=711",
    ]
    assert contract["witness_search"]["action_budget"] == 89
    assert contract["witness_search"]["processed_node_cap"] == 2_000_000
    assert contract["panel_search"]["processed_node_cap"] == 250_000
    assert contract["panel_target_multiset"] == [
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
    assert module.root_analytic_lower_bound(contract) == 76


def test_contract_tamper_routes_to_invalid_postresult_rescue_before_adjudication():
    module = _load_module()
    contract = module.build_frozen_contract()
    contract["contexts"][0]["world_seed"] = 60

    report = module.validate_frozen_contract(contract)

    assert report["valid"] is False
    assert report["verdict"] == "INVALID_POSTRESULT_RESCUE"
    assert any("contexts[0].world_seed" in reason for reason in report["failure_reasons"])


@pytest.mark.parametrize(
    ("support_deficits", "rank_gaps", "expected"),
    [
        (
            {"interact": 24, "move_forward": 13, "rest": 13, "turn_left": 13, "turn_right": 13},
            {"interact": 0, "move_forward": 0, "rest": 0, "turn_left": 0, "turn_right": 0},
            76,
        ),
        (
            {"interact": 24, "move_forward": 3, "rest": 3, "turn_left": 3, "turn_right": 3},
            {"interact": 1, "move_forward": 13, "rest": 13, "turn_left": 13, "turn_right": 13},
            76,
        ),
        (
            {"interact": 1, "move_forward": 0, "rest": 0, "turn_left": 0, "turn_right": 0},
            {"interact": 13, "move_forward": 0, "rest": 0, "turn_left": 0, "turn_right": 0},
            13,
        ),
    ],
)
def test_remaining_action_lower_bound_uses_max_per_action_without_double_counting(
    support_deficits,
    rank_gaps,
    expected,
):
    module = _load_module()

    assert (
        module.remaining_action_lower_bound(
            support_deficits=support_deficits,
            rank_gaps=rank_gaps,
        )
        == expected
    )


def test_budget_below_root_lower_bound_is_immediate_non_solution():
    module = _load_module()

    result = module.assess_budget_feasibility(
        action_budget=75,
        support_deficits={
            "interact": 24,
            "move_forward": 13,
            "rest": 13,
            "turn_left": 13,
            "turn_right": 13,
        },
        rank_gaps={action: 0 for action in module.ACTION_ORDER},
        g=0,
    )

    assert result == {
        "status": "bound_pruned",
        "g": 0,
        "h": 76,
        "f": 76,
        "action_budget": 75,
    }


def test_duplicate_key_includes_full_rows_and_same_key_different_g_is_invalid():
    module = _load_module()
    node = module.make_search_node(
        evaluator_state={"clock": 1, "position": [0, 0]},
        g=3,
        prefix=(0, 2, 4),
        support_counts={"interact": 1},
        rank_rows={"interact": [[1.0, 0.0]]},
        accepted_rows=[{"selected_action": "turn_left", "full_features": [1.0, 0.0]}],
        life_index=1,
        respawn_count=0,
    )
    same_but_row_changed = module.make_search_node(
        evaluator_state={"clock": 1, "position": [0, 0]},
        g=3,
        prefix=(0, 2, 4),
        support_counts={"interact": 1},
        rank_rows={"interact": [[1.0, 0.0]]},
        accepted_rows=[{"selected_action": "turn_left", "full_features": [0.0, 1.0]}],
        life_index=1,
        respawn_count=0,
    )
    same_digest_different_g = module.make_search_node(
        evaluator_state={"clock": 1, "position": [0, 0]},
        g=4,
        prefix=(0, 2, 4, 1),
        support_counts={"interact": 1},
        rank_rows={"interact": [[1.0, 0.0]]},
        accepted_rows=[{"selected_action": "turn_left", "full_features": [1.0, 0.0]}],
        life_index=1,
        respawn_count=0,
    )

    digest = module.search_node_digest(node)
    assert module.search_node_digest(same_but_row_changed) != digest

    ledger = module.DuplicateLedger()
    first = ledger.observe(node)
    assert first["status"] == "new"
    assert ledger.observe(node)["status"] == "duplicate"
    with pytest.raises(ValueError, match="same digest with different g"):
        ledger.observe(same_digest_different_g, digest_override=digest)


def test_dfs_receipts_respect_fixed_order_leaf_kinds_and_inconclusive_cap():
    module = _load_module()
    root = module.make_search_node(
        evaluator_state={"id": "root"},
        g=0,
        prefix=(),
        support_counts={},
        rank_rows={},
        accepted_rows=[],
        life_index=1,
        respawn_count=0,
    )
    expansions = {
        (): [
            module.make_search_node(
                evaluator_state={"id": "goal"},
                g=1,
                prefix=(0,),
                support_counts={},
                rank_rows={},
                accepted_rows=[],
                life_index=1,
                respawn_count=0,
            )
        ]
    }

    result = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda node: expansions.get(tuple(node["prefix"]), []),
        goal_fn=lambda node: tuple(node["prefix"]) == (0,),
        bound_fn=lambda node: 0,
        action_budget=1,
        processed_node_cap=10,
    )

    assert result["status"] == "goal_found"
    assert result["processed_nodes"] == 2
    assert result["receipts"][0]["dispositions"][0]["action"] == "turn_left"
    assert result["receipts"][1]["node_disposition"] == "goal"

    capped = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda node: [
            module.make_search_node(
                evaluator_state={"id": f"child-{index}"},
                g=1,
                prefix=(index,),
                support_counts={},
                rank_rows={},
                accepted_rows=[],
                life_index=1,
                respawn_count=0,
            )
            for index in range(2)
        ],
        goal_fn=lambda _node: False,
        bound_fn=lambda _node: 0,
        action_budget=3,
        processed_node_cap=1,
    )
    assert capped["status"] == "WITNESS_SEARCH_INCONCLUSIVE"
    assert capped["complete_search"] is False
    assert capped["unprocessed_legal_child"] is True


def test_warm_start_prefers_best_scored_candidate_and_replay_valid_skip():
    module = _load_module()
    history: list[str] = []

    def simulate(prefix, candidate):
        history.append(candidate["name"])
        return {
            "node": module.make_search_node(
                evaluator_state={"candidate": candidate["name"]},
                g=len(candidate["actions"]),
                prefix=tuple(candidate["actions"]),
                support_counts={},
                rank_rows={},
                accepted_rows=[],
                life_index=1,
                respawn_count=0,
            ),
            "passed": candidate["passed"],
        }

    warm = module.run_warm_start(
        prefix=(),
        candidate_specs=[
            {"name": "worse", "score": (5, -10, 3, 7, 1, (1, 2, 3)), "actions": (1, 2, 3), "passed": False},
            {"name": "best", "score": (1, -13, 2, 0, 0, (0, 4)), "actions": (0, 4), "passed": True},
        ],
        simulate_candidate=simulate,
    )

    assert history == ["best"]
    assert warm["status"] == "warm_start_certificate"
    assert warm["dfs_root_untouched"] is True
    assert warm["candidate_name"] == "best"


def test_panel_bfs_can_reorder_targets_when_fixed_order_traps_but_legal_order_completes():
    module = _load_module()
    start = {"node": "start", "front_token": None}
    graph = {
        "start": {
            "turn_left": {"node": "toward-v0", "front_token": "v0"},
            "move_forward": {"node": "toward-empty", "front_token": "empty"},
        },
        "toward-v0": {
            "move_forward": {"node": "dead-end", "front_token": None},
        },
        "toward-empty": {
            "turn_right": {"node": "toward-v0-after-empty", "front_token": "v0"},
        },
    }

    result = module.search_panel_certificate(
        start_state=start,
        target_multiset=["v0", "empty"],
        expand_fn=lambda state: graph.get(state["node"], {}),
        checkpoint_hash_fn=lambda state: state["node"],
        processed_node_cap=20,
    )

    assert result["status"] == "panel_certificate_found"
    assert result["claimed_targets"] == ["empty", "v0"]
    assert result["action_sequence"] == ["move_forward", "turn_right"]


def test_leakage_scan_and_tamper_controls_fail_closed_on_positive_controls():
    module = _load_module()
    clean = {"rows": [{"front_token": "empty", "quotient_features": [0.0, 1.0]}]}
    leaked = {
        "rows": [
            {"front_token": "v1", "private": "d29ybGRfNTI="},
            {"front_token": "v0", "raw": "world=52"},
            {"front_token": "empty", "index": 54},
        ]
    }

    clean_report = module.scan_forbidden_leakage(clean)
    leaked_report = module.scan_forbidden_leakage(leaked)

    assert clean_report["clean"] is True
    assert leaked_report["clean"] is False
    assert set(leaked_report["positive_controls_detected"]) == {"base64", "direct", "numeric_index"}

    tamper = module.semantic_tamper_report(
        baseline={"verdict": "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND", "search_digest": "a" * 64},
        tampered={"verdict": "PANEL_CAPACITY_NOT_CERTIFIED", "search_digest": "b" * 64},
    )
    assert tamper["failed_closed"] is True
    assert tamper["failure_reasons"] == ["search_digest", "verdict"]
