"""
Main entry point for emotiond daemon
"""
from emotiond.config import HOST, PORT

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "emotiond.api:app",
        host=HOST,
        port=PORT,
        log_level="info"
    )
