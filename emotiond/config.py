"""
Configuration for emotiond
"""
import os

# Environment variables with defaults
DB_PATH = os.getenv("OPENEMOTION_DB_PATH", "./data/openemotion.db")
PORT = int(os.getenv("OPENEMOTION_PORT", "18080"))
HOST = os.getenv("OPENEMOTION_HOST", "127.0.0.1")
# Subjective time constant: subjective_dt = real_dt / (1 + k * arousal)
K_AROUSAL = float(os.getenv("OPENEMOTION_K_AROUSAL", "2.0"))