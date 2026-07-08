from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from scripts.ego_kernel.state import KernelState, canonical_sha256, deep_copy
from scripts.ego_kernel.trace import build_trace_row, validate_trace_row, write_jsonl
from scripts.ego_pet import CLAIM_CEILING, TASK_ID
from scripts.ego_pet.creature import select_action, update_creature_after_feedback, zero_creature_state
from scripts.ego_pet.memory_wiring import run_poison_quarantine_probe, zero_pet_memory_state
from scripts.ego_pet.static_gate import load_static_gate_config, zero_static_gate_state
from scripts.ego_pet.world import (
    WORLD_CONFIG_PATH,
    advance_world,
    build_observation,
    load_world_config,
    zero_world_state,
)


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "egodesktop-pet-world-integration-001a"
STATIC_GATE_CONFIG_PATH = TASK_DIR / "static_gate_config_v0.json"
ADDENDUM_002_PATH = TASK_DIR / "ADDENDUM_002.md"
ARTIFACT_ROOT = ROOT / "artifacts" / "egodesktop_pet_world_integration_001a" / "p0"
RUN_ID = "egodesktop_pet_world_integration_001a_p0_v1"
ARMS = ["candidate", "standin", "random", "static", "frozen_updates", "schedule_aware_reference"]


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_path_hash(repo_root: Path = ROOT) -> str:
    rels = [
        "scripts/ego_pet/__init__.py",
        "scripts/ego_pet/world.py",
        "scripts/ego_pet/creature.py",
        "scripts/ego_pet/standin.py",
        "scripts/ego_pet/memory_wiring.py",
        "scripts/ego_pet/static_gate.py",
        "scripts/ego_pet/battery.py",
        "scripts/run_ego_pet_integration_battery.py",
        "docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json",
        "docs/codex/tasks/egodesktop-pet-world-integration-001a/static_gate_config_v0.json",
        "docs/codex/tasks/egodesktop-pet-world-integration-001a/ADDENDUM_002.md",
    ]
    digest = hashlib.sha256()
    for rel in rels:
        path = repo_root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
    return digest.hexdigest()


def _config_shas() -> dict[str, str]:
    return {
        "world_config_v0.json": sha256_file(WORLD_CONFIG_PATH),
        "static_gate_config_v0.json": sha256_file(STATIC_GATE_CONFIG_PATH),
        "ADDENDUM_002.md": sha256_file(ADDENDUM_002_PATH),
    }


def _initial_state(config: dict[str, Any], *, seed: int, arm: str, run_id: str, episode_id: str) -> KernelState:
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=0,
        substates={
            "pet_world_v0": zero_world_state(config),
            "pet_creature_v0": zero_creature_state(config, arm=arm),
            "pet_memory_v0": zero_pet_memory_state(),
            "pet_static_gate_v0": zero_static_gate_state(),
            "run_context": {"arm": arm, "zero_user_input_scoring": True},
        },
        seed_registry={"pet_policy": {"seed": int(seed), "draws": 0}},
        ablations={"pet_creature_v0": "frozen" if arm == "frozen_updates" else "live"},
    )


def generate_autonomous_observations(config: dict[str, Any], *, start_tick: int = 0, ticks: int | None = None) -> list[dict[str, Any]]:
    total = int(ticks if ticks is not None else config["time"]["episode_length_ticks"])
    return [{"tick_index": int(t), "user_event": None} for t in range(int(start_tick), int(start_tick) + total)]


def run_episode(
    *,
    config: dict[str, Any],
    seed: int,
    arm: str,
    run_id: str,
    episode_id: str,
    observations: list[dict[str, Any]] | None = None,
    initial_state: dict[str, Any] | None = None,
    checkpoint_ticks: set[int] | None = None,
) -> dict[str, Any]:
    state = KernelState.from_dict(initial_state) if initial_state else _initial_state(config, seed=seed, arm=arm, run_id=run_id, episode_id=episode_id)
    raw_observations = observations if observations is not None else generate_autonomous_observations(config, start_tick=state.step_id)
    checkpoint_ticks = set(checkpoint_ticks or set())
    checkpoints: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    viability_by_tick: dict[int, float] = {}
    for raw in raw_observations:
        before = state
        world_state = deep_copy(state.substates["pet_world_v0"])
        observation = build_observation(world_state, config, raw.get("user_event"))
        action, working_state, attribution = select_action(state, observation, config, arm=arm)
        world_after, feedback = advance_world(world_state, action, config)
        creature_before = deep_copy(working_state.substates["pet_creature_v0"])
        updates_enabled = arm not in {"frozen_updates", "static", "standin", "random"}
        creature_after = update_creature_after_feedback(creature_before, action, feedback, updates_enabled=updates_enabled)
        attribution = {
            **attribution,
            "arm": arm,
            "feedback": feedback,
            "viability": feedback["viability_after"],
            "updates_enabled": updates_enabled,
            "component": "ego_pet_p0",
        }
        state = working_state.with_updates(
            step_id=working_state.step_id + 1,
            substates={
                "pet_world_v0": world_after,
                "pet_creature_v0": creature_after,
            },
        )
        row = build_trace_row(
            state_before=before,
            observation=observation,
            action=action,
            state_after=state,
            component_attribution=attribution,
        )
        validate_trace_row(row)
        rows.append(row)
        viability_by_tick[int(observation["tick_index"])] = float(feedback["viability_after"])
        if state.step_id in checkpoint_ticks:
            checkpoints[str(state.step_id)] = state.to_dict()
    return {
        "initial_state": (_initial_state(config, seed=seed, arm=arm, run_id=run_id, episode_id=episode_id).to_dict() if initial_state is None else initial_state),
        "final_state": state.to_dict(),
        "observations": raw_observations,
        "trace_rows": rows,
        "checkpoints": checkpoints,
        "metrics": {"viability_by_tick": viability_by_tick, "window_means": window_means(viability_by_tick, config)},
    }


def replay_episode(payload: dict[str, Any]) -> dict[str, Any]:
    config = load_world_config()
    initial = payload["initial_state"]
    arm = initial["substates"]["run_context"]["arm"]
    seed = int(initial["seed_registry"]["pet_policy"]["seed"])
    return run_episode(
        config=config,
        seed=seed,
        arm=arm,
        run_id=initial["run_id"],
        episode_id=initial["episode_id"],
        initial_state=initial,
        observations=payload["observations"],
    )


def compare_sequences(expected: list[dict[str, Any]], actual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if len(expected) != len(actual):
        mismatches.append({"kind": "length", "expected": len(expected), "actual": len(actual)})
    for index, (left, right) in enumerate(zip(expected, actual)):
        for field in ("state_before_hash", "action", "state_after_hash"):
            if left.get(field) != right.get(field):
                mismatches.append({"index": index, "field": field, "expected": left.get(field), "actual": right.get(field)})
                break
    return mismatches


def window_means(viability_by_tick: dict[int, float], config: dict[str, Any]) -> dict[str, float]:
    means: dict[str, float] = {}
    for window in config["evaluation_windows"]["post_shift_windows"]:
        start, end = [int(x) for x in window["tick_range"]]
        values = [float(viability_by_tick[t]) for t in range(start, end + 1) if t in viability_by_tick]
        means[str(window["window_id"])] = round(sum(values) / len(values), 12) if values else 0.0
    ref = config["evaluation_windows"]["pre_shift_reference_window"]
    start, end = [int(x) for x in ref["tick_range"]]
    values = [float(viability_by_tick[t]) for t in range(start, end + 1) if t in viability_by_tick]
    means[str(ref["window_id"])] = round(sum(values) / len(values), 12) if values else 0.0
    means["post_shift_mean"] = round(
        sum(means[w["window_id"]] for w in config["evaluation_windows"]["post_shift_windows"])
        / len(config["evaluation_windows"]["post_shift_windows"]),
        12,
    )
    return means


def _bootstrap_indices(sample_count: int, draw_count: int, draw_index: int) -> list[int]:
    indices: list[int] = []
    for i in range(sample_count):
        digest = hashlib.sha256(f"pet-bootstrap:{draw_count}:{draw_index}:{i}".encode("utf-8")).hexdigest()
        indices.append(int(digest[:12], 16) % sample_count)
    return indices


def bootstrap_ci(values: list[float], *, draws: int = 1000) -> dict[str, float]:
    if not values:
        return {"low": 0.0, "high": 0.0, "mean": 0.0}
    means = []
    for draw in range(draws):
        indices = _bootstrap_indices(len(values), draws, draw)
        means.append(sum(values[i] for i in indices) / len(indices))
    ordered = sorted(means)
    low = ordered[int(0.025 * (len(ordered) - 1))]
    high = ordered[int(0.975 * (len(ordered) - 1))]
    return {"low": round(low, 12), "high": round(high, 12), "mean": round(sum(values) / len(values), 12)}


def _episode_id(arm: str, seed: int) -> str:
    return f"p0_{arm}_seed_{seed}"


def run_arm_set(config: dict[str, Any], seeds: list[int], *, run_id: str, arms: list[str] | None = None) -> dict[str, dict[str, Any]]:
    selected = arms or ARMS
    runs: dict[str, dict[str, Any]] = {}
    for arm in selected:
        runs[arm] = {}
        for seed in seeds:
            episode_id = _episode_id(arm, seed)
            runs[arm][str(seed)] = run_episode(config=config, seed=seed, arm=arm, run_id=run_id, episode_id=episode_id, checkpoint_ticks={300})
    return runs


def baseline_comparison(runs: dict[str, dict[str, Any]], config: dict[str, Any], *, run_id: str, code_hash: str) -> dict[str, Any]:
    per_seed: list[dict[str, Any]] = []
    for seed in sorted(int(s) for s in runs["candidate"]):
        seed_key = str(seed)
        row = {"seed": seed}
        for arm in ARMS:
            row[arm] = runs[arm][seed_key]["metrics"]["window_means"]["post_shift_mean"]
        row["candidate_minus_standin"] = round(row["candidate"] - row["standin"], 12)
        per_seed.append(row)
    diffs = [row["candidate_minus_standin"] for row in per_seed]
    ci = bootstrap_ci(diffs)
    delta = float(config["gate_constants"]["delta_hard_absolute_windowed_viability"])
    return {
        "producer_function": "baseline_comparison",
        "input_artifacts": ["world_config_v0.json", "ADDENDUM_002.md"],
        "run_id": run_id,
        "seed_ids": [row["seed"] for row in per_seed],
        "episode_ids": [_episode_id("candidate", row["seed"]) for row in per_seed],
        "aggregation_rule": "paired candidate_minus_hardcoded_standin post_shift_mean over frozen S_scored/S_dev subset with deterministic bootstrap CI",
        "code_path_hash": code_hash,
        "delta_hard": delta,
        "per_seed": per_seed,
        "ci": ci,
        "status": "pass" if ci["low"] >= delta else "fail",
        "gate": "G-PET-HARD",
    }


def ablation_report(runs: dict[str, dict[str, Any]], config: dict[str, Any], *, hard_report: dict[str, Any], run_id: str, code_hash: str) -> dict[str, Any]:
    if hard_report["status"] != "pass":
        return {
            "producer_function": "ablation_report",
            "input_artifacts": ["baseline_comparison.json"],
            "run_id": run_id,
            "seed_ids": hard_report["seed_ids"],
            "aggregation_rule": "not_evaluable when G-PET-HARD has no candidate win",
            "code_path_hash": code_hash,
            "gate": "G-PET-ABLATION",
            "status": "not_evaluable_no_win",
        }
    collapses = []
    identical_pairs = 0
    for seed in hard_report["seed_ids"]:
        key = str(seed)
        candidate = runs["candidate"][key]["metrics"]["window_means"]["post_shift_mean"]
        standin = runs["standin"][key]["metrics"]["window_means"]["post_shift_mean"]
        frozen = runs["frozen_updates"][key]["metrics"]["window_means"]["post_shift_mean"]
        gap = candidate - standin
        frozen_gap = frozen - standin
        collapse = 1.0 if gap <= 0 else (gap - frozen_gap) / gap
        collapses.append(collapse)
        cand_actions = [r["action"] for r in runs["candidate"][key]["trace_rows"][200:300]]
        frozen_actions = [r["action"] for r in runs["frozen_updates"][key]["trace_rows"][200:300]]
        if cand_actions == frozen_actions:
            identical_pairs += 1
    mean_collapse = sum(collapses) / len(collapses)
    positive_control = ablation_positive_control(config)
    tripwire_ok = identical_pairs == 0
    f_abl = float(config["gate_constants"]["f_abl_min_gap_collapse_fraction"])
    status = "pass" if mean_collapse >= f_abl and tripwire_ok and positive_control["status"] == "pass" else "fail"
    return {
        "producer_function": "ablation_report",
        "input_artifacts": ["baseline_comparison.json", "world_config_v0.json"],
        "run_id": run_id,
        "seed_ids": hard_report["seed_ids"],
        "episode_ids": [_episode_id("frozen_updates", seed) for seed in hard_report["seed_ids"]],
        "aggregation_rule": "mean collapse fraction of candidate-vs-standin post_shift gap under frozen-updates arm",
        "code_path_hash": code_hash,
        "gate": "G-PET-ABLATION",
        "f_abl": f_abl,
        "mean_collapse_fraction": round(mean_collapse, 12),
        "identity_tripwire": {"identical_pairs": identical_pairs, "status": "pass" if tripwire_ok else "fail"},
        "non_identity_positive_control": positive_control,
        "status": status,
    }


def ablation_positive_control(config: dict[str, Any]) -> dict[str, Any]:
    live = run_episode(config=config, seed=9991, arm="candidate", run_id="ablation_positive_control", episode_id="live", observations=generate_autonomous_observations(config, ticks=260))
    frozen = run_episode(config=config, seed=9991, arm="frozen_updates", run_id="ablation_positive_control", episode_id="frozen", observations=generate_autonomous_observations(config, ticks=260))
    live_actions = [row["action"] for row in live["trace_rows"][200:260]]
    frozen_actions = [row["action"] for row in frozen["trace_rows"][200:260]]
    changed = live_actions != frozen_actions
    return {
        "producer_function": "ablation_positive_control",
        "fixture": "post_shift_non_identity_constructed_fixture_seed_9991",
        "status": "pass" if changed else "fail",
        "actions_differ": changed,
    }


def replay_report(runs: dict[str, dict[str, Any]], *, repo_root: Path, run_id: str, code_hash: str) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    episode_count = 0
    for arm, by_seed in runs.items():
        for seed, result in by_seed.items():
            episode_count += 1
            payload = {"initial_state": result["initial_state"], "observations": result["observations"]}
            for fresh_index in range(2):
                completed = subprocess.run(
                    [sys.executable, "scripts/run_ego_pet_integration_battery.py", "--replay-stdin"],
                    cwd=str(repo_root),
                    input=json.dumps(payload, ensure_ascii=False),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if completed.returncode != 0:
                    mismatches.append({"arm": arm, "seed": seed, "fresh_index": fresh_index, "kind": "subprocess_error", "stderr": completed.stderr[-500:]})
                    continue
                replayed = json.loads(completed.stdout)
                diff = compare_sequences(result["trace_rows"], replayed["trace_rows"])
                for item in diff[:5]:
                    mismatches.append({"arm": arm, "seed": seed, "fresh_index": fresh_index, **item})
    return {
        "producer_function": "replay_report",
        "input_artifacts": ["trace.jsonl", "world_config_v0.json"],
        "run_id": run_id,
        "seed_ids": sorted({int(seed) for by_seed in runs.values() for seed in by_seed}),
        "episode_ids": [_episode_id(arm, int(seed)) for arm, by_seed in runs.items() for seed in by_seed],
        "aggregation_rule": "fresh subprocess replay x2, compare state_before_hash/action/state_after_hash",
        "code_path_hash": code_hash,
        "fresh_subprocess_runs_per_episode": 2,
        "episode_count": episode_count,
        "mismatches_total": len(mismatches),
        "mismatches": mismatches[:20],
        "gate": "G-PET-REPLAY",
        "status": "pass" if not mismatches else "fail",
    }


def _path_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _rng_usage_hits(path: Path) -> list[dict[str, Any]]:
    label = _path_label(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[dict[str, Any]] = []
    rng_modules = {"numpy", "torch", "random", "secrets"}
    call_prefixes = (
        "numpy.random.",
        "np.random.",
        "random.",
        "secrets.",
        "torch.rand",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = str(alias.name).split(".", 1)[0]
                if root in rng_modules:
                    hits.append({
                        "file": label,
                        "kind": "rng_framework_import",
                        "token": alias.name,
                        "lineno": int(node.lineno),
                    })
        elif isinstance(node, ast.ImportFrom):
            root = str(node.module or "").split(".", 1)[0]
            if root in rng_modules:
                hits.append({
                    "file": label,
                    "kind": "rng_framework_import",
                    "token": str(node.module),
                    "lineno": int(node.lineno),
                })
        elif isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if any(name.startswith(prefix) for prefix in call_prefixes):
                hits.append({
                    "file": label,
                    "kind": "rng_call_site",
                    "token": name,
                    "lineno": int(node.lineno),
                })
    return hits


def rng_audit(*, code_hash: str, run_id: str, scan_files: list[Path] | None = None) -> dict[str, Any]:
    files = sorted(scan_files) if scan_files is not None else sorted((ROOT / "scripts" / "ego_pet").glob("*.py"))
    forbidden_hits = []
    for path in files:
        forbidden_hits.extend(_rng_usage_hits(path))
    return {
        "producer_function": "rng_audit",
        "input_artifacts": [_path_label(p) for p in files],
        "run_id": run_id,
        "seed_ids": [],
        "aggregation_rule": "AST-level audit for RNG framework imports and call sites in all scanned pet files; detector literals are not executable usage",
        "code_path_hash": code_hash,
        "forbidden_hits": forbidden_hits,
        "status": "pass" if not forbidden_hits else "fail",
    }


def mem_path_report(*, run_id: str, code_hash: str) -> dict[str, Any]:
    report = run_poison_quarantine_probe()
    return {
        **report,
        "input_artifacts": ["scripts/ego_pet/memory_wiring.py", "scripts/ego_kernel/memory_substate.py"],
        "run_id": run_id,
        "seed_ids": [],
        "episode_ids": ["pet_mem_path_probe"],
        "aggregation_rule": "single positive-control poisoned suggestion through product input path must quarantine with zero unauthorized promotion",
        "code_path_hash": code_hash,
        "gate": "G-PET-MEM-PATH",
    }


def choose_verdict(hard: dict[str, Any], abl: dict[str, Any], replay: dict[str, Any], mem: dict[str, Any], rng: dict[str, Any]) -> tuple[str, list[str]]:
    failing = []
    for gate in (hard, abl, replay, mem, rng):
        if gate.get("status") not in {"pass", "not_evaluable_no_win"}:
            failing.append(str(gate.get("gate") or gate.get("producer_function")))
    if replay.get("status") != "pass":
        return "pet_integration_fail_G-PET-REPLAY", failing
    if mem.get("status") != "pass":
        return "pet_integration_fail_G-PET-MEM-PATH", failing
    if rng.get("status") != "pass":
        return "pet_integration_fail_unseeded_rng_audit", failing
    if hard.get("status") != "pass":
        return "pet_integration_pass_standin_shipped", failing or ["G-PET-HARD"]
    if abl.get("status") != "pass":
        return "pet_integration_fail_G-PET-ABLATION", failing
    return "pet_integration_p0_pass", failing


def flatten_trace_rows(runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for arm in ARMS:
        for seed in sorted(runs.get(arm, {}), key=lambda s: int(s)):
            rows.extend(runs[arm][seed]["trace_rows"])
    return rows


def run_battery(*, phase: str, out_dir: Path, seed: int | None = None) -> dict[str, Any]:
    started = time.process_time()
    config = load_world_config()
    code_hash = code_path_hash()
    if phase == "probe":
        if seed is None:
            seed = int(config["seed_sets"]["S_dev"][0])
        seeds = [int(seed)]
        run_id = f"{RUN_ID}_probe_seed_{seed}"
    elif phase == "scored":
        seeds = [int(x) for x in config["seed_sets"]["S_scored"]]
        run_id = f"{RUN_ID}_scored"
    else:
        raise ValueError(f"unsupported phase: {phase}")
    runs = run_arm_set(config, seeds, run_id=run_id)
    hard = baseline_comparison(runs, config, run_id=run_id, code_hash=code_hash)
    abl = ablation_report(runs, config, hard_report=hard, run_id=run_id, code_hash=code_hash)
    replay = replay_report(runs, repo_root=ROOT, run_id=run_id, code_hash=code_hash)
    mem = mem_path_report(run_id=run_id, code_hash=code_hash)
    rng = rng_audit(code_hash=code_hash, run_id=run_id)
    verdict, failing = choose_verdict(hard, abl, replay, mem, rng)
    if phase == "probe" and verdict == "pet_integration_p0_pass":
        verdict = "pet_integration_probe_clean"
    cpu_hours = (time.process_time() - started) / 3600.0
    projected = cpu_hours * 20.0 * float(config["cpu_budget"]["underestimate_correction_factor"]) if phase == "probe" else None
    result = {
        "producer_function": "run_battery",
        "phase": phase,
        "task": TASK_ID,
        "run_id": run_id,
        "claim_ceiling": CLAIM_CEILING,
        "code_path_hash": code_hash,
        "config_shas": _config_shas(),
        "seed_ids": seeds,
        "episode_ids": [_episode_id(arm, seed_value) for arm in ARMS for seed_value in seeds],
        "aggregation_rule": "P0 gate conjunction with carded downgrade on G-PET-HARD fail",
        "cpu": {
            "measured_cpu_hours": round(cpu_hours, 12),
            "projected_full_p0_cpu_hours": None if projected is None else round(projected, 12),
            "projection_rule": config["cpu_budget"]["probe_rule"],
            "line_cpu_hours": float(config["cpu_budget"]["full_P0_line_cpu_hours"]),
        },
        "gate_results": {
            "G-PET-HARD": hard,
            "G-PET-ABLATION": abl,
            "G-PET-REPLAY": replay,
            "G-PET-MEM-PATH": mem,
            "UNSEEDED-RNG-AUDIT": rng,
        },
        "verdict": verdict,
        "failing_gates": failing,
        "positive_claim_flag": phase == "scored" and verdict == "pet_integration_p0_pass",
        "what_this_does_not_prove": [
            "no EgoDesktop runtime wiring",
            "no P1 schema/static-gate audit",
            "no P2 live-session evidence",
            "no mechanism validity",
            "no autonomy agency emotion subjectivity consciousness or stable user benefit",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    if phase == "probe":
        write_json(out_dir / "probe_report.json", result)
        write_json(out_dir / "rng_audit_report.json", rng)
    else:
        write_json(out_dir / "result.json", result)
        write_json(out_dir / "baseline_comparison.json", hard)
        write_json(out_dir / "ablation_report.json", abl)
        write_json(out_dir / "replay_report.json", replay)
        write_json(out_dir / "memory_path_report.json", mem)
        write_json(out_dir / "rng_audit_report.json", rng)
        write_jsonl(out_dir / "trace.jsonl", flatten_trace_rows(runs))
        if failing:
            write_json(out_dir / "failure_manifest.json", {
                "producer_function": "failure_manifest",
                "verdict": verdict,
                "failing_gates": failing,
                "result_pointer": str((out_dir / "result.json").resolve().relative_to(ROOT.resolve())).replace("\\", "/"),
                "code_path_hash": code_hash,
            })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["probe", "scored"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--out-dir", type=Path, default=ARTIFACT_ROOT)
    parser.add_argument("--replay-stdin", action="store_true")
    args = parser.parse_args(argv)
    if args.replay_stdin:
        payload = json.loads(sys.stdin.read() or "{}")
        result = replay_episode(payload)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    if not args.phase:
        parser.error("--phase is required unless --replay-stdin is used")
    result = run_battery(phase=args.phase, out_dir=args.out_dir, seed=args.seed)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    if args.phase == "probe":
        projected = result["cpu"]["projected_full_p0_cpu_hours"]
        line = result["cpu"]["line_cpu_hours"]
        if projected is not None and projected > line:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
