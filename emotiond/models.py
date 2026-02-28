"""
Pydantic models for request/response
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class Event(BaseModel):
    """Event model for POST /event"""
    type: str  # user_message|assistant_reply|world_event
    actor: str
    target: str
    text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class PlanRequest(BaseModel):
    """Request model for POST /plan"""
    user_id: str
    user_text: str
    focus_target: Optional[str] = None  # Optional, defaults to user_id


class PlanResponse(BaseModel):
    """Response model for POST /plan"""
    tone: str  # soft|warm|guarded|cold
    intent: str  # repair|distance|seek|set_boundary|retaliate
    focus_target: str  # user|A|B|C or any dynamic target
    key_points: List[str]
    constraints: List[str]
    emotion: Dict[str, float]  # valence, arousal, anger, sadness, anxiety, joy, loneliness
    relationship: Dict[str, float]  # bond, grudge, trust, repair_bank
    relationships: Optional[Dict[str, Dict[str, float]]] = None  # All relationships if EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS=1
    regulation_budget: Optional[float] = None  # MVP-2: cost mechanism state
