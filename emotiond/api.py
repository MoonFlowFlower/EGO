"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI
import datetime
import asyncio
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan, load_initial_state, homeostasis_loop, consolidation_loop
from emotiond.db import init_db

app = FastAPI(title="OpenEmotion Daemon", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Initialize database and load state on startup"""
    await init_db()
    await load_initial_state()
    
    # Start background loops
    asyncio.create_task(homeostasis_loop())
    asyncio.create_task(consolidation_loop())


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"ok": True, "ts": datetime.datetime.now().isoformat()}


@app.post("/event")
async def event(event: Event):
    """Ingest events and update state"""
    return await process_event(event)


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return await generate_plan(request)