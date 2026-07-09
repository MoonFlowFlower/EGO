from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from scripts.ego_kernel.state import KernelState, canonical_sha256, deep_copy
from scripts.ego_pet.creature import _best_site, select_action, update_creature_after_feedback, zero_creature_state
from scripts.ego_pet.world import (
    WORLD_CONFIG_PATH,
    advance_world,
    build_observation,
    load_world_config,
    regime_for_tick,
    site_yields_for_tick,
    zero_world_state,
)
from scripts.ego_pet_capability import CLAIM_CEILING, RUN_ID_BASE, TASK_ID
from scripts.ego_pet_capability.trace import build_capability_trace_row, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / TASK_ID
STAGE_CARD_PATH = TASK_DIR / "STAGE_CARD.md"
PREREG_PATH = TASK_DIR / "PREREG_ADDENDUM_001.md"
MUTATION_SCOPE_PATH = TASK_DIR / "MUTATION_SCOPE.yaml"
ARTIFACT_ROOT = ROOT / "artifacts" / TASK_ID

PROBE_SEED = 1101
S_DEV_RESERVED = set(range(1101, 1106))
P0_SCORED_RESERVED = set(range(2101, 2121))
SCORED_SEEDS = list(range(3101, 3121))
ARMS = ("candidate", "frozen_updates", "static", "candidate_ablated")
VARIANTS = ("A", "B", "C")
NEEDS = ("energy", "comfort")
HORIZON = 50


def jcopy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def canonical_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def code_path_hash(repo_root: Path = ROOT) -> str:
    rels = [
        "scripts/ego_pet_capability/__init__.py",
        "scripts/ego_pet_capability/feedback_to_behavior.py",
        "scripts/ego_pet_capability/trace.py",
        "scripts/ego_pet/creature.py",
        "scripts/ego_pet/world.py",
        "scripts/ego_kernel/state.py",
        "scripts/ego_kernel/tick.py",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/STAGE_CARD.md",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/PREREG_ADDENDUM_001.md",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/MUTATION_SCOPE.yaml",
        "docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json",
    ]
    digest = hashlib.sha256()
    for rel in rels:
        path = repo_root / rel
        digest.update(rel.encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
    return digest.hexdigest()


def config_shas() -> dict[str, str]:
    return {
        "world_config_v0.json": sha256_file(WORLD_CONFIG_PATH),
        "STAGE_CARD.md": sha256_file(STAGE_CARD_PATH),
        "PREREG_ADDENDUM_001.md": sha256_file(PREREG_PATH),
        "MUTATION_SCOPE.yaml": sha256_file(MUTATION_SCOPE_PATH),
    }


@dataclass(frozen=True)
class InterventionEvent:
    event_id: str
    seed: int
    tick_index: int
    regime_index: int
    regime_id: str
    event_kind: str
    action_type: str
    need: str | None
    site: str | None
    injected_regime_index: int
    injected_regime_id: str
    channel: str
    gate_scope: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterventionEvent":
        return cls(
            event_id=str(payload["event_id"]),
            seed=int(payload["seed"]),
            tick_index=int(payload["tick_index"]),
            regime_index=int(payload["regime_index"]),
            regime_id=str(payload["regime_id"]),
            event_kind=str(payload["event_kind"]),
            action_type=str(payload["action_type"]),
            need=None if payload.get("need") is None else str(payload.get("need")),
            site=None if payload.get("site") is None else str(payload.get("site")),
            injected_regime_index=int(payload["injected_regime_index"]),
            injected_regime_id=str(payload["injected_regime_id"]),
            channel=str(payload["channel"]),
            gate_scope=str(payload["gate_scope"]),
        )


def _policy_arm(arm: str) -> str:
    return "candidate" if arm == "candidate_ablated" else arm


def _updates_enabled(arm: str) -> bool:
    return arm == "candidate"


def _initial_state(config: dict[str, Any], *, seed: int, arm: str, run_id: str, episode_id: str) -> KernelState:
    policy_arm = _policy_arm(arm)
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=0,
        substates={
            "pet_world_v0": zero_world_state(config),
            "pet_creature_v0": zero_creature_state(config, arm=policy_arm),
            "run_context": {"arm": arm, "policy_arm": policy_arm, "capability_conformance": True},
        },
        seed_registry={"pet_policy": {"seed": int(seed), "draws": 0}},
        ablations={"pet_creature_v0": "frozen" if not _updates_enabled(arm) else "live"},
    )


def _derived_designations(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    designations: dict[str, dict[str, str]] = {}
    for regime in config["regimes"]:
        rid = str(regime["regime_id"])
        energy = _best_site(regime["site_yields"], "energy")
        comfort = _best_site(regime["site_yields"], "comfort")
        if energy != str(regime["energy_best_site"]):
            raise ValueError(f"derived energy best-site mismatch for {rid}: {energy} != {regime['energy_best_site']}")
        if comfort != str(regime["comfort_best_site"]):
            raise ValueError(f"derived comfort best-site mismatch for {rid}: {comfort} != {regime['comfort_best_site']}")
        designations[rid] = {"energy": energy, "comfort": comfort}
    return designations


def _injected_regime_index(config: dict[str, Any], regime_index: int) -> int:
    return (int(regime_index) + 1) % len(config["regimes"])


def assert_seed_disjointness(seeds: list[int]) -> None:
    seed_set = set(int(seed) for seed in seeds)
    if seed_set & S_DEV_RESERVED:
        raise ValueError(f"seed-disjointness assertion failed vs S_dev reserved: {sorted(seed_set & S_DEV_RESERVED)}")
    if seed_set & P0_SCORED_RESERVED:
        raise ValueError(f"seed-disjointness assertion failed vs prior P0 S_scored reserved: {sorted(seed_set & P0_SCORED_RESERVED)}")


def validate_prereg_inputs(config: dict[str, Any], *, phase: str, seeds: list[int]) -> dict[str, Any]:
    if int(config["time"]["episode_length_ticks"]) != 600:
        raise ValueError("frozen episode length mismatch")
    if int(config["time"]["window_W_ticks"]) != HORIZON:
        raise ValueError("frozen persistence horizon mismatch")
    designations = _derived_designations(config)
    if phase == "scored":
        assert_seed_disjointness(seeds)
        if seeds != SCORED_SEEDS:
            raise ValueError("scored seed list differs from frozen 3101..3120 block")
    if phase == "probe" and seeds != [PROBE_SEED]:
        raise ValueError("probe seed differs from frozen 1101")
    return {
        "producer_function": "validate_prereg_inputs",
        "phase": phase,
        "seed_ids": seeds,
        "designated_best_sites_derived_from_config": designations,
        "seed_disjointness_asserted": phase == "scored",
        "status": "pass",
    }


def _channel_for_update(action: dict[str, Any], feedback: dict[str, Any], *, updates_enabled: bool) -> str:
    if not updates_enabled:
        return "none"
    if action.get("action_type") == "observe" and feedback.get("observed_site_yields"):
        return "observe"
    if action.get("site"):
        return "forage"
    return "none"


def _directional_forage_yield(
    config: dict[str, Any],
    creature_before: dict[str, Any],
    site: str,
    need: str,
) -> dict[str, float]:
    model = jcopy(creature_before["model"])
    other = "comfort" if need == "energy" else "energy"
    best_other_value = max(float(values[need]) + 0.25 * float(values[other]) for values in model.values())
    lifted = min(1.0, round(best_other_value + 0.05, 12))
    current_other = float(model[site][other])
    if need == "energy":
        return {"energy": lifted, "comfort": round(current_other, 12)}
    return {"energy": round(current_other, 12), "comfort": lifted}


def apply_feedback_variant(
    *,
    config: dict[str, Any],
    event: InterventionEvent | None,
    variant: str,
    action: dict[str, Any],
    feedback: dict[str, Any],
    creature_before: dict[str, Any],
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    modified = jcopy(feedback)
    if event is None or variant == "A":
        return modified, False, {"variant": variant, "intervention": "none"}
    if int(feedback["tick_index"]) != int(event.tick_index):
        return modified, False, {"variant": variant, "intervention": "not_at_event_tick"}
    action_type = str(action.get("action_type"))
    if event.event_kind == "observe":
        if action_type != "observe":
            return modified, False, {"variant": variant, "intervention": "event_action_mismatch"}
        if variant == "B":
            modified["observed_site_yields"] = None
            return modified, True, {"variant": variant, "intervention": "observe_withhold"}
        if variant == "C":
            source_tick = int(config["regimes"][event.injected_regime_index]["tick_range"][0])
            modified["observed_site_yields"] = site_yields_for_tick(config, source_tick)
            return modified, True, {
                "variant": variant,
                "intervention": "observe_directional_regime_snapshot",
                "injected_regime_id": event.injected_regime_id,
            }
    if event.event_kind == "forage":
        if action_type != event.action_type or not action.get("site"):
            return modified, False, {"variant": variant, "intervention": "event_action_mismatch"}
        site = str(action["site"])
        if variant == "B":
            modified["action_yield"] = jcopy(creature_before["model"][site])
            return modified, True, {"variant": variant, "intervention": "forage_prior_value"}
        if variant == "C":
            need = event.need or ("energy" if action_type == "forage_energy" else "comfort")
            modified["action_yield"] = _directional_forage_yield(config, creature_before, site, need)
            return modified, True, {
                "variant": variant,
                "intervention": "forage_directional_visited_site_lift",
                "need": need,
            }
    raise ValueError(f"unsupported variant: {variant}")


def run_step(
    *,
    state: KernelState,
    config: dict[str, Any],
    arm: str,
    seed: int,
    variant: str,
    event: InterventionEvent | None,
    pair_id: str,
) -> tuple[KernelState, dict[str, Any]]:
    state_before = state
    world_state = deep_copy(state.substates["pet_world_v0"])
    observation = build_observation(world_state, config, None)
    action, working_state, attribution = select_action(state, observation, config, arm=_policy_arm(arm))
    world_after, true_feedback = advance_world(world_state, action, config)
    creature_before = deep_copy(working_state.substates["pet_creature_v0"])
    feedback, intervention_applied, intervention_meta = apply_feedback_variant(
        config=config,
        event=event,
        variant=variant,
        action=action,
        feedback=true_feedback,
        creature_before=creature_before,
    )
    updates_enabled = _updates_enabled(arm)
    creature_after = update_creature_after_feedback(creature_before, action, feedback, updates_enabled=updates_enabled)
    state_after = working_state.with_updates(
        step_id=working_state.step_id + 1,
        substates={"pet_world_v0": world_after, "pet_creature_v0": creature_after},
    )
    channel = _channel_for_update(action, feedback, updates_enabled=updates_enabled)
    row = build_capability_trace_row(
        state_before_hash=state_before.state_hash(),
        state_after_hash=state_after.state_hash(),
        seed_context=state_after.seed_context(),
        tick_index=int(observation["tick_index"]),
        needs=jcopy(observation["needs"]),
        observation=observation,
        action=action,
        feedback=feedback,
        model_before=creature_before["model"],
        model_after=creature_after["model"],
        channel=channel,
        pair_id=pair_id,
        intervention_tick=-1 if event is None else event.tick_index,
        arm=arm,
        seed=seed,
        variant=variant,
        event_id="baseline" if event is None else event.event_id,
        event_kind="baseline" if event is None else event.event_kind,
        intervention_applied=intervention_applied,
    )
    return state_after, row


def run_baseline(config: dict[str, Any], *, seed: int, arm: str, run_id: str) -> dict[str, Any]:
    state = _initial_state(config, seed=seed, arm=arm, run_id=run_id, episode_id=f"baseline_{arm}_{seed}")
    pre_states: dict[int, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for _ in range(int(config["time"]["episode_length_ticks"])):
        tick = int(state.substates["pet_world_v0"]["tick_index"])
        pre_states[tick] = state.to_dict()
        state, row = run_step(
            state=state,
            config=config,
            arm=arm,
            seed=seed,
            variant="A",
            event=None,
            pair_id=f"baseline:{arm}:{seed}",
        )
        rows.append(row)
    return {"pre_states": pre_states, "trace_rows": rows, "final_state": state.to_dict()}


def select_candidate_events(config: dict[str, Any], *, seed: int, candidate_rows: list[dict[str, Any]]) -> list[InterventionEvent]:
    events: list[InterventionEvent] = []
    observe_by_regime: dict[int, dict[str, Any]] = {}
    forage_by_regime_need: dict[tuple[int, str], dict[str, Any]] = {}
    for row in candidate_rows:
        tick = int(row["tick_index"])
        regime = regime_for_tick(config, tick)
        regime_index = list(config["regimes"]).index(regime)
        action = row["action"]
        action_type = str(action.get("action_type"))
        if action_type == "observe" and regime_index not in observe_by_regime:
            observe_by_regime[regime_index] = row
        if action_type in {"forage_energy", "seek_comfort"}:
            need = "energy" if action_type == "forage_energy" else "comfort"
            key = (regime_index, need)
            if key not in forage_by_regime_need:
                forage_by_regime_need[key] = row
    for regime_index in range(len(config["regimes"])):
        if regime_index not in observe_by_regime:
            raise ValueError(f"missing candidate observe event in regime index {regime_index}")
        row = observe_by_regime[regime_index]
        injected_index = _injected_regime_index(config, regime_index)
        events.append(
            InterventionEvent(
                event_id=f"seed_{seed}:observe:R{regime_index}:tick_{row['tick_index']}",
                seed=seed,
                tick_index=int(row["tick_index"]),
                regime_index=regime_index,
                regime_id=str(config["regimes"][regime_index]["regime_id"]),
                event_kind="observe",
                action_type="observe",
                need=None,
                site=None,
                injected_regime_index=injected_index,
                injected_regime_id=str(config["regimes"][injected_index]["regime_id"]),
                channel="observe",
                gate_scope="r0_should_lose" if regime_index == 0 else "post_drift_observe",
            )
        )
    for regime_index in range(len(config["regimes"])):
        for need in NEEDS:
            key = (regime_index, need)
            if key not in forage_by_regime_need:
                raise ValueError(f"missing candidate first forage event for regime index {regime_index} need {need}")
            row = forage_by_regime_need[key]
            injected_index = _injected_regime_index(config, regime_index)
            events.append(
                InterventionEvent(
                    event_id=f"seed_{seed}:forage:{need}:R{regime_index}:tick_{row['tick_index']}",
                    seed=seed,
                    tick_index=int(row["tick_index"]),
                    regime_index=regime_index,
                    regime_id=str(config["regimes"][regime_index]["regime_id"]),
                    event_kind="forage",
                    action_type="forage_energy" if need == "energy" else "seek_comfort",
                    need=need,
                    site=None if row["action"].get("site") is None else str(row["action"].get("site")),
                    injected_regime_index=injected_index,
                    injected_regime_id=str(config["regimes"][injected_index]["regime_id"]),
                    channel="forage",
                    gate_scope="forage_diagnostic",
                )
            )
    return events


def _clone_state_for_pair(state_payload: dict[str, Any], *, run_id: str, episode_id: str) -> KernelState:
    state = KernelState.from_dict(state_payload)
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=state.step_id,
        substates=deep_copy(state.substates),
        seed_registry=deep_copy(state.seed_registry),
        ablations=deep_copy(state.ablations),
    )


def run_variant_from_state(
    *,
    config: dict[str, Any],
    state_payload: dict[str, Any],
    arm: str,
    seed: int,
    event: InterventionEvent,
    variant: str,
    run_id: str,
) -> dict[str, Any]:
    pair_id = f"{event.event_id}:{arm}:{variant}"
    state = _clone_state_for_pair(state_payload, run_id=run_id, episode_id=pair_id.replace(":", "_"))
    rows: list[dict[str, Any]] = []
    max_tick = min(int(config["time"]["episode_length_ticks"]) - 1, int(event.tick_index) + HORIZON)
    while int(state.substates["pet_world_v0"]["tick_index"]) <= max_tick:
        current_tick = int(state.substates["pet_world_v0"]["tick_index"])
        current_event = event if current_tick == int(event.tick_index) else None
        state, row = run_step(
            state=state,
            config=config,
            arm=arm,
            seed=seed,
            variant=variant if current_event else "A",
            event=current_event,
            pair_id=pair_id,
        )
        rows.append(row)
    return {
        "pair_id": pair_id,
        "arm": arm,
        "seed": int(seed),
        "variant": variant,
        "event": asdict(event),
        "initial_state": state_payload,
        "trace_rows": rows,
        "final_state": state.to_dict(),
    }


def _rows_by_tick(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["tick_index"]): row for row in rows}


def _best_before(row: dict[str, Any], need: str) -> str:
    return str(row[f"best_site_{need}"])


def _next_overwrite_effect_tick(rows: list[dict[str, Any]], *, start_tick: int, relevant_sites: set[str]) -> int | None:
    for row in rows:
        tick = int(row["tick_index"])
        if tick <= int(start_tick):
            continue
        if row.get("channel") == "observe":
            return tick + 1
        if row.get("channel") == "forage" and str(row.get("action", {}).get("site")) in relevant_sites:
            return tick + 1
    return None


def _window_ticks_for_ab(
    *,
    event: InterventionEvent,
    need: str,
    variant_rows: dict[str, list[dict[str, Any]]],
) -> list[int]:
    a_by_tick = _rows_by_tick(variant_rows["A"])
    b_by_tick = _rows_by_tick(variant_rows["B"])
    first_tick = int(event.tick_index) + 1
    if first_tick not in a_by_tick or first_tick not in b_by_tick:
        return []
    relevant = {_best_before(a_by_tick[first_tick], need), _best_before(b_by_tick[first_tick], need)}
    effect_ticks = [
        value
        for value in (
            _next_overwrite_effect_tick(variant_rows["A"], start_tick=event.tick_index, relevant_sites=relevant),
            _next_overwrite_effect_tick(variant_rows["B"], start_tick=event.tick_index, relevant_sites=relevant),
        )
        if value is not None
    ]
    end = min(int(event.tick_index) + HORIZON, *(tick - 1 for tick in effect_ticks)) if effect_ticks else int(event.tick_index) + HORIZON
    return [tick for tick in range(first_tick, end + 1) if tick in a_by_tick and tick in b_by_tick]


def _window_ticks_for_c(
    *,
    config: dict[str, Any],
    event: InterventionEvent,
    need: str,
    variant_rows: dict[str, list[dict[str, Any]]],
) -> tuple[list[int], str]:
    c_by_tick = _rows_by_tick(variant_rows["C"])
    first_tick = int(event.tick_index) + 1
    if first_tick not in c_by_tick:
        return [], str(config["regimes"][event.injected_regime_index][f"{need}_best_site"])
    target = str(config["regimes"][event.injected_regime_index][f"{need}_best_site"])
    effect_tick = _next_overwrite_effect_tick(variant_rows["C"], start_tick=event.tick_index, relevant_sites={target})
    end = min(int(event.tick_index) + HORIZON, effect_tick - 1) if effect_tick is not None else int(event.tick_index) + HORIZON
    return [tick for tick in range(first_tick, end + 1) if tick in c_by_tick], target


def _rate(numer: int, denom: int) -> float:
    return round(float(numer) / float(denom), 12) if denom else 0.0


def metric_records_for_event(
    *,
    config: dict[str, Any],
    arm: str,
    event: InterventionEvent,
    variant_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    needs = NEEDS if event.event_kind == "observe" else (str(event.need),)
    for need in needs:
        ab_ticks = _window_ticks_for_ab(event=event, need=need, variant_rows=variant_rows)
        a_by_tick = _rows_by_tick(variant_rows["A"])
        b_by_tick = _rows_by_tick(variant_rows["B"])
        ab_divergences = [
            {
                "tick_index": tick,
                "a_best": _best_before(a_by_tick[tick], need),
                "b_best": _best_before(b_by_tick[tick], need),
            }
            for tick in ab_ticks
            if _best_before(a_by_tick[tick], need) != _best_before(b_by_tick[tick], need)
        ]
        c_ticks, target = _window_ticks_for_c(config=config, event=event, need=need, variant_rows=variant_rows)
        c_by_tick = _rows_by_tick(variant_rows["C"])
        c_matches = [
            {"tick_index": tick, "c_best": _best_before(c_by_tick[tick], need), "target": target}
            for tick in c_ticks
            if _best_before(c_by_tick[tick], need) == target
        ]
        records.append(
            {
                "producer_function": "metric_records_for_event",
                "event_id": event.event_id,
                "seed": int(event.seed),
                "arm": arm,
                "event_kind": event.event_kind,
                "channel": event.channel,
                "regime_id": event.regime_id,
                "regime_index": event.regime_index,
                "gate_scope": event.gate_scope,
                "need": need,
                "intervention_tick": event.tick_index,
                "ab_window_ticks": ab_ticks,
                "ab_window_len": len(ab_ticks),
                "ab_divergence_count": len(ab_divergences),
                "ab_divergence_rate": _rate(len(ab_divergences), len(ab_ticks)),
                "ab_divergences": ab_divergences[:10],
                "c_window_ticks": c_ticks,
                "c_window_len": len(c_ticks),
                "c_target_site": target,
                "c_directional_match_count": len(c_matches),
                "c_directional_rate": _rate(len(c_matches), len(c_ticks)),
                "c_matches": c_matches[:10],
            }
        )
    return records


def run_pair_bundle_for_seed(config: dict[str, Any], *, seed: int, run_id: str) -> dict[str, Any]:
    baselines = {arm: run_baseline(config, seed=seed, arm=arm, run_id=run_id) for arm in ARMS}
    events = select_candidate_events(config, seed=seed, candidate_rows=baselines["candidate"]["trace_rows"])
    pair_runs: list[dict[str, Any]] = []
    metric_records: list[dict[str, Any]] = []
    for event in events:
        for arm in ARMS:
            state_payload = baselines[arm]["pre_states"][int(event.tick_index)]
            variants = {
                variant: run_variant_from_state(
                    config=config,
                    state_payload=state_payload,
                    arm=arm,
                    seed=seed,
                    event=event,
                    variant=variant,
                    run_id=run_id,
                )
                for variant in VARIANTS
            }
            pair_runs.extend(variants.values())
            metric_records.extend(
                metric_records_for_event(
                    config=config,
                    arm=arm,
                    event=event,
                    variant_rows={variant: variants[variant]["trace_rows"] for variant in VARIANTS},
                )
            )
    return {"baselines": baselines, "events": [asdict(event) for event in events], "pair_runs": pair_runs, "metric_records": metric_records}


def _aggregate_ab(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(record["ab_window_len"]) for record in records)
    div = sum(int(record["ab_divergence_count"]) for record in records)
    return {"divergent": div, "total": total, "rate": _rate(div, total)}


def _aggregate_c(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(record["c_window_len"]) for record in records)
    match = sum(int(record["c_directional_match_count"]) for record in records)
    return {"matches": match, "total": total, "rate": _rate(match, total)}


def baseline_comparison_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    post_observe = [r for r in metric_records if r["event_kind"] == "observe" and r["gate_scope"] == "post_drift_observe"]
    r0_observe = [r for r in metric_records if r["event_kind"] == "observe" and r["gate_scope"] == "r0_should_lose"]
    by_arm: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arm_post = [r for r in post_observe if r["arm"] == arm]
        arm_r0 = [r for r in r0_observe if r["arm"] == arm]
        by_arm[arm] = {
            "post_drift_observe_G_A": _aggregate_ab(arm_post),
            "post_drift_observe_G_B": _aggregate_c(arm_post),
            "r0_initial_observe_should_lose_G_A": _aggregate_ab(arm_r0),
        }
    candidate_ga = by_arm["candidate"]["post_drift_observe_G_A"]["rate"]
    frozen_ga = by_arm["frozen_updates"]["post_drift_observe_G_A"]["rate"]
    static_ga = by_arm["static"]["post_drift_observe_G_A"]["rate"]
    r0_candidate = by_arm["candidate"]["r0_initial_observe_should_lose_G_A"]["rate"]
    candidate_gb = by_arm["candidate"]["post_drift_observe_G_B"]["rate"]
    return {
        "producer_function": "baseline_comparison_report",
        "input_artifacts": ["trace.jsonl", "world_config_v0.json", "PREREG_ADDENDUM_001.md"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"{arm}:{seed}" for arm in ARMS for seed in seeds],
        "aggregation_rule": "G-A/G-B over post-drift observe-intervention metric windows; primary metric is _best_site(model_before, need)",
        "code_path_hash": code_hash,
        "gate": "G-A/G-B",
        "thresholds": {
            "G_A_candidate_min": 0.60,
            "G_A_controls_required": 0.0,
            "G_A_R0_candidate_max": 0.05,
            "G_B_candidate_min": 0.80,
            "G_B_controls_expected_max": 0.20,
        },
        "by_arm": by_arm,
        "G_A_status": "pass" if candidate_ga >= 0.60 and frozen_ga == 0.0 and static_ga == 0.0 and r0_candidate <= 0.05 else "fail",
        "G_B_status": "pass" if candidate_gb >= 0.80 else "fail",
        "status": "pass" if candidate_ga >= 0.60 and frozen_ga == 0.0 and static_ga == 0.0 and r0_candidate <= 0.05 and candidate_gb >= 0.80 else "fail",
    }


def ablation_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    post_ablation = [
        r
        for r in metric_records
        if r["arm"] == "candidate_ablated" and r["event_kind"] == "observe" and r["gate_scope"] == "post_drift_observe"
    ]
    ga = _aggregate_ab(post_ablation)
    gb = _aggregate_c(post_ablation)
    status = "pass" if ga["rate"] <= 0.02 and gb["rate"] <= 0.25 else "fail"
    return {
        "producer_function": "ablation_report",
        "input_artifacts": ["baseline_comparison.json", "trace.jsonl"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"candidate_ablated:{seed}" for seed in seeds],
        "aggregation_rule": "candidate_ablated observe-intervention G-A <= 0.02 and G-B <= 0.25",
        "code_path_hash": code_hash,
        "gate": "G-C",
        "candidate_ablated_G_A": ga,
        "candidate_ablated_G_B": gb,
        "status": status,
    }


def channel_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    nonzero_records = [r for r in metric_records if int(r["ab_divergence_count"]) > 0 or int(r["c_directional_match_count"]) > 0]
    invalid = [r for r in nonzero_records if r.get("channel") not in {"observe", "forage"}]
    split: dict[str, int] = {"observe": 0, "forage": 0}
    for record in nonzero_records:
        channel = str(record.get("channel"))
        if channel in split:
            split[channel] += int(record["ab_divergence_count"]) + int(record["c_directional_match_count"])
    total = sum(split.values())
    return {
        "producer_function": "channel_report",
        "input_artifacts": ["trace.jsonl"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"{arm}:{seed}" for arm in ARMS for seed in seeds],
        "aggregation_rule": "all nonzero divergence/directional records must map to disclosed C-observe or C-forage channel",
        "code_path_hash": code_hash,
        "gate": "G-E",
        "nonzero_record_count": len(nonzero_records),
        "invalid_channel_records": invalid[:20],
        "channel_split_counts": split,
        "channel_split_rates": {key: _rate(value, total) for key, value in split.items()},
        "status": "pass" if not invalid and bool(nonzero_records) else "fail",
    }


def _trace_digest(pair_runs: list[dict[str, Any]]) -> dict[str, Any]:
    digest = hashlib.sha256()
    row_count = 0
    for run in sorted(pair_runs, key=lambda item: str(item["pair_id"])):
        for row in run["trace_rows"]:
            digest.update(canonical_dumps(row).encode("utf-8"))
            digest.update(b"\n")
            row_count += 1
    return {"row_count": row_count, "sha256": digest.hexdigest()}


def _replay_payload(pair_runs: list[dict[str, Any]], *, run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "pairs": [
            {
                "initial_state": run["initial_state"],
                "event": run["event"],
                "arm": run["arm"],
                "seed": run["seed"],
                "variant": run["variant"],
            }
            for run in pair_runs
        ],
    }


def replay_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    config = load_world_config()
    pair_runs = [
        run_variant_from_state(
            config=config,
            state_payload=pair["initial_state"],
            arm=str(pair["arm"]),
            seed=int(pair["seed"]),
            event=InterventionEvent.from_dict(pair["event"]),
            variant=str(pair["variant"]),
            run_id=str(payload["run_id"]),
        )
        for pair in payload["pairs"]
    ]
    return {"trace_digest": _trace_digest(pair_runs), "pair_count": len(pair_runs)}


def replay_report(pair_runs: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int], repo_root: Path = ROOT) -> dict[str, Any]:
    expected = {"trace_digest": _trace_digest(pair_runs), "pair_count": len(pair_runs)}
    payload = _replay_payload(pair_runs, run_id=run_id)
    mismatches: list[dict[str, Any]] = []
    for fresh_index in range(2):
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.ego_pet_capability.feedback_to_behavior", "--replay-stdin"],
            cwd=str(repo_root),
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            mismatches.append({"fresh_index": fresh_index, "kind": "subprocess_error", "stderr": completed.stderr[-1000:]})
            continue
        actual = json.loads(completed.stdout)
        if actual != expected:
            mismatches.append({"fresh_index": fresh_index, "kind": "digest_mismatch", "expected": expected, "actual": actual})
    return {
        "producer_function": "replay_report",
        "input_artifacts": ["serialized pair initial_state + event + variant payload", "trace.jsonl"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [str(run["pair_id"]) for run in pair_runs],
        "aggregation_rule": "fresh subprocess replay x2 recomputes every pair from serialized_state + event observation protocol; compare canonical trace digest",
        "code_path_hash": code_hash,
        "gate": "G-D",
        "fresh_subprocess_runs": 2,
        "pair_count": len(pair_runs),
        "expected": expected,
        "mismatches_total": len(mismatches),
        "mismatches": mismatches,
        "status": "pass" if not mismatches else "fail",
    }


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def rng_usage_hits(path: Path) -> list[dict[str, Any]]:
    label = _rel(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[dict[str, Any]] = []
    rng_modules = {"numpy", "torch", "random", "secrets"}
    call_prefixes = ("numpy.random.", "np.random.", "random.", "secrets.", "torch.rand")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = str(alias.name).split(".", 1)[0]
                if root in rng_modules:
                    hits.append({"file": label, "kind": "rng_framework_import", "token": alias.name, "lineno": int(node.lineno)})
        elif isinstance(node, ast.ImportFrom):
            root = str(node.module or "").split(".", 1)[0]
            if root in rng_modules:
                hits.append({"file": label, "kind": "rng_framework_import", "token": str(node.module), "lineno": int(node.lineno)})
        elif isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if any(name.startswith(prefix) for prefix in call_prefixes) or name == "hash":
                hits.append({"file": label, "kind": "rng_or_hash_call_site", "token": name, "lineno": int(node.lineno)})
    return hits


def rng_audit(*, code_hash: str, run_id: str, scan_files: list[Path] | None = None) -> dict[str, Any]:
    files = scan_files or sorted((ROOT / "scripts" / "ego_pet_capability").glob("*.py"))
    hits: list[dict[str, Any]] = []
    for path in files:
        hits.extend(rng_usage_hits(path))
    return {
        "producer_function": "rng_audit",
        "input_artifacts": [_rel(path) for path in files],
        "run_id": run_id,
        "seed_ids": [],
        "episode_ids": [],
        "aggregation_rule": "AST-level audit for RNG framework imports/calls and builtin hash() in capability harness files",
        "code_path_hash": code_hash,
        "forbidden_hits": hits,
        "positive_control": "tests/test_feedback_to_behavior.py::test_rng_audit_positive_control_detects_forbidden_random",
        "status": "pass" if not hits else "fail",
    }


def choose_verdict(baseline: dict[str, Any], ablation: dict[str, Any], replay: dict[str, Any], channel: dict[str, Any], rng: dict[str, Any]) -> tuple[str, list[str]]:
    failing: list[str] = []
    if replay.get("status") != "pass":
        failing.append("G-D")
    if channel.get("status") != "pass":
        failing.append("G-E")
    if rng.get("status") != "pass":
        failing.append("UNSEEDED-RNG-AUDIT")
    by_arm = baseline["by_arm"]
    if by_arm["candidate"]["r0_initial_observe_should_lose_G_A"]["rate"] > 0.05:
        failing.append("R0_SHOULD_LOSE_LEAK")
    if by_arm["frozen_updates"]["post_drift_observe_G_A"]["rate"] != 0.0:
        failing.append("FROZEN_UPDATES_CONTROL_CONTAMINATION")
    if by_arm["static"]["post_drift_observe_G_A"]["rate"] != 0.0:
        failing.append("STATIC_CONTROL_CONTAMINATION")
    if failing:
        return "INSTRUMENT_INVALID", failing
    if baseline["G_A_status"] != "pass":
        return "CAPABILITY_ABSENT", ["G-A"]
    if baseline["G_B_status"] != "pass":
        return "PERTURBATION_ONLY_NONDIRECTIONAL", ["G-B"]
    if ablation.get("status") != "pass":
        return "INSTRUMENT_INVALID", ["G-C"]
    return "CAPABILITY_PRESENT_CHANNEL_DISCLOSED", []


def flatten_pair_trace(pair_runs: list[dict[str, Any]], *, gate_only: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in sorted(pair_runs, key=lambda item: str(item["pair_id"])):
        if gate_only and str(run["event"].get("event_kind")) != "observe":
            continue
        rows.extend(run["trace_rows"])
    return rows


def run_phase(
    *,
    phase: str,
    out_dir: Path | None = None,
    include_replay: bool = True,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    started = time.process_time()
    config = load_world_config()
    seeds = [PROBE_SEED] if phase == "probe" else list(SCORED_SEEDS)
    run_id = f"{RUN_ID_BASE}_{phase}"
    prereg = validate_prereg_inputs(config, phase=phase, seeds=seeds)
    code_hash = code_path_hash()
    bundles = [run_pair_bundle_for_seed(config, seed=seed, run_id=run_id) for seed in seeds]
    pair_runs = [run for bundle in bundles for run in bundle["pair_runs"]]
    metric_records = [record for bundle in bundles for record in bundle["metric_records"]]
    events = [event for bundle in bundles for event in bundle["events"]]
    baseline = baseline_comparison_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    ablation = ablation_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    channel = channel_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    rng = rng_audit(code_hash=code_hash, run_id=run_id)
    replay = (
        replay_report(pair_runs, run_id=run_id, code_hash=code_hash, seeds=seeds)
        if include_replay
        else {
            "producer_function": "replay_report",
            "run_id": run_id,
            "code_path_hash": code_hash,
            "gate": "G-D",
            "status": "not_run",
        }
    )
    verdict, failing = choose_verdict(baseline, ablation, replay, channel, rng)
    cpu_hours = (time.process_time() - started) / 3600.0
    result = {
        "producer_function": "run_phase",
        "task": TASK_ID,
        "phase": phase,
        "run_id": run_id,
        "verdict": verdict,
        "verdict_subtype": verdict,
        "positive_claim": phase == "scored" and verdict == "CAPABILITY_PRESENT_CHANNEL_DISCLOSED",
        "positive_claim_stop_required": phase == "scored" and verdict == "CAPABILITY_PRESENT_CHANNEL_DISCLOSED",
        "claim_ceiling": CLAIM_CEILING,
        "signature_manifest": {
            "G-A": baseline["G_A_status"],
            "G-B": baseline["G_B_status"],
            "G-C": ablation["status"],
            "G-D": replay["status"],
            "G-E": channel["status"],
            "UNSEEDED-RNG-AUDIT": rng["status"],
        },
        "failing_gates": failing,
        "code_path_hash": code_hash,
        "config_shas": config_shas(),
        "seed_ids": seeds,
        "episode_ids": [str(run["pair_id"]) for run in pair_runs],
        "event_count": len(events),
        "pair_count": len(pair_runs),
        "trace_artifact_scope": (
            "trace.jsonl/probe_trace.jsonl contain observe-intervention gate rows only to keep the Git artifact under "
            "the GitHub hard file-size boundary; forage diagnostic records remain represented in metric_records.json "
            "and in the replay digest over all pairs"
        ),
        "aggregation_rule": "frozen PREREG gate conjunction over deterministic _best_site(model_before, need) persistence windows; no threshold tuning",
        "prereg_validation": prereg,
        "cpu": {"measured_cpu_hours": round(cpu_hours, 12)},
        "gate_results": {
            "G-A/G-B": baseline,
            "G-C": ablation,
            "G-D": replay,
            "G-E": channel,
            "UNSEEDED-RNG-AUDIT": rng,
        },
        "what_this_does_not_prove": [
            "no learning or generalization claim",
            "no adaptation-quality claim",
            "no understanding or world-modeling competence claim",
            "no self agency autonomy subjectivity emotion consciousness or EGO readiness claim",
            "C-observe remains an oracle snapshot, not experiential learning",
        ],
    }
    if write_artifacts:
        target = out_dir or ARTIFACT_ROOT
        target.mkdir(parents=True, exist_ok=True)
        if phase == "probe":
            write_json(target / "probe_report.json", result)
            write_json(target / "probe_baseline_comparison.json", baseline)
            write_json(target / "probe_ablation_report.json", ablation)
            write_json(target / "probe_replay_report.json", replay)
            write_json(target / "probe_channel_report.json", channel)
            write_jsonl(target / "probe_trace.jsonl", flatten_pair_trace(pair_runs, gate_only=True))
        else:
            write_json(target / "result.json", result)
            write_json(target / "baseline_comparison.json", baseline)
            write_json(target / "ablation_report.json", ablation)
            write_json(target / "replay_report.json", replay)
            write_json(target / "channel_report.json", channel)
            write_json(target / "metric_records.json", metric_records)
            write_jsonl(target / "trace.jsonl", flatten_pair_trace(pair_runs, gate_only=True))
            (target / "claim_ceiling.txt").write_text(CLAIM_CEILING + "\n", encoding="utf-8")
            if verdict != "CAPABILITY_PRESENT_CHANNEL_DISCLOSED":
                write_json(
                    target / "failure_manifest.json",
                    {
                        "producer_function": "failure_manifest",
                        "verdict": verdict,
                        "failing_gates": failing,
                        "result_pointer": _rel(target / "result.json"),
                        "code_path_hash": code_hash,
                    },
                )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["probe", "scored"])
    parser.add_argument("--out-dir", type=Path, default=ARTIFACT_ROOT)
    parser.add_argument("--replay-stdin", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--skip-replay", action="store_true")
    args = parser.parse_args(argv)
    if args.replay_stdin:
        payload = json.loads(sys.stdin.read() or "{}")
        print(json.dumps(replay_from_payload(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    if not args.phase:
        parser.error("--phase is required unless --replay-stdin is used")
    result = run_phase(
        phase=args.phase,
        out_dir=args.out_dir,
        include_replay=not args.skip_replay,
        write_artifacts=not args.no_write,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
