from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
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
    assert contract["witness_search"]["action_order"] == list(module.ACTION_ORDER)
    assert contract["witness_search"]["analytic_root_lower_bound"] == 76
    assert contract["witness_search"]["processed_node_cap"] == 2_000_000
    assert contract["panel_search"]["processed_node_cap"] == 250_000
    assert contract["panel_search"]["action_order"] == list(module.PANEL_NAV_ACTIONS)
    assert contract["stale_world_seed_firewall"] == [60, 61, 62, 63, 64, 65]
    assert contract["stale_policy_seed_firewall"] == [721, 722]
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

    contract = module.build_frozen_contract()
    contract["panel_search"]["action_order"] = ["move_forward"]
    report = module.validate_frozen_contract(contract)
    assert report["verdict"] == "INVALID_POSTRESULT_RESCUE"
    assert "panel_search.action_order" in report["failure_reasons"]


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


def test_duplicate_ledger_is_disk_backed_packs_prefix_and_duplicate_nodes_skip_expansion(tmp_path: Path):
    module = _load_module()
    ledger = module.DuplicateLedger(tmp_path / "dup.sqlite3")
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
    duplicate = module.make_search_node(
        evaluator_state={"clock": 1, "position": [0, 0]},
        g=3,
        prefix=(0, 2, 4),
        support_counts={"interact": 1},
        rank_rows={"interact": [[1.0, 0.0]]},
        accepted_rows=[{"selected_action": "turn_left", "full_features": [1.0, 0.0]}],
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

    first = ledger.observe(node)
    second = ledger.observe(duplicate)
    assert first["status"] == "new"
    assert second["status"] == "duplicate"
    assert ledger.path.exists()
    with sqlite3.connect(ledger.path) as connection:
        row = connection.execute("SELECT digest, g, prefix_bits FROM duplicate_ledger").fetchone()
    assert row[1] == 3
    assert len(row[0]) == 32
    assert module.unpack_action_prefix(bytes(row[2]), length=3) == (0, 2, 4)
    with pytest.raises(ValueError, match="same digest with different g"):
        ledger.observe(same_digest_different_g, digest_override=first["digest"])

    expansions = {"count": 0}
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
    child = module.make_search_node(
        evaluator_state={"id": "dup-child"},
        g=1,
        prefix=(0,),
        support_counts={},
        rank_rows={},
        accepted_rows=[],
        life_index=1,
        respawn_count=0,
    )

    def expand_fn(node):
        if tuple(node["prefix"]) == ():
            expansions["count"] += 1
            return [child, child]
        expansions["count"] += 1
        return []

    result = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=expand_fn,
        goal_fn=lambda _node: False,
        bound_fn=lambda _node: 0,
        action_budget=3,
        processed_node_cap=10,
        ledger_path=tmp_path / "search.sqlite3",
        contract_digest="c" * 64,
    )
    assert result["status"] == "search_exhausted"
    assert expansions["count"] == 2


def test_dfs_streams_digest_chain_samples_and_uses_authorized_leaf_receipts(tmp_path: Path):
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
    goal = module.make_search_node(
        evaluator_state={"id": "goal"},
        g=89,
        prefix=tuple([0] * 89),
        support_counts={},
        rank_rows={},
        accepted_rows=[],
        life_index=1,
        respawn_count=0,
    )

    result = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda node: [goal] if tuple(node["prefix"]) == () else [],
        goal_fn=lambda node: tuple(node["prefix"]) == tuple([0] * 89),
        bound_fn=lambda node: 0 if tuple(node["prefix"]) == () else 0,
        action_budget=89,
        processed_node_cap=10,
        ledger_path=tmp_path / "stream.sqlite3",
        contract_digest="d" * 64,
    )

    stream = result["receipt_stream"]
    assert stream["processed_nodes"] == 2
    assert stream["first_samples"][0]["processed_node_index"] == 1
    assert stream["final_samples"][-1]["node_disposition"] == "goal"
    assert all("missing_child" not in json.dumps(sample) for sample in stream["first_samples"])
    assert isinstance(stream["digest_chain"], str) and len(stream["digest_chain"]) == 64


def test_live_warm_start_and_replay_use_r1_callables_not_generic_callbacks(monkeypatch: pytest.MonkeyPatch):
    module = _load_module()
    calls = {"init": 0, "advance": 0, "respawn": 0, "checkpoint": 0, "shortest": 0}

    def fake_initialize_evaluator_state(**kwargs):
        calls["init"] += 1
        return {"world": {"step": 0}, "organism": {}, "predictive_state": {}, "episode_index": 0, "life_index": 1, "respawn_count": 0, "awaiting_respawn": False}

    def fake_build_public_checkpoint(**kwargs):
        calls["checkpoint"] += 1
        step = kwargs["world"]["step"]
        feature = [float(step)] * 15
        return {
            "front_token": "v0" if step == 0 else "empty",
            "full_features": module.np.asarray(feature, dtype=module.np.float64),
        }

    def fake_private_shortest_front_path(world, target):
        calls["shortest"] += 1
        if target == "v0":
            return {"actions": ["turn_left"]}
        return {"actions": []}

    def fake_advance_evaluator_action(state, action):
        calls["advance"] += 1
        next_step = state["world"]["step"] + 1
        next_state = dict(state)
        next_state["world"] = {"step": next_step}
        next_state["awaiting_respawn"] = False
        row = {
            "selected_action": action,
            "outcome_type": "interacted" if action == "interact" else "turned",
            "learner_projection": {"front_token": "v0" if action == "interact" else "empty", "quotient_features": [float(next_step)] * 13},
            "full_features": [float(next_step)] * 15,
            "life_index": 1,
            "respawn_count": 0,
        }
        return {"state": next_state, "row": row}

    monkeypatch.setattr(module, "initialize_evaluator_state", fake_initialize_evaluator_state)
    monkeypatch.setattr(module, "build_public_checkpoint", fake_build_public_checkpoint)
    monkeypatch.setattr(module, "private_shortest_front_path", fake_private_shortest_front_path)
    monkeypatch.setattr(module, "advance_evaluator_action", fake_advance_evaluator_action)
    monkeypatch.setattr(module, "advance_evaluator_respawn", lambda state: state)
    monkeypatch.setattr(module, "compute_support_counts", lambda rows: {"interact::v0::interacted": 4, "interact::v1::interacted": 4, "interact::v2::interacted": 4, "interact::v3::interacted": 4, "interact::v4::interacted": 4, "interact::no_object": 4, "move_forward::moved": 4, "move_forward::blocked": 4, "rest::rested": 4, "turn_left::turned": 4, "turn_right::turned": 4})
    monkeypatch.setattr(module, "compute_rank_reports", lambda context_id, rows: {f"{context_id}::{action}": {"rank": 13} for action in module.ACTION_ORDER})

    warm = module.run_live_warm_start(module.build_frozen_contract()["contexts"][0], action_budget=89)

    assert warm["replay_valid"] is True
    assert warm["certificate_found"] is True
    assert calls["init"] == 1
    assert calls["advance"] > 0
    assert calls["checkpoint"] > 0
    assert calls["shortest"] > 0


def test_independent_checker_does_not_call_primary_dfs_and_requires_matching_edge_digest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    child = module.make_search_node(
        evaluator_state={"id": "child"},
        g=89,
        prefix=(0,),
        support_counts={},
        rank_rows={},
        accepted_rows=[],
        life_index=1,
        respawn_count=0,
    )
    primary = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda node: [child] if tuple(node["prefix"]) == () else [],
        goal_fn=lambda node: False,
        bound_fn=lambda node: 0 if tuple(node["prefix"]) == () else 0,
        action_budget=89,
        processed_node_cap=10,
        ledger_path=tmp_path / "primary.sqlite3",
        contract_digest="e" * 64,
    )

    def forbidden_primary(*args, **kwargs):
        raise AssertionError("primary DFS must not be called by independent checker")

    monkeypatch.setattr(module, "depth_first_branch_and_bound", forbidden_primary)
    verified = module.independent_verify_witness_search(
        root=root,
        expand_fn=lambda node: [child] if tuple(node["prefix"]) == () else [],
        goal_fn=lambda _node: False,
        bound_fn=lambda node: 0,
        action_budget=89,
        processed_node_cap=10,
        expected_receipt_stream=primary["receipt_stream"],
        contract_digest="e" * 64,
    )
    assert verified["verified"] is True
    assert verified["edge_census_digest"] == primary["receipt_stream"]["digest_chain"]

    mismatch = module.independent_verify_witness_search(
        root=root,
        expand_fn=lambda node: [],
        goal_fn=lambda _node: False,
        bound_fn=lambda node: 0,
        action_budget=89,
        processed_node_cap=10,
        expected_receipt_stream=primary["receipt_stream"],
        contract_digest="e" * 64,
    )
    assert mismatch["verified"] is False


def test_panel_search_uses_disk_backed_state_store_dedupe_and_live_five_action_truths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_module()
    calls = {"checkpoint": 0, "truth": 0}

    def fake_initialize_panel_state(*, context_id, layout_id, world_seed, policy_seed, panel_rollout_id):
        return {
            "node": f"r{panel_rollout_id}-start",
            "world": {"front_token": None},
            "organism": {},
            "predictive_state": {},
            "episode_index": panel_rollout_id - 1,
            "front_token": None,
            "panel_rollout_id": panel_rollout_id,
        }

    def fake_panel_expand(state):
        token = state["front_token"]
        if token is None:
            return {
                "move_forward": {"node": f"{state['panel_rollout_id']}-empty", "world": {"front_token": "empty"}, "organism": {}, "predictive_state": {}, "episode_index": state["panel_rollout_id"] - 1, "front_token": "empty", "panel_rollout_id": state["panel_rollout_id"]},
                "turn_left": {"node": f"{state['panel_rollout_id']}-v0", "world": {"front_token": "v0"}, "organism": {}, "predictive_state": {}, "episode_index": state["panel_rollout_id"] - 1, "front_token": "v0", "panel_rollout_id": state["panel_rollout_id"]},
            }
        if token == "empty":
            return {
                "turn_right": {"node": f"{state['panel_rollout_id']}-v0", "world": {"front_token": "v0"}, "organism": {}, "predictive_state": {}, "episode_index": state["panel_rollout_id"] - 1, "front_token": "v0", "panel_rollout_id": state["panel_rollout_id"]},
            }
        return {}

    def fake_build_public_checkpoint(**kwargs):
        calls["checkpoint"] += 1
        token = kwargs["world"]["front_token"]
        full = module.np.asarray([1.0 if token == "v0" else 2.0] * 15, dtype=module.np.float64)
        quotient = module.quotient_features(full)
        checkpoint_hash = module.engine.canonical_hash({"front_token": token, "panel_rollout_id": kwargs["episode_index"] + 1})
        return {
            "checkpoint_hash": checkpoint_hash,
            "front_token": token,
            "observation": {"visual": [[None, None, None], [None, None, token], [None, None, None]]},
            "predictor_input": {"organism": {}, "belief_summary": {}, "observation": {}},
            "full_features": full,
            "quotient_features": quotient,
        }

    def fake_truth(**kwargs):
        calls["truth"] += 1
        return {
            "truth": {"outcome_type": f"{kwargs['action']}_ok", "actual_delta": {}, "terminal_receipt": None},
            "callable_receipts": {
                "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
                "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
                "compute_metabolism_ledger": "labs.ego_life_playground_v0.engine.compute_metabolism_ledger",
            },
        }

    monkeypatch.setattr(module, "initialize_panel_rollout_state", fake_initialize_panel_state)
    monkeypatch.setattr(module, "panel_expand_navigation", fake_panel_expand)
    monkeypatch.setattr(module, "build_public_checkpoint", fake_build_public_checkpoint)
    monkeypatch.setattr(module, "evaluate_forced_action_truth", fake_truth)
    monkeypatch.setattr(module, "compute_rank_reports", lambda context_id, rows: {f"{context_id}::{action}": {"rank": 13} for action in module.ACTION_ORDER})

    report = module.run_panel_search(
        context_spec=module.build_frozen_contract()["contexts"][0],
        target_multiset=["v0", "empty"],
        storage_dir=tmp_path,
        processed_node_cap=200,
        rollout_ids=(9, 10),
    )

    assert report["status"] == "PANEL_CAPACITY_NOT_CERTIFIED"
    assert report["storage"]["state_store_path"].endswith("panel_state_store.sqlite3")
    assert report["storage"]["queue_entry_mode"] == "parent_pointer"
    assert calls["checkpoint"] > 0
    assert calls["truth"] == len(report["retained_checkpoints"]) * 5
    assert all(sorted(actions) == sorted(module.ACTION_ORDER) for actions in report["actions_by_checkpoint"].values())


def test_panel_search_completes_multiple_rollouts_before_positive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = _load_module()
    seen = {"rollouts": []}

    def fake_initialize_panel_state(*, context_id, layout_id, world_seed, policy_seed, panel_rollout_id):
        seen["rollouts"].append(panel_rollout_id)
        return {
            "world": {"front_token": None},
            "organism": {},
            "predictive_state": {},
            "episode_index": panel_rollout_id - 1,
            "front_token": None,
            "panel_rollout_id": panel_rollout_id,
            "awaiting_respawn": False,
        }

    def fake_panel_expand(state):
        token = state["front_token"]
        if token is None:
            return {
                "move_forward": {"world": {"front_token": "empty"}, "organism": {}, "predictive_state": {}, "episode_index": state["panel_rollout_id"] - 1, "front_token": "empty", "panel_rollout_id": state["panel_rollout_id"], "awaiting_respawn": False},
            }
        if token == "empty":
            return {
                "turn_right": {"world": {"front_token": "v0"}, "organism": {}, "predictive_state": {}, "episode_index": state["panel_rollout_id"] - 1, "front_token": "v0", "panel_rollout_id": state["panel_rollout_id"], "awaiting_respawn": False},
            }
        return {}

    def fake_build_public_checkpoint(**kwargs):
        token = kwargs["world"]["front_token"]
        rollout_id = kwargs["episode_index"] + 1
        full = module.np.asarray([1.0 if token == "v0" else 2.0] * 15, dtype=module.np.float64)
        quotient = module.quotient_features(full)
        checkpoint_hash = module.engine.canonical_hash({"front_token": token, "panel_rollout_id": rollout_id})
        return {
            "checkpoint_hash": checkpoint_hash,
            "front_token": token,
            "observation": {"visual": [[None, None, None], [None, None, token], [None, None, None]]},
            "predictor_input": {"organism": {}, "belief_summary": {}, "observation": {}},
            "full_features": full,
            "quotient_features": quotient,
        }

    def fake_truth(**kwargs):
        return {
            "truth": {"outcome_type": f"{kwargs['action']}_ok", "actual_delta": {}, "terminal_receipt": None},
            "callable_receipts": {
                "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
                "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
                "compute_metabolism_ledger": "labs.ego_life_playground_v0.engine.compute_metabolism_ledger",
            },
        }

    monkeypatch.setattr(module, "initialize_panel_rollout_state", fake_initialize_panel_state)
    monkeypatch.setattr(module, "panel_expand_navigation", fake_panel_expand)
    monkeypatch.setattr(module, "build_public_checkpoint", fake_build_public_checkpoint)
    monkeypatch.setattr(module, "evaluate_forced_action_truth", fake_truth)
    monkeypatch.setattr(module, "compute_rank_reports", lambda context_id, rows: {f"{context_id}::{action}": {"rank": 13} for action in module.ACTION_ORDER})
    report = module.run_panel_search(
        context_spec=module.build_frozen_contract()["contexts"][0],
        target_multiset=["empty", "v0"],
        storage_dir=tmp_path,
        processed_node_cap=200,
        rollout_ids=(9, 10),
    )
    assert seen["rollouts"] == [9, 10]
    assert report["construction_complete"] is True
    assert len(report["rollouts"]) == 2
    assert report["rollouts"][0]["complete"] is True
    assert report["rollouts"][1]["complete"] is True


def test_recursive_leakage_reuses_r1_scanner_and_formal_boundary_is_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_module()
    clean = {"rows": [{"front_token": "empty", "quotient_features": [0.0] * 13}]}
    leaked = {
        "rows": [
            {"front_token": "v1", "private": "d29ybGRfNTI="},
            {"front_token": "v0", "raw": "world=52"},
            {"front_token": "empty", "index": 54},
        ]
    }

    clean_report = module.recursive_leakage_scan(clean)
    leaked_report = module.recursive_leakage_scan(leaked)
    assert clean_report["all_clean"] is True
    assert leaked_report["all_clean"] is False
    assert leaked_report["all_positive_controls_detected"] is True
    assert set(leaked_report["positive_controls_detected"]) == {"base64", "direct", "numeric_index"}

    monkeypatch.setattr(module, "collect_runtime_boundary", lambda: {"output_absent": False, "runtime_receipt": module.runtime_receipt()})
    with pytest.raises(ValueError, match="output directory must be absent or empty"):
        module.run_formal(output_dir=tmp_path / "formal", execute_search=False)

    verdict = module.dispatch_r2_verdict(
        provenance_clean=True,
        contract_valid=True,
        witness_reports=[{"status": "WITNESS_SEARCH_INCONCLUSIVE", "complete_search": False}],
        panel_reports=[],
    )
    assert verdict == "WITNESS_SEARCH_INCONCLUSIVE"

    fail_closed = module.dispatch_r2_verdict(
        provenance_clean=True,
        contract_valid=True,
        witness_reports=[{"status": "search_exhausted", "complete_search": True, "independently_verified": False}],
        panel_reports=[],
    )
    assert fail_closed == "SEARCH_IMPLEMENTATION_INVALID"


def test_formal_orchestrator_calls_provenance_witness_panel_packet_and_verifier(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = _load_module()
    calls = {"observe": 0, "load": 0, "validate": 0, "witness": 0, "panel": 0, "write": 0, "verify": 0}

    monkeypatch.setattr(module, "collect_runtime_boundary", lambda: {"output_absent": True, "runtime_receipt": module.runtime_receipt()})
    monkeypatch.setattr(module, "collect_r2_pre_run_observation", lambda **kwargs: calls.__setitem__("observe", calls["observe"] + 1) or {"head_parent": "impl", "head": "prov", "repository_root": "repo", "branch": "branch", "head_changed_paths": ["docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/PRE_RUN_PROVENANCE.json"], "worktree_clean": True, "index_clean": True, "provenance_tracked_at_head": True, "runtime_receipt": module.runtime_receipt(), "engine_code_path_hash": "c" * 64, "source_hashes": {path: "a" * 64 for path in module.R2_REQUIRED_PROVENANCE_SOURCE_PATHS}, "input_hashes": {path: "b" * 64 for path in module.R2_REQUIRED_PROVENANCE_INPUT_PATHS}, "dependency_hashes": {path: "c" * 64 for path in module.R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS}, "output_dir": "tmp", "output_absent_or_empty": True})
    monkeypatch.setattr(module, "load_pre_run_provenance", lambda path: calls.__setitem__("load", calls["load"] + 1) or {"schema_version": "ego.v2.001h_r2.pre_run_provenance.v1", "task_id": "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2", "implementation_commit": "impl", "runtime_receipt": module.runtime_receipt(), "engine_code_path_hash": "c" * 64, "source_hashes": {path: "a" * 64 for path in module.R2_REQUIRED_PROVENANCE_SOURCE_PATHS}, "input_hashes": {path: "b" * 64 for path in module.R2_REQUIRED_PROVENANCE_INPUT_PATHS}, "dependency_hashes": {path: "c" * 64 for path in module.R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS}, "output_precondition": "absent_or_empty"})
    monkeypatch.setattr(module, "validate_pre_run_provenance", lambda document, observation: calls.__setitem__("validate", calls["validate"] + 1) or {"passed": True, "provenance_commit": "prov"})
    monkeypatch.setattr(module, "run_witness_stage", lambda context_spec: calls.__setitem__("witness", calls["witness"] + 1) or {"status": "witness_certificate_found", "certificate_found": True, "rows": [], "rank_reports": {}, "complete_search": False, "independently_verified": False})
    monkeypatch.setattr(module, "run_panel_search", lambda **kwargs: calls.__setitem__("panel", calls["panel"] + 1) or {"status": "PANEL_CAPACITY_NOT_CERTIFIED", "panel_rollout_ids": list(kwargs["rollout_ids"]), "target_order": list(module.PANEL_TARGET_MULTISET), "rollouts": [], "raw_checkpoints": [], "retained_checkpoints": [], "rows": [], "support_report": {"before_dedupe": {}, "after_dedupe": {}, "required_floors": module.PANEL_FLOORS, "passed": False}, "cell_support_report": {"cell_counts": {}, "required_floor_by_cell": {}, "passed": False}, "rank_reports": {}, "construction_complete": False, "panel_capacity_admitted": False, "panel_hash": "a" * 64})
    monkeypatch.setattr(module, "recursive_leakage_scan", lambda payload: {"all_clean": True, "all_positive_controls_detected": True, "findings": []})
    monkeypatch.setattr(module, "run_tamper_controls", lambda **kwargs: {"all_tamper_controls_rejected": True, "controls": {}})
    monkeypatch.setattr(module, "independent_reduce_context", lambda **kwargs: {"reported_values_match": True, "producer_receipts_valid": True, "hashes_valid": True, "check_map": {"control_envelope_comparable": True, "privileged_support_witness_found": False, "deterministic_panel_capacity_admitted": False}})
    monkeypatch.setattr(module, "fresh_process_recompute", lambda bundle: {"equal": True, "contexts": {}})
    monkeypatch.setattr(module, "write_r2_formal_packet", lambda output, bundle: calls.__setitem__("write", calls["write"] + 1) or {"verdict": bundle["adjudication"]["verdict"]})
    monkeypatch.setattr(module, "verify_r2_formal_packet", lambda output: calls.__setitem__("verify", calls["verify"] + 1) or {"verified": True})

    result = module.run_formal(output_dir=tmp_path, execute_search=True)

    assert result["verdict"] == "PANEL_CAPACITY_NOT_CERTIFIED"
    assert calls == {"observe": 1, "load": 1, "validate": 1, "witness": 2, "panel": 2, "write": 1, "verify": 1}
