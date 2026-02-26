"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan

app = FastAPI(title="OpenEmotion Daemon", version="0.1.0")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"ok": True, "ts": "..."}


@app.post("/event")
async def event(event: Event):
    """Ingest events and update state"""
    return process_event(event)


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return generate_plan(request)