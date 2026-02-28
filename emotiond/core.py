"""
Core emotion processing and state management
"""
import os
import asyncio
import time
from typing import Dict, Any, Optional
from emotiond.models import Event, PlanRequest, PlanResponse
from emotiond.db import get_state, update_state, add_event, get_relationships, update_relationship, update_meaningful_contact_time
from emotiond.config import K_AROUSAL, is_core_disabled
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
            elif event.text and any(w in event.text.lower() for w in ["bad", "hate", "stupid", "wrong", "angry"]):
                self.valence = max(-1.0, self.valence - 0.1)
                self.arousal = min(1.0, self.arousal + 0.1)
                self.anger = min(1.0, self.anger + 0.05)
        
        elif event.type == "assistant_reply":
            self.valence = self.valence * 0.95
            self.arousal = self.arousal * 0.9
        
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            
            if subtype == "care":
                self.valence = min(1.0, self.valence + 0.15)
                self.arousal = max(-1.0, self.arousal + 0.1)
                self.joy = min(1.0, self.joy + 0.15)
                self.anxiety = max(0.0, self.anxiety - 0.1)
                self.loneliness = max(0.0, self.loneliness - 0.1)
            elif subtype == "rejection":
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
                self.sadness = min(1.0, self.sadness + 0.2)
                self.loneliness = min(1.0, self.loneliness + 0.15)
                self.anger = min(1.0, self.anger + 0.1)
            elif subtype == "betrayal":
                self.valence = max(-1.0, self.valence - 0.3)
                self.arousal = min(1.0, self.arousal + 0.25)
                self.anger = min(1.0, self.anger + 0.25)
                self.sadness = min(1.0, self.sadness + 0.15)
                self.anxiety = min(1.0, self.anxiety + 0.15)
                self.joy = max(0.0, self.joy - 0.2)
            elif subtype == "repair_success":
                self.valence = min(1.0, self.valence + 0.1)
                self.arousal = self.arousal * 0.8
                self.joy = min(1.0, self.joy + 0.1)
                self.anxiety = max(0.0, self.anxiety - 0.1)
            elif subtype == "ignored":
                self.loneliness = min(1.0, self.loneliness + 0.1)
                self.sadness = min(1.0, self.sadness + 0.05)
            elif subtype == "time_passed":
                seconds = event.meta.get("seconds", 60) if event.meta else 60
                self.apply_homeostasis_drift(real_dt=seconds)
            elif event.meta and event.meta.get("positive", False):
                self.valence = min(1.0, self.valence + 0.2)
            elif event.meta and event.meta.get("negative", False):
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
        
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
        time_since_contact = time.time() - self.last_meaningful_contact
        if time_since_contact > 3600:
            loneliness_factor = min(0.5, (time_since_contact - 3600) / 7200)
            self.valence = max(-1.0, self.valence - loneliness_factor * 0.01 * subjective_dt)
            self.loneliness = min(1.0, self.loneliness + loneliness_factor * 0.01 * subjective_dt)


class RelationshipManager:
    def __init__(self):
        self.relationships: Dict[str, Dict[str, float]] = {}
    
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


emotion_state = EmotionState()
relationship_manager = RelationshipManager()


async def load_initial_state():
    global emotion_state, relationship_manager
    db_state = await get_state()
    emotion_state.valence = db_state["valence"]
    emotion_state.arousal = db_state["arousal"]
    emotion_state.subjective_time = db_state["subjective_time"]
    emotion_state.last_meaningful_contact = db_state["last_meaningful_contact"]
    emotion_state.prediction_error = db_state["prediction_error"]
    emotion_state.regulation_budget = db_state.get("regulation_budget", 1.0)
    db_relationships = await get_relationships()
    for rel in db_relationships:
        relationship_manager.relationships[rel["target"]] = {
            "bond": rel["bond"],
            "grudge": rel["grudge"],
            "trust": rel.get("trust", 0.0),
            "repair_bank": rel.get("repair_bank", 0.0)
        }
    await initialize_memory_system()


async def process_event(event: Event) -> Dict[str, Any]:
    await add_event(event.model_dump())
    if event.type == "user_message" and event.text:
        await update_meaningful_contact_time()
    actual_valence_change = emotion_state.update_from_event(event)
    prediction_error = emotion_state.calculate_prediction_error(event, actual_valence_change)
    emotion_state.prediction_error = prediction_error
    emotion_state.arousal = min(1.0, emotion_state.arousal + prediction_error * 0.5)
    memory_strength = memory_system.calculate_memory_strength(prediction_error, emotion_state.arousal)
    relationship_manager.update_from_event(event, emotion_state)
    await update_state(emotion_state.valence, emotion_state.arousal, emotion_state.subjective_time, emotion_state.prediction_error, emotion_state.regulation_budget)
    for target, rel_data in relationship_manager.relationships.items():
        await update_relationship(target, rel_data["bond"], rel_data["grudge"], rel_data.get("trust", 0.0), rel_data.get("repair_bank", 0.0))
    return {"status": "processed", "valence": emotion_state.valence, "arousal": emotion_state.arousal, "prediction_error": emotion_state.prediction_error, "memory_strength": memory_strength, "regulation_budget": emotion_state.regulation_budget}


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
        await update_state(emotion_state.valence, emotion_state.arousal, emotion_state.subjective_time, emotion_state.prediction_error, emotion_state.regulation_budget)
        await asyncio.sleep(1)


async def consolidation_loop():
    while True:
        relationship_manager.apply_consolidation_drift()
        await memory_system.summarize_memories()
        for target, rel_data in relationship_manager.relationships.items():
            await update_relationship(target, rel_data["bond"], rel_data["grudge"], rel_data.get("trust", 0.0), rel_data.get("repair_bank", 0.0))
        await asyncio.sleep(30)
