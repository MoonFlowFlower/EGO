from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.app import PlaygroundController, TerminalPlayground
from labs.ego_life_playground_v0.engine import compute_code_path_hash
from labs.ego_life_playground_v0.microworld import (
    ALLOWED_WORLD_EVENTS,
    make_public_frame,
)
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.store import RecoveryError
from scripts import codex_session_guard


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run_ego_life_playground_v0.py"


def test_p0_public_microworld_frame_is_readable_and_contains_no_hidden_or_oracle_fields(tmp_path):
    with SQLiteEventStore(tmp_path / "p0.sqlite3") as store:
        controller = PlaygroundController(store, run_id="p0-public", seed=17)
        terminal = TerminalPlayground(controller)
        stepped = terminal.execute("inject resource_appears")

        assert stepped["status"] == "committed"
        snapshot = stepped["snapshot"]
        world = snapshot["world"]
        assert world["product_clock"]["global_tick"] == 1
        assert world["observation"]["event"] == "resource_appears"
        assert world["agent"]["position"] in {"home", "fork", "site_a", "site_b"}
        assert len(world["map_rows"]) == 5
        assert "@" in world["ascii_map"]
        assert world["objects"]
        assert snapshot["internal_state"] == controller.state["organism"]
        assert snapshot["current_goal"] == controller.state["current_goal"]
        assert len(snapshot["candidates"]) >= 2
        assert snapshot["selected_action"] == controller.last_trace["selected_action"]
        assert snapshot["prediction"] == controller.last_trace["prediction"]
        assert snapshot["prediction_error"] == controller.last_trace["prediction_error"]
        assert snapshot["memory"]["write"] == controller.last_trace["memory_update"]
        assert snapshot["state_transition"]["after_hash"] == controller.last_trace["state_after_hash"]
        encoded = json.dumps(world, sort_keys=True).lower()
        assert "hidden_regime" not in encoded
        assert "oracle" not in encoded
        assert "correct_action" not in encoded


def test_p0_terminal_commands_cover_step_run_pause_inspect_inject_save_load_reset_and_replay(tmp_path):
    db_path = tmp_path / "commands.sqlite3"
    export_path = tmp_path / "saved.trace.jsonl"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="p0-command-run", seed=23)
        terminal = TerminalPlayground(controller)

        assert terminal.execute("pause") == {
            "command": "pause",
            "status": "paused",
            "global_tick": 0,
        }
        assert terminal.execute("step")["snapshot"]["world"]["product_clock"]["global_tick"] == 1
        assert terminal.execute("inject threat_nearby")["snapshot"]["world"]["observation"]["event"] == "threat_nearby"
        ran = terminal.execute("run 7")
        assert ran["status"] == "committed"
        assert ran["ticks_committed"] == 7
        assert ran["snapshot"]["world"]["product_clock"]["global_tick"] == 9
        assert ran["snapshot"]["world"]["product_clock"]["episode_index"] == 1
        inspected = terminal.execute("inspect")
        assert inspected["status"] == "ok"
        assert inspected["snapshot"]["timeline"][-1]["sequence"] == 9
        saved = terminal.execute(f"save {export_path}")
        assert saved["status"] == "saved"
        assert export_path.exists()

        reset = terminal.execute("reset p0-second-run")
        assert reset["status"] == "reset"
        assert controller.run_id == "p0-second-run"
        assert controller.state["clock"]["global_tick"] == 0
        loaded = terminal.execute("load p0-command-run")
        assert loaded["status"] == "loaded"
        assert controller.state["clock"]["global_tick"] == 9
        replayed = terminal.execute("replay")
        assert replayed["status"] == "recomputed"
        assert replayed["frame_count"] == 10
        assert replayed["timeline"][-1]["sequence"] == 9


def test_p0_fresh_process_terminal_load_recomputes_same_durable_timeline(tmp_path):
    db_path = tmp_path / "fresh.sqlite3"
    first = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--db",
            str(db_path),
            "--terminal",
            "--run-id",
            "fresh-process-run",
            "--command",
            "run 10",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--db",
            str(db_path),
            "--terminal",
            "--run-id",
            "fresh-process-run",
            "--command",
            "replay",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    first_payload = json.loads(first.stdout.strip().splitlines()[-1])
    second_payload = json.loads(second.stdout.strip().splitlines()[-1])
    assert first_payload["snapshot"]["world"]["product_clock"]["global_tick"] == 10
    assert second_payload["status"] == "recomputed"
    assert second_payload["frame_count"] == 11
    assert second_payload["timeline"][-1]["trace_hash"] == first_payload["snapshot"]["trace_hash"]


def test_p0_event_set_and_causal_code_hash_are_explicit():
    assert ALLOWED_WORLD_EVENTS == (
        "resource_appears",
        "social_signal",
        "novel_object",
        "threat_nearby",
        "quiet_interval",
    )
    assert make_public_frame.__module__.endswith("microworld")
    assert len(compute_code_path_hash()) == 64


def test_p0_scope_passes_real_committed_phase_c_mutation_admission():
    scope_path = (
        REPO_ROOT
        / "docs/codex/tasks/EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A-MUTATION_SCOPE.yaml"
    )
    scope = yaml.safe_load(scope_path.read_text(encoding="utf-8"))
    assert scope["task_kind"] == "bounded_v2_microworld_implementation"
    assert scope["authority_commit"] == "a34ff6630a6456b9e333199b10ee866d30e1c0cd"
    assert (
        scope["authorized_implementation_targets"]
        == codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS
    )
    admission = codex_session_guard.validate_phase_c_v2_mutation_admission(
        scope,
        repo=REPO_ROOT,
        itl_repo=Path(r"D:\Project\AIProject\MyProject\intelligence-theory-lab"),
    )
    assert admission["status"] == "pass", admission
    assert admission["errors"] == []


def test_p0_world_event_observation_legality_and_transition_are_canonical_reducer_state(tmp_path):
    with SQLiteEventStore(tmp_path / "causal-world.sqlite3") as store:
        controller = PlaygroundController(store, run_id="causal-world", seed=31)
        initial_world = controller.state["world"]
        assert initial_world["agent"]["position"] == "home"
        assert initial_world["public_observation"]["event"] == "quiet_interval"

        terminal = TerminalPlayground(controller)
        result = terminal.execute("inject resource_appears")
        assert result["status"] == "committed"
        trace = controller.last_trace
        assert trace["command"]["world_event"] == "resource_appears"
        assert trace["world_event"] == "resource_appears"
        assert trace["observation"] == trace["world_observation"]
        assert trace["observation_hash"] == engine.canonical_hash(trace["observation"])
        assert trace["legal_actions"] == list(engine.ACTIONS)
        assert trace["gated_actions"] == []
        assert all(candidate["legal"] is True for candidate in trace["candidates"])
        assert all(candidate["gate_reasons"] == [] for candidate in trace["candidates"])
        assert trace["world_before_hash"] == microworld.world_hash(initial_world)
        assert trace["world_after_hash"] == microworld.world_hash(controller.state["world"])
        assert controller.state["world"]["public_observation"]["event"] == "resource_appears"
        assert result["snapshot"]["decision_observation"] == trace["observation"]
        assert result["snapshot"]["decision_observation_hash"] == trace["observation_hash"]
        assert result["snapshot"]["observation_hash"] == microworld.observation_hash(
            controller.state["world"]["public_observation"]
        )

        reopened = store.recover_run("causal-world")
        assert reopened.state["world"] == controller.state["world"]
        assert reopened.traces[-1]["world_after_hash"] == trace["world_after_hash"]


def test_p0_renderer_uses_recovered_world_state_not_selected_action_posthoc(tmp_path):
    with SQLiteEventStore(tmp_path / "renderer-state.sqlite3") as store:
        controller = PlaygroundController(store, run_id="renderer-state", seed=17)
        TerminalPlayground(controller).execute("inject social_signal")
        recovered_state = controller.recovery.state
        forged_trace = dict(controller.last_trace)
        forged_trace["selected_action"] = "withdraw"
        canonical_frame = make_public_frame(recovered_state, controller.last_trace)
        forged_frame = make_public_frame(recovered_state, forged_trace)
        assert forged_frame == canonical_frame
        assert forged_frame["agent"] == recovered_state["world"]["agent"]
        assert forged_frame["objects"] == recovered_state["world"]["objects"]
        assert forged_frame["observation"] == recovered_state["world"]["public_observation"]


def test_p0_typed_world_event_rehash_tamper_fails_recomputing_replay(tmp_path):
    with SQLiteEventStore(tmp_path / "event-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="event-tamper", seed=17)
        TerminalPlayground(controller).execute("inject resource_appears")
        row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        ).fetchone()
        command = json.loads(row["command_json"])
        command["world_event"] = "threat_nearby"
        command["command_hash"] = engine.canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        )
        store.connection.execute(
            "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = 1",
            (
                engine.canonical_json(command),
                command["command_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="command recomputation failed"):
            store.recover_run(controller.run_id)


def test_p0_rehashed_persisted_world_state_tamper_fails_recomputing_replay(tmp_path):
    with SQLiteEventStore(tmp_path / "world-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="world-tamper", seed=17)
        TerminalPlayground(controller).execute("step")
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?", (controller.run_id,)
        ).fetchone()
        initial = json.loads(row["initial_state_json"])
        initial["world"]["agent"]["position"] = "site_b"
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (
                engine.canonical_json(initial),
                engine.canonical_hash(initial),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="command recomputation failed"):
            store.recover_run(controller.run_id)


def test_p0_default_launch_skips_incompatible_latest_but_explicit_load_fails_closed(tmp_path):
    db_path = tmp_path / "compatibility.sqlite3"
    with SQLiteEventStore(db_path) as store:
        compatible = PlaygroundController(store, run_id="compatible", seed=17)
        TerminalPlayground(compatible).execute("step")
        incompatible_meta = engine.make_run_metadata("incompatible-latest", 17)
        incompatible_meta["code_path_hash"] = "0" * 64
        incompatible_state = engine.initial_state(run_id="incompatible-latest")
        store.connection.execute(
            "INSERT INTO runs(run_id, run_meta_json, initial_state_json, initial_state_hash, code_path_hash) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                "incompatible-latest",
                engine.canonical_json(incompatible_meta),
                engine.canonical_json(incompatible_state),
                engine.canonical_hash(incompatible_state),
                "0" * 64,
            ),
        )
        assert store.latest_run_id() == "incompatible-latest"

        default = PlaygroundController(store, seed=999)
        assert default.run_id == "compatible"
        before_hash = engine.state_hash(default.state)
        before_frames = len(default.recovery.frames)
        explicit = TerminalPlayground(default).execute("load incompatible-latest")
        assert explicit["status"] == "error"
        assert "code-path drift" in explicit["error"]
        assert default.run_id == "compatible"
        assert engine.state_hash(default.state) == before_hash
        assert len(default.recovery.frames) == before_frames


def test_p0_default_launch_creates_new_run_when_no_compatible_run_exists(tmp_path):
    db_path = tmp_path / "no-compatible.sqlite3"
    with SQLiteEventStore(db_path) as store:
        meta = engine.make_run_metadata("old-only", 17)
        meta["code_path_hash"] = "f" * 64
        state = engine.initial_state(run_id="old-only")
        store.connection.execute(
            "INSERT INTO runs(run_id, run_meta_json, initial_state_json, initial_state_hash, code_path_hash) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                "old-only",
                engine.canonical_json(meta),
                engine.canonical_json(state),
                engine.canonical_hash(state),
                "f" * 64,
            ),
        )
        controller = PlaygroundController(store, seed=41)
        assert controller.run_id != "old-only"
        assert controller.recovery_status == "new run"
        assert controller.run_meta["code_path_hash"] == compute_code_path_hash()


def test_p0_save_oserror_is_structured_and_preserves_state_and_history(tmp_path):
    with SQLiteEventStore(tmp_path / "save-error.sqlite3") as store:
        controller = PlaygroundController(store, run_id="save-error", seed=17)
        terminal = TerminalPlayground(controller)
        terminal.execute("step")
        state_before = engine.canonical_json(controller.state)
        traces_before = engine.canonical_json(controller.recovery.traces)
        counts_before = store.row_counts(controller.run_id)

        result = terminal.execute(f"save {tmp_path}")
        assert result["status"] == "error"
        assert "OSError" in result["error"] or "PermissionError" in result["error"]
        assert engine.canonical_json(controller.state) == state_before
        assert engine.canonical_json(controller.recovery.traces) == traces_before
        assert store.row_counts(controller.run_id) == counts_before


def test_p0_code_path_manifest_is_exact_and_each_causal_file_is_hash_sensitive(monkeypatch):
    manifest = engine.compute_code_path_manifest()
    assert manifest["schema_version"] == "ego.life_playground.code_path.v2"
    assert [item["path"] for item in manifest["files"]] == [
        "engine.py",
        "microworld.py",
        "store.py",
    ]
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])
    baseline = compute_code_path_hash()
    original_read_bytes = Path.read_bytes
    for target in ("engine.py", "microworld.py", "store.py"):
        with monkeypatch.context() as scoped:
            def read_with_drift(path: Path, *, _target: str = target) -> bytes:
                payload = original_read_bytes(path)
                return payload + b"\n# causal positive control\n" if path.name == _target else payload

            scoped.setattr(Path, "read_bytes", read_with_drift)
            assert compute_code_path_hash() != baseline
