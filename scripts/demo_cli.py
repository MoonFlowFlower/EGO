#!/usr/bin/env python3
"""
Demo CLI script for emotiond
"""
import asyncio
import httpx
import time
from typing import Dict, Any


async def demo_scenario():
    """Run demo scenario showing emotion dynamics"""
    print("Starting OpenEmotion demo scenario...")
    print("=" * 50)
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:18080") as client:
        # Step 1: Health check
        try:
            health_response = await client.get("/health")
            print(f"✓ Health check: {health_response.json()}")
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return
        
        # Step 2: A accepts repeatedly to build bond
        print("\nStep 1: Building bond with target A...")
        for i in range(3):
            event = {
                "type": "user_message",
                "actor": "A",
                "target": "agent",
                "text": f"Positive interaction {i+1}"
            }
            await client.post("/event", json=event)
            print(f"  Event {i+1}: A positive interaction")
        
        # Step 3: Get current plan
        plan_request = {
            "user_id": "demo_user",
            "user_text": "How are you feeling?"
        }
        plan_response = await client.post("/plan", json=plan_request)
        plan_data = plan_response.json()
        print(f"\nCurrent state after positive interactions:")
        print(f"  Tone: {plan_data['tone']}")
        print(f"  Intent: {plan_data['intent']}")
        print(f"  Emotion: {plan_data['emotion']}")
        print(f"  Relationship: {plan_data['relationship']}")
        
        # Step 4: A rejects/betrays once to induce sadness and grudge
        print("\nStep 2: A betrays to induce sadness and grudge...")
        betrayal_event = {
            "type": "user_message",
            "actor": "A",
            "target": "agent",
            "text": "I don't care about you anymore"
        }
        await client.post("/event", json=betrayal_event)
        print("  Event: A betrayal")
        
        # Step 5: Get plan after betrayal
        plan_response = await client.post("/plan", json=plan_request)
        plan_data = plan_response.json()
        print(f"\nState after betrayal:")
        print(f"  Tone: {plan_data['tone']}")
        print(f"  Intent: {plan_data['intent']}")
        print(f"  Emotion: {plan_data['emotion']}")
        print(f"  Relationship: {plan_data['relationship']}")
        
        # Step 6: Separation period
        print("\nStep 3: Separation period (simulated)...")
        print("  No contact for separation pain demonstration")
        
        # Step 7: Repair sequence
        print("\nStep 4: Repair sequence...")
        for i in range(2):
            repair_event = {
                "type": "user_message",
                "actor": "A",
                "target": "agent",
                "text": f"I'm sorry, let's repair our relationship {i+1}"
            }
            await client.post("/event", json=repair_event)
            print(f"  Repair attempt {i+1}")
        
        # Step 8: Final state
        plan_response = await client.post("/plan", json=plan_request)
        plan_data = plan_response.json()
        print(f"\nFinal state after repair attempts:")
        print(f"  Tone: {plan_data['tone']}")
        print(f"  Intent: {plan_data['intent']}")
        print(f"  Emotion: {plan_data['emotion']}")
        print(f"  Relationship: {plan_data['relationship']}")
        
        print("\n" + "=" * 50)
        print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_scenario())