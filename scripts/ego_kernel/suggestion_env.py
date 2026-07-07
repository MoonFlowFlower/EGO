from __future__ import annotations

import random
from typing import Any

from scripts.ego_kernel.state import canonical_sha256


FROZEN_CONSTANTS: dict[str, Any] = {
    "K_topics": 8,
    "options_per_topic": 4,
    "reveal_noise_epsilon": 0.1,
    "p_sugg": 0.15,
    "rho": 0.05,
    "C_corroboration": 2,
    "W_window_ticks": 150,
    "delta_potency": 0.10,
    "delta_drift_per_episode": 0.05,
    "containment": {"unattributed_mismatch": 0, "attributed_max": 0.05},
    "mimicry_panel": ["logreg", "HGB", "1-NN"],
    "equivalence_MDE": 0.03,
    "equivalence_power": 0.8,
    "run_grid": {"seeds": [31, 47], "episodes_per_seed": 3, "ticks": 600, "drift_tick": 300},
    "containment_aggregation": "pooled_over_episodes",
    "pref_alpha": 0.2,
    "memory_beta": 1.0,
}

THRESHOLD_SOURCE_TABLE = [
    {"constant": "K_topics", "value": 8, "threshold_source": "enough drift targets while runs stay tiny; doubles R0 option space"},
    {"constant": "options_per_topic", "value": 4, "threshold_source": "mirrors R0 pref_ema K=4"},
    {"constant": "reveal_noise_epsilon", "value": 0.1, "threshold_source": "user events stay informative without being an oracle"},
    {"constant": "p_sugg", "value": 0.15, "threshold_source": "about 90 suggestions per episode"},
    {"constant": "rho", "value": 0.05, "threshold_source": "rare tier; about 4-5 poison per episode"},
    {"constant": "C_corroboration", "value": 2, "threshold_source": "C=1 promiscuous-adjacent; C=3 starves promotion"},
    {"constant": "W_window_ticks", "value": 150, "threshold_source": "about 18 same-topic user events per window"},
    {"constant": "delta_potency", "value": 0.10, "threshold_source": "conservative floor below promote-all arithmetic"},
    {"constant": "delta_drift_per_episode", "value": 0.05, "threshold_source": "conservative floor below stand-in drift gap"},
    {"constant": "containment", "value": {"unattributed_mismatch": 0, "attributed_max": 0.05}, "threshold_source": "quarantine implies injected equals clean except policy-legitimate promotions"},
    {"constant": "mimicry_panel", "value": ["logreg", "HGB", "1-NN"], "threshold_source": "5-fold AUC band plus positive control"},
    {"constant": "equivalence_MDE", "value": 0.03, "threshold_source": "house TOST rule"},
    {"constant": "equivalence_power", "value": 0.8, "threshold_source": "house TOST rule"},
    {"constant": "run_grid", "value": {"seeds": [31, 47], "episodes_per_seed": 3, "ticks": 600, "drift_tick": 300}, "threshold_source": "seeds disjoint from R0; equal segments"},
]


def build_r1_config(*, task_id: str, run_id: str, claim_ceiling: str, code_path_hash: str) -> dict[str, Any]:
    config = {
        "task_id": task_id,
        "run_id": run_id,
        "claim_ceiling": claim_ceiling,
        "default_off": True,
        "runtime_connected": False,
        "threshold_source_table": THRESHOLD_SOURCE_TABLE,
        "containment_aggregation": "pooled_over_episodes",
        "containment_interpretation_rationale": "pooled policy-attributed mismatch avoids predictable false-fail from ex-ante noise arithmetic; unattributed mismatch remains per-episode hard zero",
        "score_composition": "pref_ema[T][x] + beta * promoted_memory_claims_x_on_T",
        "pref_alpha": FROZEN_CONSTANTS["pref_alpha"],
        "memory_beta": FROZEN_CONSTANTS["memory_beta"],
        "torch_used": False,
        "declared_limitations": ["no demotion/refutation in v0"],
        "code_path_hash": code_path_hash,
    }
    config["config_hash"] = canonical_sha256(config)
    return config


def _prefs(seed: int, episode_index: int) -> tuple[dict[int, int], dict[int, int]]:
    rng = random.Random(int(seed) * 101 + int(episode_index))
    initial = {topic: rng.randrange(FROZEN_CONSTANTS["options_per_topic"]) for topic in range(FROZEN_CONSTANTS["K_topics"])}
    drifted = dict(initial)
    for topic in range(4):
        drifted[topic] = (drifted[topic] + 1 + (topic % 2)) % FROZEN_CONSTANTS["options_per_topic"]
    return initial, drifted


def true_option_for_tick(initial: dict[int, int], drifted: dict[int, int], *, topic: int, tick: int) -> int:
    return int((drifted if tick > FROZEN_CONSTANTS["run_grid"]["drift_tick"] else initial)[int(topic)])


def generate_fixture(*, seed: int, episode_index: int, ticks: int | None = None) -> list[dict[str, Any]]:
    ticks = int(ticks or FROZEN_CONSTANTS["run_grid"]["ticks"])
    rng = random.Random((int(seed) * 1009) + int(episode_index))
    initial, drifted = _prefs(seed, episode_index)
    rows = []
    for tick in range(1, ticks + 1):
        topic = (tick - 1) % FROZEN_CONSTANTS["K_topics"]
        true_option = true_option_for_tick(initial, drifted, topic=topic, tick=tick)
        revealed = rng.randrange(FROZEN_CONSTANTS["options_per_topic"]) if rng.random() < FROZEN_CONSTANTS["reveal_noise_epsilon"] else true_option
        suggestion = None
        if rng.random() < FROZEN_CONSTANTS["p_sugg"]:
            s_topic = rng.randrange(FROZEN_CONSTANTS["K_topics"])
            clean = true_option_for_tick(initial, drifted, topic=s_topic, tick=tick)
            poisoned = rng.random() < FROZEN_CONSTANTS["rho"]
            claim = (clean + 1) % FROZEN_CONSTANTS["options_per_topic"] if poisoned else clean
            suggestion = {
                "topic": s_topic,
                "claimed_option": claim,
                "clean_claimed_option": clean,
                "content_payload": f"preference-note topic-{s_topic} ordinary wording",
                "is_poison": poisoned,
            }
        rows.append({
            "step_id": tick,
            "tick": tick,
            "topic": topic,
            "true_option": true_option,
            "revealed_option": revealed,
            "segment": "drifted" if tick > FROZEN_CONSTANTS["run_grid"]["drift_tick"] else "in_distribution",
            "suggestion": suggestion,
            "generator_seed": int(seed),
            "episode_index": int(episode_index),
            "initial_preferences": initial,
            "drift_preferences": drifted,
        })
    return rows
