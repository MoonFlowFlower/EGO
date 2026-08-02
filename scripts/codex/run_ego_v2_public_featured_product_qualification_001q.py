#!/usr/bin/env python3
"""Run the one-shot, new-packet 001Q product integration qualification."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0 import public_featured_hierarchical as learner
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.terminal import render_homeostatic_trace_html


TASK_ID = "EGO-V2-PUBLIC-FEATURED-HIERARCHICAL-TRANSFER-PRODUCT-001Q"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / TASK_ID
PROFILE = "public_featured_hierarchical_transfer"
MODE = "hierarchical_bayes"
QUALIFICATION_SEED = 104729
QUALIFICATION_RUN_ID = "ego-v2-public-featured-product-001q-qualification"
MIN_ACTIONS_AFTER_WORLD_SWITCH = 1


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _source_hashes() -> dict[str, str]:
    paths = (
        "labs/ego_life_playground_v0/public_featured_hierarchical.py",
        "labs/ego_life_playground_v0/public_featured_product_world.py",
        "labs/ego_life_playground_v0/engine.py",
        "labs/ego_life_playground_v0/controller.py",
        "labs/ego_life_playground_v0/store.py",
        "scripts/codex/verify_ego_v2_public_featured_product_qualification_001q.py",
    )
    return {
        path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        for path in paths
    }


def _interventions(*, update_mode: str = "canonical") -> dict[str, str]:
    return dict(
        engine.DEFAULT_INTERVENTIONS,
        update_mode=update_mode,
        public_featured_transfer_mode=MODE,
    )


def _public_rows(recovery: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frame in recovery.frames[1:]:
        trace = frame.trace or {}
        featured = trace.get("public_featured_transfer") or {}
        update = featured.get("update") or {}
        row = {
            "schema_version": "ego.v2.public_featured_product_public_row.001q.v1",
            "sequence": int(frame.sequence),
            "transition_kind": trace.get("transition_kind"),
            "observation": deepcopy(featured.get("observation")),
            "plan": deepcopy(featured.get("plan")),
            "selected_action": trace.get("selected_action"),
            "actual_feedback": deepcopy(featured.get("actual_feedback")),
            "update_applied": bool(update.get("applied")),
            "learner_state_hash_before": update.get("state_hash_before"),
            "learner_state_hash_after": update.get(
                "state_hash_after", update.get("state_hash_before")
            ),
            "slow_state_hash_after": featured.get("slow_state_hash"),
            "fast_state_hash_after": featured.get("fast_state_hash"),
            "posterior_entropy_bits": featured.get("posterior_entropy_bits"),
            "world_switch_count": featured.get("world_switch_count"),
            "trace_hash": trace.get("trace_hash"),
        }
        row["row_hash"] = _canonical_hash(row)
        rows.append(row)
    return rows


def _drive_intervention(trained_state: dict[str, Any]) -> dict[str, Any]:
    public_slots = [
        {"features": [0, 0, 0, 0, 0]},
        {"features": [1, 0, 0, 0, 0]},
        {"features": [1, 0, 1, 0, 1]},
    ]
    energy_deficit = {
        "organism": {"energy": 0.1, "safety": 0.8, "target": 0.72},
        "slots": public_slots,
        "previous": None,
    }
    safety_deficit = deepcopy(energy_deficit)
    safety_deficit["organism"] = {
        "energy": 0.8,
        "safety": 0.1,
        "target": 0.72,
    }
    slow_before = learner.slow_state_hash(trained_state)
    first = learner.plan_action(trained_state, energy_deficit)
    second = learner.plan_action(trained_state, safety_deficit)
    return {
        "passed": (
            first["ranking"] != second["ranking"]
            and first["reason"]["primary_deficit"] == "energy"
            and second["reason"]["primary_deficit"] == "safety"
            and slow_before == learner.slow_state_hash(trained_state)
        ),
        "public_slots_identical": True,
        "posterior_unchanged": slow_before == learner.slow_state_hash(trained_state),
        "energy_deficit_plan": first,
        "safety_deficit_plan": second,
    }


def _no_update_check() -> dict[str, Any]:
    state = engine.initial_state(
        run_id="001q-no-update", seed=199933, product_profile=PROFILE
    )
    meta = engine.make_run_metadata(
        "001q-no-update", 199933, product_profile=PROFILE
    )
    before_hash = learner.state_hash(state["public_featured_transfer"]["learner"])
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=_interventions(update_mode="frozen"),
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, meta)
    after_hash = learner.state_hash(
        result.next_state["public_featured_transfer"]["learner"]
    )
    return {
        "passed": (
            before_hash == after_hash
            and result.trace["public_featured_transfer"]["update"]["applied"]
            is False
        ),
        "learner_hash_before": before_hash,
        "learner_hash_after": after_hash,
        "update": result.trace["public_featured_transfer"]["update"],
    }


def _default_off_check(tmp: Path) -> dict[str, Any]:
    with SQLiteEventStore(tmp / "default-off.sqlite3") as store:
        controller = PlaygroundController(
            store, run_id="001q-default-off", seed=314159
        )
        result = controller.dispatch(trigger_source="headless_acceptance")
        return {
            "passed": (
                result.receipt.committed
                and controller.state["public_featured_transfer"]["active"] is False
                and controller.last_trace["interventions"][
                    "public_featured_transfer_mode"
                ]
                == "off"
            ),
            "active": controller.state["public_featured_transfer"]["active"],
            "mode": controller.last_trace["interventions"][
                "public_featured_transfer_mode"
            ],
        }


def _leakage_check() -> dict[str, Any]:
    rejected: list[str] = []
    base = {
        "organism": {"energy": 0.5, "safety": 0.5, "target": 0.72},
        "slots": [
            {"features": [0, 0, 0, 0, 0]},
            {"features": [0, 1, 0, 1, 0]},
            {"features": [1, 0, 1, 0, 1]},
        ],
        "previous": None,
    }
    for field in ("seed", "world_id", "mapping", "oracle_action", "future"):
        hostile = deepcopy(base)
        hostile[field] = "positive-control"
        try:
            learner.plan_action(learner.new_learner_state(), hostile)
        except ValueError:
            rejected.append(field)
    return {
        "passed": len(rejected) == 5,
        "positive_controls": 5,
        "rejected": rejected,
    }


def _code_path_tamper_check() -> dict[str, Any]:
    state = engine.initial_state(
        run_id="001q-path-tamper", seed=271828, product_profile=PROFILE
    )
    meta = engine.make_run_metadata(
        "001q-path-tamper", 271828, product_profile=PROFILE
    )
    meta["public_featured_code_path_hash"] = "0" * 64
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=_interventions(),
        prev_command_hash=None,
    )
    try:
        engine.compute_step(state, command, meta)
    except engine.EngineInvariantError as exc:
        return {"passed": True, "error": str(exc)}
    return {"passed": False, "error": None}


def run_qualification(output_dir: Path = ARTIFACT_DIR) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("001Q qualification output already exists; refuse rerun")
    output_dir.mkdir(parents=True, exist_ok=True)
    freeze = {
        "schema_version": "ego.v2.public_featured_product_freeze.001q.v1",
        "task_id": TASK_ID,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "qualification_seed": QUALIFICATION_SEED,
        "run_id": QUALIFICATION_RUN_ID,
        "stop_rule": "first action after first existing-lifecycle respawn",
        "source_hashes": _source_hashes(),
        "learner_hyperparameters": learner.hyperparameters(),
        "interventions": _interventions(),
    }
    _write_json(output_dir / "qualification_freeze.json", freeze)

    with TemporaryDirectory(prefix="ego-001q-") as temp_text:
        temp = Path(temp_text)
        db_path = temp / "qualification.sqlite3"
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id=QUALIFICATION_RUN_ID,
                seed=QUALIFICATION_SEED,
                public_featured_transfer=True,
            )
            action_count_after_switch = 0
            while True:
                result = controller.dispatch(
                    _interventions(), trigger_source="headless_acceptance"
                )
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "qualification commit failed")
                featured = controller.state["public_featured_transfer"]
                if int(featured["world_switch_count"]) >= 1:
                    if result.step and result.step.trace["transition_kind"] == "action":
                        action_count_after_switch += 1
                if action_count_after_switch >= MIN_ACTIONS_AFTER_WORLD_SWITCH:
                    break
                if int(controller.state["clock"]["global_tick"]) > 300:
                    raise RuntimeError("qualification stop rule exceeded 300 commands")
            recovery = controller.recover()
            rows = _public_rows(recovery)
            rows_path = output_dir / "qualification_public_rows.jsonl"
            rows_path.write_text(
                "".join(_canonical_json(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            render_homeostatic_trace_html(
                recovery, output_dir / "qualification_trace.html"
            )
            replay_report = {
                "passed": recovery.recovered,
                "verification_mode": recovery.verification_mode,
                "command_count": recovery.command_count,
                "last_trace_hash": recovery.traces[-1]["trace_hash"],
                "world_switch_count": recovery.state["public_featured_transfer"][
                    "world_switch_count"
                ],
                "slow_update_count": recovery.state["public_featured_transfer"][
                    "learner"
                ]["update_count"],
                "fast_world_update_count": recovery.state[
                    "public_featured_transfer"
                ]["learner"]["world_update_count"],
            }
            drive_report = _drive_intervention(
                deepcopy(recovery.state["public_featured_transfer"]["learner"])
            )

            # Positive control: corrupt a stored trace after the clean replay.
            last_sequence = recovery.last_committed_sequence
            stored = store.connection.execute(
                "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = ?",
                (controller.run_id, last_sequence),
            ).fetchone()
            tampered = json.loads(stored["trace_json"])
            tampered["selected_action"] = (
                "interact_0" if tampered.get("selected_action") == "rest" else "rest"
            )
            store.connection.execute(
                "UPDATE traces SET trace_json = ? WHERE run_id = ? AND sequence = ?",
                (_canonical_json(tampered), controller.run_id, last_sequence),
            )
            store.connection.commit()
            try:
                store.recover_run(controller.run_id)
            except RecoveryError as exc:
                trace_tamper_report = {"passed": True, "error": str(exc)}
            else:
                trace_tamper_report = {"passed": False, "error": None}

        default_off_report = _default_off_check(temp)

    verifier_path = (
        REPO_ROOT
        / "scripts/codex/verify_ego_v2_public_featured_product_qualification_001q.py"
    )
    row_report_path = output_dir / "independent_row_recomputation.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(verifier_path),
            str(rows_path),
            "--output",
            str(row_report_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    row_report = json.loads(row_report_path.read_text(encoding="utf-8"))
    row_report["subprocess_returncode"] = completed.returncode
    row_report["subprocess_stdout"] = completed.stdout.strip()
    row_report["subprocess_stderr"] = completed.stderr.strip()
    _write_json(row_report_path, row_report)

    no_update_report = _no_update_check()
    leakage_report = _leakage_check()
    code_path_tamper_report = _code_path_tamper_check()
    _write_json(output_dir / "replay_report.json", replay_report)
    _write_json(output_dir / "drive_intervention_report.json", drive_report)
    _write_json(output_dir / "no_update_report.json", no_update_report)
    _write_json(output_dir / "default_off_report.json", default_off_report)
    _write_json(output_dir / "leakage_report.json", leakage_report)
    _write_json(
        output_dir / "tamper_report.json",
        {
            "trace_tamper": trace_tamper_report,
            "featured_code_path_tamper": code_path_tamper_report,
            "passed": trace_tamper_report["passed"]
            and code_path_tamper_report["passed"],
        },
    )

    checks = {
        "replay": bool(replay_report["passed"]),
        "reference_row_parity": bool(row_report["passed"])
        and completed.returncode == 0,
        "world_switch_slow_persistence": (
            int(replay_report["world_switch_count"]) >= 1
            and int(replay_report["slow_update_count"])
            > int(replay_report["fast_world_update_count"])
        ),
        "no_update": bool(no_update_report["passed"]),
        "drive_intervention": bool(drive_report["passed"]),
        "default_off": bool(default_off_report["passed"]),
        "leakage": bool(leakage_report["passed"]),
        "tamper": bool(trace_tamper_report["passed"])
        and bool(code_path_tamper_report["passed"]),
    }
    passed = all(checks.values())
    result = {
        "schema_version": "ego.v2.public_featured_product_qualification.001q.v1",
        "task_id": TASK_ID,
        "verdict": (
            "PRODUCT_RUNTIME_INTEGRATION_QUALIFIED_AGAINST_FROZEN_REFERENCE"
            if passed
            else "PRODUCT_RUNTIME_INTEGRATION_QUALIFICATION_FAILED"
        ),
        "passed": passed,
        "checks": checks,
        "qualification_seed": QUALIFICATION_SEED,
        "command_count": replay_report["command_count"],
        "action_row_count": row_report["action_count"],
        "respawn_row_count": row_report["respawn_count"],
        "claim_ceiling": (
            "Bounded runtime integration and exact public-row parity with the "
            "frozen 001O reference only."
        ),
    }
    _write_json(output_dir / "result.json", result)
    (output_dir / "claim_ceiling.txt").write_text(
        "This proves only that the frozen finite-family public model-based learner "
        "runs, updates, persists across one product world switch, and replays through "
        "the sole local reducer/store path. It does not prove general transfer, "
        "learning outside the hypothesis family, agency, consciousness, or real-world "
        "survival ability.\n",
        encoding="utf-8",
    )
    failure_manifest = {
        "present": not passed,
        "failed_checks": [name for name, value in checks.items() if not value],
    }
    _write_json(output_dir / "failure_manifest.json", failure_manifest)

    manifest_entries = []
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        if path.name == "artifact_manifest.json" or not path.is_file():
            continue
        manifest_entries.append(
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    _write_json(
        output_dir / "artifact_manifest.json",
        {
            "schema_version": "ego.v2.public_featured_product_manifest.001q.v1",
            "task_id": TASK_ID,
            "entries": manifest_entries,
        },
    )
    return result


def main() -> int:
    result = run_qualification()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
