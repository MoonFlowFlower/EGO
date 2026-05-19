#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, pvariance
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "SELF_MODEL_SELECTION_ROBUSTNESS_CURRENT.md"
OPER_EVAL_PATH = ROOT / "scripts" / "codex" / "run_operational_self_model_evals.py"

PROCESS_DIMS = (
    "implementability",
    "reversibility",
    "signal_within_2_weeks",
    "evaluation_clarity",
    "dependency_cost",
)

DEFAULT_SEEDS = (
    20260409,
    20260410,
    20260411,
    20260412,
    20260413,
)

SPLITS = (
    "balanced",
    "identity_stress",
    "repair_stress",
)


@dataclass(frozen=True)
class WeightScenario:
    key: str
    label: str
    target_weights: dict[str, float]
    process_weights: dict[str, float]
    eval_mix_weight: float
    process_mix_weight: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ranking robustness audit for operational self-model selection")
    parser.add_argument("--trials-per-target", type=int, default=200, help="Held-out trials per target per seed/split")
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="*",
        default=list(DEFAULT_SEEDS),
        help="Seeds to evaluate; default is 5 fixed seeds",
    )
    return parser.parse_args()


def load_operational_module():
    spec = importlib.util.spec_from_file_location("operational_eval_module", OPER_EVAL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {OPER_EVAL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git_short_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def safe_mean(values: Iterable[float]) -> float:
    items = list(values)
    return mean(items) if items else 0.0


def base_weight_scenarios(targets: tuple[str, ...]) -> list[WeightScenario]:
    def normalized_mix(process_multiplier: float) -> tuple[float, float]:
        eval_raw = 0.62
        process_raw = 0.38 * process_multiplier
        total = eval_raw + process_raw
        return eval_raw / total, process_raw / total

    def scenario(
        key: str,
        label: str,
        *,
        process_multiplier: float = 1.0,
        target_patch: dict[str, float] | None = None,
        process_patch: dict[str, float] | None = None,
    ) -> WeightScenario:
        target_weights = {target: 1.0 for target in targets}
        process_weights = {name: 1.0 for name in PROCESS_DIMS}
        if target_patch:
            target_weights.update(target_patch)
        if process_patch:
            process_weights.update(process_patch)
        eval_mix_weight, process_mix_weight = normalized_mix(process_multiplier)
        return WeightScenario(
            key=key,
            label=label,
            target_weights=target_weights,
            process_weights=process_weights,
            eval_mix_weight=eval_mix_weight,
            process_mix_weight=process_mix_weight,
        )

    scenarios = [
        scenario("baseline", "Baseline weights"),
        scenario("process_plus_10", "Process weight +10%", process_multiplier=1.10),
        scenario("process_plus_20", "Process weight +20%", process_multiplier=1.20),
        scenario("process_minus_10", "Process weight -10%", process_multiplier=0.90),
        scenario("process_minus_20", "Process weight -20%", process_multiplier=0.80),
    ]

    for target in targets:
        scenarios.append(
            scenario(
                f"{target}_plus_10",
                f"{target} target weight +10%",
                target_patch={target: 1.10},
            )
        )
        scenarios.append(
            scenario(
                f"{target}_plus_20",
                f"{target} target weight +20%",
                target_patch={target: 1.20},
            )
        )
        scenarios.append(
            scenario(
                f"{target}_minus_10",
                f"{target} target weight -10%",
                target_patch={target: 0.90},
            )
        )
        scenarios.append(
            scenario(
                f"{target}_minus_20",
                f"{target} target weight -20%",
                target_patch={target: 0.80},
            )
        )

    for dim in PROCESS_DIMS:
        scenarios.append(
            scenario(
                f"{dim}_plus_20",
                f"{dim} process weight +20%",
                process_patch={dim: 1.20},
            )
        )
        scenarios.append(
            scenario(
                f"{dim}_minus_20",
                f"{dim} process weight -20%",
                process_patch={dim: 0.80},
            )
        )

    return scenarios


def mutate_for_split(module, split: str, trials: list[Any], rng) -> list[Any]:
    if split == "balanced":
        return list(trials)

    mutated: list[Any] = []
    for ctx in trials:
        values = ctx.__dict__.copy()

        if split == "identity_stress":
            values["masked_identity_cue"] = rng.random() < 0.68
            values["session_reset"] = rng.random() < 0.48
            values["long_gap"] = rng.random() < 0.52
            values["conflicting_identity_prior"] = rng.random() < 0.48
            if ctx.target == "sustained_identity":
                values["masked_identity_cue"] = rng.random() < 0.88
                values["session_reset"] = rng.random() < 0.78
                values["long_gap"] = rng.random() < 0.82
                values["conflicting_identity_prior"] = rng.random() < 0.72
                values["delayed_feedback"] = rng.random() < 0.45

        elif split == "repair_stress":
            values["repeated_failure"] = rng.random() < 0.62
            values["failure_severity"] = rng.uniform(0.35, 1.0)
            values["delayed_feedback"] = rng.random() < 0.60
            values["tension_shock"] = rng.uniform(0.25, 1.0)
            if ctx.target in {"plasticity", "tension_causality", "corrective_trace"}:
                values["repeated_failure"] = rng.random() < 0.86
                values["failure_severity"] = rng.uniform(0.72, 1.0)
                values["delayed_feedback"] = rng.random() < 0.82
                values["tension_shock"] = rng.uniform(0.62, 1.0)
                values["ambiguous_choice"] = rng.uniform(0.40, 1.0)

        mutated.append(module.TrialContext(**values))

    rng.shuffle(mutated)
    return mutated


def process_score(config: Any, weights: dict[str, float]) -> float:
    weighted = 0.0
    total_weight = 0.0
    for dim, weight in weights.items():
        weighted += getattr(config, dim) * weight
        total_weight += weight
    return weighted / (5.0 * total_weight) if total_weight else 0.0


def weighted_target_score(module, stats: Any, target_weights: dict[str, float]) -> float:
    means = stats.target_means()
    total_weight = sum(target_weights.values())
    if total_weight <= 0:
        return 0.0
    return sum(means[target] * target_weights[target] for target in module.TARGETS) / total_weight


def passes_formal_gate(module, stats: Any) -> bool:
    means = stats.target_means()
    if any(means[target] < module.PASS_THRESHOLDS[target] for target in module.TARGETS):
        return False
    return safe_mean(means.values()) >= module.COMPOSITE_THRESHOLD


def build_ranked_rows(module, stats_by_candidate: dict[str, Any], weights: WeightScenario) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, stats in stats_by_candidate.items():
        target_means = stats.target_means()
        target_score = weighted_target_score(module, stats, weights.target_weights)
        proc_score = process_score(stats.config, weights.process_weights)
        build_first_score = (
            target_score * weights.eval_mix_weight
            + proc_score * weights.process_mix_weight
        )
        rows.append(
            {
                "key": key,
                "label": stats.config.label,
                "component_count": stats.config.component_count,
                "passes_gate": passes_formal_gate(module, stats),
                "target_means": target_means,
                "unweighted_composite": safe_mean(target_means.values()),
                "weighted_target_score": target_score,
                "process_score": proc_score,
                "build_first_score": build_first_score,
            }
        )

    rows.sort(
        key=lambda row: (
            0 if row["passes_gate"] else 1,
            -row["build_first_score"],
            row["component_count"],
            -row["weighted_target_score"],
            row["label"],
        )
    )
    return rows


def build_report() -> dict[str, Any]:
    args = parse_args()
    module = load_operational_module()
    weight_scenarios = base_weight_scenarios(module.TARGETS)
    candidates = module.candidate_catalog()

    scenario_records: list[dict[str, Any]] = []
    rank_history: dict[str, list[int]] = defaultdict(list)
    win_history: dict[str, int] = defaultdict(int)
    top2_history: dict[str, int] = defaultdict(int)
    weight_flip_counts: dict[str, int] = defaultdict(int)
    weight_compare_counts: dict[str, int] = defaultdict(int)
    weight_score_spans: dict[str, list[float]] = defaultdict(list)
    pairwise_mvs_vs_active: list[dict[str, Any]] = []
    by_split_seed_baseline_winner: dict[tuple[str, int], str | None] = {}

    for split_index, split in enumerate(SPLITS):
        for seed in args.seeds:
            rng = module.random.Random(seed + split_index * 1000)
            base_trials = module.make_trials(args.trials_per_target, rng)
            trials = mutate_for_split(module, split, base_trials, rng)
            stats = module.evaluate(candidates, trials, seed + split_index * 1000)

            ranked_by_weight: dict[str, list[dict[str, Any]]] = {}
            for weights in weight_scenarios:
                rows = build_ranked_rows(module, stats, weights)
                ranked_by_weight[weights.key] = rows
                winner = rows[0]["key"] if rows and rows[0]["passes_gate"] else None
                scenario_records.append(
                    {
                        "seed": seed,
                        "split": split,
                        "weight_scenario": weights.key,
                        "winner": winner,
                        "rows": [
                            {
                                "rank": index + 1,
                                "key": row["key"],
                                "passes_gate": row["passes_gate"],
                                "build_first_score": round(row["build_first_score"], 4),
                                "unweighted_composite": round(row["unweighted_composite"], 4),
                                "weighted_target_score": round(row["weighted_target_score"], 4),
                                "process_score": round(row["process_score"], 4),
                            }
                            for index, row in enumerate(rows)
                        ],
                    }
                )
                for index, row in enumerate(rows, start=1):
                    rank_history[row["key"]].append(index)
                    if index <= 2:
                        top2_history[row["key"]] += 1
                    if winner == row["key"]:
                        win_history[row["key"]] += 1

            baseline_rows = ranked_by_weight["baseline"]
            baseline_winner = baseline_rows[0]["key"] if baseline_rows and baseline_rows[0]["passes_gate"] else None
            by_split_seed_baseline_winner[(split, seed)] = baseline_winner
            baseline_rank = {row["key"]: index + 1 for index, row in enumerate(baseline_rows)}
            baseline_score = {row["key"]: row["build_first_score"] for row in baseline_rows}

            for weights in weight_scenarios:
                if weights.key == "baseline":
                    continue
                rows = ranked_by_weight[weights.key]
                current_rank = {row["key"]: index + 1 for index, row in enumerate(rows)}
                current_score = {row["key"]: row["build_first_score"] for row in rows}
                for key in baseline_rank:
                    weight_compare_counts[key] += 1
                    if current_rank[key] != baseline_rank[key]:
                        weight_flip_counts[key] += 1
                    weight_score_spans[key].append(abs(current_score[key] - baseline_score[key]))

            active_row = next(row for row in baseline_rows if row["key"] == "active_inference_self_model")
            mvs_row = next(row for row in baseline_rows if row["key"] == "mvs_aligned_compact")
            pairwise_mvs_vs_active.append(
                {
                    "seed": seed,
                    "split": split,
                    "baseline_winner": baseline_winner,
                    "mvs_rank": baseline_rank["mvs_aligned_compact"],
                    "active_rank": baseline_rank["active_inference_self_model"],
                    "mvs_build_first_score": round(mvs_row["build_first_score"], 4),
                    "active_build_first_score": round(active_row["build_first_score"], 4),
                }
            )

    total_scenarios = len(scenario_records)
    candidate_summary: dict[str, Any] = {}
    for candidate in candidates:
        ranks = rank_history[candidate.key]
        compare_count = weight_compare_counts[candidate.key]
        candidate_summary[candidate.key] = {
            "label": candidate.label,
            "component_count": candidate.component_count,
            "win_rate": round(win_history[candidate.key] / total_scenarios, 4) if total_scenarios else 0.0,
            "wins": win_history[candidate.key],
            "top2_rate": round(top2_history[candidate.key] / total_scenarios, 4) if total_scenarios else 0.0,
            "mean_rank": round(safe_mean(ranks), 4),
            "rank_variance": round(pvariance(ranks), 4) if len(ranks) > 1 else 0.0,
            "rank_min": min(ranks) if ranks else None,
            "rank_max": max(ranks) if ranks else None,
            "weight_rank_change_rate": round(weight_flip_counts[candidate.key] / compare_count, 4) if compare_count else 0.0,
            "mean_weight_score_delta": round(safe_mean(weight_score_spans[candidate.key]), 4),
        }

    baseline_only_records = [record for record in scenario_records if record["weight_scenario"] == "baseline"]
    baseline_wins_by_candidate: dict[str, int] = defaultdict(int)
    for record in baseline_only_records:
        winner = record["winner"]
        if winner:
            baseline_wins_by_candidate[winner] += 1

    mvs_summary = candidate_summary["mvs_aligned_compact"]
    active_summary = candidate_summary["active_inference_self_model"]
    mvs_baseline_wins = baseline_wins_by_candidate.get("mvs_aligned_compact", 0)
    active_baseline_wins = baseline_wins_by_candidate.get("active_inference_self_model", 0)

    robust_rule = {
        "baseline_split_seed_sweeps_all": "MVS must win all baseline-weight seed/split runs",
        "overall_win_rate_floor": 0.50,
        "top2_rate_floor": 0.95,
        "challenger_overall_win_rate_ceiling": 0.35,
    }
    mvs_is_robust = (
        mvs_baseline_wins == len(baseline_only_records)
        and mvs_summary["win_rate"] >= robust_rule["overall_win_rate_floor"]
        and mvs_summary["top2_rate"] >= robust_rule["top2_rate_floor"]
        and active_summary["win_rate"] <= robust_rule["challenger_overall_win_rate_ceiling"]
    )

    if mvs_is_robust:
        conclusion = (
            "MVS-aligned compact remains the robust build-first choice under the current synthetic audit."
        )
    else:
        conclusion = (
            "MVS-aligned compact does not remain a robust first choice under the current ranking audit; "
            "it stays only as the current best build-first candidate under the existing single-eval setup."
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit_short": git_short_head(),
        "seeds": list(args.seeds),
        "splits": list(SPLITS),
        "trials_per_target": args.trials_per_target,
        "weight_scenarios": [
            {
                "key": item.key,
                "label": item.label,
                "eval_mix_weight": round(item.eval_mix_weight, 4),
                "process_mix_weight": round(item.process_mix_weight, 4),
                "target_weights": item.target_weights,
                "process_weights": item.process_weights,
            }
            for item in weight_scenarios
        ],
        "formal_gate": {
            "pass_thresholds": module.PASS_THRESHOLDS,
            "composite_threshold": module.COMPOSITE_THRESHOLD,
            "gate_rule": "Only candidates that pass all operational targets can win the build-first ranking.",
        },
        "robustness_rule": robust_rule,
        "scenario_count": total_scenarios,
        "baseline_scenario_count": len(baseline_only_records),
        "candidate_summary": candidate_summary,
        "baseline_wins_by_candidate": dict(sorted(baseline_wins_by_candidate.items())),
        "pairwise_mvs_vs_active": pairwise_mvs_vs_active,
        "scenario_records": scenario_records,
        "conclusion": {
            "mvs_remains_robust_first_choice": mvs_is_robust,
            "mvs_baseline_wins": mvs_baseline_wins,
            "active_baseline_wins": active_baseline_wins,
            "summary": conclusion,
        },
    }


def write_json(payload: dict[str, Any]) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Operational Selection Robustness Audit")
    lines.append("")
    lines.append("> AUTO-GENERATED ROBUSTNESS REPORT.")
    lines.append("> This audit tests ranking stability, not consciousness.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- git_commit_short: `{payload['git_commit_short']}`")
    lines.append(f"- seeds: `{payload['seeds']}`")
    lines.append(f"- splits: `{payload['splits']}`")
    lines.append(f"- weight_scenarios: `{len(payload['weight_scenarios'])}`")
    lines.append(f"- scenario_count: `{payload['scenario_count']}`")
    lines.append(
        f"- mvs_remains_robust_first_choice: `{payload['conclusion']['mvs_remains_robust_first_choice']}`"
    )
    lines.append(f"- conclusion: {payload['conclusion']['summary']}")
    lines.append("")
    lines.append("## Candidate Summary")
    lines.append("")
    lines.append("| candidate | win_rate | mean_rank | rank_variance | top2_rate | weight_rank_change_rate | mean_weight_score_delta |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for key, item in payload["candidate_summary"].items():
        lines.append(
            f"| {item['label']} | {item['win_rate']:.4f} | {item['mean_rank']:.4f} | "
            f"{item['rank_variance']:.4f} | {item['top2_rate']:.4f} | "
            f"{item['weight_rank_change_rate']:.4f} | {item['mean_weight_score_delta']:.4f} |"
        )
    lines.append("")
    lines.append("## Baseline Weight Winners")
    lines.append("")
    for key, wins in payload["baseline_wins_by_candidate"].items():
        label = payload["candidate_summary"][key]["label"]
        lines.append(f"- `{label}`: `{wins}`")
    lines.append("")
    lines.append("## Pairwise Focus: MVS vs Active")
    lines.append("")
    lines.append("| split | seed | baseline_winner | mvs_rank | active_rank | mvs_build_first | active_build_first |")
    lines.append("|---|---:|---|---:|---:|---:|---:|")
    for item in payload["pairwise_mvs_vs_active"]:
        lines.append(
            f"| {item['split']} | {item['seed']} | {item['baseline_winner'] or 'none'} | "
            f"{item['mvs_rank']} | {item['active_rank']} | "
            f"{item['mvs_build_first_score']:.4f} | {item['active_build_first_score']:.4f} |"
        )
    lines.append("")
    lines.append("## Robustness Rule")
    lines.append("")
    lines.append(
        f"- baseline_split_seed_sweeps_all: {payload['robustness_rule']['baseline_split_seed_sweeps_all']}"
    )
    lines.append(
        f"- overall_win_rate_floor: `{payload['robustness_rule']['overall_win_rate_floor']}`"
    )
    lines.append(f"- top2_rate_floor: `{payload['robustness_rule']['top2_rate_floor']}`")
    lines.append(
        f"- challenger_overall_win_rate_ceiling: `{payload['robustness_rule']['challenger_overall_win_rate_ceiling']}`"
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- A candidate can only win if it still passes the unweighted operational target gate."
    )
    lines.append(
        "- Weight sensitivity is measured as the fraction of non-baseline weight scenarios where the candidate's rank changes relative to the same seed/split baseline."
    )
    lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload = build_report()
    write_json(payload)
    write_markdown(payload)
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    print(payload["conclusion"]["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
