#!/usr/bin/env python3
"""Callable integration evidence for the default-off Chinese Tk visual console."""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.app import (
    DispatchResult,
    PlaygroundController,
    PlaygroundWindow,
    build_chinese_causal_view,
    recorded_waypoints,
    validate_scheduled_waypoints,
)
from labs.ego_life_playground_v0.engine import canonical_json, compute_code_path_hash
from labs.ego_life_playground_v0.store import CommitReceipt, SQLiteEventStore


TASK_ID = "EGO-V2-P0-VISUAL-CONSOLE-LIVE-001A"
RUN_ID = "ego-v2-visual-console-live-001"
RUN_SEED = 701
WORLD_SEED = 42
LAYOUT_ID = "p2_offset_v1"
CLAIM_CEILING = (
    "Local default-off visual console connected to the canonical controller, SQLite, "
    "recomputing recovery/replay, and recorded trace path, with Chinese display limited "
    "to recorded fields. This does not establish thought, emotion, learning success, "
    "memory causality, initiative, agency, subjectivity, consciousness, electronic life, "
    "product readiness, or user value."
)
REQUIRED_ARTIFACTS = {
    "result.json",
    "trace.jsonl",
    "baseline_comparison.json",
    "ablation_report.json",
    "replay_report.json",
    "failure_manifest.json",
    "live_ui_receipt.json",
    "claim_ceiling.txt",
}
FORBIDDEN_RENDERER_TOKENS = (
    "oracle_evidence_record",
    "private_dynamics",
    "hidden_regime",
    "correct_action",
)
APP_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "app.py"
CONTROLLER_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "controller.py"
TERMINAL_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "terminal.py"
VISUAL_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "visual_console.py"
ENGINE_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "engine.py"
STORE_PATH = REPO_ROOT / "labs" / "ego_life_playground_v0" / "store.py"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": _sha256(raw)}


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "engine_code_path_hash": compute_code_path_hash(),
                "view_module_sha256": {
                    str(path.relative_to(REPO_ROOT)): _file_record(path)["sha256"]
                    for path in (APP_PATH, CONTROLLER_PATH, TERMINAL_PATH, VISUAL_PATH)
                },
                "verifier_sha256": _file_record(Path(__file__))["sha256"],
            }
        )
    )


def _evidence(value: bool, *, producer_function: str, inputs: list[Any]) -> dict[str, Any]:
    return {
        "producer_function": producer_function,
        "input_artifacts": deepcopy(inputs),
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "world_seed": WORLD_SEED,
            "layout_id": LAYOUT_ID,
        },
        "aggregation_rule": "boolean result from the named callable computation path",
        "code_path_hash": _code_path_hash(),
        "value": bool(value),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _pump_tk_until(root: Any, predicate: Any, *, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise RuntimeError("Tk evidence condition timed out")
        root.update()
        time.sleep(0.006)


def scan_forbidden_tokens(path: str | Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    matches = [
        token for token in FORBIDDEN_RENDERER_TOKENS if token.encode("ascii") in raw
    ]
    return {
        "producer_function": "scan_forbidden_tokens",
        "path_sha256": _sha256(raw),
        "matches": matches,
    }


def _scan_second_engine_path(path: Path = VISUAL_PATH) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    window_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PlaygroundWindow"
    )
    forbidden_names = {
        "compute_step",
        "make_command",
        "initial_state",
        "canonical_action_path",
        "transition_world",
    }
    direct_forbidden = sorted(
        {
            node.func.id
            for node in ast.walk(window_class)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in forbidden_names
        }
    )
    dispatch_calls = []
    for node in ast.walk(window_class):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "dispatch"
        ):
            continue
        receiver = node.func.value
        receiver_text = ast.unparse(receiver)
        dispatch_calls.append(receiver_text)
    return {
        "producer_function": "_scan_second_engine_path",
        "direct_forbidden_calls": direct_forbidden,
        "dispatch_receivers": sorted(dispatch_calls),
        "pass": direct_forbidden == [] and dispatch_calls == ["self.controller"],
    }


def aggregate_visual_result(checks: Mapping[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    for name, record in checks.items():
        if not isinstance(record, Mapping) or type(record.get("value")) is not bool:
            raise ValueError(f"computed check record required: {name}")
        if record["value"] is not True:
            failed.append(str(name))
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def _fresh_process_recover(db_path: Path, run_id: str) -> dict[str, Any]:
    script = (
        "import json,sys;"
        "from labs.ego_life_playground_v0.store import SQLiteEventStore;"
        "s=SQLiteEventStore(sys.argv[1]);"
        "r=s.recover_run(sys.argv[2]);"
        "print(json.dumps({'run_id':r.run_id,'sequence':r.frames[-1].sequence,"
        "'command_count':r.command_count,'recovered':r.recovered,"
        "'trace_hash':r.traces[-1]['trace_hash'],'selected_action':r.traces[-1]['selected_action']}));"
        "s.close()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(db_path), run_id],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload: dict[str, Any] = {}
    if completed.returncode == 0:
        payload = json.loads(completed.stdout.strip())
    return {
        "producer_function": "_fresh_process_recover",
        "returncode": completed.returncode,
        "stdout_sha256": _sha256(completed.stdout.encode("utf-8")),
        "stderr_sha256": _sha256(completed.stderr.encode("utf-8")),
        **payload,
    }


def _capture_window(root: Any, output: Path) -> dict[str, Any]:
    from PIL import ImageGrab

    root.deiconify()
    root.lift()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    root.update_idletasks()
    root.update()
    time.sleep(0.08)
    root.update()
    x = int(root.winfo_rootx())
    y = int(root.winfo_rooty())
    width = int(root.winfo_width())
    height = int(root.winfo_height())
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    try:
        root.attributes("-topmost", False)
    except Exception:
        pass
    return {
        "producer_function": "_capture_window",
        "path": str(output),
        "sha256": _file_record(output)["sha256"],
        "bytes": output.stat().st_size,
        "width": image.width,
        "height": image.height,
    }


def _frozen_player_baseline(temp_root: Path) -> dict[str, Any]:
    db_path = temp_root / "frozen-player.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id="visual-frozen-player-baseline",
            seed=RUN_SEED,
            world_seed=WORLD_SEED,
            layout_id=LAYOUT_ID,
        )
        before = store.row_counts(controller.run_id)
        build_chinese_causal_view(controller.recovery.frames[-1])
        after = store.row_counts(controller.run_id)
        recovered = store.recover_run(controller.run_id)
    return {
        "producer_function": "_frozen_player_baseline",
        "committed_sequence_delta": after[0] - before[0],
        "fresh_recovered_sequence": recovered.frames[-1].sequence,
    }


def _run_no_op_dispatch_ablation(temp_root: Path) -> dict[str, Any]:
    db_path = temp_root / "no-op-dispatch.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id="visual-no-op-dispatch",
            seed=RUN_SEED,
            world_seed=WORLD_SEED,
            layout_id=LAYOUT_ID,
        )

        def no_op_dispatch(*_args: Any, **_kwargs: Any) -> DispatchResult:
            return DispatchResult(
                receipt=CommitReceipt(
                    committed=False,
                    run_id=controller.run_id,
                    sequence=1,
                    trace_hash=None,
                    error="no-op dispatch intervention",
                ),
                step=None,
            )

        controller.dispatch = no_op_dispatch  # type: ignore[method-assign]
        result = controller.dispatch("contact", {}, trigger_source="ui_step_button")
        counts = store.row_counts(controller.run_id)
    return {
        "producer_function": "_run_no_op_dispatch_ablation",
        "failure_observed": result.receipt.committed is False and counts == (0, 0),
        "row_counts": list(counts),
    }


def run_visual_verification(
    output_dir: str | Path, *, screenshot_path: str | Path
) -> dict[str, Any]:
    import tkinter as tk

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    screenshot = Path(screenshot_path)
    for name in REQUIRED_ARTIFACTS:
        candidate = output / name
        if candidate.exists():
            candidate.unlink()

    input_artifacts = [
        _file_record(APP_PATH),
        _file_record(CONTROLLER_PATH),
        _file_record(TERMINAL_PATH),
        _file_record(VISUAL_PATH),
        _file_record(ENGINE_PATH),
        _file_record(STORE_PATH),
        _file_record(Path(__file__)),
    ]
    with tempfile.TemporaryDirectory(prefix="ego-v2-visual-console-") as temp_name:
        temp_root = Path(temp_name)
        db_path = temp_root / "live.sqlite3"
        store = SQLiteEventStore(db_path)
        root = tk.Tk()  # Fail, never skip, if the target interpreter cannot create Tk.
        dispatch_animating_states: list[bool] = []
        pause_close_counts: dict[str, list[int]] = {}
        try:
            controller = PlaygroundController(
                store,
                run_id=RUN_ID,
                seed=RUN_SEED,
                world_seed=WORLD_SEED,
                layout_id=LAYOUT_ID,
            )
            window = PlaygroundWindow(
                root,
                controller,
                display_interval_ms=60,
                animation_segment_ms=70,
            )
            original_dispatch = controller.dispatch

            def observed_dispatch(*args: Any, **kwargs: Any) -> DispatchResult:
                dispatch_animating_states.append(window._animating)
                return original_dispatch(*args, **kwargs)

            controller.dispatch = observed_dispatch  # type: ignore[method-assign]
            root.update()

            causal_before = canonical_json(
                {
                    "state": controller.recovery.frames[-1].state,
                    "trace": controller.recovery.frames[-1].trace,
                }
            )
            build_chinese_causal_view(controller.recovery.frames[-1])
            initial_translation_unchanged = causal_before == canonical_json(
                {
                    "state": controller.recovery.frames[-1].state,
                    "trace": controller.recovery.frames[-1].trace,
                }
            )

            window.event_display_var.set("社交信号出现")
            window.step_button.invoke()
            first_frame = controller.recovery.frames[-1]
            first_expected = recorded_waypoints(first_frame)
            first_panel_ids = deepcopy(window._panel_frame_ids)
            _pump_tk_until(root, lambda: not window._animating)
            first_scheduled = deepcopy(window._scheduled_waypoints)

            window.run_button.invoke()
            _pump_tk_until(
                root, lambda: store.row_counts(controller.run_id)[0] >= 3
            )
            window.pause_button.invoke()
            pause_close_counts["at_pause"] = list(store.row_counts(controller.run_id))
            for _ in range(15):
                root.update()
                time.sleep(0.01)
            pause_close_counts["after_pause_wait"] = list(
                store.row_counts(controller.run_id)
            )
            if window._animating:
                window._animation_paused = False
                window._schedule_animation_subframe()
                _pump_tk_until(root, lambda: not window._animating)

            live_counts = store.row_counts(controller.run_id)
            latest_frame = controller.recovery.frames[-1]
            live_translation_before = canonical_json(
                {"state": latest_frame.state, "trace": latest_frame.trace}
            )
            latest_view = build_chinese_causal_view(latest_frame)
            translation_unchanged = live_translation_before == canonical_json(
                {"state": latest_frame.state, "trace": latest_frame.trace}
            )
            ordinary_text = json.dumps(latest_view, ensure_ascii=False, sort_keys=True)

            direct_export = temp_root / "direct.jsonl"
            ui_export = temp_root / "ui.jsonl"
            controller.export(direct_export)
            with patch(
                "labs.ego_life_playground_v0.app.filedialog.asksaveasfilename",
                return_value=str(ui_export),
            ):
                window._export()
            export_equal = direct_export.read_bytes() == ui_export.read_bytes()
            controller.export(output / "trace.jsonl")

            fresh = _fresh_process_recover(db_path, controller.run_id)
            same_process_recovery = store.recover_run(controller.run_id)
            recomputed_trace_equal = (
                same_process_recovery.traces[-1] == controller.recovery.traces[-1]
                and fresh.get("trace_hash")
                == controller.recovery.traces[-1]["trace_hash"]
            )

            app_scan = scan_forbidden_tokens(VISUAL_PATH)
            positive_control = temp_root / "leakage-positive-control.txt"
            positive_control.write_text(
                "hidden_regime = 'scanner-positive-control'\n", encoding="utf-8"
            )
            positive_scan = scan_forbidden_tokens(positive_control)
            engine_scan = _scan_second_engine_path()

            expected = first_expected
            straight_decoy = [deepcopy(expected[0]), deepcopy(expected[-1])]
            straight_failed = False
            try:
                validate_scheduled_waypoints(expected, straight_decoy)
            except ValueError:
                straight_failed = True

            latch_before = store.row_counts(controller.run_id)
            window.running = True
            window._animating = True
            window._run_tick()
            latch_after = store.row_counts(controller.run_id)
            window.running = False
            window._animating = False

            id_only = {
                "event": latest_frame.trace.get("world_event"),
                "action": latest_frame.trace.get("selected_action"),
            }
            id_only_text = json.dumps(id_only, ensure_ascii=False)
            id_only_failed = any(
                technical_id in id_only_text
                for technical_id in ("social_signal", "resource_appears", "approach", "explore")
            ) and not any(
                technical_id in ordinary_text
                for technical_id in (
                    latest_frame.trace.get("world_event"),
                    latest_frame.trace.get("selected_action"),
                    latest_frame.trace.get("command_hash"),
                )
                if isinstance(technical_id, str)
            )

            capture = _capture_window(root, screenshot)
            tk_patchlevel = str(root.tk.call("info", "patchlevel"))
            pause_close_counts["before_close"] = list(
                store.row_counts(controller.run_id)
            )
            window.close()
            pause_close_counts["after_close"] = list(
                store.row_counts(controller.run_id)
            )

            baseline = {
                "schema_version": "ego.visual_console.baseline_comparison.v1",
                "producer_function": "run_visual_verification.baseline_comparison",
                "input_artifacts": input_artifacts,
                "run_id": RUN_ID,
                "seed_context_episode_ids": {
                    "run_seed": RUN_SEED,
                    "world_seed": WORLD_SEED,
                    "layout_id": LAYOUT_ID,
                },
                "aggregation_rule": "live path must commit and fresh-recover; frozen player must not dispatch or commit",
                "code_path_hash": _code_path_hash(),
                "live_visual_console": {
                    "committed_sequence_delta": live_counts[0],
                    "fresh_recovered_sequence": fresh.get("sequence"),
                },
                "frozen_player_no_dispatch": _frozen_player_baseline(temp_root),
            }
            no_op = _run_no_op_dispatch_ablation(temp_root)
            ablation = {
                "schema_version": "ego.visual_console.ablation_report.v1",
                "producer_function": "run_visual_verification.ablation_report",
                "input_artifacts": input_artifacts,
                "run_id": RUN_ID,
                "seed_context_episode_ids": {
                    "run_seed": RUN_SEED,
                    "world_seed": WORLD_SEED,
                    "layout_id": LAYOUT_ID,
                },
                "aggregation_rule": "every named intervention must produce its predeclared failure",
                "code_path_hash": _code_path_hash(),
                "no_op_dispatch": no_op,
                "straight_line_decoy": {
                    "producer_function": "validate_scheduled_waypoints",
                    "failure_observed": straight_failed,
                    "expected": expected,
                    "decoy": straight_decoy,
                },
                "animation_latch_held_closed": {
                    "producer_function": "PlaygroundWindow._run_tick",
                    "failure_observed": latch_before == latch_after,
                    "row_counts_before": list(latch_before),
                    "row_counts_after": list(latch_after),
                },
                "id_only_translation": {
                    "producer_function": "build_chinese_causal_view",
                    "failure_observed": id_only_failed,
                },
                "leakage_positive_control": {
                    "producer_function": "scan_forbidden_tokens",
                    "failure_observed": positive_scan["matches"] == ["hidden_regime"],
                    "positive_control_matches": positive_scan["matches"],
                },
            }
            replay_report = {
                "schema_version": "ego.visual_console.replay_report.v1",
                "producer_function": "run_visual_verification.replay_report",
                "input_artifacts": [
                    *input_artifacts,
                    _file_record(output / "trace.jsonl"),
                ],
                "run_id": RUN_ID,
                "seed_context_episode_ids": {
                    "run_seed": RUN_SEED,
                    "world_seed": WORLD_SEED,
                    "layout_id": LAYOUT_ID,
                    "sequence": latest_frame.sequence,
                },
                "aggregation_rule": "recover from serialized initial state plus ordered commands and recompute the same trace",
                "code_path_hash": _code_path_hash(),
                "fresh_process": fresh,
                "recomputed_trace_equal": recomputed_trace_equal,
                "stored_trace_hash_only_comparison": False,
            }
            live_receipt = {
                "schema_version": "ego.visual_console.live_ui_receipt.v1",
                "producer_function": "run_visual_verification.live_ui_receipt",
                "input_artifacts": input_artifacts,
                "run_id": RUN_ID,
                "seed_context_episode_ids": {
                    "run_seed": RUN_SEED,
                    "world_seed": WORLD_SEED,
                    "layout_id": LAYOUT_ID,
                },
                "aggregation_rule": "real Tk triggers plus SQLite/recovery/path/capture readback",
                "code_path_hash": _code_path_hash(),
                "dispatch_observed_animating_states": dispatch_animating_states,
                "sqlite_row_counts": list(live_counts),
                "first_recovered_sequence": first_frame.sequence,
                "first_expected_waypoints": first_expected,
                "first_actual_scheduled_waypoints": first_scheduled,
                "panel_frame_ids": first_panel_ids,
                "pause_close_row_counts": pause_close_counts,
                "capture": capture,
                "tk_patchlevel": tk_patchlevel,
                "default_off": True,
                "runtime_authority": "local_explicit_v2_only",
            }

            pause_close_zero = (
                pause_close_counts["at_pause"]
                == pause_close_counts["after_pause_wait"]
                == pause_close_counts["before_close"]
                == pause_close_counts["after_close"]
            )
            checks = {
                "ui_step_calls_canonical_dispatch": _evidence(
                    len(dispatch_animating_states) >= 3
                    and dispatch_animating_states[0] is False,
                    producer_function="PlaygroundWindow._step_once -> PlaygroundController.dispatch",
                    inputs=input_artifacts,
                ),
                "sqlite_committed_transition": _evidence(
                    live_counts[0] == live_counts[1] and live_counts[0] >= 3,
                    producer_function="SQLiteEventStore.row_counts",
                    inputs=input_artifacts,
                ),
                "fresh_process_recover": _evidence(
                    fresh.get("returncode") == 0
                    and fresh.get("recovered") is True
                    and fresh.get("sequence") == live_counts[0],
                    producer_function="_fresh_process_recover",
                    inputs=input_artifacts,
                ),
                "same_recovery_frame_all_panels": _evidence(
                    len(set(first_panel_ids.values())) == 1
                    and next(iter(first_panel_ids.values())) == id(first_frame),
                    producer_function="PlaygroundWindow.redraw",
                    inputs=input_artifacts,
                ),
                "scheduled_waypoints_equal_trace": _evidence(
                    first_scheduled == first_expected,
                    producer_function="validate_scheduled_waypoints",
                    inputs=input_artifacts,
                ),
                "run_commit_recover_animate_lockstep": _evidence(
                    dispatch_animating_states
                    and all(value is False for value in dispatch_animating_states),
                    producer_function="PlaygroundWindow._animation_complete",
                    inputs=input_artifacts,
                ),
                "pause_close_zero_extra_dispatch": _evidence(
                    pause_close_zero,
                    producer_function="PlaygroundWindow._pause/close",
                    inputs=input_artifacts,
                ),
                "export_byte_identity": _evidence(
                    export_equal,
                    producer_function="PlaygroundWindow._export -> PlaygroundController.export",
                    inputs=input_artifacts,
                ),
                "replay_recomputes_serialized_state_observation": _evidence(
                    recomputed_trace_equal,
                    producer_function="SQLiteEventStore.recover_run",
                    inputs=input_artifacts,
                ),
                "chinese_mapping_causal_bytes_unchanged": _evidence(
                    initial_translation_unchanged and translation_unchanged,
                    producer_function="build_chinese_causal_view",
                    inputs=input_artifacts,
                ),
                "private_field_leakage_scan_positive_control": _evidence(
                    app_scan["matches"] == []
                    and positive_scan["matches"] == ["hidden_regime"],
                    producer_function="scan_forbidden_tokens",
                    inputs=input_artifacts,
                ),
                "no_second_engine_path": _evidence(
                    engine_scan["pass"] is True,
                    producer_function="_scan_second_engine_path",
                    inputs=input_artifacts,
                ),
                "fresh_process_and_tk_non_skip": _evidence(
                    fresh.get("returncode") == 0 and capture["bytes"] > 0,
                    producer_function="tk.Tk + _fresh_process_recover",
                    inputs=input_artifacts,
                ),
                "ux_capture_produced": _evidence(
                    capture["bytes"] > 0,
                    producer_function="_capture_window",
                    inputs=input_artifacts,
                ),
            }
            aggregation = aggregate_visual_result(checks)
            result = {
                "schema_version": "ego.visual_console.result.v1",
                "task_id": TASK_ID,
                "producer_function": "run_visual_verification",
                "input_artifacts": [
                    *input_artifacts,
                    _file_record(output / "trace.jsonl"),
                ],
                "run_id": RUN_ID,
                "seed_context_episode_ids": {
                    "run_seed": RUN_SEED,
                    "world_seed": WORLD_SEED,
                    "layout_id": LAYOUT_ID,
                },
                "aggregation_rule": "pass iff all 14 callable integration checks are true",
                "code_path_hash": _code_path_hash(),
                "checks": checks,
                "verdict": aggregation["verdict"],
                "failed_checks": aggregation["failed_checks"],
                "claim_ceiling": CLAIM_CEILING,
            }
            failure_manifest = {
                "schema_version": "ego.visual_console.failure_manifest.v1",
                "producer_function": "aggregate_visual_result",
                "input_artifacts": result["input_artifacts"],
                "run_id": RUN_ID,
                "seed_context_episode_ids": result["seed_context_episode_ids"],
                "aggregation_rule": result["aggregation_rule"],
                "code_path_hash": _code_path_hash(),
                "status": "clean" if aggregation["verdict"] == "pass" else "fail",
                "failures": aggregation["failed_checks"],
            }
            _write_json(output / "baseline_comparison.json", baseline)
            _write_json(output / "ablation_report.json", ablation)
            _write_json(output / "replay_report.json", replay_report)
            _write_json(output / "live_ui_receipt.json", live_receipt)
            _write_json(output / "failure_manifest.json", failure_manifest)
            _write_json(output / "result.json", result)
            (output / "claim_ceiling.txt").write_text(
                CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
            )
            if set(path.name for path in output.iterdir()) != REQUIRED_ARTIFACTS:
                raise RuntimeError("visual evidence output set is not exact")
            return result
        finally:
            try:
                if root.winfo_exists():
                    root.destroy()
            except Exception:
                pass
            store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_visual_verification(
        args.output_dir, screenshot_path=args.screenshot
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
