"""
Configuration for emotiond
"""
import os
import logging

# Environment variables with defaults
DB_PATH = os.getenv("OPENEMOTION_DB_PATH", "./data/openemotion.db")
PORT = int(os.getenv("OPENEMOTION_PORT", "18080"))
HOST = os.getenv("OPENEMOTION_HOST", "127.0.0.1")
# Subjective time constant: subjective_dt = real_dt / (1 + k * arousal)
K_AROUSAL = float(os.getenv("OPENEMOTION_K_AROUSAL", "2.0"))


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