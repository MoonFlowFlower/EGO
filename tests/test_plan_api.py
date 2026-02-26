"""
Test plan generation API endpoint
"""
import os
import pytest
from fastapi.testclient import TestClient
from emotiond.api import app
from emotiond.db import init_db, update_state, update_relationship
from emotiond.config import DB_PATH


class TestPlanAPI:
    """Test plan generation API endpoint"""
    
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
    
    def test_plan_endpoint_returns_valid_json(self):
        """Test POST /plan endpoint returns valid Response Plan JSON"""
        client = TestClient(app)
        
        # Set up initial state
        asyncio.run(update_state(0.5, 0.3, 100))
        asyncio.run(update_relationship("test_user", 0.7, 0.1))
        
        request_data = {
            "user_id": "test_user",
            "user_text": "How are you feeling?"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "tone" in data
        assert "intent" in data
        assert "focus_target" in data
        assert "key_points" in data
        assert "constraints" in data
        assert "emotion" in data
        assert "relationship" in data
    
    def test_plan_endpoint_includes_all_required_fields(self):
        """Test POST /plan endpoint includes all required fields"""
        client = TestClient(app)
        
        # Set up initial state
        asyncio.run(update_state(0.2, 0.4, 100))
        asyncio.run(update_relationship("user_b", 0.5, 0.2))
        
        request_data = {
            "user_id": "user_b",
            "user_text": "What's on your mind?"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert data["tone"] in ["soft", "warm", "guarded", "cold"]
        assert data["intent"] in ["repair", "distance", "seek", "set_boundary", "retaliate"]
        assert data["focus_target"] == "user_b"
        assert isinstance(data["key_points"], list)
        assert isinstance(data["constraints"], list)
        assert isinstance(data["emotion"], dict)
        assert "valence" in data["emotion"]
        assert "arousal" in data["emotion"]
        assert isinstance(data["relationship"], dict)
        assert "bond" in data["relationship"]
        assert "grudge" in data["relationship"]
    
    def test_plan_endpoint_emotion_ranges(self):
        """Test that emotion values in plan response are within valid ranges"""
        client = TestClient(app)
        
        # Set up extreme state
        asyncio.run(update_state(-0.9, 0.95, 100))
        asyncio.run(update_relationship("test_user", 0.1, 0.9))
        
        request_data = {
            "user_id": "test_user",
            "user_text": "Test"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check emotion ranges
        assert -1.0 <= data["emotion"]["valence"] <= 1.0
        assert 0.0 <= data["emotion"]["arousal"] <= 1.0
        
        # Check relationship ranges
        assert 0.0 <= data["relationship"]["bond"] <= 1.0
        assert 0.0 <= data["relationship"]["grudge"] <= 1.0
    
    def test_plan_endpoint_key_points_and_constraints(self):
        """Test that key_points and constraints are generated in plan response"""
        client = TestClient(app)
        
        # Set up state
        asyncio.run(update_state(0.4, 0.5, 100))
        asyncio.run(update_relationship("test_user", 0.6, 0.3))
        
        request_data = {
            "user_id": "test_user",
            "user_text": "Hello"
        }
        
        response = client.post("/plan", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify key_points and constraints exist
        assert isinstance(data["key_points"], list)
        assert isinstance(data["constraints"], list)
        assert len(data["key_points"]) > 0
        assert len(data["constraints"]) > 0
        
        # Verify they are strings
        for point in data["key_points"]:
            assert isinstance(point, str)
        for constraint in data["constraints"]:
            assert isinstance(constraint, str)
    
    def test_plan_endpoint_with_different_users(self):
        """Test that plan endpoint works with different user IDs"""
        client = TestClient(app)
        
        # Set up different relationships for different users
        asyncio.run(update_state(0.3, 0.4, 100))
        asyncio.run(update_relationship("user_a", 0.8, 0.1))
        asyncio.run(update_relationship("user_b", 0.2, 0.7))
        
        # Test user A (high bond, low grudge)
        request_a = {
            "user_id": "user_a",
            "user_text": "Hello"
        }
        response_a = client.post("/plan", json=request_a)
        assert response_a.status_code == 200
        data_a = response_a.json()
        assert data_a["focus_target"] == "user_a"
        assert data_a["relationship"]["bond"] > 0.5
        
        # Test user B (low bond, high grudge)
        request_b = {
            "user_id": "user_b",
            "user_text": "Hello"
        }
        response_b = client.post("/plan", json=request_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert data_b["focus_target"] == "user_b"
        assert data_b["relationship"]["grudge"] > 0.5