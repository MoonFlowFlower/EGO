"""
Core emotion processing and state management
"""
import asyncio
import time
from typing import Dict, Any, Optional
from emotiond.models import Event, PlanRequest, PlanResponse
from emotiond.db import get_state, update_state, add_event, get_relationships, update_relationship


class EmotionState:
    """Core emotional state management"""
    
    def __init__(self):
        self.valence = 0.0  # -1.0 to 1.0 (negative to positive)
        self.arousal = 0.3  # 0.0 to 1.0 (calm to excited)
        self.subjective_time = 0
    
    def update_from_event(self, event: Event) -> None:
        """Update emotional state based on event type and content"""
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
            # World events can have strong impacts
            if event.meta and event.meta.get("positive", False):
                self.valence = min(1.0, self.valence + 0.2)
            elif event.meta and event.meta.get("negative", False):
                self.valence = max(-1.0, self.valence - 0.2)
                self.arousal = min(1.0, self.arousal + 0.15)
    
    def apply_homeostasis_drift(self) -> None:
        """Apply natural drift toward neutral state"""
        # Valence slowly drifts toward neutral
        if self.valence > 0:
            self.valence = max(0, self.valence - 0.01)
        elif self.valence < 0:
            self.valence = min(0, self.valence + 0.01)
        
        # Arousal slowly drifts toward calm
        self.arousal = self.arousal * 0.99
        
        # Update subjective time
        self.subjective_time += 1


class RelationshipManager:
    """Manages bond and grudge relationships with targets"""
    
    def __init__(self):
        self.relationships: Dict[str, Dict[str, float]] = {}
    
    def update_from_event(self, event: Event) -> None:
        """Update relationships based on event"""
        target = event.target
        
        # Initialize relationship if it doesn't exist
        if target not in self.relationships:
            self.relationships[target] = {"bond": 0.0, "grudge": 0.0}
        
        # Update based on event type
        if event.type == "user_message":
            # Positive interactions build bond
            if event.text and any(word in event.text.lower() for word in ["good", "great", "thanks", "love", "happy"]):
                self.relationships[target]["bond"] = min(1.0, self.relationships[target]["bond"] + 0.1)
            # Negative interactions build grudge
            elif event.text and any(word in event.text.lower() for word in ["bad", "hate", "stupid", "wrong", "angry", "terrible", "awful", "horrible"]):
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.1)
        
        elif event.type == "assistant_reply":
            # Replies maintain existing relationships
            pass
        
        elif event.type == "world_event":
            # World events can affect relationships
            if event.meta and event.meta.get("betrayal", False):
                self.relationships[target]["grudge"] = min(1.0, self.relationships[target]["grudge"] + 0.3)
                self.relationships[target]["bond"] = max(0.0, self.relationships[target]["bond"] - 0.2)
    
    def apply_consolidation_drift(self) -> None:
        """Apply slow decay to relationships"""
        for target in self.relationships:
            # Bond slowly decays
            self.relationships[target]["bond"] = self.relationships[target]["bond"] * 0.995
            
            # Grudge slowly decays (slower than bond)
            self.relationships[target]["grudge"] = self.relationships[target]["grudge"] * 0.99


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
    
    # Load relationships
    db_relationships = await get_relationships()
    for rel in db_relationships:
        relationship_manager.relationships[rel["target"]] = {
            "bond": rel["bond"],
            "grudge": rel["grudge"]
        }


async def process_event(event: Event) -> Dict[str, Any]:
    """Process incoming events and update emotional state"""
    # Store event
    await add_event(event.model_dump())
    
    # Update emotional state based on event
    emotion_state.update_from_event(event)
    relationship_manager.update_from_event(event)
    
    # Persist state to database
    await update_state(
        emotion_state.valence,
        emotion_state.arousal,
        emotion_state.subjective_time
    )
    
    # Persist relationships to database
    for target, rel_data in relationship_manager.relationships.items():
        await update_relationship(target, rel_data["bond"], rel_data["grudge"])
    
    return {"status": "processed", "valence": emotion_state.valence, "arousal": emotion_state.arousal}


async def generate_plan(request: PlanRequest) -> PlanResponse:
    """Generate response plan based on current emotional state"""
    # Get current state from memory
    current_valence = emotion_state.valence
    current_arousal = emotion_state.arousal
    
    # Get relationships for the user
    user_relationship = relationship_manager.relationships.get(request.user_id, {"bond": 0.0, "grudge": 0.0})
    
    # Determine tone based on valence and arousal
    if current_valence > 0.3 and current_arousal < 0.5:
        tone = "warm"
    elif current_valence > 0:
        tone = "soft"
    elif current_valence < -0.3 and user_relationship["grudge"] > 0.5:
        tone = "cold"
    else:
        tone = "guarded"
    
    # Determine intent based on emotional state and relationships
    if current_valence < -0.2 and user_relationship["grudge"] > 0.7:
        intent = "retaliate"
    elif user_relationship["bond"] < 0.3 and user_relationship["grudge"] > 0.4:
        intent = "distance"
    elif current_valence < -0.1:
        intent = "repair"
    elif user_relationship["bond"] > 0.6:
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
    
    plan = PlanResponse(
        tone=tone,
        intent=intent,
        focus_target=request.user_id,
        key_points=key_points,
        constraints=constraints,
        emotion={"valence": current_valence, "arousal": current_arousal},
        relationship={"bond": user_relationship["bond"], "grudge": user_relationship["grudge"]}
    )
    
    return plan


async def homeostasis_loop():
    """Loop A: homeostasis drift + emotion inertia + subjective time update (1-2s)"""
    while True:
        # Update emotional state drift
        emotion_state.apply_homeostasis_drift()
        
        # Persist state to database
        await update_state(
            emotion_state.valence,
            emotion_state.arousal,
            emotion_state.subjective_time
        )
        
        await asyncio.sleep(1)


async def consolidation_loop():
    """Loop B: consolidation (slow variable drift: bond/grudge decay) (30-120s)"""
    while True:
        # Update bond/grudge decay
        relationship_manager.apply_consolidation_drift()
        
        # Persist relationships to database
        for target, rel_data in relationship_manager.relationships.items():
            await update_relationship(target, rel_data["bond"], rel_data["grudge"])
        
        await asyncio.sleep(30)