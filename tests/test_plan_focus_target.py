"""
Test plan endpoint focus_target semantics and relationship handling
"""
import os
import pytest
import asyncio
from unittest.mock import patch
from emotiond.db import init_db, update_state, update_relationship
from emotiond.models import PlanRequest, PlanResponse
from emotiond.core import emotion_state, relationship_manager, generate_plan
from emotiond.config import DB_PATH


class TestPlanFocusTargetSemantics:
    """Test focus_target parameter and relationship semantics"""
    
    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Setup database for tests"""
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Initialize database
        asyncio.run(init_db())
        
        # Save original state
        original_relationships = dict(relationship_manager.relationships)
        original_valence = emotion_state.valence
        original_arousal = emotion_state.arousal
        
        # Reset in-memory state for this test
        relationship_manager.relationships = {}
        emotion_state.valence = 0.0
        emotion_state.arousal = 0.3
        
        # Clean up after tests
        yield
        
        # Restore original state
        relationship_manager.relationships = original_relationships
        emotion_state.valence = original_valence
        emotion_state.arousal = original_arousal
        
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    
    def test_plan_with_user_id_returns_relationship_for_user(self):
        """Test that /plan with user_id='X' returns relationship for X"""
        # Set up relationship for user X
        asyncio.run(update_state(0.3, 0.4, 100))
        asyncio.run(update_relationship("user_x", 0.7, 0.2))
        
        # Load into memory
        relationship_manager.relationships["user_x"] = {"bond": 0.7, "grudge": 0.2}
        
        # Generate plan without focus_target
        request = PlanRequest(
            user_id="user_x",
            user_text="Hello"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify relationship is for user_x
        assert response.focus_target == "user_x"
        assert response.relationship["bond"] == 0.7
        assert response.relationship["grudge"] == 0.2
        assert "trust" in response.relationship
    
    def test_plan_with_focus_target_returns_relationship_for_target(self):
        """Test that /plan with user_id='X' and focus_target='Y' returns relationship for Y"""
        # Set up relationships for different users
        asyncio.run(update_state(0.3, 0.4, 100))
        asyncio.run(update_relationship("user_x", 0.7, 0.2))
        asyncio.run(update_relationship("user_y", 0.3, 0.8))
        
        # Load into memory
        relationship_manager.relationships["user_x"] = {"bond": 0.7, "grudge": 0.2}
        relationship_manager.relationships["user_y"] = {"bond": 0.3, "grudge": 0.8}
        
        # Generate plan with focus_target='Y'
        request = PlanRequest(
            user_id="user_x",
            user_text="Hello",
            focus_target="user_y"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify relationship is for user_y (focus_target)
        assert response.focus_target == "user_y"
        assert response.relationship["bond"] == 0.3
        assert response.relationship["grudge"] == 0.8
    
    def test_plan_with_no_relationship_returns_empty(self):
        """Test that /plan returns empty relationship if no relationship exists"""
        asyncio.run(update_state(0.3, 0.4, 100))
        
        # No relationship set for new_user
        request = PlanRequest(
            user_id="new_user",
            user_text="Hello"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify empty relationship is returned
        assert response.focus_target == "new_user"
        assert response.relationship["bond"] == 0.0
        assert response.relationship["grudge"] == 0.0
        assert response.relationship["trust"] == 0.0
    
    def test_plan_with_focus_target_no_relationship_returns_empty(self):
        """Test that /plan with focus_target returns empty relationship if target has no relationship"""
        asyncio.run(update_state(0.3, 0.4, 100))
        relationship_manager.relationships["user_x"] = {"bond": 0.5, "grudge": 0.1}
        
        # focus_target='user_z' has no relationship
        request = PlanRequest(
            user_id="user_x",
            user_text="Hello",
            focus_target="user_z"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify empty relationship for user_z
        assert response.focus_target == "user_z"
        assert response.relationship["bond"] == 0.0
        assert response.relationship["grudge"] == 0.0
        assert response.relationship["trust"] == 0.0
    
    def test_plan_includes_trust_field(self):
        """Test that relationship includes trust field"""
        asyncio.run(update_state(0.3, 0.4, 100))
        relationship_manager.relationships["test_user"] = {"bond": 0.6, "grudge": 0.2}
        
        request = PlanRequest(
            user_id="test_user",
            user_text="Hello"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify trust field exists
        assert "trust" in response.relationship
        assert response.relationship["trust"] == 0.0  # Default value
    
    def test_plan_relationships_field_disabled_by_default(self):
        """Test that relationships field is None by default"""
        asyncio.run(update_state(0.3, 0.4, 100))
        relationship_manager.relationships["user_a"] = {"bond": 0.6, "grudge": 0.1}
        relationship_manager.relationships["user_b"] = {"bond": 0.3, "grudge": 0.5}
        
        request = PlanRequest(
            user_id="user_a",
            user_text="Hello"
        )
        
        response = asyncio.run(generate_plan(request))
        
        # Verify relationships field is None by default
        assert response.relationships is None
    
    def test_plan_relationships_field_enabled_with_env_flag(self):
        """Test that relationships field includes all relationships when env flag is set"""
        asyncio.run(update_state(0.3, 0.4, 100))
        relationship_manager.relationships["user_a"] = {"bond": 0.6, "grudge": 0.1}
        relationship_manager.relationships["user_b"] = {"bond": 0.3, "grudge": 0.5}
        
        # Set env flag
        with patch.dict(os.environ, {"EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS": "1"}):
            request = PlanRequest(
                user_id="user_a",
                user_text="Hello"
            )
            
            response = asyncio.run(generate_plan(request))
            
            # Verify relationships field includes all relationships
            assert response.relationships is not None
            assert "user_a" in response.relationships
            assert "user_b" in response.relationships
            assert response.relationships["user_a"]["bond"] == 0.6
            assert response.relationships["user_b"]["grudge"] == 0.5
            # Verify trust field in all relationships
            assert "trust" in response.relationships["user_a"]
            assert "trust" in response.relationships["user_b"]
    
    def test_plan_dynamic_target_any_string(self):
        """Test that target can be any string (not just A/B/C)"""
        asyncio.run(update_state(0.3, 0.4, 100))
        
        # Test with arbitrary user ID
        arbitrary_user = "arbitrary_user_123"
        relationship_manager.relationships[arbitrary_user] = {"bond": 0.8, "grudge": 0.1}
        
        request = PlanRequest(
            user_id=arbitrary_user,
            user_text="Hello"
        )
        
        response = asyncio.run(generate_plan(request))
        
        assert response.focus_target == arbitrary_user
        assert response.relationship["bond"] == 0.8
        assert response.relationship["grudge"] == 0.1
    
    def test_plan_dynamic_focus_target_any_string(self):
        """Test that focus_target can be any string"""
        asyncio.run(update_state(0.3, 0.4, 100))
        
        arbitrary_target = "some_random_target_xyz"
        relationship_manager.relationships[arbitrary_target] = {"bond": 0.4, "grudge": 0.6}
        
        request = PlanRequest(
            user_id="user_a",
            user_text="Hello",
            focus_target=arbitrary_target
        )
        
        response = asyncio.run(generate_plan(request))
        
        assert response.focus_target == arbitrary_target
        assert response.relationship["bond"] == 0.4
        assert response.relationship["grudge"] == 0.6


class TestPlanAPIClient:
    """Test plan API with focus_target via HTTP client"""
    
    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Setup database for tests"""
        os.makedirs("data", exist_ok=True)
        asyncio.run(init_db())
        
        # Save original state
        original_relationships = dict(relationship_manager.relationships)
        original_valence = emotion_state.valence
        original_arousal = emotion_state.arousal
        
        relationship_manager.relationships = {}
        emotion_state.valence = 0.0
        emotion_state.arousal = 0.3
        
        yield
        
        # Restore original state
        relationship_manager.relationships = original_relationships
        emotion_state.valence = original_valence
        emotion_state.arousal = original_arousal
        
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
    
    def test_api_plan_with_focus_target(self):
        """Test POST /plan with focus_target parameter"""
        from fastapi.testclient import TestClient
        from emotiond.api import app
        
        client = TestClient(app)
        
        # Set up relationships
        asyncio.run(update_state(0.3, 0.4, 100))
        asyncio.run(update_relationship("user_x", 0.7, 0.2))
        asyncio.run(update_relationship("user_y", 0.3, 0.8))
        
        relationship_manager.relationships["user_x"] = {"bond": 0.7, "grudge": 0.2}
        relationship_manager.relationships["user_y"] = {"bond": 0.3, "grudge": 0.8}
        
        # Request with focus_target
        request_data = {
            "user_id": "user_x",
            "user_text": "Hello",
            "focus_target": "user_y"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify relationship is for focus_target (user_y)
        assert data["focus_target"] == "user_y"
        assert data["relationship"]["bond"] == 0.3
        assert data["relationship"]["grudge"] == 0.8
        assert "trust" in data["relationship"]
    
    def test_api_plan_without_focus_target_defaults_to_user_id(self):
        """Test POST /plan without focus_target defaults to user_id"""
        from fastapi.testclient import TestClient
        from emotiond.api import app
        
        client = TestClient(app)
        
        asyncio.run(update_state(0.3, 0.4, 100))
        asyncio.run(update_relationship("user_x", 0.7, 0.2))
        
        relationship_manager.relationships["user_x"] = {"bond": 0.7, "grudge": 0.2}
        
        # Request without focus_target
        request_data = {
            "user_id": "user_x",
            "user_text": "Hello"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify focus_target defaults to user_id
        assert data["focus_target"] == "user_x"
        assert data["relationship"]["bond"] == 0.7
        assert data["relationship"]["grudge"] == 0.2
    
    def test_api_plan_with_env_flag_includes_all_relationships(self):
        """Test POST /plan with env flag includes all relationships"""
        from fastapi.testclient import TestClient
        from emotiond.api import app
        
        client = TestClient(app)
        
        asyncio.run(update_state(0.3, 0.4, 100))
        relationship_manager.relationships["user_a"] = {"bond": 0.6, "grudge": 0.1}
        relationship_manager.relationships["user_b"] = {"bond": 0.3, "grudge": 0.5}
        
        # Set env flag
        with patch.dict(os.environ, {"EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS": "1"}):
            request_data = {
                "user_id": "user_a",
                "user_text": "Hello"
            }
            
            response = client.post("/plan", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify relationships field is present
            assert "relationships" in data
            assert data["relationships"] is not None
            assert "user_a" in data["relationships"]
            assert "user_b" in data["relationships"]
