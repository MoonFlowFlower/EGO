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
    init_tokens,
    resolve_server_source,
    validate_event_for_source
)
from emotiond.db import add_event, get_last_decision, get_latest_decision_for_target

app = FastAPI(title="OpenEmotion Daemon", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Initialize tokens, database and load state on startup"""
    init_tokens()  # Initialize tokens on startup
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


# MVP-4 D2: Appraisal endpoint
from emotiond.models import AppraisalRequest, AppraisalResponse, AppraisalResult
from emotiond.appraisal import appraise_event, create_context_from_state
from emotiond.state import AffectState, MoodState, BondState
from emotiond.db import get_mood_state, get_relationships


@app.post("/appraisal")
async def get_appraisal(request: AppraisalRequest):
    """
    MVP-4 D2: Get appraisal for an event without modifying state.
    
    Returns the 5-dimensional appraisal vector and mapped emotion.
    """
    try:
        # Get current mood state
        mood_data = await get_mood_state()
        mood_state = MoodState(
            valence=mood_data["valence"],
            arousal=mood_data["arousal"],
            anxiety=mood_data["anxiety"],
            joy=mood_data["joy"],
            sadness=mood_data["sadness"],
            anger=mood_data["anger"],
            loneliness=mood_data["loneliness"],
            uncertainty=mood_data["uncertainty"]
        )
        
        # Get target relationship
        target = request.event.actor if request.event.type == "user_message" else request.event.target
        bond_state = None
        
        relationships = await get_relationships()
        for rel in relationships:
            if rel["target"] == target:
                bond_state = BondState(
                    target=target,
                    bond=rel["bond"],
                    trust=rel.get("trust", 0.0),
                    grudge=rel["grudge"],
                    repair_bank=rel.get("repair_bank", 0.0)
                )
                break
        
        # Create affect state from current emotion state
        from emotiond.core import emotion_state
        affect_state = AffectState(
            valence=emotion_state.valence,
            arousal=emotion_state.arousal,
            anger=emotion_state.anger,
            sadness=emotion_state.sadness,
            anxiety=emotion_state.anxiety,
            joy=emotion_state.joy,
            loneliness=emotion_state.loneliness,
            social_safety=emotion_state.social_safety,
            energy=emotion_state.energy,
            uncertainty=emotion_state.uncertainty
        )
        
        # Perform appraisal
        appraisal_result = appraise_event(
            event=request.event,
            affect=affect_state,
            mood=mood_state,
            bond=bond_state
        )
        
        # Build response
        response = AppraisalResponse(appraisal=appraisal_result)
        
        if request.include_context:
            response.affect = affect_state.to_dict()
            response.mood = mood_state.to_dict()
            if bond_state:
                response.bond = bond_state.to_dict()
        
        return response
        
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# MVP-6 D3: External Events Endpoint
import json
import hashlib
import time
from pathlib import Path
from emotiond.models import ExternalEventRequest, ExternalEventResponse
from emotiond.db import check_and_record_duplicate

# Load JSON schema for external events
_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "external_event.schema.json"
_EXTERNAL_EVENT_SCHEMA = None

def get_external_event_schema() -> dict:
    """Load and cache the external event JSON schema."""
    global _EXTERNAL_EVENT_SCHEMA
    if _EXTERNAL_EVENT_SCHEMA is None:
        try:
            with open(_SCHEMA_PATH, 'r') as f:
                _EXTERNAL_EVENT_SCHEMA = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Schema not available - will use Pydantic validation only
            _EXTERNAL_EVENT_SCHEMA = {}
    return _EXTERNAL_EVENT_SCHEMA


# Valid event types
VALID_EVENT_TYPES = {"user_message", "assistant_reply", "world_event"}

# Valid payload subtypes for world_event
VALID_WORLD_SUBTYPES = {"care", "apology", "ignored", "rejection", "betrayal", "neutral", "uncertain", "repair_success", "time_passed"}

# Valid payload fields per type
VALID_PAYLOAD_FIELDS = {
    "user_message": {"sentiment", "urgency", "entities"},
    "assistant_reply": {"tone", "intent", "confidence"},
    "world_event": {"subtype", "severity", "context"}
}

# Valid enum values
VALID_SENTIMENTS = {"positive", "negative", "neutral"}
VALID_TONES = {"soft", "warm", "guarded", "cold", "neutral"}
VALID_INTENTS = {"repair", "distance", "seek", "set_boundary", "retaliate", "inform"}


def validate_external_event_payload(event_type: str, payload: dict) -> tuple[bool, Optional[str]]:
    """
    Validate payload structure based on event type.
    Returns (is_valid, error_message).
    """
    if payload is None:
        if event_type == "world_event":
            return False, "world_event requires payload with subtype"
        return True, None
    
    if not isinstance(payload, dict):
        return False, f"payload must be an object, got {type(payload).__name__}"
    
    # Check for unknown fields
    allowed_fields = VALID_PAYLOAD_FIELDS.get(event_type, set())
    unknown_fields = set(payload.keys()) - allowed_fields
    if unknown_fields:
        return False, f"unknown payload fields for {event_type}: {sorted(unknown_fields)}"
    
    # Type-specific validation
    if event_type == "user_message":
        if "sentiment" in payload:
            if payload["sentiment"] not in VALID_SENTIMENTS:
                return False, f"invalid sentiment: {payload['sentiment']}"
        if "urgency" in payload:
            u = payload["urgency"]
            if not isinstance(u, (int, float)) or u < 0 or u > 1:
                return False, f"urgency must be in [0, 1], got {u}"
        if "entities" in payload:
            if not isinstance(payload["entities"], list):
                return False, "entities must be an array"
            if len(payload["entities"]) > 100:
                return False, "entities array exceeds max 100 items"
    
    elif event_type == "assistant_reply":
        if "tone" in payload:
            if payload["tone"] not in VALID_TONES:
                return False, f"invalid tone: {payload['tone']}"
        if "intent" in payload:
            if payload["intent"] not in VALID_INTENTS:
                return False, f"invalid intent: {payload['intent']}"
        if "confidence" in payload:
            c = payload["confidence"]
            if not isinstance(c, (int, float)) or c < 0 or c > 1:
                return False, f"confidence must be in [0, 1], got {c}"
    
    elif event_type == "world_event":
        if "subtype" not in payload:
            return False, "world_event payload requires subtype"
        if payload["subtype"] not in VALID_WORLD_SUBTYPES:
            return False, f"invalid subtype: {payload['subtype']}"
        if "severity" in payload:
            s = payload["severity"]
            if not isinstance(s, (int, float)) or s < 0 or s > 1:
                return False, f"severity must be in [0, 1], got {s}"
        if "context" in payload:
            if not isinstance(payload["context"], dict):
                return False, "context must be an object"
    
    return True, None


def sanitize_event_id(event_id: Optional[str]) -> Optional[str]:
    """Sanitize event_id for idempotency key."""
    if event_id is None:
        return None
    # Limit length and allow only safe characters
    event_id = event_id.strip()
    if len(event_id) > 128:
        event_id = event_id[:128]
    # Allow alphanumeric, underscore, hyphen
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', event_id):
        return None
    return event_id


@app.post("/events/external")
async def post_events_external(
    request: ExternalEventRequest,
    http_request: Request
):
    """
    MVP-6 D3: External events endpoint with strict validation.
    
    - Validates type enum and payload structure
    - Requires target_id for anti-forgery
    - Supports optional event_id for idempotency
    - Graceful degradation on timeout/errors
    - Minimal trace logging (no payload bloat)
    """
    start_time = time.time()
    degraded = False
    trace_info = {
        "endpoint": "/events/external",
        "client_host": http_request.client.host if http_request.client else "unknown",
    }
    
    try:
        # Validate event_id format if provided
        event_id = sanitize_event_id(request.event_id)
        if request.event_id and event_id is None:
            trace_info["validation_error"] = "invalid_event_id_format"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "rejected",
                    "event_id": request.event_id,
                    "message": "event_id must be alphanumeric with underscores/hyphens only, max 128 chars",
                    "degraded": False
                }
            )
        
        # Check idempotency if event_id provided
        if event_id:
            is_duplicate = await check_and_record_duplicate(event_id, window_hours=24)
            if is_duplicate:
                trace_info["idempotency"] = "duplicate_detected"
                return {
                    "status": "duplicate",
                    "event_id": event_id,
                    "message": "event with this event_id already processed within 24h",
                    "degraded": False
                }
        
        # Validate required fields
        if not request.type:
            trace_info["validation_error"] = "missing_type"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "rejected",
                    "event_id": event_id,
                    "message": "type is required",
                    "degraded": False
                }
            )
        
        if not request.target_id:
            trace_info["validation_error"] = "missing_target_id"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "rejected",
                    "event_id": event_id,
                    "message": "target_id is required for anti-forgery",
                    "degraded": False
                }
            )
        
        # Validate type enum
        if request.type not in VALID_EVENT_TYPES:
            trace_info["validation_error"] = f"invalid_type: {request.type}"
            return JSONResponse(
                status_code=400,
                content={
                    "status": "rejected",
                    "event_id": event_id,
                    "message": f"invalid type: {request.type}. Must be one of: {sorted(VALID_EVENT_TYPES)}",
                    "degraded": False
                }
            )
        
        # Validate payload structure
        payload_valid, payload_error = validate_external_event_payload(
            request.type,
            request.payload
        )
        if not payload_valid:
            trace_info["validation_error"] = payload_error
            return JSONResponse(
                status_code=400,
                content={
                    "status": "rejected",
                    "event_id": event_id,
                    "message": payload_error,
                    "degraded": False
                }
            )
        
        # Build internal event
        actor = request.actor if request.actor else request.target_id
        
        # Merge payload into meta for internal processing
        meta = dict(request.meta) if request.meta else {}
        if request.payload:
            # For world_event, extract subtype to meta
            if request.type == "world_event":
                meta["subtype"] = request.payload.get("subtype")
                if "severity" in request.payload:
                    meta["severity"] = request.payload["severity"]
                if "context" in request.payload:
                    meta["context"] = request.payload["context"]
            # For user_message, extract sentiment
            elif request.type == "user_message":
                if "sentiment" in request.payload:
                    meta["sentiment"] = request.payload["sentiment"]
                if "urgency" in request.payload:
                    meta["urgency"] = request.payload["urgency"]
            # For assistant_reply, extract tone/intent
            elif request.type == "assistant_reply":
                if "tone" in request.payload:
                    meta["tone"] = request.payload["tone"]
                if "intent" in request.payload:
                    meta["intent"] = request.payload["intent"]
        
        # Create internal Event
        internal_event = Event(
            type=request.type,
            actor=actor,
            target=request.target_id,
            text=request.text,
            meta=meta
        )
        
        # Process with timeout for graceful degradation
        try:
            # 5 second timeout for processing
            result = await asyncio.wait_for(
                process_event(internal_event),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            trace_info["degradation"] = "timeout"
            degraded = True
            # Accept event but mark as degraded
            result = {"status": "accepted_degraded", "reason": "processing_timeout"}
        
        # Generate internal event ID
        internal_event_id = hashlib.sha256(
            f"{request.type}:{request.target_id}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        trace_info["duration_ms"] = round((time.time() - start_time) * 1000, 2)
        trace_info["result_status"] = result.get("status", "unknown")
        
        response_status = "accepted"
        if degraded:
            response_status = "accepted"
        elif result.get("status") == "error":
            response_status = "error"
        
        return {
            "status": response_status,
            "event_id": event_id,
            "internal_event_id": internal_event_id,
            "message": result.get("message") if degraded else None,
            "degraded": degraded
        }
        
    except Exception as e:
        trace_info["error"] = str(e)
        trace_info["error_type"] = type(e).__name__
        # Log minimal trace (no payload)
        import logging
        logger = logging.getLogger("emotiond.api.external")
        logger.warning(f"External event error: {trace_info}")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "event_id": event_id if 'event_id' in locals() else None,
                "message": "internal error processing event",
                "degraded": True
            }
        )


@app.get("/memory/episodic/{target_id}")
async def get_episodic_memory(target_id: str, query: str = "", k: int = 3):
    k = max(1, min(10, int(k)))
    items = await episodic_memory_manager.retrieve(target_id=target_id, query=query, k=k)
    telemetry = episodic_memory_manager.get_telemetry()
    return {
        "status": "ok",
        "target_id": target_id,
        "query": query,
        "k": k,
        "items": items,
        "telemetry": telemetry,
    }
