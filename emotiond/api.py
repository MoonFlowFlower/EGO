"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI
import datetime
import asyncio
import traceback
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan, load_initial_state
from emotiond.daemon import daemon_manager
from emotiond.config import is_core_disabled

app = FastAPI(title="OpenEmotion Daemon", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Initialize database and load state on startup"""
    await daemon_manager.start()
    await load_initial_state()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "ok": True, 
        "ts": datetime.datetime.now().isoformat(),
        "emotiond": {
            "version": "0.1.0",
            "status": "running",
            "core_enabled": not is_core_disabled()
        }
    }


@app.post("/event")
async def event(event: Event):
    """Ingest events and update state"""
    try:
        return await process_event(event)
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return await generate_plan(request)
