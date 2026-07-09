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

from scripts.ego_kernel.state import KernelState, deep_copy
from scripts.ego_pet.creature import (
    _best_site,
    _derived_prediction_error_trigger,
    _prediction_for_action,
    select_action,
    update_creature_after_feedback,
    zero_creature_state,
)
from scripts.ego_pet.world import (
    WORLD_CONFIG_PATH,
    advance_world,
    build_observation,
    load_world_config,
    regime_for_tick,
    zero_world_state,
)
from scripts.ego_pet_capability import CLAIM_CEILING, TASK_ID
from scripts.ego_pet_capability.trace import build_capability_trace_row, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / TASK_ID
STAGE_CARD_PATH = TASK_DIR / "STAGE_CARD.md"
PREREG_001_PATH = TASK_DIR / "PREREG_ADDENDUM_001.md"
PREREG_002_PATH = TASK_DIR / "PREREG_ADDENDUM_002_INSTRUMENT_REPAIR.md"
PREREG_003_PATH = TASK_DIR / "PREREG_ADDENDUM_003_C-FORAGE-PREDICTION-ERROR.md"
MUTATION_SCOPE_PATH = TASK_DIR / "MUTATION_SCOPE.yaml"
ARTIFACT_ROOT = ROOT / "artifacts" / TASK_ID / "pe_forage_003"

RUN_ID_BASE = "ego_pet_capability_conformance_001a_c_forage_pe_003"
PROBE_SEED = 1107
S_DEV_RESERVED = set(range(1101, 1108))
P0_SCORED_RESERVED = set(range(2101, 2121))
CAPABILITY_001_SCORED_RESERVED = set(range(3101, 3121))
CAPABILITY_REPAIR_SCORED_RESERVED = set(range(4101, 4121))
SCORED_SEEDS = list(range(5101, 5121))
ARMS = ("candidate", "frozen_updates", "static", "candidate_ablated", "schedule_reobserve")
VARIANTS = ("A", "B", "C")
NEEDS = ("energy", "comfort")
HORIZON = 50
POSITIVE_VERDICTS = {"PE_REFLEX_AND_WRITE_PRESENT_DISCLOSED", "WRITE_ONLY", "PE_REFLEX_ONLY"}


class InstrumentInvalidError(ValueError):
    def __init__(self, message: str, manifest: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.manifest = manifest or {
            "producer_function": "instrument_invalid_error",
            "status": "fail",
            "reason": message,
            "failing_gates": ["PREREG_VALIDATION"],
        }


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
        "scripts/ego_pet_capability/forage_prediction_error.py",
        "scripts/ego_pet_capability/trace.py",
        "scripts/ego_pet/creature.py",
        "scripts/ego_pet/world.py",
        "scripts/ego_kernel/state.py",
        "scripts/ego_kernel/tick.py",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/STAGE_CARD.md",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/PREREG_ADDENDUM_001.md",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/PREREG_ADDENDUM_002_INSTRUMENT_REPAIR.md",
        "docs/codex/tasks/ego-pet-capability-conformance-001a/PREREG_ADDENDUM_003_C-FORAGE-PREDICTION-ERROR.md",
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
        "PREREG_ADDENDUM_001.md": sha256_file(PREREG_001_PATH),
        "PREREG_ADDENDUM_002_INSTRUMENT_REPAIR.md": sha256_file(PREREG_002_PATH),
        "PREREG_ADDENDUM_003_C-FORAGE-PREDICTION-ERROR.md": sha256_file(PREREG_003_PATH),
        "MUTATION_SCOPE.yaml": sha256_file(MUTATION_SCOPE_PATH),
    }


@dataclass(frozen=True)
class ForageEvent:
    event_id: str
    seed: int
    tick_index: int
    regime_index: int
    regime_id: str
    action_type: str
    need: str
    candidate_site: str
    gate_scope: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ForageEvent":
        return cls(
            event_id=str(payload["event_id"]),
            seed=int(payload["seed"]),
            tick_index=int(payload["tick_index"]),
            regime_index=int(payload["regime_index"]),
            regime_id=str(payload["regime_id"]),
            action_type=str(payload["action_type"]),
            need=str(payload["need"]),
            candidate_site=str(payload["candidate_site"]),
            gate_scope=str(payload["gate_scope"]),
        )


def _policy_arm(arm: str) -> str:
    return "candidate" if arm in {"candidate_ablated", "schedule_reobserve"} else arm


def _updates_enabled(arm: str) -> bool:
    return arm in {"candidate", "schedule_reobserve"}


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
            "run_context": {"arm": arm, "policy_arm": policy_arm, "capability_conformance": "c_forage_pe_003"},
        },
        seed_registry={"pet_policy": {"seed": int(seed), "draws": 0}},
        ablations={"pet_creature_v0": "live" if _updates_enabled(arm) else "frozen"},
    )


def _site_score(yields: dict[str, float], need_key: str) -> float:
    other = "comfort" if need_key == "energy" else "energy"
    return float(yields[need_key]) + 0.25 * float(yields[other])


def _derived_designations(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    designations: dict[str, dict[str, str]] = {}
    for regime in config["regimes"]:
        rid = str(regime["regime_id"])
        designations[rid] = {
            "energy": _best_site(regime["site_yields"], "energy"),
            "comfort": _best_site(regime["site_yields"], "comfort"),
        }
    return designations


def assert_seed_disjointness(seeds: list[int]) -> None:
    seed_set = {int(seed) for seed in seeds}
    reserved_sets = {
        "S_dev_1101_1107": S_DEV_RESERVED,
        "P0_scored_2101_2120": P0_SCORED_RESERVED,
        "capability_001_3101_3120": CAPABILITY_001_SCORED_RESERVED,
        "capability_repair_4101_4120": CAPABILITY_REPAIR_SCORED_RESERVED,
    }
    for name, reserved in reserved_sets.items():
        overlap = sorted(seed_set & reserved)
        if overlap:
            raise InstrumentInvalidError(
                f"seed-disjointness assertion failed vs {name}: {overlap}",
                {
                    "producer_function": "assert_seed_disjointness",
                    "verdict": "INSTRUMENT_INVALID",
                    "failing_gates": ["SEED_DISJOINTNESS"],
                    "overlap": overlap,
                },
            )


def validate_prereg_inputs(config: dict[str, Any], *, phase: str, seeds: list[int]) -> dict[str, Any]:
    if int(config["time"]["episode_length_ticks"]) != 600:
        raise InstrumentInvalidError("frozen episode length mismatch")
    if int(config["time"]["window_W_ticks"]) != HORIZON:
        raise InstrumentInvalidError("frozen persistence horizon mismatch")
    if phase == "probe" and seeds != [PROBE_SEED]:
        raise InstrumentInvalidError(
            "probe seed differs from frozen 1107",
            {"producer_function": "validate_prereg_inputs", "verdict": "INSTRUMENT_INVALID", "failing_gates": ["SEED_DISJOINTNESS"]},
        )
    if phase == "scored":
        assert_seed_disjointness(seeds)
        if seeds != SCORED_SEEDS:
            raise InstrumentInvalidError(
                "scored seed list differs from frozen 5101..5120 block",
                {"producer_function": "validate_prereg_inputs", "verdict": "INSTRUMENT_INVALID", "failing_gates": ["SEED_DISJOINTNESS"]},
            )
    return {
        "producer_function": "validate_prereg_inputs",
        "phase": phase,
        "seed_ids": seeds,
        "designated_best_sites_derived_from_config": _derived_designations(config),
        "seed_disjointness_asserted": phase == "scored",
        "status": "pass",
    }


def schedule_context_from_candidate(candidate_rows: list[dict[str, Any]], events: list[ForageEvent]) -> dict[str, Any]:
    total = len(candidate_rows)
    observe_count = sum(1 for row in candidate_rows if row["action"].get("action_type") == "observe")
    rho = float(observe_count) / float(total)
    period = max(1, int(round(1.0 / rho))) if rho > 0 else total + 1
    forbidden_phases = {int(event.tick_index) % period for event in events}
    phase = next((candidate for candidate in range(period) if candidate not in forbidden_phases), 0)
    return {
        "producer_function": "schedule_context_from_candidate",
        "candidate_observe_count": observe_count,
        "episode_ticks": total,
        "rho": round(rho, 12),
        "period": period,
        "phase": phase,
        "event_ticks_excluded_from_schedule": [int(event.tick_index) for event in events],
    }


def schedule_reobserve_action(
    state: KernelState,
    observation: dict[str, Any],
    config: dict[str, Any],
    schedule_context: dict[str, Any],
) -> tuple[dict[str, Any], KernelState, dict[str, Any]]:
    creature = deep_copy(state.substates["pet_creature_v0"])
    tick = int(observation["tick_index"])
    period = int(schedule_context["period"])
    phase = int(schedule_context["phase"])
    if period > 0 and tick % period == phase:
        action = {"policy": "schedule_reobserve", "action_type": "observe", "site": None}
        return action, state, {
            "policy": "schedule_reobserve",
            "schedule_period": period,
            "schedule_phase": phase,
            "pe_blind": True,
            "prediction": _prediction_for_action(creature, action),
        }
    needs = observation["needs"]
    need = "energy" if (1.0 - float(needs["energy"])) >= (1.0 - float(needs["comfort"])) else "comfort"
    action_type = "forage_energy" if need == "energy" else "seek_comfort"
    site = _best_site(creature["model"], need)
    action = {"policy": "schedule_reobserve", "action_type": action_type, "site": site}
    return action, state, {
        "policy": "schedule_reobserve",
        "schedule_period": period,
        "schedule_phase": phase,
        "pe_blind": True,
        "prediction": _prediction_for_action(creature, action),
    }


def _need_from_action(action: dict[str, Any], fallback: str) -> str:
    if action.get("action_type") == "forage_energy":
        return "energy"
    if action.get("action_type") == "seek_comfort":
        return "comfort"
    return fallback


def pair_c_yield(
    config: dict[str, Any],
    creature_before: dict[str, Any],
    action: dict[str, Any],
    need: str,
) -> tuple[dict[str, float], dict[str, Any]]:
    site = action.get("site")
    if not site or site not in creature_before["model"]:
        raise InstrumentInvalidError(
            "Pair-C target derivation requires a site action",
            {"producer_function": "pair_c_yield", "verdict": "INSTRUMENT_INVALID", "failing_gates": ["PAIR_C_TARGET_DEGENERACY"]},
        )
    site = str(site)
    model = jcopy(creature_before["model"])
    pre_best = _best_site(model, need)
    trigger = _derived_prediction_error_trigger(config)
    prediction = _prediction_for_action(creature_before, action)
    if site == pre_best:
        candidate_actual = {"energy": 0.0, "comfort": 0.0}
    else:
        candidate_actual = dict(prediction)
        candidate_actual[need] = 1.0
    candidate_actual = {key: round(float(value), 12) for key, value in candidate_actual.items()}
    post_model = jcopy(model)
    post_model[site] = jcopy(candidate_actual)
    target = _best_site(post_model, need)
    pe = abs(float(prediction["energy"]) - float(candidate_actual["energy"])) + abs(
        float(prediction["comfort"]) - float(candidate_actual["comfort"])
    )
    if target == pre_best or pe <= trigger:
        raise InstrumentInvalidError(
            "Pair-C target-degeneracy assertion failed",
            {
                "producer_function": "pair_c_yield",
                "verdict": "INSTRUMENT_INVALID",
                "failing_gates": ["PAIR_C_TARGET_DEGENERACY"],
                "site": site,
                "need": need,
                "pre_intervention_best_site": pre_best,
                "target_site": target,
                "prediction_error": round(pe, 12),
                "trigger": trigger,
            },
        )
    return candidate_actual, {
        "pair_c_target_site": target,
        "pre_intervention_best_site": pre_best,
        "pair_c_site": site,
        "pair_c_need": need,
        "pair_c_prediction_error": round(pe, 12),
        "prediction_error_trigger": trigger,
    }


def apply_feedback_variant(
    *,
    config: dict[str, Any],
    event: ForageEvent | None,
    variant: str,
    action: dict[str, Any],
    feedback: dict[str, Any],
    creature_before: dict[str, Any],
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    modified = jcopy(feedback)
    prediction = _prediction_for_action(creature_before, action)
    base = {
        "variant": variant,
        "prediction_before_update": prediction,
        "expected_prediction_error": abs(float(prediction["energy"]) - float(modified["action_yield"]["energy"]))
        + abs(float(prediction["comfort"]) - float(modified["action_yield"]["comfort"])),
    }
    if event is None or variant == "A":
        return modified, False, {**base, "intervention": "none"}
    if int(feedback["tick_index"]) != int(event.tick_index):
        return modified, False, {**base, "intervention": "not_at_event_tick"}
    if not action.get("site"):
        raise InstrumentInvalidError(
            "scored forage event reached a non-site action",
            {"producer_function": "apply_feedback_variant", "verdict": "INSTRUMENT_INVALID", "failing_gates": ["PAIR_C_TARGET_DEGENERACY"]},
        )
    if variant == "B":
        modified["action_yield"] = jcopy(prediction)
        return modified, True, {
            **base,
            "intervention": "prediction_matched_pe_zero",
            "expected_prediction_error": 0.0,
        }
    if variant == "C":
        need = _need_from_action(action, event.need)
        actual, target_meta = pair_c_yield(config, creature_before, action, need)
        modified["action_yield"] = actual
        return modified, True, {
            **base,
            "intervention": "prediction_divergent_directional_forage_yield",
            "expected_prediction_error": target_meta["pair_c_prediction_error"],
            **target_meta,
        }
    raise ValueError(f"unsupported variant: {variant}")


def run_step(
    *,
    state: KernelState,
    config: dict[str, Any],
    arm: str,
    seed: int,
    variant: str,
    event: ForageEvent | None,
    pair_id: str,
    schedule_context: dict[str, Any] | None,
) -> tuple[KernelState, dict[str, Any]]:
    state_before = state
    world_state = deep_copy(state.substates["pet_world_v0"])
    observation = build_observation(world_state, config, None)
    if arm == "schedule_reobserve":
        action, working_state, attribution = schedule_reobserve_action(state, observation, config, schedule_context or {})
    else:
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
    channel = "C-forage" if intervention_applied and action.get("site") else "none"
    if action.get("action_type") == "observe":
        channel = "C-PE" if int(observation["tick_index"]) == (int(event.tick_index) + 1 if event else -2) else "observe"
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
        event_kind="baseline" if event is None else "forage_prediction_error",
        intervention_applied=intervention_applied,
    )
    prediction = _prediction_for_action(creature_before, action)
    expected_pe = abs(float(prediction["energy"]) - float(feedback["action_yield"]["energy"])) + abs(
        float(prediction["comfort"]) - float(feedback["action_yield"]["comfort"])
    )
    row.update(
        {
            "attribution": attribution,
            "prediction_before_update": prediction,
            "expected_prediction_error": round(expected_pe, 12),
            "recorded_prediction_error": round(float(creature_after.get("last_prediction_error", 0.0)), 12),
            "prediction_error_abs_diff": round(abs(float(creature_after.get("last_prediction_error", 0.0)) - expected_pe), 12),
            "intervention_meta": intervention_meta,
        }
    )
    return state_after, row


def run_baseline(
    config: dict[str, Any],
    *,
    seed: int,
    arm: str,
    run_id: str,
    schedule_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
            schedule_context=schedule_context,
        )
        rows.append(row)
    return {"pre_states": pre_states, "trace_rows": rows, "final_state": state.to_dict()}


def select_candidate_events(config: dict[str, Any], *, seed: int, candidate_rows: list[dict[str, Any]]) -> list[ForageEvent]:
    by_regime_need: dict[tuple[int, str], dict[str, Any]] = {}
    for row in candidate_rows:
        action = row["action"]
        action_type = str(action.get("action_type"))
        if action_type not in {"forage_energy", "seek_comfort"}:
            continue
        tick = int(row["tick_index"])
        regime = regime_for_tick(config, tick)
        regime_index = list(config["regimes"]).index(regime)
        need = "energy" if action_type == "forage_energy" else "comfort"
        by_regime_need.setdefault((regime_index, need), row)
    events: list[ForageEvent] = []
    for regime_index in range(len(config["regimes"])):
        for need in NEEDS:
            key = (regime_index, need)
            if key not in by_regime_need:
                raise InstrumentInvalidError(
                    f"missing candidate first forage event for regime {regime_index} need {need}",
                    {"producer_function": "select_candidate_events", "verdict": "INSTRUMENT_INVALID", "failing_gates": ["PAIR_C_TARGET_DEGENERACY"]},
                )
            row = by_regime_need[key]
            action_type = "forage_energy" if need == "energy" else "seek_comfort"
            events.append(
                ForageEvent(
                    event_id=f"seed_{seed}:forage_pe:{need}:R{regime_index}:tick_{row['tick_index']}",
                    seed=seed,
                    tick_index=int(row["tick_index"]),
                    regime_index=regime_index,
                    regime_id=str(config["regimes"][regime_index]["regime_id"]),
                    action_type=action_type,
                    need=need,
                    candidate_site=str(row["action"]["site"]),
                    gate_scope="forage_pe_scored",
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


def state_payload_for_arm(state_payload: dict[str, Any], *, arm: str) -> dict[str, Any]:
    payload = jcopy(state_payload)
    creature = payload["substates"]["pet_creature_v0"]
    creature["arm"] = _policy_arm(arm)
    creature["updates_enabled"] = _updates_enabled(arm)
    payload["substates"]["run_context"]["arm"] = arm
    payload["substates"]["run_context"]["policy_arm"] = _policy_arm(arm)
    payload["ablations"]["pet_creature_v0"] = "live" if _updates_enabled(arm) else "frozen"
    return payload


def run_variant_from_state(
    *,
    config: dict[str, Any],
    state_payload: dict[str, Any],
    arm: str,
    seed: int,
    event: ForageEvent,
    variant: str,
    run_id: str,
    schedule_context: dict[str, Any] | None,
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
            schedule_context=schedule_context,
        )
        rows.append(row)
    return {
        "pair_id": pair_id,
        "arm": arm,
        "seed": int(seed),
        "variant": variant,
        "event": asdict(event),
        "schedule_context": schedule_context,
        "initial_state": state_payload,
        "trace_rows": rows,
        "final_state": state.to_dict(),
    }


def _rows_by_tick(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(row["tick_index"]): row for row in rows}


def _window_ticks_for_w(event: ForageEvent, c_rows: list[dict[str, Any]], *, site: str) -> list[int]:
    rows_by_tick = _rows_by_tick(c_rows)
    first_tick = int(event.tick_index) + 1
    end = int(event.tick_index) + HORIZON
    for row in c_rows:
        tick = int(row["tick_index"])
        if tick <= int(event.tick_index):
            continue
        if row.get("channel") == "observe":
            end = min(end, tick)
            break
        if row.get("channel") == "C-forage" and str(row.get("action", {}).get("site")) == site:
            end = min(end, tick)
            break
    return [tick for tick in range(first_tick, end + 1) if tick in rows_by_tick]


def metric_records_for_event(
    *,
    arm: str,
    event: ForageEvent,
    variant_runs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    a_rows = variant_runs["A"]["trace_rows"]
    b_rows = variant_runs["B"]["trace_rows"]
    c_rows = variant_runs["C"]["trace_rows"]
    b_by_tick = _rows_by_tick(b_rows)
    c_by_tick = _rows_by_tick(c_rows)
    t = int(event.tick_index)
    b_t = b_by_tick[t]
    c_t = c_by_tick[t]
    b_next = b_by_tick.get(t + 1)
    c_next = c_by_tick.get(t + 1)
    target_meta = c_t["intervention_meta"]
    target_site = str(target_meta.get("pair_c_target_site", ""))
    pair_c_site = str(target_meta.get("pair_c_site", ""))
    need = str(target_meta.get("pair_c_need", event.need))
    w_ticks = _window_ticks_for_w(event, c_rows, site=pair_c_site)
    w_matches = [
        tick
        for tick in w_ticks
        if _best_site(c_by_tick[tick]["model_before"], need) == target_site
    ]
    pe_rows = [row for row in (a_rows[0], b_t, c_t) if int(row["tick_index"]) == t]
    pe_failures = [
        {
            "variant": row["variant"],
            "recorded": row["recorded_prediction_error"],
            "expected": row["expected_prediction_error"],
            "abs_diff": row["prediction_error_abs_diff"],
        }
        for row in pe_rows
        if float(row["prediction_error_abs_diff"]) > 1e-9
    ]
    observe_b = bool(b_next and b_next["action"].get("action_type") == "observe")
    observe_c = bool(c_next and c_next["action"].get("action_type") == "observe")
    return [
        {
            "producer_function": "metric_records_for_event",
            "event_id": event.event_id,
            "seed": int(event.seed),
            "arm": arm,
            "regime_id": event.regime_id,
            "regime_index": event.regime_index,
            "need": need,
            "intervention_tick": t,
            "pair_c_site": pair_c_site,
            "pair_c_target_site": target_site,
            "pre_intervention_best_site": target_meta.get("pre_intervention_best_site"),
            "target_degenerate": target_site == target_meta.get("pre_intervention_best_site"),
            "pair_c_prediction_error": target_meta.get("pair_c_prediction_error"),
            "prediction_error_trigger": target_meta.get("prediction_error_trigger"),
            "pe_fidelity_failures": pe_failures,
            "pe_fidelity_status": "pass" if not pe_failures else "fail",
            "b_observe_t_plus_1": observe_b,
            "c_observe_t_plus_1": observe_c,
            "c_minus_b_observe_delta_count": int(observe_c) - int(observe_b),
            "w_window_ticks": w_ticks,
            "w_window_len": len(w_ticks),
            "w_match_count": len(w_matches),
            "w_rate": round(float(len(w_matches)) / float(len(w_ticks)), 12) if w_ticks else 0.0,
            "w_matches": w_matches[:10],
        }
    ]


def run_pair_bundle_for_seed(config: dict[str, Any], *, seed: int, run_id: str) -> dict[str, Any]:
    candidate_baseline = run_baseline(config, seed=seed, arm="candidate", run_id=run_id)
    events = select_candidate_events(config, seed=seed, candidate_rows=candidate_baseline["trace_rows"])
    schedule_context = schedule_context_from_candidate(candidate_baseline["trace_rows"], events)
    baselines: dict[str, dict[str, Any]] = {"candidate": candidate_baseline}
    pair_runs: list[dict[str, Any]] = []
    metric_records: list[dict[str, Any]] = []
    for event in events:
        for arm in ARMS:
            state_payload = state_payload_for_arm(candidate_baseline["pre_states"][int(event.tick_index)], arm=arm)
            variants = {
                variant: run_variant_from_state(
                    config=config,
                    state_payload=state_payload,
                    arm=arm,
                    seed=seed,
                    event=event,
                    variant=variant,
                    run_id=run_id,
                    schedule_context=schedule_context if arm == "schedule_reobserve" else None,
                )
                for variant in VARIANTS
            }
            pair_runs.extend(variants.values())
            metric_records.extend(metric_records_for_event(arm=arm, event=event, variant_runs=variants))
    return {
        "baselines": baselines,
        "events": [asdict(event) for event in events],
        "schedule_context": schedule_context,
        "pair_runs": pair_runs,
        "metric_records": metric_records,
    }


def _rate(numer: int, denom: int) -> float:
    return round(float(numer) / float(denom), 12) if denom else 0.0


def _aggregate_c(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    c_obs = sum(1 for record in records if record["c_observe_t_plus_1"])
    b_obs = sum(1 for record in records if record["b_observe_t_plus_1"])
    return {
        "c_observe": c_obs,
        "b_observe": b_obs,
        "total": total,
        "c_rate": _rate(c_obs, total),
        "b_rate": _rate(b_obs, total),
        "C_delta": round(_rate(c_obs, total) - _rate(b_obs, total), 12),
    }


def _aggregate_w(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(record["w_window_len"]) for record in records)
    matches = sum(int(record["w_match_count"]) for record in records)
    return {"matches": matches, "total": total, "W_rate": _rate(matches, total)}


def pe_fidelity_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    failures = [record for record in metric_records if record["pe_fidelity_status"] != "pass" or record["target_degenerate"]]
    return {
        "producer_function": "pe_fidelity_report",
        "input_artifacts": ["trace.jsonl", "PREREG_ADDENDUM_003_C-FORAGE-PREDICTION-ERROR.md"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [str(record["event_id"]) for record in metric_records],
        "aggregation_rule": "Every scored event records last_prediction_error == L1(prediction, actual) within 1e-9 and Pair-C target differs from pre-intervention best_site.",
        "code_path_hash": code_hash,
        "gate": "G-PE-FIDELITY",
        "failure_count": len(failures),
        "failures": failures[:20],
        "status": "pass" if not failures else "fail",
    }


def baseline_comparison_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    by_arm = {arm: _aggregate_c([record for record in metric_records if record["arm"] == arm]) for arm in ARMS}
    candidate = by_arm["candidate"]["C_delta"]
    schedule = by_arm["schedule_reobserve"]["C_delta"]
    static = by_arm["static"]["C_delta"]
    return {
        "producer_function": "baseline_comparison_report",
        "input_artifacts": ["trace.jsonl", "PREREG_ADDENDUM_003_C-FORAGE-PREDICTION-ERROR.md"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"{arm}:{seed}" for arm in ARMS for seed in seeds],
        "aggregation_rule": "G-P PE-reflex: C(arm)=rate[observe@t+1|Pair-C]-rate[observe@t+1|Pair-B] over forage interventions.",
        "code_path_hash": code_hash,
        "gate": "G-P",
        "thresholds": {"candidate_C_min": 0.60, "schedule_reobserve_C_max": 0.05, "static_C_max": 0.05},
        "by_arm": by_arm,
        "predeclared_reflex_survives_ablation": {
            "frozen_updates_C_delta": by_arm["frozen_updates"]["C_delta"],
            "candidate_ablated_C_delta": by_arm["candidate_ablated"]["C_delta"],
            "not_failure": True,
        },
        "status": "pass" if candidate >= 0.60 and schedule <= 0.05 and static <= 0.05 else "fail",
        "schedule_degradation_margin": round(candidate - schedule, 12),
    }


def ablation_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    by_arm = {arm: _aggregate_w([record for record in metric_records if record["arm"] == arm]) for arm in ARMS}
    candidate = by_arm["candidate"]["W_rate"]
    ablated = by_arm["candidate_ablated"]["W_rate"]
    frozen = by_arm["frozen_updates"]["W_rate"]
    static = by_arm["static"]["W_rate"]
    return {
        "producer_function": "ablation_report",
        "input_artifacts": ["trace.jsonl", "baseline_comparison.json"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"{arm}:{seed}" for arm in ARMS for seed in seeds],
        "aggregation_rule": "G-W forage-write: W(arm)=rate[_best_site(model,need)==Pair-C target] over persistence windows; candidate >=0.60 and write controls <=0.05.",
        "code_path_hash": code_hash,
        "gate": "G-W",
        "thresholds": {"candidate_W_min": 0.60, "write_control_W_max": 0.05},
        "by_arm": by_arm,
        "status": "pass" if candidate >= 0.60 and ablated <= 0.05 and frozen <= 0.05 and static <= 0.05 else "fail",
    }


def channel_report(metric_records: list[dict[str, Any]], *, run_id: str, code_hash: str, seeds: list[int]) -> dict[str, Any]:
    c_records = [record for record in metric_records if record["arm"] in {"candidate", "frozen_updates", "candidate_ablated"} and record["c_minus_b_observe_delta_count"] > 0]
    w_records = [record for record in metric_records if record["arm"] == "candidate" and record["w_match_count"] > 0]
    split = {"C-PE": len(c_records), "C-forage": sum(int(record["w_match_count"]) for record in w_records)}
    total = sum(split.values())
    return {
        "producer_function": "channel_report",
        "input_artifacts": ["trace.jsonl"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [f"{arm}:{seed}" for arm in ARMS for seed in seeds],
        "aggregation_rule": "Nonzero PE-reflex records are attributed to C-PE; nonzero Pair-C write-window matches are attributed to C-forage.",
        "code_path_hash": code_hash,
        "gate": "G-E",
        "channel_split_counts": split,
        "channel_split_rates": {key: _rate(value, total) for key, value in split.items()},
        "fixed_threshold_disclosure": "_derived_prediction_error_trigger(config) is fixed/config-derived; PE reflex is not update-gated and not adaptation.",
        "direct_write_disclosure": "C-forage write is model[site]=actual for the visited site; direct single-site overwrite, not inference.",
        "status": "pass" if total > 0 else "fail",
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
                "schedule_context": run.get("schedule_context"),
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
            event=ForageEvent.from_dict(pair["event"]),
            variant=str(pair["variant"]),
            run_id=str(payload["run_id"]),
            schedule_context=pair.get("schedule_context"),
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
            [sys.executable, "-m", "scripts.ego_pet_capability.forage_prediction_error", "--replay-stdin"],
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
        "input_artifacts": ["serialized pair initial_state + event + variant + schedule_context payload", "trace.jsonl"],
        "run_id": run_id,
        "seed_ids": seeds,
        "episode_ids": [str(run["pair_id"]) for run in pair_runs],
        "aggregation_rule": "fresh subprocess replay x2 recomputes every pair from serialized_state + event + schedule context; compare canonical trace digest",
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
    files = scan_files or [ROOT / "scripts" / "ego_pet_capability" / "forage_prediction_error.py"]
    hits: list[dict[str, Any]] = []
    for path in files:
        hits.extend(rng_usage_hits(path))
    return {
        "producer_function": "rng_audit",
        "input_artifacts": [_rel(path) for path in files],
        "run_id": run_id,
        "seed_ids": [],
        "episode_ids": [],
        "aggregation_rule": "AST-level audit for RNG framework imports/calls and builtin hash() in #3 capability harness files",
        "code_path_hash": code_hash,
        "forbidden_hits": hits,
        "positive_control": "tests/test_forage_prediction_error.py::test_rng_audit_positive_control_detects_forbidden_random",
        "status": "pass" if not hits else "fail",
    }


def choose_verdict(
    pe: dict[str, Any],
    baseline: dict[str, Any],
    ablation: dict[str, Any],
    replay: dict[str, Any],
    channel: dict[str, Any],
    rng: dict[str, Any],
) -> tuple[str, list[str]]:
    invalid: list[str] = []
    if pe.get("status") != "pass":
        invalid.append("G-PE-FIDELITY")
    if replay.get("status") != "pass":
        invalid.append("G-D")
    if channel.get("status") != "pass":
        invalid.append("G-E")
    if rng.get("status") != "pass":
        invalid.append("UNSEEDED-RNG-AUDIT")
    if baseline["by_arm"]["schedule_reobserve"]["C_delta"] > 0.05:
        invalid.append("SCHEDULE_REOBSERVE_CONTINGENCY_CONTAMINATION")
    if baseline["by_arm"]["static"]["C_delta"] > 0.05:
        invalid.append("STATIC_PE_CONTINGENCY_CONTAMINATION")
    for arm in ("candidate_ablated", "frozen_updates", "static"):
        if ablation["by_arm"][arm]["W_rate"] > 0.05:
            invalid.append(f"{arm.upper()}_WRITE_CONTAMINATION")
    if invalid:
        return "INSTRUMENT_INVALID", invalid
    gp = baseline.get("status") == "pass"
    gw = ablation.get("status") == "pass"
    if gp and gw:
        return "PE_REFLEX_AND_WRITE_PRESENT_DISCLOSED", []
    if baseline["schedule_degradation_margin"] <= 0.05:
        return "DEGRADES_TO_SCHEDULE", ["G-P"]
    if gw and not gp:
        return "WRITE_ONLY", ["G-P"]
    if gp and not gw:
        return "PE_REFLEX_ONLY", ["G-W"]
    return "CAPABILITY_ABSENT", ["G-P", "G-W"]


def flatten_pair_trace(pair_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in sorted(pair_runs, key=lambda item: str(item["pair_id"])):
        rows.extend(run["trace_rows"])
    return rows


def invalid_result(
    *,
    phase: str,
    run_id: str,
    seeds: list[int],
    code_hash: str,
    error: InstrumentInvalidError,
) -> tuple[dict[str, Any], dict[str, Any]]:
    failure_manifest = {
        "producer_function": "failure_manifest",
        "verdict": "INSTRUMENT_INVALID",
        "failing_gates": list(error.manifest.get("failing_gates", ["PREREG_VALIDATION"])),
        "reason": str(error),
        "source_manifest": error.manifest,
        "code_path_hash": code_hash,
    }
    result = {
        "producer_function": "run_phase",
        "task": TASK_ID,
        "phase": phase,
        "run_id": run_id,
        "verdict": "INSTRUMENT_INVALID",
        "verdict_subtype": "INSTRUMENT_INVALID",
        "positive_claim": False,
        "positive_claim_stop_required": False,
        "claim_ceiling": CLAIM_CEILING,
        "signature_manifest": {"PREREG-VALIDATION": "fail"},
        "failing_gates": failure_manifest["failing_gates"],
        "code_path_hash": code_hash,
        "config_shas": config_shas(),
        "seed_ids": seeds,
        "episode_ids": [],
        "event_count": 0,
        "pair_count": 0,
        "prereg_validation": {"status": "fail", "reason": str(error), "source_manifest": error.manifest},
        "gate_results": {},
        "what_this_does_not_prove": not_proven(),
    }
    return result, failure_manifest


def not_proven() -> list[str]:
    return [
        "no learning claim",
        "no adaptation-quality claim",
        "no world-modeling or inference claim",
        "no uncertainty-driven behavior claim",
        "no self agency autonomy subjectivity emotion consciousness or EGO readiness claim",
        "PE reflex uses a fixed config-derived threshold and is not update-gated adaptation",
        "C-forage is a direct single-site write, not inference",
    ]


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
    code_hash = code_path_hash()
    try:
        prereg = validate_prereg_inputs(config, phase=phase, seeds=seeds)
        bundles = [run_pair_bundle_for_seed(config, seed=seed, run_id=run_id) for seed in seeds]
    except InstrumentInvalidError as exc:
        result, failure_manifest = invalid_result(phase=phase, run_id=run_id, seeds=seeds, code_hash=code_hash, error=exc)
        if write_artifacts:
            target = out_dir or ARTIFACT_ROOT
            target.mkdir(parents=True, exist_ok=True)
            write_json(target / ("probe_report.json" if phase == "probe" else "result.json"), result)
            write_json(target / "failure_manifest.json", failure_manifest)
        return result
    pair_runs = [run for bundle in bundles for run in bundle["pair_runs"]]
    metric_records = [record for bundle in bundles for record in bundle["metric_records"]]
    events = [event for bundle in bundles for event in bundle["events"]]
    pe = pe_fidelity_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    baseline = baseline_comparison_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    ablation = ablation_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    channel = channel_report(metric_records, run_id=run_id, code_hash=code_hash, seeds=seeds)
    rng = rng_audit(code_hash=code_hash, run_id=run_id)
    replay = (
        replay_report(pair_runs, run_id=run_id, code_hash=code_hash, seeds=seeds)
        if include_replay
        else {"producer_function": "replay_report", "run_id": run_id, "code_path_hash": code_hash, "gate": "G-D", "status": "not_run"}
    )
    verdict, failing = choose_verdict(pe, baseline, ablation, replay, channel, rng)
    positive = phase == "scored" and verdict in POSITIVE_VERDICTS
    result = {
        "producer_function": "run_phase",
        "task": TASK_ID,
        "phase": phase,
        "run_id": run_id,
        "verdict": verdict,
        "verdict_subtype": verdict,
        "positive_claim": positive,
        "positive_claim_stop_required": positive,
        "claim_ceiling": CLAIM_CEILING,
        "signature_manifest": {
            "G-PE-FIDELITY": pe["status"],
            "G-P": baseline["status"],
            "G-W": ablation["status"],
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
        "per_arm_C_table": baseline["by_arm"],
        "per_arm_W_table": ablation["by_arm"],
        "reflex_survives_ablation_disclosure": baseline["predeclared_reflex_survives_ablation"],
        "fixed_threshold_disclosure": channel["fixed_threshold_disclosure"],
        "direct_write_disclosure": channel["direct_write_disclosure"],
        "aggregation_rule": "Frozen PREREG_003 gate conjunction over PE-fidelity, PE-reflex contingency, forage-write W, replay, channel, and RNG audit; no threshold tuning.",
        "prereg_validation": prereg,
        "cpu": {"measured_cpu_hours": round((time.process_time() - started) / 3600.0, 12)},
        "gate_results": {
            "G-PE-FIDELITY": pe,
            "G-P": baseline,
            "G-W": ablation,
            "G-D": replay,
            "G-E": channel,
            "UNSEEDED-RNG-AUDIT": rng,
        },
        "what_this_does_not_prove": not_proven(),
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
            write_jsonl(target / "probe_trace.jsonl", flatten_pair_trace(pair_runs))
        else:
            write_json(target / "result.json", result)
            write_json(target / "baseline_comparison.json", baseline)
            write_json(target / "ablation_report.json", ablation)
            write_json(target / "replay_report.json", replay)
            write_json(target / "channel_report.json", channel)
            write_json(target / "metric_records.json", metric_records)
            write_jsonl(target / "trace.jsonl", flatten_pair_trace(pair_runs))
            if verdict not in POSITIVE_VERDICTS:
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
    result = run_phase(phase=args.phase, out_dir=args.out_dir, include_replay=not args.skip_replay, write_artifacts=not args.no_write)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
