from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import PlaygroundController, public_state_projection
from labs.ego_life_playground_v0.engine import DEFAULT_INTERVENTIONS, compute_step as engine_compute_step
from labs.ego_life_playground_v0.microworld import policy_observation
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.terminal import TerminalPlayground


def test_controller_dispatch_uses_one_cue_free_compute_commit_and_recovery_path(
    tmp_path, monkeypatch
):
    calls = {"make_command": [], "compute_step": 0, "recover_run": 0}

    from labs.ego_life_playground_v0 import controller as controller_module

    real_make_command = controller_module.make_command

    def spy_make_command(**kwargs):
        calls["make_command"].append(kwargs)
        return real_make_command(**kwargs)

    def spy_compute_step(state, command, run_meta):
        calls["compute_step"] += 1
        return engine_compute_step(state, command, run_meta)

    db_path = tmp_path / "controller.sqlite3"
    with SQLiteEventStore(db_path) as store:
        real_recover_run = store.recover_run

        def spy_recover_run(run_id):
            calls["recover_run"] += 1
            return real_recover_run(run_id)

        monkeypatch.setattr(controller_module, "make_command", spy_make_command)
        monkeypatch.setattr(controller_module, "compute_step", spy_compute_step)
        monkeypatch.setattr(store, "recover_run", spy_recover_run)
        controller = PlaygroundController(store, run_id="controller-path", seed=17)
        calls["recover_run"] = 0

        result = controller.dispatch(trigger_source="ui_step_button")

        assert result.receipt.committed is True
        assert store.row_counts(controller.run_id) == (1, 1)
        assert calls == {
            "make_command": [calls["make_command"][0]],
            "compute_step": 1,
            "recover_run": 0,
        }
        assert controller.recovery.verification_mode == "incremental_committed"
        assert result.receipt.row_readback_verified is True
        assert calls["make_command"][0] == {
            "sequence": 1,
            "trigger_source": "ui_step_button",
            "interventions": DEFAULT_INTERVENTIONS,
            "prev_command_hash": None,
            "injected_event": None,
        }
        assert controller.last_trace["command"]["schema_version"] == "ego.life_playground.command.v7"
        assert "cue" not in controller.last_trace["command"]
        assert controller.last_trace["command"]["interventions"] == DEFAULT_INTERVENTIONS


def test_controller_injected_event_stays_trace_only_and_out_of_policy_projection(tmp_path):
    db_path = tmp_path / "injection.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="inject-trace", seed=17)
        result = controller.dispatch(injected_event="resource_appears")

        assert result.receipt.committed is True
        assert controller.last_trace["command"]["injected_event"] == "resource_appears"
        assert controller.last_trace["observation"] == policy_observation(
            controller.state["world"], occlusion=True
        )
        assert (
            controller.last_trace["policy_projection"]["observation"]
            != controller.last_trace["observation"]
        )
        encoded_projection = json.dumps(controller.last_trace["policy_projection"], sort_keys=True)
        assert "resource_appears" not in encoded_projection
        public_projection = public_state_projection(controller.state)
        assert public_projection["world"]["world"]["layout"] == controller.state["world"]["layout"]
        assert public_projection["world"]["world"]["agent"] == controller.state["world"]["agent"]
        assert "visible_objects" in public_projection["world"]["world"]
        assert public_projection["world"] != controller.last_trace["policy_projection"]


def test_failed_atomic_commit_leaves_controller_state_and_callbacks_unchanged(tmp_path):
    callbacks = []
    recovered = []
    db_path = tmp_path / "atomic.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id="atomic-invariant",
            seed=17,
            on_committed=lambda state, trace: callbacks.append((state, trace)),
            on_recovered=lambda payload: recovered.append(payload.command_count),
        )
        before_state = json.dumps(controller.state, sort_keys=True)
        before_status = controller.recovery_status
        store.connection.execute(
            "CREATE TRIGGER fail_trace_insert BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced trace failure'); END"
        )

        result = controller.dispatch()

        assert result.receipt.committed is False
        assert store.row_counts(controller.run_id) == (0, 0)
        assert json.dumps(controller.state, sort_keys=True) == before_state
        assert controller.last_trace is None
        assert controller.recovery_status == before_status
        assert callbacks == []
        assert recovered == []


def test_terminal_step_run_inject_replay_reset_load_and_export_follow_controller_contract(
    tmp_path,
):
    db_path = tmp_path / "terminal.sqlite3"
    export_path = tmp_path / "terminal.jsonl"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="terminal-run", seed=17)
        terminal = TerminalPlayground(controller)

        assert terminal.execute("step extra")["status"] == "error"

        stepped = terminal.execute("step")
        assert stepped["status"] == "committed"
        assert stepped["snapshot"]["timeline"][-1]["injected_event"] is None
        assert stepped["snapshot"]["timeline"][-1]["selected_action"] is not None
        assert "legal_actions" not in stepped["snapshot"]
        assert "gated_actions" not in stepped["snapshot"]
        assert "policy_non_memory_projection_hash" not in stepped["snapshot"]
        assert stepped["snapshot"]["world_transition"] is not None

        ran = terminal.execute("run 2")
        assert ran["status"] == "committed"
        assert ran["ticks_committed"] == 2
        assert ran["snapshot"]["timeline"][-1]["sequence"] == 3
        assert ran["snapshot"]["timeline"][-1]["injected_event"] is None

        injected = terminal.execute("inject resource_appears")
        assert injected["status"] == "committed"
        assert injected["event"] == "resource_appears"
        assert injected["snapshot"]["timeline"][-1]["injected_event"] == "resource_appears"

        saved = terminal.execute(f"save {export_path}")
        assert saved["status"] == "saved"
        assert export_path.exists()

        replayed = terminal.execute("replay")
        assert replayed["status"] == "recomputed"
        assert replayed["frame_count"] == 5

        reset = terminal.execute("reset reset-run")
        assert reset["status"] == "reset"
        assert reset["run_id"] == "reset-run"
        assert reset["frame_count"] == 1

        loaded = terminal.execute("load terminal-run")
        assert loaded["status"] == "loaded"
        assert loaded["run_id"] == "terminal-run"
        assert loaded["frame_count"] == 5


def test_launcher_quick_check_uses_cue_free_dispatch_and_reports_headless_fields(
    tmp_path, capsys
):
    launcher = REPO_ROOT / "scripts/run_ego_life_playground_v0.py"
    spec = importlib.util.spec_from_file_location("run_ego_life_playground_v0_controller_test", launcher)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.main(["--quick-check", "--db", str(tmp_path / "quick.sqlite3"), "--seed", "53"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert result == 0
    assert payload["command_schema_version"] == "ego.life_playground.command.v7"
    assert payload["selected_action"] is not None
    assert isinstance(payload["observation_hash"], str) and len(payload["observation_hash"]) == 64
    assert payload["recovered"] is True
    assert payload["frame_count"] == 2
    assert payload["science_weight"] == 0
    assert "cue" not in json.dumps(payload, sort_keys=True)


def test_controller_default_run_selection_skips_incompatible_latest_and_explicit_load_fails_closed(
    tmp_path,
):
    db_path = tmp_path / "compat.sqlite3"
    with SQLiteEventStore(db_path) as store:
        compatible = PlaygroundController(store, run_id="compatible-run", seed=17)
        assert compatible.dispatch().receipt.committed is True

        incompatible = PlaygroundController(store, run_id="incompatible-run", seed=17)
        assert incompatible.dispatch().receipt.committed is True
        store.connection.execute(
            "UPDATE runs SET code_path_hash = 'old-code-hash' WHERE run_id = ?",
            ("incompatible-run",),
        )

        default_selected = PlaygroundController(store, seed=99)
        assert default_selected.run_id == "compatible-run"

        terminal = TerminalPlayground(default_selected)
        loaded = terminal.execute("load incompatible-run")
        assert loaded["status"] == "error"
        assert "drift" in loaded["error"].lower()


def test_explicit_old_schema_run_fails_closed_on_load(tmp_path):
    db_path = tmp_path / "schema.sqlite3"
    with SQLiteEventStore(db_path) as store:
        current = PlaygroundController(store, run_id="current-run", seed=17)
        assert current.dispatch().receipt.committed is True

        stale = PlaygroundController(store, run_id="stale-run", seed=17)
        assert stale.dispatch().receipt.committed is True
        row = store.connection.execute(
            "SELECT run_meta_json FROM runs WHERE run_id = ?",
            ("stale-run",),
        ).fetchone()
        run_meta = json.loads(row["run_meta_json"])
        run_meta["schema_version"] = "ego.life_playground.run.v2"
        store.connection.execute(
            "UPDATE runs SET run_meta_json = ? WHERE run_id = ?",
            (json.dumps(run_meta, sort_keys=True, separators=(",", ":")), "stale-run"),
        )

        terminal = TerminalPlayground(current)
        loaded = terminal.execute("load stale-run")
        assert loaded["status"] == "error"
        assert "schema" in loaded["error"].lower()
