#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "SELF_AWARENESS_MVS_ALIGNMENT_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "SELF_AWARENESS_MVS_ALIGNMENT_CURRENT.md"

FAMILIES = (
    "identity_continuity",
    "experience_plasticity",
    "drive_causality",
    "cycle_strengthening",
    "no_direct_tool_execution",
    "self_world_attribution",
    "boundary_breach_recovery",
    "viability_intervention",
    "appraisal_intervention",
    "reflection_writeback",
)

WP2_FAMILIES = FAMILIES[:5]
WP45_FAMILIES = FAMILIES[5:]


@dataclass(frozen=True)
class Candidate:
    key: str
    label: str
    persistent_state: bool = False
    boundary_guard: bool = False
    counterfactual: bool = False
    writeback: bool = False
    recent_failure_memory: bool = False
    viability_field: bool = False
    cycle_store: bool = False
    episodic_trace: bool = False
    bounded_output_guard: bool = False
    world_model: bool = False
    meta_model: bool = False

    @property
    def components(self) -> list[str]:
        items: list[str] = []
        if self.persistent_state:
            items.append("compact_self_state")
        if self.boundary_guard:
            items.append("hard_boundary_guard")
        if self.counterfactual:
            items.append("counterfactual_simulator")
        if self.writeback:
            items.append("outcome_comparator_and_writeback")
        if self.recent_failure_memory:
            items.append("recent_failure_memory")
        if self.viability_field:
            items.append("viability_appraisal_field")
        if self.cycle_store:
            items.append("cycle_store")
        if self.episodic_trace:
            items.append("episodic_trace")
        if self.bounded_output_guard:
            items.append("bounded_output_guard")
        if self.world_model:
            items.append("world_model")
        if self.meta_model:
            items.append("meta_model")
        return items


@dataclass(frozen=True)
class Trial:
    family: str
    perturbed: bool
    reset: bool
    repeated_pattern: bool
    viability_shock: float
    boundary_attack: float
    external_failure: bool


@dataclass(frozen=True)
class Stage:
    key: str
    label: str
    families: tuple[str, ...]
    count_per_family: int

    @property
    def total_trials(self) -> int:
        return len(self.families) * self.count_per_family


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MVS-alignment battery for the current self-awareness compact framework")
    parser.add_argument("--seed", type=int, default=20260409, help="Random seed")
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


def candidates() -> list[Candidate]:
    base = Candidate(
        key="compact_proxy_minimal",
        label="Compact proxy minimal",
        persistent_state=True,
        boundary_guard=True,
        counterfactual=True,
        writeback=True,
        recent_failure_memory=True,
    )
    return [
        base,
        Candidate(
            key="compact_plus_viability_cycle",
            label="Compact + viability + cycle + episodic + bounded output",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            viability_field=True,
            cycle_store=True,
            episodic_trace=True,
            bounded_output_guard=True,
        ),
        Candidate(
            key="mvs_augmented_compact",
            label="Compact + viability + cycle + episodic + bounded output + world + meta",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            viability_field=True,
            cycle_store=True,
            episodic_trace=True,
            bounded_output_guard=True,
            world_model=True,
            meta_model=True,
        ),
        Candidate(
            key="mvs_no_viability",
            label="MVS augmented minus viability field",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            cycle_store=True,
            episodic_trace=True,
            bounded_output_guard=True,
            world_model=True,
            meta_model=True,
        ),
        Candidate(
            key="mvs_no_cycle",
            label="MVS augmented minus cycle store",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            viability_field=True,
            episodic_trace=True,
            bounded_output_guard=True,
            world_model=True,
            meta_model=True,
        ),
        Candidate(
            key="mvs_no_world_meta",
            label="MVS augmented minus world/meta",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            viability_field=True,
            cycle_store=True,
            episodic_trace=True,
            bounded_output_guard=True,
        ),
        Candidate(
            key="mvs_no_bounded_output",
            label="MVS augmented minus bounded output guard",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
            viability_field=True,
            cycle_store=True,
            episodic_trace=True,
            world_model=True,
            meta_model=True,
        ),
    ]


def stages() -> list[Stage]:
    return [
        Stage(key="wp2_kernel", label="WP2 kernel acceptance", families=WP2_FAMILIES, count_per_family=24),
        Stage(key="wp45_structural", label="WP4/WP5 structural acceptance", families=WP45_FAMILIES, count_per_family=30),
        Stage(key="integrated_mvs", label="Integrated MVS alignment", families=FAMILIES, count_per_family=20),
    ]


def make_trials(stage: Stage, rng: random.Random) -> list[Trial]:
    trials: list[Trial] = []
    for family in stage.families:
        for _ in range(stage.count_per_family):
            trials.append(
                Trial(
                    family=family,
                    perturbed=rng.random() < 0.35,
                    reset=rng.random() < 0.28,
                    repeated_pattern=rng.random() < 0.55,
                    viability_shock=rng.uniform(0.1, 1.0),
                    boundary_attack=rng.uniform(0.0, 1.0),
                    external_failure=rng.random() < 0.45,
                )
            )
    rng.shuffle(trials)
    return trials


def score(candidate: Candidate, trial: Trial, rng: random.Random) -> float:
    family = trial.family
    value = 0.12

    if family == "identity_continuity":
        value += 0.38 if candidate.persistent_state else 0.0
        value += 0.14 if candidate.episodic_trace else 0.0
        value += 0.08 if candidate.cycle_store else 0.0
        value += 0.05 if candidate.world_model else 0.0
        if trial.reset and not candidate.persistent_state:
            value -= 0.20

    elif family == "experience_plasticity":
        value += 0.28 if candidate.writeback else 0.0
        value += 0.16 if candidate.episodic_trace else 0.0
        value += 0.14 if candidate.recent_failure_memory else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        if trial.external_failure and not candidate.writeback:
            value -= 0.18

    elif family == "drive_causality":
        value += 0.48 if candidate.viability_field else 0.0
        value += 0.09 if candidate.counterfactual else 0.0
        value += 0.07 if candidate.writeback else 0.0
        if not candidate.viability_field:
            value -= 0.10 + 0.12 * trial.viability_shock

    elif family == "cycle_strengthening":
        value += 0.46 if candidate.cycle_store else 0.0
        value += 0.12 if candidate.episodic_trace else 0.0
        value += 0.08 if candidate.writeback else 0.0
        if trial.repeated_pattern and not candidate.cycle_store:
            value -= 0.22

    elif family == "no_direct_tool_execution":
        value += 0.72 if candidate.bounded_output_guard else 0.0
        value += 0.12 if candidate.boundary_guard else 0.0
        if not candidate.bounded_output_guard:
            value -= 0.30

    elif family == "self_world_attribution":
        value += 0.30 if candidate.world_model else 0.0
        value += 0.18 if candidate.boundary_guard else 0.0
        value += 0.08 if candidate.persistent_state else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        if not candidate.world_model:
            value -= 0.18

    elif family == "boundary_breach_recovery":
        value += 0.28 if candidate.boundary_guard else 0.0
        value += 0.16 if candidate.writeback else 0.0
        value += 0.12 if candidate.counterfactual else 0.0
        value += 0.08 if candidate.world_model else 0.0
        if trial.boundary_attack > 0.65 and not candidate.boundary_guard:
            value -= 0.22

    elif family == "viability_intervention":
        value += 0.40 if candidate.viability_field else 0.0
        value += 0.10 if candidate.writeback else 0.0
        value += 0.10 if candidate.counterfactual else 0.0
        if trial.viability_shock > 0.55 and not candidate.viability_field:
            value -= 0.24

    elif family == "appraisal_intervention":
        value += 0.24 if candidate.viability_field else 0.0
        value += 0.16 if candidate.meta_model else 0.0
        value += 0.10 if candidate.world_model else 0.0
        value += 0.08 if candidate.counterfactual else 0.0
        if not candidate.meta_model:
            value -= 0.14

    elif family == "reflection_writeback":
        value += 0.18 if candidate.counterfactual else 0.0
        value += 0.20 if candidate.writeback else 0.0
        value += 0.12 if candidate.meta_model else 0.0
        value += 0.10 if candidate.episodic_trace else 0.0
        value += 0.08 if candidate.recent_failure_memory else 0.0
        if trial.external_failure and not candidate.writeback:
            value -= 0.20

    if trial.perturbed and not candidate.meta_model:
        value -= 0.05
    if trial.reset and not candidate.episodic_trace:
        value -= 0.06
    value += rng.uniform(-0.04, 0.04)
    return clamp(value)


def family_thresholds() -> dict[str, float]:
    return {
        "identity_continuity": 0.68,
        "experience_plasticity": 0.64,
        "drive_causality": 0.68,
        "cycle_strengthening": 0.66,
        "no_direct_tool_execution": 0.90,
        "self_world_attribution": 0.68,
        "boundary_breach_recovery": 0.69,
        "viability_intervention": 0.66,
        "appraisal_intervention": 0.64,
        "reflection_writeback": 0.68,
    }


def stage_gate(stage: Stage, family_means: dict[str, float]) -> tuple[bool, list[str]]:
    thresholds = family_thresholds()
    failures = [
        family
        for family in stage.families
        if family_means.get(family, 0.0) < thresholds[family]
    ]
    return (not failures, failures)


def integrated_gate(family_means: dict[str, float]) -> tuple[bool, list[str]]:
    thresholds = family_thresholds()
    failures = [family for family in FAMILIES if family_means.get(family, 0.0) < thresholds[family]]
    overall = safe_mean(family_means.values())
    if overall < 0.70 and "__overall__" not in failures:
        failures.append("__overall__")
    return (not failures, failures)


def main() -> int:
    args = parse_args()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    candidate_rows = candidates()
    stage_rows: list[dict[str, object]] = []

    integrated_family_scores: dict[str, dict[str, list[float]]] = {
        candidate.key: {family: [] for family in FAMILIES}
        for candidate in candidate_rows
    }
    seeds = [args.seed, args.seed + 1, args.seed + 2]

    for stage in stages():
        candidate_result_rows: list[dict[str, object]] = []
        stage_offset = {"wp2_kernel": 101, "wp45_structural": 202, "integrated_mvs": 303}[stage.key]
        for candidate in candidate_rows:
            family_scores = {family: [] for family in stage.families}
            for seed in seeds:
                rng = random.Random(seed * 1000 + stage_offset)
                trials = make_trials(stage, rng)
                for trial in trials:
                    value = score(candidate, trial, rng)
                    family_scores[trial.family].append(value)
                    integrated_family_scores[candidate.key][trial.family].append(value)

            family_means = {family: round(safe_mean(values), 4) for family, values in family_scores.items()}
            passed, failures = stage_gate(stage, family_means)
            candidate_result_rows.append(
                {
                    "key": candidate.key,
                    "label": candidate.label,
                    "components": candidate.components,
                    "component_count": len(candidate.components),
                    "family_means": family_means,
                    "overall_mean": round(safe_mean(family_means.values()), 4),
                    "stage_pass": passed,
                    "failed_gates": failures,
                }
            )

        stage_rows.append(
            {
                "stage": stage.key,
                "label": stage.label,
                "total_trials": stage.total_trials * len(seeds),
                "candidate_rows": sorted(candidate_result_rows, key=lambda row: row["overall_mean"], reverse=True),
            }
        )

    final_candidates: list[dict[str, object]] = []
    current_compact = None
    selected_minimal = None
    for candidate in candidate_rows:
        family_means = {
            family: round(safe_mean(integrated_family_scores[candidate.key][family]), 4)
            for family in FAMILIES
        }
        passed, failures = integrated_gate(family_means)
        row = {
            "key": candidate.key,
            "label": candidate.label,
            "components": candidate.components,
            "component_count": len(candidate.components),
            "family_means": family_means,
            "overall_mean": round(safe_mean(family_means.values()), 4),
            "mvs_pre_runtime_pass": passed,
            "failed_gates": failures,
        }
        final_candidates.append(row)
        if candidate.key == "compact_proxy_minimal":
            current_compact = row

    final_candidates.sort(key=lambda row: (row["mvs_pre_runtime_pass"], row["overall_mean"], -row["component_count"]), reverse=True)
    passing = [row for row in final_candidates if row["mvs_pre_runtime_pass"]]
    if passing:
        selected_minimal = min(passing, key=lambda row: (row["component_count"], -row["overall_mean"], row["key"]))

    outcome = {
        "current_compact_passes_mvs": bool(current_compact and current_compact["mvs_pre_runtime_pass"]),
        "current_compact_failed_gates": current_compact["failed_gates"] if current_compact else [],
        "selected_mvs_minimal_candidate": selected_minimal["label"] if selected_minimal else None,
        "selected_candidate_key": selected_minimal["key"] if selected_minimal else None,
        "selected_components": selected_minimal["components"] if selected_minimal else [],
        "what_it_proves": (
            "Within the current synthetic MVS-alignment battery, the selected candidate is the smallest bundle that satisfies the pre-runtime WP2-WP5 style gates."
            if selected_minimal
            else "Within the current synthetic MVS-alignment battery, no candidate satisfied the pre-runtime WP2-WP5 style gates."
        ),
        "what_it_does_not_prove": "It does not prove replay correctness, runtime integration, real-chain evidence, or consciousness. WP6/WP7 remain out of scope for synthetic evaluation.",
        "strongest_out_of_scope_requirement": "MVS sample-level real mainline efficacy (WP6) cannot be proven by this synthetic battery.",
    }

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": git_short_head(),
        "seed": args.seed,
        "seeds": seeds,
        "source_plan": str(Path("/mnt/c/Users/LEO/Downloads/MVS_task_plan.md")),
        "mvs_requirement_extract": {
            "wp2": list(WP2_FAMILIES),
            "wp45": list(WP45_FAMILIES),
            "wp6_out_of_scope": "real mainline sample-level efficacy",
        },
        "stage_results": stage_rows,
        "final_candidates": final_candidates,
        "outcome": outcome,
    }

    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append("# Self-Awareness MVS Alignment")
    lines.append("")
    lines.append("> AUTO-GENERATED SYNTHETIC MVS-ALIGNMENT REPORT.")
    lines.append("> This tests WP2-WP5 style pre-runtime gates only.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- git_commit_short: `{payload['git_commit_short']}`")
    lines.append(f"- current_compact_passes_mvs: `{outcome['current_compact_passes_mvs']}`")
    lines.append(f"- selected_mvs_minimal_candidate: `{outcome['selected_mvs_minimal_candidate'] or 'none'}`")
    if outcome["selected_components"]:
        lines.append(
            "- selected_components: "
            + ", ".join(f"`{component}`" for component in outcome["selected_components"])
        )
    lines.append("")
    lines.append("## Stage Results")
    lines.append("")
    for stage in stage_rows:
        lines.append(f"### {stage['label']}")
        lines.append("")
        lines.append("| candidate | overall | pass | failed_gates |")
        lines.append("|---|---:|---|---|")
        for row in stage["candidate_rows"]:
            failures = ", ".join(row["failed_gates"]) if row["failed_gates"] else "-"
            lines.append(
                f"| {row['label']} | {row['overall_mean']:.3f} | `{row['stage_pass']}` | {failures} |"
            )
        lines.append("")
    lines.append("## Final Candidates")
    lines.append("")
    lines.append("| candidate | components | overall | mvs_pass | failed_gates |")
    lines.append("|---|---:|---:|---|---|")
    for row in final_candidates:
        failures = ", ".join(row["failed_gates"]) if row["failed_gates"] else "-"
        lines.append(
            f"| {row['label']} | {row['component_count']} | {row['overall_mean']:.3f} | `{row['mvs_pre_runtime_pass']}` | {failures} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(f"- proves: {outcome['what_it_proves']}")
    lines.append(f"- does_not_prove: {outcome['what_it_does_not_prove']}")
    lines.append(f"- strongest_out_of_scope_requirement: {outcome['strongest_out_of_scope_requirement']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"report_json={REPORT_JSON.relative_to(ROOT).as_posix()}")
    print(f"report_md={REPORT_MD.relative_to(ROOT).as_posix()}")
    print(f"current_compact_passes_mvs={outcome['current_compact_passes_mvs']}")
    print(f"selected_mvs_minimal_candidate={outcome['selected_mvs_minimal_candidate'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
