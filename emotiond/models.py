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


class PlanResponse(BaseModel):
    """Response model for POST /plan"""
    tone: str  # soft|warm|guarded|cold
    intent: str  # repair|distance|seek|set_boundary|retaliate
    focus_target: str  # user|A|B|C
    key_points: List[str]
    constraints: List[str]
    emotion: Dict[str, float]  # valence: -1.0..1.0, arousal: 0.0..1.0
    relationship: Dict[str, float]  # bond: 0.0..1.0, grudge: 0.0..1.0