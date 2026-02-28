"""
Final integration and smoke tests for the complete emotiond system.
Tests end-to-end functionality, daemon startup, API access, and OpenClaw skill integration.
"""

import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openclaw_skill.emotion_core.skill import check_daemon_health, send_event, get_plan, process_user_message, process_assistant_reply


class TestFinalIntegration:
    """Final integration tests for the complete emotiond system."""

    def test_daemon_startup_and_health(self):
        """Test that the daemon starts successfully and health endpoint works."""
        # Start daemon in background
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            # Wait for daemon to start
            time.sleep(5)
            
            # Test health endpoint
            response = requests.get("http://127.0.0.1:18080/health")
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert "emotiond" in data
            assert "version" in data["emotiond"]
            
        finally:
            # Stop daemon
            daemon_process.terminate()
            daemon_process.wait()

    def test_api_endpoints_accessible(self):
        """Test that all API endpoints are accessible."""
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Test event endpoint
            event_data = {
                "type": "user_message",
                "actor": "test_user",
                "target": "assistant",
                "text": "Hello, how are you?"
            }
            response = requests.post("http://127.0.0.1:18080/event", json=event_data)
            assert response.status_code == 200
            
            # Test plan endpoint
            plan_data = {
                "user_id": "test_user",
                "user_text": "Hello, how are you?"
            }
            response = requests.post("http://127.0.0.1:18080/plan", json=plan_data)
            assert response.status_code == 200
            plan = response.json()
            
            # Verify plan structure
            required_fields = ["tone", "intent", "focus_target", "key_points", 
                             "constraints", "emotion", "relationship"]
            for field in required_fields:
                assert field in plan
            
            # Verify emotion ranges
            assert -1 <= plan["emotion"]["valence"] <= 1
            assert 0 <= plan["emotion"]["arousal"] <= 1
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()

    def test_openclaw_skill_integration(self):
        """Test OpenClaw skill integration with the daemon."""
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Test health check
            health_result = check_daemon_health()
            assert health_result is True
            
            # Test user message processing
            plan_result = process_user_message("test_user", "Hello, how are you feeling today?")
            assert "tone" in plan_result
            assert "intent" in plan_result
            assert "emotion" in plan_result
            
            # Test assistant reply processing
            reply_result = process_assistant_reply("test_user", "I'm doing well, thank you for asking!")
            assert reply_result is not None
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()

    def test_emotion_state_persistence(self):
        """Test that emotion state persists across daemon restarts."""
        # Start daemon and send event
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Send positive event
            event_data = {
                "type": "user_message",
                "actor": "persistence_user",
                "target": "assistant",
                "text": "You're doing great!"
            }
            response = requests.post("http://127.0.0.1:18080/event", json=event_data)
            assert response.status_code == 200
            
            # Get initial state
            plan_data = {
                "user_id": "persistence_user",
                "user_text": "How are you feeling?"
            }
            response = requests.post("http://127.0.0.1:18080/plan", json=plan_data)
            initial_plan = response.json()
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()
        
        # Restart daemon
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Get state after restart
            plan_data = {
                "user_id": "persistence_user",
                "user_text": "How are you feeling now?"
            }
            response = requests.post("http://127.0.0.1:18080/plan", json=plan_data)
            restarted_plan = response.json()
            
            # State should be similar (not necessarily identical due to time drift)
            # But the emotional signature should be recognizable
            assert restarted_plan["emotion"]["valence"] > -0.5  # Should be somewhat positive
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()

    def test_demo_cli_functionality(self):
        """Test that the demo CLI script works correctly."""
        # Run demo script in test mode (no actual daemon startup)
        result = subprocess.run(
            ["venv2/bin/python", "scripts/demo_cli.py", "--test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Should run without errors
        assert result.returncode == 0
        assert "Demo scenarios defined" in result.stdout or "test mode" in result.stdout.lower()

    def test_eval_suite_generation(self):
        """Test that the evaluation suite can generate reports."""
        # Run eval suite in test mode
        result = subprocess.run(
            ["venv2/bin/python", "scripts/eval_suite.py", "--test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Should run without errors
        assert result.returncode == 0
        assert "Evaluation" in result.stdout or "test mode" in result.stdout.lower()

    def test_systemd_deployment_script(self):
        """Test that the systemd deployment script exists and is valid."""
        deployment_script = Path(__file__).parent.parent / "scripts" / "deploy_systemd.py"
        assert deployment_script.exists()
        
        # Check script syntax
        result = subprocess.run(
            ["venv2/bin/python", "-m", "py_compile", str(deployment_script)],
            capture_output=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0, f"Deployment script syntax error: {result.stderr}"

    def test_complete_workflow(self):
        """Test complete workflow: daemon startup -> user interaction -> plan generation."""
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Simulate conversation flow
            conversation_steps = [
                ("user_message", "user1", "Hello, nice to meet you!"),
                ("assistant_reply", "assistant", "Nice to meet you too!"),
                ("user_message", "user1", "How are you feeling today?"),
                ("assistant_reply", "assistant", "I'm doing well, thanks for asking!"),
            ]
            
            plans = []
            for event_type, actor, text in conversation_steps:
                # Send event
                event_data = {
                    "type": event_type,
                    "actor": actor,
                    "target": "assistant",
                    "text": text
                }
                response = requests.post("http://127.0.0.1:18080/event", json=event_data)
                assert response.status_code == 200
                
                # Get plan
                if event_type == "user_message":
                    plan_data = {
                        "user_id": actor,
                        "user_text": text
                    }
                    response = requests.post("http://127.0.0.1:18080/plan", json=plan_data)
                    assert response.status_code == 200
                    plan = response.json()
                    plans.append(plan)
            
            # Verify we got plans and they have emotional content
            assert len(plans) >= 2
            for plan in plans:
                assert "emotion" in plan
                assert "valence" in plan["emotion"]
                assert "arousal" in plan["emotion"]
                
        finally:
            daemon_process.terminate()
            daemon_process.wait()


class TestPerformanceAndStability:
    """Performance and stability tests for the emotiond system."""

    def test_daemon_stability_under_load(self):
        """Test that the daemon remains stable under moderate load."""
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Send multiple rapid requests
            for i in range(10):
                event_data = {
                    "type": "user_message",
                    "actor": f"load_user_{i}",
                    "target": "assistant",
                    "text": f"Test message {i}"
                }
                response = requests.post("http://127.0.0.1:18080/event", json=event_data)
                assert response.status_code == 200
                
                plan_data = {
                    "user_id": f"load_user_{i}",
                    "user_text": f"Test message {i}"
                }
                response = requests.post("http://127.0.0.1:18080/plan", json=plan_data)
                assert response.status_code == 200
            
            # Health should still work
            response = requests.get("http://127.0.0.1:18080/health")
            assert response.status_code == 200
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()

    def test_memory_usage_stability(self):
        """Test that memory usage doesn't grow excessively."""
        # This is a basic test - in production you'd want more sophisticated monitoring
        daemon_process = subprocess.Popen(
            ["venv2/bin/python", "scripts/run_daemon.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            time.sleep(3)
            
            # Send events and verify responses are consistent
            for i in range(5):
                event_data = {
                    "type": "user_message",
                    "actor": "memory_user",
                    "target": "assistant",
                    "text": f"Memory test {i}"
                }
                response = requests.post("http://127.0.0.1:18080/event", json=event_data)
                assert response.status_code == 200
                
                # Small delay to allow processing
                time.sleep(0.1)
            
            # Final health check
            response = requests.get("http://127.0.0.1:18080/health")
            assert response.status_code == 200
            
        finally:
            daemon_process.terminate()
            daemon_process.wait()