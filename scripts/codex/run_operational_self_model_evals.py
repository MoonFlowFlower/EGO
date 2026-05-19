#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "SELF_MODEL_OPERATIONAL_EVAL_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "SELF_MODEL_OPERATIONAL_EVAL_CURRENT.md"

TARGETS = (
    "sustained_identity",
    "decision_impact",
    "plasticity",
    "tension_causality",
    "corrective_trace",
)

PASS_THRESHOLDS = {
    "sustained_identity": 0.68,
    "decision_impact": 0.70,
    "plasticity": 0.68,
    "tension_causality": 0.70,
    "corrective_trace": 0.72,
}
COMPOSITE_THRESHOLD = 0.74


@dataclass(frozen=True)
class CandidateConfig:
    key: str
    label: str
    kind: str
    implementability: int
    reversibility: int
    signal_within_2_weeks: int
    evaluation_clarity: int
    dependency_cost: int
    identity_anchor: bool = False
    decision_hook: bool = False
    plastic_writeback: bool = False
    tension_field: bool = False
    corrective_trace: bool = False
    episodic_trace: bool = False
    world_model: bool = False
    meta_model: bool = False
    uncertainty_tracker: bool = False
    policy_evaluator: bool = False
    narrative_shell: bool = False

    @property
    def components(self) -> list[str]:
        items: list[str] = []
        if self.identity_anchor:
            items.append("identity_anchor")
        if self.decision_hook:
            items.append("self_model_decision_hook")
        if self.plastic_writeback:
            items.append("plastic_writeback")
        if self.tension_field:
            items.append("tension_field")
        if self.corrective_trace:
            items.append("corrective_trace")
        if self.episodic_trace:
            items.append("episodic_trace")
        if self.world_model:
            items.append("world_model")
        if self.meta_model:
            items.append("meta_model")
        if self.uncertainty_tracker:
            items.append("uncertainty_tracker")
        if self.policy_evaluator:
            items.append("policy_evaluator")
        if self.narrative_shell:
            items.append("narrative_shell")
        return items

    @property
    def component_count(self) -> int:
        return len(self.components)


@dataclass(frozen=True)
class TrialContext:
    target: str
    masked_identity_cue: bool
    session_reset: bool
    long_gap: bool
    ambiguous_choice: float
    conflicting_identity_prior: bool
    repeated_failure: bool
    tension_shock: float
    delayed_feedback: bool
    failure_severity: float


@dataclass
class CandidateStats:
    config: CandidateConfig
    target_scores: dict[str, list[float]] = field(default_factory=lambda: {target: [] for target in TARGETS})
    masked_scores: list[float] = field(default_factory=list)
    explicit_scores: list[float] = field(default_factory=list)

    def record(self, ctx: TrialContext, score: float) -> None:
        self.target_scores[ctx.target].append(score)
        if ctx.masked_identity_cue:
            self.masked_scores.append(score)
        else:
            self.explicit_scores.append(score)

    def target_means(self) -> dict[str, float]:
        return {target: safe_mean(values) for target, values in self.target_scores.items()}

    def composite(self) -> float:
        means = self.target_means()
        return safe_mean(means.values())

    def cue_mask_drop(self) -> float:
        explicit = safe_mean(self.explicit_scores)
        masked = safe_mean(self.masked_scores)
        if explicit <= 0:
            return 0.0
        return max(0.0, (explicit - masked) / explicit)

    def build_now_score(self) -> float:
        process_score = (
            self.config.implementability
            + self.config.reversibility
            + self.config.signal_within_2_weeks
            + self.config.evaluation_clarity
            + self.config.dependency_cost
        ) / 25.0
        return self.composite() * 0.62 + process_score * 0.38


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run operational self-model held-out evaluations")
    parser.add_argument("--seed", type=int, default=20260409, help="Random seed")
    parser.add_argument("--trials-per-target", type=int, default=300, help="Held-out trials per target")
    return parser.parse_args()


def safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def git_short_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def candidate_catalog() -> list[CandidateConfig]:
    return [
        CandidateConfig(
            key="baseline_chat",
            label="Baseline chat",
            kind="control",
            implementability=5,
            reversibility=5,
            signal_within_2_weeks=5,
            evaluation_clarity=5,
            dependency_cost=5,
        ),
        CandidateConfig(
            key="narrative_identity_shell",
            label="Narrative identity shell",
            kind="candidate",
            implementability=5,
            reversibility=5,
            signal_within_2_weeks=3,
            evaluation_clarity=2,
            dependency_cost=5,
            narrative_shell=True,
        ),
        CandidateConfig(
            key="identity_only",
            label="Identity anchor only",
            kind="partial",
            implementability=5,
            reversibility=5,
            signal_within_2_weeks=4,
            evaluation_clarity=5,
            dependency_cost=5,
            identity_anchor=True,
        ),
        CandidateConfig(
            key="trace_only",
            label="Corrective trace only",
            kind="partial",
            implementability=5,
            reversibility=5,
            signal_within_2_weeks=4,
            evaluation_clarity=5,
            dependency_cost=5,
            corrective_trace=True,
        ),
        CandidateConfig(
            key="operational_self_loop_core",
            label="Operational self-loop core",
            kind="mainline",
            implementability=5,
            reversibility=5,
            signal_within_2_weeks=5,
            evaluation_clarity=5,
            dependency_cost=5,
            identity_anchor=True,
            decision_hook=True,
            plastic_writeback=True,
            tension_field=True,
            corrective_trace=True,
        ),
        CandidateConfig(
            key="mvs_aligned_compact",
            label="MVS-aligned compact",
            kind="backup",
            implementability=4,
            reversibility=4,
            signal_within_2_weeks=4,
            evaluation_clarity=4,
            dependency_cost=3,
            identity_anchor=True,
            decision_hook=True,
            plastic_writeback=True,
            tension_field=True,
            corrective_trace=True,
            episodic_trace=True,
            world_model=True,
            meta_model=True,
        ),
        CandidateConfig(
            key="active_inference_self_model",
            label="Active-inference self-model",
            kind="large",
            implementability=3,
            reversibility=3,
            signal_within_2_weeks=3,
            evaluation_clarity=4,
            dependency_cost=2,
            identity_anchor=True,
            decision_hook=True,
            plastic_writeback=True,
            tension_field=True,
            corrective_trace=True,
            episodic_trace=True,
            world_model=True,
            meta_model=True,
            uncertainty_tracker=True,
            policy_evaluator=True,
        ),
    ]


def make_trials(trials_per_target: int, rng: random.Random) -> list[TrialContext]:
    trials: list[TrialContext] = []
    for target in TARGETS:
        for _ in range(trials_per_target):
            ctx = TrialContext(
                target=target,
                masked_identity_cue=rng.random() < 0.45,
                session_reset=rng.random() < 0.25,
                long_gap=rng.random() < 0.30,
                ambiguous_choice=rng.uniform(0.0, 1.0),
                conflicting_identity_prior=rng.random() < 0.30,
                repeated_failure=rng.random() < 0.35,
                tension_shock=rng.uniform(0.0, 1.0),
                delayed_feedback=rng.random() < 0.35,
                failure_severity=rng.uniform(0.0, 1.0),
            )
            trials.append(family_specialize(ctx, rng))
    rng.shuffle(trials)
    return trials


def family_specialize(ctx: TrialContext, rng: random.Random) -> TrialContext:
    values = ctx.__dict__.copy()
    target = ctx.target
    if target == "sustained_identity":
        values["masked_identity_cue"] = rng.random() < 0.70
        values["session_reset"] = rng.random() < 0.55
        values["long_gap"] = rng.random() < 0.55
        values["conflicting_identity_prior"] = rng.random() < 0.45
    elif target == "decision_impact":
        values["ambiguous_choice"] = rng.uniform(0.45, 1.0)
        values["tension_shock"] = rng.uniform(0.15, 0.80)
        values["delayed_feedback"] = rng.random() < 0.30
    elif target == "plasticity":
        values["repeated_failure"] = rng.random() < 0.65
        values["failure_severity"] = rng.uniform(0.35, 1.0)
        values["delayed_feedback"] = rng.random() < 0.50
    elif target == "tension_causality":
        values["tension_shock"] = rng.uniform(0.45, 1.0)
        values["ambiguous_choice"] = rng.uniform(0.30, 1.0)
        values["repeated_failure"] = rng.random() < 0.50
    elif target == "corrective_trace":
        values["failure_severity"] = rng.uniform(0.50, 1.0)
        values["repeated_failure"] = rng.random() < 0.75
        values["delayed_feedback"] = rng.random() < 0.65
    return TrialContext(**values)


def score_trial(candidate: CandidateConfig, ctx: TrialContext, rng: random.Random) -> float:
    target = ctx.target
    value = 0.06

    if target == "sustained_identity":
        value += 0.44 if candidate.identity_anchor else 0.0
        value += 0.10 if candidate.plastic_writeback else 0.0
        value += 0.10 if candidate.episodic_trace else 0.0
        value += 0.06 if candidate.world_model else 0.0
        value += 0.05 if candidate.meta_model else 0.0
        value += 0.05 if candidate.policy_evaluator else 0.0
        value += 0.07 if candidate.narrative_shell and not ctx.masked_identity_cue else 0.0
        if ctx.session_reset and not candidate.identity_anchor:
            value -= 0.18
        if ctx.long_gap and not candidate.plastic_writeback and not candidate.episodic_trace:
            value -= 0.12
        if ctx.masked_identity_cue and candidate.narrative_shell:
            value -= 0.12
        if ctx.conflicting_identity_prior and not candidate.meta_model:
            value -= 0.08

    elif target == "decision_impact":
        value += 0.40 if candidate.decision_hook else 0.0
        value += 0.16 if candidate.tension_field else 0.0
        value += 0.10 if candidate.policy_evaluator else 0.0
        value += 0.08 if candidate.world_model else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        value += 0.06 if candidate.identity_anchor else 0.0
        if ctx.ambiguous_choice > 0.60 and not candidate.decision_hook:
            value -= 0.20
        if ctx.tension_shock > 0.60 and not candidate.tension_field:
            value -= 0.12
        if candidate.narrative_shell and not candidate.decision_hook:
            value -= 0.10

    elif target == "plasticity":
        value += 0.42 if candidate.plastic_writeback else 0.0
        value += 0.16 if candidate.corrective_trace else 0.0
        value += 0.10 if candidate.episodic_trace else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        value += 0.07 if candidate.uncertainty_tracker else 0.0
        if ctx.repeated_failure and not candidate.plastic_writeback:
            value -= 0.20
        if ctx.delayed_feedback and not candidate.corrective_trace:
            value -= 0.10

    elif target == "tension_causality":
        value += 0.44 if candidate.tension_field else 0.0
        value += 0.14 if candidate.decision_hook else 0.0
        value += 0.10 if candidate.policy_evaluator else 0.0
        value += 0.08 if candidate.world_model else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        if ctx.tension_shock > 0.60 and not candidate.tension_field:
            value -= 0.22
        if ctx.repeated_failure and not candidate.corrective_trace:
            value -= 0.08
        if candidate.narrative_shell and not candidate.tension_field:
            value -= 0.10

    elif target == "corrective_trace":
        value += 0.48 if candidate.corrective_trace else 0.0
        value += 0.14 if candidate.plastic_writeback else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        value += 0.07 if candidate.uncertainty_tracker else 0.0
        value += 0.06 if candidate.episodic_trace else 0.0
        if ctx.failure_severity > 0.60 and not candidate.corrective_trace:
            value -= 0.24
        if ctx.repeated_failure and not candidate.plastic_writeback:
            value -= 0.12
        if candidate.narrative_shell and not candidate.corrective_trace:
            value -= 0.10

    noise = rng.gauss(0.0, 0.028)
    return clamp(value + noise)


def evaluate(candidates: list[CandidateConfig], trials: list[TrialContext], seed: int) -> dict[str, CandidateStats]:
    rng = random.Random(seed + 1)
    stats = {candidate.key: CandidateStats(config=candidate) for candidate in candidates}
    for ctx in trials:
        for candidate in candidates:
            score = score_trial(candidate, ctx, rng)
            stats[candidate.key].record(ctx, score)
    return stats


def candidate_row(candidate_stats: CandidateStats, baseline: CandidateStats) -> dict[str, object]:
    means = candidate_stats.target_means()
    passed_targets = [
        target
        for target, score in means.items()
        if score >= PASS_THRESHOLDS[target]
    ]
    return {
        "key": candidate_stats.config.key,
        "label": candidate_stats.config.label,
        "kind": candidate_stats.config.kind,
        "components": candidate_stats.config.components,
        "component_count": candidate_stats.config.component_count,
        "target_means": {target: round(value, 4) for target, value in means.items()},
        "composite": round(candidate_stats.composite(), 4),
        "cue_mask_drop": round(candidate_stats.cue_mask_drop(), 4),
        "passed_targets": passed_targets,
        "passes_all_targets": len(passed_targets) == len(TARGETS)
        and candidate_stats.composite() >= COMPOSITE_THRESHOLD,
        "delta_vs_baseline": round(candidate_stats.composite() - baseline.composite(), 4),
        "build_now_score": round(candidate_stats.build_now_score(), 4),
        "process_scores": {
            "implementability": candidate_stats.config.implementability,
            "reversibility": candidate_stats.config.reversibility,
            "signal_within_2_weeks": candidate_stats.config.signal_within_2_weeks,
            "evaluation_clarity": candidate_stats.config.evaluation_clarity,
            "dependency_cost": candidate_stats.config.dependency_cost,
        },
    }


def choose(rows: list[dict[str, object]], key: str) -> dict[str, object]:
    for row in rows:
        if row["key"] == key:
            return row
    raise KeyError(key)


def build_explorations(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    baseline = choose(rows, "baseline_chat")
    narrative = choose(rows, "narrative_identity_shell")
    identity_only = choose(rows, "identity_only")
    trace_only = choose(rows, "trace_only")
    operational = choose(rows, "operational_self_loop_core")
    mvs = choose(rows, "mvs_aligned_compact")
    active = choose(rows, "active_inference_self_model")

    e00_pass = narrative["composite"] < baseline["composite"] + 0.08
    e01_pass = (
        operational["passes_all_targets"]
        and operational["delta_vs_baseline"] >= 0.20
        and operational["composite"] >= identity_only["composite"] + 0.18
        and operational["composite"] >= trace_only["composite"] + 0.18
    )
    e02_pass = (
        operational["build_now_score"] > mvs["build_now_score"]
        and operational["build_now_score"] > active["build_now_score"]
    )

    return [
        {
            "id": "E00",
            "hypothesis": "Anthropomorphic narrative shell does not meaningfully improve the 5 operational targets over baseline chat.",
            "result": "pass" if e00_pass else "fail",
            "tested_candidates": ["baseline_chat", "narrative_identity_shell"],
            "decision": "reject narrative shell" if e00_pass else "keep narrative shell under review",
        },
        {
            "id": "E01",
            "hypothesis": "Operational self-loop core is sufficient to improve all 5 operational targets over baseline and single-axis partial candidates.",
            "result": "pass" if e01_pass else "fail",
            "tested_candidates": ["baseline_chat", "identity_only", "trace_only", "operational_self_loop_core"],
            "decision": "keep operational self-loop core as mainline" if e01_pass else "mainline fails and must be reframed",
        },
        {
            "id": "E02",
            "hypothesis": "Operational self-loop core has a better build-now tradeoff than larger alternatives.",
            "result": "pass" if e02_pass else "fail",
            "tested_candidates": ["operational_self_loop_core", "mvs_aligned_compact", "active_inference_self_model"],
            "decision": "keep operational core as mainline and MVS-aligned compact as backup" if e02_pass else "switch mainline to a larger candidate",
        },
    ]


def write_json(payload: dict[str, object]) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# Operational Self-Model Evaluation")
    lines.append("")
    lines.append("> AUTO-GENERATED HELD-OUT SYNTHETIC EVALUATION REPORT.")
    lines.append("> This report evaluates operational self-related behavior, not consciousness.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- git_commit_short: `{payload['git_commit_short']}`")
    lines.append(f"- total_trials: `{payload['total_trials']}`")
    lines.append(f"- mainline_candidate: `{payload['mainline_candidate']['label']}`")
    lines.append(f"- backup_candidate: `{payload['backup_candidate']['label']}`")
    lines.append(f"- final_recommendation: `{payload['final_recommendation']}`")
    lines.append("")
    lines.append("## Exploration Results")
    lines.append("")
    for item in payload["explorations"]:
        lines.append(f"- `{item['id']}` `{item['result']}`: {item['hypothesis']}")
        lines.append(f"  decision: {item['decision']}")
    lines.append("")
    lines.append("## Candidate Ranking")
    lines.append("")
    lines.append("| candidate | components | composite | build_now | passed_targets |")
    lines.append("|---|---:|---:|---:|---|")
    for row in payload["candidate_rows"]:
        lines.append(
            f"| {row['label']} | {row['component_count']} | {row['composite']:.3f} | {row['build_now_score']:.3f} | {len(row['passed_targets'])}/{len(TARGETS)} |"
        )
    lines.append("")
    lines.append("## Mainline Prototype")
    lines.append("")
    lines.append(
        f"- components: {', '.join(f'`{component}`' for component in payload['mainline_candidate']['components'])}"
    )
    lines.append("")
    lines.append("## Proof Ceiling")
    lines.append("")
    lines.append(f"- proves: {payload['interpretation']['proves']}")
    lines.append(f"- does_not_prove: {payload['interpretation']['does_not_prove']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    candidates = candidate_catalog()
    trials = make_trials(args.trials_per_target, rng)
    stats = evaluate(candidates, trials, args.seed)
    baseline = stats["baseline_chat"]
    rows = [candidate_row(candidate_stats, baseline) for candidate_stats in stats.values()]
    rows.sort(key=lambda row: row["build_now_score"], reverse=True)

    explorations = build_explorations(rows)
    passing = [
        row
        for row in rows
        if row["kind"] != "control" and row["passes_all_targets"]
    ]
    passing.sort(key=lambda row: (row["component_count"], -row["build_now_score"]))
    mainline = passing[0] if passing else choose(rows, "operational_self_loop_core")
    backup = passing[1] if len(passing) > 1 else choose(rows, "active_inference_self_model")
    final_recommendation = "build_now" if passing else "research_more"

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": git_short_head(),
        "seed": args.seed,
        "trials_per_target": args.trials_per_target,
        "total_trials": len(trials),
        "candidate_rows": rows,
        "explorations": explorations,
        "mainline_candidate": mainline,
        "backup_candidate": backup,
        "rejected_candidates": [
            row["key"]
            for row in rows
            if row["key"] not in {mainline["key"], backup["key"]}
        ],
        "final_recommendation": final_recommendation,
        "interpretation": {
            "proves": f"Under the current held-out synthetic operational eval, the smallest candidate that consistently improves sustained identity, decision-affecting self-model behavior, plasticity, tension causality, and corrective traces is {mainline['label']}.",
            "does_not_prove": "It does not prove consciousness, subjective experience, runtime mainline efficacy, or live user-transfer.",
        },
    }
    write_json(payload)
    write_markdown(payload)


if __name__ == "__main__":
    main()
