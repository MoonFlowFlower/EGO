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
        scratch_dir=tmp_path / "checker-ok",
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
        scratch_dir=tmp_path / "checker-mismatch",
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
    source_hashes = module.sha256_map(module.R2_REQUIRED_PROVENANCE_SOURCE_PATHS)
    input_hashes = module.sha256_map(module.R2_REQUIRED_PROVENANCE_INPUT_PATHS)
    dependency_hashes = module.sha256_map(module.R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS)

    monkeypatch.setattr(module, "collect_runtime_boundary", lambda: {"output_absent": True, "runtime_receipt": module.runtime_receipt()})
    monkeypatch.setattr(module, "collect_r2_pre_run_observation", lambda **kwargs: calls.__setitem__("observe", calls["observe"] + 1) or {"head_parent": "impl", "head": "prov", "repository_root": "repo", "branch": "branch", "head_changed_paths": ["docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/PRE_RUN_PROVENANCE.json"], "worktree_clean": True, "index_clean": True, "provenance_tracked_at_head": True, "runtime_receipt": module.runtime_receipt(), "engine_code_path_hash": "c" * 64, "source_hashes": source_hashes, "input_hashes": input_hashes, "dependency_hashes": dependency_hashes, "output_dir": "tmp", "output_absent_or_empty": True})
    monkeypatch.setattr(module, "load_pre_run_provenance", lambda path: calls.__setitem__("load", calls["load"] + 1) or {"schema_version": "ego.v2.001h_r2.pre_run_provenance.v1", "task_id": "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2", "implementation_commit": "impl", "runtime_receipt": module.runtime_receipt(), "engine_code_path_hash": "c" * 64, "source_hashes": source_hashes, "input_hashes": input_hashes, "dependency_hashes": dependency_hashes, "output_precondition": "absent_or_empty"})
    monkeypatch.setattr(module, "validate_pre_run_provenance", lambda document, observation: calls.__setitem__("validate", calls["validate"] + 1) or {"passed": True, "provenance_commit": "prov"})
    monkeypatch.setattr(module, "run_witness_stage", lambda context_spec, **_kwargs: calls.__setitem__("witness", calls["witness"] + 1) or {"status": "witness_certificate_found", "certificate_found": True, "rows": [], "rank_reports": {}, "complete_search": False, "independently_verified": False})
    monkeypatch.setattr(module, "run_panel_search", lambda **kwargs: calls.__setitem__("panel", calls["panel"] + 1) or {"status": "PANEL_CAPACITY_NOT_CERTIFIED", "panel_rollout_ids": list(kwargs["rollout_ids"]), "target_order": list(module.PANEL_TARGET_MULTISET), "rollouts": [], "raw_checkpoints": [], "retained_checkpoints": [], "rows": [], "support_report": {"before_dedupe": {}, "after_dedupe": {}, "required_floors": module.PANEL_FLOORS, "passed": False}, "cell_support_report": {"cell_counts": {}, "required_floor_by_cell": {}, "passed": False}, "rank_reports": {}, "construction_complete": False, "panel_capacity_admitted": False, "panel_hash": "a" * 64})
    monkeypatch.setattr(module, "scan_r2_evidence_leakage", lambda payload: {"all_clean": True, "all_positive_controls_detected": True, "findings": []})
    monkeypatch.setattr(module, "run_r2_tamper_controls", lambda **kwargs: {"all_tamper_controls_rejected": True, "controls": {}})
    monkeypatch.setattr(module, "independent_reduce_context", lambda **kwargs: {"reported_values_match": True, "producer_receipts_valid": True, "hashes_valid": True, "check_map": {"control_envelope_comparable": True, "privileged_support_witness_found": False, "deterministic_panel_capacity_admitted": False}})
    monkeypatch.setattr(module, "fresh_process_recompute", lambda bundle, **_kwargs: {"equal": True, "contexts": {}})
    monkeypatch.setattr(module, "write_r2_formal_packet", lambda output, bundle: calls.__setitem__("write", calls["write"] + 1) or {"verdict": bundle["adjudication"]["verdict"]})
    monkeypatch.setattr(module, "verify_r2_formal_packet", lambda output: calls.__setitem__("verify", calls["verify"] + 1) or {"verified": True})

    result = module.run_formal(output_dir=tmp_path, execute_search=True)

    assert result["verdict"] == "PANEL_CAPACITY_NOT_CERTIFIED"
    assert calls == {"observe": 1, "load": 1, "validate": 1, "witness": 2, "panel": 2, "write": 1, "verify": 1}


def _synthetic_node(module, name: str, g: int, prefix: tuple[int, ...]):
    return module.make_search_node(
        evaluator_state={"name": name, "clock": g},
        g=g,
        prefix=prefix,
        support_counts={},
        rank_rows={},
        accepted_rows=[],
        life_index=1,
        respawn_count=0,
    )


def test_dfs_cap_is_checked_before_next_new_node_and_two_leaf_frontier_is_not_overrun(tmp_path: Path):
    module = _load_module()
    root = _synthetic_node(module, "root", 0, ())
    left = _synthetic_node(module, "left", 89, (0,) * 89)
    right = _synthetic_node(module, "right", 89, (1,) * 89)

    result = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda node: [left, right] if node["evaluator_state"]["name"] == "root" else [],
        goal_fn=lambda _node: False,
        bound_fn=lambda _node: 0,
        action_budget=89,
        processed_node_cap=2,
        ledger_path=tmp_path / "cap.sqlite3",
        contract_digest="1" * 64,
    )

    assert result["status"] == "WITNESS_SEARCH_INCONCLUSIVE"
    assert result["processed_nodes"] == 2
    assert result["unprocessed_legal_child"] is True
    assert result["receipt_stream"]["disposition_counts"]["horizon_non_goal"] == 1


def test_independent_checker_rejects_sample_and_disposition_tamper_even_when_digest_field_is_unchanged(tmp_path: Path):
    module = _load_module()
    root = _synthetic_node(module, "root", 89, (0,) * 89)
    primary = module.depth_first_branch_and_bound(
        root=root,
        expand_fn=lambda _node: [],
        goal_fn=lambda _node: False,
        bound_fn=lambda _node: 0,
        action_budget=89,
        processed_node_cap=2,
        ledger_path=tmp_path / "primary.sqlite3",
        contract_digest="2" * 64,
    )
    tampered = json.loads(json.dumps(primary["receipt_stream"]))
    tampered["first_samples"][0]["node_disposition"] = "goal"

    checked = module.independent_verify_witness_search(
        root=root,
        expand_fn=lambda _node: [],
        goal_fn=lambda _node: False,
        bound_fn=lambda _node: 0,
        action_budget=89,
        processed_node_cap=2,
        expected_receipt_stream=tampered,
        contract_digest="2" * 64,
        scratch_dir=tmp_path / "checker-tamper",
    )
    assert checked["verified"] is False
    assert "serialized_receipts" in checked["failure_reasons"]


def test_live_witness_root_and_five_action_expansion_use_real_r1_callables_for_frozen_contexts(monkeypatch: pytest.MonkeyPatch):
    module = _load_module()
    original_init = module.initialize_evaluator_state
    original_advance = module.advance_evaluator_action
    calls = {"init": 0, "advance": 0}

    def counted_init(**kwargs):
        calls["init"] += 1
        return original_init(**kwargs)

    def counted_advance(state, action):
        calls["advance"] += 1
        return original_advance(state, action)

    monkeypatch.setattr(module, "initialize_evaluator_state", counted_init)
    monkeypatch.setattr(module, "advance_evaluator_action", counted_advance)
    for context in module.build_frozen_contract()["contexts"]:
        root = module.build_live_witness_root(context)
        children = module.expand_live_witness_node(root, action_budget=89)
        assert [item["action"] for item in children] == list(module.ACTION_ORDER)
        assert all(item["node"]["g"] == 1 for item in children)
        assert all(item["node"]["accepted_rows"][0]["selected_action"] == item["action"] for item in children)
    assert calls == {"init": 2, "advance": 10}


def test_warm_failure_cannot_refute_and_runs_real_dfs_from_untouched_live_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = _load_module()
    context = module.build_frozen_contract()["contexts"][0]
    monkeypatch.setattr(
        module,
        "run_live_warm_start",
        lambda *_args, **_kwargs: {"certificate_found": False, "replay_valid": False, "actions": [], "rows": [], "support_counts": {}, "rank_reports": {}},
    )
    calls = {"advance": 0}
    original_advance = module.advance_evaluator_action

    def counted_advance(state, action):
        calls["advance"] += 1
        return original_advance(state, action)

    monkeypatch.setattr(module, "advance_evaluator_action", counted_advance)
    report = module.run_witness_stage(context, scratch_dir=tmp_path, processed_node_cap=1)
    assert calls["advance"] == 5
    assert report["status"] == "WITNESS_SEARCH_INCONCLUSIVE"
    assert report["complete_search"] is False
    assert report["independently_verified"] is False


def _panel_fixture(monkeypatch: pytest.MonkeyPatch, module, graph, tokens, seen_rollouts, truth_calls):
    def init(**kwargs):
        rollout = kwargs["panel_rollout_id"]
        seen_rollouts.append(rollout)
        return {"node": f"r{rollout}:root", "world": {"node": f"r{rollout}:root"}, "organism": {}, "predictive_state": {}, "episode_index": rollout - 1, "life_index": 1, "respawn_count": 0, "awaiting_respawn": False}

    def checkpoint(**kwargs):
        node = kwargs["world"]["node"]
        token = tokens.get(node)
        full = module.np.asarray([float(sum(map(ord, node)) % 17)] * 15, dtype=module.np.float64)
        return {"checkpoint_hash": module.engine.canonical_hash({"node": node}), "front_token": token, "observation": {"visual": node}, "predictor_input": {"organism": {}, "belief_summary": {}}, "full_features": full, "quotient_features": module.quotient_features(full)}

    def expand(state):
        children = {}
        for action, target in graph.get(state["world"]["node"], {}).items():
            children[action] = {**state, "node": target, "world": {"node": target}, "awaiting_respawn": target.endswith(":dead")}
        return children

    def truth(**kwargs):
        assert set(seen_rollouts) == {9, 10}
        truth_calls.append(kwargs["action"])
        return {"truth": {"outcome_type": "ok", "actual_delta": {}, "terminal_receipt": None}, "callable_receipts": {"transition_world": "live", "compute_actual_delta": "live", "compute_metabolism_ledger": "live"}}

    monkeypatch.setattr(module, "initialize_panel_rollout_state", init)
    monkeypatch.setattr(module, "build_public_checkpoint", checkpoint)
    monkeypatch.setattr(module, "panel_expand_navigation", expand)
    monkeypatch.setattr(module, "evaluate_forced_action_truth", truth)
    monkeypatch.setattr(module, "json_public_checkpoint", lambda cp, **kw: {**cp, **kw})
    monkeypatch.setattr(module, "compute_rank_reports", lambda context_id, rows: {f"{context_id}::{action}": {"rank": 13} for action in module.ACTION_ORDER})


def test_panel_bfs_dedupes_loops_prunes_terminal_before_count_uses_per_rollout_cap_and_defers_truths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    module = _load_module()
    seen_rollouts, truth_calls = [], []
    graph, tokens = {}, {}
    for rollout in (9, 10):
        root, goal, dead = f"r{rollout}:root", f"r{rollout}:goal", f"r{rollout}:dead"
        graph[root] = {"turn_left": root, "turn_right": dead, "move_forward": goal}
        graph[goal] = {}
        tokens[goal] = "v0"
    _panel_fixture(monkeypatch, module, graph, tokens, seen_rollouts, truth_calls)

    report = module.run_panel_search(
        context_spec=module.build_frozen_contract()["contexts"][0],
        target_multiset=["v0"],
        storage_dir=tmp_path,
        processed_node_cap=2,
        rollout_ids=(9, 10),
    )
    assert [item["processed_nodes"] for item in report["rollouts"]] == [2, 2]
    assert report["construction_complete"] is True
    assert len(report["raw_checkpoints"]) == 2
    assert truth_calls == list(module.ACTION_ORDER) * 2
    assert report["storage"]["queue_contains_only_ids"] is True
    with sqlite3.connect(report["storage"]["state_store_path"]) as connection:
        assert connection.execute("SELECT COUNT(*) FROM search_keys").fetchone()[0] == 4


def test_provenance_requires_exact_sets_authority_pins_paths_clean_git_and_caps():
    module = _load_module()
    contract = module.build_frozen_contract()
    observation = {
        "repository_root": str(module.REPO_ROOT).replace("\\", "/"),
        "branch": "codex/test",
        "head": "b" * 40,
        "head_parent": "a" * 40,
        "head_changed_paths": [module.R2_PROVENANCE_RELPATH],
        "worktree_clean": True,
        "index_clean": True,
        "provenance_tracked_at_head": True,
        "runtime_receipt": module.runtime_receipt(),
        "engine_code_path_hash": "c" * 64,
        "source_hashes": {path: "1" * 64 for path in module.R2_REQUIRED_PROVENANCE_SOURCE_PATHS},
        "input_hashes": {path: "2" * 64 for path in module.R2_REQUIRED_PROVENANCE_INPUT_PATHS},
        "dependency_hashes": {path: "3" * 64 for path in module.R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS},
        "authority_pins": dict(module.FROZEN_SOURCE_PINS),
        "output_dir": module.R2_OUTPUT_RELPATH,
        "output_absent_or_empty": True,
        "caps": {"witness_processed_node_cap": 2_000_000, "panel_processed_node_cap_per_rollout": 250_000},
        "action_orders": {"witness": list(module.ACTION_ORDER), "panel_navigation": list(module.PANEL_NAV_ACTIONS)},
        "firewalls": {"stale_world_seeds": sorted(module.STALE_WORLD_SEEDS), "stale_policy_seeds": sorted(module.STALE_POLICY_SEEDS)},
    }
    document = {
        "schema_version": "ego.v2.001h_r2.pre_run_provenance.v1",
        "task_id": contract["task_id"],
        "implementation_commit": observation["head_parent"],
        "runtime_receipt": observation["runtime_receipt"],
        "engine_code_path_hash": observation["engine_code_path_hash"],
        "source_hashes": dict(observation["source_hashes"]),
        "input_hashes": dict(observation["input_hashes"]),
        "dependency_hashes": dict(observation["dependency_hashes"]),
        "authority_pins": dict(observation["authority_pins"]),
        "output_dir": observation["output_dir"],
        "output_precondition": "absent_or_empty",
        "caps": dict(observation["caps"]),
        "action_orders": dict(observation["action_orders"]),
        "firewalls": dict(observation["firewalls"]),
    }
    assert module.validate_pre_run_provenance(document, observation)["passed"] is True

    mutations = []
    missing = json.loads(json.dumps(document)); missing["source_hashes"].pop(next(iter(missing["source_hashes"]))); mutations.append(missing)
    extra = json.loads(json.dumps(document)); extra["source_hashes"]["extra.py"] = "0" * 64; mutations.append(extra)
    path_tamper = json.loads(json.dumps(document)); path_tamper["output_dir"] = "artifacts/elsewhere"; mutations.append(path_tamper)
    authority = json.loads(json.dumps(document)); authority["authority_pins"][next(iter(authority["authority_pins"]))] = "0" * 64; mutations.append(authority)
    cap = json.loads(json.dumps(document)); cap["caps"]["witness_processed_node_cap"] -= 1; mutations.append(cap)
    for tampered in mutations:
        with pytest.raises(ValueError):
            module.validate_pre_run_provenance(tampered, observation)


def test_subprocess_recompute_uses_different_pid_and_rejects_reported_row_tamper():
    module = _load_module()
    rows = [{"selected_action": "turn_left", "learner_projection": {"quotient_features": [0.0] * 13}, "life_index": 1, "respawn_count": 0}]
    receipt = module.spawn_independent_row_recompute("ctx", rows)
    assert receipt["child_pid"] != receipt["parent_pid"]
    assert receipt["row_count"] == 1
    assert receipt["rows_digest"] == module.engine.canonical_hash(rows)
    with pytest.raises(ValueError, match="row recompute mismatch"):
        module.validate_independent_row_recompute(rows, {**receipt, "row_count": 2})


def test_packet_clears_only_owned_scratch_has_exact_file_set_and_semantic_verifier_rejects_rebuilt_manifest_tamper(tmp_path: Path):
    module = _load_module()
    packet = tmp_path / "packet"
    scratch = packet / "_scratch"
    scratch.mkdir(parents=True)
    (scratch / "ledger.sqlite3").write_bytes(b"scratch")
    context_id = module.build_frozen_contract()["contexts"][0]["context_id"]
    bundle = {
        "contexts": {
            context_id: {
                "control": {"prefix": []},
                "witness": {"rows": [], "rank_reports": {}, "replay_valid": False, "search_report": {}, "ablation_report": {}},
                "panel": {"rows": [], "panel_rollout_ids": list(range(9, 17)), "target_order": list(module.PANEL_TARGET_MULTISET), "rollouts": [], "raw_checkpoints": [], "retained_checkpoints": [], "rank_reports": {}, "support_report": {"before_dedupe": {token: 0 for token in module.PANEL_FLOORS}, "after_dedupe": {token: 0 for token in module.PANEL_FLOORS}, "required_floors": dict(module.PANEL_FLOORS), "passed": False}, "cell_support_report": {"cell_counts": {}, "required_floor_by_cell": {}, "passed": False}, "construction_complete": False, "panel_capacity_admitted": False, "panel_hash": module.engine.canonical_hash({})},
            }
        },
        "adjudication": {"verdict": "PANEL_CAPACITY_NOT_CERTIFIED"},
        "source_hashes": {}, "input_hashes": {}, "dependency_hashes": {},
        "provenance_document": {"runtime_receipt": module.runtime_receipt(), "implementation_commit": "a" * 40},
        "leakage_report": {"all_clean": True, "all_positive_controls_detected": True, "findings": []},
        "fresh_recompute_report": {"equal": True, "contexts": {}},
    }
    module.write_r2_formal_packet(packet, bundle)
    assert not scratch.exists()
    assert module.verify_r2_formal_packet(packet)["verified"] is True

    result_path = packet / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["verdict"] = "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND"
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (packet / "artifact_manifest.json").write_text(json.dumps(module.build_artifact_manifest(packet), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="semantic"):
        module.verify_r2_formal_packet(packet)


@pytest.mark.parametrize("world_seed", [52, 54])
def test_frozen_context_live_smoke_advances_few_steps_without_formal_run(world_seed: int):
    module = _load_module()
    context = next(item for item in module.build_frozen_contract()["contexts"] if item["world_seed"] == world_seed)
    root = module.build_live_witness_root(context)
    first = module.expand_live_witness_node(root, action_budget=89)[0]["node"]
    second = module.expand_live_witness_node(first, action_budget=89)[2]["node"]
    assert [row["selected_action"] for row in second["accepted_rows"]] == ["turn_left", "move_forward"]
    assert second["g"] == 2


def test_r2_tamper_controls_are_computed_and_dispatcher_fails_closed_on_unknown_or_missing(tmp_path: Path):
    module = _load_module()
    witness = [{"status": "witness_certificate_found", "certificate_found": True, "rows": []}]
    panel = [{"status": "PANEL_CAPACITY_NOT_CERTIFIED", "panel_capacity_admitted": False, "rows": [], "retained_checkpoints": []}]
    report = module.run_r2_tamper_controls(
        contract=module.build_frozen_contract(),
        source_hashes=dict(module.FROZEN_SOURCE_PINS),
        witness_reports=witness,
        panel_reports=panel,
        scratch_dir=tmp_path,
    )
    assert report["all_tamper_controls_rejected"] is True
    assert set(report["controls"]) >= {"contract_budget", "authority_hash", "row_recompute", "producer_receipt", "unknown_verdict"}
    assert all(item["rejected"] is True for item in report["controls"].values())
    assert module.dispatch_r2_verdict(provenance_clean=True, contract_valid=True, witness_reports=[{"status": "mystery"}], panel_reports=[]) == "SEARCH_IMPLEMENTATION_INVALID"
    assert module.dispatch_r2_verdict(provenance_clean=True, contract_valid=True, witness_reports=[], panel_reports=[]) == "SEARCH_IMPLEMENTATION_INVALID"


@pytest.mark.parametrize("world_seed", [52, 54])
def test_panel_navigation_live_smoke_calls_r1_advance_for_three_legal_actions(monkeypatch: pytest.MonkeyPatch, world_seed: int):
    module = _load_module()
    context = next(item for item in module.build_frozen_contract()["contexts"] if item["world_seed"] == world_seed)
    state = module.initialize_panel_rollout_state(
        context_id=context["context_id"], layout_id=context["layout_id"], world_seed=world_seed,
        policy_seed=context["policy_seed"], panel_rollout_id=9,
    )
    calls = []
    original = module.advance_evaluator_action

    def counted(current, action):
        calls.append(action)
        return original(current, action)

    monkeypatch.setattr(module, "advance_evaluator_action", counted)
    children = module.panel_expand_navigation(state)
    assert calls == list(module.PANEL_NAV_ACTIONS)
    assert set(children).issubset(set(module.PANEL_NAV_ACTIONS))
