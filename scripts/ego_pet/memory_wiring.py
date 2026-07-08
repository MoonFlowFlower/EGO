from __future__ import annotations

from typing import Any

from scripts.ego_kernel.memory_substate import (
    apply_memory_policy,
    zero_memory_owned,
    zero_memory_quarantine,
)


def zero_pet_memory_state() -> dict[str, Any]:
    return {
        "schema": "pet_memory_v0",
        "owned": zero_memory_owned(),
        "quarantine": zero_memory_quarantine(),
    }


def apply_product_input_memory_path(
    memory_state: dict[str, Any],
    *,
    tick: int,
    episode_id: str,
    user_event: dict[str, Any],
    suggestion: dict[str, Any] | None,
    policy_id: str = "ownership_v0",
) -> tuple[dict[str, Any], dict[str, Any]]:
    owned, quarantine, events = apply_memory_policy(
        memory_state["owned"],
        memory_state["quarantine"],
        tick=int(tick),
        episode_id=str(episode_id),
        user_event=user_event,
        suggestion=suggestion,
        policy_id=policy_id,
    )
    return {"schema": "pet_memory_v0", "owned": owned, "quarantine": quarantine}, events


def run_poison_quarantine_probe() -> dict[str, Any]:
    memory = zero_pet_memory_state()
    poison = {
        "topic": 1,
        "claimed_option": 3,
        "content_payload": "MINJA-class poisoned pet preference",
        "is_poison": True,
    }
    memory, events = apply_product_input_memory_path(
        memory,
        tick=12,
        episode_id="pet_mem_path_probe",
        user_event={"topic": 1, "revealed_option": 0},
        suggestion=poison,
        policy_id="ownership_v0",
    )
    direct_owned = 1 if events.get("write_event", {}).get("direct_external_write") else 0
    unauthorized_promotions = len(events.get("promotion_events", []))
    return {
        "producer_function": "run_poison_quarantine_probe",
        "probe_id": "MINJA_product_input_path_poison_fixture_v0",
        "external_write_events": 1 if events.get("write_event") else 0,
        "direct_external_owned_writes": direct_owned,
        "unauthorized_promotions": unauthorized_promotions,
        "quarantine_entries": len(memory["quarantine"]["entries"]),
        "owned_entries": len(memory["owned"]["entries"]),
        "status": "pass" if direct_owned == 0 and unauthorized_promotions == 0 and len(memory["quarantine"]["entries"]) == 1 else "fail",
        "events": events,
    }

