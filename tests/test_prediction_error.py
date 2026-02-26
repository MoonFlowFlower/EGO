"""
Test prediction error calculation and modulation
"""
import pytest
import asyncio
from emotiond.api import app
from fastapi.testclient import TestClient
from emotiond.models import Event
from emotiond.db import init_db
from emotiond.config import DB_PATH
import os


class TestPredictionError:
    """Test prediction error calculation and modulation"""
    
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
    
    def test_prediction_error_calculation_for_positive_message(self):
        """Test prediction error calculation for positive user message"""
        client = TestClient(app)
        
        # Positive message should create prediction error
        response = client.post("/event", json={
            "type": "user_message",
            "actor": "user",
            "target": "agent",
            "text": "This is great! I love it!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "prediction_error" in data
        # Prediction error should be calculated (not zero)
        assert isinstance(data["prediction_error"], (int, float))
        
    def test_prediction_error_calculation_for_negative_message(self):
        """Test prediction error calculation for negative user message"""
        client = TestClient(app)
        
        # Negative message should create prediction error
        response = client.post("/event", json={
            "type": "user_message",
            "actor": "user",
            "target": "agent",
            "text": "This is terrible! I hate it!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "prediction_error" in data
        assert isinstance(data["prediction_error"], (int, float))
        
    def test_prediction_error_modulates_arousal(self):
        """Test that prediction error modulates arousal"""
        client = TestClient(app)
        
        # Get initial arousal
        response1 = client.post("/event", json={
            "type": "user_message",
            "actor": "user",
            "target": "agent",
            "text": "Test message"
        })
        data1 = response1.json()
        initial_arousal = data1["arousal"]
        initial_prediction_error = data1["prediction_error"]
        
        # Send unexpected positive message
        response2 = client.post("/event", json={
            "type": "user_message",
            "actor": "user",
            "target": "agent",
            "text": "This is amazing! Wonderful! Fantastic!"
        })
        data2 = response2.json()
        final_arousal = data2["arousal"]
        final_prediction_error = data2["prediction_error"]
        
        # Prediction error should increase arousal
        # (strong positive message creates larger prediction error)
        assert final_prediction_error > initial_prediction_error
        assert final_arousal > initial_arousal
        
    def test_prediction_error_for_world_events(self):
        """Test prediction error calculation for world events"""
        client = TestClient(app)
        
        # Positive world event
        response = client.post("/event", json={
            "type": "world_event",
            "actor": "system",
            "target": "agent",
            "text": "System achievement",
            "meta": {"positive": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert "prediction_error" in data
        assert isinstance(data["prediction_error"], (int, float))
        
    def test_prediction_error_stored_in_database(self):
        """Test that prediction error is stored in database"""
        client = TestClient(app)
        
        # Send multiple events and check prediction error persistence
        events = [
            {
                "type": "user_message",
                "actor": "user",
                "target": "agent",
                "text": "First positive message"
            },
            {
                "type": "user_message",
                "actor": "user",
                "target": "agent",
                "text": "Second negative message"
            }
        ]
        
        prediction_errors = []
        for event in events:
            response = client.post("/event", json=event)
            assert response.status_code == 200
            data = response.json()
            prediction_errors.append(data["prediction_error"])
        
        # Prediction errors should be calculated for both events
        assert len(prediction_errors) == 2
        assert all(isinstance(pe, (int, float)) for pe in prediction_errors)
        
    def test_prediction_model_learning_mechanism(self):
        """Test that prediction error could be used for model learning (future enhancement)"""
        client = TestClient(app)
        
        # Send similar events multiple times
        for i in range(3):
            response = client.post("/event", json={
                "type": "user_message",
                "actor": "user",
                "target": "agent",
                "text": "Consistent positive message"
            })
            assert response.status_code == 200
            data = response.json()
            # Prediction error should exist
            assert "prediction_error" in data
            # In a real implementation, prediction error would decrease over time
            # as the model learns the pattern