"""
Security module for MVP-2.1.1: Source resolution + meta sanitization

Provides:
- Server-side source resolution from auth tokens
- Meta key validation and sanitization
- Time_passed clamping for user sources
"""
import os
from typing import Dict, Any, Optional, Tuple


# Environment variable names for tokens
SYSTEM_TOKEN_ENV = "EMOTIOND_SYSTEM_TOKEN"
OPENCLAW_TOKEN_ENV = "EMOTIOND_OPENCLAW_TOKEN"

# User-allowed subtypes for world_event
USER_ALLOWED_SUBTYPES = {"care", "rejection", "ignored", "apology", "time_passed"}

# User-allowed meta keys for world_event WITH subtype (source is server-controlled)
USER_ALLOWED_META_KEYS = {"subtype", "seconds", "client_source", "request_id"}

# Time_passed clamp bounds for user sources
TIME_PASSED_MIN_SECONDS = 1
TIME_PASSED_MAX_SECONDS = 300


def get_system_token() -> Optional[str]:
    """Get the system token from environment."""
    return os.environ.get(SYSTEM_TOKEN_ENV)


def get_openclaw_token() -> Optional[str]:
    """Get the openclaw token from environment."""
    return os.environ.get(OPENCLAW_TOKEN_ENV)


def resolve_server_source(authorization_header: Optional[str], x_token_header: Optional[str]) -> str:
    """
    Resolve the server-determined source from auth headers.
    
    Priority:
    1. Authorization: Bearer <token>
    2. X-Emotiond-Token: <token>
    
    Returns:
        "system" if token matches system token
        "openclaw" if token matches openclaw token
        "user" otherwise (default)
    """
    token = None
    
    # Try Authorization header first
    if authorization_header:
        if authorization_header.lower().startswith("bearer "):
            token = authorization_header[7:].strip()
        else:
            token = authorization_header.strip()
    
    # Fall back to X-Emotiond-Token
    if not token and x_token_header:
        token = x_token_header.strip()
    
    if not token:
        return "user"
    
    # Check against configured tokens
    system_token = get_system_token()
    openclaw_token = get_openclaw_token()
    
    if system_token and token == system_token:
        return "system"
    
    if openclaw_token and token == openclaw_token:
        return "openclaw"
    
    return "user"


def sanitize_meta_for_user(
    meta: Optional[Dict[str, Any]], 
    event_type: str
) -> Tuple[Dict[str, Any], Optional[str], Optional[Dict[str, Any]]]:
    """
    Sanitize meta dict for user source.
    
    Args:
        meta: The meta dict from the event
        event_type: The event type (e.g., "world_event")
    
    Returns:
        Tuple of (sanitized_meta, deny_reason, audit_info)
        - sanitized_meta: cleaned meta dict
        - deny_reason: None if allowed, error string if denied
        - audit_info: additional info for audit log
    """
    if meta is None:
        meta = {}
    
    if event_type != "world_event":
        # Non-world_event types: pass through
        result = dict(meta)
        return result, None, None
    
    # For world_event, check subtype
    subtype = meta.get("subtype")
    
    # If no subtype, allow all meta keys (backward compatibility with generic world_events)
    # These are informational events without emotional dynamics
    if not subtype:
        result = dict(meta)
        return result, None, None
    
    # Check if subtype is allowed for users (restricted subtypes)
    if subtype in {"betrayal", "repair_success"}:
        return (
            meta,
            f"user source not allowed for {subtype}",
            {
                "denied_subtype": subtype,
                "allowed_subtypes": sorted(USER_ALLOWED_SUBTYPES),
                "reason": "high_impact_event_requires_elevated_source"
            }
        )
    
    # For other subtypes (care, rejection, ignored, apology, time_passed),
    # validate meta keys to prevent injection
    # Note: 'source' is added by API layer (server-controlled), so exclude it from check
    allowed_keys = USER_ALLOWED_META_KEYS
    meta_keys_to_check = set(meta.keys()) - {"source"}  # source is server-controlled
    unknown_keys = meta_keys_to_check - allowed_keys
    if unknown_keys:
        return (
            meta,
            f"unknown meta keys for user source with subtype: {sorted(unknown_keys)}",
            {
                "denied_keys": sorted(unknown_keys),
                "allowed_keys": sorted(allowed_keys),
                "reason": "unauthorized_meta_keys"
            }
        )
    
    # Validate time_passed seconds
    result = dict(meta)
    audit_info = None
    
    if subtype == "time_passed":
        seconds = meta.get("seconds", 60)
        
        # Validate minimum
        if seconds < TIME_PASSED_MIN_SECONDS:
            return (
                meta,
                f"time_passed seconds must be >= {TIME_PASSED_MIN_SECONDS}, got {seconds}",
                {
                    "denied_seconds": seconds,
                    "min_allowed": TIME_PASSED_MIN_SECONDS,
                    "reason": "invalid_time_passed_value"
                }
            )
        
        # Clamp maximum
        if seconds > TIME_PASSED_MAX_SECONDS:
            result["seconds"] = TIME_PASSED_MAX_SECONDS
            result["clamped_from"] = seconds
            audit_info = {
                "original_seconds": seconds,
                "clamped_to": TIME_PASSED_MAX_SECONDS,
                "reason": "time_passed_clamped"
            }
    
    return result, None, audit_info



def validate_time_passed_cumulative(
    seconds: float,
    current_window_sum: float,
    max_cumulative: float = 60.0
) -> Tuple[float, Dict[str, Any]]:
    """
    Validate time_passed against cumulative rate limit.
    
    Args:
        seconds: Requested seconds
        current_window_sum: Current sum of seconds in the window
        max_cumulative: Maximum allowed cumulative seconds (default 60)
    
    Returns:
        Tuple of (clamped_seconds, audit_info)
        - clamped_seconds: Allowed seconds (may be clamped)
        - audit_info: Details about clamping decision
    """
    remaining_budget = max_cumulative - current_window_sum
    
    if remaining_budget <= 0:
        # Budget exhausted, reject entirely
        return 0.0, {
            "window_sum": current_window_sum,
            "requested": seconds,
            "clamped_to": 0.0,
            "reason": "cumulative_budget_exhausted"
        }
    
    if seconds <= remaining_budget:
        # Within budget, allow fully
        return seconds, {
            "window_sum": current_window_sum,
            "requested": seconds,
            "clamped_to": seconds,
            "reason": "within_budget"
        }
    
    # Partial budget available, clamp to remaining
    return remaining_budget, {
        "window_sum": current_window_sum,
        "requested": seconds,
        "clamped_to": remaining_budget,
        "reason": "clamped_to_remaining_budget"
    }


def validate_event_for_source(
    event_type: str,
    meta: Optional[Dict[str, Any]],
    server_source: str
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate an event for a given server source.
    
    Args:
        event_type: The event type
        meta: The meta dict
        server_source: Server-resolved source ("system", "openclaw", "user")
    
    Returns:
        Tuple of (allowed, deny_reason, sanitized_meta)
        - allowed: True if event should be processed
        - deny_reason: None if allowed, error string if denied
        - sanitized_meta: sanitized meta (with clamping if applicable)
    """
    if meta is None:
        meta = {}
    
    # System and openclaw sources: no restrictions
    if server_source in {"system", "openclaw"}:
        return True, None, dict(meta)
    
    # User source: apply sanitization
    sanitized, deny_reason, audit_info = sanitize_meta_for_user(meta, event_type)
    
    if deny_reason:
        return False, deny_reason, meta  # Return original meta for audit
    
    return True, None, sanitized
