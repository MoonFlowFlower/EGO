"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI
import datetime
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan, load_initial_state
from emotiond.db import init_db

app = FastAPI(title="OpenEmotion Daemon", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Initialize database and load state on startup"""
    await init_db()
    await load_initial_state()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"ok": True, "ts": datetime.datetime.now().isoformat()}


@app.post("/event")
async def event(event: Event):
    """Ingest events and update state"""
    return process_event(event)


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return generate_plan(request)