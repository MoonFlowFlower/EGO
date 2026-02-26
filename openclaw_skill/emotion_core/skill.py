#!/usr/bin/env python3
"""
OpenClaw skill for emotiond integration
"""

import httpx
import json
import sys
from typing import Dict, Any

EMOTIOND_URL = "http://127.0.0.1:18080"

def send_event(event_data: Dict[str, Any]) -> bool:
    """Send an event to emotiond"""
    try:
        response = httpx.post(f"{EMOTIOND_URL}/event", json=event_data, timeout=5.0)
        return response.status_code == 200
    except httpx.RequestError:
        return False

def get_plan(user_id: str, user_text: str) -> Dict[str, Any]:
    """Get response plan from emotiond"""
    try:
        response = httpx.post(
            f"{EMOTIOND_URL}/plan", 
            json={"user_id": user_id, "user_text": user_text},
            timeout=5.0
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"emotiond returned status {response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"Failed to connect to emotiond: {e}"}

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) < 3:
        print("Usage: skill.py <user_id> <user_text>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    user_text = sys.argv[2]
    
    # Send user message event
    event_sent = send_event({
        "type": "user_message",
        "actor": user_id,
        "target": "agent",
        "text": user_text
    })
    
    if not event_sent:
        print("ERROR: Failed to send event to emotiond")
        sys.exit(1)
    
    # Get response plan
    plan = get_plan(user_id, user_text)
    print(json.dumps(plan, indent=2))
    
    # Exit with error code if emotiond failed
    if "error" in plan:
        sys.exit(1)