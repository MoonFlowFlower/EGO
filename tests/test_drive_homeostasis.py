"""
Tests for US-651: Homeostasis Drive v0
"""

import pytest
from datetime import datetime, timedelta
from emotiond.drive_homeostasis import DriveState, drive_error, emotion_from_drive


class TestHomeostasisDrive:
    """Test homeostatic drive system"""
    
    def test_drive_component_computation(self):
        """Test individual drive components compute correctly"""
        state = DriveState()
        
        # Test normal range
        state.update_component("energy", 0.7)
        state.update_component("uncertainty", 0.3)
        state.update_component("social", 0.5)
        state.update_component("safety", 0.8)
        state.update_component("fatigue", 0.2)
        
        # Verify setpoints and deviations
        assert state.get_deviation("energy") == pytest.approx(0.7 - 0.75, abs=1e-3)
        assert state.get_deviation("uncertainty") == pytest.approx(0.3 - 0.25, abs=1e-3)
        assert state.get_deviation("fatigue") == pytest.approx(0.2 - 0.15, abs=1e-3)
        
        # Drive error should be positive
        error = drive_error(state)
        assert error > 0
        
    def test_drive_error_degraded_state(self):
        """Test drive error increases in degraded state"""
        state = DriveState()
        
        # Normal state
        state.update_component("energy", 0.8)
        state.update_component("safety", 0.9)
        normal_error = drive_error(state)
        
        # Degraded state
        state.update_component("energy", 0.2)  # Low energy
        state.update_component("safety", 0.1)  # Low safety
        state.update_component("fatigue", 0.9)  # High fatigue
        
        degraded_error = drive_error(state)
        
        # Degraded should have higher error
        assert degraded_error > normal_error
        
    def test_drive_history_size_limit(self):
        """Test drive state history respects size limit"""
        state = DriveState(max_history=3)
        
        # Add more entries than limit
        for i in range(5):
            state.update_component("energy", 0.5 + i * 0.1)
        
        # Should only keep last 3 entries
        assert len(state.history) == 3
        
        # Verify it's the most recent entries
        assert state.history[-1]["energy"] == pytest.approx(0.9, abs=1e-3)
        
    def test_emotion_from_drive_explainability(self):
        """Test emotion_from_drive provides interpretable mapping"""
        state = DriveState()
        
        # High uncertainty, low safety → anxiety-like
        state.update_component("uncertainty", 0.9)
        state.update_component("safety", 0.1)
        
        emotion = emotion_from_drive(state)
        
        # Should contain anxiety/fear components
        assert "anxiety" in emotion.lower() or "fear" in emotion.lower()
        
        # High energy, low fatigue → approach-like
        state2 = DriveState()
        state2.update_component("energy", 0.9)
        state2.update_component("fatigue", 0.1)
        
        emotion2 = emotion_from_drive(state2)
        
        # Should contain positive/approach components
        assert any(word in emotion2.lower() for word in ["approach", "engaged", "positive"])
        
    def test_drive_error_zero_perfect(self):
        """Test drive error is zero for perfect homeostasis"""
        state = DriveState()
        
        # Set all components to perfect setpoints
        for component, setpoint in state.setpoints.items():
            state.update_component(component, setpoint)
        
        error = drive_error(state)
        assert error == pytest.approx(0.0, abs=1e-6)
        
    def test_drive_error_symmetry(self):
        """Test drive error is symmetric around setpoint"""
        state = DriveState()
        
        # Above setpoint
        state.update_component("energy", 0.9)
        error_above = drive_error(state)
        
        # Below setpoint (same distance)
        state.update_component("energy", 0.6)
        error_below = drive_error(state)
        
        # Should be approximately equal for symmetric deviations
        assert abs(error_above - error_below) < 0.1
