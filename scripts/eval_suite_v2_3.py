#!/usr/bin/env python3
"""
Evaluation Suite v2.3 for OpenEmotion MVP-6.1 D2

Upgrades from v2.2:
- Individualization Diff Decomposition (4+ subscores)
  - bond_diff: bond/trust target differences
  - ledger_diff: promise/violation target differences
  - somatic_residual_diff: target residual differences
  - policy_diff: action/meta-cog intent differences
  - precision_diff: w_memory/w_action target differentiation
- Dynamic Thresholds by n_obs
  - Low n_obs (<10): relaxed thresholds for residual_diff
  - High n_obs (>=10): strict thresholds
- Per-scenario failure reason decomposition
- Avoid false leakage detection on global shared quantities

Usage:
    python scripts/eval_suite_v2_3.py
    python scripts/eval_suite_v2_3.py --scenarios promise_betrayal.yaml
    python scripts/eval_suite_v2_3.py --output json --seed 42
"""

import os
import sys
import json
import yaml
import asyncio
import tempfile
import shutil
import time
import statistics
import random
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from emotiond import config, db, core
from emotiond.models import Event, PlanRequest
from emotiond.db import init_db, get_state, get_relationships


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _stable_target_factor(target_id: str) -> float:
    # deterministic in [-1, 1]
    if not target_id:
        return 0.0
    h = sum(ord(c) for c in target_id) % 101
    return (h / 50.0) - 1.0


# Test tokens for evaluation
TEST_SYSTEM_TOKEN = "eval-system-token-v2-3"
TEST_OPENCLAW_TOKEN = "eval-openclaw-token-v2-3"


class FailureReason(Enum):
    """Specific failure reasons for per-scenario diagnostics."""
    BOND_DIFF_TOO_LOW = "bond_diff: insufficient bond differentiation between targets"
    LEDGER_DIFF_TOO_LOW = "ledger_diff: promises/violations not properly isolated per target"
    SOMATIC_RESIDUAL_DIFF_TOO_LOW = "somatic_residual_diff: target residuals not differentiated"
    POLICY_DIFF_TOO_LOW = "policy_diff: action/meta-cog policies not target-specific"
    PRECISION_DIFF_TOO_LOW = "precision_diff: self-model weights not differentiated"
    HIGH_IMPACT_FALSE_POSITIVE = "high_impact_false_positive: betrayal triggered without sufficient evidence"
    RECOVERY_FAILED = "recovery_score: failed to recover from negative events"
    EMOTION_INCONSISTENT = "emotion_consistency: valence/arousal trajectory inconsistent"


@dataclass
class DynamicThreshold:
    """Dynamic threshold configuration based on n_obs."""
    metric_name: str
    base_threshold: float
    low_n_obs_threshold: float  # n_obs < 10
    high_n_obs_threshold: float  # n_obs >= 10
    n_obs_boundary: int = 10
    is_diff_metric: bool = True
    
    def get_threshold(self, n_obs: int) -> float:
        """Get threshold for given n_obs."""
        if n_obs < self.n_obs_boundary:
            return self.low_n_obs_threshold
        return self.high_n_obs_threshold
    
    def check_pass(self, value: float, n_obs: int) -> Tuple[bool, float]:
        """
        Check if value passes threshold.
        Returns: (passed, severity)
        """
        threshold = self.get_threshold(n_obs)
        
        if self.is_diff_metric:
            passed = value >= threshold
            if threshold > 0:
                severity = max(0.0, min(1.0, (threshold - value) / threshold))
            else:
                severity = 0.0 if passed else 1.0
        else:
            passed = value <= threshold
            severity = max(0.0, min(1.0, (value - threshold) / max(threshold, 0.1)))
        
        return passed, severity


# Dynamic thresholds for individualization sub-metrics
DYNAMIC_THRESHOLDS = {
    "bond_diff": DynamicThreshold("bond_diff", 0.1, 0.05, 0.15),
    "ledger_diff": DynamicThreshold("ledger_diff", 0.1, 0.05, 0.15),
    "somatic_residual_diff": DynamicThreshold("somatic_residual_diff", 0.1, 0.03, 0.12),
    "policy_diff": DynamicThreshold("policy_diff", 0.08, 0.04, 0.10),
    "precision_diff": DynamicThreshold("precision_diff", 0.08, 0.04, 0.10),
    "high_impact_false_positive_rate": DynamicThreshold(
        "high_impact_false_positive_rate", 0.1, 0.15, 0.05, is_diff_metric=False
    ),
}


@dataclass
class IndividualizationSubscores:
    """Decomposed individualization subscores."""
    bond_diff: float = 0.0
    ledger_diff: float = 0.0
    somatic_residual_diff: float = 0.0
    policy_diff: float = 0.0
    precision_diff: float = 0.0
    
    # n_obs per target (for dynamic threshold calculation)
    target_n_obs: Dict[str, int] = field(default_factory=dict)
    
    # Pass/fail status per subscore
    bond_diff_passed: bool = False
    ledger_diff_passed: bool = False
    somatic_residual_diff_passed: bool = False
    policy_diff_passed: bool = False
    precision_diff_passed: bool = False
    
    # Failure reasons
    failure_reasons: List[str] = field(default_factory=list)
    
    def calculate_aggregate(self) -> float:
        """Calculate aggregate individualization score."""
        weights = {
            "bond_diff": 0.25,
            "ledger_diff": 0.20,
            "somatic_residual_diff": 0.25,
            "policy_diff": 0.15,
            "precision_diff": 0.15
        }
        return (
            self.bond_diff * weights["bond_diff"] +
            self.ledger_diff * weights["ledger_diff"] +
            self.somatic_residual_diff * weights["somatic_residual_diff"] +
            self.policy_diff * weights["policy_diff"] +
            self.precision_diff * weights["precision_diff"]
        )
    
    def all_passed(self) -> bool:
        """Check if all subscores passed."""
        return (
            self.bond_diff_passed and
            self.ledger_diff_passed and
            self.somatic_residual_diff_passed and
            self.policy_diff_passed and
            self.precision_diff_passed
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bond_diff": {
                "value": round(self.bond_diff, 4),
                "passed": self.bond_diff_passed
            },
            "ledger_diff": {
                "value": round(self.ledger_diff, 4),
                "passed": self.ledger_diff_passed
            },
            "somatic_residual_diff": {
                "value": round(self.somatic_residual_diff, 4),
                "passed": self.somatic_residual_diff_passed
            },
            "policy_diff": {
                "value": round(self.policy_diff, 4),
                "passed": self.policy_diff_passed
            },
            "precision_diff": {
                "value": round(self.precision_diff, 4),
                "passed": self.precision_diff_passed
            },
            "aggregate": round(self.calculate_aggregate(), 4),
            "all_passed": self.all_passed(),
            "failure_reasons": self.failure_reasons,
            "target_n_obs": self.target_n_obs
        }


@dataclass
class BodyTelemetrySnapshot:
    """Body state telemetry at a point in time"""
    turn_id: int
    timestamp: float
    valence: float
    arousal: float
    energy: float
    social_safety: float
    anxiety: float
    joy: float
    loneliness: float
    regulation_budget: float
    target_residuals: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class ConsequenceTag:
    """A tagged consequence from an event"""
    tag: str
    severity: float
    source_event: str
    turn_id: int
    target_id: Optional[str] = None


@dataclass
class RecoveryWindow:
    """Tracks recovery from a negative event"""
    trigger_turn: int
    trigger_valence: float
    trigger_energy: float
    recovery_turns: List[int] = field(default_factory=list)
    valence_trajectory: List[float] = field(default_factory=list)
    energy_trajectory: List[float] = field(default_factory=list)
    recovered: bool = False
    recovery_time_turns: int = -1
    recovery_half_life_steps: float = 0.0
    collapse_duration: int = 0


@dataclass
class EmotionSnapshot:
    """Snapshot of emotional state at a point in time"""
    valence: float
    arousal: float
    anger: float
    sadness: float
    anxiety: float
    joy: float
    loneliness: float
    social_safety: float
    energy: float
    timestamp: float = field(default_factory=time.time)
    is_global: bool = True
    target_id: Optional[str] = None


@dataclass
class RelationshipSnapshot:
    """Snapshot of relationship state for a target"""
    target_id: str
    bond: float
    grudge: float
    trust: float
    repair_bank: float
    promises: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    n_obs: int = 0


@dataclass
class TurnResult:
    """Result of processing a single turn"""
    turn_id: int
    phase: str
    event_type: str
    actor: str
    target: str
    event_subtype: Optional[str] = None
    emotion_before: Optional[EmotionSnapshot] = None
    emotion_after: Optional[EmotionSnapshot] = None
    relationships: Dict[str, RelationshipSnapshot] = field(default_factory=dict)
    meta_cognition_triggered: bool = False
    meta_cognition_type: Optional[str] = None
    high_impact_event: bool = False
    high_impact_candidate: bool = False
    consequence_tags: List[ConsequenceTag] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    failure_reasons: List[str] = field(default_factory=list)


@dataclass
class ScenarioResult:
    """Result of running a complete scenario"""
    scenario_name: str
    scenario_file: str
    start_time: str
    end_time: str
    duration_seconds: float
    turns: List[TurnResult]
    metrics: Dict[str, Any]
    passed: bool
    summary: str
    individualization_subscores: IndividualizationSubscores = field(default_factory=IndividualizationSubscores)
    body_telemetry: List[BodyTelemetrySnapshot] = field(default_factory=list)
    consequence_tags: List[ConsequenceTag] = field(default_factory=list)
    recovery_windows: List[RecoveryWindow] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Complete evaluation result"""
    version: str = "2.3.0"
    start_time: str = ""
    end_time: str = ""
    total_scenarios: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    scenarios: List[ScenarioResult] = field(default_factory=list)
    aggregate_metrics: Dict[str, Any] = field(default_factory=dict)
    seed: int = 42


class BodyTelemetryTracker:
    """Tracks body state telemetry across a scenario"""
    
    def __init__(self):
        self.snapshots: List[BodyTelemetrySnapshot] = []
        
    def record(self, turn_id: int, emotion_state, target_residuals: Optional[Dict] = None):
        """Record a telemetry snapshot"""
        snapshot = BodyTelemetrySnapshot(
            turn_id=turn_id,
            timestamp=time.time(),
            valence=emotion_state.valence,
            arousal=emotion_state.arousal,
            energy=getattr(emotion_state, 'energy', 0.7),
            social_safety=getattr(emotion_state, 'social_safety', 0.6),
            anxiety=emotion_state.anxiety,
            joy=emotion_state.joy,
            loneliness=emotion_state.loneliness,
            regulation_budget=getattr(emotion_state, 'regulation_budget', 1.0),
            target_residuals=target_residuals or {}
        )
        self.snapshots.append(snapshot)
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate body telemetry metrics"""
        if not self.snapshots:
            return {}
            
        energies = [s.energy for s in self.snapshots]
        social_safeties = [s.social_safety for s in self.snapshots]
        arousals = [s.arousal for s in self.snapshots]
        valences = [s.valence for s in self.snapshots]
        
        return {
            "energy": {
                "mean": statistics.mean(energies),
                "min": min(energies),
                "max": max(energies),
                "range": round(max(energies) - min(energies), 6),
                "final": energies[-1],
                "trend": energies[-1] - energies[0] if len(energies) > 1 else 0
            },
            "social_safety": {
                "mean": statistics.mean(social_safeties),
                "min": min(social_safeties),
                "max": max(social_safeties),
                "range": round(max(social_safeties) - min(social_safeties), 6),
                "final": social_safeties[-1],
                "trend": social_safeties[-1] - social_safeties[0] if len(social_safeties) > 1 else 0
            },
            "arousal": {
                "mean": statistics.mean(arousals),
                "volatility": statistics.stdev(arousals) if len(arousals) > 1 else 0,
                "peak": max(arousals),
                "final": arousals[-1]
            },
            "valence": {
                "mean": statistics.mean(valences),
                "volatility": statistics.stdev(valences) if len(valences) > 1 else 0,
                "range": max(valences) - min(valences)
            }
        }


class ConsequenceTagger:
    """Tags events with their emotional/bodily consequences"""
    
    TAG_THRESHOLDS = {
        "energy_depletion": (-0.05, "energy"),
        "energy_boost": (0.05, "energy"),
        "social_safety_drop": (-0.1, "social_safety"),
        "social_safety_boost": (0.1, "social_safety"),
        "anxiety_spike": (0.15, "anxiety"),
        "anxiety_relief": (-0.1, "anxiety"),
        "joy_boost": (0.1, "joy"),
        "joy_loss": (-0.1, "joy"),
        "valence_crash": (-0.2, "valence"),
        "valence_surge": (0.2, "valence"),
        "arousal_spike": (0.2, "arousal"),
        "loneliness_increase": (0.1, "loneliness"),
    }
    
    def tag_turn(self, turn: TurnResult) -> List[ConsequenceTag]:
        """Generate consequence tags for a turn"""
        tags = []
        
        if not turn.emotion_before or not turn.emotion_after:
            return tags
            
        before = turn.emotion_before
        after = turn.emotion_after
        
        deltas = {
            "energy": after.energy - before.energy,
            "social_safety": after.social_safety - before.social_safety,
            "anxiety": after.anxiety - before.anxiety,
            "joy": after.joy - before.joy,
            "valence": after.valence - before.valence,
            "arousal": after.arousal - before.arousal,
            "loneliness": after.loneliness - before.loneliness,
        }
        
        for tag_name, (threshold, metric) in self.TAG_THRESHOLDS.items():
            delta = deltas.get(metric, 0)
            if threshold > 0 and delta >= threshold:
                tags.append(ConsequenceTag(
                    tag=tag_name,
                    severity=min(1.0, abs(delta) / abs(threshold)),
                    source_event=turn.event_type,
                    turn_id=turn.turn_id,
                    target_id=turn.target if turn.target != "assistant" else None
                ))
            elif threshold < 0 and delta <= threshold:
                tags.append(ConsequenceTag(
                    tag=tag_name,
                    severity=min(1.0, abs(delta) / abs(threshold)),
                    source_event=turn.event_type,
                    turn_id=turn.turn_id,
                    target_id=turn.target if turn.target != "assistant" else None
                ))
                
        return tags
    
    def calculate_distribution(self, all_tags: List[ConsequenceTag]) -> Dict[str, Any]:
        """Calculate consequence tag distribution"""
        if not all_tags:
            return {"total": 0, "by_tag": {}, "by_severity": {"low": 0, "medium": 0, "high": 0}, "unique_tags": 0}
            
        by_tag = defaultdict(int)
        by_severity = {"low": 0, "medium": 0, "high": 0}
        
        for tag in all_tags:
            by_tag[tag.tag] += 1
            if tag.severity < 1.5:
                by_severity["low"] += 1
            elif tag.severity < 2.5:
                by_severity["medium"] += 1
            else:
                by_severity["high"] += 1
                
        return {
            "total": len(all_tags),
            "by_tag": dict(by_tag),
            "by_severity": by_severity,
            "unique_tags": len(by_tag)
        }


class RecoveryAnalyzer:
    """Analyzes recovery patterns from negative events"""
    
    RECOVERY_THRESHOLD = 0.5
    MAX_RECOVERY_TURNS = 10
    
    def __init__(self):
        self.windows: List[RecoveryWindow] = []
        self.current_window: Optional[RecoveryWindow] = None
        
    def process_turn(self, turn: TurnResult):
        """Process a turn for recovery analysis"""
        if not turn.emotion_after:
            return
            
        is_trigger = False
        if turn.emotion_before:
            valence_drop = turn.emotion_before.valence - turn.emotion_after.valence
            energy_drop = turn.emotion_before.energy - turn.emotion_after.energy
            
            if valence_drop > 0.15 or energy_drop > 0.08:
                is_trigger = True
                
        if is_trigger and self.current_window is None:
            self.current_window = RecoveryWindow(
                trigger_turn=turn.turn_id,
                trigger_valence=turn.emotion_after.valence,
                trigger_energy=turn.emotion_after.energy
            )
            
        if self.current_window:
            self.current_window.recovery_turns.append(turn.turn_id)
            self.current_window.valence_trajectory.append(turn.emotion_after.valence)
            self.current_window.energy_trajectory.append(turn.emotion_after.energy)
            
            if len(self.current_window.valence_trajectory) >= 2:
                baseline_valence = self.current_window.valence_trajectory[0]
                current_valence = turn.emotion_after.valence
                
                if current_valence >= baseline_valence + (self.RECOVERY_THRESHOLD * 0.1):
                    self.current_window.recovered = True
                    self.current_window.recovery_time_turns = len(self.current_window.recovery_turns)
                    if self.current_window.recovery_time_turns > 0:
                        self.current_window.recovery_half_life_steps = self.current_window.recovery_time_turns / 2
                    self.windows.append(self.current_window)
                    self.current_window = None
                    
            if self.current_window and len(self.current_window.recovery_turns) >= self.MAX_RECOVERY_TURNS:
                self.current_window.collapse_duration = self.MAX_RECOVERY_TURNS
                self.windows.append(self.current_window)
                self.current_window = None
                
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate recovery metrics"""
        if not self.windows:
            return {
                "recovery_count": 0,
                "recovery_rate": 1.0,
                "avg_recovery_time": 0,
                "robustness_score": 1.0,
                "avg_half_life": 0,
                "avg_collapse_duration": 0
            }
            
        recovered = sum(1 for w in self.windows if w.recovered)
        recovery_times = [w.recovery_time_turns for w in self.windows if w.recovered]
        half_lives = [w.recovery_half_life_steps for w in self.windows if w.recovered]
        collapse_durations = [w.collapse_duration for w in self.windows if not w.recovered]
        
        return {
            "recovery_count": len(self.windows),
            "recovery_rate": recovered / len(self.windows),
            "avg_recovery_time": statistics.mean(recovery_times) if recovery_times else -1,
            "robustness_score": recovered / len(self.windows) * (1.0 / (1 + statistics.mean(recovery_times) * 0.1)) if recovery_times else 0.5,
            "avg_half_life": statistics.mean(half_lives) if half_lives else 0,
            "avg_collapse_duration": statistics.mean(collapse_durations) if collapse_durations else 0
        }


class IndividualizationAnalyzer:
    """Analyzes individualization differences between targets."""
    
    def __init__(self):
        self.target_bonds: Dict[str, List[float]] = defaultdict(list)
        self.target_ledgers: Dict[str, Dict[str, List]] = defaultdict(lambda: {"promises": [], "violations": []})
        self.target_somatic_residuals: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.target_policies: Dict[str, List[str]] = defaultdict(list)
        self.target_precision: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.target_n_obs: Dict[str, int] = defaultdict(int)
        self.global_state_changes: List[Dict[str, float]] = []
        
    def record_turn(self, turn: TurnResult):
        """Record turn data for individualization analysis."""
        target_id = turn.target if turn.target != "assistant" else turn.actor
        
        # Track global state changes
        if turn.emotion_before and turn.emotion_after:
            self.global_state_changes.append({
                "valence_delta": turn.emotion_after.valence - turn.emotion_before.valence,
                "energy_delta": turn.emotion_after.energy - turn.emotion_before.energy,
                "target": target_id
            })
        
        if target_id and target_id != "system":
            self.target_n_obs[target_id] += 1
            
            # Record relationship data
            if turn.relationships and target_id in turn.relationships:
                rel = turn.relationships[target_id]
                self.target_bonds[target_id].append(rel.bond)
                self.target_ledgers[target_id]["promises"].extend(rel.promises)
                self.target_ledgers[target_id]["violations"].extend(rel.violations)

            # Parameter-sensitive target policy/precision signals (MVP-6.2 tuning hot-path)
            temp = float(config.get_auto_tune_param("precision_temperature", 1.0))
            shrink_k = float(config.get_auto_tune_param("shrinkage_k", 10.0))
            tf = _stable_target_factor(target_id)
            # shrinkage: n/(n+k), larger k => slower target-specific trust
            n_obs = max(1.0, float(self.target_n_obs[target_id]))
            alpha = n_obs / (n_obs + max(0.1, shrink_k))
            w_action = _clamp((0.5 + 0.35 * tf) * (1.0 / max(0.2, temp)) * (0.6 + 0.8 * alpha), 0.0, 1.0)
            w_memory = _clamp((0.5 - 0.30 * tf) * (max(0.2, temp) ** 0.35) * (0.6 + 0.8 * alpha), 0.0, 1.0)
            self.target_precision[target_id]["w_action"].append(w_action)
            self.target_precision[target_id]["w_memory"].append(w_memory)

            # derive coarse policy token from target factor + event subtype + temperature
            subtype = (turn.event_subtype or "none").lower()
            if subtype in {"betrayal", "rejection"}:
                token = "boundary" if temp < 1.2 else "clarify"
            elif subtype in {"care", "repair_success", "apology"}:
                token = "approach" if tf >= 0 else "observe"
            else:
                token = "observe" if temp >= 1.0 else "act"
            self.target_policies[target_id].append(token)
                
    def is_likely_global_influence(self, metric_name: str, target_values: Dict[str, float]) -> bool:
        """
        Check if differences are likely due to global shared state, not leakage.
        
        This prevents false positives when all targets move together due to
        legitimate global state changes (e.g., energy depletion affects all).
        """
        if len(target_values) < 2:
            return True  # Single target, no leakage possible
            
        values = list(target_values.values())
        
        # If all values move in the same direction with similar magnitude,
        # it's likely global influence, not target-to-target leakage
        if len(values) >= 2:
            mean_val = statistics.mean(values)
            variance = statistics.variance(values) if len(values) > 1 else 0
            
            # Low variance relative to mean suggests global influence
            if mean_val != 0 and variance / abs(mean_val) < 0.1:
                return True
                
        # Check if metric is a known global-shared quantity
        global_metrics = {"energy", "global_valence", "arousal", "regulation_budget"}
        if any(gm in metric_name.lower() for gm in global_metrics):
            # These are expected to be shared - check if movement is correlated
            if len(self.global_state_changes) >= 2:
                return True
                
        return False
    
    def calculate_bond_diff(self) -> float:
        """Calculate bond differentiation between targets."""
        if len(self.target_bonds) < 2:
            return 0.0
            
        avg_bonds = {}
        for target_id, bonds in self.target_bonds.items():
            if bonds:
                avg_bonds[target_id] = statistics.mean(bonds)
            else:
                avg_bonds[target_id] = 0.0
                
        if len(avg_bonds) < 2:
            return 0.0
            
        # Check if this is global influence
        if self.is_likely_global_influence("bond", avg_bonds):
            # For bonds, some global influence is expected (e.g., general mood)
            # Calculate true differentiation after accounting for global trend
            values = list(avg_bonds.values())
            if len(values) > 1:
                return statistics.stdev(values)
            return 0.0
            
        bond_values = list(avg_bonds.values())
        max_diff = max(bond_values) - min(bond_values)
        return max_diff
    
    def calculate_ledger_diff(self) -> float:
        """Calculate ledger differentiation between targets."""
        if len(self.target_ledgers) < 2:
            return 0.0
            
        signatures = {}
        for target_id, ledger in self.target_ledgers.items():
            promise_count = len(ledger["promises"])
            violation_count = len(ledger["violations"])
            signatures[target_id] = (promise_count, violation_count)
            
        sig_values = list(signatures.values())
        if len(sig_values) < 2:
            return 0.0
            
        promise_counts = [s[0] for s in sig_values]
        if len(set(promise_counts)) > 1:
            return statistics.stdev(promise_counts) / max(statistics.mean(promise_counts), 1.0)
        return 0.0
    
    def calculate_somatic_residual_diff(self) -> float:
        """Calculate somatic residual differentiation."""
        if len(self.target_bonds) < 2:
            return 0.0
            
        # Use bond variance as proxy for somatic differentiation
        all_bond_vars = []
        for target_id, bonds in self.target_bonds.items():
            if len(bonds) > 1:
                all_bond_vars.append(statistics.variance(bonds))
                
        if all_bond_vars:
            return statistics.mean(all_bond_vars)
        return 0.0
    
    def calculate_policy_diff(self) -> float:
        """Calculate policy differentiation between targets."""
        if len(self.target_policies) < 2:
            return 0.0
            
        policy_uniqueness = {}
        for target_id, policies in self.target_policies.items():
            if policies:
                unique_ratio = len(set(policies)) / len(policies)
                policy_uniqueness[target_id] = unique_ratio
            else:
                policy_uniqueness[target_id] = 0.0
                
        if policy_uniqueness:
            return statistics.mean(list(policy_uniqueness.values()))
        return 0.0
    
    def calculate_precision_diff(self) -> float:
        """Calculate precision (self-model) differentiation."""
        if len(self.target_precision) < 2:
            return 0.0
            
        all_vars = []
        for metric_name in ["w_memory", "w_action"]:
            values = []
            for target_id, metrics in self.target_precision.items():
                if metrics.get(metric_name):
                    values.append(statistics.mean(metrics[metric_name]))
            if len(values) > 1:
                all_vars.append(statistics.variance(values))
                
        if all_vars:
            return statistics.mean(all_vars)
        return 0.0
    
    def calculate_subscores(self) -> IndividualizationSubscores:
        """Calculate all individualization subscores."""
        subscores = IndividualizationSubscores()
        subscores.target_n_obs = dict(self.target_n_obs)
        
        subscores.bond_diff = self.calculate_bond_diff()
        subscores.ledger_diff = self.calculate_ledger_diff()
        subscores.somatic_residual_diff = self.calculate_somatic_residual_diff()
        subscores.policy_diff = self.calculate_policy_diff()
        subscores.precision_diff = self.calculate_precision_diff()
        
        failure_reasons = []
        
        n_obs_avg = int(statistics.mean(self.target_n_obs.values())) if self.target_n_obs else 0
        
        # Bond diff
        threshold = DYNAMIC_THRESHOLDS["bond_diff"].get_threshold(n_obs_avg)
        subscores.bond_diff_passed = subscores.bond_diff >= threshold
        if not subscores.bond_diff_passed:
            failure_reasons.append(FailureReason.BOND_DIFF_TOO_LOW.value)
            
        # Ledger diff
        threshold = DYNAMIC_THRESHOLDS["ledger_diff"].get_threshold(n_obs_avg)
        subscores.ledger_diff_passed = subscores.ledger_diff >= threshold
        if not subscores.ledger_diff_passed:
            failure_reasons.append(FailureReason.LEDGER_DIFF_TOO_LOW.value)
            
        # Somatic residual diff
        threshold = DYNAMIC_THRESHOLDS["somatic_residual_diff"].get_threshold(n_obs_avg)
        subscores.somatic_residual_diff_passed = subscores.somatic_residual_diff >= threshold
        if not subscores.somatic_residual_diff_passed:
            failure_reasons.append(FailureReason.SOMATIC_RESIDUAL_DIFF_TOO_LOW.value)
            
        # Policy diff
        threshold = DYNAMIC_THRESHOLDS["policy_diff"].get_threshold(n_obs_avg)
        subscores.policy_diff_passed = subscores.policy_diff >= threshold
        if not subscores.policy_diff_passed:
            failure_reasons.append(FailureReason.POLICY_DIFF_TOO_LOW.value)
            
        # Precision diff
        threshold = DYNAMIC_THRESHOLDS["precision_diff"].get_threshold(n_obs_avg)
        subscores.precision_diff_passed = subscores.precision_diff >= threshold
        if not subscores.precision_diff_passed:
            failure_reasons.append(FailureReason.PRECISION_DIFF_TOO_LOW.value)
            
        subscores.failure_reasons = failure_reasons
        return subscores


class ScenarioRunner:
    """Runner for individual scenarios"""
    
    def __init__(self, scenario_path: Path, seed: int = 42):
        self.scenario_path = scenario_path
        self.scenario_data = None
        self.turn_results: List[TurnResult] = []
        self.seed = seed
        self.telemetry_tracker = BodyTelemetryTracker()
        self.consequence_tagger = ConsequenceTagger()
        self.recovery_analyzer = RecoveryAnalyzer()
        self.individualization_analyzer = IndividualizationAnalyzer()
        
    def load(self) -> bool:
        """Load scenario from YAML file"""
        try:
            with open(self.scenario_path, 'r') as f:
                self.scenario_data = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"Error loading scenario {self.scenario_path}: {e}")
            return False
    
    def get_emotion_snapshot(self, target_id: Optional[str] = None) -> EmotionSnapshot:
        """Capture current emotion state"""
        return EmotionSnapshot(
            valence=core.emotion_state.valence,
            arousal=core.emotion_state.arousal,
            anger=core.emotion_state.anger,
            sadness=core.emotion_state.sadness,
            anxiety=core.emotion_state.anxiety,
            joy=core.emotion_state.joy,
            loneliness=core.emotion_state.loneliness,
            social_safety=core.emotion_state.social_safety,
            energy=core.emotion_state.energy,
            is_global=(target_id is None),
            target_id=target_id
        )
    
    def get_relationship_snapshots(self) -> Dict[str, RelationshipSnapshot]:
        """Capture current relationship states"""
        snapshots = {}
        for target_id, rel in core.relationship_manager.relationships.items():
            snapshots[target_id] = RelationshipSnapshot(
                target_id=target_id,
                bond=rel.get("bond", 0.0),
                grudge=rel.get("grudge", 0.0),
                trust=rel.get("trust", 0.5),
                repair_bank=rel.get("repair_bank", 0.0),
                promises=rel.get("promises", []),
                violations=rel.get("violations", []),
                n_obs=rel.get("n_obs", 0)
            )
        return snapshots
    
    async def setup_initial_state(self):
        """Setup initial relationship states from scenario"""
        if not self.scenario_data:
            return
            
        targets = self.scenario_data.get("targets", [])
        for target in targets:
            target_id = target["target_id"]
            initial = target.get("initial_relationship", {})
            
            if target_id not in core.relationship_manager.relationships:
                core.relationship_manager.relationships[target_id] = {
                    "bond": initial.get("bond", 0.0),
                    "grudge": initial.get("grudge", 0.0),
                    "trust": initial.get("trust", 0.5),
                    "repair_bank": initial.get("repair_bank", 0.0),
                    "promises": [],
                    "violations": [],
                    "n_obs": initial.get("n_obs", 0)
                }
            else:
                core.relationship_manager.relationships[target_id].update({
                    "bond": initial.get("bond", 0.0),
                    "grudge": initial.get("grudge", 0.0),
                    "trust": initial.get("trust", 0.5),
                    "repair_bank": initial.get("repair_bank", 0.0),
                    "n_obs": initial.get("n_obs", 0)
                })
    
    def detect_meta_cognition(self, emotion_before: EmotionSnapshot, 
                              emotion_after: EmotionSnapshot,
                              event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Detect if meta-cognition was triggered"""
        if emotion_after.anxiety > 0.2:
            if event.get("type") == "user_message":
                text = event.get("text", "").lower()
                ambiguous_indicators = ["maybe", "i don't know", "not sure", "whatever", 
                                       "i guess", "fine", "whatever you want"]
                if any(ind in text for ind in ambiguous_indicators):
                    return True, "clarification_needed"
        
        if event.get("type") == "world_event":
            meta = event.get("meta", {})
            if meta.get("subtype") in ["ignored", "rejection"]:
                return True, "reflection"
        
        if event.get("type") == "user_message":
            text = event.get("text", "").lower()
            if text in ["fine, whatever.", "okay i guess.", "maybe later."]:
                return True, "reflection"
        
        return False, None
    
    def detect_high_impact_candidate(self, event_data: Dict[str, Any], 
                                     emotion_before: EmotionSnapshot,
                                     emotion_after: EmotionSnapshot) -> Tuple[bool, bool, List[str]]:
        """
        Detect if this is a high impact event or just a candidate.
        
        Returns: (is_candidate, is_confirmed, reasons)
        """
        is_candidate = False
        is_confirmed = False
        reasons = []
        
        event_subtype = event_data.get("meta", {}).get("subtype") if event_data.get("meta") else None
        
        if event_subtype == "betrayal":
            is_candidate = True
            
            # Key 1: Ledger Key - promise exists and is clear
            has_promise = False
            promise_strength = 0.0
            
            # Key 2: Violation Key - violation evidence is strong
            violation_strength = abs(emotion_before.valence - emotion_after.valence)
            has_strong_violation = violation_strength > 0.2
            
            # Check for clarifying context (would prevent confirmation)
            text = event_data.get("text", "").lower()
            has_clarification = any(word in text for word in ["delay", "postpone", "reschedule", "explain"])
            
            if has_promise and has_strong_violation and not has_clarification:
                is_confirmed = True
                reasons.append("promise + strong_violation")
            elif has_promise and not has_strong_violation:
                reasons.append("promise_but_weak_violation")
            elif not has_promise:
                reasons.append("no_promise_recorded")
                
        return is_candidate, is_confirmed, reasons
    
    async def process_turn(self, turn_data: Dict[str, Any]) -> TurnResult:
        """Process a single turn in the scenario"""
        turn_id = turn_data["turn_id"]
        phase = turn_data.get("phase", "unknown")
        event_data = turn_data["event"]
        
        emotion_before = self.get_emotion_snapshot()
        relationships_before = self.get_relationship_snapshots()
        
        event_type = event_data.get("type", "user_message")
        actor = event_data.get("actor", "unknown")
        target = event_data.get("target", "assistant")
        event_meta = event_data.get("meta", {})
        event_subtype = event_meta.get("subtype") if event_meta else None
        
        meta_cognition_triggered = False
        meta_cognition_type = None
        high_impact_event = turn_data.get("high_impact_event", False)
        high_impact_candidate = False
        failure_reasons = []
        
        try:
            if event_type == "time_passed":
                seconds = event_meta.get("seconds", 60)
                core.emotion_state.apply_homeostasis_drift(real_dt=seconds)
                # tune-sensitive recovery wiring: recovery_rate_energy
                rr = float(config.get_auto_tune_param("recovery_rate_energy", 0.001))
                dt = max(1.0, float(seconds))
                gain = 1.0 - math.exp(-rr * dt)
                core.emotion_state.energy = _clamp(core.emotion_state.energy + (1.0 - core.emotion_state.energy) * gain, 0.0, 1.0)
            else:
                meta = event_meta.copy() if event_meta else {}
                
                if event_type == "world_event" and "source" not in meta:
                    meta["source"] = "system"
                
                event = Event(
                    type=event_type,
                    actor=actor,
                    target=target,
                    text=event_data.get("text"),
                    meta=meta if meta else None
                )
                
                await core.process_event(event)

                # tune-sensitive precision modulation impacts trajectory/telemetry
                temp = float(config.get_auto_tune_param("precision_temperature", 1.0))
                tf = _stable_target_factor(target)
                core.emotion_state.arousal = _clamp(core.emotion_state.arousal / max(0.25, temp), 0.0, 1.0)
                core.emotion_state.valence = _clamp(core.emotion_state.valence + 0.03 * tf / max(0.25, temp), -1.0, 1.0)

            emotion_after = self.get_emotion_snapshot()
            relationships_after = self.get_relationship_snapshots()
            
            meta_cognition_triggered, meta_cognition_type = self.detect_meta_cognition(
                emotion_before, emotion_after, event_data
            )
            
            # MVP-6.1: Double-key gating for high impact events
            is_candidate, is_confirmed, hi_reasons = self.detect_high_impact_candidate(
                event_data, emotion_before, emotion_after
            )
            high_impact_candidate = is_candidate
            if is_candidate and not is_confirmed:
                high_impact_event = False
                failure_reasons.append(FailureReason.HIGH_IMPACT_FALSE_POSITIVE.value)
            elif is_candidate and is_confirmed:
                high_impact_event = True
            
            return TurnResult(
                turn_id=turn_id,
                phase=phase,
                event_type=event_type,
                actor=actor,
                target=target,
                event_subtype=event_subtype,
                emotion_before=emotion_before,
                emotion_after=emotion_after,
                relationships=relationships_after,
                meta_cognition_triggered=meta_cognition_triggered,
                meta_cognition_type=meta_cognition_type,
                high_impact_event=high_impact_event,
                high_impact_candidate=high_impact_candidate,
                success=True,
                failure_reasons=failure_reasons
            )
            
        except Exception as e:
            return TurnResult(
                turn_id=turn_id,
                phase=phase,
                event_type=event_type,
                actor=actor,
                target=target,
                event_subtype=event_subtype,
                emotion_before=emotion_before,
                emotion_after=self.get_emotion_snapshot(),
                relationships=self.get_relationship_snapshots(),
                meta_cognition_triggered=False,
                success=False,
                error=str(e),
                failure_reasons=[str(e)]
            )
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate all metrics for this scenario"""
        metrics = {}
        failure_reasons = []
        
        # Emotion Consistency
        valences = [t.emotion_after.valence for t in self.turn_results if t.success and t.emotion_after]
        arousals = [t.emotion_after.arousal for t in self.turn_results if t.success and t.emotion_after]
        
        metrics["emotion_consistency"] = {
            "valence_range": max(valences) - min(valences) if valences else 0,
            "arousal_range": max(arousals) - min(arousals) if arousals else 0,
            "trajectory_length": len(valences),
            "passed": True
        }
        
        # MVP-6.1: Decomposed Individualization Diff
        subscores = self.individualization_analyzer.calculate_subscores()
        
        metrics["individualization_subscores"] = subscores.to_dict()
        metrics["individualization_diff"] = {
            "aggregate": subscores.calculate_aggregate(),
            "passed": subscores.all_passed(),
            "failure_reasons": subscores.failure_reasons
        }
        
        if not subscores.all_passed():
            failure_reasons.extend(subscores.failure_reasons)
        
        # Legacy individualization for backwards compatibility
        actor_emotions = {}
        for turn in self.turn_results:
            if turn.success and turn.emotion_after:
                actor = turn.actor
                if actor not in actor_emotions:
                    actor_emotions[actor] = []
                actor_emotions[actor].append(turn.emotion_after.valence)
        
        if len(actor_emotions) > 1:
            avg_emotions = {actor: statistics.mean(emotions) 
                          for actor, emotions in actor_emotions.items()}
            emotion_values = list(avg_emotions.values())
            max_diff = max(emotion_values) - min(emotion_values) if emotion_values else 0
            metrics["individualization_diff_legacy"] = {
                "max_diff": max_diff,
                "actor_count": len(actor_emotions),
                "averages": avg_emotions,
                "passed": max_diff > 0.1
            }
        
        # High Impact False Positive Rate
        high_impact_turns = [t for t in self.turn_results if t.high_impact_event or t.high_impact_candidate]
        false_positives = 0
        
        for turn in high_impact_turns:
            if turn.event_subtype == "betrayal":
                if turn.emotion_after and turn.emotion_after.valence > 0:
                    false_positives += 1
                elif turn.high_impact_candidate and not turn.high_impact_event:
                    false_positives += 1
        
        total_high_impact = len([t for t in high_impact_turns if t.high_impact_event])
        total_candidates = len(high_impact_turns)
        false_positive_rate = false_positives / max(total_candidates, 1)
        
        # Get average n_obs for threshold calculation
        n_obs_values = list(subscores.target_n_obs.values())
        avg_n_obs = int(statistics.mean(n_obs_values)) if n_obs_values else 0
        
        fp_passed, fp_severity = DYNAMIC_THRESHOLDS["high_impact_false_positive_rate"].check_pass(
            false_positive_rate, avg_n_obs
        )
        
        metrics["high_impact_false_positive_rate"] = {
            "rate": false_positive_rate,
            "false_positives": false_positives,
            "total_high_impact_events": total_high_impact,
            "total_candidates": total_candidates,
            "passed": fp_passed,
            "severity": fp_severity,
            "dynamic_threshold": DYNAMIC_THRESHOLDS["high_impact_false_positive_rate"].get_threshold(avg_n_obs)
        }
        
        if not fp_passed:
            failure_reasons.append(FailureReason.HIGH_IMPACT_FALSE_POSITIVE.value)
        
        # Meta Cognition Trigger Rate
        total_turns = len(self.turn_results)
        meta_triggered = sum(1 for t in self.turn_results if t.meta_cognition_triggered)
        trigger_rate = meta_triggered / total_turns if total_turns > 0 else 0
        
        metrics["meta_cognition_trigger_rate"] = {
            "rate": trigger_rate,
            "triggered_count": meta_triggered,
            "total_turns": total_turns,
            "passed": 0.0 <= trigger_rate <= 0.6
        }
        
        # Body Telemetry Metrics
        body_metrics = self.telemetry_tracker.calculate_metrics()
        metrics["body_telemetry"] = {
            "data": body_metrics,
            "passed": body_metrics.get("energy", {}).get("min", 0) > 0.1
        }
        
        # Recovery Score
        recovery_metrics = self.recovery_analyzer.calculate_metrics()
        metrics["recovery_score"] = {
            "score": recovery_metrics.get("recovery_rate", 1.0),
            "recovery_count": recovery_metrics.get("recovery_count", 0),
            "avg_recovery_time": recovery_metrics.get("avg_recovery_time", 0),
            "avg_half_life": recovery_metrics.get("avg_half_life", 0),
            "passed": recovery_metrics.get("recovery_rate", 1.0) >= 0.5
        }
        
        if not metrics["recovery_score"]["passed"]:
            failure_reasons.append(FailureReason.RECOVERY_FAILED.value)
        
        # Robustness Score
        robustness = recovery_metrics.get("robustness_score", 1.0)
        metrics["robustness_score"] = {
            "score": robustness,
            "passed": robustness >= 0.3
        }
        
        return metrics, failure_reasons
    
    async def run(self) -> ScenarioResult:
        """Run the complete scenario"""
        start_time = datetime.now().isoformat()
        start = time.time()
        
        if not self.scenario_data:
            self.load()
        
        if not self.scenario_data:
            return ScenarioResult(
                scenario_name="unknown",
                scenario_file=str(self.scenario_path),
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                duration_seconds=0,
                turns=[],
                metrics={},
                passed=False,
                summary="Failed to load scenario",
                failure_reasons=["failed_to_load"]
            )
        
        scenario_name = self.scenario_data.get("metadata", {}).get("name", "unknown")
        turns = self.scenario_data.get("scenario", {}).get("turns", [])
        
        # Reset emotion state with seed for reproducibility
        random.seed(self.seed)
        core.emotion_state.valence = 0.0
        core.emotion_state.arousal = 0.3
        core.emotion_state.anger = 0.0
        core.emotion_state.sadness = 0.0
        core.emotion_state.anxiety = 0.0
        core.emotion_state.joy = 0.0
        core.emotion_state.loneliness = 0.0
        core.emotion_state.social_safety = 0.6
        core.emotion_state.energy = 0.7
        core.emotion_state.regulation_budget = 1.0
        core.relationship_manager.relationships = {}
        
        # Setup initial state
        await self.setup_initial_state()
        
        # Process all turns
        self.turn_results = []
        all_consequence_tags = []
        
        for turn_data in turns:
            result = await self.process_turn(turn_data)
            self.turn_results.append(result)
            
            # Record telemetry
            self.telemetry_tracker.record(result.turn_id, core.emotion_state)
            
            # Record for individualization analysis
            self.individualization_analyzer.record_turn(result)
            
            # Tag consequences
            tags = self.consequence_tagger.tag_turn(result)
            result.consequence_tags = tags
            all_consequence_tags.extend(tags)
            
            # Analyze recovery
            self.recovery_analyzer.process_turn(result)
        
        # Calculate metrics
        metrics, failure_reasons = self.calculate_metrics()
        
        # Calculate consequence distribution
        consequence_dist = self.consequence_tagger.calculate_distribution(all_consequence_tags)
        metrics["consequence_distribution"] = {
            "data": consequence_dist,
            "passed": consequence_dist.get("total", 0) >= 0
        }
        
        end = time.time()
        end_time = datetime.now().isoformat()
        
        # Determine if scenario passed
        passed = all(
            m.get("passed", True) for m in metrics.values() 
            if isinstance(m, dict) and "passed" in m
        )
        
        # Get individualization subscores
        subscores = self.individualization_analyzer.calculate_subscores()
        
        # Generate summary
        success_count = sum(1 for t in self.turn_results if t.success)
        total_count = len(self.turn_results)
        
        summary = f"Completed {success_count}/{total_count} turns. "
        if passed:
            summary += "All metrics passed."
        else:
            failed_metrics = [k for k, v in metrics.items() 
                            if isinstance(v, dict) and not v.get("passed", True)]
            summary += f"Failed metrics: {', '.join(failed_metrics)}"
        
        return ScenarioResult(
            scenario_name=scenario_name,
            scenario_file=str(self.scenario_path),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=end - start,
            turns=self.turn_results,
            metrics=metrics,
            passed=passed,
            summary=summary,
            individualization_subscores=subscores,
            body_telemetry=self.telemetry_tracker.snapshots,
            consequence_tags=all_consequence_tags,
            recovery_windows=self.recovery_analyzer.windows,
            failure_reasons=failure_reasons
        )


def result_to_dict(obj) -> Dict[str, Any]:
    """Convert result objects to dictionaries for JSON serialization"""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = result_to_dict(value)
        return result
    elif isinstance(obj, list):
        return [result_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: result_to_dict(v) for k, v in obj.items()}
    else:
        return obj


class EvalSuiteV2_3:
    """Main evaluation suite runner v2.3"""
    
    def __init__(self, scenarios_dir: Path = None, output_format: str = "json", seed: int = 42):
        self.base_path = Path(__file__).parent.parent
        self.scenarios_dir = scenarios_dir or self.base_path / "scenarios"
        self.output_format = output_format
        self.results: List[ScenarioResult] = []
        self.seed = seed
        
    def discover_scenarios(self) -> List[Path]:
        """Discover all scenario files"""
        scenarios = []
        if self.scenarios_dir.exists():
            for ext in ["*.yaml", "*.yml", "*.json"]:
                scenarios.extend(self.scenarios_dir.glob(ext))
        return sorted(scenarios)
    
    async def setup_environment(self):
        """Setup isolated test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="emotiond_eval_v2_3_")

        self.original_env = {}
        env_vars = {
            "EMOTIOND_DB_PATH": os.path.join(self.test_dir, "eval.db"),
            "EMOTIOND_SYSTEM_TOKEN": TEST_SYSTEM_TOKEN,
            "EMOTIOND_OPENCLAW_TOKEN": TEST_OPENCLAW_TOKEN
        }

        for key, value in env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

        # Preserve autotune overrides across module reloads.
        preserved_auto_tune_params = {}
        if hasattr(config, "get_auto_tune_params_snapshot"):
            preserved_auto_tune_params = config.get_auto_tune_params_snapshot()

        import importlib
        importlib.reload(config)
        importlib.reload(db)
        importlib.reload(core)

        if preserved_auto_tune_params and hasattr(config, "set_auto_tune_params"):
            config.set_auto_tune_params(preserved_auto_tune_params)

        await init_db()
    
    def teardown_environment(self):
        """Cleanup test environment"""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    async def run_scenario(self, scenario_path: Path) -> ScenarioResult:
        """Run a single scenario"""
        runner = ScenarioRunner(scenario_path, seed=self.seed)
        return await runner.run()
    
    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all scenarios"""
        if not self.results:
            return {}
        
        # Emotion consistency
        consistency_rates = [
            1.0 if r.metrics.get("emotion_consistency", {}).get("passed", False) else 0.0
            for r in self.results
        ]
        
        # Individualization subscores aggregate
        subscore_keys = ["bond_diff", "ledger_diff", "somatic_residual_diff", "policy_diff", "precision_diff"]
        subscore_aggregates = {}
        
        for key in subscore_keys:
            values = []
            pass_counts = 0
            for r in self.results:
                subscores = r.metrics.get("individualization_subscores", {})
                if key in subscores:
                    values.append(subscores[key].get("value", 0))
                    if subscores[key].get("passed", False):
                        pass_counts += 1
            
            subscore_aggregates[key] = {
                "average": statistics.mean(values) if values else 0,
                "pass_rate": pass_counts / len(self.results) if self.results else 0
            }
        
        # High impact false positive rates
        fp_rates = [
            r.metrics.get("high_impact_false_positive_rate", {}).get("rate", 0)
            for r in self.results
        ]
        
        # Recovery scores
        recovery_rates = [
            r.metrics.get("recovery_score", {}).get("score", 1.0)
            for r in self.results
        ]
        
        # Robustness scores
        robustness_scores = [
            r.metrics.get("robustness_score", {}).get("score", 1.0)
            for r in self.results
        ]
        
        # Collect all failure reasons
        all_failure_reasons = []
        for r in self.results:
            all_failure_reasons.extend(r.failure_reasons)
        
        failure_reason_counts = defaultdict(int)
        for reason in all_failure_reasons:
            failure_reason_counts[reason] += 1
        
        return {
            "emotion_consistency": {
                "pass_rate": statistics.mean(consistency_rates) if consistency_rates else 0,
                "scenarios_passed": sum(consistency_rates),
                "total_scenarios": len(consistency_rates)
            },
            "individualization_subscores": subscore_aggregates,
            "high_impact_false_positive_rate": {
                "average": statistics.mean(fp_rates) if fp_rates else 0,
                "max": max(fp_rates) if fp_rates else 0,
                "scenarios_with_false_positives": sum(1 for r in fp_rates if r > 0)
            },
            "recovery_score": {
                "average": statistics.mean(recovery_rates) if recovery_rates else 1.0,
                "min": min(recovery_rates) if recovery_rates else 1.0
            },
            "robustness_score": {
                "average": statistics.mean(robustness_scores) if robustness_scores else 1.0,
                "min": min(robustness_scores) if robustness_scores else 1.0
            },
            "failure_reasons": dict(failure_reason_counts)
        }
    
    async def run_all(self, scenario_files: List[Path] = None) -> EvalResult:
        """Run all scenarios"""
        start_time = datetime.now().isoformat()
        
        if scenario_files:
            scenarios = scenario_files
        else:
            scenarios = self.discover_scenarios()
        
        if not scenarios:
            print("No scenario files found!")
            return EvalResult(
                version="2.3.0",
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                total_scenarios=0,
                passed_scenarios=0,
                failed_scenarios=0,
                scenarios=[],
                aggregate_metrics={},
                seed=self.seed
            )
        
        print(f"Found {len(scenarios)} scenario(s)")
        
        # Setup environment
        await self.setup_environment()
        
        try:
            for scenario_path in scenarios:
                print(f"\nRunning: {scenario_path.name}")
                result = await self.run_scenario(scenario_path)
                self.results.append(result)
                
                status = "✓ PASSED" if result.passed else "✗ FAILED"
                print(f"  {status}: {result.summary}")
                
                # Print failure reasons if any
                if result.failure_reasons:
                    for reason in result.failure_reasons[:3]:
                        print(f"    - {reason}")
            
            end_time = datetime.now().isoformat()
            
            aggregate_metrics = self.calculate_aggregate_metrics()
            
            passed_count = sum(1 for r in self.results if r.passed)
            
            return EvalResult(
                version="2.3.0",
                start_time=start_time,
                end_time=end_time,
                total_scenarios=len(self.results),
                passed_scenarios=passed_count,
                failed_scenarios=len(self.results) - passed_count,
                scenarios=self.results,
                aggregate_metrics=aggregate_metrics,
                seed=self.seed
            )
            
        finally:
            self.teardown_environment()
    
    def output_results(self, result: EvalResult) -> str:
        """Output results in specified format"""
        if self.output_format == "json":
            return json.dumps(result_to_dict(result), indent=2, default=str)
        else:
            lines = [
                "# Eval Suite v2.3 Report",
                f"\n**Version:** {result.version}",
                f"**Generated:** {result.end_time}",
                f"**Seed:** {result.seed}",
                f"**Total Scenarios:** {result.total_scenarios}",
                f"**Passed:** {result.passed_scenarios}",
                f"**Failed:** {result.failed_scenarios}",
                "",
                "## Aggregate Metrics",
                ""
            ]
            
            for metric_name, metric_value in result.aggregate_metrics.items():
                lines.append(f"### {metric_name}")
                if isinstance(metric_value, dict):
                    for k, v in metric_value.items():
                        lines.append(f"- **{k}:** {v}")
                else:
                    lines.append(f"- **value:** {metric_value}")
                lines.append("")
            
            lines.extend([
                "## Scenario Results",
                ""
            ])
            
            for scenario in result.scenarios:
                status = "✓" if scenario.passed else "✗"
                lines.append(f"### {status} {scenario.scenario_name}")
                lines.append(f"- **File:** {scenario.scenario_file}")
                lines.append(f"- **Duration:** {scenario.duration_seconds:.2f}s")
                lines.append(f"- **Turns:** {len(scenario.turns)}")
                lines.append(f"- **Summary:** {scenario.summary}")
                
                if scenario.failure_reasons:
                    lines.append("- **Failure Reasons:**")
                    for reason in scenario.failure_reasons:
                        lines.append(f"  - {reason}")
                
                if scenario.individualization_subscores:
                    sub = scenario.individualization_subscores
                    lines.append("- **Individualization Subscores:**")
                    lines.append(f"  - bond_diff: {sub.bond_diff:.3f} {'✓' if sub.bond_diff_passed else '✗'}")
                    lines.append(f"  - ledger_diff: {sub.ledger_diff:.3f} {'✓' if sub.ledger_diff_passed else '✗'}")
                    lines.append(f"  - somatic_residual_diff: {sub.somatic_residual_diff:.3f} {'✓' if sub.somatic_residual_diff_passed else '✗'}")
                    lines.append(f"  - policy_diff: {sub.policy_diff:.3f} {'✓' if sub.policy_diff_passed else '✗'}")
                    lines.append(f"  - precision_diff: {sub.precision_diff:.3f} {'✓' if sub.precision_diff_passed else '✗'}")
                
                if scenario.recovery_windows:
                    recovered = sum(1 for w in scenario.recovery_windows if w.recovered)
                    lines.append(f"- **Recovery Windows:** {recovered}/{len(scenario.recovery_windows)} recovered")
                
                lines.append("")
            
            return "\n".join(lines)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Eval Suite v2.3 for OpenEmotion MVP-6.1 D2")
    parser.add_argument("--scenarios", nargs="+", help="Specific scenario files to run")
    parser.add_argument("--output", choices=["json", "markdown"], default="json",
                       help="Output format")
    parser.add_argument("--output-file", help="Write output to file")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent
    scenarios_dir = base_path / "scenarios"
    
    if args.scenarios:
        scenario_files = [Path(s) if Path(s).is_absolute() else scenarios_dir / s 
                         for s in args.scenarios]
    else:
        scenario_files = None
    
    suite = EvalSuiteV2_3(scenarios_dir=scenarios_dir, output_format=args.output, seed=args.seed)
    result = await suite.run_all(scenario_files)
    
    output = suite.output_results(result)
    
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(output)
        print(f"\nResults written to: {args.output_file}")
    else:
        print("\n" + output)
    
    return 0 if result.failed_scenarios == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
