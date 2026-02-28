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


class MoodResponse(BaseModel):
    """MVP-4 D1: Mood state in plan response"""
    valence: float = 0.0
    arousal: float = 0.3
    anxiety: float = 0.0
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    loneliness: float = 0.0
    uncertainty: float = 0.5


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
    last_decision: Optional[Dict[str, Any]] = None  # MVP-3 C2: most recent decision with explanation
    # MVP-4 D1: Hierarchical state system
    mood: Optional[MoodResponse] = None  # Global mood baseline
    uncertainty: Optional[float] = None  # Current affect uncertainty
    bond_uncertainty: Optional[float] = None  # Per-target bond uncertainty


class AppraisalResult(BaseModel):
    """MVP-4 D2: Structured appraisal result for an event"""
    goal_progress: float = 0.0  # [-1, 1]
    expectation_violation: float = 0.0  # [0, 1]
    controllability: float = 0.5  # [0, 1]
    social_threat: float = 0.0  # [0, 1]
    novelty: float = 0.0  # [0, 1]
    observed_delta: Dict[str, float] = {}  # safety, energy
    emotion_label: str = "neutral"
    intensity: float = 0.0  # [0, 1]
    reasoning: List[str] = []


class AppraisalRequest(BaseModel):
    """MVP-4 D2: Request for appraisal endpoint"""
    event: Event
    include_context: bool = False  # Whether to include affect/mood/bond in response


class AppraisalResponse(BaseModel):
    """MVP-4 D2: Response for appraisal endpoint"""
    appraisal: AppraisalResult
    affect: Optional[Dict[str, float]] = None
    mood: Optional[Dict[str, float]] = None
    bond: Optional[Dict[str, float]] = None
