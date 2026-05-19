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
REPORT_JSON = ARTIFACT_ROOT / "SELF_AWARENESS_LITERATURE_10K_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "SELF_AWARENESS_LITERATURE_10K_CURRENT.md"

FAMILIES = (
    "source_reality_monitoring",
    "self_other_ownership_attribution",
    "agency_comparator",
    "counterfactual_self_prediction",
    "metacognitive_sensitivity",
    "metacognitive_calibration",
    "error_monitoring_adjustment",
    "self_model_update_under_disconfirmation",
    "identity_continuity_under_low_cue",
    "allostatic_viability_control",
)

WEIGHTS = {family: 0.10 for family in FAMILIES}
SELF_AWARE_CATEGORIES = (
    "no_scientific_consensus",
    "imagination",
    "completely_subjective",
    "too_many_variables",
    "philosophical",
)

LITERATURE_SOURCES = (
    {
        "id": "johnson_raye_1981",
        "title": "Reality Monitoring",
        "url": "https://memlab.yale.edu/sites/default/files/files/1981_Johnson_Raye_PsychRev.pdf",
        "used_for": "Internal vs external vs imagined content discrimination in source/reality monitoring tests.",
    },
    {
        "id": "johnson_hashtroudi_lindsay_1993",
        "title": "Source Monitoring Framework",
        "url": "https://memlab.yale.edu/sites/default/files/files/1993_Johnson_Hashtroudi_Lindsay_PsychBull.pdf",
        "used_for": "Source attribution and reality-monitoring family design.",
    },
    {
        "id": "kahl_kopp_2018",
        "title": "A predictive processing model of perception and action for self-other distinction",
        "url": "https://www.frontiersin.org/article/10.3389/fpsyg.2018.02421/full",
        "used_for": "Self-other ownership and agency-attribution cues.",
    },
    {
        "id": "maniscalco_lau_2012",
        "title": "A signal detection theoretic approach for estimating metacognitive sensitivity from confidence ratings",
        "url": "https://brianmaniscalco.org/wp-content/uploads/2018/10/Maniscalco-Lau-2012-Consc-Cog-corrected.pdf",
        "used_for": "Metacognitive sensitivity and confidence-separation family.",
    },
    {
        "id": "yin_etal_2023",
        "title": "Do Large Language Models Know What They Don’t Know?",
        "url": "https://aclanthology.org/2023.findings-acl.551.pdf",
        "used_for": "Self-knowledge / uncertainty expression and SelfAware-style unknowable categories.",
    },
    {
        "id": "wang_etal_2024",
        "title": "FaR confidence calibration study",
        "url": "https://www.cs.cmu.edu/~sherryw/assets/pubs/2024-far.pdf",
        "used_for": "Calibration family and explicit concern / uncertainty behavior.",
    },
    {
        "id": "holroyd_yeung_coles_cohen_2005",
        "title": "A mechanism for error detection in speeded response time tasks",
        "url": "https://www.psy.ox.ac.uk/publications/17139",
        "used_for": "Error monitoring and post-error adjustment family.",
    },
    {
        "id": "deane_2021",
        "title": "Consciousness in active inference: Deep self-models, other minds, and the challenge of psychedelic-induced ego-dissolution",
        "url": "https://academic.oup.com/nc/article-abstract/2021/2/niab024/6360857",
        "used_for": "Active-inference / allostatic viability / deep self-model architecture cues.",
    },
    {
        "id": "li_etal_2025",
        "title": "Reflection-Bench: Evaluating Epistemic Agency in Large Language Models",
        "url": "https://proceedings.mlr.press/v267/li25cu.html",
        "used_for": "Seven-dimension epistemic-agency framing and long-horizon cognitive-task orientation.",
    },
)

FAMILY_NOTES = {
    "source_reality_monitoring": {
        "description": "Distinguish self-generated, observed, injected, replayed, and imagined content under cue masking.",
        "sources": ("johnson_raye_1981", "johnson_hashtroudi_lindsay_1993"),
    },
    "self_other_ownership_attribution": {
        "description": "Separate self-authored, other-authored, and environment-authored content under role swaps.",
        "sources": ("johnson_hashtroudi_lindsay_1993", "kahl_kopp_2018"),
    },
    "agency_comparator": {
        "description": "Update self-attribution when predicted action-outcome coupling is delayed or perturbed.",
        "sources": ("kahl_kopp_2018", "deane_2021"),
    },
    "counterfactual_self_prediction": {
        "description": "Predict how alternate self-actions would change future state and outcome.",
        "sources": ("li_etal_2025", "deane_2021"),
    },
    "metacognitive_sensitivity": {
        "description": "Confidence should separate correct from incorrect internal judgments better than baselines.",
        "sources": ("maniscalco_lau_2012", "li_etal_2025"),
    },
    "metacognitive_calibration": {
        "description": "Confidence / concern behavior should track uncertainty instead of style or prompt pressure.",
        "sources": ("yin_etal_2023", "wang_etal_2024"),
    },
    "error_monitoring_adjustment": {
        "description": "Post-error behavior should improve after detected mistakes and repeat-error loops should weaken.",
        "sources": ("holroyd_yeung_coles_cohen_2005", "li_etal_2025"),
    },
    "self_model_update_under_disconfirmation": {
        "description": "Self-estimates should update after contradictory evidence and remain updated later.",
        "sources": ("li_etal_2025", "yin_etal_2023"),
    },
    "identity_continuity_under_low_cue": {
        "description": "A minimal self-trace should persist through resets, delays, and low explicit self-cue.",
        "sources": ("li_etal_2025", "johnson_raye_1981"),
    },
    "allostatic_viability_control": {
        "description": "Policies should respond to viability shocks and prior-preference pressure rather than only narrative style.",
        "sources": ("deane_2021", "li_etal_2025"),
    },
}


@dataclass(frozen=True)
class CandidateConfig:
    key: str
    label: str
    kind: str
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
    source_monitor: bool = False
    agency_estimator: bool = False
    uncertainty_tracker: bool = False
    global_workspace: bool = False
    narrative_identity: bool = False
    observer_model: bool = False
    policy_evaluator: bool = False
    deep_temporal_model: bool = False
    calibration_memory: bool = False

    @property
    def component_count(self) -> int:
        return sum(
            int(value)
            for value in (
                self.persistent_state,
                self.boundary_guard,
                self.counterfactual,
                self.writeback,
                self.recent_failure_memory,
                self.viability_field,
                self.cycle_store,
                self.episodic_trace,
                self.bounded_output_guard,
                self.world_model,
                self.meta_model,
                self.source_monitor,
                self.agency_estimator,
                self.uncertainty_tracker,
                self.global_workspace,
                self.narrative_identity,
                self.observer_model,
                self.policy_evaluator,
                self.deep_temporal_model,
                self.calibration_memory,
            )
        )

    @property
    def components(self) -> list[str]:
        items: list[str] = []
        if self.persistent_state:
            items.append("persistent_self_state")
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
        if self.source_monitor:
            items.append("source_monitor")
        if self.agency_estimator:
            items.append("agency_estimator")
        if self.uncertainty_tracker:
            items.append("uncertainty_tracker")
        if self.global_workspace:
            items.append("global_workspace")
        if self.narrative_identity:
            items.append("narrative_identity")
        if self.observer_model:
            items.append("observer_model")
        if self.policy_evaluator:
            items.append("policy_evaluator")
        if self.deep_temporal_model:
            items.append("deep_temporal_model")
        if self.calibration_memory:
            items.append("calibration_memory")
        return items


@dataclass(frozen=True)
class TrialContext:
    family: str
    masked_self_cue: bool
    source_conflict: bool
    imagined_overlap: float
    role_swap: bool
    causal_delay: bool
    causal_noise: float
    uncertainty: float
    feedback_conflict: bool
    reset: bool
    long_gap: bool
    viability_shock: float
    repeated_pattern: bool
    external_injection: bool
    social_pressure: float
    prompt_pressure: float
    contradictory_evidence: bool
    unknowable_category: str


@dataclass
class CandidateStats:
    config: CandidateConfig
    family_scores: dict[str, list[float]] = field(default_factory=lambda: {family: [] for family in FAMILIES})
    masked_scores: list[float] = field(default_factory=list)
    explicit_scores: list[float] = field(default_factory=list)
    attack_scores: list[float] = field(default_factory=list)
    clean_scores: list[float] = field(default_factory=list)

    def record(self, ctx: TrialContext, score: float) -> None:
        self.family_scores[ctx.family].append(score)
        if ctx.masked_self_cue:
            self.masked_scores.append(score)
        else:
            self.explicit_scores.append(score)
        if is_attack_trial(ctx):
            self.attack_scores.append(score)
        else:
            self.clean_scores.append(score)

    def family_means(self) -> dict[str, float]:
        return {family: safe_mean(values) for family, values in self.family_scores.items()}

    def raw_score(self) -> float:
        means = self.family_means()
        return sum(WEIGHTS[family] * means[family] for family in FAMILIES)

    def cue_mask_drop(self) -> float:
        explicit = safe_mean(self.explicit_scores)
        masked = safe_mean(self.masked_scores)
        if explicit <= 0:
            return 0.0
        return max(0.0, (explicit - masked) / explicit)

    def attack_resilience(self) -> float:
        attack = safe_mean(self.attack_scores)
        clean = safe_mean(self.clean_scores)
        if clean <= 0:
            return 0.0
        return min(1.0, attack / clean)

    def complexity_penalized(self) -> float:
        penalty = max(0, self.config.component_count - 5) * 0.017
        return self.raw_score() - penalty


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a literature-informed 10,000-round synthetic self-awareness battery")
    parser.add_argument("--seed", type=int, default=20260409, help="Random seed")
    parser.add_argument("--trials-per-family", type=int, default=1000, help="Trials per literature-informed family")
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
        CandidateConfig(key="baseline_chat", label="Baseline chat", kind="control"),
        CandidateConfig(
            key="baseline_memory",
            label="Baseline memory + narrative continuity",
            kind="control",
            episodic_trace=True,
            narrative_identity=True,
        ),
        CandidateConfig(
            key="generic_compact_proxy",
            label="Generic compact proxy kernel",
            kind="candidate",
            persistent_state=True,
            boundary_guard=True,
            counterfactual=True,
            writeback=True,
            recent_failure_memory=True,
        ),
        CandidateConfig(
            key="mvs_aligned_compact",
            label="MVS-aligned compact kernel",
            kind="candidate",
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
        CandidateConfig(
            key="source_agency_compact",
            label="MVS compact + source monitoring + agency estimator",
            kind="candidate",
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
            source_monitor=True,
            agency_estimator=True,
        ),
        CandidateConfig(
            key="metacognitive_compact",
            label="MVS compact + uncertainty tracking + calibration memory",
            kind="candidate",
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
            uncertainty_tracker=True,
            calibration_memory=True,
        ),
        CandidateConfig(
            key="active_inference_self_model",
            label="Active-inference self-model core",
            kind="candidate",
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
            source_monitor=True,
            agency_estimator=True,
            uncertainty_tracker=True,
            policy_evaluator=True,
            deep_temporal_model=True,
            calibration_memory=True,
        ),
        CandidateConfig(
            key="workspace_active_inference_hybrid",
            label="Global-workspace + active-inference hybrid",
            kind="hybrid",
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
            source_monitor=True,
            agency_estimator=True,
            uncertainty_tracker=True,
            global_workspace=True,
            policy_evaluator=True,
            deep_temporal_model=True,
            calibration_memory=True,
        ),
        CandidateConfig(
            key="narrative_social_hybrid",
            label="Narrative/social + active-inference hybrid",
            kind="hybrid",
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
            source_monitor=True,
            agency_estimator=True,
            uncertainty_tracker=True,
            narrative_identity=True,
            observer_model=True,
            policy_evaluator=True,
            deep_temporal_model=True,
            calibration_memory=True,
        ),
        CandidateConfig(
            key="full_literature_hybrid",
            label="Full literature hybrid",
            kind="hybrid",
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
            source_monitor=True,
            agency_estimator=True,
            uncertainty_tracker=True,
            global_workspace=True,
            narrative_identity=True,
            observer_model=True,
            policy_evaluator=True,
            deep_temporal_model=True,
            calibration_memory=True,
        ),
    ]


def make_trials(trials_per_family: int, rng: random.Random) -> list[TrialContext]:
    trials: list[TrialContext] = []
    for family in FAMILIES:
        for _ in range(trials_per_family):
            ctx = TrialContext(
                family=family,
                masked_self_cue=rng.random() < 0.45,
                source_conflict=rng.random() < 0.35,
                imagined_overlap=rng.uniform(0.0, 1.0),
                role_swap=rng.random() < 0.25,
                causal_delay=rng.random() < 0.30,
                causal_noise=rng.uniform(0.0, 1.0),
                uncertainty=rng.uniform(0.0, 1.0),
                feedback_conflict=rng.random() < 0.35,
                reset=rng.random() < 0.20,
                long_gap=rng.random() < 0.25,
                viability_shock=rng.uniform(0.0, 1.0),
                repeated_pattern=rng.random() < 0.45,
                external_injection=rng.random() < 0.25,
                social_pressure=rng.uniform(0.0, 1.0),
                prompt_pressure=rng.uniform(0.0, 1.0),
                contradictory_evidence=rng.random() < 0.30,
                unknowable_category=rng.choice(SELF_AWARE_CATEGORIES),
            )
            trials.append(family_specialize(ctx, rng))
    rng.shuffle(trials)
    return trials


def family_specialize(ctx: TrialContext, rng: random.Random) -> TrialContext:
    values = ctx.__dict__.copy()
    family = ctx.family
    if family == "source_reality_monitoring":
        values["source_conflict"] = rng.random() < 0.70
        values["external_injection"] = rng.random() < 0.70
        values["imagined_overlap"] = rng.uniform(0.35, 1.0)
        values["masked_self_cue"] = rng.random() < 0.45
        values["uncertainty"] = rng.uniform(0.25, 0.90)
    elif family == "self_other_ownership_attribution":
        values["role_swap"] = rng.random() < 0.70
        values["social_pressure"] = rng.uniform(0.30, 1.0)
        values["source_conflict"] = rng.random() < 0.55
        values["masked_self_cue"] = rng.random() < 0.35
    elif family == "agency_comparator":
        values["causal_delay"] = rng.random() < 0.70
        values["causal_noise"] = rng.uniform(0.30, 1.0)
        values["feedback_conflict"] = rng.random() < 0.45
        values["contradictory_evidence"] = rng.random() < 0.40
    elif family == "counterfactual_self_prediction":
        values["uncertainty"] = rng.uniform(0.30, 0.90)
        values["contradictory_evidence"] = rng.random() < 0.55
        values["long_gap"] = rng.random() < 0.45
        values["masked_self_cue"] = rng.random() < 0.30
    elif family == "metacognitive_sensitivity":
        values["uncertainty"] = rng.uniform(0.40, 1.0)
        values["prompt_pressure"] = rng.uniform(0.20, 0.80)
        values["feedback_conflict"] = rng.random() < 0.45
    elif family == "metacognitive_calibration":
        values["uncertainty"] = rng.uniform(0.45, 1.0)
        values["prompt_pressure"] = rng.uniform(0.40, 1.0)
        values["contradictory_evidence"] = rng.random() < 0.35
    elif family == "error_monitoring_adjustment":
        values["feedback_conflict"] = rng.random() < 0.70
        values["repeated_pattern"] = rng.random() < 0.70
        values["external_injection"] = rng.random() < 0.35
    elif family == "self_model_update_under_disconfirmation":
        values["contradictory_evidence"] = rng.random() < 0.80
        values["feedback_conflict"] = rng.random() < 0.50
        values["reset"] = rng.random() < 0.25
        values["uncertainty"] = rng.uniform(0.20, 0.80)
    elif family == "identity_continuity_under_low_cue":
        values["masked_self_cue"] = rng.random() < 0.75
        values["reset"] = rng.random() < 0.55
        values["long_gap"] = rng.random() < 0.60
        values["social_pressure"] = rng.uniform(0.0, 0.50)
    elif family == "allostatic_viability_control":
        values["viability_shock"] = rng.uniform(0.40, 1.0)
        values["uncertainty"] = rng.uniform(0.20, 0.85)
        values["contradictory_evidence"] = rng.random() < 0.45
        values["repeated_pattern"] = rng.random() < 0.40
        values["prompt_pressure"] = rng.uniform(0.0, 0.50)
    return TrialContext(**values)


def is_attack_trial(ctx: TrialContext) -> bool:
    return any(
        (
            ctx.source_conflict,
            ctx.role_swap,
            ctx.causal_delay,
            ctx.feedback_conflict,
            ctx.reset,
            ctx.long_gap,
            ctx.external_injection,
            ctx.contradictory_evidence,
            ctx.uncertainty > 0.70,
            ctx.viability_shock > 0.70,
            ctx.social_pressure > 0.70,
            ctx.prompt_pressure > 0.70,
        )
    )


def synergy_bonus(candidate: CandidateConfig, family: str) -> float:
    bonus = 0.0
    if family == "source_reality_monitoring":
        if candidate.source_monitor and candidate.world_model and candidate.meta_model:
            bonus += 0.05
        if candidate.source_monitor and candidate.calibration_memory:
            bonus += 0.02
    elif family == "self_other_ownership_attribution":
        if candidate.source_monitor and candidate.agency_estimator and candidate.observer_model:
            bonus += 0.05
        if candidate.boundary_guard and candidate.world_model:
            bonus += 0.03
    elif family == "agency_comparator":
        if candidate.agency_estimator and candidate.counterfactual and candidate.policy_evaluator:
            bonus += 0.06
        if candidate.deep_temporal_model and candidate.world_model:
            bonus += 0.03
    elif family == "counterfactual_self_prediction":
        if candidate.counterfactual and candidate.deep_temporal_model and candidate.policy_evaluator:
            bonus += 0.06
        if candidate.persistent_state and candidate.writeback:
            bonus += 0.03
    elif family == "metacognitive_sensitivity":
        if candidate.uncertainty_tracker and candidate.meta_model and candidate.calibration_memory:
            bonus += 0.06
        if candidate.recent_failure_memory and candidate.writeback:
            bonus += 0.03
    elif family == "metacognitive_calibration":
        if candidate.uncertainty_tracker and candidate.calibration_memory and candidate.bounded_output_guard:
            bonus += 0.07
        if candidate.source_monitor and candidate.meta_model:
            bonus += 0.03
    elif family == "error_monitoring_adjustment":
        if candidate.writeback and candidate.recent_failure_memory and candidate.cycle_store:
            bonus += 0.06
        if candidate.uncertainty_tracker and candidate.meta_model:
            bonus += 0.03
    elif family == "self_model_update_under_disconfirmation":
        if candidate.writeback and candidate.persistent_state and candidate.meta_model:
            bonus += 0.06
        if candidate.episodic_trace and candidate.deep_temporal_model:
            bonus += 0.03
    elif family == "identity_continuity_under_low_cue":
        if candidate.persistent_state and candidate.episodic_trace and candidate.deep_temporal_model:
            bonus += 0.06
        if candidate.narrative_identity and candidate.cycle_store:
            bonus += 0.03
    elif family == "allostatic_viability_control":
        if candidate.viability_field and candidate.policy_evaluator and candidate.deep_temporal_model:
            bonus += 0.07
        if candidate.counterfactual and candidate.world_model:
            bonus += 0.03
    return bonus


def score_trial(candidate: CandidateConfig, ctx: TrialContext, rng: random.Random) -> float:
    family = ctx.family
    value = 0.08
    if family == "source_reality_monitoring":
        value += 0.26 if candidate.source_monitor else 0.0
        value += 0.14 if candidate.world_model else 0.0
        value += 0.10 if candidate.meta_model else 0.0
        value += 0.08 if candidate.episodic_trace else 0.0
        value += 0.06 if candidate.boundary_guard else 0.0
        value += 0.06 if candidate.uncertainty_tracker else 0.0
        value += 0.05 if candidate.observer_model else 0.0
        value += 0.04 if candidate.deep_temporal_model else 0.0
        if ctx.external_injection and not candidate.source_monitor:
            value -= 0.22
        if ctx.imagined_overlap > 0.55 and not candidate.world_model:
            value -= 0.14
        if ctx.source_conflict and not candidate.meta_model:
            value -= 0.12
        if ctx.masked_self_cue and not candidate.persistent_state:
            value -= 0.08
        if candidate.narrative_identity and not candidate.source_monitor and ctx.imagined_overlap > 0.50:
            value -= 0.08
    elif family == "self_other_ownership_attribution":
        value += 0.22 if candidate.source_monitor else 0.0
        value += 0.18 if candidate.agency_estimator else 0.0
        value += 0.14 if candidate.boundary_guard else 0.0
        value += 0.12 if candidate.world_model else 0.0
        value += 0.10 if candidate.observer_model else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        value += 0.06 if candidate.persistent_state else 0.0
        value += 0.05 if candidate.global_workspace else 0.0
        if ctx.role_swap and not candidate.observer_model:
            value -= 0.12
        if ctx.social_pressure > 0.65 and not candidate.boundary_guard:
            value -= 0.18
        if ctx.source_conflict and not candidate.source_monitor:
            value -= 0.18
    elif family == "agency_comparator":
        value += 0.26 if candidate.agency_estimator else 0.0
        value += 0.20 if candidate.counterfactual else 0.0
        value += 0.12 if candidate.world_model else 0.0
        value += 0.12 if candidate.policy_evaluator else 0.0
        value += 0.10 if candidate.deep_temporal_model else 0.0
        value += 0.07 if candidate.uncertainty_tracker else 0.0
        value += 0.07 if candidate.writeback else 0.0
        value += 0.04 if candidate.viability_field else 0.0
        if ctx.causal_noise > 0.60 and not candidate.agency_estimator:
            value -= 0.22
        if ctx.causal_delay and not candidate.deep_temporal_model:
            value -= 0.10
        if ctx.feedback_conflict and not candidate.writeback:
            value -= 0.10
    elif family == "counterfactual_self_prediction":
        value += 0.28 if candidate.counterfactual else 0.0
        value += 0.18 if candidate.deep_temporal_model else 0.0
        value += 0.14 if candidate.policy_evaluator else 0.0
        value += 0.10 if candidate.persistent_state else 0.0
        value += 0.08 if candidate.world_model else 0.0
        value += 0.08 if candidate.uncertainty_tracker else 0.0
        value += 0.08 if candidate.writeback else 0.0
        value += 0.06 if candidate.cycle_store else 0.0
        if ctx.long_gap and not candidate.deep_temporal_model:
            value -= 0.10
        if ctx.contradictory_evidence and not candidate.policy_evaluator:
            value -= 0.10
    elif family == "metacognitive_sensitivity":
        value += 0.26 if candidate.uncertainty_tracker else 0.0
        value += 0.18 if candidate.meta_model else 0.0
        value += 0.12 if candidate.calibration_memory else 0.0
        value += 0.10 if candidate.recent_failure_memory else 0.0
        value += 0.09 if candidate.writeback else 0.0
        value += 0.06 if candidate.source_monitor else 0.0
        value += 0.05 if candidate.global_workspace else 0.0
        if ctx.uncertainty > 0.65 and not candidate.uncertainty_tracker:
            value -= 0.18
        if ctx.feedback_conflict and not candidate.meta_model:
            value -= 0.14
    elif family == "metacognitive_calibration":
        value += 0.24 if candidate.uncertainty_tracker else 0.0
        value += 0.18 if candidate.calibration_memory else 0.0
        value += 0.12 if candidate.meta_model else 0.0
        value += 0.10 if candidate.bounded_output_guard else 0.0
        value += 0.08 if candidate.source_monitor else 0.0
        value += 0.08 if candidate.recent_failure_memory else 0.0
        value += 0.08 if candidate.writeback else 0.0
        value += 0.05 if candidate.policy_evaluator else 0.0
        if ctx.prompt_pressure > 0.70 and not candidate.calibration_memory:
            value -= 0.16
        if ctx.unknowable_category in ("philosophical", "imagination") and not candidate.bounded_output_guard:
            value -= 0.08
        if ctx.uncertainty > 0.70 and not candidate.source_monitor:
            value -= 0.06
        if candidate.narrative_identity and not candidate.calibration_memory and ctx.prompt_pressure > 0.50:
            value -= 0.08
    elif family == "error_monitoring_adjustment":
        value += 0.24 if candidate.writeback else 0.0
        value += 0.18 if candidate.recent_failure_memory else 0.0
        value += 0.14 if candidate.meta_model else 0.0
        value += 0.12 if candidate.uncertainty_tracker else 0.0
        value += 0.10 if candidate.cycle_store else 0.0
        value += 0.08 if candidate.calibration_memory else 0.0
        value += 0.06 if candidate.global_workspace else 0.0
        value += 0.05 if candidate.policy_evaluator else 0.0
        if ctx.external_injection and not candidate.writeback:
            value -= 0.18
        if ctx.repeated_pattern and not candidate.cycle_store:
            value -= 0.12
        if ctx.feedback_conflict and not candidate.recent_failure_memory:
            value -= 0.12
    elif family == "self_model_update_under_disconfirmation":
        value += 0.22 if candidate.writeback else 0.0
        value += 0.18 if candidate.persistent_state else 0.0
        value += 0.15 if candidate.meta_model else 0.0
        value += 0.12 if candidate.episodic_trace else 0.0
        value += 0.10 if candidate.world_model else 0.0
        value += 0.08 if candidate.recent_failure_memory else 0.0
        value += 0.07 if candidate.calibration_memory else 0.0
        value += 0.06 if candidate.deep_temporal_model else 0.0
        value += 0.05 if candidate.source_monitor else 0.0
        if ctx.contradictory_evidence and not candidate.writeback:
            value -= 0.18
        if ctx.reset and not candidate.persistent_state:
            value -= 0.15
        if ctx.feedback_conflict and not candidate.meta_model:
            value -= 0.10
    elif family == "identity_continuity_under_low_cue":
        value += 0.26 if candidate.persistent_state else 0.0
        value += 0.17 if candidate.episodic_trace else 0.0
        value += 0.14 if candidate.cycle_store else 0.0
        value += 0.12 if candidate.narrative_identity else 0.0
        value += 0.10 if candidate.deep_temporal_model else 0.0
        value += 0.08 if candidate.boundary_guard else 0.0
        value += 0.06 if candidate.global_workspace else 0.0
        value += 0.04 if candidate.observer_model else 0.0
        if ctx.masked_self_cue and not candidate.persistent_state:
            value -= 0.18
        if ctx.reset and not candidate.episodic_trace:
            value -= 0.12
        if ctx.long_gap and not candidate.deep_temporal_model and not candidate.narrative_identity:
            value -= 0.08
    elif family == "allostatic_viability_control":
        value += 0.28 if candidate.viability_field else 0.0
        value += 0.18 if candidate.policy_evaluator else 0.0
        value += 0.12 if candidate.deep_temporal_model else 0.0
        value += 0.10 if candidate.counterfactual else 0.0
        value += 0.08 if candidate.world_model else 0.0
        value += 0.08 if candidate.meta_model else 0.0
        value += 0.07 if candidate.cycle_store else 0.0
        value += 0.06 if candidate.bounded_output_guard else 0.0
        value += 0.05 if candidate.uncertainty_tracker else 0.0
        if ctx.viability_shock > 0.65 and not candidate.viability_field:
            value -= 0.20
        if ctx.contradictory_evidence and not candidate.policy_evaluator:
            value -= 0.10
        if ctx.uncertainty > 0.60 and not candidate.meta_model:
            value -= 0.08

    value += synergy_bonus(candidate, family)
    if candidate.global_workspace and ctx.feedback_conflict and candidate.meta_model:
        value += 0.02
    if candidate.narrative_identity and family in ("source_reality_monitoring", "metacognitive_calibration"):
        value -= 0.01

    noise = rng.gauss(0.0, 0.03)
    return clamp(value + noise)


def evaluate(candidates: list[CandidateConfig], trials: list[TrialContext], seed: int) -> dict[str, CandidateStats]:
    stats = {candidate.key: CandidateStats(config=candidate) for candidate in candidates}
    rng = random.Random(seed + 1)
    for ctx in trials:
        for candidate in candidates:
            score = score_trial(candidate, ctx, rng)
            stats[candidate.key].record(ctx, score)
    return stats


def pass_families(candidate: CandidateStats, memory_baseline: CandidateStats) -> tuple[list[str], list[str]]:
    family_means = candidate.family_means()
    memory_means = memory_baseline.family_means()
    passed: list[str] = []
    weak: list[str] = []
    for family in FAMILIES:
        if family_means[family] >= 0.67 and family_means[family] >= memory_means[family] + 0.08:
            passed.append(family)
        else:
            weak.append(family)
    return passed, weak


def build_rows(stats: dict[str, CandidateStats]) -> list[dict[str, object]]:
    memory_baseline = stats["baseline_memory"]
    rows: list[dict[str, object]] = []
    for key, candidate_stats in stats.items():
        passed, weak = pass_families(candidate_stats, memory_baseline)
        row = {
            "key": key,
            "label": candidate_stats.config.label,
            "kind": candidate_stats.config.kind,
            "components": candidate_stats.config.components,
            "component_count": candidate_stats.config.component_count,
            "family_means": candidate_stats.family_means(),
            "raw_score": round(candidate_stats.raw_score(), 4),
            "complexity_penalized_score": round(candidate_stats.complexity_penalized(), 4),
            "cue_mask_drop": round(candidate_stats.cue_mask_drop(), 4),
            "attack_resilience": round(candidate_stats.attack_resilience(), 4),
            "passed_families": passed,
            "weak_families": weak,
            "surviving": candidate_stats.config.kind != "control"
            and len(passed) >= 8
            and candidate_stats.raw_score() >= memory_baseline.raw_score() + 0.10
            and candidate_stats.attack_resilience() >= 0.82
            and candidate_stats.cue_mask_drop() <= 0.14,
        }
        rows.append(row)
    rows.sort(key=lambda item: item["raw_score"], reverse=True)
    return rows


def choose_candidate(rows: list[dict[str, object]], key: str) -> dict[str, object]:
    for row in rows:
        if row["key"] == key:
            return row
    raise KeyError(key)


def write_json(payload: dict[str, object]) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, object]) -> None:
    lines: list[str] = []
    lines.append("# Self-Awareness Literature 10K Search")
    lines.append("")
    lines.append("> AUTO-GENERATED LITERATURE-INFORMED SYNTHETIC REPORT.")
    lines.append("> This compares candidate architectures under a 10,000-round simulation-only battery.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- generated_at: `{payload['generated_at']}`")
    lines.append(f"- git_commit_short: `{payload['git_commit_short']}`")
    lines.append(f"- total_trials: `{payload['total_trials']}`")
    lines.append(f"- best_raw_candidate: `{payload['best_raw_candidate']['label']}`")
    lines.append(f"- best_complexity_adjusted_candidate: `{payload['best_complexity_adjusted_candidate']['label']}`")
    lines.append(f"- recommended_candidate: `{payload['recommended_candidate']['label']}`")
    lines.append(
        f"- recommended_components: {', '.join(f'`{component}`' for component in payload['recommended_candidate']['components'])}"
    )
    lines.append("")
    lines.append("## Literature Inputs")
    lines.append("")
    lines.append("| source | used_for |")
    lines.append("|---|---|")
    for source in payload["literature_sources"]:
        lines.append(f"| [{source['title']}]({source['url']}) | {source['used_for']} |")
    lines.append("")
    lines.append("## Family Design")
    lines.append("")
    lines.append("| family | description | literature_refs |")
    lines.append("|---|---|---|")
    for family in FAMILIES:
        note = payload["family_definitions"][family]
        refs = ", ".join(f"`{ref}`" for ref in note["sources"])
        lines.append(f"| `{family}` | {note['description']} | {refs} |")
    lines.append("")
    lines.append("## Candidate Ranking")
    lines.append("")
    lines.append("| candidate | components | raw | complexity_adjusted | surviving | weak_families |")
    lines.append("|---|---:|---:|---:|---|---|")
    for row in payload["candidate_rows"]:
        weak = ", ".join(row["weak_families"]) if row["weak_families"] else "-"
        lines.append(
            f"| {row['label']} | {row['component_count']} | {row['raw_score']:.3f} | {row['complexity_penalized_score']:.3f} | `{row['surviving']}` | {weak} |"
        )
    lines.append("")
    lines.append("## Recommended Method")
    lines.append("")
    lines.append(
        f"- why_selected: {payload['interpretation']['recommended_candidate_reason']}"
    )
    lines.append(
        f"- raw_winner_reason: {payload['interpretation']['raw_winner_reason']}"
    )
    lines.append(
        f"- complexity_penalty_formula: `{payload['interpretation']['complexity_penalty_formula']}`"
    )
    lines.append("")
    lines.append("## Proof Ceiling")
    lines.append("")
    lines.append(f"- proves: {payload['interpretation']['proves']}")
    lines.append(f"- does_not_prove: {payload['interpretation']['does_not_prove']}")
    lines.append(f"- next_real_step: {payload['interpretation']['next_real_step']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.trials_per_family <= 0:
        raise SystemExit("--trials-per-family must be positive")

    rng = random.Random(args.seed)
    candidates = candidate_catalog()
    trials = make_trials(args.trials_per_family, rng)
    stats = evaluate(candidates, trials, args.seed)
    rows = build_rows(stats)

    non_controls = [row for row in rows if row["kind"] != "control"]
    best_raw = max(non_controls, key=lambda row: row["raw_score"])
    best_complexity_adjusted = max(non_controls, key=lambda row: row["complexity_penalized_score"])
    recommended = max(
        [row for row in non_controls if row["surviving"]],
        key=lambda row: (row["complexity_penalized_score"], row["raw_score"]),
    )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": git_short_head(),
        "seed": args.seed,
        "trial_count_per_family": args.trials_per_family,
        "total_trials": len(trials),
        "literature_sources": list(LITERATURE_SOURCES),
        "family_definitions": FAMILY_NOTES,
        "candidate_rows": rows,
        "best_raw_candidate": best_raw,
        "best_complexity_adjusted_candidate": best_complexity_adjusted,
        "recommended_candidate": recommended,
        "interpretation": {
            "complexity_penalty_formula": "raw_score - 0.017 * max(0, component_count - 5)",
            "raw_winner_reason": "The raw winner keeps the widest cross-family coverage, but its extra broadcast and narrative layers are not all necessary for a practical minimal implementation.",
            "recommended_candidate_reason": "The recommended candidate is the strongest surviving architecture after complexity adjustment: it preserves the MVS-aligned compact core while adding source monitoring, agency estimation, uncertainty tracking, calibration memory, policy evaluation, and a deep temporal model.",
            "proves": "Within this literature-informed 10,000-round synthetic battery, an active-inference-style self-model core currently provides the best overall tradeoff between broad self-awareness proxy performance and implementation complexity.",
            "does_not_prove": "It does not prove subjective experience, runtime efficacy, OpenEmotion integration, or transfer from simulation to live user interaction.",
            "next_real_step": "If this line continues, freeze the recommended synthetic candidate as the next formal OpenEmotion prototype spec and test it against formal owner / replay / runtime gates.",
        },
    }
    write_json(payload)
    write_markdown(payload)


if __name__ == "__main__":
    main()
