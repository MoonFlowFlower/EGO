"""
Core emotion processing and state management
"""
import os
import asyncio
import time
import math
from typing import Dict, Any, Optional, List
from emotiond.models import Event, PlanRequest, PlanResponse
from emotiond.db import (
    get_state, update_state, add_event, get_relationships, update_relationship,
    update_meaningful_contact_time,
    check_and_record_duplicate, update_dedupe_event_id,
    get_time_passed_window_sum, record_time_passed,
    get_db_path,
    load_predictions, save_predictions, update_prediction
)
from emotiond.config import (
    K_AROUSAL, is_core_disabled, TIME_PASSED_WINDOW_SECONDS, TIME_PASSED_MAX_CUMULATIVE,
    ACTION_SPACE, TEST_MODE, ACTION_PRIORS, OBSERVATION_MAP, get_observed_delta,
    ACTION_SCORE_WEIGHTS, SOFTMAX_TEMPERATURE, PREDICTION_LEARNING_RATE
)
from emotiond.security import validate_time_passed_cumulative
from emotiond.memory import memory_system, initialize_memory_system


class EmotionState:
    """Core emotional state management"""
    
    def __init__(self):
        self.valence = 0.0  # -1.0 to 1.0 (negative to positive)
        self.arousal = 0.3  # -1.0 to 1.0 (calm to excited)
        self.subjective_time = 0
        self.last_meaningful_contact = time.time()
        self.prediction_error = 0.0
        
        # 5-dimension emotion vector
        self.anger = 0.0
        self.sadness = 0.0
        self.anxiety = 0.0
        self.joy = 0.0
        self.loneliness = 0.0
        
        # Cost mechanism
        self.regulation_budget = 1.0
        
        # MVP-3 B1: Interoceptive states
        self.social_safety = 0.6  # [0, 1], default 0.6
        self.energy = 0.7  # [0, 1], default 0.7
        
        self.prediction_model = {
            "user_message": {"positive": 0.08, "negative": -0.12, "neutral": 0.0},
            "assistant_reply": {"positive": 0.0, "negative": 0.0, "neutral": -0.03},
            "world_event": {
                "positive": 0.15, "negative": -0.25, "neutral": 0.0,
                "care": 0.12, "rejection": -0.25, "betrayal": -0.35,
                "repair_success": 0.08, "time_passed": 0.0
            }
        }
    
    def update_from_event(self, event: Event) -> float:
        if is_core_disabled():
            return 0.0
        initial_valence = self.valence
        
        if event.type == "user_message" and event.text:
            self.last_meaningful_contact = time.time()
        
        if event.type == "user_message":
            if event.text and any(w in event.text.lower() for w in ["good", "great", "thanks", "love", "happy"]):
                self.valence = min(1.0, self.valence + 0.1)
                self.arousal = min(1.0, self.arousal + 0.05)
                self.joy = min(1.0, self.joy + 0.05)
                # MVP-3 B1: Positive user messages improve social safety
                self.social_safety = min(1.0, self.social_safety + 0.02)
            elif event.text and any(w in event.text.lower() for w in ["bad", "hate", "stupid", "wrong", "angry"]):
                self.valence = max(-1.0, self.valence - 0.1)
                self.arousal = min(1.0, self.arousal + 0.1)
                self.anger = min(1.0, self.anger + 0.05)
                # MVP-3 B1: Negative user messages reduce social safety
                self.social_safety = max(0.0, self.social_safety - 0.02)
        
        elif event.type == "assistant_reply":
            self.valence = self.valence * 0.95
            self.arousal = self.arousal * 0.9
        
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            
            # MVP-3 B1: Update interoceptive states based on event subtype
            if subtype == "care":
                self.valence = min(1.0, self.valence + 0.15)
                self.arousal = max(-1.0, self.arousal + 0.1)
                self.joy = min(1.0, self.joy + 0.15)
                self.anxiety = max(0.0, self.anxiety - 0.1)
                self.loneliness = max(0.0, self.loneliness - 0.1)
                self.social_safety = min(1.0, self.social_safety + 0.1)
                self.energy = min(1.0, self.energy + 0.05)
            elif subtype == "rejection":
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
                self.sadness = min(1.0, self.sadness + 0.2)
                self.loneliness = min(1.0, self.loneliness + 0.15)
                self.anger = min(1.0, self.anger + 0.1)
                self.social_safety = max(0.0, self.social_safety - 0.15)
                self.energy = max(0.0, self.energy - 0.08)
            elif subtype == "betrayal":
                self.valence = max(-1.0, self.valence - 0.3)
                self.arousal = min(1.0, self.arousal + 0.25)
                self.anger = min(1.0, self.anger + 0.25)
                self.sadness = min(1.0, self.sadness + 0.15)
                self.anxiety = min(1.0, self.anxiety + 0.15)
                self.joy = max(0.0, self.joy - 0.2)
                self.social_safety = max(0.0, self.social_safety - 0.25)
                self.energy = max(0.0, self.energy - 0.15)
            elif subtype == "repair_success":
                self.valence = min(1.0, self.valence + 0.1)
                self.arousal = self.arousal * 0.8
                self.joy = min(1.0, self.joy + 0.1)
                self.anxiety = max(0.0, self.anxiety - 0.1)
                self.social_safety = min(1.0, self.social_safety + 0.12)
                self.energy = min(1.0, self.energy + 0.05)
            elif subtype == "apology":
                self.social_safety = min(1.0, self.social_safety + 0.08)
                self.energy = min(1.0, self.energy + 0.02)
            elif subtype == "ignored":
                self.loneliness = min(1.0, self.loneliness + 0.1)
                self.sadness = min(1.0, self.sadness + 0.05)
                self.social_safety = max(0.0, self.social_safety - 0.05)
                self.energy = max(0.0, self.energy - 0.03)
            elif subtype == "time_passed":
                seconds = event.meta.get("seconds", 60) if event.meta else 60
                self.apply_homeostasis_drift(real_dt=seconds)
            elif event.meta and event.meta.get("positive", False):
                self.valence = min(1.0, self.valence + 0.2)
                self.social_safety = min(1.0, self.social_safety + 0.05)
            elif event.meta and event.meta.get("negative", False):
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
                self.social_safety = max(0.0, self.social_safety - 0.05)
        
        return self.valence - initial_valence
    
    def calculate_subjective_time_delta(self, real_dt: float) -> float:
        return real_dt / (1 + K_AROUSAL * self.arousal)

    def calculate_prediction_error(self, event: Event, actual_valence_change: float) -> float:
        if is_core_disabled():
            return 0.0
        if event.type == "user_message":
            if event.text and any(w in event.text.lower() for w in ["good", "great", "thanks", "love", "happy"]):
                expected = self.prediction_model["user_message"]["positive"]
            elif event.text and any(w in event.text.lower() for w in ["bad", "hate", "stupid", "wrong", "angry", "terrible", "awful", "horrible"]):
                expected = self.prediction_model["user_message"]["negative"]
            else:
                expected = self.prediction_model["user_message"]["neutral"]
        elif event.type == "assistant_reply":
            expected = self.prediction_model["assistant_reply"]["neutral"]
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            if subtype in ["care", "rejection", "betrayal", "repair_success", "time_passed"]:
                expected = self.prediction_model["world_event"].get(subtype, 0.0)
            elif event.meta and event.meta.get("positive", False):
                expected = self.prediction_model["world_event"]["positive"]
            elif event.meta and event.meta.get("negative", False):
                expected = self.prediction_model["world_event"]["negative"]
            else:
                expected = self.prediction_model["world_event"]["neutral"]
        else:
            expected = 0.0
        return abs(expected - actual_valence_change)
    
    def apply_homeostasis_drift(self, real_dt: float = 1.0) -> None:
        if is_core_disabled():
            return
        subjective_dt = self.calculate_subjective_time_delta(real_dt)
        valence_drift = 0.01 * subjective_dt
        if self.valence > 0:
            self.valence = max(0, self.valence - valence_drift)
        elif self.valence < 0:
            self.valence = min(0, self.valence + valence_drift)
        self.arousal = self.arousal * (0.99 ** subjective_dt)
        emotion_drift = 0.005 * subjective_dt
        self.anger = max(0.0, self.anger - emotion_drift)
        self.sadness = max(0.0, self.sadness - emotion_drift)
        self.anxiety = max(0.0, self.anxiety - emotion_drift)
        self.joy = max(0.0, self.joy - emotion_drift * 0.5)
        self.loneliness = max(0.0, self.loneliness - emotion_drift)
        self.regulation_budget = min(1.0, self.regulation_budget + 0.001 * subjective_dt)
        self.subjective_time += subjective_dt
        
        # MVP-3 B1: Energy recovery over time
        energy_recovery = 0.001 * real_dt  # 0.1% per second
        self.energy = min(1.0, self.energy + energy_recovery)
        
        time_since_contact = time.time() - self.last_meaningful_contact
        if time_since_contact > 3600:
            loneliness_factor = min(0.5, (time_since_contact - 3600) / 7200)
            self.valence = max(-1.0, self.valence - loneliness_factor * 0.01 * subjective_dt)
            self.loneliness = min(1.0, self.loneliness + loneliness_factor * 0.01 * subjective_dt)


class RelationshipManager:
    def __init__(self):
        self.relationships: Dict[str, Dict[str, float]] = {}
        self.last_actions: Dict[str, Optional[str]] = {}  # MVP-3 B2: Track last action per target
    
    def _ensure_relationship_fields(self, target: str) -> None:
        if target not in self.relationships:
            self.relationships[target] = {"bond": 0.0, "grudge": 0.0, "trust": 0.0, "repair_bank": 0.0}
        else:
            rel = self.relationships[target]
            if "trust" not in rel:
                rel["trust"] = 0.0
            if "repair_bank" not in rel:
                rel["repair_bank"] = 0.0
    
    def update_from_event(self, event: Event, emotion_state: Optional[EmotionState] = None) -> None:
        if is_core_disabled():
            return
        if event.type == "user_message":
            target = event.actor
        elif event.type == "assistant_reply":
            target = event.target
        else:
            target = event.actor
        self._ensure_relationship_fields(target)
        memory_impact = memory_system.get_memory_impact_on_relationship(target)
        
        if event.type == "user_message":
            if event.text and any(w in event.text.lower() for w in ["good", "great", "thanks", "love", "happy"]):
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.1 + memory_impact["bond_modifier"])
            elif event.text and any(w in event.text.lower() for w in ["bad", "hate", "stupid", "wrong", "angry", "terrible", "awful", "horrible"]):
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.1 + memory_impact["grudge_modifier"])
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            if subtype == "care":
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.15)
                self.relationships[target]["grudge"] = max(0.0, self.relationships[target]["grudge"] - 0.05)
            elif subtype == "rejection":
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.1)
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.1)
            elif subtype == "betrayal":
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.25)
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.2)
                self.relationships[target]["trust"] = max(0.0, self.relationships[target]["trust"] - 0.15)
            elif subtype == "apology":
                self.relationships[target]["repair_bank"] = min(1.0, self.relationships[target]["repair_bank"] + 0.02)
                self.relationships[target]["trust"] = min(1.0, self.relationships[target]["trust"] + 0.01)
            elif subtype == "repair_success":
                if emotion_state is not None:
                    current_trust = self.relationships[target]["trust"]
                    current_repair_bank = self.relationships[target]["repair_bank"]
                    max_reduction = min(current_trust, current_repair_bank, emotion_state.regulation_budget)
                    actual_reduction = max(0.05, min(max_reduction, 0.15))
                    self.relationships[target]["grudge"] = max(0.0, self.relationships[target]["grudge"] - actual_reduction)
                    emotion_state.regulation_budget = max(0.0, emotion_state.regulation_budget - actual_reduction)
                    self.relationships[target]["repair_bank"] = min(1.0, self.relationships[target]["repair_bank"] + 0.1)
                    self.relationships[target]["trust"] = min(1.0, self.relationships[target]["trust"] + 0.05)
                else:
                    self.relationships[target]["grudge"] = max(0.0, self.relationships[target]["grudge"] - 0.1)
                    self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.05)
            elif subtype == "ignored":
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.01)
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.01)
            elif event.meta and event.meta.get("betrayal", False):
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.3)
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.2)
    
    def apply_consolidation_drift(self) -> None:
        if is_core_disabled():
            return
        for target in list(self.relationships.keys()):
            self._ensure_relationship_fields(target)
            self.relationships[target]["bond"] *= 0.995
            self.relationships[target]["grudge"] *= 0.998
            self.relationships[target]["repair_bank"] *= 0.99
            if self.relationships[target]["trust"] > 0.5:
                self.relationships[target]["trust"] -= 0.001
            elif self.relationships[target]["trust"] < 0.5:
                self.relationships[target]["trust"] += 0.001
    
    def set_last_action(self, target: str, action: str) -> None:
        """MVP-3 B2: Set the last action taken toward a target."""
        self.last_actions[target] = action
    
    def get_last_action(self, target: str) -> Optional[str]:
        """MVP-3 B2: Get the last action taken toward a target."""
        return self.last_actions.get(target)


# MVP-3 B3+B5: Global prediction store
_predictions: Dict[str, Dict[str, float]] = {}


emotion_state = EmotionState()
relationship_manager = RelationshipManager()


async def load_initial_state():
    global emotion_state, relationship_manager, _predictions
    db_state = await get_state()
    emotion_state.valence = db_state["valence"]
    emotion_state.arousal = db_state["arousal"]
    emotion_state.subjective_time = db_state["subjective_time"]
    emotion_state.last_meaningful_contact = db_state["last_meaningful_contact"]
    emotion_state.prediction_error = db_state["prediction_error"]
    emotion_state.regulation_budget = db_state.get("regulation_budget", 1.0)
    # MVP-3 B1: Load interoceptive states
    emotion_state.social_safety = db_state.get("social_safety", 0.6)
    emotion_state.energy = db_state.get("energy", 0.7)
    db_relationships = await get_relationships()
    for rel in db_relationships:
        relationship_manager.relationships[rel["target"]] = {
            "bond": rel["bond"],
            "grudge": rel["grudge"],
            "trust": rel.get("trust", 0.0),
            "repair_bank": rel.get("repair_bank", 0.0)
        }
        # MVP-3 B2: Load last action
        if rel.get("last_action"):
            relationship_manager.last_actions[rel["target"]] = rel["last_action"]
    # MVP-3 B3: Load predictions
    _predictions.update(await load_predictions())
    await initialize_memory_system()


async def process_event(event: Event) -> Dict[str, Any]:
    """Process an event after security validation (handled in api.py).
    
    MVP-2.1.1: Also validates source for direct calls (backward compatibility).
    MVP-3: Added request_id idempotency and time_passed cumulative rate limiting.
    """
    # === MVP-3: Request Idempotency Check ===
    request_id = None
    source = "user"
    
    if event.type == "world_event" and event.meta:
        request_id = event.meta.get("request_id")
        source = event.meta.get("source", "user")
    
    if request_id:
        dedupe_result = await check_and_record_duplicate(source, request_id)
        if dedupe_result["is_duplicate"]:
            # Audit: record duplicate rejection
            await add_event({
                "type": "world_event_duplicate",
                "actor": event.actor,
                "target": event.target,
                "text": event.text,
                "meta": {
                    "original_request_id": request_id,
                    "source": source,
                    "decision": "duplicate_ignored",
                    "reason": "request_id already processed",
                    "original_event_id": dedupe_result.get("event_id"),
                    "original_decision_id": dedupe_result.get("decision_id")
                }
            })
            return {
                "status": "duplicate_ignored",
                "request_id": request_id,
                "source": source,
                "original_event_id": dedupe_result.get("event_id"),
                "reason": "request_id already processed"
            }
    
    # === MVP-2.1.1 Auth Gate (for direct calls, api.py handles HTTP) ===
    if event.type == "world_event":
        subtype = event.meta.get("subtype") if event.meta else None
        
        # High-impact subtypes that require system/openclaw source
        restricted_subtypes = {"betrayal", "repair_success"}
        
        if subtype in restricted_subtypes and source == "user":
            # Audit: record denial
            await add_event({
                "type": "world_event_denied",
                "actor": event.actor,
                "target": event.target,
                "text": event.text,
                "meta": {
                    "original_subtype": subtype,
                    "source": source,
                    "decision": "deny",
                    "reason": f"user source not allowed for {subtype}",
                    "allowed_subtypes": ["care", "rejection", "ignored", "apology", "time_passed"]
                }
            })
            # Return structured error (not HTTPException, since api.py catches exceptions)
            return {
                "status": "denied",
                "error": "forbidden_event_type",
                "reason": f"user source not allowed for {subtype}",
                "allowed_subtypes": ["care", "rejection", "ignored", "apology", "time_passed"],
                "hint": "Use source=system or source=openclaw for high-impact events"
            }
    # === End Auth Gate ===
    
    # === MVP-3: Time Passed Cumulative Rate Limiting ===
    time_passed_audit = None
    if event.type == "world_event" and event.meta and event.meta.get("subtype") == "time_passed":
        requested_seconds = event.meta.get("seconds", 60)
        
        # Get current window sum for this source
        window_sum = await get_time_passed_window_sum(source, TIME_PASSED_WINDOW_SECONDS)
        
        # Validate against cumulative limit
        clamped_seconds, time_passed_audit = validate_time_passed_cumulative(
            requested_seconds,
            window_sum,
            TIME_PASSED_MAX_CUMULATIVE
        )
        
        # Update event meta with clamped value
        event.meta["seconds"] = clamped_seconds
        event.meta["time_passed_audit"] = time_passed_audit
        
        # Record for future cumulative checks (only if > 0)
        if clamped_seconds > 0:
            await record_time_passed(source, clamped_seconds)
    # === End Rate Limiting ===
    
    await add_event(event.model_dump())
    
    # Update dedupe record with event_id if request_id was provided
    if request_id:
        # Get the last inserted event id using the already imported module
        import aiosqlite
        async with aiosqlite.connect(get_db_path()) as db:
            cursor = await db.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            if row:
                await update_dedupe_event_id(source, request_id, row[0])
    
    if event.type == "user_message" and event.text:
        await update_meaningful_contact_time()
    actual_valence_change = emotion_state.update_from_event(event)
    prediction_error = emotion_state.calculate_prediction_error(event, actual_valence_change)
    emotion_state.prediction_error = prediction_error
    emotion_state.arousal = min(1.0, emotion_state.arousal + prediction_error * 0.5)
    memory_strength = memory_system.calculate_memory_strength(prediction_error, emotion_state.arousal)
    relationship_manager.update_from_event(event, emotion_state)
    await update_state(
        emotion_state.valence, 
        emotion_state.arousal, 
        emotion_state.subjective_time, 
        emotion_state.prediction_error, 
        emotion_state.regulation_budget,
        emotion_state.social_safety,
        emotion_state.energy
    )
    for target, rel_data in relationship_manager.relationships.items():
        await update_relationship(target, rel_data["bond"], rel_data["grudge"], rel_data.get("trust", 0.0), rel_data.get("repair_bank", 0.0))
    
    result = {
        "status": "processed",
        "valence": emotion_state.valence,
        "arousal": emotion_state.arousal,
        "prediction_error": emotion_state.prediction_error,
        "memory_strength": memory_strength,
        "regulation_budget": emotion_state.regulation_budget,
        "social_safety": emotion_state.social_safety,  # MVP-3 B1
        "energy": emotion_state.energy  # MVP-3 B1
    }
    
    # Include time_passed audit info in response if applicable
    if time_passed_audit:
        result["time_passed_audit"] = time_passed_audit
    
    return result


async def generate_plan(request: PlanRequest) -> PlanResponse:
    current_valence = emotion_state.valence
    current_arousal = emotion_state.arousal
    focus_target = request.focus_target if request.focus_target is not None else request.user_id
    target_relationship = relationship_manager.relationships.get(focus_target, {"bond": 0.0, "grudge": 0.0, "trust": 0.0, "repair_bank": 0.0})
    
    if current_valence > 0.3 and current_arousal < 0.5:
        tone = "warm"
    elif current_valence > 0:
        tone = "soft"
    elif current_valence < -0.3 and target_relationship["grudge"] > 0.5:
        tone = "cold"
    else:
        tone = "guarded"
    
    if current_valence < -0.2 and target_relationship["grudge"] > 0.7:
        intent = "retaliate"
    elif target_relationship["bond"] < 0.3 and target_relationship["grudge"] > 0.4:
        intent = "distance"
    elif current_valence < -0.1:
        intent = "repair"
    elif target_relationship["bond"] > 0.6:
        intent = "seek"
    else:
        intent = "set_boundary"
    
    key_points, constraints = [], []
    if intent == "repair":
        key_points, constraints = ["Acknowledge the emotional state", "Express willingness to improve"], ["Avoid defensiveness", "Focus on understanding"]
    elif intent == "seek":
        key_points, constraints = ["Express curiosity", "Ask engaging questions"], ["Be authentic", "Show genuine interest"]
    elif intent == "distance":
        key_points, constraints = ["Maintain professional boundaries", "Keep responses concise"], ["Avoid emotional entanglement", "Stay objective"]
    elif intent == "retaliate":
        key_points, constraints = ["Assert boundaries clearly", "Address the issue directly"], ["Avoid escalation", "Maintain professionalism"]
    else:
        key_points, constraints = ["Establish clear expectations", "Communicate needs"], ["Be firm but respectful", "Avoid ambiguity"]
    
    relationship_dict = {"bond": target_relationship["bond"], "grudge": target_relationship["grudge"], "trust": target_relationship.get("trust", 0.0), "repair_bank": target_relationship.get("repair_bank", 0.0)}
    
    include_all = os.environ.get("EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS", "0") == "1"
    all_relationships = None
    if include_all:
        all_relationships = {t: {"bond": r["bond"], "grudge": r["grudge"], "trust": r.get("trust", 0.0), "repair_bank": r.get("repair_bank", 0.0)} for t, r in relationship_manager.relationships.items()}
    
    emotion_dict = {"valence": current_valence, "arousal": current_arousal, "anger": emotion_state.anger, "sadness": emotion_state.sadness, "anxiety": emotion_state.anxiety, "joy": emotion_state.joy, "loneliness": emotion_state.loneliness}
    
    return PlanResponse(tone=tone, intent=intent, focus_target=focus_target, key_points=key_points, constraints=constraints, emotion=emotion_dict, relationship=relationship_dict, relationships=all_relationships, regulation_budget=emotion_state.regulation_budget)


async def homeostasis_loop():
    last_time = time.time()
    while True:
        current_time = time.time()
        real_dt = current_time - last_time
        last_time = current_time
        emotion_state.apply_homeostasis_drift(real_dt)
        await update_state(
            emotion_state.valence, 
            emotion_state.arousal, 
            emotion_state.subjective_time, 
            emotion_state.prediction_error, 
            emotion_state.regulation_budget,
            emotion_state.social_safety,
            emotion_state.energy
        )
        await asyncio.sleep(1)


async def consolidation_loop():
    while True:
        relationship_manager.apply_consolidation_drift()
        await memory_system.summarize_memories()
        for target, rel_data in relationship_manager.relationships.items():
            await update_relationship(target, rel_data["bond"], rel_data["grudge"], rel_data.get("trust", 0.0), rel_data.get("repair_bank", 0.0))
        await asyncio.sleep(30)


# MVP-3 B6: Action Selection Functions

def score_action(
    action: str,
    state: EmotionState,
    relationship: Dict[str, float],
    predictions: Dict[str, Dict[str, float]]
) -> float:
    """
    MVP-3 B6: Score an action based on relationship, prediction, and uncertainty.
    
    Args:
        action: The action to score
        state: Current emotional state
        relationship: Relationship dict with bond, grudge, trust, repair_bank
        predictions: Prediction dict for this action
    
    Returns:
        Float score for the action
    """
    w = ACTION_SCORE_WEIGHTS
    
    # Relationship benefit
    rel_score = (
        w["bond"] * relationship.get("bond", 0.0) +
        w["grudge"] * relationship.get("grudge", 0.0) +
        w["trust"] * relationship.get("trust", 0.0)
    )
    
    # Predicted change
    pred_safety = predictions.get("social_safety_delta", 0.0)
    pred_energy = predictions.get("energy_delta", 0.0)
    pred_score = w["safety"] * pred_safety + w["energy"] * pred_energy
    
    # Uncertainty penalty
    prediction_count = predictions.get("prediction_count", 0)
    prediction_error_sum = predictions.get("prediction_error_sum", 0.0)
    uncertainty = prediction_error_sum / prediction_count if prediction_count > 0 else 0.0
    uncertainty_penalty = -w["uncertainty"] * abs(uncertainty)
    
    return rel_score + pred_score + uncertainty_penalty


def select_action(
    state: EmotionState,
    target: str,
    test_mode: bool = False
) -> str:
    """
    MVP-3 B6: Select an action for a target.
    
    Args:
        state: Current emotional state
        target: Target identifier
        test_mode: If True, use argmax; if False, use softmax
    
    Returns:
        Selected action string
    """
    global _predictions
    
    relationship = relationship_manager.relationships.get(target, {"bond": 0.0, "grudge": 0.0, "trust": 0.0, "repair_bank": 0.0})
    
    # Score all actions
    scores = {}
    for action in ACTION_SPACE:
        pred = _predictions.get(action, {
            "social_safety_delta": 0.0,
            "energy_delta": 0.0,
            "prediction_error_sum": 0.0,
            "prediction_count": 0
        })
        scores[action] = score_action(action, state, relationship, pred)
    
    if test_mode or TEST_MODE:
        # Deterministic: argmax
        best_action = max(scores.keys(), key=lambda a: scores[a])
    else:
        # Stochastic: softmax
        temp = SOFTMAX_TEMPERATURE
        max_score = max(scores.values())
        exp_scores = {a: math.exp((s - max_score) / temp) for a, s in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {a: e / sum_exp for a, e in exp_scores.items()}
        
        # Sample from distribution
        import random
        r = random.random()
        cumsum = 0.0
        best_action = ACTION_SPACE[0]
        for a, p in probs.items():
            cumsum += p
            if r <= cumsum:
                best_action = a
                break
    
    return best_action


async def get_action_scores(target: str) -> Dict[str, Any]:
    """
    Get action scores for a target (useful for debugging/explanation).
    
    Returns:
        dict with scores and selected action
    """
    global _predictions
    
    relationship = relationship_manager.relationships.get(target, {"bond": 0.0, "grudge": 0.0, "trust": 0.0, "repair_bank": 0.0})
    
    scores = {}
    for action in ACTION_SPACE:
        pred = _predictions.get(action, {
            "social_safety_delta": 0.0,
            "energy_delta": 0.0,
            "prediction_error_sum": 0.0,
            "prediction_count": 0
        })
        scores[action] = score_action(action, emotion_state, relationship, pred)
    
    selected = select_action(emotion_state, target)
    
    return {
        "target": target,
        "scores": scores,
        "selected": selected,
        "relationship": relationship,
        "interoception": {
            "social_safety": emotion_state.social_safety,
            "energy": emotion_state.energy
        }
    }


# MVP-3 C1: Structured Explanation Generation
async def generate_explanation(
    target: str,
    selected_action: Optional[str] = None,
    test_mode: bool = False
) -> Dict[str, Any]:
    """
    MVP-3 C1: Generate a structured explanation for action selection.
    
    Args:
        target: Target identifier
        selected_action: Pre-selected action (if None, will select one)
        test_mode: If True, use deterministic selection
    
    Returns:
        dict with emotion, interoception, relationships, candidates, selected, selection_reasons
    """
    global _predictions
    
    # Get current state
    state = emotion_state
    
    # Build emotion section - top 2 emotions + all 5D
    emotion_values = {
        "anger": state.anger,
        "sadness": state.sadness,
        "anxiety": state.anxiety,
        "joy": state.joy,
        "loneliness": state.loneliness
    }
    
    # Sort by value descending, get top 2
    sorted_emotions = sorted(emotion_values.items(), key=lambda x: x[1], reverse=True)
    top2 = [(name, value) for name, value in sorted_emotions[:2] if value > 0.0]
    
    emotion_section = {
        "top2": top2,
        "all": emotion_values
    }
    
    # Build interoception section
    interoception_section = {
        "social_safety": state.social_safety,
        "energy": state.energy
    }
    
    # Build relationships section for target
    relationship = relationship_manager.relationships.get(target, {"bond": 0.0, "grudge": 0.0, "trust": 0.0, "repair_bank": 0.0})
    relationships_section = {
        "bond": relationship.get("bond", 0.0),
        "grudge": relationship.get("grudge", 0.0),
        "trust": relationship.get("trust", 0.0),
        "repair_bank": relationship.get("repair_bank", 0.0)
    }
    
    # Build candidates section - score all actions
    scores = {}
    predicted_deltas = {}
    for action in ACTION_SPACE:
        pred = _predictions.get(action, {
            "social_safety_delta": 0.0,
            "energy_delta": 0.0,
            "prediction_error_sum": 0.0,
            "prediction_count": 0
        })
        scores[action] = score_action(action, state, relationship, pred)
        predicted_deltas[action] = {
            "safety": pred.get("social_safety_delta", 0.0),
            "energy": pred.get("energy_delta", 0.0)
        }
    
    # Get top 3 candidates by score
    sorted_actions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3 = sorted_actions[:3]
    
    # Generate reasons for each candidate
    candidates = []
    for action, score in top3:
        reasons = _generate_action_reasons(action, state, relationship, predicted_deltas[action])
        candidates.append({
            "action": action,
            "score": score,
            "predicted_delta": predicted_deltas[action],
            "reasons": reasons
        })
    
    # Select action if not provided
    if selected_action is None:
        selected_action = select_action(state, target, test_mode)
    
    # Generate selection reasons
    selection_reasons = _generate_selection_reasons(selected_action, state, relationship, scores)
    
    explanation = {
        "emotion": emotion_section,
        "interoception": interoception_section,
        "relationships": relationships_section,
        "candidates": candidates,
        "selected": selected_action,
        "selection_reasons": selection_reasons
    }
    
    return explanation


def _generate_action_reasons(
    action: str,
    state: EmotionState,
    relationship: Dict[str, float],
    predicted_delta: Dict[str, float]
) -> List[str]:
    """Generate human-readable reasons for an action's score."""
    reasons = []
    
    # Relationship-based reasons
    if relationship.get("bond", 0) > 0.5:
        reasons.append("High bond with target")
    if relationship.get("grudge", 0) > 0.5:
        reasons.append("Existing grudge")
    if relationship.get("trust", 0) < 0.3:
        reasons.append("Low trust")
    
    # State-based reasons
    if state.social_safety < 0.4:
        reasons.append("Low social safety")
    if state.energy < 0.4:
        reasons.append("Low energy")
    
    # Prediction-based reasons
    if predicted_delta.get("safety", 0) > 0.02:
        reasons.append(f"Predicted to improve safety (+{predicted_delta['safety']:.2f})")
    if predicted_delta.get("energy", 0) > 0.01:
        reasons.append(f"Energy-preserving (+{predicted_delta['energy']:.2f})")
    if predicted_delta.get("safety", 0) < -0.02:
        reasons.append("Risk of safety reduction")
    
    # Action-specific reasons
    if action == "approach" and state.social_safety > 0.5:
        reasons.append("Safe to approach")
    if action == "repair_offer" and relationship.get("grudge", 0) > 0.3:
        reasons.append("Opportunity for repair")
    if action == "boundary" and relationship.get("trust", 0) < 0.4:
        reasons.append("Boundary needed for protection")
    if action == "withdraw" and state.social_safety < 0.4:
        reasons.append("Conservative choice for low safety")
    if action == "attack" and relationship.get("grudge", 0) > 0.7:
        reasons.append("Strong grudge motivates retaliation")
    
    # Default reason if none generated
    if not reasons:
        reasons.append(f"Neutral expected outcome")
    
    return reasons


def _generate_selection_reasons(
    selected_action: str,
    state: EmotionState,
    relationship: Dict[str, float],
    scores: Dict[str, float]
) -> List[str]:
    """Generate reasons for why this action was selected."""
    reasons = []
    
    # Check if selected has highest score
    max_score_action = max(scores.keys(), key=lambda a: scores[a])
    if selected_action == max_score_action:
        reasons.append("Highest score given current state")
    else:
        reasons.append(f"Selected via stochastic process (score: {scores[selected_action]:.3f})")
    
    # State-based reasons
    if state.social_safety < 0.4:
        reasons.append("Low social safety favors conservative action")
    if state.energy < 0.4:
        reasons.append("Low energy favors efficient action")
    
    # Relationship-based reasons
    if relationship.get("grudge", 0) > 0.5:
        reasons.append("High grudge influences selection")
    if relationship.get("trust", 0) < 0.3:
        reasons.append("Low trust increases caution")
    
    # Action-specific reasons
    if selected_action == "withdraw":
        reasons.append("Withdrawal preserves safety and energy")
    elif selected_action == "approach":
        reasons.append("Approach builds connection")
    elif selected_action == "repair_offer":
        reasons.append("Repair attempt may reduce grudge")
    elif selected_action == "boundary":
        reasons.append("Boundary establishes protection")
    elif selected_action == "attack":
        reasons.append("Attack addresses perceived threat")
    
    return reasons[:3]  # Limit to top 3 reasons


async def select_action_with_explanation(
    target: str,
    test_mode: bool = False
) -> Dict[str, Any]:
    """
    MVP-3 C1: Select an action and generate explanation, storing it in DB.
    
    Args:
        target: Target identifier
        test_mode: If True, use deterministic selection
    
    Returns:
        dict with action, explanation, and decision_id
    """
    from emotiond.db import save_decision
    
    # Ensure relationship exists
    relationship_manager._ensure_relationship_fields(target)
    
    # Generate explanation (which includes action selection)
    explanation = await generate_explanation(target, test_mode=test_mode)
    selected_action = explanation["selected"]
    
    # Save decision to database
    decision_id = await save_decision(selected_action, explanation)
    
    # Update relationship with last action
    relationship_manager.set_last_action(target, selected_action)
    await update_relationship(
        target,
        relationship_manager.relationships[target]["bond"],
        relationship_manager.relationships[target]["grudge"],
        relationship_manager.relationships[target].get("trust", 0.0),
        relationship_manager.relationships[target].get("repair_bank", 0.0),
        selected_action
    )
    
    return {
        "action": selected_action,
        "explanation": explanation,
        "decision_id": decision_id
    }
