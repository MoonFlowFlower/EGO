"""
Configuration for emotiond
"""
import os
import logging


def get_db_path():
    """Get database path from environment (dynamic, not cached)"""
    return os.getenv("EMOTIOND_DB_PATH", "./data/emotiond.db")


def is_core_disabled():
    """Check if core functionality is disabled (dynamic, checked at runtime)"""
    return os.getenv("EMOTIOND_DISABLE_CORE", "").strip().lower() in ["1", "true", "yes", "on"]


# Static values for backward compatibility
DB_PATH = get_db_path()
PORT = int(os.getenv("EMOTIOND_PORT", "18080"))
HOST = os.getenv("EMOTIOND_HOST", "127.0.0.1")
K_AROUSAL = float(os.getenv("EMOTIOND_K_AROUSAL", "2.0"))
DISABLE_CORE = is_core_disabled()

# MVP-3: Time passed cumulative rate limiting
TIME_PASSED_WINDOW_SECONDS = float(os.getenv("EMOTIOND_TIME_PASSED_WINDOW_SECONDS", "10.0"))
TIME_PASSED_MAX_CUMULATIVE = float(os.getenv("EMOTIOND_TIME_PASSED_MAX_CUMULATIVE", "60.0"))


def setup_logging():
    """Setup logging configuration for the daemon"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/emotiond.log')
        ]
    )
