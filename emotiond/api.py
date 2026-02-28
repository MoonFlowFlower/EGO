"""
FastAPI application for emotiond daemon
"""
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
import datetime
import asyncio
import traceback
from typing import Optional
from emotiond.models import Event, PlanRequest, PlanResponse
from emotiond.core import (
    process_event, generate_plan, load_initial_state,
    select_action_with_explanation,
    select_action_with_explanation_v31,
    resolve_target_id
)
from emotiond.daemon import daemon_manager
from emotiond.config import is_core_disabled
from emotiond.security import (
    resolve_server_source,
    validate_event_for_source
)
from emotiond.db import add_event, get_last_decision, get_latest_decision_for_target

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
async def event(
    event: Event, 
    request: Request,
    include_explanation: bool = Query(False, description="MVP-3 C2: Include decision explanation in response")
):
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
        
        result = await process_event(event)
        
        # MVP-3 C2: Optionally include explanation in response
        if include_explanation and result.get("status") == "processed":
            target = event.target if event.target else event.actor
            last_decision = await get_last_decision()
            if last_decision:
                result["last_decision"] = last_decision
        
        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.post("/plan")
async def plan(request: PlanRequest):
    """Generate response plan JSON"""
    result = await generate_plan(request)
    
    # MVP-3 C2: Add last_decision to /plan response
    last_decision = await get_last_decision()
    if last_decision:
        result_dict = result.model_dump()
        result_dict["last_decision"] = last_decision
        return result_dict
    
    return result


# MVP-3 C2: New /decision endpoint
@app.get("/decision")
async def get_decision(target_id: Optional[str] = Query(None, description="Filter by target_id")):
    """
    Get the most recent decision with explanation.
    
    If target_id is provided, returns the latest decision for that target.
    Otherwise returns the global latest decision.
    """
    if target_id:
        decision = await get_latest_decision_for_target(target_id)
    else:
        decision = await get_last_decision()
    
    if decision is None:
        return {"status": "no_decision", "decision": None}
    
    return {
        "status": "ok",
        "decision_id": decision["id"],
        "action": decision["action"],
        "explanation": decision.get("explanation"),
        "target_id": decision.get("target_id"),
        "created_at": decision.get("created_at")
    }


@app.post("/decision")
async def make_decision(
    request: PlanRequest,
    test_mode: bool = Query(False, description="Use deterministic action selection")
):
    """MVP-3 C2: Select an action for a target and store the decision"""
    target = request.focus_target if request.focus_target else request.user_id
    
    result = await select_action_with_explanation(target, test_mode=test_mode)
    
    return {
        "status": "ok",
        "action": result["action"],
        "explanation": result["explanation"],
        "decision_id": result["decision_id"],
        "target": target
    }

# MVP-3.1: Target-specific decision endpoint
@app.post("/decision/target")
async def make_decision_target(
    request: PlanRequest,
    target_id: Optional[str] = Query(None, description="MVP-3.1: Target ID for prediction lookup (defaults to client_source or 'default')"),
    test_mode: bool = Query(False, description="Use deterministic action selection")
):
    """MVP-3.1: Select an action using target-specific predictions with partial pooling."""
    target = request.focus_target if request.focus_target else request.user_id
    
    # If target_id not provided, try to derive from request context
    # In a real scenario, this would come from event meta
    if target_id is None:
        target_id = target  # Default to same as target
    
    result = await select_action_with_explanation_v31(target, target_id, test_mode=test_mode)
    
    return {
        "status": "ok",
        "action": result["action"],
        "explanation": result["explanation"],
        "decision_id": result["decision_id"],
        "target": target,
        "target_id": result["target_id"]
    }


@app.get("/decision/target/{target_id}")
async def get_decision_by_target(
    target_id: str,
    test_mode: bool = Query(False, description="Use deterministic action selection")
):
    """MVP-3.1: Get or create a decision for a specific target_id."""
    # Use target_id as both target and target_id for simplicity
    result = await select_action_with_explanation_v31(target_id, target_id, test_mode=test_mode)
    
    return {
        "status": "ok",
        "action": result["action"],
        "explanation": result["explanation"],
        "decision_id": result["decision_id"],
        "target": target_id,
        "target_id": result["target_id"]
    }
