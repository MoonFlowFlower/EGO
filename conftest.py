"""
pytest configuration for OpenEmotion tests with mock emotiond service.
"""

import pytest
import subprocess
import time
import sys
import os

# Add the fixtures directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests', 'fixtures'))

@pytest.fixture(scope='session')
def mock_emotiond():
    """Start mock emotiond service for integration tests."""
    # Import the mock server
    import mock_emotiond
    
    # Start the server
    httpd, server_thread = mock_emotiond.start_mock_server()
    
    # Give it time to start
    time.sleep(2)
    
    # Set environment variables for tests
    os.environ['EMOTIOND_URL'] = 'http://127.0.0.1:18080'
    os.environ['EMOTIOND_OPENCLAW_TOKEN'] = '93e0a7a76de9e871b5c3ce658ce2c426b2ab69148b7b88b73100db0356ffcc72'
    
    yield {
        'url': 'http://127.0.0.1:18080',
        'token': '93e0a7a76de9e871b5c3ce658ce2c426b2ab69148b7b88b73100db0356ffcc72'
    }
    
    # Cleanup
    httpd.shutdown()
    server_thread.join(timeout=5)

@pytest.fixture(scope='session')
def emotiond_available(mock_emotiond):
    """Override the original emotiond_available fixture to always return True."""
    return True