"""
Configuration for emotiond
"""
import os
import logging

# Environment variables with defaults
DB_PATH = os.getenv("EMOTIOND_DB_PATH", "./data/emotiond.db")
PORT = int(os.getenv("EMOTIOND_PORT", "18080"))
HOST = os.getenv("EMOTIOND_HOST", "127.0.0.1")
# Subjective time constant: subjective_dt = real_dt / (1 + k * arousal)
K_AROUSAL = float(os.getenv("EMOTIOND_K_AROUSAL", "2.0"))
# Core functionality disable flag for ablation baseline
DISABLE_CORE = bool(os.getenv("EMOTIOND_DISABLE_CORE", "").strip().lower() in ["1", "true", "yes", "on"])


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