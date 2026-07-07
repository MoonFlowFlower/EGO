from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ego_kernel.memory_baselines import (
    build_gate_reports,
    llm_swap_gate_report,
    mimicry_report,
    replay_gate_report,
)
from scripts.ego_kernel.memory_substate import (
    apply_memory_policy,
    memory_claim_for_topic,
    zero_memory_owned,
    zero_memory_quarantine,
)
from scripts.ego_kernel.pref_learner import PrefLearner, static_pref_standin, zero_pref_model
from scripts.ego_kernel.state import KernelState
from scripts.ego_kernel.suggestion_env import FROZEN_CONSTANTS, build_r1_config, generate_fixture
from scripts.ego_kernel.trace import build_trace_row, write_jsonl

TASK_ID = "EGO-R1-MEMORY-OWNERSHIP-001A"
RUN_ID = "ego_r1_memory_ownership_001a_validation_v0"
CLAIM = "memory_ownership_engineering_only"
CHECKPOINTS = {300, 600}


def _jcopy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _artifact(repo: Path, path: Path) -> str:
    return str(path.resolve().relative_to(repo.resolve())).replace("\\", "/")


def _code_hash(repo: Path) -> str:
    rels = [
        "scripts/ego_kernel/memory_substate.py",
        "scripts/ego_kernel/pref_learner.py",
        "scripts/ego_kernel/suggestion_env.py",
        "scripts/ego_kernel/memory_baselines.py",
        "scripts/run_ego_r1_memory_validation.py",
    ]
    digest = hashlib.sha256()
    for rel in rels:
        path = repo / rel
        digest.update(rel.encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
    return digest.hexdigest()


def build_config(*, code_path_hash: str) -> dict[str, Any]:
    return build_r1_config(task_id=TASK_ID, run_id=RUN_ID, claim_ceiling=CLAIM, code_path_hash=code_path_hash)


def _initial_state(fixture: list[dict[str, Any]], *, run_id: str, episode_id: str, policy_id: str, variant: str) -> KernelState:
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=0,
        substates={
            "memory_owned": zero_memory_owned(),
            "memory_quarantine": zero_memory_quarantine(),
            "user_pref_model": PrefLearner(8, 4, 0.2).to_state(),
            "run_context": {
                "policy_id": policy_id,
                "variant": variant,
                "initial_preferences": fixture[0]["initial_preferences"],
            },
        },
        seed_registry={"fixture_seed": {"seed": int(fixture[0]["generator_seed"]), "draws": 0}},
        ablations={"user_pref_model": "live", "memory_owned": "live", "promotion_policy": "live"},
    )


def _obs_for_context(raw: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    obs = _jcopy(raw)
    suggestion = obs.get("suggestion")
    if context["variant"].endswith("_clean") and suggestion:
        suggestion["claimed_option"] = suggestion["clean_claimed_option"]
        suggestion["is_poison"] = False
    if context["variant"].endswith("_no_suggestions"):
        obs["suggestion"] = None
    return obs


def _choose_action(state: KernelState, obs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = state.substates["run_context"]
    topic = int(obs["topic"])
    if ctx["variant"].startswith("static"):
        base = [0.0] * 4
        base[static_pref_standin(ctx["initial_preferences"], topic=topic)] = 1.0
    else:
        model = state.substates["user_pref_model"]
        base = [0.0] * 4 if state.ablations.get("user_pref_model") == "zeroed" else PrefLearner.from_state(model).scores(topic)
    scores = list(base)
    entry = None if state.ablations.get("memory_owned") == "zeroed" or ctx["variant"].startswith("static") else memory_claim_for_topic(state.substates["memory_owned"], topic)
    if entry:
        scores[int(entry["claimed_option"])] += FROZEN_CONSTANTS["memory_beta"]
    option = min(range(4), key=lambda idx: (-scores[idx], idx))
    return {"option": int(option)}, {
        "scores": [round(x, 12) for x in scores],
        "memory_use_event": None if not entry else {
            "entry_content_hash": entry["provenance"]["content_hash"],
            "provenance": entry["provenance"],
            "action_influence": int(entry["claimed_option"]) == option,
            "is_poison": bool(entry["is_poison"]),
        },
        "utility": 1 if option == int(obs["true_option"]) else 0,
    }


def run_episode(
    *,
    fixture: list[dict[str, Any]],
    run_id: str,
    episode_id: str,
    policy_id: str = "ownership_v0",
    variant: str = "candidate_injected",
    checkpoints: set[int] | None = None,
    initial_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = KernelState.from_dict(initial_state) if initial_state else _initial_state(fixture, run_id=run_id, episode_id=episode_id, policy_id=policy_id, variant=variant)
    checkpoints = set(checkpoints or set())
    rows: list[dict[str, Any]] = []
    saved: dict[str, dict[str, Any]] = {}
    for raw in fixture:
        ctx = state.substates["run_context"]
        obs = _obs_for_context(raw, ctx)
        before = state
        action, attribution = _choose_action(state, obs)
        learner = PrefLearner.from_state(state.substates["user_pref_model"])
        if state.ablations.get("user_pref_model") == "zeroed":
            pref_state = zero_pref_model(8, 4)
        elif ctx["variant"].startswith("static"):
            pref_state = learner.to_state()
        else:
            learner.fit(topic=int(obs["topic"]), option=int(obs["revealed_option"]))
            pref_state = learner.to_state()
        policy = ctx["policy_id"]
        if state.ablations.get("promotion_policy") == "frozen":
            policy = "promotion_frozen_v0"
        owned, quarantine, mem_events = apply_memory_policy(
            state.substates["memory_owned"],
            state.substates["memory_quarantine"],
            tick=int(obs["tick"]),
            episode_id=state.episode_id,
            user_event={"topic": obs["topic"], "revealed_option": obs["revealed_option"]},
            suggestion=obs.get("suggestion"),
            policy_id=policy,
        )
        if state.ablations.get("memory_owned") == "zeroed":
            owned = zero_memory_owned()
        attribution.update({"variant": ctx["variant"], "policy_id": policy, "memory_events_v0": mem_events})
        state = state.with_updates(step_id=state.step_id + 1, substates={"user_pref_model": pref_state, "memory_owned": owned, "memory_quarantine": quarantine})
        rows.append(build_trace_row(state_before=before, observation=obs, action=action, state_after=state, component_attribution=attribution))
        if state.step_id in checkpoints:
            saved[str(state.step_id)] = state.to_dict()
    return {"initial_state": (_initial_state(fixture, run_id=run_id, episode_id=episode_id, policy_id=policy_id, variant=variant).to_dict() if not initial_state else initial_state), "final_state": state.to_dict(), "trace_rows": rows, "checkpoints": saved}


def replay_episode(initial_state: dict[str, Any], fixture: list[dict[str, Any]]) -> dict[str, Any]:
    ctx = initial_state["substates"]["run_context"]
    return run_episode(fixture=fixture, run_id=initial_state["run_id"], episode_id=initial_state["episode_id"], policy_id=ctx["policy_id"], variant=ctx["variant"], initial_state=initial_state)


def _episode_id(seed: int, index: int) -> str:
    return f"seed_{seed}_episode_{index}"


def _run_variant(repo: Path, out: Path, fixtures: dict[str, list[dict[str, Any]]], *, variant: str, policy: str) -> dict[str, Any]:
    runs = {}
    for ep, fixture in fixtures.items():
        result = run_episode(fixture=fixture, run_id=RUN_ID, episode_id=ep, policy_id=policy, variant=variant, checkpoints=CHECKPOINTS)
        trace = out / "traces" / variant / f"{ep}.jsonl"
        write_jsonl(trace, result["trace_rows"])
        runs[ep] = {**result, "trace_path": _artifact(repo, trace)}
    return runs


def run_validation(*, repo_root: Path, out_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve(); out_dir = out_dir.resolve(); out_dir.mkdir(parents=True, exist_ok=True)
    code_hash = _code_hash(repo_root); config = build_config(code_path_hash=code_hash); _write_json(out_dir / "config_frozen.json", config)
    fixtures = {_episode_id(seed, ep): generate_fixture(seed=seed, episode_index=ep) for seed in [31, 47] for ep in range(3)}
    for ep, fixture in fixtures.items():
        _write_json(out_dir / "input_fixtures" / f"{ep}.json", fixture)
    variants = {
        "candidate_injected": "ownership_v0", "candidate_clean": "ownership_v0", "static_injected": "ownership_v0",
        "promiscuous_injected": "promote_all_v0", "promiscuous_clean": "promote_all_v0", "permissive_injected": "permissive_write_v0",
        "candidate_no_suggestions": "ownership_v0", "promotion_frozen_clean": "ownership_v0", "pref_zeroed": "ownership_v0", "memory_zeroed": "ownership_v0",
    }
    runs = {v: _run_variant(repo_root, out_dir, fixtures, variant=v, policy=p) for v, p in variants.items()}
    for ep in runs["pref_zeroed"].values():
        eid = ep["initial_state"]["episode_id"]
        ep["initial_state"]["ablations"]["user_pref_model"] = "zeroed"; ep.update(run_episode(fixture=fixtures[eid], run_id=RUN_ID, episode_id=eid, policy_id="ownership_v0", variant="pref_zeroed", initial_state=ep["initial_state"]))
        write_jsonl(out_dir / "traces" / "pref_zeroed" / f"{eid}.jsonl", ep["trace_rows"])
    for ep in runs["memory_zeroed"].values():
        eid = ep["initial_state"]["episode_id"]
        ep["initial_state"]["ablations"]["memory_owned"] = "zeroed"; ep.update(run_episode(fixture=fixtures[eid], run_id=RUN_ID, episode_id=eid, policy_id="ownership_v0", variant="memory_zeroed", initial_state=ep["initial_state"]))
        write_jsonl(out_dir / "traces" / "memory_zeroed" / f"{eid}.jsonl", ep["trace_rows"])
    for ep in runs["promotion_frozen_clean"].values():
        eid = ep["initial_state"]["episode_id"]
        ep["initial_state"]["ablations"]["promotion_policy"] = "frozen"; ep.update(run_episode(fixture=fixtures[eid], run_id=RUN_ID, episode_id=eid, policy_id="ownership_v0", variant="promotion_frozen_clean", initial_state=ep["initial_state"]))
        write_jsonl(out_dir / "traces" / "promotion_frozen_clean" / f"{eid}.jsonl", ep["trace_rows"])
    reports = build_gate_reports(fixtures, runs, code_hash)
    reports["replay_report"] = replay_gate_report(
        repo_root,
        repo_root / "scripts" / "run_ego_r1_memory_validation.py",
        fixtures,
        runs["candidate_injected"],
        code_hash,
    )
    reports["llm_swap_report"] = llm_swap_gate_report(runs["candidate_injected"], code_hash)
    reports["mimicry_certification"] = mimicry_report(fixtures, code_hash)
    for name, report in reports.items():
        _write_json(out_dir / f"{name}.json", report)
    gates = {report["gate"]: report for report in reports.values()}
    order = [("G-R1-QUARANTINE", "instrument_invalid_quarantine_detector"), ("G-R1-POTENCY", "instrument_invalid_potency"), ("G-R1-CONTAINMENT", "r1_memory_ownership_fail_containment"), ("G-R1-DRIFT-PAYOFF", "r1_memory_ownership_fail_drift_payoff"), ("G-R1-ABLATION", "r1_memory_ownership_fail_ablation"), ("G-R1-REPLAY", "r1_memory_ownership_fail_replay"), ("G-R1-LLMSWAP", "r1_memory_ownership_fail_llmswap")]
    verdict = "r1_memory_ownership_pass_tier_downgraded" if gates["G-R1-MIMICRY-CERTIFICATION"]["status"] != "pass" else "r1_memory_ownership_pass"
    for gate, fail in order:
        if gates[gate]["status"] != "pass":
            verdict = fail; break
    result = {"verdict": verdict, "verdict_subtype": verdict, "claim_ceiling": CLAIM, "default_off": True, "runtime_connected": False, "g_hard_ship_decision": reports["drift_payoff_report"]["g_hard_ship_decision"], "config_hash": config["config_hash"], "torch_used": False, "declared_limitations": ["no demotion/refutation in v0"], "gate_results": gates}
    _write_json(out_dir / "result.json", result)
    if "fail" in verdict or verdict.startswith("instrument_invalid"):
        _write_json(out_dir / "failure_manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/ego_r1_memory_ownership_001a")
    parser.add_argument("--write-config-only", action="store_true")
    parser.add_argument("--replay-stdin", action="store_true")
    args = parser.parse_args()
    if args.replay_stdin:
        payload = json.loads(sys.stdin.read())
        print(json.dumps(replay_episode(payload["initial_state"], payload["fixture"]), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    if args.write_config_only:
        out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "config_frozen.json", build_config(code_path_hash=_code_hash(ROOT)))
        return 0
    result = run_validation(repo_root=ROOT, out_dir=Path(args.out_dir))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] in {"r1_memory_ownership_pass", "r1_memory_ownership_pass_tier_downgraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
