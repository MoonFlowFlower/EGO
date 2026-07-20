from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    EngineInvariantError,
    canonical_hash,
    compute_code_path_hash,
    compute_code_path_manifest,
    compute_step,
    compute_trace_hash,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.microworld import policy_observation
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


SCRIPT_PATH = REPO_ROOT / "scripts" / "run_ego_life_playground_v0.py"


def _step(
    state: dict | None = None,
    *,
    run_id: str = "card-a",
    seed: int = 17,
    trigger_source: str = "headless_acceptance",
    interventions: dict[str, str] | None = None,
    injected_event: str | None = None,
):
    before = deepcopy(state) if state is not None else initial_state(run_id=run_id)
    meta = make_run_metadata(run_id, seed)
    command = make_command(
        sequence=int(before["clock"]["global_tick"]) + 1,
        trigger_source=trigger_source,
        interventions=DEFAULT_INTERVENTIONS if interventions is None else interventions,
        prev_command_hash=before["last_command_hash"],
        injected_event=injected_event,
    )
    return before, meta, command, compute_step(before, command, meta)


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )


def test_card_a_command_v5_and_compute_step_are_deterministic_replay_inputs_only():
    state, meta, command, result = _step(run_id="deterministic")
    replayed = compute_step(deepcopy(state), deepcopy(command), deepcopy(meta))

    assert result.trace["schema_version"] == "ego.life_playground.trace.v8"
    assert command["schema_version"] == "ego.life_playground.command.v6"
    assert set(command) == {
        "schema_version",
        "sequence",
        "injected_event",
        "trigger_source",
        "interventions",
        "prev_command_hash",
        "command_hash",
    }
    assert result.next_state == replayed.next_state
    assert result.trace == replayed.trace
    assert result.trace["selected_action"] in {"turn_left", "turn_right", "move_forward", "interact", "rest"}
    assert "cue" not in command
    assert "selected_action" not in command
    assert "world_seed" not in command
    assert "path" not in command
    assert "legal_mask" not in command


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda command: command.update({"selected_action": "rest"}), "schema mismatch"),
        (lambda command: command.update({"cue": "resource"}), "schema mismatch"),
        (
            lambda command: command["interventions"].update({"provenance_shuffle_seed": 17}),
            "intervention enum values must be strings",
        ),
        (
            lambda command: command["interventions"].update(
                {"memory_mode": "off", "provenance_mode": "shuffle_projection"}
            ),
            "invalid intervention combination",
        ),
    ],
)
def test_card_a_command_schema_and_tamper_fail_closed(mutator, match):
    state = initial_state(run_id="tamper-command")
    meta = make_run_metadata("tamper-command", 17)
    command = make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )

    mutator(command)
    if "command_hash" in command:
        command["command_hash"] = canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        )

    with pytest.raises(EngineInvariantError, match=match):
        compute_step(state, command, meta)


def test_card_a_trace_provenance_and_hash_chain_are_computed():
    _state, _meta, command, result = _step(run_id="trace-provenance")
    trace = result.trace

    assert trace["producer_function"] == "ego_life_playground_v0.engine.compute_step"
    assert trace["input_artifacts"] == [
        "run:trace-provenance",
        f"command:{command['command_hash']}",
    ]
    assert trace["aggregation_rule"] == "single_reducer_command_transition_action_or_respawn"
    assert trace["run_id"] == "trace-provenance"
    assert trace["seed"] == 17
    assert trace["episode_id"] == result.next_state["clock"]["episode_id"]
    assert trace["command_hash"] == command["command_hash"]
    assert len(trace["state_after_hash"]) == 64
    assert trace["state_after_hash"] != trace["state_before_hash"]
    assert trace["trace_hash"] == compute_trace_hash(trace)
    assert result.next_state["last_command_hash"] == command["command_hash"]
    assert result.next_state["last_trace_hash"] == trace["trace_hash"]


def test_card_a_atomic_command_trace_commit_and_forced_second_insert_rollback(tmp_path: Path):
    with SQLiteEventStore(tmp_path / "atomic.sqlite3") as store:
        controller = PlaygroundController(store, run_id="atomic-run", seed=17)
        before = json.dumps(controller.state, sort_keys=True)
        before_status = controller.recovery_status

        first = controller.dispatch(trigger_source="ui_step_button")
        assert first.receipt.committed is True
        assert store.row_counts(controller.run_id) == (1, 1)

        callbacks: list[tuple[dict, dict]] = []
        controller.on_committed = lambda state, trace: callbacks.append((state, trace))
        store.connection.execute(
            "CREATE TRIGGER fail_trace_insert BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced trace failure'); END"
        )
        snapshot = json.dumps(controller.state, sort_keys=True)
        status = controller.recovery_status

        failed = controller.dispatch(trigger_source="ui_step_button")

        assert failed.receipt.committed is False
        assert "forced trace failure" in (failed.receipt.error or "")
        assert store.row_counts(controller.run_id) == (1, 1)
        assert json.dumps(controller.state, sort_keys=True) == snapshot
        assert controller.recovery_status == status
        assert callbacks == []
        assert json.dumps(initial_state(run_id="unused"), sort_keys=True) != before
        assert before_status == "new run"


def test_card_a_recovery_recomputes_from_serialized_initial_state_and_commands(tmp_path: Path):
    with SQLiteEventStore(tmp_path / "recover.sqlite3") as store:
        controller = PlaygroundController(store, run_id="recover-run", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        assert controller.dispatch(
            trigger_source="terminal_event", injected_event="resource_appears"
        ).receipt.committed is True

        recovered = store.recover_run(controller.run_id)
        command_rows = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (controller.run_id,),
        ).fetchall()
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?",
            (controller.run_id,),
        ).fetchone()
        state = json.loads(row["initial_state_json"])
        meta = recovered.run_meta
        recomputed_hashes = []
        for command_row in command_rows:
            command = json.loads(command_row["command_json"])
            step = compute_step(state, command, meta)
            recomputed_hashes.append(step.trace["trace_hash"])
            state = step.next_state

        assert recovered.recovered is True
        assert recovered.command_count == 2
        assert [trace["trace_hash"] for trace in recovered.traces] == recomputed_hashes
        assert recovered.state == state


def test_card_a_recovery_rejects_trace_tamper_even_after_rehash_and_command_tamper(tmp_path: Path):
    with SQLiteEventStore(tmp_path / "tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="tamper-run", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True

        trace_row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        ).fetchone()
        tampered_trace = json.loads(trace_row["trace_json"])
        tampered_trace["selected_action"] = (
            "rest" if tampered_trace["selected_action"] != "rest" else "turn_left"
        )
        tampered_trace["trace_hash"] = compute_trace_hash(tampered_trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
            (
                json.dumps(tampered_trace, sort_keys=True, separators=(",", ":")),
                tampered_trace["trace_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="stored trace differs"):
            store.recover_run(controller.run_id)

    with SQLiteEventStore(tmp_path / "command-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="command-tamper", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        command_row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        ).fetchone()
        tampered_command = json.loads(command_row["command_json"])
        tampered_command["trigger_source"] = "tampered"
        tampered_command["command_hash"] = "0" * 64
        store.connection.execute(
            "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = 1",
            (
                json.dumps(tampered_command, sort_keys=True, separators=(",", ":")),
                tampered_command["command_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="command recomputation failed"):
            store.recover_run(controller.run_id)


def test_card_a_recovery_rejects_state_world_tamper_and_missing_trace_parity(tmp_path: Path):
    with SQLiteEventStore(tmp_path / "state-world.sqlite3") as store:
        controller = PlaygroundController(store, run_id="state-world", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?",
            (controller.run_id,),
        ).fetchone()
        initial = json.loads(row["initial_state_json"])

        state_tamper = deepcopy(initial)
        state_tamper["organism"]["energy"] = 1.5
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (
                json.dumps(state_tamper, sort_keys=True, separators=(",", ":")),
                canonical_hash(state_tamper),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="organism energy"):
            store.recover_run(controller.run_id)

    with SQLiteEventStore(tmp_path / "world-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="world-tamper", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?",
            (controller.run_id,),
        ).fetchone()
        initial = json.loads(row["initial_state_json"])
        world_tamper = deepcopy(initial)
        world_tamper["world"]["objects_by_cause"]["resource"]["position"] = [999, 999]
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (
                json.dumps(world_tamper, sort_keys=True, separators=(",", ":")),
                canonical_hash(world_tamper),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="object position must be a walkable"):
            store.recover_run(controller.run_id)

    with SQLiteEventStore(tmp_path / "parity.sqlite3") as store:
        controller = PlaygroundController(store, run_id="parity-run", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        store.connection.execute(
            "DELETE FROM traces WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        )
        with pytest.raises(RecoveryError, match="row parity mismatch"):
            store.recover_run(controller.run_id)


def test_card_a_code_path_drift_and_source_bytes_fail_closed(tmp_path: Path):
    manifest = compute_code_path_manifest()
    assert manifest["schema_version"] == "ego.life_playground.code_path.v5"
    assert {entry["path"] for entry in manifest["files"]} == {
        "claims.py",
        "engine.py",
        "microworld.py",
        "survival_learning.py",
        "store.py",
    }
    assert all(len(entry["sha256"]) == 64 for entry in manifest["files"])

    with SQLiteEventStore(tmp_path / "drift.sqlite3") as store:
        controller = PlaygroundController(store, run_id="drift-run", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        store.connection.execute(
            "UPDATE runs SET code_path_hash = ? WHERE run_id = ?",
            ("old-code-hash", controller.run_id),
        )
        with pytest.raises(RecoveryError, match="code-path drift"):
            store.recover_run(controller.run_id)

    meta = make_run_metadata("drift-meta", 17)
    meta["code_path_hash"] = "0" * 64
    with pytest.raises(EngineInvariantError, match="code-path hash"):
        compute_step(
            initial_state(run_id="drift-meta"),
            make_command(
                sequence=1,
                trigger_source="headless_acceptance",
                interventions=DEFAULT_INTERVENTIONS,
                prev_command_hash=None,
            ),
            meta,
        )


def test_card_a_export_requires_clean_recovery_and_tamper_creates_no_output(tmp_path: Path):
    export_path = tmp_path / "trace.jsonl"
    with SQLiteEventStore(tmp_path / "export.sqlite3") as store:
        controller = PlaygroundController(store, run_id="export-run", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True

        output = controller.export(export_path)
        records = output.read_text(encoding="utf-8").splitlines()
        header = json.loads(records[0])

        assert output == export_path
        assert header["producer_function"] == "ego_life_playground_v0.store.SQLiteEventStore.export_run"
        assert header["aggregation_rule"] == "ordered_recomputed_trace_export"
        assert header["command_count"] == 1
        assert len(records) == 2

    failed_output = tmp_path / "tampered.jsonl"
    with SQLiteEventStore(tmp_path / "export-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="export-tamper", seed=17)
        assert controller.dispatch(trigger_source="terminal_step").receipt.committed is True
        trace_row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        ).fetchone()
        tampered_trace = json.loads(trace_row["trace_json"])
        tampered_trace["selected_action"] = "rest"
        tampered_trace["trace_hash"] = compute_trace_hash(tampered_trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
            (
                json.dumps(tampered_trace, sort_keys=True, separators=(",", ":")),
                tampered_trace["trace_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError):
            controller.export(failed_output)
        assert not failed_output.exists()


def test_card_a_fresh_restart_and_fresh_subprocess_runs_match_hashes(tmp_path: Path):
    db_path = tmp_path / "restart.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="restart-run", seed=53, world_seed=30)
        assert controller.dispatch(trigger_source="headless_acceptance").receipt.committed is True
        before = controller.last_trace["trace_hash"]
        before_state = canonical_hash(controller.state)

    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run("restart-run")
        assert recovered.traces[-1]["trace_hash"] == before
        assert canonical_hash(recovered.state) == before_state

    run_a = _run_script("--quick-check", "--db", str(tmp_path / "subprocess-a.sqlite3"), "--run-id", "same", "--seed", "53", "--world-seed", "30")
    run_b = _run_script("--quick-check", "--db", str(tmp_path / "subprocess-b.sqlite3"), "--run-id", "same", "--seed", "53", "--world-seed", "30")
    payload_a = json.loads(run_a.stdout.strip())
    payload_b = json.loads(run_b.stdout.strip())
    assert run_a.returncode == 0
    assert run_b.returncode == 0
    assert payload_a["public_state_hash"] == payload_b["public_state_hash"]
    assert payload_a["observation_hash"] == payload_b["observation_hash"]
    assert payload_a["selected_action"] == payload_b["selected_action"]


def test_card_a_run_selection_explicit_load_reset_and_layout_mismatch_fail_closed(tmp_path: Path):
    with SQLiteEventStore(tmp_path / "selection.sqlite3") as store:
        compatible = PlaygroundController(
            store, run_id="compatible-run", seed=17, layout_id="p0_cross_v1"
        )
        assert compatible.dispatch(trigger_source="terminal_step").receipt.committed is True

        incompatible = PlaygroundController(
            store, run_id="incompatible-run", seed=17, layout_id="p2_vertical_v1"
        )
        assert incompatible.dispatch(trigger_source="terminal_step").receipt.committed is True
        store.connection.execute(
            "UPDATE runs SET code_path_hash = ? WHERE run_id = ?",
            ("stale-code-hash", "incompatible-run"),
        )

        default_selected = PlaygroundController(store, seed=99)
        assert default_selected.run_id == "compatible-run"

        with pytest.raises(RecoveryError, match="code-path drift"):
            default_selected.load_run("incompatible-run")

        with pytest.raises(EngineInvariantError, match="does not match requested"):
            PlaygroundController(
                store,
                run_id="compatible-run",
                seed=17,
                layout_id="p2_vertical_v1",
            )

        old_run = default_selected.run_id
        old_hash = default_selected.recovery.frames[-1].state["world"]["trial"]["token_mapping"]
        reset = default_selected.reset_run("fresh-run")
        assert reset.run_id == "fresh-run"
        assert default_selected.run_id == "fresh-run"
        assert store.run_exists(old_run) is True
        assert store.recover_run(old_run).state["world"]["trial"]["token_mapping"] == old_hash
        assert store.recover_run("fresh-run").command_count == 0


def test_card_a_real_headless_launcher_and_tk_forwarding_path():
    spec = importlib.util.spec_from_file_location("ego_launcher_module", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    called: dict[str, object] = {}

    def fake_run_app(db_path, **kwargs):
        called["db_path"] = db_path
        called.update(kwargs)

    module.run_app = fake_run_app
    exit_code = module.main(["--db", "demo.sqlite3", "--seed", "19", "--world-seed", "31", "--layout", "p2_vertical_v1", "--run-id", "demo"])

    assert exit_code == 0
    assert Path(called["db_path"]).name == "demo.sqlite3"
    assert called["seed"] == 19
    assert called["world_seed"] == 31
    assert called["layout_id"] == "p2_vertical_v1"
    assert called["run_id"] == "demo"


def test_card_a_ast_guard_keeps_single_controller_reducer_store_replay_path():
    controller_source = (REPO_ROOT / "labs" / "ego_life_playground_v0" / "controller.py").read_text(
        encoding="utf-8"
    )
    terminal_source = (REPO_ROOT / "labs" / "ego_life_playground_v0" / "terminal.py").read_text(
        encoding="utf-8"
    )
    visual_source = (REPO_ROOT / "labs" / "ego_life_playground_v0" / "visual_console.py").read_text(
        encoding="utf-8"
    )

    assert controller_source.count("compute_step(") == 1
    assert controller_source.count("append_step(") == 1
    assert controller_source.count("recover_run(") >= 3
    assert "compute_step(" not in terminal_source
    assert "append_step(" not in terminal_source
    assert "create_run(" not in terminal_source
    assert "compute_step(" not in visual_source
    assert "append_step(" not in visual_source
    assert "create_run(" not in visual_source

    tree = ast.parse(visual_source)
    forbidden = {"compute_step", "append_step", "create_run", "transition_world"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else None
        assert target not in forbidden
