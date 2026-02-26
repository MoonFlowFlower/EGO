"""
Configuration for emotiond
"""
import os

# Environment variables with defaults
DB_PATH = os.getenv("OPENEMOTION_DB_PATH", "./data/openemotion.db")
PORT = int(os.getenv("OPENEMOTION_PORT", "18080"))
HOST = os.getenv("OPENEMOTION_HOST", "127.0.0.1")