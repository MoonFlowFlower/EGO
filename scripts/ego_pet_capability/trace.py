from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from scripts.ego_pet.creature import _best_site


def best_sites(model: dict[str, dict[str, float]]) -> dict[str, str]:
    return {
        "energy": _best_site(model, "energy"),
        "comfort": _best_site(model, "comfort"),
    }


def build_capability_trace_row(
    *,
    state_before_hash: str,
    state_after_hash: str,
    seed_context: dict[str, Any],
    tick_index: int,
    needs: dict[str, Any],
    observation: dict[str, Any],
    action: dict[str, Any],
    feedback: dict[str, Any],
    model_before: dict[str, dict[str, float]],
    model_after: dict[str, dict[str, float]],
    channel: str,
    pair_id: str,
    intervention_tick: int,
    arm: str,
    seed: int,
    variant: str,
    event_id: str,
    event_kind: str,
    intervention_applied: bool,
    attribution: dict[str, Any],
) -> dict[str, Any]:
    before_best = best_sites(model_before)
    after_best = best_sites(model_after)
    return {
        "tick_index": int(tick_index),
        "needs": needs,
        "observation": observation,
        "action": action,
        "feedback": feedback,
        "model_before": model_before,
        "model_after": model_after,
        "channel": str(channel),
        "best_site_energy": before_best["energy"],
        "best_site_comfort": before_best["comfort"],
        "best_site_after_energy": after_best["energy"],
        "best_site_after_comfort": after_best["comfort"],
        "pair_id": pair_id,
        "intervention_tick": int(intervention_tick),
        "arm": arm,
        "seed": int(seed),
        "variant": variant,
        "event_id": event_id,
        "event_kind": event_kind,
        "intervention_applied": bool(intervention_applied),
        "state_before_hash": state_before_hash,
        "state_after_hash": state_after_hash,
        "seed_context": seed_context,
        "component_attribution": attribution,
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

