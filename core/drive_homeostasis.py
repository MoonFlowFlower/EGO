"""
Homeostasis Drive v0 (US-651)

Implements drive_error for homeostatic regulation and its influence
on emotion generation and behavioral modulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DriveType(str, Enum):
    """Types of homeostatic drives"""
    ENERGY = "energy"
    UNCERTAINTY = "uncertainty"
    SOCIAL = "social"
    SAFETY = "safety"
    FATIGUE = "fatigue"


@dataclass
class DriveRange:
    """Acceptable range for a drive value"""
    low: float
    high: float
    
    def contains(self, value: float) -> bool:
        return self.low <= value <= self.high
    
    def clamp(self, value: float) -> float:
        return max(self.low, min(self.high, value))
    
    def distance_from_optimal(self, value: float) -> float:
        """Distance from center of range (normalized)"""
        center = (self.low + self.high) / 2
        half_width = (self.high - self.low) / 2
        if half_width == 0:
            return 0.0
        return abs(value - center) / half_width


# Default setpoints for each drive
DEFAULT_DRIVE_SETPOINTS: Dict[DriveType, DriveRange] = {
    DriveType.ENERGY: DriveRange(0.4, 0.8),      # Moderate energy
    DriveType.UNCERTAINTY: DriveRange(0.0, 0.3), # Low uncertainty preferred
    DriveType.SOCIAL: DriveRange(0.3, 0.7),      # Balanced social engagement
    DriveType.SAFETY: DriveRange(0.5, 1.0),      # High safety needed
    DriveType.FATIGUE: DriveRange(0.0, 0.4),     # Low fatigue preferred
}


@dataclass
class DriveState:
    """
    Current state of all homeostatic drives.
    
    Attributes:
        energy: Energy level (0-1)
        uncertainty: Uncertainty level (0-1)
        social: Social engagement level (0-1)
        safety: Safety perception (0-1)
        fatigue: Fatigue level (0-1)
        setpoints: Custom setpoints (defaults used if not provided)
        timestamp: When this state was recorded
    """
    energy: float = 0.6
    uncertainty: float = 0.2
    social: float = 0.5
    safety: float = 0.8
    fatigue: float = 0.2
    setpoints: Dict[DriveType, DriveRange] = field(default_factory=lambda: DEFAULT_DRIVE_SETPOINTS.copy())
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "energy": self.energy,
            "uncertainty": self.uncertainty,
            "social": self.social,
            "safety": self.safety,
            "fatigue": self.fatigue,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DriveState":
        return cls(
            energy=data.get("energy", 0.6),
            uncertainty=data.get("uncertainty", 0.2),
            social=data.get("social", 0.5),
            safety=data.get("safety", 0.8),
            fatigue=data.get("fatigue", 0.2),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
    
    def get_drive(self, drive_type: DriveType) -> float:
        """Get the current value of a specific drive"""
        return getattr(self, drive_type.value, 0.5)
    
    def set_drive(self, drive_type: DriveType, value: float) -> None:
        """Set a drive value (clamped to 0-1)"""
        clamped = max(0.0, min(1.0, value))
        setattr(self, drive_type.value, clamped)


def huber_loss(x: float, delta: float = 1.0) -> float:
    """
    Huber loss function - less sensitive to outliers than squared loss.
    
    For |x| <= delta: 0.5 * x^2
    For |x| > delta: delta * (|x| - 0.5 * delta)
    """
    abs_x = abs(x)
    if abs_x <= delta:
        return 0.5 * x * x
    return delta * (abs_x - 0.5 * delta)


def drive_error(state: DriveState, weights: Optional[Dict[DriveType, float]] = None) -> float:
    """
    Compute the total homeostatic drive error.
    
    Lower values = closer to homeostasis (better).
    Higher values = more deviation from setpoints (worse).
    
    Args:
        state: Current drive state
        weights: Optional weights for each drive (defaults to equal weight)
    
    Returns:
        Total drive error (sum of weighted deviations)
    """
    if weights is None:
        weights = {dt: 1.0 for dt in DriveType}
    
    total_error = 0.0
    for drive_type in DriveType:
        current_value = state.get_drive(drive_type)
        setpoint = state.setpoints.get(drive_type, DriveRange(0.3, 0.7))
        
        # Compute deviation from acceptable range
        if setpoint.contains(current_value):
            # Within range: small penalty based on distance from center
            deviation = setpoint.distance_from_optimal(current_value) * 0.1
        else:
            # Outside range: larger penalty
            if current_value < setpoint.low:
                deviation = setpoint.low - current_value
            else:
                deviation = current_value - setpoint.high
        
        # Apply Huber loss to reduce sensitivity to extreme values
        loss = huber_loss(deviation, delta=0.3)
        total_error += weights.get(drive_type, 1.0) * loss
    
    return total_error


def emotion_from_drive(state: DriveState) -> Dict[str, float]:
    """
    Derive emotional tendencies from drive state.
    
    This provides an interpretable layer between homeostatic drives
    and emotional responses.
    
    Args:
        state: Current drive state
    
    Returns:
        Dictionary of emotion dimensions (0-1 scale)
    """
    # Base emotions derived from drive configurations
    emotions = {
        "joy": 0.5,
        "sadness": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "disgust": 0.0,
        "surprise": 0.0,
        "anxiety": 0.0,
        "loneliness": 0.0,
        "contentment": 0.5,
    }
    
    # Energy influences joy and contentment
    if state.energy < 0.3:
        emotions["sadness"] += 0.3
        emotions["contentment"] -= 0.2
    elif state.energy > 0.7:
        emotions["joy"] += 0.2
    
    # Uncertainty drives anxiety and fear
    if state.uncertainty > 0.5:
        emotions["anxiety"] += state.uncertainty * 0.5
        emotions["fear"] += state.uncertainty * 0.3
    
    # Low social contact drives loneliness
    if state.social < 0.2:
        emotions["loneliness"] += 0.4
        emotions["sadness"] += 0.2
    elif state.social > 0.7:
        emotions["joy"] += 0.1
    
    # Safety affects fear and anxiety
    if state.safety < 0.3:
        emotions["fear"] += 0.4
        emotions["anxiety"] += 0.3
    elif state.safety > 0.8:
        emotions["contentment"] += 0.2
    
    # Fatigue reduces positive emotions
    if state.fatigue > 0.6:
        emotions["joy"] -= 0.2
        emotions["contentment"] -= 0.3
        emotions["sadness"] += 0.2
    
    # Clamp all values to [0, 1]
    for key in emotions:
        emotions[key] = max(0.0, min(1.0, emotions[key]))
    
    return emotions


def modulate_strategy(
    state: DriveState,
    base_strategy: str,
    available_strategies: List[str],
) -> Tuple[str, Dict[str, Any]]:
    """
    Modulate strategy selection based on drive state.
    
    Args:
        state: Current drive state
        base_strategy: Default strategy to use
        available_strategies: List of available strategy names
    
    Returns:
        (selected_strategy, modulation_info) tuple
    """
    modulation_info = {
        "base_strategy": base_strategy,
        "drive_error": drive_error(state),
        "modulations": [],
    }
    
    selected = base_strategy
    
    # High uncertainty -> prefer clarification
    if state.uncertainty > 0.5 and "clarify" in available_strategies:
        selected = "clarify"
        modulation_info["modulations"].append({
            "reason": "high_uncertainty",
            "from": base_strategy,
            "to": "clarify",
            "drive_value": state.uncertainty,
        })
    
    # High fatigue -> prefer conservative/short responses
    if state.fatigue > 0.6 and "conservative" in available_strategies:
        selected = "conservative"
        modulation_info["modulations"].append({
            "reason": "high_fatigue",
            "from": selected,
            "to": "conservative",
            "drive_value": state.fatigue,
        })
    
    # Low safety -> prefer cautious strategies
    if state.safety < 0.3 and "cautious" in available_strategies:
        selected = "cautious"
        modulation_info["modulations"].append({
            "reason": "low_safety",
            "from": selected,
            "to": "cautious",
            "drive_value": state.safety,
        })
    
    modulation_info["selected_strategy"] = selected
    return selected, modulation_info


def score_rollout_candidate(
    state: DriveState,
    candidate: Dict[str, Any],
    base_score: float,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score a rollout candidate considering drive state.
    
    Candidates that reduce drive_error are preferred.
    
    Args:
        state: Current drive state
        candidate: Rollout candidate dictionary
        base_score: Base score from other factors
    
    Returns:
        (final_score, scoring_info) tuple
    """
    current_error = drive_error(state)
    
    # Predict drive change from candidate (simplified model)
    predicted_state = DriveState.from_dict(state.to_dict())
    
    # Assume certain actions affect drives
    action = candidate.get("action", "")
    if "rest" in action.lower():
        predicted_state.fatigue = max(0, predicted_state.fatigue - 0.2)
        predicted_state.energy = min(1, predicted_state.energy + 0.1)
    elif "clarify" in action.lower():
        predicted_state.uncertainty = max(0, predicted_state.uncertainty - 0.3)
    elif "escalate" in action.lower():
        predicted_state.uncertainty = max(0, predicted_state.uncertainty - 0.1)
        predicted_state.safety = min(1, predicted_state.safety + 0.1)
    
    predicted_error = drive_error(predicted_state)
    error_reduction = current_error - predicted_error
    
    # Adjust score based on error reduction
    drive_bonus = error_reduction * 0.5  # Weight for drive influence
    final_score = base_score + drive_bonus
    
    scoring_info = {
        "base_score": base_score,
        "drive_error_current": current_error,
        "drive_error_predicted": predicted_error,
        "error_reduction": error_reduction,
        "drive_bonus": drive_bonus,
        "final_score": final_score,
    }
    
    return final_score, scoring_info
