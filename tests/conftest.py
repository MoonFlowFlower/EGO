"""
Pytest configuration for OpenEmotion tests
"""
import os
import pytest
import asyncio
from emotiond.db import init_db
from emotiond.config import DB_PATH


@pytest.fixture(scope="function")
async def setup_db():
    """Setup database for tests"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Initialize database
    await init_db()
    
    yield
    
    # Clean up after tests
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_path():
    """Provide test database path"""
    return "data/test_emotiond.db"