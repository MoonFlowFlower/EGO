from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.app import DISCLOSURE, PlaygroundController
from labs.ego_life_playground_v0.engine import (
    CUES,
    DEFAULT_TOGGLES,
    EMA_ALPHA,
    EngineInvariantError,
    canonical_hash,
    canonical_json,
    compute_code_path_hash,
    compute_step,
    compute_trace_hash,
    initial_state,
    make_command,
    make_run_metadata,
    state_hash,
)
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore, default_db_path


def _step(state=None, *, run_id="run-a", seed=17, cue="resource", toggles=None, meta=None):
    state = deepcopy(state or initial_state())
    meta = deepcopy(meta or make_run_metadata(run_id, seed, "episode-a"))
    command = make_command(
        sequence=state["step"] + 1,
        cue=cue,
        toggles=toggles or DEFAULT_TOGGLES,
        prev_command_hash=state["last_command_hash"],
    )
    return compute_step(state, command, meta), command, meta


def _controller(tmp_path, *, run_id="run-a", seed=17, callback=None):
    store = SQLiteEventStore(tmp_path / "playground.sqlite3")
    controller = PlaygroundController(
        store, run_id=run_id, seed=seed, episode_id="episode-a", on_committed=callback
    )
    return store, controller


def _commit_one(store, controller, cue="resource", toggles=None):
    result = controller.dispatch(cue, toggles or DEFAULT_TOGGLES)
    assert result.receipt.committed, result.receipt.error
    assert result.step is not None
    return result


def test_compute_step_is_fully_deterministic():
    state = initial_state()
    meta = make_run_metadata("deterministic", 41, "episode-d")
    command = make_command(
        sequence=1, cue="contact", toggles=DEFAULT_TOGGLES, prev_command_hash=None
    )
    first = compute_step(deepcopy(state), deepcopy(command), deepcopy(meta))
    second = compute_step(deepcopy(state), deepcopy(command), deepcopy(meta))
    assert canonical_json(first.next_state) == canonical_json(second.next_state)
    assert canonical_json(first.trace) == canonical_json(second.trace)


def test_seed_is_used_by_deterministic_tie_component():
    first, _, _ = _step(seed=1)
    second, _, _ = _step(seed=2)
    first_ties = {item["action"]: item["tie_break"] for item in first.trace["candidates"]}
    second_ties = {item["action"]: item["tie_break"] for item in second.trace["candidates"]}
    assert first_ties != second_ties
    assert first.trace["seed"] == 1
    assert second.trace["seed"] == 2


def test_command_contains_only_replay_inputs_and_hash():
    command = make_command(
        sequence=1, cue="resource", toggles=DEFAULT_TOGGLES, prev_command_hash=None
    )
    assert set(command) == {
        "sequence",
        "cue",
        "toggles",
        "prev_command_hash",
        "command_hash",
    }
    forbidden = {"selected_action", "actual_delta", "state", "candidate", "prediction"}
    assert not (set(command) & forbidden)


def test_prediction_error_updates_tabular_ema():
    result, _, _ = _step(cue="resource")
    update = result.trace["model_update"]
    assert update["applied"] is True
    assert update["alpha"] == EMA_ALPHA
    assert update["new_count"] == 1
    assert any(abs(value) > 0 for value in result.trace["prediction_error"].values())
    entry = result.next_state["model"][result.trace["context_key"]][result.trace["selected_action"]]
    assert entry["count"] == 1
    assert entry["ema_delta"] == result.trace["actual_delta"]


def test_learning_off_reads_but_does_not_change_model_bytes():
    first, _, meta = _step()
    before = canonical_json(first.next_state["model"])
    toggles = dict(DEFAULT_TOGGLES, learning_on=False)
    second, _, _ = _step(first.next_state, toggles=toggles, meta=meta)
    assert canonical_json(second.next_state["model"]) == before
    assert second.trace["model_update"]["applied"] is False
    selected = next(
        item for item in second.trace["candidates"] if item["action"] == second.trace["selected_action"]
    )
    # Existing estimates remain legal read inputs even when writes are frozen.
    assert selected["model_ref"]["source"] in {"tabular_ema", "hardcoded_prior"}


def test_memory_off_zeroes_bias_refs_and_preserves_memory_bytes():
    state = initial_state()
    state["memory"]["consolidated"].append(
        {
            "memory_id": "con-force",
            "kind": "consolidated",
            "key": "resource|stimulation|approach",
            "cue": "resource",
            "dominant_goal": "stimulation",
            "action": "approach",
            "strength": 0.5,
            "provenance_ids": ["ep-a", "ep-b", "ep-c"],
            "episode_count": 3,
        }
    )
    before = canonical_json(state["memory"])
    toggles = dict(DEFAULT_TOGGLES, memory_on=False)
    result, _, _ = _step(state, toggles=toggles)
    assert canonical_json(result.next_state["memory"]) == before
    assert all(item["memory_bias"] == 0.0 for item in result.trace["candidates"])
    assert all(item["memory_refs"] == [] for item in result.trace["candidates"])
    assert result.trace["memory_update"]["reason"] == "memory_disabled"


def test_structured_memory_directly_changes_action_score_and_selection():
    state = initial_state()
    without, _, _ = _step(state)
    state["memory"]["consolidated"].append(
        {
            "memory_id": "con-force",
            "kind": "consolidated",
            "key": "resource|stimulation|approach",
            "cue": "resource",
            "dominant_goal": "stimulation",
            "action": "approach",
            "strength": 0.5,
            "provenance_ids": ["ep-a", "ep-b", "ep-c"],
            "episode_count": 3,
        }
    )
    with_memory, _, _ = _step(state)
    approach = next(item for item in with_memory.trace["candidates"] if item["action"] == "approach")
    assert without.trace["selected_action"] == "forage"
    assert approach["memory_bias"] > 0
    assert approach["memory_refs"] == ["con-force"]
    assert with_memory.trace["selected_action"] == "approach"


def test_consolidation_requires_three_matching_episodes_and_records_provenance():
    state = initial_state({"energy": 0.0, "safety": 0.9, "connection": 0.9, "stimulation": 0.9})
    meta = make_run_metadata("consolidate", 17, "episode-c")
    result = None
    for _ in range(3):
        result, _, _ = _step(state, run_id="consolidate", cue="resource", meta=meta)
        state = result.next_state
    assert result is not None
    update = result.trace["memory_update"]
    assert update["consolidation_applied"] is True
    assert len(update["consolidation_refs"]) == 3
    consolidated = result.next_state["memory"]["consolidated"]
    assert len(consolidated) == 1
    assert consolidated[0]["provenance_ids"] == update["consolidation_refs"]


def test_consolidation_off_keeps_episodic_writes_but_never_consolidates():
    state = initial_state({"energy": 0.0, "safety": 0.9, "connection": 0.9, "stimulation": 0.9})
    meta = make_run_metadata("no-consolidate", 17, "episode-c")
    toggles = dict(DEFAULT_TOGGLES, consolidation_on=False)
    for _ in range(3):
        result, _, _ = _step(state, cue="resource", toggles=toggles, meta=meta)
        state = result.next_state
    assert len(state["memory"]["episodic"]) == 3
    assert state["memory"]["consolidated"] == []
    assert result.trace["memory_update"]["reason"] == "consolidation_disabled"


def test_trace_has_computed_evidence_provenance_fields():
    result, command, meta = _step()
    trace = result.trace
    assert trace["producer_function"].endswith("engine.compute_step")
    assert trace["run_id"] == meta["run_id"]
    assert trace["episode_id"] == meta["episode_id"]
    assert trace["input_artifacts"][-1] == f"command:{command['command_hash']}"
    assert trace["aggregation_rule"] == "single_step_deterministic_one_step_argmax"
    assert trace["code_path_hash"] == compute_code_path_hash()
    assert trace["trace_hash"] == compute_trace_hash(trace)
    assert trace["state_after_hash"] == state_hash(result.next_state)


def test_atomic_command_and_trace_commit(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        result = _commit_one(store, controller)
        assert store.row_counts(controller.run_id) == (1, 1)
        assert result.receipt.trace_hash == controller.last_trace["trace_hash"]
    finally:
        store.close()


def test_second_insert_failure_rolls_back_both_rows_and_returns_typed_receipt(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        store.connection.execute(
            "CREATE TRIGGER force_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced trace failure'); END"
        )
        result = controller.dispatch("resource", DEFAULT_TOGGLES)
        assert result.receipt.committed is False
        assert result.receipt.run_id == controller.run_id
        assert result.receipt.sequence == 1
        assert result.receipt.trace_hash is None
        assert "forced trace failure" in result.receipt.error
        assert store.row_counts(controller.run_id) == (0, 0)
    finally:
        store.close()


def test_controller_changes_state_and_callback_only_after_commit(tmp_path):
    callbacks = []
    store, controller = _controller(tmp_path, callback=lambda state, trace: callbacks.append((state, trace)))
    try:
        before = canonical_json(controller.state)
        store.connection.execute(
            "CREATE TRIGGER force_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced'); END"
        )
        failed = controller.dispatch("resource", DEFAULT_TOGGLES)
        assert failed.receipt.committed is False
        assert canonical_json(controller.state) == before
        assert controller.last_trace is None
        assert callbacks == []
        store.connection.execute("DROP TRIGGER force_trace_failure")
        succeeded = controller.dispatch("resource", DEFAULT_TOGGLES)
        assert succeeded.receipt.committed is True
        assert controller.state["step"] == 1
        assert len(callbacks) == 1
    finally:
        store.close()


def test_fresh_store_restart_recomputes_same_state_model_memory_and_trace(tmp_path):
    db_path = tmp_path / "restart.sqlite3"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id="restart", seed=29, episode_id="episode-r")
    _commit_one(store, controller, "resource")
    _commit_one(store, controller, "contact")
    expected_state = canonical_json(controller.state)
    expected_trace = canonical_json(controller.last_trace)
    store.close()

    restarted_store = SQLiteEventStore(db_path)
    try:
        restarted = PlaygroundController(restarted_store, run_id="restart", seed=999)
        assert canonical_json(restarted.state) == expected_state
        assert canonical_json(restarted.last_trace) == expected_trace
        assert restarted.recovery_status == "recomputed 2 command(s)"
    finally:
        restarted_store.close()


def test_stored_action_tamper_even_after_rehash_fails_recovery(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        ).fetchone()
        trace = json.loads(row["trace_json"])
        trace["selected_action"] = "withdraw" if trace["selected_action"] != "withdraw" else "approach"
        trace["trace_hash"] = compute_trace_hash(trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
            (canonical_json(trace), trace["trace_hash"], controller.run_id),
        )
        with pytest.raises(RecoveryError, match="independent recomputation"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_command_tamper_fails_before_stored_trace_is_accepted(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        ).fetchone()
        command = json.loads(row["command_json"])
        command["cue"] = "threat"
        store.connection.execute(
            "UPDATE commands SET command_json = ? WHERE run_id = ? AND sequence = 1",
            (canonical_json(command), controller.run_id),
        )
        with pytest.raises(RecoveryError, match="recomputation failed"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_missing_trace_fails_row_parity(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "DELETE FROM traces WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        )
        with pytest.raises(RecoveryError, match="row parity"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_run_code_path_drift_fails_closed(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "UPDATE runs SET code_path_hash = 'drifted' WHERE run_id = ?", (controller.run_id,)
        )
        with pytest.raises(RecoveryError, match="code-path drift"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_store_source_bytes_participate_in_code_path_hash_and_recovery(tmp_path, monkeypatch):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        original_hash = compute_code_path_hash()
        original_read_bytes = Path.read_bytes

        def read_with_store_drift(path: Path) -> bytes:
            payload = original_read_bytes(path)
            if path.name == "store.py" and path.parent.name == "ego_life_playground_v0":
                return payload + b"\n# bounded store drift positive control\n"
            return payload

        monkeypatch.setattr(Path, "read_bytes", read_with_store_drift)
        assert compute_code_path_hash() != original_hash
        with pytest.raises(RecoveryError, match="code-path drift"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_export_requires_recovery_and_emits_provenance_jsonl(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        output = store.export_run(controller.run_id, tmp_path / "trace.jsonl")
        records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        assert records[0]["record_type"] == "run"
        assert records[0]["producer_function"].endswith("SQLiteEventStore.export_run")
        assert records[0]["code_path_hash"] == compute_code_path_hash()
        assert records[1]["record_type"] == "trace"
        assert records[1]["trace"]["trace_hash"] == controller.last_trace["trace_hash"]
    finally:
        store.close()


def test_export_after_tamper_fails_without_creating_output(tmp_path):
    store, controller = _controller(tmp_path)
    output = tmp_path / "must-not-exist.jsonl"
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "UPDATE commands SET command_hash = 'tampered' WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        )
        with pytest.raises(RecoveryError):
            store.export_run(controller.run_id, output)
        assert not output.exists()
    finally:
        store.close()


def test_app_import_is_safe_and_discloses_baseline():
    import tkinter as tk
    import labs.ego_life_playground_v0.app as app

    assert tk._default_root is None
    assert app.PlaygroundController is PlaygroundController
    assert DISCLOSURE == (
        "Deterministic deficit scorer + tabular EMA; local product-clock surface; science weight 0."
    )


def test_default_database_path_is_outside_repository():
    path = default_db_path().resolve()
    assert REPO_ROOT.resolve() not in path.parents


def test_forbidden_import_and_runtime_surface_ast_scan():
    implementation_paths = [
        REPO_ROOT / "labs/ego_life_playground_v0/__init__.py",
        REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
        REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        REPO_ROOT / "labs/ego_life_playground_v0/app.py",
        REPO_ROOT / "scripts/run_ego_life_playground_v0.py",
    ]
    forbidden_import_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "openai",
        "anthropic",
        "EgoDesktop",
        "EgoOperator",
    }
    for path in implementation_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert not (imported & forbidden_import_roots), (path, imported & forbidden_import_roots)


def test_launcher_headless_smoke_uses_real_controller_store_and_recovery(tmp_path, capsys):
    launcher = REPO_ROOT / "scripts/run_ego_life_playground_v0.py"
    spec = importlib.util.spec_from_file_location("run_ego_life_playground_v0_test", launcher)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.main(["--headless-smoke", "--db", str(tmp_path / "smoke.sqlite3"), "--seed", "53"])
    payload = json.loads(capsys.readouterr().out.strip())
    assert result == 0
    assert payload["recovered"] is True
    assert payload["step"] == 1
    assert payload["science_weight"] == 0
    assert len(payload["trace_hash"]) == 64


def test_all_cues_are_callable_through_one_compute_path():
    for cue in CUES:
        result, command, _ = _step(cue=cue)
        assert result.trace["command"] == command
        assert result.trace["producer_function"].endswith("engine.compute_step")
        assert result.next_state["step"] == 1


def test_invalid_command_schema_and_hidden_selected_action_are_rejected():
    state = initial_state()
    meta = make_run_metadata("schema", 1)
    command = make_command(
        sequence=1, cue="resource", toggles=DEFAULT_TOGGLES, prev_command_hash=None
    )
    command["selected_action"] = "forage"
    with pytest.raises(EngineInvariantError, match="schema mismatch"):
        compute_step(state, command, meta)
