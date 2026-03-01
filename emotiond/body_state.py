"""
MVP-6 D1: Virtual Body State Vector

Five-dimensional body state representation with uncertainty tracking
time-based dynamics, and configurable recovery constants.

Dimensions:
- energy: Physical/mental energy level [0, 1]
- safety_stress: Perceived safety vs stress [0, 1] (0=stress, 1=safety)
- social_need: Need for social interaction [0, 1]
- novelty_need: Need for novelty/exploration [0, 1]
- focus_fatigue: Mental focus fatigue [0, 1] (0=focused, 1=fatigued)

Each dimension has:
- value: Current value [0, 1]
- uncertainty: Uncertainty of the value [0, 1]
- last_updated: Timestamp of last update

Compatibility with existing energy_budget:
- Body state energy is the SOURCE OF TRUTH for physical energy
- energy_budget in EmotionState is DEPRECATED but maintained for backward compatibility
- energy_budget is now derived from body_state.energy with a multiplier
"""
import time
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class BodyStateDimension:
    """
    A single dimension of the body state vector.
    
    Attributes:
        value: Current value [0, 1]
        uncertainty: Uncertainty of the value [0, 1]
        last_updated: Timestamp of last update
    """
    value: float = 0.5
    uncertainty: float = 0.5
    last_updated: float = field(default_factory=time.time)
    
    # Class defaults for recovery/regression (can be overridden per instance)
    recovery_rate: float = 0.001  # Per second recovery toward baseline
    regression_rate: float = 0.0005  # Per second regression away from baseline
    baseline: float = 0.5  # Homeostatic baseline
    
    def __post_init__(self):
        """Clamp values to valid ranges after initialization."""
        self._clamp()
    
    def _clamp(self):
        """Clamp value and uncertainty to valid ranges [0, 1]."""
        self.value = max(0.0, min(1.0, self.value))
        self.uncertainty = max(0.0, min(1.0, self.uncertainty))
    
    def update(self, delta: float, observation_uncertainty: float = 0.1) -> "BodyStateDimension":
        """
        Update dimension value with a delta, reducing uncertainty.
        
        Args:
            delta: Change in value (can be positive or negative)
            observation_uncertainty: Uncertainty of this observation [0, 1]
        
        Returns:
            Self for chaining
        """
        self.value += delta
        self._clamp()
        # Observation reduces uncertainty
        self.uncertainty = max(0.0, self.uncertainty - 0.05)
        self.uncertainty = max(self.uncertainty, observation_uncertainty)
        self.last_updated = time.time()
        return self
    
    def set_value(self, value: float, uncertainty: Optional[float] = None) -> "BodyStateDimension":
        """
        Set dimension value directly.
        
        Args:
            value: New value [0, 1]
            uncertainty: Optional new uncertainty [0, 1]
        
        Returns:
            Self for chaining
        """
        self.value = value
        if uncertainty is not None:
            self.uncertainty = uncertainty
        self._clamp()
        self.last_updated = time.time()
        return self
    
    def apply_time_passed(self, seconds: float) -> "BodyStateDimension":
        """
        Apply time-based dynamics: recovery toward baseline or regression.
        
        If value is below baseline, it recovers (increases).
        If value is above baseline, it regresses (decreases).
        Uncertainty grows over time.
        
        Args:
            seconds: Time passed in seconds
        
        Returns:
            Self for chaining
        """
        if self.value < self.baseline:
            # Recovery toward baseline
            recovery = self.recovery_rate * seconds
            self.value = min(self.baseline, self.value + recovery)
        elif self.value > self.baseline:
            # Regression toward baseline
            regression = self.regression_rate * seconds
            self.value = max(self.baseline, self.value - regression)
        
        # Uncertainty grows over time (we become less certain)
        uncertainty_growth = 0.0001 * seconds
        self.uncertainty = min(1.0, self.uncertainty + uncertainty_growth)
        
        self._clamp()
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "value": self.value,
            "uncertainty": self.uncertainty,
            "last_updated": self.last_updated,
            "recovery_rate": self.recovery_rate,
            "regression_rate": self.regression_rate,
            "baseline": self.baseline,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BodyStateDimension":
        """Deserialize from dictionary."""
        dim = cls(
            value=data.get("value", 0.5),
            uncertainty=data.get("uncertainty", 0.5),
            last_updated=data.get("last_updated", time.time()),
        )
        dim.recovery_rate = data.get("recovery_rate", 0.001)
        dim.regression_rate = data.get("regression_rate", 0.0005)
        dim.baseline = data.get("baseline", 0.5)
        return dim


@dataclass
class BodyStateVector:
    """
    Five-dimensional virtual body state vector.
    
    Dimensions:
    - energy: Physical/mental energy [0, 1] (baseline 0.7)
    - safety_stress: Safety vs stress [0, 1] (baseline 0.6, 1=safety)
    - social_need: Need for social interaction [0, 1] (baseline 0.5)
    - novelty_need: Need for novelty [0, 1] (baseline 0.5)
    - focus_fatigue: Focus fatigue [0, 1] (baseline 0.3, higher=more fatigued)
    """
    
    # Each dimension with specific defaults
    energy: BodyStateDimension = field(default_factory=lambda: BodyStateDimension(
        value=0.7, uncertainty=0.3, baseline=0.7, recovery_rate=0.001, regression_rate=0.0003
    ))
    safety_stress: BodyStateDimension = field(default_factory=lambda: BodyStateDimension(
        value=0.6, uncertainty=0.4, baseline=0.6, recovery_rate=0.0008, regression_rate=0.0005
    ))
    social_need: BodyStateDimension = field(default_factory=lambda: BodyStateDimension(
        value=0.5, uncertainty=0.5, baseline=0.5, recovery_rate=0.0005, regression_rate=0.0005
    ))
    novelty_need: BodyStateDimension = field(default_factory=lambda: BodyStateDimension(
        value=0.5, uncertainty=0.5, baseline=0.5, recovery_rate=0.0003, regression_rate=0.0003
    ))
    focus_fatigue: BodyStateDimension = field(default_factory=lambda: BodyStateDimension(
        value=0.3, uncertainty=0.4, baseline=0.3, recovery_rate=0.002, regression_rate=0.001
    ))
    
    def __post_init__(self):
        """Ensure all dimensions are properly initialized."""
        # Ensure each dimension is a BodyStateDimension instance
        if isinstance(self.energy, dict):
            self.energy = BodyStateDimension.from_dict(self.energy)
        if isinstance(self.safety_stress, dict):
            self.safety_stress = BodyStateDimension.from_dict(self.safety_stress)
        if isinstance(self.social_need, dict):
            self.social_need = BodyStateDimension.from_dict(self.social_need)
        if isinstance(self.novelty_need, dict):
            self.novelty_need = BodyStateDimension.from_dict(self.novelty_need)
        if isinstance(self.focus_fatigue, dict):
            self.focus_fatigue = BodyStateDimension.from_dict(self.focus_fatigue)
    
    def apply_time_passed(self, seconds: float) -> "BodyStateVector":
        """
        Apply time-based dynamics to all dimensions.
        
        Args:
            seconds: Time passed in seconds
        
        Returns:
            Self for chaining
        """
        self.energy.apply_time_passed(seconds)
        self.safety_stress.apply_time_passed(seconds)
        self.social_need.apply_time_passed(seconds)
        self.novelty_need.apply_time_passed(seconds)
        self.focus_fatigue.apply_time_passed(seconds)
        return self
    
    def update_from_event(self, event_type: str, event_subtype: Optional[str] = None,
                          meta: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Update body state based on event type and subtype.
        
        Args:
            event_type: Type of event (user_message, assistant_reply, world_event)
            event_subtype: Subtype for world_events
            meta: Additional metadata
        
        Returns:
            Dictionary of applied deltas per dimension
        """
        deltas = {
            "energy": 0.0,
            "safety_stress": 0.0,
            "social_need": 0.0,
            "novelty_need": 0.0,
            "focus_fatigue": 0.0,
        }
        
        if event_type == "user_message":
            # User interaction affects energy and focus
            deltas["energy"] = -0.02  # Small energy cost
            deltas["focus_fatigue"] = 0.01  # Slight fatigue
            deltas["social_need"] = -0.03  # Social need partially satisfied
            self.energy.update(deltas["energy"])
            self.focus_fatigue.update(deltas["focus_fatigue"])
            self.social_need.update(deltas["social_need"])
            
        elif event_type == "assistant_reply":
            # Responding costs energy and increases fatigue
            deltas["energy"] = -0.03
            deltas["focus_fatigue"] = 0.02
            self.energy.update(deltas["energy"])
            self.focus_fatigue.update(deltas["focus_fatigue"])
            
        elif event_type == "world_event" and event_subtype:
            subtype_deltas = self._get_subtype_deltas(event_subtype, meta)
            deltas.update(subtype_deltas)
            
            # Apply all deltas
            if deltas["energy"]:
                self.energy.update(deltas["energy"])
            if deltas["safety_stress"]:
                self.safety_stress.update(deltas["safety_stress"])
            if deltas["social_need"]:
                self.social_need.update(deltas["social_need"])
            if deltas["novelty_need"]:
                self.novelty_need.update(deltas["novelty_need"])
            if deltas["focus_fatigue"]:
                self.focus_fatigue.update(deltas["focus_fatigue"])
        
        return deltas
    
    def _get_subtype_deltas(self, subtype: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Get deltas for world event subtypes."""
        deltas = {
            "energy": 0.0,
            "safety_stress": 0.0,
            "social_need": 0.0,
            "novelty_need": 0.0,
            "focus_fatigue": 0.0,
        }
        
        if subtype == "care":
            deltas["energy"] = 0.05
            deltas["safety_stress"] = 0.10
            deltas["social_need"] = -0.05
        elif subtype == "rejection":
            deltas["energy"] = -0.08
            deltas["safety_stress"] = -0.15
            deltas["social_need"] = 0.10
        elif subtype == "betrayal":
            deltas["energy"] = -0.15
            deltas["safety_stress"] = -0.25
            deltas["social_need"] = 0.05
            deltas["focus_fatigue"] = 0.05
        elif subtype == "apology":
            deltas["safety_stress"] = 0.08
            deltas["energy"] = 0.02
        elif subtype == "repair_success":
            deltas["energy"] = 0.05
            deltas["safety_stress"] = 0.12
            deltas["social_need"] = -0.03
        elif subtype == "ignored":
            deltas["social_need"] = 0.08
            deltas["safety_stress"] = -0.05
            deltas["energy"] = -0.03
        elif subtype == "time_passed":
            # Time passage has its own dynamics handled by apply_time_passed
            seconds = meta.get("seconds", 60) if meta else 60
            # Apply time-based dynamics
            self.apply_time_passed(seconds)
        elif subtype == "novelty":
            deltas["novelty_need"] = -0.10  # Novelty satisfied
            deltas["energy"] = 0.03
        elif subtype == "routine":
            deltas["novelty_need"] = 0.05  # Novelty increases with routine
            deltas["focus_fatigue"] = -0.02  # Routine reduces fatigue
        
        return deltas
    
    def get_energy_budget_factor(self) -> float:
        """
        Calculate energy budget factor from body state energy.
        
        This provides compatibility with the existing energy_budget system.
        energy_budget in EmotionState is derived from body_state.energy.
        
        Returns:
            Energy budget factor [0, 1] suitable for regulation_budget
        """
        # Map energy [0, 1] to budget factor with a slight curve
        # Higher energy = higher budget
        energy = self.energy.value
        # Apply a gentle curve: budget = energy^0.5 (square root)
        # This means low energy has disproportionate impact on budget
        return math.sqrt(energy)
    
    def get_summary(self) -> Dict[str, float]:
        """Get a summary of all dimension values."""
        return {
            "energy": self.energy.value,
            "safety_stress": self.safety_stress.value,
            "social_need": self.social_need.value,
            "novelty_need": self.novelty_need.value,
            "focus_fatigue": self.focus_fatigue.value,
        }
    
    def get_uncertainties(self) -> Dict[str, float]:
        """Get uncertainties for all dimensions."""
        return {
            "energy": self.energy.uncertainty,
            "safety_stress": self.safety_stress.uncertainty,
            "social_need": self.social_need.uncertainty,
            "novelty_need": self.novelty_need.uncertainty,
            "focus_fatigue": self.focus_fatigue.uncertainty,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "energy": self.energy.to_dict(),
            "safety_stress": self.safety_stress.to_dict(),
            "social_need": self.social_need.to_dict(),
            "novelty_need": self.novelty_need.to_dict(),
            "focus_fatigue": self.focus_fatigue.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BodyStateVector":
        """Deserialize from dictionary."""
        return cls(
            energy=BodyStateDimension.from_dict(data.get("energy", {})),
            safety_stress=BodyStateDimension.from_dict(data.get("safety_stress", {})),
            social_need=BodyStateDimension.from_dict(data.get("social_need", {})),
            novelty_need=BodyStateDimension.from_dict(data.get("novelty_need", {})),
            focus_fatigue=BodyStateDimension.from_dict(data.get("focus_fatigue", {})),
        )
    
    def clone(self) -> "BodyStateVector":
        """Create a deep copy of this body state vector."""
        return BodyStateVector.from_dict(self.to_dict())


# Global body state instance (singleton pattern)
_global_body_state: Optional[BodyStateVector] = None


def get_body_state() -> BodyStateVector:
    """Get the global body state vector (creates if needed)."""
    global _global_body_state
    if _global_body_state is None:
        _global_body_state = BodyStateVector()
    return _global_body_state


def set_body_state(body_state: BodyStateVector) -> None:
    """Set the global body state vector."""
    global _global_body_state
    _global_body_state = body_state


def reset_body_state() -> BodyStateVector:
    """Reset the global body state vector to defaults."""
    global _global_body_state
    _global_body_state = BodyStateVector()
    return _global_body_state
