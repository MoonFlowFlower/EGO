"""
Pytest configuration for OpenEmotion tests
"""
import os
import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
from emotiond.db import init_db
from emotiond.config import DB_PATH


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def isolated_db():
    """Setup isolated database for tests with proper cleanup"""
    # Create temp directory for this test
    test_data_dir = tempfile.mkdtemp(prefix="emotiond_test_")
    
    # Override DB_PATH for this test
    original_db_path = os.environ.get("EMOTIOND_DB_PATH")
    os.environ["EMOTIOND_DB_PATH"] = os.path.join(test_data_dir, "test_emotiond.db")
    
    # Reimport config to pick up new DB path
    import importlib
    from emotiond import config, db, core
    importlib.reload(config)
    importlib.reload(db)
    
    # Reset global state
    core.emotion_state.valence = 0.0
    core.emotion_state.arousal = 0.3
    core.emotion_state.subjective_time = 0
    core.emotion_state.prediction_error = 0.0
    core.relationship_manager.relationships = {}
    
    # Initialize database
    await db.init_db()
    
    yield
    
    # Cleanup
    if original_db_path:
        os.environ["EMOTIOND_DB_PATH"] = original_db_path
    else:
        os.environ.pop("EMOTIOND_DB_PATH", None)
    
    # Remove temp directory
    shutil.rmtree(test_data_dir, ignore_errors=True)


@pytest.fixture
def test_db_path():
    """Provide test database path"""
    return "data/test_emotiond.db"
