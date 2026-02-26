"""
Test plan generation endpoint functionality
"""
import os
import pytest
import asyncio
from emotiond.db import init_db, update_state, update_relationship
from emotiond.models import PlanRequest, PlanResponse
from emotiond.core import emotion_state, relationship_manager, generate_plan
from emotiond.config import DB_PATH


class TestPlanGeneration:
    """Test plan generation functionality"""
    
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        """Setup database for tests"""
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Initialize database
        await init_db()
        
        # Clean up after tests
        yield
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    
    async def test_plan_generation_returns_valid_response(self):
        """Test that generate_plan returns valid Response Plan JSON"""
        # Set up initial state
        await update_state(0.5, 0.3, 100)
        await update_relationship("test_user", 0.7, 0.1)
        
        # Load state into memory
        await asyncio.sleep(0.1)  # Allow state to load
        
        # Generate plan
        request = PlanRequest(
            user_id="test_user",
            user_text="How are you?"
        )
        
        response = await generate_plan(request)
        
        # Verify response structure
        assert isinstance(response, PlanResponse)
        assert hasattr(response, "tone")
        assert hasattr(response, "intent")
        assert hasattr(response, "focus_target")
        assert hasattr(response, "key_points")
        assert hasattr(response, "constraints")
        assert hasattr(response, "emotion")
        assert hasattr(response, "relationship")
    
    async def test_plan_includes_all_required_fields(self):
        """Test that plan response includes all required fields"""
        # Set up initial state
        await update_state(0.2, 0.4, 100)
        await update_relationship("user_a", 0.5, 0.2)
        
        # Load state into memory
        await asyncio.sleep(0.1)
        
        # Generate plan
        request = PlanRequest(
            user_id="user_a",
            user_text="What do you think?"
        )
        
        response = await generate_plan(request)
        
        # Check all required fields
        assert response.tone in ["soft", "warm", "guarded", "cold"]
        assert response.intent in ["repair", "distance", "seek", "set_boundary", "retaliate"]
        assert response.focus_target == "user_a"
        assert isinstance(response.key_points, list)
        assert isinstance(response.constraints, list)
        assert isinstance(response.emotion, dict)
        assert "valence" in response.emotion
        assert "arousal" in response.emotion
        assert isinstance(response.relationship, dict)
        assert "bond" in response.relationship
        assert "grudge" in response.relationship
    
    async def test_plan_tone_values(self):
        """Test that tone values are valid"""
        valid_tones = {"soft", "warm", "guarded", "cold"}
        
        # Test multiple scenarios
        test_scenarios = [
            (0.8, 0.2, 0.8, 0.1, "warm"),    # High valence, low arousal, high bond
            (0.4, 0.6, 0.6, 0.2, "soft"),    # Positive valence, moderate bond
            (-0.1, 0.4, 0.4, 0.3, "guarded"), # Slightly negative
            (-0.5, 0.6, 0.3, 0.8, "cold"),   # Very negative, high grudge
        ]
        
        for valence, arousal, bond, grudge, expected_tone in test_scenarios:
            await update_state(valence, arousal, 100)
            await update_relationship("test_user", bond, grudge)
            
            # Load state into memory
            await asyncio.sleep(0.1)
            
            request = PlanRequest(
                user_id="test_user",
                user_text="Test"
            )
            
            response = await generate_plan(request)
            assert response.tone in valid_tones
    
    async def test_plan_intent_values(self):
        """Test that intent values are valid"""
        valid_intents = {"repair", "distance", "seek", "set_boundary", "retaliate"}
        
        # Test multiple scenarios
        test_scenarios = [
            (-0.3, 0.8, 0.9, "retaliate"),    # Very negative, high grudge
            (0.2, 0.3, 0.8, "seek"),          # High bond
            (-0.2, 0.5, 0.2, "repair"),       # Negative valence
            (0.1, 0.4, 0.3, "set_boundary"),  # Default case
        ]
        
        for valence, grudge, bond, expected_intent in test_scenarios:
            await update_state(valence, 0.4, 100)
            await update_relationship("test_user", bond, grudge)
            
            # Load state into memory
            await asyncio.sleep(0.1)
            
            request = PlanRequest(
                user_id="test_user",
                user_text="Test"
            )
            
            response = await generate_plan(request)
            assert response.intent in valid_intents
    
    async def test_plan_emotion_range(self):
        """Test that emotion values are within valid ranges"""
        await update_state(-0.7, 0.9, 100)
        await update_relationship("test_user", 0.2, 0.8)
        
        # Load state into memory
        await asyncio.sleep(0.1)
        
        request = PlanRequest(
            user_id="test_user",
            user_text="Test"
        )
        
        response = await generate_plan(request)
        
        # Check emotion ranges
        assert -1.0 <= response.emotion["valence"] <= 1.0
        assert 0.0 <= response.emotion["arousal"] <= 1.0
        
        # Check relationship ranges
        assert 0.0 <= response.relationship["bond"] <= 1.0
        assert 0.0 <= response.relationship["grudge"] <= 1.0
    
    async def test_plan_key_points_and_constraints(self):
        """Test that key_points and constraints are generated"""
        await update_state(0.3, 0.4, 100)
        await update_relationship("test_user", 0.6, 0.2)
        
        # Load state into memory
        await asyncio.sleep(0.1)
        
        request = PlanRequest(
            user_id="test_user",
            user_text="Test"
        )
        
        response = await generate_plan(request)
        
        # Verify key_points and constraints exist
        assert isinstance(response.key_points, list)
        assert isinstance(response.constraints, list)
        assert len(response.key_points) > 0
        assert len(response.constraints) > 0
        
        # Verify they are strings
        for point in response.key_points:
            assert isinstance(point, str)
        for constraint in response.constraints:
            assert isinstance(constraint, str)