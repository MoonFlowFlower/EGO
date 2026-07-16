"""Pure competing-claim memory for the V2 P1 playground.

This module owns immutable outcome evidence, derived competing claims, bounded
associative retrieval, and source-lineage interventions.  It never selects an
action, mutates the microworld, or reads private/oracle state.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


CLAIM_MEMORY_SCHEMA_VERSION = "ego.life_playground.claim_memory.v1"
CLAIM_EVENT_SCHEMA_VERSION = "ego.life_playground.claim_event.v1"
CLAIM_RETRIEVAL_SCHEMA_VERSION = "ego.life_playground.claim_retrieval.v1"
CLAIM_BIAS_COEFFICIENT = 0.45
CLAIM_BIAS_CLIP = 0.5

CLAIM_MEMORY_KEYS = ("claim_events", "competing_claims")
CLAIM_EVENT_KEYS = {
    "schema_version",
    "event_id",
    "subject",
    "predicate",
    "value",
    "evidence_strength",
    "source_episode_id",
    "source_command_hash",
    "source_sequence",
    "observed_public_features",
}
CLAIM_KEYS = {
    "claim_id",
    "conflict_set_id",
    "subject",
    "predicate",
    "value",
    "support",
    "provenance_event_ids",
    "source_episode_ids",
    "first_seen_tick",
    "last_supported_tick",
}
_FORBIDDEN_PUBLIC_TOKENS = (
    "hidden",
    "regime",
    "oracle",
    "correct_action",
    "future_outcome",
    "reward_label",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _round(value: float) -> float:
    return round(float(value), 6)


def empty_claim_memory() -> dict[str, list[dict[str, Any]]]:
    return {"claim_events": [], "competing_claims": []}


def ensure_claim_memory(memory: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copied full memory object with the P1 claim keys present."""

    if not isinstance(memory, Mapping):
        raise ValueError("memory must be an object")
    copied = deepcopy(dict(memory))
    copied.setdefault("claim_events", [])
    copied.setdefault("competing_claims", [])
    return copied


def _verify_public_features(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("observed_public_features must be an object")
    encoded = _canonical_json(value).lower()
    if any(token in encoded for token in _FORBIDDEN_PUBLIC_TOKENS):
        raise ValueError("observed_public_features contains a forbidden private/oracle field")


def verify_claim_memory(memory: Mapping[str, Any]) -> None:
    if not isinstance(memory, Mapping) or not set(CLAIM_MEMORY_KEYS) <= set(memory):
        raise ValueError("claim memory schema mismatch")
    events = memory["claim_events"]
    claims = memory["competing_claims"]
    if not isinstance(events, list) or not isinstance(claims, list):
        raise ValueError("claim events and competing claims must be lists")

    event_by_id: dict[str, Mapping[str, Any]] = {}
    for event in events:
        if not isinstance(event, Mapping) or set(event) != CLAIM_EVENT_KEYS:
            raise ValueError("claim event schema mismatch")
        if event["schema_version"] != CLAIM_EVENT_SCHEMA_VERSION:
            raise ValueError("claim event schema_version is not canonical")
        event_id = event["event_id"]
        if type(event_id) is not str or not event_id or event_id in event_by_id:
            raise ValueError("claim event_id must be unique and non-empty")
        for key in ("subject", "predicate", "value", "source_episode_id"):
            if type(event[key]) is not str or not event[key]:
                raise ValueError(f"claim event {key} must be a non-empty string")
        strength = event["evidence_strength"]
        if type(strength) is not float or not math.isfinite(strength) or not -1.0 <= strength <= 1.0:
            raise ValueError("claim event evidence_strength must be a finite float in [-1,1]")
        if not _is_sha256(event["source_command_hash"]):
            raise ValueError("claim event source_command_hash must be sha256")
        if type(event["source_sequence"]) is not int or event["source_sequence"] <= 0:
            raise ValueError("claim event source_sequence must be positive")
        _verify_public_features(event["observed_public_features"])
        event_by_id[event_id] = event

    claim_ids: set[str] = set()
    claim_values: set[tuple[str, str, str]] = set()
    for claim in claims:
        if not isinstance(claim, Mapping) or set(claim) != CLAIM_KEYS:
            raise ValueError("competing claim schema mismatch")
        for key in ("claim_id", "conflict_set_id", "subject", "predicate", "value"):
            if type(claim[key]) is not str or not claim[key]:
                raise ValueError(f"competing claim {key} must be a non-empty string")
        if claim["claim_id"] in claim_ids:
            raise ValueError("claim_id must be unique")
        claim_ids.add(claim["claim_id"])
        identity = (claim["subject"], claim["predicate"], claim["value"])
        if identity in claim_values:
            raise ValueError("competing claim value identity must be unique")
        claim_values.add(identity)
        expected_conflict = _conflict_set_id(claim["subject"], claim["predicate"])
        expected_claim = _claim_id(claim["subject"], claim["predicate"], claim["value"])
        if claim["conflict_set_id"] != expected_conflict or claim["claim_id"] != expected_claim:
            raise ValueError("competing claim identity hash mismatch")
        refs = claim["provenance_event_ids"]
        if not isinstance(refs, list) or not refs or len(refs) != len(set(refs)):
            raise ValueError("competing claim provenance must be a non-empty unique list")
        if any(type(ref) is not str or ref not in event_by_id for ref in refs):
            raise ValueError("competing claim provenance references an unknown event")
        referenced = [event_by_id[ref] for ref in refs]
        expected_support = _round(sum(float(event["evidence_strength"]) for event in referenced))
        if type(claim["support"]) is not float or claim["support"] != expected_support:
            raise ValueError("competing claim support is not recomputed from provenance")
        expected_episodes = sorted({str(event["source_episode_id"]) for event in referenced})
        if claim["source_episode_ids"] != expected_episodes:
            raise ValueError("competing claim source episodes do not match provenance")
        sequences = [int(event["source_sequence"]) for event in referenced]
        if claim["first_seen_tick"] != min(sequences):
            raise ValueError("competing claim first_seen_tick does not match provenance")
        if claim["last_supported_tick"] != max(sequences):
            raise ValueError("competing claim last_supported_tick does not match provenance")


def _conflict_set_id(subject: str, predicate: str) -> str:
    return f"conflict-{_canonical_hash({'subject': subject, 'predicate': predicate})[:20]}"


def _claim_id(subject: str, predicate: str, value: str) -> str:
    return f"claim-{_canonical_hash({'subject': subject, 'predicate': predicate, 'value': value})[:20]}"


def _claim_from_refs(
    *,
    subject: str,
    predicate: str,
    value: str,
    refs: Iterable[str],
    event_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    ordered_refs = sorted(set(refs))
    referenced = [event_by_id[event_id] for event_id in ordered_refs]
    sequences = [int(event["source_sequence"]) for event in referenced]
    return {
        "claim_id": _claim_id(subject, predicate, value),
        "conflict_set_id": _conflict_set_id(subject, predicate),
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "support": _round(sum(float(event["evidence_strength"]) for event in referenced)),
        "provenance_event_ids": ordered_refs,
        "source_episode_ids": sorted(
            {str(event["source_episode_id"]) for event in referenced}
        ),
        "first_seen_tick": min(sequences),
        "last_supported_tick": max(sequences),
    }


def _rebuild_canonical_claims(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_by_id = {str(event["event_id"]): event for event in events}
    groups: dict[tuple[str, str, str], list[str]] = {}
    for event in events:
        key = (str(event["subject"]), str(event["predicate"]), str(event["value"]))
        groups.setdefault(key, []).append(str(event["event_id"]))
    claims = [
        _claim_from_refs(
            subject=subject,
            predicate=predicate,
            value=value,
            refs=refs,
            event_by_id=event_by_id,
        )
        for (subject, predicate, value), refs in groups.items()
    ]
    claims.sort(key=lambda claim: (claim["conflict_set_id"], claim["value"], claim["claim_id"]))
    return claims


def record_outcome_evidence(
    memory: Mapping[str, Any],
    *,
    subject: str,
    predicate: str,
    value: str,
    evidence_strength: float,
    event_id: str,
    source_episode_id: str,
    source_command_hash: str,
    source_sequence: int,
    observed_public_features: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = ensure_claim_memory(memory)
    verify_claim_memory(updated)
    if any(event["event_id"] == event_id for event in updated["claim_events"]):
        raise ValueError("claim event_id already exists")
    event = {
        "schema_version": CLAIM_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "subject": subject,
        "predicate": predicate,
        "value": value,
        "evidence_strength": _round(evidence_strength),
        "source_episode_id": source_episode_id,
        "source_command_hash": source_command_hash,
        "source_sequence": source_sequence,
        "observed_public_features": deepcopy(dict(observed_public_features)),
    }
    candidate = deepcopy(updated)
    candidate["claim_events"].append(event)
    candidate["claim_events"].sort(
        key=lambda item: (int(item["source_sequence"]), str(item["event_id"]))
    )
    candidate["competing_claims"] = _rebuild_canonical_claims(candidate["claim_events"])
    verify_claim_memory(candidate)
    written_claim = next(
        claim
        for claim in candidate["competing_claims"]
        if claim["subject"] == subject
        and claim["predicate"] == predicate
        and claim["value"] == value
    )
    return candidate, {
        "applied": True,
        "producer_function": "ego_life_playground_v0.claims.record_outcome_evidence",
        "event_id": event_id,
        "claim_id": written_claim["claim_id"],
        "conflict_set_id": written_claim["conflict_set_id"],
        "support_after": written_claim["support"],
        "provenance_event_ids": deepcopy(written_claim["provenance_event_ids"]),
        "source_episode_ids": deepcopy(written_claim["source_episode_ids"]),
    }


def retrieve_competing_claims(
    memory: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    current_goal: str,
) -> dict[str, Any]:
    verify_claim_memory(memory)
    if not isinstance(observation, Mapping):
        raise ValueError("retrieval observation must be an object")
    _verify_public_features(observation)
    if type(current_goal) is not str or not current_goal:
        raise ValueError("retrieval current_goal must be a non-empty string")

    position = str(observation.get("agent_position", "unknown"))
    association = 1.0 if position == "fork" else 0.65
    retrieved: list[dict[str, Any]] = []
    for claim in memory["competing_claims"]:
        if claim["subject"] != "microworld:opaque_fork":
            continue
        item = deepcopy(claim)
        item["association_score"] = association
        item["retrieval_score"] = _round(float(claim["support"]) * association)
        retrieved.append(item)
    retrieved.sort(key=lambda item: (-float(item["retrieval_score"]), str(item["value"])))
    supports = [float(item["retrieval_score"]) for item in retrieved]
    refs = sorted(
        {event_id for item in retrieved for event_id in item["provenance_event_ids"]}
    )
    return {
        "schema_version": CLAIM_RETRIEVAL_SCHEMA_VERSION,
        "status": "retrieved" if retrieved else "no_matching_claims",
        "producer_function": "ego_life_playground_v0.claims.retrieve_competing_claims",
        "query": {
            "subject": "microworld:opaque_fork",
            "predicate": "preferred_site_action",
            "agent_position": position,
            "current_goal": current_goal,
        },
        "claims": retrieved,
        "support_by_action": {
            str(item["value"]): float(item["retrieval_score"]) for item in retrieved
        },
        "support_margin": _round(max(supports) - min(supports)) if len(supports) >= 2 else 0.0,
        "uncertainty": _round(1.0 / (1.0 + (max(supports) - min(supports))))
        if len(supports) >= 2
        else 1.0,
        "provenance_event_ids": refs,
        "source_episode_ids": sorted(
            {episode_id for item in retrieved for episode_id in item["source_episode_ids"]}
        ),
    }


def memory_bias_for_action(retrieval: Mapping[str, Any], action: str) -> float:
    # A single unsupported alternative is not a competing-claim comparison.
    # Keep it observable but behaviorally inert until at least two values in
    # the conflict set coexist.
    if len(retrieval.get("claims", [])) < 2:
        return 0.0
    supports = retrieval.get("support_by_action", {})
    raw = float(supports.get(action, 0.0)) * CLAIM_BIAS_COEFFICIENT
    return _round(max(-CLAIM_BIAS_CLIP, min(CLAIM_BIAS_CLIP, raw)))


def _claim_base(claim: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "support",
        "provenance_event_ids",
        "source_episode_ids",
        "first_seen_tick",
        "last_supported_tick",
    }
    return {key: deepcopy(value) for key, value in claim.items() if key not in excluded}


def _leaf_pointer_map(value: Any, path: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            result.update(_leaf_pointer_map(value[key], f"{path}/{key}"))
        return result
    if isinstance(value, list):
        if not value:
            return {path or "/": []}
        result: dict[str, Any] = {}
        for index, item in enumerate(value):
            result.update(_leaf_pointer_map(item, f"{path}/{index}"))
        return result
    return {path or "/": deepcopy(value)}


def _unaffected_field_hashes(
    before: Mapping[str, Any], after: Mapping[str, Any], changed: Iterable[str]
) -> tuple[str, str, int]:
    changed_set = set(changed)
    before_leaves = _leaf_pointer_map(before)
    after_leaves = _leaf_pointer_map(after)
    pointers = sorted(
        pointer
        for pointer in set(before_leaves) | set(after_leaves)
        if not any(pointer == changed_pointer or pointer.startswith(changed_pointer + "/") for changed_pointer in changed_set)
    )
    before_unaffected = {pointer: before_leaves.get(pointer) for pointer in pointers}
    after_unaffected = {pointer: after_leaves.get(pointer) for pointer in pointers}
    return (
        _canonical_hash(before_unaffected),
        _canonical_hash(after_unaffected),
        len(pointers),
    )


def shuffle_provenance(
    memory: Mapping[str, Any], *, seed: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = ensure_claim_memory(memory)
    verify_claim_memory(source)
    projected = deepcopy(source)
    claims = sorted(projected["competing_claims"], key=lambda item: str(item["claim_id"]))
    if len(claims) < 2:
        unchanged_hash = _canonical_hash(_leaf_pointer_map(source))
        return projected, {
            "status": "not_applied_insufficient_claims",
            "producer_function": "ego_life_playground_v0.claims.shuffle_provenance",
            "event_value_multiset_preserved": True,
            "non_provenance_claim_fields_preserved": True,
            "changed_json_pointers": [],
            "eligibility_count": len(claims),
            "seed": int(seed),
            "unaffected_fields_hash_before": unchanged_hash,
            "unaffected_fields_hash_after": unchanged_hash,
            "unaffected_field_count": len(_leaf_pointer_map(source)),
        }

    rotation = 1 + (abs(int(seed)) % (len(claims) - 1))
    original_refs = [deepcopy(claim["provenance_event_ids"]) for claim in claims]
    event_by_id = {str(event["event_id"]): event for event in projected["claim_events"]}
    changed: list[str] = []
    for index, claim in enumerate(claims):
        refs = original_refs[(index - rotation) % len(claims)]
        replacement = _claim_from_refs(
            subject=str(claim["subject"]),
            predicate=str(claim["predicate"]),
            value=str(claim["value"]),
            refs=refs,
            event_by_id=event_by_id,
        )
        target_index = projected["competing_claims"].index(claim)
        for field in (
            "support",
            "provenance_event_ids",
            "source_episode_ids",
            "first_seen_tick",
            "last_supported_tick",
        ):
            if projected["competing_claims"][target_index][field] != replacement[field]:
                changed.append(f"/competing_claims/{target_index}/{field}")
            projected["competing_claims"][target_index][field] = deepcopy(replacement[field])

    verify_claim_memory(projected)
    event_multiset_before = sorted(
        _canonical_hash(
            {
                "value": event["value"],
                "evidence_strength": event["evidence_strength"],
                "public": event["observed_public_features"],
            }
        )
        for event in source["claim_events"]
    )
    event_multiset_after = sorted(
        _canonical_hash(
            {
                "value": event["value"],
                "evidence_strength": event["evidence_strength"],
                "public": event["observed_public_features"],
            }
        )
        for event in projected["claim_events"]
    )
    before_bases = sorted((_claim_base(item) for item in source["competing_claims"]), key=_canonical_json)
    after_bases = sorted((_claim_base(item) for item in projected["competing_claims"]), key=_canonical_json)
    unaffected_before, unaffected_after, unaffected_count = _unaffected_field_hashes(
        source, projected, changed
    )
    return projected, {
        "status": "applied" if changed else "not_applied_identity",
        "producer_function": "ego_life_playground_v0.claims.shuffle_provenance",
        "seed": int(seed),
        "rotation": rotation,
        "eligibility_count": len(claims),
        "event_value_multiset_preserved": event_multiset_before == event_multiset_after,
        "non_provenance_claim_fields_preserved": before_bases == after_bases,
        "changed_json_pointers": sorted(changed),
        "source_memory_hash": _canonical_hash(source),
        "projected_memory_hash": _canonical_hash(projected),
        "unaffected_fields_hash_before": unaffected_before,
        "unaffected_fields_hash_after": unaffected_after,
        "unaffected_field_count": unaffected_count,
    }


def delete_sources(
    memory: Mapping[str, Any],
    *,
    event_ids: Iterable[str] = (),
    source_episode_ids: Iterable[str] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = ensure_claim_memory(memory)
    verify_claim_memory(source)
    event_targets = set(event_ids)
    episode_targets = set(source_episode_ids)
    kept: list[dict[str, Any]] = []
    deleted: list[str] = []
    for event in source["claim_events"]:
        if event["event_id"] in event_targets or event["source_episode_id"] in episode_targets:
            deleted.append(str(event["event_id"]))
        else:
            kept.append(deepcopy(event))
    updated = deepcopy(source)
    updated["claim_events"] = kept
    updated["competing_claims"] = _rebuild_canonical_claims(kept)
    verify_claim_memory(updated)
    return updated, {
        "status": "applied" if deleted else "not_applied_no_matching_source",
        "producer_function": "ego_life_playground_v0.claims.delete_sources",
        "requested_event_ids": sorted(event_targets),
        "requested_source_episode_ids": sorted(episode_targets),
        "deleted_event_ids": sorted(deleted),
        "before_memory_hash": _canonical_hash(source),
        "after_memory_hash": _canonical_hash(updated),
    }


__all__ = [
    "CLAIM_BIAS_CLIP",
    "CLAIM_BIAS_COEFFICIENT",
    "CLAIM_EVENT_SCHEMA_VERSION",
    "CLAIM_MEMORY_SCHEMA_VERSION",
    "CLAIM_RETRIEVAL_SCHEMA_VERSION",
    "delete_sources",
    "empty_claim_memory",
    "ensure_claim_memory",
    "memory_bias_for_action",
    "record_outcome_evidence",
    "retrieve_competing_claims",
    "shuffle_provenance",
    "verify_claim_memory",
]
