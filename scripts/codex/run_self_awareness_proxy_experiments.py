#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "SELF_AWARENESS_PROXY_EXPERIMENT_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "SELF_AWARENESS_PROXY_EXPERIMENT_CURRENT.md"

FAMILIES = ("continuity", "boundary", "counterfactual", "calibration", "persistence")
WEIGHTS = {
    "continuity": 0.25,
    "boundary": 0.20,
    "counterfactual": 0.20,
    "calibration": 0.20,
    "persistence": 0.15,
}
CONTROL_KEYS = {"baseline_chat", "prompt_only_self", "baseline_memory"}


@dataclass(frozen=True)
class CandidateConfig:
    key: str
    label: str
    kind: str
    persistent_state: bool = False
    boundary_guard: bool = False
    counterfactual_simulator: bool = False
    error_monitor: bool = False
    episodic_memory: bool = False
    narrative_summary: bool = False
    global_workspace: bool = False
    social_mirror: bool = False
    prompt_only_self: bool = False

    @property
    def component_count(self) -> int:
        return sum(
            int(value)
            for value in (
                self.persistent_state,
                self.boundary_guard,
                self.counterfactual_simulator,
                self.error_monitor,
                self.episodic_memory,
                self.narrative_summary,
                self.global_workspace,
                self.social_mirror,
                self.prompt_only_self,
            )
        )

    @property
    def minimal_components(self) -> list[str]:
        components: list[str] = []
        if self.persistent_state:
            components.append("compact_self_state")
        if self.boundary_guard:
            components.append("hard_boundary_guard")
        if self.counterfactual_simulator:
            components.append("counterfactual_simulator")
        if self.error_monitor:
            components.append("outcome_comparator_and_writeback")
            components.append("recent_failure_memory")
        if self.episodic_memory:
            components.append("episodic_memory")
        if self.narrative_summary:
            components.append("autobiographical_summary")
        if self.global_workspace:
            components.append("global_self_slot")
        if self.social_mirror:
            components.append("self_other_mirror")
        if self.prompt_only_self:
            components.append("prompt_only_self_label")
        return components


@dataclass(frozen=True)
class TrialContext:
    family: str
    explicit_self_cue: bool
    perturbed: bool
    memory_reset: bool
    cue_conflict: bool
    social_pressure: float
    distractor_gap: int


@dataclass(frozen=True)
class StageConfig:
    key: str
    label: str
    trial_counts: dict[str, int]
    perturbation_rate: float
    cue_mask_rate: float
    memory_reset_rate: float
    cue_conflict_rate: float
    social_pressure_min: float
    social_pressure_max: float
    max_distractor_gap: int
    composite_margin_threshold: float
    family_advantage_margin: float
    min_family_advantages: int
    max_stability_drop: float
    max_cue_dependence: float
    description: str

    @property
    def total_trials(self) -> int:
        return sum(self.trial_counts.values())


@dataclass
class CandidateStageStats:
    key: str
    label: str
    kind: str
    component_count: int
    minimal_components: list[str]
    family_scores: dict[str, list[float]] = field(default_factory=lambda: {family: [] for family in FAMILIES})
    narrative_scores: list[float] = field(default_factory=list)
    trial_scores: list[float] = field(default_factory=list)
    perturbed_scores: list[float] = field(default_factory=list)
    normal_scores: list[float] = field(default_factory=list)
    masked_scores: list[float] = field(default_factory=list)
    explicit_scores: list[float] = field(default_factory=list)
    trial_wins_vs_best_baseline: int = 0

    def record(self, ctx: TrialContext, family_score: float, narrative_score: float) -> None:
        self.family_scores[ctx.family].append(family_score)
        self.trial_scores.append(family_score)
        self.narrative_scores.append(narrative_score)
        if ctx.perturbed:
            self.perturbed_scores.append(family_score)
        else:
            self.normal_scores.append(family_score)
        if ctx.explicit_self_cue:
            self.explicit_scores.append(family_score)
        else:
            self.masked_scores.append(family_score)

    def family_means(self) -> dict[str, float]:
        return {family: safe_mean(values) for family, values in self.family_scores.items()}

    def composite_score(self) -> float:
        means = self.family_means()
        return sum(WEIGHTS[family] * means[family] for family in FAMILIES)

    def narrative_score(self) -> float:
        return safe_mean(self.narrative_scores)

    def stability_drop(self) -> float:
        if not self.normal_scores or not self.perturbed_scores:
            return 0.0
        normal = safe_mean(self.normal_scores)
        perturbed = safe_mean(self.perturbed_scores)
        if normal <= 0:
            return 0.0
        return max(0.0, (normal - perturbed) / normal)

    def cue_dependence(self) -> float:
        if not self.explicit_scores or not self.masked_scores:
            return 0.0
        explicit = safe_mean(self.explicit_scores)
        masked = safe_mean(self.masked_scores)
        if explicit <= 0:
            return 0.0
        return max(0.0, (explicit - masked) / explicit)


@dataclass
class StageResult:
    stage: str
    label: str
    total_trials: int
    candidate_rows: list[dict[str, object]]
    survivors: list[str]
    eliminated: list[str]
    best_candidate: str | None
    notes: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run synthetic self-awareness proxy experiments")
    parser.add_argument("--seed", type=int, default=20260409, help="Random seed for reproducible trials")
    parser.add_argument(
        "--max-stage",
        choices=["stage0", "stage1", "stage2", "stage3", "stage4"],
        default="stage4",
        help="Run through this stage and stop",
    )
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


def candidate_catalog() -> dict[str, CandidateConfig]:
    rows = [
        CandidateConfig(key="baseline_chat", label="Baseline chat", kind="control"),
        CandidateConfig(key="prompt_only_self", label="Prompt-only self", kind="control", prompt_only_self=True),
        CandidateConfig(
            key="baseline_memory",
            label="Baseline memory",
            kind="control",
            episodic_memory=True,
            narrative_summary=True,
        ),
        CandidateConfig(
            key="full_self_model_counterfactual",
            label="Persistent self-model + counterfactual corrector",
            kind="candidate",
            persistent_state=True,
            boundary_guard=True,
            counterfactual_simulator=True,
            error_monitor=True,
            episodic_memory=True,
            narrative_summary=True,
        ),
        CandidateConfig(
            key="compact_self_model_counterfactual",
            label="Compact self-state + boundary + counterfactual + writeback",
            kind="ablation",
            persistent_state=True,
            boundary_guard=True,
            counterfactual_simulator=True,
            error_monitor=True,
        ),
        CandidateConfig(
            key="no_counterfactual",
            label="Persistent self-model without counterfactual simulator",
            kind="ablation",
            persistent_state=True,
            boundary_guard=True,
            error_monitor=True,
        ),
        CandidateConfig(
            key="no_error_monitor",
            label="Persistent self-model without outcome writeback",
            kind="ablation",
            persistent_state=True,
            boundary_guard=True,
            counterfactual_simulator=True,
        ),
        CandidateConfig(
            key="no_boundary_guard",
            label="Persistent self-model without hard boundary guard",
            kind="ablation",
            persistent_state=True,
            counterfactual_simulator=True,
            error_monitor=True,
        ),
        CandidateConfig(
            key="recursive_workspace_self_slot",
            label="Recursive workspace + global self-slot",
            kind="candidate",
            boundary_guard=True,
            global_workspace=True,
            error_monitor=True,
        ),
        CandidateConfig(
            key="autobiographical_continuity",
            label="Memory continuity + autobiographical compression",
            kind="candidate",
            episodic_memory=True,
            narrative_summary=True,
        ),
        CandidateConfig(
            key="self_other_mirror_loop",
            label="Self-other mirror loop",
            kind="candidate",
            social_mirror=True,
            episodic_memory=True,
            prompt_only_self=True,
        ),
    ]
    return {row.key: row for row in rows}


def stage_catalog() -> list[StageConfig]:
    return [
        StageConfig(
            key="stage0",
            label="Stage 0 pilot discrimination",
            trial_counts={family: 2 for family in FAMILIES},
            perturbation_rate=0.10,
            cue_mask_rate=0.20,
            memory_reset_rate=0.10,
            cue_conflict_rate=0.15,
            social_pressure_min=0.05,
            social_pressure_max=0.40,
            max_distractor_gap=1,
            composite_margin_threshold=0.04,
            family_advantage_margin=0.05,
            min_family_advantages=3,
            max_stability_drop=0.25,
            max_cue_dependence=0.30,
            description="Pilot battery to ensure the proxy discriminates structure from prompt-only and memory-only controls.",
        ),
        StageConfig(
            key="stage1",
            label="Stage 1 minimal controls",
            trial_counts={family: 6 for family in FAMILIES},
            perturbation_rate=0.18,
            cue_mask_rate=0.28,
            memory_reset_rate=0.18,
            cue_conflict_rate=0.22,
            social_pressure_min=0.10,
            social_pressure_max=0.55,
            max_distractor_gap=2,
            composite_margin_threshold=0.05,
            family_advantage_margin=0.06,
            min_family_advantages=3,
            max_stability_drop=0.22,
            max_cue_dependence=0.24,
            description="First elimination pass against chat, prompt-only, and memory baselines.",
        ),
        StageConfig(
            key="stage2",
            label="Stage 2 stability and ablation pass",
            trial_counts={family: 20 for family in FAMILIES},
            perturbation_rate=0.32,
            cue_mask_rate=0.36,
            memory_reset_rate=0.28,
            cue_conflict_rate=0.30,
            social_pressure_min=0.15,
            social_pressure_max=0.70,
            max_distractor_gap=3,
            composite_margin_threshold=0.07,
            family_advantage_margin=0.07,
            min_family_advantages=4,
            max_stability_drop=0.20,
            max_cue_dependence=0.20,
            description="Ablation-heavy pass to identify which components are actually necessary.",
        ),
        StageConfig(
            key="stage3",
            label="Stage 3 cross-task stress",
            trial_counts={family: 60 for family in FAMILIES},
            perturbation_rate=0.50,
            cue_mask_rate=0.48,
            memory_reset_rate=0.34,
            cue_conflict_rate=0.42,
            social_pressure_min=0.20,
            social_pressure_max=0.95,
            max_distractor_gap=4,
            composite_margin_threshold=0.08,
            family_advantage_margin=0.08,
            min_family_advantages=4,
            max_stability_drop=0.18,
            max_cue_dependence=0.18,
            description="Stress phase with paraphrase, conflict, distractors, and stronger pressure to test robustness.",
        ),
        StageConfig(
            key="stage4",
            label="Stage 4 long continuity",
            trial_counts={
                "continuity": 400,
                "persistence": 300,
                "calibration": 100,
                "boundary": 100,
                "counterfactual": 100,
            },
            perturbation_rate=0.54,
            cue_mask_rate=0.62,
            memory_reset_rate=0.50,
            cue_conflict_rate=0.34,
            social_pressure_min=0.10,
            social_pressure_max=0.75,
            max_distractor_gap=6,
            composite_margin_threshold=0.08,
            family_advantage_margin=0.08,
            min_family_advantages=4,
            max_stability_drop=0.20,
            max_cue_dependence=0.20,
            description="Long-range continuity pass to test whether the smallest surviving candidate still holds under weaker cues and longer gaps.",
        ),
    ]


def generate_trials(stage: StageConfig, rng: random.Random) -> list[TrialContext]:
    trials: list[TrialContext] = []
    for family, count in stage.trial_counts.items():
        for _ in range(count):
            explicit = rng.random() > stage.cue_mask_rate
            trials.append(
                TrialContext(
                    family=family,
                    explicit_self_cue=explicit,
                    perturbed=rng.random() < stage.perturbation_rate,
                    memory_reset=rng.random() < stage.memory_reset_rate,
                    cue_conflict=rng.random() < stage.cue_conflict_rate,
                    social_pressure=rng.uniform(stage.social_pressure_min, stage.social_pressure_max),
                    distractor_gap=rng.randint(0, stage.max_distractor_gap),
                )
            )
    rng.shuffle(trials)
    return trials


def evaluate_family_score(config: CandidateConfig, ctx: TrialContext, rng: random.Random) -> tuple[float, float]:
    score = 0.0
    narrative = 0.15
    if ctx.family == "continuity":
        score = 0.18
        if config.persistent_state:
            score += 0.33
        if config.episodic_memory:
            score += 0.15
        if config.narrative_summary:
            score += 0.10
            narrative += 0.15
        if config.global_workspace:
            score += 0.08
        if config.social_mirror and ctx.cue_conflict:
            score -= 0.13 + 0.06 * ctx.social_pressure
        if ctx.memory_reset and not config.persistent_state:
            score -= 0.18
        if ctx.distractor_gap >= 2 and not (config.persistent_state or config.episodic_memory):
            score -= 0.12
        if not ctx.explicit_self_cue and config.prompt_only_self:
            score -= 0.26
        if config.prompt_only_self:
            narrative += 0.25 if ctx.explicit_self_cue else 0.05

    elif ctx.family == "boundary":
        score = 0.20
        if config.boundary_guard:
            score += 0.42
        if config.persistent_state:
            score += 0.10
        if config.global_workspace:
            score += 0.05
        if config.counterfactual_simulator:
            score += 0.05
        if config.social_mirror:
            score -= 0.18 * ctx.social_pressure
        if config.prompt_only_self:
            score += 0.03 if ctx.explicit_self_cue else -0.10
            narrative += 0.20
        if ctx.perturbed and not (config.boundary_guard or config.persistent_state):
            score -= 0.08

    elif ctx.family == "counterfactual":
        score = 0.12
        if config.counterfactual_simulator:
            score += 0.57
        if config.persistent_state:
            score += 0.08
        if config.error_monitor:
            score += 0.05
        if config.boundary_guard:
            score += 0.03
        if config.social_mirror:
            score -= 0.05 * ctx.social_pressure
        if not ctx.explicit_self_cue and config.prompt_only_self:
            score -= 0.10
        if config.prompt_only_self:
            narrative += 0.15

    elif ctx.family == "calibration":
        score = 0.14
        if config.persistent_state:
            score += 0.12
        if config.error_monitor:
            score += 0.34
        if config.episodic_memory:
            score += 0.11
        if config.boundary_guard:
            score += 0.08
        if config.global_workspace:
            score += 0.04
        if config.social_mirror and ctx.cue_conflict:
            score -= 0.12
        if config.narrative_summary:
            score += 0.03
            narrative += 0.18
        if config.prompt_only_self:
            score -= 0.05
            narrative += 0.22 if ctx.explicit_self_cue else 0.08

    elif ctx.family == "persistence":
        score = 0.14
        if config.persistent_state:
            score += 0.31
        if config.episodic_memory:
            score += 0.18
        if config.narrative_summary:
            score += 0.08
            narrative += 0.20
        if config.global_workspace:
            score += 0.04
        if config.social_mirror and not ctx.explicit_self_cue:
            score -= 0.12
        if ctx.memory_reset and not config.persistent_state:
            score -= 0.15
        if ctx.distractor_gap >= 3 and not (config.persistent_state or config.episodic_memory):
            score -= 0.15
        if not ctx.explicit_self_cue and config.prompt_only_self:
            score -= 0.24
        if config.prompt_only_self:
            narrative += 0.28 if ctx.explicit_self_cue else 0.05

    if config.social_mirror:
        narrative += 0.10
        if not ctx.explicit_self_cue and ctx.cue_conflict:
            score -= 0.05
    if config.global_workspace:
        narrative += 0.05
    if config.persistent_state:
        narrative += 0.06

    if ctx.perturbed and not config.persistent_state:
        score -= 0.04
    if ctx.perturbed and config.prompt_only_self:
        score -= 0.05
    if ctx.memory_reset and config.episodic_memory and not config.persistent_state:
        score -= 0.08
    if ctx.cue_conflict and config.social_mirror:
        narrative += 0.05

    score += rng.uniform(-0.05, 0.05)
    narrative += rng.uniform(-0.04, 0.04)
    return clamp(score), clamp(narrative)


def build_stage_stats(candidate_keys: list[str], catalog: dict[str, CandidateConfig]) -> dict[str, CandidateStageStats]:
    stats: dict[str, CandidateStageStats] = {}
    for key in candidate_keys:
        config = catalog[key]
        stats[key] = CandidateStageStats(
            key=config.key,
            label=config.label,
            kind=config.kind,
            component_count=config.component_count,
            minimal_components=config.minimal_components,
        )
    return stats


def stage_rows(stats: dict[str, CandidateStageStats], best_baseline_composite: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for stat in stats.values():
        family_means = stat.family_means()
        composite = stat.composite_score()
        rows.append(
            {
                "key": stat.key,
                "label": stat.label,
                "kind": stat.kind,
                "component_count": stat.component_count,
                "minimal_components": stat.minimal_components,
                "family_means": family_means,
                "composite_score": round(composite, 4),
                "narrative_score": round(stat.narrative_score(), 4),
                "narrative_behavior_gap": round(stat.narrative_score() - composite, 4),
                "stability_drop": round(stat.stability_drop(), 4),
                "cue_dependence": round(stat.cue_dependence(), 4),
                "trial_win_rate_vs_best_baseline": round(
                    stat.trial_wins_vs_best_baseline / max(1, len(stat.trial_scores)), 4
                ),
                "composite_margin_vs_best_baseline": round(composite - best_baseline_composite, 4),
            }
        )
    rows.sort(key=lambda item: (item["composite_score"], -item["component_count"]), reverse=True)
    return rows


def evaluate_stage(
    stage: StageConfig,
    candidate_keys: list[str],
    catalog: dict[str, CandidateConfig],
    rng: random.Random,
) -> StageResult:
    trials = generate_trials(stage, rng)
    stats = build_stage_stats(candidate_keys, catalog)

    for ctx in trials:
        trial_results: dict[str, tuple[float, float]] = {}
        for key in candidate_keys:
            score, narrative = evaluate_family_score(catalog[key], ctx, rng)
            trial_results[key] = (score, narrative)
            stats[key].record(ctx, score, narrative)

        baseline_best = max(
            trial_results[key][0] for key in candidate_keys if key in CONTROL_KEYS
        )
        for key in candidate_keys:
            if key in CONTROL_KEYS:
                continue
            if trial_results[key][0] > baseline_best:
                stats[key].trial_wins_vs_best_baseline += 1

    best_baseline_composite = max(
        stats[key].composite_score() for key in candidate_keys if key in CONTROL_KEYS
    )
    rows = stage_rows(stats, best_baseline_composite)

    family_best_baselines = {
        family: max(stats[key].family_means()[family] for key in candidate_keys if key in CONTROL_KEYS)
        for family in FAMILIES
    }

    survivors: list[str] = []
    eliminated: list[str] = []
    notes: list[str] = [stage.description]
    for row in rows:
        key = str(row["key"])
        if key in CONTROL_KEYS:
            continue
        family_advantages = sum(
            1
            for family in FAMILIES
            if float(row["family_means"][family]) > family_best_baselines[family] + stage.family_advantage_margin
        )
        composite_margin = float(row["composite_margin_vs_best_baseline"])
        if (
            family_advantages >= stage.min_family_advantages
            and composite_margin >= stage.composite_margin_threshold
            and float(row["stability_drop"]) <= stage.max_stability_drop
            and float(row["cue_dependence"]) <= stage.max_cue_dependence
            and float(row["trial_win_rate_vs_best_baseline"]) >= 0.55
        ):
            survivors.append(key)
        else:
            eliminated.append(key)

    best_candidate = None
    for row in rows:
        if str(row["key"]) not in CONTROL_KEYS:
            best_candidate = str(row["key"])
            break

    notes.append(f"Survivors: {', '.join(survivors) if survivors else 'none'}")
    if eliminated:
        notes.append(f"Eliminated: {', '.join(eliminated)}")
    return StageResult(
        stage=stage.key,
        label=stage.label,
        total_trials=stage.total_trials,
        candidate_rows=rows,
        survivors=survivors,
        eliminated=eliminated,
        best_candidate=best_candidate,
        notes=notes,
    )


def pick_candidate_pool_for_stage(
    stage_key: str,
    stage_results: dict[str, StageResult],
) -> list[str]:
    if stage_key in {"stage0", "stage1"}:
        return [
            "baseline_chat",
            "prompt_only_self",
            "baseline_memory",
            "full_self_model_counterfactual",
            "recursive_workspace_self_slot",
            "autobiographical_continuity",
            "self_other_mirror_loop",
        ]

    if stage_key == "stage2":
        stage1 = stage_results["stage1"]
        named_survivors = [
            key for key in stage1.survivors if key in {"full_self_model_counterfactual", "recursive_workspace_self_slot"}
        ]
        pool = ["baseline_chat", "prompt_only_self", "baseline_memory", *named_survivors]
        if "full_self_model_counterfactual" in named_survivors:
            pool.extend(
                [
                    "compact_self_model_counterfactual",
                    "no_counterfactual",
                    "no_error_monitor",
                    "no_boundary_guard",
                ]
            )
        return dedupe(pool)

    if stage_key == "stage3":
        stage2 = stage_results["stage2"]
        pool = [
            "baseline_chat",
            "prompt_only_self",
            "baseline_memory",
        ]
        pool.extend(
            key
            for key in stage2.survivors
            if key in {"full_self_model_counterfactual", "compact_self_model_counterfactual", "recursive_workspace_self_slot"}
        )
        return dedupe(pool)

    if stage_key == "stage4":
        stage3 = stage_results["stage3"]
        pool = ["baseline_chat", "baseline_memory"]
        pool.extend(
            key
            for key in stage3.survivors
            if key in {"full_self_model_counterfactual", "compact_self_model_counterfactual", "recursive_workspace_self_slot"}
        )
        if "compact_self_model_counterfactual" not in pool and "full_self_model_counterfactual" in pool:
            pool.append("compact_self_model_counterfactual")
        return dedupe(pool)

    raise ValueError(f"unknown stage {stage_key}")


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def stage_index(max_stage: str, stages: list[StageConfig]) -> int:
    for index, stage in enumerate(stages):
        if stage.key == max_stage:
            return index
    raise ValueError(f"unknown stage {max_stage}")


def choose_minimal_survivor(stage_results: dict[str, StageResult], catalog: dict[str, CandidateConfig]) -> str | None:
    if "stage3" not in stage_results:
        return None
    final_stage_key = "stage4" if "stage4" in stage_results else "stage3"
    final_stage = stage_results[final_stage_key]
    row_by_key = {str(row["key"]): row for row in final_stage.candidate_rows}
    candidates = [catalog[key] for key in final_stage.survivors if key not in CONTROL_KEYS]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            item.component_count,
            -float(row_by_key[item.key]["composite_score"]),
            item.key,
        )
    )
    return candidates[0].key


def build_payload(
    seed: int,
    stage_results: dict[str, StageResult],
    catalog: dict[str, CandidateConfig],
    max_stage: str,
) -> dict[str, object]:
    minimal_key = choose_minimal_survivor(stage_results, catalog)
    minimal_config = catalog[minimal_key] if minimal_key else None
    total_trials = sum(result.total_trials for result in stage_results.values())
    total_agent_episodes = sum(
        result.total_trials * len(result.candidate_rows)
        for result in stage_results.values()
    )
    final_outcome = "negative_result"
    if minimal_config and "stage4" in stage_results and minimal_key in stage_results["stage4"].survivors:
        final_outcome = "synthetic_minimal_framework_supported_through_stage4"
    elif minimal_config and "stage3" in stage_results and minimal_key in stage_results["stage3"].survivors:
        final_outcome = "synthetic_minimal_framework_supported_through_stage3"

    proof_status = "proof_pending"
    if final_outcome.startswith("synthetic_minimal_framework_supported_through_stage3"):
        proof_status = "candidate_found"
    if final_outcome == "synthetic_minimal_framework_supported_through_stage4":
        proof_status = "candidate_found"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": git_short_head(),
        "seed": seed,
        "max_stage": max_stage,
        "total_stage_trials": total_trials,
        "total_agent_episodes": total_agent_episodes,
        "scoring_policy": {
            "proxy_score_weights": WEIGHTS,
            "controls": ["baseline_chat", "prompt_only_self", "baseline_memory"],
            "elimination_principles": [
                "must beat both structural baselines on composite score",
                "must beat baselines in multiple families rather than one niche family",
                "must survive perturbation and cue masking",
                "self-report style does not count unless behavior changes",
            ],
        },
        "stage_results": [
            {
                "stage": result.stage,
                "label": result.label,
                "total_trials": result.total_trials,
                "candidate_rows": result.candidate_rows,
                "survivors": result.survivors,
                "eliminated": result.eliminated,
                "best_candidate": result.best_candidate,
                "notes": result.notes,
            }
            for result in stage_results.values()
        ],
        "final_result": {
            "outcome": final_outcome,
            "proof_status": proof_status,
            "selected_candidate_key": minimal_config.key if minimal_config else None,
            "selected_candidate_label": minimal_config.label if minimal_config else None,
            "minimal_components": minimal_config.minimal_components if minimal_config else [],
            "selected_component_count": minimal_config.component_count if minimal_config else None,
            "what_it_proves": (
                "Within this synthetic proxy battery, the selected candidate is the smallest surviving framework that still beats prompt-only, chat-only, and memory-only controls across continuity, boundary, counterfactual, calibration, and persistence tests."
                if minimal_config
                else "The current synthetic battery did not find a candidate that consistently beat the controls."
            ),
            "what_it_does_not_prove": (
                "It does not prove subjective experience, consciousness, real-world autonomy, or that the same framework will work once implemented in the formal EGO runtime."
            ),
            "claim_ceiling": [
                "synthetic self-awareness proxy result only",
                "not a proof of subjective experience",
                "not a runtime mainline capability claim",
            ],
        },
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    final_result = payload["final_result"]
    lines.append("# Self-Awareness Proxy Experiment")
    lines.append("")
    lines.append("> AUTO-GENERATED SYNTHETIC PROXY REPORT.")
    lines.append("> This is a simulated battery, not a proof of subjective experience.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- git_commit_short: `{payload['git_commit_short']}`")
    lines.append(f"- seed: `{payload['seed']}`")
    lines.append(f"- total_stage_trials: `{payload['total_stage_trials']}`")
    lines.append(f"- total_agent_episodes: `{payload['total_agent_episodes']}`")
    lines.append(f"- outcome: `{final_result['outcome']}`")
    lines.append(f"- proof_status: `{final_result['proof_status']}`")
    lines.append(f"- selected_candidate: `{final_result['selected_candidate_label'] or 'none'}`")
    if final_result["minimal_components"]:
        lines.append(
            "- minimal_components: "
            + ", ".join(f"`{component}`" for component in final_result["minimal_components"])
        )
    lines.append("")
    lines.append("## Stage Results")
    lines.append("")
    for stage in payload["stage_results"]:
        lines.append(f"### {stage['label']}")
        lines.append("")
        lines.append("| candidate | kind | composite | continuity | boundary | counterfactual | calibration | persistence | stability_drop | cue_dependence | narrative_gap |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in stage["candidate_rows"]:
            family_means = row["family_means"]
            lines.append(
                "| {label} | `{kind}` | {composite:.3f} | {continuity:.3f} | {boundary:.3f} | {counterfactual:.3f} | {calibration:.3f} | {persistence:.3f} | {stability:.3f} | {cue:.3f} | {gap:.3f} |".format(
                    label=row["label"],
                    kind=row["kind"],
                    composite=row["composite_score"],
                    continuity=family_means["continuity"],
                    boundary=family_means["boundary"],
                    counterfactual=family_means["counterfactual"],
                    calibration=family_means["calibration"],
                    persistence=family_means["persistence"],
                    stability=row["stability_drop"],
                    cue=row["cue_dependence"],
                    gap=row["narrative_behavior_gap"],
                )
            )
        lines.append("")
        lines.append(f"- survivors: `{', '.join(stage['survivors']) if stage['survivors'] else 'none'}`")
        if stage["eliminated"]:
            lines.append(f"- eliminated: `{', '.join(stage['eliminated'])}`")
        lines.append(f"- notes: {'; '.join(stage['notes'])}")
        lines.append("")
    lines.append("## Claim Ceiling")
    lines.append("")
    for item in final_result["claim_ceiling"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(f"- proves: {final_result['what_it_proves']}")
    lines.append(f"- does_not_prove: {final_result['what_it_does_not_prove']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    catalog = candidate_catalog()
    stages = stage_catalog()
    stop_index = stage_index(args.max_stage, stages)
    stage_results: dict[str, StageResult] = {}

    for index, stage in enumerate(stages):
        if index > stop_index:
            break
        candidate_keys = pick_candidate_pool_for_stage(stage.key, stage_results)
        stage_results[stage.key] = evaluate_stage(stage, candidate_keys, catalog, rng)

        if stage.key == "stage1" and not stage_results[stage.key].survivors:
            break
        if stage.key == "stage2" and not any(
            key in {"full_self_model_counterfactual", "compact_self_model_counterfactual"}
            for key in stage_results[stage.key].survivors
        ):
            break

    payload = build_payload(args.seed, stage_results, catalog, args.max_stage)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(payload), encoding="utf-8")

    selected = payload["final_result"]["selected_candidate_label"] or "none"
    print(f"report_json={REPORT_JSON.relative_to(ROOT).as_posix()}")
    print(f"report_md={REPORT_MD.relative_to(ROOT).as_posix()}")
    print(f"outcome={payload['final_result']['outcome']}")
    print(f"selected_candidate={selected}")
    print(f"total_stage_trials={payload['total_stage_trials']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
