"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI
import datetime
import asyncio
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan, load_initial_state
from emotiond.daemon import daemon_manager

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
            "core_enabled": True
        }
    }


@app.post("/event")
async def event(event: Event):
    """Ingest events and update state"""
    return await process_event(event)


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return await generate_plan(request)