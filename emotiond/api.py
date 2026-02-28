"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import datetime
import asyncio
import traceback
from emotiond.models import Event, PlanRequest
from emotiond.core import process_event, generate_plan, load_initial_state
from emotiond.daemon import daemon_manager
from emotiond.config import is_core_disabled
from emotiond.security import (
    resolve_server_source,
    validate_event_for_source
)
from emotiond.db import add_event

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
async def event(event: Event, request: Request):
    """Ingest events and update state"""
    try:
        # MVP-2.1.1: Server-side source resolution
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        x_token_header = request.headers.get("x-emotiond-token") or request.headers.get("X-Emotiond-Token")
        
        server_source = resolve_server_source(auth_header, x_token_header)
        
        # Prepare meta with server source
        meta = dict(event.meta) if event.meta else {}
        
        # Save client's source as client_source if provided
        if "source" in meta:
            meta["client_source"] = meta["source"]
        
        # Overwrite source with server-determined value
        meta["source"] = server_source
        
        # Validate and sanitize for user source
        allowed, deny_reason, sanitized_meta = validate_event_for_source(
            event.type,
            meta,
            server_source
        )
        
        if not allowed:
            # Audit: record denial
            audit_meta = {
                "original_type": event.type,
                "original_meta": meta,
                "server_source": server_source,
                "decision": "deny",
                "reason": deny_reason
            }
            await add_event({
                "type": "world_event_denied",
                "actor": event.actor,
                "target": event.target,
                "text": event.text,
                "meta": audit_meta
            })
            
            return JSONResponse(
                status_code=403,
                content={
                    "status": "denied",
                    "error": "forbidden_event",
                    "reason": deny_reason,
                    "server_source": server_source
                }
            )
        
        # Update event meta with sanitized version
        event.meta = sanitized_meta
        
        return await process_event(event)
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    return await generate_plan(request)
