from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

from .experiments import ConditionResult, evaluate_seeds, gate_status, result_to_dict


REPORTS = {
    "BASELINE_REPORT.md": "baseline",
    "DANGER_GENERALIZATION_REPORT.md": "danger_generalization",
    "MEMORY_DELETION_ABLATION.md": "memory_deletion",
    "FROZEN_WORLD_MODEL_ABLATION.md": "frozen_world_model",
    "FROZEN_SELF_MODEL_ABLATION.md": "frozen_self_model",
    "NO_PREDICTION_ERROR_LEARNING_ABLATION.md": "no_prediction_error_learning",
    "REPLAY_DETERMINISM_REPORT.md": "replay_determinism",
}


def run_experiments(out: str | Path, seeds: Iterable[int]) -> Dict[str, object]:
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)
    traces_dir = out_path / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    seed_list = [int(seed) for seed in seeds]
    results = evaluate_seeds(seed_list)
    gates = gate_status(results)
    overall_status = "E4_passed" if all(gates.values()) else "hold"

    _write_traces(traces_dir, results)
    for filename, report_kind in REPORTS.items():
        (out_path / filename).write_text(
            _render_report(
                report_kind=report_kind,
                seeds=seed_list,
                overall_status=overall_status,
                gates=gates,
                results=results,
            ),
            encoding="utf-8",
        )

    summary = {
        "overall_status": overall_status,
        "claim_level": "lab_only_proto_self_mechanism",
        "seeds": seed_list,
        "gates": gates,
        "trace_dir": str(traces_dir.as_posix()),
        "what_it_proves": "PSPC-local lab ablation gates passed under deterministic seeds."
        if overall_status == "E4_passed"
        else "At least one PSPC-local lab ablation gate did not pass.",
        "what_it_does_not_prove": [
            "stable real user benefit",
            "live autonomy",
            "durable operator memory efficacy",
            "EgoOperator runtime efficacy",
            "philosophical consciousness",
            "subjective experience",
        ],
    }
    (out_path / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _write_traces(traces_dir: Path, results: Dict[str, List[ConditionResult]]) -> None:
    for scenario, scenario_results in results.items():
        trace_path = traces_dir / f"{scenario}.jsonl"
        with trace_path.open("w", encoding="utf-8", newline="\n") as handle:
            for result in scenario_results:
                handle.write(json.dumps(result.trace_payload, ensure_ascii=False, sort_keys=True) + "\n")


def _render_report(
    *,
    report_kind: str,
    seeds: List[int],
    overall_status: str,
    gates: Dict[str, bool],
    results: Dict[str, List[ConditionResult]],
) -> str:
    title = {
        "baseline": "VirtualCatPSPC v0 Baseline Report",
        "danger_generalization": "VirtualCatPSPC v0 Danger Generalization Report",
        "memory_deletion": "VirtualCatPSPC v0 Memory Deletion Ablation",
        "frozen_world_model": "VirtualCatPSPC v0 Frozen World Model Ablation",
        "frozen_self_model": "VirtualCatPSPC v0 Frozen Self Model Ablation",
        "no_prediction_error_learning": "VirtualCatPSPC v0 No Prediction-Error Learning Ablation",
        "replay_determinism": "VirtualCatPSPC v0 Replay Determinism Report",
    }[report_kind]
    relevant = _relevant_results(report_kind, results)
    trace_hashes = sorted({result.trace_hash for group in relevant.values() for result in group})
    rows = _metric_rows(relevant)
    gate_name = "different_histories" if report_kind == "baseline" else report_kind
    status = "pass" if gates.get(gate_name, False) or (report_kind == "baseline" and gates["different_histories"]) else "hold"

    return "\n".join(
        [
            f"# {title}",
            "",
            f"- status: `{status}`",
            f"- pspc_local_status: `{overall_status}`",
            f"- seeds: `{', '.join(str(seed) for seed in seeds)}`",
            f"- claim_level: `lab_only_proto_self_mechanism`",
            "",
            "## Summary",
            _summary_for(report_kind),
            "",
            "## Metrics",
            rows,
            "",
            "## Trace Refs",
            "\n".join(f"- trace_hash `{trace_hash}`" for trace_hash in trace_hashes),
            "",
            "## What It Proves",
            _proves_for(report_kind),
            "",
            "## What It Does Not Prove",
            (
                "This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, "
                "EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production "
                "transport safety, or that PSPC should be connected to the runtime."
            ),
            "",
            "## Failure Meaning",
            _failure_for(report_kind),
            "",
            "## Rollback Note",
            "Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.",
            "",
        ]
    )


def _relevant_results(report_kind: str, results: Dict[str, List[ConditionResult]]) -> Dict[str, List[ConditionResult]]:
    if report_kind == "baseline":
        return {"danger": results["danger"], "safe": results["safe"]}
    if report_kind == "danger_generalization":
        return {"danger": results["danger"]}
    if report_kind == "memory_deletion":
        return {"danger": results["danger"], "memory_deleted": results["memory_deleted"]}
    if report_kind == "frozen_world_model":
        return {"danger": results["danger"], "frozen_world": results["frozen_world"]}
    if report_kind == "frozen_self_model":
        return {"danger": results["danger"], "frozen_self": results["frozen_self"]}
    if report_kind == "no_prediction_error_learning":
        return {"danger": results["danger"], "no_prediction_error_learning": results["no_prediction_error_learning"]}
    if report_kind == "replay_determinism":
        return {"replay_first": results["replay_first"], "replay_second": results["replay_second"]}
    raise ValueError(report_kind)


def _metric_rows(relevant: Dict[str, List[ConditionResult]]) -> str:
    lines = ["| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |", "|---|---:|---|---:|---:|---:|---|"]
    for condition, condition_results in relevant.items():
        for result in condition_results:
            lines.append(
                "| {condition} | {seed} | {action} | {caution:.2f} | {risk:.4f} | {error:.4f} | `{trace}` |".format(
                    condition=condition,
                    seed=result.seed,
                    action=result.selected_action,
                    caution=result.caution_score,
                    risk=result.self_risk_score,
                    error=result.world_prediction_error,
                    trace=result.trace_hash,
                )
            )
    return "\n".join(lines)


def _summary_for(report_kind: str) -> str:
    return {
        "baseline": "Different seeded histories are compared on the same unseen unstable tall object.",
        "danger_generalization": "The learned risk response is checked on `blue_glass_bottle_unseen`, not the seen red cup.",
        "memory_deletion": "Relevant unstable-object memories are removed before training to test causal memory support.",
        "frozen_world_model": "World-model learning is disabled while the rest of the lab chain remains present.",
        "frozen_self_model": "Self-model learning is disabled while world-risk prediction remains available.",
        "no_prediction_error_learning": "Prediction-error updates are disabled to test whether behavior still changes without learning.",
        "replay_determinism": "The same seed and state are run twice to compare selected action and trace digest.",
    }[report_kind]


def _proves_for(report_kind: str) -> str:
    return {
        "baseline": "Within this lab setup, different histories can produce different future behavior on the same target.",
        "danger_generalization": "Within this lab setup, learned caution transfers by unstable-object features rather than by the seen object id.",
        "memory_deletion": "Within this lab setup, deleting relevant memory reduces the cautious behavior supported by that memory.",
        "frozen_world_model": "Within this lab setup, freezing world-model learning degrades prediction/planning quality.",
        "frozen_self_model": "Within this lab setup, freezing self-model learning reduces self-risk judgment and changes action selection.",
        "no_prediction_error_learning": "Within this lab setup, disabling prediction-error learning blocks the learned caution effect.",
        "replay_determinism": "Within this lab setup, same seed and internal state replay the same decision digest.",
    }[report_kind]


def _failure_for(report_kind: str) -> str:
    return {
        "baseline": "If this fails, history is not causally affecting planning.",
        "danger_generalization": "If this fails, the system may be learning an object-name rule or not learning risk features.",
        "memory_deletion": "If this fails, memory writes are logs only and not causal supports for future behavior.",
        "frozen_world_model": "If this fails, the planner is not using the world model or prediction error is not updating it.",
        "frozen_self_model": "If this fails, the self model is not causally involved in risk/ability judgment.",
        "no_prediction_error_learning": "If this fails, the claimed learning path is not the source of behavior change.",
        "replay_determinism": "If this fails, the lab evidence is not auditably replayable.",
    }[report_kind]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VirtualCatPSPC v0 lab experiments.")
    parser.add_argument("--out", default="artifacts/virtual_cat_pspc_v0", help="Output artifact directory.")
    parser.add_argument("--seeds", default="101,102,103", help="Comma-separated deterministic seeds.")
    args = parser.parse_args()
    seeds = [int(part.strip()) for part in args.seeds.split(",") if part.strip()]
    summary = run_experiments(args.out, seeds=seeds)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["overall_status"] == "E4_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
