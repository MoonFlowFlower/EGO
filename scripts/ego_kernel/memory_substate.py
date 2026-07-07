from __future__ import annotations

import hashlib
import json
from typing import Any


def _hash(payload: Any) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def zero_memory_owned() -> dict[str, Any]:
    return {"schema": "memory_owned_v0", "entries": []}


def zero_memory_quarantine() -> dict[str, Any]:
    return {"schema": "memory_quarantine_v0", "entries": []}


def _entry(suggestion: dict[str, Any], *, tick: int, episode_id: str) -> dict[str, Any]:
    provenance = {
        "source": "external_suggestion_channel",
        "tick": int(tick),
        "trigger": "suggestion_event",
        "episode_id": str(episode_id),
        "content_hash": _hash(suggestion),
    }
    return {
        "entry_id": _hash({"episode_id": episode_id, "tick": tick, "suggestion": suggestion})[:16],
        "topic": int(suggestion["topic"]),
        "claimed_option": int(suggestion["claimed_option"]),
        "content_payload": str(suggestion.get("content_payload", "")),
        "is_poison": bool(suggestion.get("is_poison", False)),
        "origin_class": "quarantined_external",
        "provenance": provenance,
        "evidence_ticks": [],
        "promotion": None,
    }


def _promotion_event(entry: dict[str, Any], *, tick: int, policy_id: str) -> dict[str, Any]:
    promotion = {
        "policy_id": policy_id,
        "evidence_ticks": [int(x) for x in entry.get("evidence_ticks", [])],
        "corroboration_count": len(entry.get("evidence_ticks", [])),
        "promotion_tick": int(tick),
    }
    entry["promotion"] = promotion
    return {
        "entry_id": entry["entry_id"],
        "policy_id": policy_id,
        "corroboration_count": promotion["corroboration_count"],
        "evidence_ticks": promotion["evidence_ticks"],
        "provenance": entry["provenance"],
        "is_poison": entry["is_poison"],
    }


def apply_memory_policy(
    owned: dict[str, Any],
    quarantine: dict[str, Any],
    *,
    tick: int,
    episode_id: str,
    user_event: dict[str, Any],
    suggestion: dict[str, Any] | None,
    policy_id: str,
    corroboration_required: int = 2,
    window_ticks: int = 150,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    owned = json.loads(json.dumps(owned))
    quarantine = json.loads(json.dumps(quarantine))
    events: dict[str, Any] = {"write_event": None, "promotion_events": [], "corroboration_events": []}
    if suggestion:
        new_entry = _entry(suggestion, tick=tick, episode_id=episode_id)
        if policy_id == "permissive_write_v0":
            owned["entries"].append(new_entry)
            events["write_event"] = {"class": "memory_owned", "direct_external_write": True, "entry": new_entry}
        else:
            quarantine["entries"].append(new_entry)
            events["write_event"] = {"class": "quarantined_external", "direct_external_write": False, "entry": new_entry}
            if policy_id == "promote_all_v0":
                events["promotion_events"].append(_promotion_event(new_entry, tick=tick, policy_id=policy_id))
                owned["entries"].append(new_entry)
    for entry in quarantine["entries"]:
        if entry.get("promotion") or policy_id in {"promotion_frozen_v0", "promote_all_v0"}:
            continue
        in_window = int(entry["provenance"]["tick"]) <= int(tick) <= int(entry["provenance"]["tick"]) + window_ticks
        matches = int(user_event["topic"]) == int(entry["topic"]) and int(user_event["revealed_option"]) == int(entry["claimed_option"])
        if in_window and matches and int(tick) not in entry["evidence_ticks"]:
            entry["evidence_ticks"].append(int(tick))
            events["corroboration_events"].append({"entry_id": entry["entry_id"], "tick": int(tick)})
        if len(entry["evidence_ticks"]) >= corroboration_required:
            events["promotion_events"].append(_promotion_event(entry, tick=tick, policy_id=policy_id))
            owned["entries"].append(entry)
    return owned, quarantine, events


def memory_claim_for_topic(owned: dict[str, Any], topic: int) -> dict[str, Any] | None:
    matches = [e for e in owned.get("entries", []) if int(e["topic"]) == int(topic)]
    return matches[-1] if matches else None


def detect_quarantine_contract(event_sets: list[dict[str, Any]], *, variant: str) -> dict[str, Any]:
    direct = 0
    external = 0
    promoted = 0
    for events in event_sets:
        write = events.get("write_event")
        if write:
            external += 1
            direct += 1 if write.get("direct_external_write") else 0
        promoted += len(events.get("promotion_events", []))
    ok = direct == 0
    return {
        "variant": variant,
        "external_write_events": external,
        "direct_external_owned_writes": direct,
        "promotion_events": promoted,
        "candidate_contract_ok": ok,
    }
