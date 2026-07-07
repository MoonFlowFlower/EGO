from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.ego_kernel.probe_substate import (
    TASK_ID,
    build_probe_state,
    generate_observation_log,
    run_probe_episode,
)
from scripts.ego_kernel.replay import (
    compare_action_hash_sequences,
    replay_fresh_subprocess,
    replay_in_process,
)
from scripts.ego_kernel.state import canonical_sha256
from scripts.ego_kernel.trace import KERNEL_TRACE_SCHEMA_VERSION, write_jsonl
from scripts.ego_kernel.validation_gates import hygiene_gate, llm_swap_gate


RUN_ID = "ego_r0_kernel_state_substrate_001a_validation_v0"
CLAIM_CEILING = "kernel_substrate_engineering_only"
RUN_PLAN = {
    "task_id": TASK_ID,
    "run_id": RUN_ID,
    "episodes_per_seed": 3,
    "seeds": [11, 23],
    "ticks_per_episode": 300,
    "checkpoint_ticks": [0, 100, 200, 300],
    "trace_schema": KERNEL_TRACE_SCHEMA_VERSION,
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _artifact_ref(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _code_path_hash(repo_root: Path) -> str:
    paths = sorted((repo_root / "scripts" / "ego_kernel").glob("*.py"))
    paths.append(repo_root / "scripts" / "run_ego_kernel_substrate_validation.py")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(repo_root)).replace("\\", "/").encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
    return digest.hexdigest()


def _provenance(name: str, inputs: list[str], code_hash: str, episode_ids: list[str]) -> dict[str, Any]:
    return {
        "producer_function": name,
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context": {"seeds": RUN_PLAN["seeds"], "episode_ids": episode_ids},
        "aggregation_rule": "predeclared all-episodes gate; zero tolerance unless a floor is named in STAGE_CARD",
        "code_path_hash": code_hash,
    }


def _prepare_runs(repo_root: Path, out_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    runs = []
    fixture_paths = []
    for seed in RUN_PLAN["seeds"]:
        for episode_index in range(RUN_PLAN["episodes_per_seed"]):
            episode_id = f"seed_{seed}_episode_{episode_index}"
            observations = generate_observation_log(
                seed=seed,
                episode_index=episode_index,
                ticks=RUN_PLAN["ticks_per_episode"],
            )
            fixture_path = out_dir / "input_logs" / f"{episode_id}.json"
            _write_json(fixture_path, observations)
            initial = build_probe_state(seed=seed, run_id=RUN_ID, episode_id=episode_id)
            episode = run_probe_episode(
                initial,
                observations,
                checkpoint_ticks=set(RUN_PLAN["checkpoint_ticks"]),
            )
            trace_path = out_dir / "traces" / f"{episode_id}.jsonl"
            write_jsonl(trace_path, episode["trace_rows"])
            for tick, state in episode["checkpoints"].items():
                _write_json(out_dir / "checkpoints" / episode_id / f"tick_{tick}.json", state)
            runs.append({
                "seed": seed,
                "episode_index": episode_index,
                "episode_id": episode_id,
                "observations": observations,
                "fixture_path": _artifact_ref(repo_root, fixture_path),
                "trace_path": _artifact_ref(repo_root, trace_path),
                **episode,
            })
            fixture_paths.append(_artifact_ref(repo_root, fixture_path))
    return runs, fixture_paths


def _replay_gate(repo_root: Path, runs: list[dict[str, Any]], code_hash: str) -> dict[str, Any]:
    mismatches = []
    for run in runs:
        for repeat in range(2):
            fresh = replay_fresh_subprocess(
                initial_state=run["initial_state"],
                observations=run["observations"],
                repo_root=repo_root,
            )
            for mismatch in compare_action_hash_sequences(run["trace_rows"], fresh["trace_rows"]):
                mismatches.append({"episode_id": run["episode_id"], "mode": f"fresh_{repeat}", **mismatch})
        resumed = replay_in_process(
            initial_state=run["checkpoints"]["100"],
            observations=run["observations"][100:],
        )
        for mismatch in compare_action_hash_sequences(run["trace_rows"][100:], resumed["trace_rows"]):
            mismatches.append({"episode_id": run["episode_id"], "mode": "resume_100", **mismatch})
    episode_ids = [run["episode_id"] for run in runs]
    return {
        "gate": "G-R0-REPLAY",
        "status": "pass" if not mismatches else "fail",
        "fresh_subprocess_runs_per_episode": 2,
        "mismatches_total": len(mismatches),
        "mismatches": mismatches[:20],
        **_provenance("_replay_gate", [run["fixture_path"] for run in runs], code_hash, episode_ids),
    }


def _rate(rows: list[dict[str, Any]], option: int) -> float:
    return sum(1 for row in rows if row["action"]["option"] == option) / float(len(rows))


def _causality_gate(out_dir: Path, code_hash: str) -> dict[str, Any]:
    observations = generate_observation_log(seed=11, episode_index=0, ticks=RUN_PLAN["ticks_per_episode"])
    left = run_probe_episode(build_probe_state(seed=11, run_id=RUN_ID, episode_id="causal_left", pref_bias=0), observations)
    right = run_probe_episode(build_probe_state(seed=11, run_id=RUN_ID, episode_id="causal_right", pref_bias=3), observations)
    zeroed = run_probe_episode(
        build_probe_state(seed=11, run_id=RUN_ID, episode_id="causal_zeroed", pref_bias=0, ablations={
            "pref_ema": "zeroed",
            "counter": "live",
            "noise_user": "live",
        }),
        observations,
    )
    pairwise_diff = sum(
        1 for lrow, rrow in zip(left["trace_rows"], right["trace_rows"])
        if lrow["action"]["option"] != rrow["action"]["option"]
    ) / float(len(observations))
    zeroed_agreement = sum(
        1 for lrow, zrow in zip(left["trace_rows"], zeroed["trace_rows"])
        if lrow["action"]["option"] == zrow["action"]["option"]
    ) / float(len(observations))
    left_agree = _rate(left["trace_rows"], 0)
    right_agree = _rate(right["trace_rows"], 3)
    passed = min(left_agree, right_agree) >= 0.90 and pairwise_diff >= 0.50 and zeroed_agreement <= 0.40
    report = {
        "gate": "G-R0-CAUSALITY",
        "status": "pass" if passed else "fail",
        "left_direction_agreement": left_agree,
        "right_direction_agreement": right_agree,
        "min_direction_agreement": min(left_agree, right_agree),
        "pairwise_difference_rate": pairwise_diff,
        "zeroed_agreement_with_original": zeroed_agreement,
        **_provenance("_causality_gate", [], code_hash, ["causal_left", "causal_right", "causal_zeroed"]),
    }
    _write_json(out_dir / "causality_traces" / "left.json", left["trace_rows"])
    _write_json(out_dir / "causality_traces" / "right.json", right["trace_rows"])
    _write_json(out_dir / "causality_traces" / "zeroed.json", zeroed["trace_rows"])
    return report


def _seed_negctrl_gate(repo_root: Path, run: dict[str, Any], code_hash: str) -> dict[str, Any]:
    perturbed = json.loads(json.dumps(run["initial_state"]))
    perturbed["seed_registry"]["noise_user"]["seed"] += 1
    perturbed_replay = replay_fresh_subprocess(initial_state=perturbed, observations=run["observations"], repo_root=repo_root)
    perturbed_mismatches = compare_action_hash_sequences(run["trace_rows"], perturbed_replay["trace_rows"])
    missing = json.loads(json.dumps(run["initial_state"]))
    missing["seed_registry"].pop("noise_user")
    a = replay_fresh_subprocess(initial_state=missing, observations=run["observations"], repo_root=repo_root, allow_unregistered_seed=True)
    b = replay_fresh_subprocess(initial_state=missing, observations=run["observations"], repo_root=repo_root, allow_unregistered_seed=True)
    missing_mismatches = compare_action_hash_sequences(a["trace_rows"], b["trace_rows"])
    status = "pass" if perturbed_mismatches and missing_mismatches else "fail"
    return {
        "gate": "G-R0-SEED-NEGCTRL",
        "status": status,
        "perturbed_seed_detected": bool(perturbed_mismatches),
        "perturbed_seed_mismatch_count": len(perturbed_mismatches),
        "missing_registry_nondeterminism_detected": bool(missing_mismatches),
        "missing_registry_mismatch_count": len(missing_mismatches),
        **_provenance("_seed_negctrl_gate", [run["fixture_path"]], code_hash, [run["episode_id"]]),
    }


def _verdict(gates: dict[str, dict[str, Any]]) -> str:
    if gates["G-R0-SEED-NEGCTRL"]["status"] != "pass":
        return "instrument_invalid_seed_detector_blind"
    for name in ("G-R0-REPLAY", "G-R0-CAUSALITY", "G-R0-LLMSWAP-HARNESS", "HYGIENE"):
        if gates[name]["status"] != "pass":
            return f"r0_substrate_fail_{name.lower().replace('g-r0-', '').replace('-', '_')}"
    return "r0_substrate_pass"
def run_validation(*, repo_root: Path, out_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    code_hash = _code_path_hash(repo_root)
    config = {**RUN_PLAN, "config_hash": canonical_sha256(RUN_PLAN), "code_path_hash": code_hash}
    _write_json(out_dir / "config_frozen.json", config)
    runs, _fixture_paths = _prepare_runs(repo_root, out_dir)
    gates = {
        "G-R0-REPLAY": _replay_gate(repo_root, runs, code_hash),
        "G-R0-CAUSALITY": _causality_gate(out_dir, code_hash),
        "G-R0-SEED-NEGCTRL": _seed_negctrl_gate(repo_root, runs[0], code_hash),
        "G-R0-LLMSWAP-HARNESS": llm_swap_gate(code_hash, RUN_PLAN, RUN_ID, _provenance),
        "HYGIENE": hygiene_gate(repo_root, code_hash, _provenance),
    }
    verdict = _verdict(gates)
    result = {"verdict": verdict, "claim_ceiling": CLAIM_CEILING, "config_hash": config["config_hash"], "gate_results": gates}
    _write_json(out_dir / "replay_report.json", gates["G-R0-REPLAY"])
    _write_json(out_dir / "state_causality_report.json", gates["G-R0-CAUSALITY"])
    _write_json(out_dir / "seed_negctrl_report.json", gates["G-R0-SEED-NEGCTRL"])
    _write_json(out_dir / "llm_swap_harness_report.json", gates["G-R0-LLMSWAP-HARNESS"])
    _write_json(out_dir / "result.json", result)
    if verdict != "r0_substrate_pass":
        _write_json(out_dir / "failure_manifest.json", result)
    return result
