from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path

import pytest

from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    EngineInvariantError,
    canonical_json,
    compute_step,
    initial_state,
    make_run_metadata,
)
from labs.ego_life_playground_v0.store import SQLiteEventStore
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dispatch_adopts_atomic_commit_without_full_history_replay(
    tmp_path, monkeypatch
) -> None:
    with SQLiteEventStore(tmp_path / "incremental.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="runtime-incremental",
            seed=17,
            world_seed=23,
        )
        full_replay = store.recover_run
        calls = 0

        def counted(run_id: str):
            nonlocal calls
            calls += 1
            return full_replay(run_id)

        monkeypatch.setattr(store, "recover_run", counted)
        result = controller.dispatch(
            deepcopy(DEFAULT_INTERVENTIONS), trigger_source="ui_run_button"
        )

        assert result.receipt.committed is True
        assert result.receipt.row_readback_verified is True
        assert calls == 0
        assert controller.recovery.verification_mode == "incremental_committed"
        assert controller.recovery.last_committed_sequence == 1
        assert controller.recovery.last_full_replay_sequence == 0
        assert controller.recovery.recovered is False

        independently_recovered = full_replay(controller.run_id)
        assert canonical_json(controller.state) == canonical_json(
            independently_recovered.state
        )
        assert canonical_json(controller.last_trace) == canonical_json(
            independently_recovered.traces[-1]
        )


def test_explicit_recover_marks_full_replay_boundary(tmp_path) -> None:
    with SQLiteEventStore(tmp_path / "explicit-recover.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="runtime-explicit-recover",
            seed=17,
            world_seed=23,
        )
        controller.dispatch(
            deepcopy(DEFAULT_INTERVENTIONS), trigger_source="ui_run_button"
        )
        recovered = controller.recover()

        assert recovered.verification_mode == "full_replay"
        assert recovered.last_committed_sequence == 1
        assert recovered.last_full_replay_sequence == 1
        assert recovered.recovered is True
        assert controller.recovery_status == "fully replayed 1 command(s)"


def test_compact_trace_does_not_copy_complete_model_or_memory(tmp_path) -> None:
    with SQLiteEventStore(tmp_path / "compact.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="runtime-compact-trace",
            seed=17,
            world_seed=23,
        )
        for _ in range(8):
            result = controller.dispatch(
                deepcopy(DEFAULT_INTERVENTIONS), trigger_source="ui_run_button"
            )
            assert result.receipt.committed is True

        trace = controller.last_trace
        assert trace is not None
        projection = trace["policy_projection"]
        assert "model" not in projection
        assert set(projection["model_access"]) == {
            "component_hash",
            "context_key",
            "entries_by_action",
            "transition_counts",
        }
        provenance = trace["provenance_projection"]
        assert "memory" not in provenance
        assert "source_memory" not in provenance
        assert "component_hash" in provenance
        assert len(canonical_json(trace).encode("utf-8")) <= 65_536


def test_controller_dispatch_source_has_no_recover_run_call() -> None:
    source = inspect.getsource(PlaygroundController.dispatch)
    assert ".recover_run(" not in source
    assert "compute_step(" in source
    assert "append_step(" in source


def test_phase_a_command_fixture_fails_closed_after_phase_b_schema_bump() -> None:
    baseline = json.loads(
        (
            REPO_ROOT
            / "artifacts"
            / "EGO-V2-P0-RUNTIME-SCALING-001A"
            / "semantic_baseline.json"
        ).read_text(encoding="utf-8")
    )
    state = initial_state(
        run_id=baseline["run_id"], seed=int(baseline["world_seed"])
    )
    run_meta = make_run_metadata(baseline["run_id"], int(baseline["seed"]))

    with pytest.raises(EngineInvariantError, match="command schema_version"):
        compute_step(state, baseline["records"][0]["command"], run_meta)
