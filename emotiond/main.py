"""
Main entry point for emotiond daemon
"""
import uvicorn
from emotiond.config import HOST, PORT

if __name__ == "__main__":
    uvicorn.run(
        "emotiond.api:app",
        host=HOST,
        port=PORT,
        log_level="info"
    )