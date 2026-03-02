"""Tests for US-651 Homeostasis Drive v0."""

import pytest
from core.drive_homeostasis import (
    DriveType,
    DriveRange,
    DriveState,
    huber_loss,
    drive_error,
    emotion_from_drive,
    modulate_strategy,
    score_rollout_candidate,
)


class TestDriveRange:
    def test_contains(self):
        r = DriveRange(0.3, 0.7)
        assert r.contains(0.5)
        assert r.contains(0.3)
        assert r.contains(0.7)
        assert not r.contains(0.2)
        assert not r.contains(0.8)
    
    def test_clamp(self):
        r = DriveRange(0.3, 0.7)
        assert r.clamp(0.5) == 0.5
        assert r.clamp(0.2) == 0.3
        assert r.clamp(0.8) == 0.7
    
    def test_distance_from_optimal(self):
        r = DriveRange(0.0, 1.0)
        assert r.distance_from_optimal(0.5) == 0.0
        assert r.distance_from_optimal(0.0) == 1.0
        assert r.distance_from_optimal(1.0) == 1.0


class TestHuberLoss:
    def test_huber_small_values(self):
        assert huber_loss(0.1) == pytest.approx(0.5 * 0.1 ** 2)
        assert huber_loss(-0.2) == pytest.approx(0.5 * 0.2 ** 2)
    
    def test_huber_large_values(self):
        delta = 1.0
        assert huber_loss(2.0) == delta * (2.0 - 0.5 * delta)
        assert huber_loss(-2.0) == delta * (2.0 - 0.5 * delta)


class TestDriveState:
    def test_default_state(self):
        state = DriveState()
        assert 0 <= state.energy <= 1
        assert 0 <= state.uncertainty <= 1
        assert state.setpoints is not None
    
    def test_serialization(self):
        state = DriveState(energy=0.8, uncertainty=0.1)
        data = state.to_dict()
        assert data["energy"] == 0.8
        assert data["uncertainty"] == 0.1
        
        restored = DriveState.from_dict(data)
        assert restored.energy == 0.8
        assert restored.uncertainty == 0.1
    
    def test_get_set_drive(self):
        state = DriveState()
        state.set_drive(DriveType.ENERGY, 0.9)
        assert state.get_drive(DriveType.ENERGY) == 0.9
        
        # Test clamping
        state.set_drive(DriveType.ENERGY, 1.5)
        assert state.get_drive(DriveType.ENERGY) == 1.0


class TestDriveError:
    def test_low_error_when_in_range(self):
        state = DriveState(energy=0.5, uncertainty=0.1, safety=0.8, fatigue=0.1)
        error = drive_error(state)
        assert error < 0.5
    
    def test_high_error_when_out_of_range(self):
        state = DriveState(energy=0.1, uncertainty=0.9, safety=0.1, fatigue=0.9)
        error = drive_error(state)
        assert error > 0.2  # Huber loss reduces extreme values
    
    def test_custom_weights(self):
        state = DriveState(uncertainty=0.9)
        error_low = drive_error(state, weights={DriveType.UNCERTAINTY: 0.1})
        error_high = drive_error(state, weights={DriveType.UNCERTAINTY: 2.0})
        assert error_high > error_low


class TestEmotionFromDrive:
    def test_balanced_state(self):
        state = DriveState(energy=0.6, uncertainty=0.2, social=0.5, safety=0.8, fatigue=0.2)
        emotions = emotion_from_drive(state)
        assert all(0 <= v <= 1 for v in emotions.values())
        # Balanced state should have moderate positive emotions
        assert emotions["contentment"] >= 0.3
    
    def test_high_uncertainty_increases_anxiety(self):
        low_uncertainty = DriveState(uncertainty=0.1)
        high_uncertainty = DriveState(uncertainty=0.8)
        
        emotions_low = emotion_from_drive(low_uncertainty)
        emotions_high = emotion_from_drive(high_uncertainty)
        
        assert emotions_high["anxiety"] > emotions_low["anxiety"]
        assert emotions_high["fear"] >= emotions_low["fear"]
    
    def test_low_social_increases_loneliness(self):
        low_social = DriveState(social=0.1)
        high_social = DriveState(social=0.8)
        
        emotions_low = emotion_from_drive(low_social)
        emotions_high = emotion_from_drive(high_social)
        
        assert emotions_low["loneliness"] > emotions_high["loneliness"]
    
    def test_high_fatigue_reduces_joy(self):
        low_fatigue = DriveState(fatigue=0.1)
        high_fatigue = DriveState(fatigue=0.8)
        
        emotions_low = emotion_from_drive(low_fatigue)
        emotions_high = emotion_from_drive(high_fatigue)
        
        assert emotions_high["joy"] < emotions_low["joy"]


class TestModulateStrategy:
    def test_base_strategy_when_balanced(self):
        state = DriveState(energy=0.6, uncertainty=0.2, fatigue=0.2, safety=0.8)
        selected, info = modulate_strategy(state, "default", ["default", "clarify"])
        assert selected == "default"
    
    def test_high_uncertainty_selects_clarify(self):
        state = DriveState(uncertainty=0.7)
        selected, info = modulate_strategy(state, "default", ["default", "clarify"])
        assert selected == "clarify"
        assert any(m["reason"] == "high_uncertainty" for m in info["modulations"])
    
    def test_high_fatigue_selects_conservative(self):
        state = DriveState(fatigue=0.8)
        selected, info = modulate_strategy(state, "default", ["default", "conservative"])
        assert selected == "conservative"
    
    def test_low_safety_selects_cautious(self):
        state = DriveState(safety=0.2)
        selected, info = modulate_strategy(state, "default", ["default", "cautious"])
        assert selected == "cautious"


class TestScoreRolloutCandidate:
    def test_rest_action_reduces_fatigue_error(self):
        state = DriveState(fatigue=0.8, energy=0.3)
        candidate = {"action": "take a rest"}
        score, info = score_rollout_candidate(state, candidate, 0.5)
        
        assert info["error_reduction"] > 0
        assert score > 0.5  # Should get bonus
    
    def test_clarify_action_reduces_uncertainty_error(self):
        state = DriveState(uncertainty=0.8)
        candidate = {"action": "clarify the situation"}
        score, info = score_rollout_candidate(state, candidate, 0.5)
        
        assert info["error_reduction"] > 0
    
    def test_neutral_action_no_change(self):
        state = DriveState()
        candidate = {"action": "wait"}
        score, info = score_rollout_candidate(state, candidate, 0.5)
        
        # No significant change expected
        assert abs(info["error_reduction"]) < 0.5
