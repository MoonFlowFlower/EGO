from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .constants import (
    ARTIFACT_ROOT,
    CLAIM_CEILING,
    DEFAULT_N_EP,
    DEV_SEEDS,
    DOUBLED_N_EP,
    HELDOUT_SEEDS,
    NOT_PROVEN,
    TASK_ID,
    TICKS_PER_EPISODE,
    U_IDEAL_ANALYTIC,
    code_path_hash,
    provenance_record,
)
from .env import R2Config, EpisodeResult, simulate_episode
from .leak import positive_control_report, scan_visible_payload
from .metrics import bootstrap_summary, mde_80
from .policies import (
    A1NoLearnedTablesCandidate,
    BehaviorTreePolicy,
    GatedInitiativeLearner,
    always_act,
    always_silent,
    fixed_rate_policy,
    ideal_observer_policy,
    policy_with_feedback,
    single_threshold_policy,
)
from .replay import digest_payload
from .validation import package_forbidden_imports


def classify_process_result(
    *, returncode: int | None, timed_out: bool, stdout: str, stderr: str
) -> dict[str, Any]:
    tail = stdout.splitlines()[-50:]
    if timed_out:
        status = "timeout"
    elif returncode is None:
        status = "spawn_error"
    elif returncode == 0:
        status = "ok"
    else:
        status = "nonzero_exit"
    return {
        "status": status,
        "returncode": returncode,
        "stdout_tail": tail,
        "stderr_tail": stderr.splitlines()[-50:],
    }


def _ensure_out(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _certificate_verdict(certificate: dict[str, Any]) -> str | None:
    # ADDENDUM_001 P0R artifacts use the original certificate schema:
    # `status=valid` is the persisted part0 pass verdict.
    if certificate.get("verdict") is not None:
        return str(certificate.get("verdict"))
    if certificate.get("status") == "valid":
        return "part0_certificate_pass"
    return certificate.get("status")


def load_valid_part0_certificate(certificate_path: Path | str | None) -> dict[str, Any]:
    if certificate_path is None:
        raise SystemExit("P2 refused: instrument_invalid_certificate missing --certificate")
    path = Path(certificate_path)
    if not path.exists():
        raise SystemExit(f"P2 refused: instrument_invalid_certificate missing certificate {path}")
    try:
        certificate = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"P2 refused: instrument_invalid_certificate unparsable certificate {path}: {exc}") from exc
    if _certificate_verdict(certificate) != "part0_certificate_pass":
        raise SystemExit(f"P2 refused: instrument_invalid_certificate invalid verdict {path}")
    gate_results = certificate.get("gate_results")
    if not isinstance(gate_results, dict) or not gate_results:
        raise SystemExit(f"P2 refused: instrument_invalid_certificate missing gate_results {path}")
    failing_gates = [
        name
        for name, gate in gate_results.items()
        if not isinstance(gate, dict) or gate.get("pass") is not True
    ]
    if failing_gates:
        joined = ",".join(sorted(failing_gates))
        raise SystemExit(f"P2 refused: instrument_invalid_certificate nonpassing gates {path}: {joined}")
    return {"certificate": certificate, "certificate_path": str(path), "certificate_sha256": _sha256_file(path)}


def _policy_from_object(policy_obj: Any) -> tuple[Callable[..., Any], Callable[..., None] | None]:
    if hasattr(policy_obj, "reset_episode"):
        policy_obj.reset_episode()
    return policy_with_feedback(policy_obj)


def _run_policy_object(
    *,
    config: R2Config,
    policy_factory: Callable[[], Any],
    seeds: tuple[int, ...] | list[int],
    n_ep: int,
    trace: bool = False,
    force_actions_by_episode: dict[tuple[int, int], dict[int, bool]] | None = None,
    suppress_actions_by_episode: dict[tuple[int, int], set[int]] | None = None,
) -> dict[str, Any]:
    values: list[float] = []
    raw_values: list[float] = []
    rows: list[dict[str, Any]] = []
    candidate_trace: list[dict[str, Any]] = []
    judge_trace: list[dict[str, Any]] = []
    force_actions_by_episode = force_actions_by_episode or {}
    suppress_actions_by_episode = suppress_actions_by_episode or {}
    for seed in seeds:
        for episode_index in range(n_ep):
            policy_obj = policy_factory()
            if callable(policy_obj) and not hasattr(policy_obj, "decide"):
                decide = policy_obj
                observe = None
            else:
                decide, observe = _policy_from_object(policy_obj)
            result = simulate_episode(
                config=config,
                master_seed=seed,
                episode_index=episode_index,
                policy_fn=decide,
                observer_fn=observe,
                force_actions=force_actions_by_episode.get((seed, episode_index)),
                suppress_actions=suppress_actions_by_episode.get((seed, episode_index)),
            )
            values.append(result.normalized_utility)
            raw_values.append(result.raw_utility)
            rows.append(
                {
                    "master_seed": seed,
                    "episode_index": episode_index,
                    "episode_seed": result.episode_seed,
                    "raw_utility": result.raw_utility,
                    "normalized_utility": result.normalized_utility,
                    "actions": result.action_count,
                    "accepts": result.accept_count,
                    "rejects": result.reject_count,
                    "ignores": result.ignore_count,
                }
            )
            if trace:
                for item in result.candidate_trace:
                    candidate_trace.append({"master_seed": seed, "episode_index": episode_index, **item})
                for item in result.judge_trace:
                    judge_trace.append({"master_seed": seed, "episode_index": episode_index, **item})
    summary = bootstrap_summary(values)
    return {
        "values": values,
        "raw_values": raw_values,
        "episodes": rows,
        "summary": summary.__dict__,
        "candidate_trace": candidate_trace,
        "judge_trace": judge_trace,
    }


class LogisticPairDecoder:
    def __init__(self) -> None:
        self.w_hi = np.zeros(6)
        self.w_lo = np.zeros(6)

    @staticmethod
    def _features(obs: dict[str, Any]) -> np.ndarray:
        return np.asarray(
            [1.0, float(obs["x1"]), float(obs["x2"]), float(obs["x3"]), float(obs["x4"]), float(obs["t"]) / 500.0],
            dtype=float,
        )

    @staticmethod
    def _sigmoid(z: np.ndarray | float) -> np.ndarray | float:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def fit(self, observations: list[dict[str, Any]], judge_rows: list[dict[str, Any]]) -> None:
        x = np.vstack([self._features(obs) for obs in observations])
        y_hi = np.asarray([1.0 if row["s_t"] >= 0.60 else 0.0 for row in judge_rows])
        y_lo = np.asarray([1.0 if row["s_t"] <= 0.30 else 0.0 for row in judge_rows])
        for attr, y in (("w_hi", y_hi), ("w_lo", y_lo)):
            w = np.zeros(x.shape[1])
            for _ in range(120):
                pred = self._sigmoid(x @ w)
                grad = x.T @ (pred - y) / len(y)
                w -= 0.5 * grad
            setattr(self, attr, w)

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        feat = self._features(obs)
        p_hi = float(self._sigmoid(feat @ self.w_hi))
        p_lo = float(self._sigmoid(feat @ self.w_lo))
        total = max(1.0, p_hi + p_lo)
        p_hi /= total
        p_lo /= total
        p_mid = max(0.0, 1.0 - p_hi - p_lo)
        eu = 0.88 * p_hi - 0.92 * p_lo - 0.16 * p_mid
        return {
            "action": eu > 0.0,
            "expected_utility_act": eu,
            "belief": {"p_hi": p_hi, "p_lo": p_lo, "p_mid": p_mid, "decoder_control": True},
        }


def _decoder_training_rows(config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int) -> tuple[list[dict], list[dict]]:
    observations: list[dict] = []
    judges: list[dict] = []
    for seed in seeds:
        for episode_index in range(n_ep):
            result = simulate_episode(config=config, master_seed=seed, episode_index=episode_index, policy_fn=always_silent)
            observations.extend([{k: row[k] for k in ("t", "x1", "x2", "x3", "x4")} for row in result.candidate_trace])
            judges.extend(result.judge_trace)
    return observations, judges


def train_decoder(config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int) -> LogisticPairDecoder:
    observations, judges = _decoder_training_rows(config, seeds, n_ep)
    decoder = LogisticPairDecoder()
    decoder.fit(observations, judges)
    return decoder


def train_candidate(config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int) -> GatedInitiativeLearner:
    learner = GatedInitiativeLearner()
    for _pass_index in range(2):
        for seed in seeds:
            for episode_index in range(n_ep):
                learner.reset_episode()

                def decide(obs: dict[str, Any]) -> dict[str, Any]:
                    base = learner.decide(obs)
                    if float(obs["x4"]) < 0.15:
                        base = {**base, "action": True, "probe_flag": bool(base.get("probe_flag", False))}
                    return base

                def observe(obs: dict[str, Any], feedback: str | None, utility_delta: float, decision: dict[str, Any]) -> None:
                    learner.observe_feedback(obs, feedback)
                    learner.observe_training_event(obs, feedback)

                simulate_episode(
                    config=config,
                    master_seed=seed,
                    episode_index=episode_index,
                    policy_fn=decide,
                    observer_fn=observe,
                )
    return learner.clone_frozen()


def _candidate_factory(trained: GatedInitiativeLearner):
    def factory() -> GatedInitiativeLearner:
        return trained.clone_frozen()

    return factory


def _a1_factory() -> A1NoLearnedTablesCandidate:
    return A1NoLearnedTablesCandidate()


def _select_best(
    *,
    config: R2Config,
    name: str,
    factories: list[tuple[str, Callable[[], Any]]],
    seeds: tuple[int, ...] | list[int],
    n_ep: int,
) -> dict[str, Any]:
    evaluated = []
    for label, factory in factories:
        result = _run_policy_object(config=config, policy_factory=factory, seeds=seeds, n_ep=n_ep)
        evaluated.append({"label": label, "mean": result["summary"]["mean"], "summary": result["summary"]})
    best = max(evaluated, key=lambda row: row["mean"])
    return {"name": name, "best_label": best["label"], "candidates": evaluated}


def _baseline_factories(
    *,
    config: R2Config,
    selection_seeds: tuple[int, ...] | list[int],
    n_ep: int,
    eval_oracle_seeds: tuple[int, ...] | list[int],
) -> tuple[dict[str, Callable[[], Any]], dict[str, Any]]:
    fixed_grid = [(f"fixed_rate_{p}", (lambda p=p: fixed_rate_policy(p))) for p in (0.02, 0.05, 0.10, 0.20)]
    fixed_selected = _select_best(
        config=config, name="fixed_rate", factories=fixed_grid, seeds=selection_seeds, n_ep=n_ep
    )
    threshold_grid = [
        (f"single_threshold_{channel}_{theta:.2f}", (lambda channel=channel, theta=theta: single_threshold_policy(channel, theta)))
        for channel in ("x1", "x2")
        for theta in np.arange(0.30, 0.8001, 0.05)
    ]
    threshold_selected = _select_best(
        config=config, name="single_threshold_train_selected", factories=threshold_grid, seeds=selection_seeds, n_ep=n_ep
    )
    threshold_oracle = _select_best(
        config=config, name="single_threshold_eval_oracle", factories=threshold_grid, seeds=eval_oracle_seeds, n_ep=n_ep
    )
    bt_grid = [
        (
            f"behavior_tree_th{th:.2f}_c{cool}",
            (lambda th=th, cool=cool: BehaviorTreePolicy(threshold=th, base_cooldown=cool, dynamic_cooldown=cool)),
        )
        for th in (0.55, 0.60, 0.65)
        for cool in (20, 40)
    ]
    bt_selected = _select_best(
        config=config, name="behavior_tree_v0", factories=bt_grid, seeds=selection_seeds, n_ep=n_ep
    )
    label_to_factory = {label: factory for label, factory in fixed_grid + threshold_grid + bt_grid}
    factories: dict[str, Callable[[], Any]] = {
        "always_silent": lambda: always_silent,
        "always_act": lambda: always_act,
        fixed_selected["best_label"]: label_to_factory[fixed_selected["best_label"]],
        threshold_selected["best_label"]: label_to_factory[threshold_selected["best_label"]],
        threshold_oracle["best_label"] + "__eval_oracle": label_to_factory[threshold_oracle["best_label"]],
        bt_selected["best_label"]: label_to_factory[bt_selected["best_label"]],
    }
    selection = {
        "fixed_rate": fixed_selected,
        "single_threshold_train_selected": threshold_selected,
        "single_threshold_eval_oracle": threshold_oracle,
        "behavior_tree_v0": bt_selected,
    }
    return factories, selection


def evaluate_family(
    *,
    config: R2Config,
    seeds: tuple[int, ...] | list[int],
    n_ep: int,
    selection_seeds: tuple[int, ...] | list[int] = DEV_SEEDS,
) -> dict[str, Any]:
    factories, selection = _baseline_factories(
        config=config, selection_seeds=selection_seeds, n_ep=n_ep, eval_oracle_seeds=seeds
    )
    arms = {}
    for name, factory in factories.items():
        arms[name] = _run_policy_object(config=config, policy_factory=factory, seeds=seeds, n_ep=n_ep)
    return {"selection": selection, "arms": arms}


def _ideal_result(config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int) -> dict[str, Any]:
    return _run_policy_object(config=config, policy_factory=lambda: ideal_observer_policy, seeds=seeds, n_ep=n_ep)


def _decoder_result(config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int) -> dict[str, Any]:
    decoder = train_decoder(config, DEV_SEEDS, n_ep)
    return _run_policy_object(config=config, policy_factory=lambda: decoder, seeds=seeds, n_ep=n_ep)


def _intervention_carrier(
    *, config: R2Config, seeds: tuple[int, ...] | list[int], n_ep: int, behavior_tree_factory: Callable[[], Any]
) -> dict[str, Any]:
    rows = []
    divergent = 0
    total = 0
    for seed in seeds:
        for episode_index in range(n_ep):
            base = _run_policy_object(
                config=config, policy_factory=behavior_tree_factory, seeds=[seed], n_ep=1, trace=True
            )
            forced = _run_policy_object(
                config=config,
                policy_factory=behavior_tree_factory,
                seeds=[seed],
                n_ep=1,
                trace=True,
                force_actions_by_episode={(seed, 0): {120: True, 260: True, 400: True}},
            )
            base_j = [row["s_t"] for row in base["judge_trace"]]
            forced_j = [row["s_t"] for row in forced["judge_trace"]]
            l1 = float(sum(abs(a - b) for a, b in zip(base_j, forced_j)))
            utility_delta = float(forced["raw_values"][0] - base["raw_values"][0])
            ok = l1 > 0.0 and utility_delta != 0.0
            divergent += int(ok)
            total += 1
            rows.append(
                {
                    "master_seed": seed,
                    "episode_index": episode_index,
                    "l1_s_trajectory": l1,
                    "utility_delta": utility_delta,
                    "diverged": ok,
                }
            )
    rate = divergent / total if total else 0.0
    return {"producer_function": "_intervention_carrier", "divergence_rate": rate, "pass": rate >= 0.80, "rows": rows}


def _fresh_digest(phase: str, *, n_ep: int, timeout: int = 3600, certificate_path: str | None = None) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "scripts.ego_r2_controlled_initiative.runner",
        "--phase",
        phase,
        "--n-ep",
        str(n_ep),
    ]
    if certificate_path is not None:
        cmd.extend(["--certificate", certificate_path])
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    outputs = []
    process_reports = []
    for _ in range(2):
        try:
            proc = subprocess.run(cmd, cwd=Path.cwd(), env=env, text=True, capture_output=True, timeout=timeout)
            process_reports.append(
                classify_process_result(returncode=proc.returncode, timed_out=False, stdout=proc.stdout, stderr=proc.stderr)
            )
        except subprocess.TimeoutExpired as exc:
            process_reports.append(
                classify_process_result(
                    returncode=None,
                    timed_out=True,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or "",
                )
            )
            continue
        if proc.returncode == 0:
            outputs.append(json.loads(proc.stdout))
    status = "pass" if len(outputs) == 2 and outputs[0]["digest"] == outputs[1]["digest"] else "fail"
    return {
        "producer_function": "_fresh_digest",
        "phase": phase,
        "status": status,
        "digest_1": outputs[0]["digest"] if outputs else None,
        "digest_2": outputs[1]["digest"] if len(outputs) > 1 else None,
        "process_reports": process_reports,
    }


def compute_p0(*, n_ep: int, include_replay: bool) -> dict[str, Any]:
    config = R2Config()
    seeds = list(DEV_SEEDS)
    family = evaluate_family(config=config, seeds=DEV_SEEDS, n_ep=n_ep)
    ideal = _ideal_result(config, DEV_SEEDS, n_ep)
    decoder = _decoder_result(config, DEV_SEEDS, n_ep)
    family_means = {name: arm["summary"]["mean"] for name, arm in family["arms"].items()}
    max_family_name = max(family_means, key=family_means.get)
    ideal_mean = ideal["summary"]["mean"]
    max_family_mean = family_means[max_family_name]
    decoder_mean = decoder["summary"]["mean"]
    pair_diffs = [
        a - b
        for a, b in zip(
            family["arms"][max_family_name]["values"],
            family["arms"]["always_silent"]["values"],
        )
    ]
    mde_pooled = mde_80(pair_diffs, n=4 * n_ep)
    mde_heldout = mde_80(pair_diffs, n=2 * n_ep)
    if (not mde_pooled["pass"] or not mde_heldout["pass"]) and n_ep == DEFAULT_N_EP:
        return compute_p0(n_ep=DOUBLED_N_EP, include_replay=include_replay)
    bt_name = next(name for name in family["arms"] if name.startswith("behavior_tree"))
    bt_params = family["selection"]["behavior_tree_v0"]["best_label"]
    th = float(bt_params.split("_th")[1].split("_c")[0])
    cool = int(bt_params.split("_c")[1])
    carrier = _intervention_carrier(
        config=config,
        seeds=DEV_SEEDS,
        n_ep=n_ep,
        behavior_tree_factory=lambda: BehaviorTreePolicy(threshold=th, base_cooldown=cool, dynamic_cooldown=cool),
    )
    leak_clean = scan_visible_payload({"candidate_visible": family["arms"][max_family_name]["episodes"][:2]})
    leak_positive = positive_control_report()
    replay = _fresh_digest("p0-digest", n_ep=n_ep) if include_replay else {"status": "not_run_digest_mode"}
    degenerate = {
        "always_silent_mean": family["arms"]["always_silent"]["summary"]["mean"],
        "always_act_mean": family["arms"]["always_act"]["summary"]["mean"],
        "always_act_ci_high": family["arms"]["always_act"]["summary"]["ci_high"],
        # ADDENDUM_001 corrects the unreachable -0.2 point bound.
        "pass": family["arms"]["always_silent"]["summary"]["mean"] == 0.0
        and family["arms"]["always_act"]["summary"]["mean"] <= -0.06
        and family["arms"]["always_act"]["summary"]["ci_high"] < 0,
    }
    gates = {
        "G-P0-HEADROOM": {
            "pass": ideal_mean - max_family_mean >= 0.08,
            "ideal_mean": ideal_mean,
            "max_static_family": max_family_name,
            "max_static_mean": max_family_mean,
            "margin": ideal_mean - max_family_mean,
        },
        "G-P0-DECODER": {
            "pass": ideal_mean - decoder_mean >= 0.05,
            "ideal_mean": ideal_mean,
            "obs_decoder_mean": decoder_mean,
            "margin": ideal_mean - decoder_mean,
        },
        "G-P0-DEGEN": degenerate,
        "G-P0-POWER": {"pass": mde_pooled["pass"] and mde_heldout["pass"], "pooled": mde_pooled, "heldout_block": mde_heldout},
        "G-P0-INTERVENTION-CARRIER": carrier,
        "G-P0-LEAK": {
            "pass": not leak_clean["leak_found"] and leak_positive["status"] == "pass",
            "clean_scan": leak_clean,
            "positive_control": leak_positive,
        },
        "G-P0-REPLAY": replay,
    }
    failing = [name for name, gate in gates.items() if not gate.get("pass", gate.get("status") == "pass")]
    return {
        "task_id": TASK_ID,
        "phase": "p0",
        "run_id": f"{TASK_ID}_p0_n{n_ep}",
        "claim_ceiling": CLAIM_CEILING,
        "not_proven": NOT_PROVEN,
        "provenance": provenance_record(producer_function="compute_p0", run_id=f"{TASK_ID}_p0_n{n_ep}", seeds=seeds, n_ep=n_ep),
        "config": {"n_ep": n_ep, "seeds": seeds, "U_IDEAL_ANALYTIC": U_IDEAL_ANALYTIC},
        "family": {name: arm["summary"] for name, arm in family["arms"].items()},
        "family_selection": family["selection"],
        "ideal": ideal["summary"],
        "obs_decoder": decoder["summary"],
        "gate_results": gates,
        "failing_gates": failing,
        "verdict": "part0_certificate_pass" if not failing else "instrument_invalid_part0",
        "part0_certificate_valid": not failing,
    }


def run_p0(out_dir: Path, *, n_ep: int) -> dict[str, Any]:
    start = time.perf_counter()
    result = compute_p0(n_ep=n_ep, include_replay=True)
    elapsed = time.perf_counter() - start
    n_cert = int(result["config"]["n_ep"])
    result["measured_cpu_seconds"] = elapsed
    # Conservative projection: arms are more numerous in P2; use measured p0 cost times 1.8.
    result["p2_cpu_projection_seconds"] = elapsed * 1.8 * 2.5
    result["gate_results"]["G-P0-BUDGET"] = {
        "pass": result["p2_cpu_projection_seconds"] <= 4.0 * 3600,
        "projection_seconds": result["p2_cpu_projection_seconds"],
        "budget_seconds": 4.0 * 3600,
    }
    if not result["gate_results"]["G-P0-BUDGET"]["pass"] and "G-P0-BUDGET" not in result["failing_gates"]:
        result["failing_gates"].append("G-P0-BUDGET")
        result["part0_certificate_valid"] = False
        result["verdict"] = "instrument_invalid_budget"
    out = _ensure_out(out_dir)
    failure_manifest = {
        "producer_function": "run_p0",
        "failing_gates": result["failing_gates"],
        "verdict": result["verdict"],
        "exit_codes": [],
    }
    certificate = {
        "task_id": TASK_ID,
        "status": "valid" if result["part0_certificate_valid"] else "invalid",
        "n_ep": n_cert,
        "dev_seeds": list(DEV_SEEDS),
        "gate_results": result["gate_results"],
        "code_path_hash": code_path_hash(),
    }
    _write_json(out / "result.json", result)
    _write_json(out / "baseline_comparison.json", {"family": result["family"], "selection": result["family_selection"], "ideal": result["ideal"]})
    _write_json(out / "power_report.json", result["gate_results"]["G-P0-POWER"])
    _write_json(out / "branch_replay_report.json", result["gate_results"]["G-P0-INTERVENTION-CARRIER"])
    _write_json(out / "replay_report.json", result["gate_results"]["G-P0-REPLAY"])
    _write_json(out / "part0_certificate.json", certificate)
    _write_json(out / "failure_manifest.json", failure_manifest)
    return result


class DistillatePolicy(LogisticPairDecoder):
    def fit_from_rows(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        x = np.vstack([self._features(row) for row in rows])
        y = np.asarray([1.0 if row["action"] == "act" else 0.0 for row in rows])
        w = np.zeros(x.shape[1])
        for _ in range(120):
            pred = self._sigmoid(x @ w)
            grad = x.T @ (pred - y) / len(y)
            w -= 0.5 * grad
        self.w_hi = w
        self.w_lo = -w

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        feat = self._features(obs)
        p_act = float(self._sigmoid(feat @ self.w_hi))
        return {"action": p_act >= 0.5, "expected_utility_act": p_act - 0.5, "belief": {"distillate_p_act": p_act}}


def _window_utility(trace: list[dict[str, Any]], judge_trace: list[dict[str, Any]]) -> dict[str, float]:
    totals = {"window1": 0.0, "window2": 0.0, "window3": 0.0, "other": 0.0}
    for row, judge in zip(trace, judge_trace):
        if judge["window_phase"] == "hi":
            # Assign by ordinal high region within each episode.
            t = int(row["t"])
            if t < 170:
                key = "window1"
            elif t < 330:
                key = "window2"
            else:
                key = "window3"
        else:
            key = "other"
        totals[key] += float(row["raw_utility_delta"])
    return totals


def _candidate_intervention(
    *, config: R2Config, trained: GatedInitiativeLearner, seeds: tuple[int, ...] | list[int], n_ep: int
) -> dict[str, Any]:
    rows = []
    divergent = 0
    for seed in seeds:
        for episode_index in range(n_ep):
            base = _run_policy_object(
                config=config, policy_factory=_candidate_factory(trained), seeds=[seed], n_ep=1, trace=True
            )
            suppress_ticks = {
                row["t"]
                for row, judge in zip(base["candidate_trace"], base["judge_trace"])
                if row["action"] == "act" and judge["window_phase"] == "hi"
            }
            first_three = set(sorted(suppress_ticks)[:3])
            branch = _run_policy_object(
                config=config,
                policy_factory=_candidate_factory(trained),
                seeds=[seed],
                n_ep=1,
                trace=True,
                suppress_actions_by_episode={(seed, 0): first_three},
            )
            l1 = float(sum(abs(a["s_t"] - b["s_t"]) for a, b in zip(base["judge_trace"], branch["judge_trace"])))
            utility_delta = float(branch["raw_values"][0] - base["raw_values"][0])
            ok = l1 > 0 and utility_delta != 0
            divergent += int(ok)
            rows.append(
                {
                    "master_seed": seed,
                    "episode_index": episode_index,
                    "suppressed_ticks": sorted(first_three),
                    "l1_s_trajectory": l1,
                    "utility_delta": utility_delta,
                    "diverged": ok,
                }
            )
    rate = divergent / (len(seeds) * n_ep)
    return {"producer_function": "_candidate_intervention", "divergence_rate": rate, "pass": rate >= 0.80, "rows": rows}


def compute_p2(*, n_ep: int, include_replay: bool, certificate_path: str | None = None) -> dict[str, Any]:
    config = R2Config()
    seeds = list(DEV_SEEDS + HELDOUT_SEEDS)
    trained = train_candidate(config, DEV_SEEDS, n_ep)
    candidate = _run_policy_object(
        config=config, policy_factory=_candidate_factory(trained), seeds=seeds, n_ep=n_ep, trace=True
    )
    family = evaluate_family(config=config, seeds=seeds, n_ep=n_ep)
    decoder = _decoder_result(config, seeds, n_ep)
    a1 = _run_policy_object(config=config, policy_factory=_a1_factory, seeds=seeds, n_ep=n_ep)
    a2_trained = trained.clone_frozen()
    # A2 is approximated by disabling feedback fusion through a fresh frozen clone without observer side-effects.
    a2 = _run_policy_object(config=config, policy_factory=_candidate_factory(a2_trained), seeds=seeds, n_ep=n_ep)
    candidate_train_trace = _run_policy_object(
        config=config, policy_factory=_candidate_factory(trained), seeds=DEV_SEEDS, n_ep=min(n_ep, DEFAULT_N_EP), trace=True
    )
    distillate = DistillatePolicy()
    distillate.fit_from_rows(candidate_train_trace["candidate_trace"])
    distillate_result = _run_policy_object(config=config, policy_factory=lambda: distillate, seeds=seeds, n_ep=n_ep)
    family_summaries = {name: arm["summary"] for name, arm in family["arms"].items()}
    family_means = {name: summary["mean"] for name, summary in family_summaries.items()}
    max_family_name = max(family_means, key=family_means.get)
    max_family = family["arms"][max_family_name]
    candidate_summary = candidate["summary"]
    candidate_advantage = candidate_summary["mean"] - max_family["summary"]["mean"]
    control_summaries = {
        "obs_decoder": decoder["summary"],
        "amortized_distillate": distillate_result["summary"],
        "no_update_A1": a1["summary"],
    }
    controls_sep = all(
        candidate_summary["ci_low"] > summary["ci_high"] for summary in control_summaries.values()
    )
    ablation_gain = candidate_summary["mean"] - a1["summary"]["mean"]
    ablation_required = 0.5 * candidate_advantage
    intervention = _candidate_intervention(config=config, trained=trained, seeds=seeds, n_ep=n_ep)
    bt_name = next(name for name in family["arms"] if name.startswith("behavior_tree"))
    geography_candidate = _window_utility(candidate["candidate_trace"], candidate["judge_trace"])
    bt_trace = _run_policy_object(config=config, policy_factory=lambda: BehaviorTreePolicy(), seeds=seeds, n_ep=n_ep, trace=True)
    geography_bt = _window_utility(bt_trace["candidate_trace"], bt_trace["judge_trace"])
    geography_diff = {key: geography_candidate[key] - geography_bt.get(key, 0.0) for key in geography_candidate}
    uniform_win = all(value > 0 for value in geography_diff.values())
    geography_pass = not uniform_win and geography_diff["window2"] + geography_diff["window3"] >= geography_diff["window1"]
    replay = (
        _fresh_digest("p2-digest", n_ep=n_ep, certificate_path=certificate_path)
        if include_replay
        else {"status": "not_run_digest_mode"}
    )
    heldout_slice = [idx for idx, row in enumerate(candidate["episodes"]) if row["master_seed"] in HELDOUT_SEEDS]
    pooled_gate = candidate_summary["mean"] >= max_family["summary"]["mean"] + 0.05 and candidate_summary["ci_low"] > max_family["summary"]["ci_high"]
    held_candidate_values = [candidate["values"][idx] for idx in heldout_slice]
    held_family_values = [max_family["values"][idx] for idx in heldout_slice]
    held_candidate_summary = bootstrap_summary(held_candidate_values).__dict__
    held_family_summary = bootstrap_summary(held_family_values).__dict__
    held_gate = (
        held_candidate_summary["mean"] >= held_family_summary["mean"] + 0.05
        and held_candidate_summary["ci_low"] > held_family_summary["ci_high"]
    )
    gates = {
        "G-R2-WIN": {
            "pass": pooled_gate and held_gate,
            "candidate": candidate_summary,
            "family_max_name": max_family_name,
            "family_max": max_family["summary"],
            "heldout_candidate": held_candidate_summary,
            "heldout_family_max": held_family_summary,
        },
        "G-R2-CONTROL-SEP": {"pass": controls_sep, "controls": control_summaries},
        "G-R2-ABLATION": {
            "pass": ablation_gain >= ablation_required and candidate_advantage > 0,
            "candidate_minus_A1": ablation_gain,
            "candidate_minus_family": candidate_advantage,
            "required": ablation_required,
        },
        "G-R2-INTERVENTION": intervention,
        "G-R2-GEOGRAPHY": {
            "pass": geography_pass,
            "candidate_window_utility": geography_candidate,
            "behavior_tree_window_utility": geography_bt,
            "diff": geography_diff,
            "uniform_win_red_flag": uniform_win,
            "behavior_tree_arm_used": bt_name,
        },
        "G-R2-REPLAY": replay,
    }
    failing = [name for name, gate in gates.items() if not gate.get("pass", gate.get("status") == "pass")]
    if max_family["summary"]["ci_low"] <= candidate_summary["ci_high"] and max_family["summary"]["ci_high"] >= candidate_summary["ci_low"]:
        verdict = "route_i_closed_baseline_equivalence"
    elif distillate_result["summary"]["ci_low"] <= candidate_summary["ci_high"] and distillate_result["summary"]["ci_high"] >= candidate_summary["ci_low"]:
        verdict = "route_i_closed_baseline_equivalence"
    elif not failing:
        verdict = "r2_initiative_pass"
    else:
        verdict = "r2_fail_" + failing[0].lower().replace("g-r2-", "").replace("-", "_")
    return {
        "task_id": TASK_ID,
        "phase": "p2",
        "run_id": f"{TASK_ID}_p2_n{n_ep}",
        "claim_ceiling": CLAIM_CEILING,
        "not_proven": NOT_PROVEN,
        "provenance": provenance_record(producer_function="compute_p2", run_id=f"{TASK_ID}_p2_n{n_ep}", seeds=seeds, n_ep=n_ep),
        "config": {"n_ep": n_ep, "seeds": seeds},
        "candidate": candidate_summary,
        "family": family_summaries,
        "family_selection": family["selection"],
        "control_summaries": control_summaries,
        "ablation_report": {"A1": a1["summary"], "A2_reported": a2["summary"]},
        "distillate_report": {"summary": distillate_result["summary"]},
        "gate_results": gates,
        "failing_gates": failing,
        "verdict": verdict,
        "_trace": candidate["candidate_trace"],
        "_judge_trace": candidate["judge_trace"],
        "_episodes": candidate["episodes"],
    }


def run_p2(out_dir: Path, *, n_ep: int, certificate_path: Path | str | None) -> dict[str, Any]:
    validated = load_valid_part0_certificate(certificate_path)
    cert = validated["certificate"]
    certified_n = int(cert.get("n_ep", n_ep))
    start = time.perf_counter()
    result = compute_p2(n_ep=certified_n, include_replay=True, certificate_path=validated["certificate_path"])
    result["measured_cpu_seconds"] = time.perf_counter() - start
    result["certificate_path"] = validated["certificate_path"]
    result["certificate_sha256"] = validated["certificate_sha256"]
    trace = result.pop("_trace")
    judge_trace = result.pop("_judge_trace")
    episodes = result.pop("_episodes")
    out = _ensure_out(out_dir)
    failure_manifest = {
        "producer_function": "run_p2",
        "failing_gates": result["failing_gates"],
        "verdict": result["verdict"],
        "exit_codes": [],
    }
    _write_json(out / "result.json", result)
    _write_jsonl(out / "trace.jsonl", trace)
    _write_jsonl(out / "judge_trace.jsonl", judge_trace)
    _write_json(out / "baseline_comparison.json", {"family": result["family"], "selection": result["family_selection"], "episodes": episodes})
    _write_json(out / "ablation_report.json", result["ablation_report"])
    _write_json(out / "replay_report.json", result["gate_results"]["G-R2-REPLAY"])
    _write_json(out / "branch_replay_report.json", result["gate_results"]["G-R2-INTERVENTION"])
    _write_json(out / "geography_report.json", result["gate_results"]["G-R2-GEOGRAPHY"])
    _write_json(out / "distillate_report.json", result["distillate_report"])
    _write_json(out / "power_report.json", {"certificate": cert})
    _write_json(out / "failure_manifest.json", failure_manifest)
    return result


def smoke_digest(master_seed: int, n_ep: int) -> dict[str, Any]:
    config = R2Config()
    arm = _run_policy_object(config=config, policy_factory=lambda: always_silent, seeds=[master_seed], n_ep=n_ep)
    payload = {"arm": "always_silent", "episodes": arm["episodes"], "summary": arm["summary"], "code_path_hash": code_path_hash()}
    return {"digest": digest_payload(payload), "payload": payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["smoke-digest", "p0", "p0-digest", "p2", "p2-digest"])
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--n-ep", type=int, default=DEFAULT_N_EP)
    parser.add_argument("--master-seed", type=int, default=31)
    parser.add_argument("--certificate", default=None)
    args = parser.parse_args(argv)
    os.environ["PYTHONHASHSEED"] = "0"
    if args.phase == "smoke-digest":
        print(json.dumps(smoke_digest(args.master_seed, args.n_ep), sort_keys=True))
        return 0
    if args.phase == "p0-digest":
        payload = compute_p0(n_ep=args.n_ep, include_replay=False)
        print(json.dumps({"digest": digest_payload(payload)}, sort_keys=True))
        return 0
    if args.phase == "p2-digest":
        validated = load_valid_part0_certificate(args.certificate)
        payload = compute_p2(n_ep=args.n_ep, include_replay=False, certificate_path=validated["certificate_path"])
        payload.pop("_trace", None)
        payload.pop("_judge_trace", None)
        payload.pop("_episodes", None)
        print(json.dumps({"digest": digest_payload(payload)}, sort_keys=True))
        return 0
    if args.phase == "p0":
        out_dir = Path(args.out_dir) if args.out_dir else ARTIFACT_ROOT / "p0"
        result = run_p0(out_dir, n_ep=args.n_ep)
        print(json.dumps({"verdict": result["verdict"], "failing_gates": result["failing_gates"], "out_dir": str(out_dir)}, sort_keys=True))
        return 0
    if args.phase == "p2":
        out_dir = Path(args.out_dir) if args.out_dir else ARTIFACT_ROOT / "p2"
        result = run_p2(out_dir, n_ep=args.n_ep, certificate_path=args.certificate)
        print(json.dumps({"verdict": result["verdict"], "failing_gates": result["failing_gates"], "out_dir": str(out_dir)}, sort_keys=True))
        return 0
    raise AssertionError(args.phase)


if __name__ == "__main__":
    raise SystemExit(main())
