"""
Homeostasis Drive v0 - MVP-7 US-651

Drive system that maintains setpoints and influences decision-making.
Provides engineering version of homeostasis/free-energy principle.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import time
from enum import Enum


class DriveType(Enum):
    ENERGY = "energy"
    UNCERTAINTY = "uncertainty"
    SOCIAL = "social"
    SAFETY = "safety"
    FATIGUE = "fatigue"


@dataclass
class DriveState:
    """Current state of all drives with their setpoints and values."""
    
    # Current values (0-1 normalized)
    energy: float = 0.8
    uncertainty: float = 0.3
    social: float = 0.7
    safety: float = 0.9
    fatigue: float = 0.2
    
    # Setpoints (optimal ranges)
    energy_setpoint: Tuple[float, float] = (0.7, 0.9)
    uncertainty_setpoint: Tuple[float, float] = (0.1, 0.3)
    social_setpoint: Tuple[float, float] = (0.6, 0.8)
    safety_setpoint: Tuple[float, float] = (0.8, 1.0)
    fatigue_setpoint: Tuple[float, float] = (0.0, 0.3)
    
    # Weights for combining drive errors
    weights: Dict[DriveType, float] = field(default_factory=lambda: {
        DriveType.ENERGY: 0.3,
        DriveType.UNCERTAINTY: 0.25,
        DriveType.SOCIAL: 0.2,
        DriveType.SAFETY: 0.15,
        DriveType.FATIGUE: 0.1
    })
    
    # Last update timestamp
    last_update: float = field(default_factory=time.time)
    
    def update_value(self, drive_type: DriveType, value: float) -> None:
        """Update a drive value with validation."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Drive value must be in [0,1], got {value}")
        
        setattr(self, drive_type.value, value)
        self.last_update = time.time()
    
    def get_value(self, drive_type: DriveType) -> float:
        """Get current value of a drive."""
        return getattr(self, drive_type.value)
    
    def get_setpoint(self, drive_type: DriveType) -> Tuple[float, float]:
        """Get setpoint range for a drive."""
        return getattr(self, f"{drive_type.value}_setpoint")


class HomeostasisDrive:
    """Main drive system maintaining homeostasis."""
    
    def __init__(self, state: Optional[DriveState] = None):
        self.state = state or DriveState()
        self._huber_delta = 0.1  # Huber loss threshold for robust error calculation
    
    def _compute_drive_error(self, drive_type: DriveType) -> float:
        """
        Compute deviation from setpoint using Huber loss for robustness.
        
        Returns error in [0, 1], where 0 = perfect, 1 = maximum deviation.
        """
        value = self.state.get_value(drive_type)
        setpoint_min, setpoint_max = self.state.get_setpoint(drive_type)
        
        # If within setpoint, no error
        if setpoint_min <= value <= setpoint_max:
            return 0.0
        
        # Compute deviation from nearest setpoint bound
        if value < setpoint_min:
            deviation = setpoint_min - value
        else:
            deviation = value - setpoint_max
        
        # Normalize by maximum possible deviation (0 to 1 range)
        max_deviation = max(setpoint_min, 1.0 - setpoint_max)
        normalized_deviation = min(deviation / max_deviation, 1.0)
        
        # Apply Huber loss for robustness
        if normalized_deviation <= self._huber_delta:
            # Quadratic for small errors
            return (normalized_deviation ** 2) / (2 * self._huber_delta)
        else:
            # Linear for large errors
            return normalized_deviation - self._huber_delta / 2
    
    def drive_error(self) -> float:
        """
        Compute overall drive error as weighted sum of individual drive errors.
        
        Returns:
            Overall drive error in [0, 1]
        """
        total_error = 0.0
        total_weight = 0.0
        
        for drive_type in DriveType:
            error = self._compute_drive_error(drive_type)
            weight = self.state.weights[drive_type]
            total_error += error * weight
            total_weight += weight
        
        return total_error / total_weight if total_weight > 0 else 0.0
    
    def emotion_from_drive(self) -> Dict[str, float]:
        """
        Map drive states to interpretable emotion-like signals.
        
        Returns:
            Dictionary of emotion-like signals with explainable mappings.
        """
        energy = self.state.get_value(DriveType.ENERGY)
        uncertainty = self.state.get_value(DriveType.UNCERTAINTY)
        social = self.state.get_value(DriveType.SOCIAL)
        safety = self.state.get_value(DriveType.SAFETY)
        fatigue = self.state.get_value(DriveType.FATIGUE)
        
        # Explainable mappings from drives to emotion-like signals
        return {
            "confidence": energy * safety * (1 - uncertainty),  # High energy + safety + low uncertainty
            "curiosity": (1 - fatigue) * uncertainty,  # Low fatigue + high uncertainty
            "affiliation": social * energy * (1 - fatigue),  # Social + energy + not tired
            "caution": uncertainty * (1 - safety),  # High uncertainty + low safety
            "rest_need": fatigue * (1 - energy),  # Tired + low energy
        }
    
    def get_drive_modulations(self) -> Dict[str, float]:
        """
        Compute modulation factors for decision-making based on drive states.
        
        Returns:
            Dictionary of modulation factors for different aspects of behavior.
        """
        energy = self.state.get_value(DriveType.ENERGY)
        uncertainty = self.state.get_value(DriveType.UNCERTAINTY)
        social = self.state.get_value(DriveType.SOCIAL)
        safety = self.state.get_value(DriveType.SAFETY)
        fatigue = self.state.get_value(DriveType.FATIGUE)
        
        return {
            # Rollout scoring modulation
            "rollout_drive_bias": self.drive_error(),  # Higher error = more drive-motivated
            
            # Strategy modulation
            "conservatism_factor": (1 - safety) + fatigue,  # Low safety + high fatigue = more conservative
            "clarification倾向": uncertainty * (1 - fatigue),  # High uncertainty + energy = seek clarification
            "social_engagement": social * energy * (1 - fatigue),  # Social when energized and not tired
            
            # Response modulation
            "response_length_factor": (1 - fatigue) * energy,  # Longer responses when not tired + energized
            "risk_tolerance": safety * energy * (1 - uncertainty),  # Take risks when safe + energized + certain
            
            # Sampling parameters (if using LLM)
            "temperature_modulation": uncertainty * (1 - safety),  # Higher temp when uncertain + unsafe
            "top_p_modulation": 1.0 - fatigue,  # More diverse when not fatigued
        }
    
    def apply_drive_to_decision(self, 
                              base_strategy: str,
                              context: Dict[str, any]) -> Dict[str, any]:
        """
        Apply drive modulation to a decision context.
        
        Args:
            base_strategy: Base decision strategy
            context: Decision context
            
        Returns:
            Modified context with drive influences applied.
        """
        modulations = self.get_drive_modulations()
        emotions = self.emotion_from_drive()
        
        # Add drive information to context
        context["drive_state"] = {
            "error": self.drive_error(),
            "modulations": modulations,
            "emotions": emotions,
            "timestamp": self.state.last_update
        }
        
        # Apply specific modulations based on strategy
        if base_strategy == "rollout_selection":
            # Bias rollout selection toward drive-reducing options
            context["drive_bias"] = modulations["rollout_drive_bias"]
            
        elif base_strategy == "response_generation":
            # Modulate response characteristics
            context["response_factors"] = {
                "length_bias": modulations["response_length_factor"],
                "conservatism": modulations["conservatism_factor"],
                "clarification_need": modulations["clarification倾向"]
            }
            
        elif base_strategy == "risk_assessment":
            # Directly influence risk tolerance
            context["risk_tolerance"] = modulations["risk_tolerance"]
        
        return context
    
    def update_from_feedback(self, feedback: Dict[str, float]) -> None:
        """
        Update drive states based on environmental feedback.
        
        Args:
            feedback: Dictionary mapping drive types to delta changes
        """
        for drive_name, delta in feedback.items():
            try:
                drive_type = DriveType(drive_name)
                current_value = self.state.get_value(drive_type)
                new_value = max(0.0, min(1.0, current_value + delta))
                self.state.update_value(drive_type, new_value)
            except ValueError:
                # Ignore unknown drive types
                continue
    
    def get_drive_summary(self) -> Dict[str, any]:
        """
        Get a comprehensive summary of current drive state.
        
        Returns:
            Dictionary with drive summary for debugging and monitoring.
        """
        return {
            "overall_error": self.drive_error(),
            "individual_drives": {
                drive_type.value: {
                    "value": self.state.get_value(drive_type),
                    "setpoint": self.state.get_setpoint(drive_type),
                    "error": self._compute_drive_error(drive_type)
                }
                for drive_type in DriveType
            },
            "emotions": self.emotion_from_drive(),
            "modulations": self.get_drive_modulations(),
            "last_update": self.state.last_update
        }


# Global instance for use across the system
_drive_instance: Optional[HomeostasisDrive] = None


def get_drive() -> HomeostasisDrive:
    """Get or create the global drive instance."""
    global _drive_instance
    if _drive_instance is None:
        _drive_instance = HomeostasisDrive()
    return _drive_instance


def reset_drive() -> None:
    """Reset the global drive instance (for testing)."""
    global _drive_instance
    _drive_instance = None
