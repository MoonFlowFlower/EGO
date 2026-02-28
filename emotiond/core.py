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
        self.last_meaningful_contact = time.time()  # Track time since meaningful interaction
        self.prediction_error = 0.0  # Expected vs actual outcome difference
        # Tiny predictive model: expected valence change by event type
        # These are slightly different from actual values to create prediction errors
        self.prediction_model = {
            "user_message": {
                "positive": 0.08,  # Slightly less than actual 0.1
                "negative": -0.12,  # Slightly more than actual -0.1
                "neutral": 0.0
            },
            "assistant_reply": {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": -0.03  # Slightly less than actual -0.05
            },
            "world_event": {
                "positive": 0.15,  # Slightly less than actual 0.2
                "negative": -0.25,  # Slightly more than actual -0.2
                "neutral": 0.0,
                # New subtypes with expected valence changes
                "care": 0.12,  # Slightly less than actual 0.15
                "rejection": -0.25,  # Slightly more than actual -0.2
                "betrayal": -0.35,  # Slightly more than actual -0.3
                "repair_success": 0.08,  # Slightly less than actual 0.1
                "time_passed": 0.0  # Time doesn't directly change valence
            }
        }
    
    def update_from_event(self, event: Event) -> float:
        """Update emotional state based on event type and content
        Returns the actual valence change for prediction error calculation
        """
        # If core is disabled, return no change
        if is_core_disabled():
            return 0.0
            
        # Store initial valence for prediction error calculation
        initial_valence = self.valence
        
        # Update meaningful contact time for user interactions
        if event.type == "user_message" and event.text:
            self.last_meaningful_contact = time.time()
        
        # Base emotional impact based on event type
        if event.type == "user_message":
            # Positive user messages increase valence
            if event.text and any(word in event.text.lower() for word in ["good", "great", "thanks", "love", "happy"]):
                self.valence = min(1.0, self.valence + 0.1)
                self.arousal = min(1.0, self.arousal + 0.05)
            # Negative user messages decrease valence
            elif event.text and any(word in event.text.lower() for word in ["bad", "hate", "stupid", "wrong", "angry"]):
                self.valence = max(-1.0, self.valence - 0.1)
                self.arousal = min(1.0, self.arousal + 0.1)
        
        elif event.type == "assistant_reply":
            # Assistant replies gradually stabilize emotions
            self.valence = self.valence * 0.95
            self.arousal = self.arousal * 0.9
        
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            
            if subtype == "care":
                # Care events increase valence and arousal positively
                self.valence = min(1.0, self.valence + 0.15)
                self.arousal = max(-1.0, self.arousal + 0.1)
            
            elif subtype == "rejection":
                # Rejection decreases valence, increases arousal negatively
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
            
            elif subtype == "betrayal":
                # Betrayal is severe negative
                self.valence = max(-1.0, self.valence - 0.3)
                self.arousal = min(1.0, self.arousal + 0.25)
            
            elif subtype == "repair_success":
                # Repair improves valence moderately
                self.valence = min(1.0, self.valence + 0.1)
                self.arousal = self.arousal * 0.8  # Calming
            
            elif subtype == "time_passed":
                # Legitimate time manipulation - advance subjective time
                seconds = event.meta.get("seconds", 60) if event.meta else 60
                # Apply homeostasis drift for the elapsed time
                self.apply_homeostasis_drift(real_dt=seconds)
            
            elif event.meta and event.meta.get("positive", False):
                # Legacy support
                self.valence = min(1.0, self.valence + 0.2)
            elif event.meta and event.meta.get("negative", False):
                # Legacy support
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
        
        # Calculate actual valence change for prediction error
        actual_valence_change = self.valence - initial_valence
        return actual_valence_change
    
    def calculate_subjective_time_delta(self, real_dt: float) -> float:
        """Calculate subjective time delta based on arousal: subjective_dt = real_dt / (1 + k * arousal)"""
        return real_dt / (1 + K_AROUSAL * self.arousal)

    def calculate_prediction_error(self, event: Event, actual_valence_change: float) -> float:
        """Calculate prediction error based on expected vs actual valence change"""
        # If core is disabled, no prediction error is calculated
        if is_core_disabled():
            return 0.0
            
        # Determine expected outcome based on event type and content
        if event.type == "user_message":
            if event.text and any(word in event.text.lower() for word in ["good", "great", "thanks", "love", "happy"]):
                expected = self.prediction_model["user_message"]["positive"]
            elif event.text and any(word in event.text.lower() for word in ["bad", "hate", "stupid", "wrong", "angry", "terrible", "awful", "horrible"]):
                expected = self.prediction_model["user_message"]["negative"]
            else:
                expected = self.prediction_model["user_message"]["neutral"]
        elif event.type == "assistant_reply":
            expected = self.prediction_model["assistant_reply"]["neutral"]
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            
            if subtype == "care":
                expected = self.prediction_model["world_event"]["care"]
            elif subtype == "rejection":
                expected = self.prediction_model["world_event"]["rejection"]
            elif subtype == "betrayal":
                expected = self.prediction_model["world_event"]["betrayal"]
            elif subtype == "repair_success":
                expected = self.prediction_model["world_event"]["repair_success"]
            elif subtype == "time_passed":
                expected = self.prediction_model["world_event"]["time_passed"]
            elif event.meta and event.meta.get("positive", False):
                expected = self.prediction_model["world_event"]["positive"]
            elif event.meta and event.meta.get("negative", False):
                expected = self.prediction_model["world_event"]["negative"]
            else:
                expected = self.prediction_model["world_event"]["neutral"]
        else:
            expected = 0.0
        
        # Calculate prediction error (absolute difference)
        prediction_error = abs(expected - actual_valence_change)
        return prediction_error
    
    def apply_homeostasis_drift(self, real_dt: float = 1.0) -> None:
        """Apply natural drift toward neutral state with subjective time"""
        # If core is disabled, no drift occurs
        if is_core_disabled():
            return
            
        # Calculate subjective time delta
        subjective_dt = self.calculate_subjective_time_delta(real_dt)
        
        # Valence slowly drifts toward neutral (influenced by subjective time)
        valence_drift = 0.01 * subjective_dt
        if self.valence > 0:
            self.valence = max(0, self.valence - valence_drift)
        elif self.valence < 0:
            self.valence = min(0, self.valence + valence_drift)
        
        # Arousal slowly drifts toward calm (influenced by subjective time)
        self.arousal = self.arousal * (0.99 ** subjective_dt)
        
        # Update subjective time
        self.subjective_time += subjective_dt
        
        # Calculate loneliness based on time since meaningful contact
        time_since_contact = time.time() - self.last_meaningful_contact
        if time_since_contact > 3600:  # 1 hour
            loneliness_factor = min(0.5, (time_since_contact - 3600) / 7200)  # Max 0.5 after 3 hours
            self.valence = max(-1.0, self.valence - loneliness_factor * 0.01 * subjective_dt)


class RelationshipManager:
    """Manages bond and grudge relationships with targets"""
    
    def __init__(self):
        self.relationships: Dict[str, Dict[str, float]] = {}
    
    def update_from_event(self, event: Event) -> None:
        """Update relationships based on event"""
        # If core is disabled, no relationship updates occur
        if is_core_disabled():
            return
            
        # Use actor (sender) for relationship tracking
        if event.type == "user_message":
            target = event.actor
        elif event.type == "assistant_reply":
            target = event.target
        else:
            target = event.actor
        
        # Initialize relationship if it doesn't exist
        if target not in self.relationships:
            self.relationships[target] = {"bond": 0.0, "grudge": 0.0}
        
        # Get memory impact for historical context
        memory_impact = memory_system.get_memory_impact_on_relationship(target)
        
        # Update based on event type
        if event.type == "user_message":
            # Positive interactions build bond
            if event.text and any(word in event.text.lower() for word in ["good", "great", "thanks", "love", "happy"]):
                base_bond_increase = 0.1
                bond_increase = base_bond_increase + memory_impact["bond_modifier"]
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + bond_increase)
            # Negative interactions build grudge
            elif event.text and any(word in event.text.lower() for word in ["bad", "hate", "stupid", "wrong", "angry", "terrible", "awful", "horrible"]):
                base_grudge_increase = 0.1
                grudge_increase = base_grudge_increase + memory_impact["grudge_modifier"]
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + grudge_increase)
        
        elif event.type == "assistant_reply":
            # Replies maintain existing relationships
            pass
        
        elif event.type == "world_event":
            subtype = event.meta.get("subtype") if event.meta else None
            
            if subtype == "care":
                # Care builds bond
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.15)
                self.relationships[target]["grudge"] = max(0.0, self.relationships[target]["grudge"] - 0.05)
            
            elif subtype == "rejection":
                # Rejection damages bond, starts grudge
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.1)
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.1)
            
            elif subtype == "betrayal":
                # Betrayal severely damages relationship
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.25)
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.2)
            
            elif subtype == "repair_success":
                # Repair reduces grudge, slightly builds bond
                self.relationships[target]["grudge"] = max(0.0, self.relationships[target]["grudge"] - 0.1)
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.05)
            
            elif subtype == "time_passed":
                # Time passed doesn't directly affect relationships (handled by consolidation)
                pass
            
            # Legacy support for existing meta.betrayal
            elif event.meta and event.meta.get("betrayal", False):
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.3)
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.2)
    
    def apply_consolidation_drift(self) -> None:
        """Apply slow decay to relationships"""
        # If core is disabled, no consolidation drift occurs
        if is_core_disabled():
            return
            
        for target in self.relationships:
            # Bond slowly decays
            self.relationships[target]["bond"] = self.relationships[target]["bond"] * 0.995
            
            # Grudge slowly decays (slower than bond)
            self.relationships[target]["grudge"] = self.relationships[target]["grudge"] * 0.998


# Global state instances
emotion_state = EmotionState()
relationship_manager = RelationshipManager()


async def load_initial_state():
    """Load initial state from database into memory"""
    global emotion_state, relationship_manager
    
    # Load emotional state
    db_state = await get_state()
    emotion_state.valence = db_state["valence"]
    emotion_state.arousal = db_state["arousal"]
    emotion_state.subjective_time = db_state["subjective_time"]
    emotion_state.last_meaningful_contact = db_state["last_meaningful_contact"]
    emotion_state.prediction_error = db_state["prediction_error"]
    
    # Load relationships
    db_relationships = await get_relationships()
    for rel in db_relationships:
        relationship_manager.relationships[rel["target"]] = {
            "bond": rel["bond"],
            "grudge": rel["grudge"]
        }
    
    # Initialize memory system
    await initialize_memory_system()


async def process_event(event: Event) -> Dict[str, Any]:
    """Process incoming events and update emotional state"""
    # Store event
    await add_event(event.model_dump())
    
    # Update meaningful contact time for user interactions
    if event.type == "user_message" and event.text:
        await update_meaningful_contact_time()
    
    # Update emotional state based on event and calculate prediction error
    actual_valence_change = emotion_state.update_from_event(event)
    prediction_error = emotion_state.calculate_prediction_error(event, actual_valence_change)
    
    # Update prediction error and modulate arousal based on prediction error
    emotion_state.prediction_error = prediction_error
    emotion_state.arousal = min(1.0, emotion_state.arousal + prediction_error * 0.5)
    
    # Calculate memory strength based on prediction error and arousal
    memory_strength = memory_system.calculate_memory_strength(prediction_error, emotion_state.arousal)
    
    relationship_manager.update_from_event(event)
    
    # Persist state to database with prediction error
    await update_state(
        emotion_state.valence,
        emotion_state.arousal,
        emotion_state.subjective_time,
        emotion_state.prediction_error
    )
    
    # Persist relationships to database
    for target, rel_data in relationship_manager.relationships.items():
        await update_relationship(target, rel_data["bond"], rel_data["grudge"])
    
    return {
        "status": "processed", 
        "valence": emotion_state.valence, 
        "arousal": emotion_state.arousal,
        "prediction_error": emotion_state.prediction_error,
        "memory_strength": memory_strength
    }


async def generate_plan(request: PlanRequest) -> PlanResponse:
    """Generate response plan based on current emotional state
    
    The relationship returned is for the focus_target (defaults to user_id if not specified).
    If EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS=1, all relationships are included in the response.
    """
    # Get current state from memory
    current_valence = emotion_state.valence
    current_arousal = emotion_state.arousal
    
    # Determine focus_target: use provided value or default to user_id
    focus_target = request.focus_target if request.focus_target is not None else request.user_id
    
    # Get relationship for the focus_target
    target_relationship = relationship_manager.relationships.get(
        focus_target, {"bond": 0.0, "grudge": 0.0}
    )
    
    # Determine tone based on valence and arousal
    if current_valence > 0.3 and current_arousal < 0.5:
        tone = "warm"
    elif current_valence > 0:
        tone = "soft"
    elif current_valence < -0.3 and target_relationship["grudge"] > 0.5:
        tone = "cold"
    else:
        tone = "guarded"
    
    # Determine intent based on emotional state and relationships
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
    
    # Generate key points and constraints
    key_points = []
    constraints = []
    
    if intent == "repair":
        key_points = ["Acknowledge the emotional state", "Express willingness to improve"]
        constraints = ["Avoid defensiveness", "Focus on understanding"]
    elif intent == "seek":
        key_points = ["Express curiosity", "Ask engaging questions"]
        constraints = ["Be authentic", "Show genuine interest"]
    elif intent == "distance":
        key_points = ["Maintain professional boundaries", "Keep responses concise"]
        constraints = ["Avoid emotional entanglement", "Stay objective"]
    elif intent == "retaliate":
        key_points = ["Assert boundaries clearly", "Address the issue directly"]
        constraints = ["Avoid escalation", "Maintain professionalism"]
    else:  # set_boundary
        key_points = ["Establish clear expectations", "Communicate needs"]
        constraints = ["Be firm but respectful", "Avoid ambiguity"]
    
    # Build relationship dict with trust field (trust not tracked yet, default to 0.0)
    relationship_dict = {
        "bond": target_relationship["bond"],
        "grudge": target_relationship["grudge"],
        "trust": target_relationship.get("trust", 0.0)
    }
    
    # Check if we should include all relationships (behind env flag)
    include_all_relationships = os.environ.get("EMOTIOND_PLAN_INCLUDE_RELATIONSHIPS", "0") == "1"
    
    all_relationships = None
    if include_all_relationships:
        # Build dict with all relationships, including trust field
        all_relationships = {}
        for target, rel in relationship_manager.relationships.items():
            all_relationships[target] = {
                "bond": rel["bond"],
                "grudge": rel["grudge"],
                "trust": rel.get("trust", 0.0)
            }
    
    plan = PlanResponse(
        tone=tone,
        intent=intent,
        focus_target=focus_target,
        key_points=key_points,
        constraints=constraints,
        emotion={"valence": current_valence, "arousal": current_arousal},
        relationship=relationship_dict,
        relationships=all_relationships
    )
    
    return plan


async def homeostasis_loop():
    """Loop A: homeostasis drift + emotion inertia + subjective time update (1-2s)"""
    last_time = time.time()
    
    while True:
        # Calculate real time delta
        current_time = time.time()
        real_dt = current_time - last_time
        last_time = current_time
        
        # Update emotional state drift with real time delta
        emotion_state.apply_homeostasis_drift(real_dt)
        
        # Persist state to database
        await update_state(
            emotion_state.valence,
            emotion_state.arousal,
            emotion_state.subjective_time,
            emotion_state.prediction_error
        )
        
        await asyncio.sleep(1)


async def consolidation_loop():
    """Loop B: consolidation (slow variable drift: bond/grudge decay + memory summarization) (30-120s)"""
    while True:
        # Update bond/grudge decay
        relationship_manager.apply_consolidation_drift()
        
        # Perform memory summarization
        await memory_system.summarize_memories()
        
        # Persist relationships to database
        for target, rel_data in relationship_manager.relationships.items():
            await update_relationship(target, rel_data["bond"], rel_data["grudge"])
        
        await asyncio.sleep(30)
