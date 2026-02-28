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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def isolated_db():
    """Setup isolated database for tests with proper cleanup"""
    from emotiond import config, db, core
    import importlib
    
    test_data_dir = tempfile.mkdtemp(prefix="emotiond_test_")
    original_db_path = os.environ.get("EMOTIOND_DB_PATH")
    os.environ["EMOTIOND_DB_PATH"] = os.path.join(test_data_dir, "test_emotiond.db")
    
    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(core)
    
    # Reset global state (including MVP-2 fields)
    core.emotion_state.valence = 0.0
    core.emotion_state.arousal = 0.3
    core.emotion_state.subjective_time = 0
    core.emotion_state.prediction_error = 0.0
    core.emotion_state.anger = 0.0
    core.emotion_state.sadness = 0.0
    core.emotion_state.anxiety = 0.0
    core.emotion_state.joy = 0.0
    core.emotion_state.loneliness = 0.0
    core.emotion_state.regulation_budget = 1.0
    core.relationship_manager.relationships = {}
    
    await db.init_db()
    
    yield
    
    if original_db_path:
        os.environ["EMOTIOND_DB_PATH"] = original_db_path
    else:
        os.environ.pop("EMOTIOND_DB_PATH", None)
    
    # Reset state after test
    core.emotion_state.valence = 0.0
    core.emotion_state.arousal = 0.3
    core.emotion_state.subjective_time = 0
    core.emotion_state.prediction_error = 0.0
    core.emotion_state.anger = 0.0
    core.emotion_state.sadness = 0.0
    core.emotion_state.anxiety = 0.0
    core.emotion_state.joy = 0.0
    core.emotion_state.loneliness = 0.0
    core.emotion_state.regulation_budget = 1.0
    core.relationship_manager.relationships = {}
    
    shutil.rmtree(test_data_dir, ignore_errors=True)


@pytest.fixture
def test_db_path():
    return "data/test_emotiond.db"


@pytest_asyncio.fixture(scope="function")
async def setup_db():
    """Alias for isolated_db - backward compatibility"""
    from emotiond import config, db, core
    import importlib
    
    test_data_dir = tempfile.mkdtemp(prefix="emotiond_test_")
    original_db_path = os.environ.get("EMOTIOND_DB_PATH")
    os.environ["EMOTIOND_DB_PATH"] = os.path.join(test_data_dir, "test_emotiond.db")
    
    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(core)
    
    core.emotion_state.valence = 0.0
    core.emotion_state.arousal = 0.3
    core.emotion_state.subjective_time = 0
    core.emotion_state.prediction_error = 0.0
    core.emotion_state.anger = 0.0
    core.emotion_state.sadness = 0.0
    core.emotion_state.anxiety = 0.0
    core.emotion_state.joy = 0.0
    core.emotion_state.loneliness = 0.0
    core.emotion_state.regulation_budget = 1.0
    core.relationship_manager.relationships = {}
    
    await db.init_db()
    
    yield
    
    if original_db_path:
        os.environ["EMOTIOND_DB_PATH"] = original_db_path
    else:
        os.environ.pop("EMOTIOND_DB_PATH", None)
    
    core.emotion_state.valence = 0.0
    core.emotion_state.arousal = 0.3
    core.emotion_state.subjective_time = 0
    core.emotion_state.prediction_error = 0.0
    core.emotion_state.anger = 0.0
    core.emotion_state.sadness = 0.0
    core.emotion_state.anxiety = 0.0
    core.emotion_state.joy = 0.0
    core.emotion_state.loneliness = 0.0
    core.emotion_state.regulation_budget = 1.0
    core.relationship_manager.relationships = {}
    
    shutil.rmtree(test_data_dir, ignore_errors=True)
