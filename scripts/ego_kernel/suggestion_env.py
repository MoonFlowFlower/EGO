from __future__ import annotations

import random
from typing import Any

from scripts.ego_kernel.state import canonical_sha256


FROZEN_CONSTANTS: dict[str, Any] = {
    "env_version": "r1_env_v2",
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
    "preview_window": [200, 300],
    "preview_topics": [0, 1, 2, 3],
    "drift2_tick": 450,
    "drift2_topics": [4, 5, 6, 7],
    "preview_window_2": [350, 450],
    "preview_topics_2": [4, 5, 6, 7],
    "guaranteed_preview": "deterministic insertion, topics asc, first suggestion-free tick, zero rng draws",
    "benign_value_floor": 0.03,
    "potency_eligibility": "governing_poison_mask_v1",
    "attribution_rule": "poison_row_attribution_v1",
    "run_grid": {"dev_seeds": [31, 47], "heldout_seeds": [61, 79], "episodes_per_seed": 3, "ticks": 600, "drift_tick": 300},
    "containment_aggregation": "pooled_over_episodes",
    "pref_alpha": 0.2,
    "memory_beta": 1.0,
    "guard_seconds_per_phase": 3600,
}

THRESHOLD_SOURCE_TABLE = [
    {"constant": "env_version", "value": "r1_env_v2", "threshold_source": "second drift wave plus deterministic preview insertion; rng sequence and poison logic byte-unchanged"},
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
    {"constant": "preview_window", "value": [200, 300], "threshold_source": "ends at drift tick; W=150 straddles the drift boundary"},
    {"constant": "preview_topics", "value": [0, 1, 2, 3], "threshold_source": "the only topics where future-truth differs from current-truth"},
    {"constant": "drift2_tick", "value": 450, "threshold_source": "splits the drifted segment into two approximately 150-tick waves"},
    {"constant": "drift2_topics", "value": [4, 5, 6, 7], "threshold_source": "disjoint from wave 1; no interaction with wave-1 previews"},
    {"constant": "drift2_rule", "value": "(wave1[t]+1+(t%2))%4", "threshold_source": "mirrors the frozen wave-1 rule"},
    {"constant": "preview_window_2", "value": [350, 450], "threshold_source": "ends at drift2 tick; W=150 straddles the second drift boundary"},
    {"constant": "preview_topics_2", "value": [4, 5, 6, 7], "threshold_source": "the only topics whose future truth differs in wave 2"},
    {"constant": "guaranteed_preview", "value": "deterministic insertion, topics asc, first suggestion-free tick, zero rng draws", "threshold_source": "removes stochastic zero-coverage episodes without touching rng or poison generation"},
    {"constant": "benign_value_floor", "value": 0.03, "threshold_source": "v0 frozen equivalence_MDE; axis must beat house indistinguishability band"},
    {"constant": "potency_eligibility", "value": "governing_poison_mask_v1", "threshold_source": "matches promote-all latest-governs semantics and v0 harm-accounting principle"},
    {"constant": "attribution_rule", "value": "poison_row_attribution_v1", "threshold_source": "restores promotion-level attribution wording with fail-able controls"},
    {"constant": "run_grid", "value": {"dev_seeds": [31, 47], "heldout_seeds": [61, 79], "episodes_per_seed": 3, "ticks": 600, "drift_tick": 300}, "threshold_source": "held-out seeds pre-registered; dev seeds preserve v0 diagnosis surface"},
    {"constant": "guard", "value": "3600 s / phase", "threshold_source": "about 6x measured v0 battery"},
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


def _preference_waves(seed: int, episode_index: int) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    rng = random.Random(int(seed) * 101 + int(episode_index))
    initial = {topic: rng.randrange(FROZEN_CONSTANTS["options_per_topic"]) for topic in range(FROZEN_CONSTANTS["K_topics"])}
    drifted = dict(initial)
    for topic in range(4):
        drifted[topic] = (drifted[topic] + 1 + (topic % 2)) % FROZEN_CONSTANTS["options_per_topic"]
    drift2 = dict(drifted)
    for topic in FROZEN_CONSTANTS["drift2_topics"]:
        drift2[topic] = (drifted[topic] + 1 + (topic % 2)) % FROZEN_CONSTANTS["options_per_topic"]
    return initial, drifted, drift2


def _prefs(seed: int, episode_index: int) -> tuple[dict[int, int], dict[int, int]]:
    initial, drifted, _drift2 = _preference_waves(seed, episode_index)
    return initial, drifted


def true_option_for_tick(
    initial: dict[int, int],
    drifted: dict[int, int],
    *,
    topic: int,
    tick: int,
    drift2: dict[int, int] | None = None,
) -> int:
    topic = int(topic)
    tick = int(tick)
    if drift2 is not None and tick > FROZEN_CONSTANTS["drift2_tick"]:
        return int(drift2[topic])
    return int((drifted if tick > FROZEN_CONSTANTS["run_grid"]["drift_tick"] else initial)[topic])


def _preview_claim_for(
    *,
    env_version: str,
    tick: int,
    topic: int,
    drifted: dict[int, int],
    drift2: dict[int, int],
) -> int | None:
    if (
        env_version in {"r1_env_v1", "r1_env_v2"}
        and FROZEN_CONSTANTS["preview_window"][0] <= tick <= FROZEN_CONSTANTS["preview_window"][1]
        and topic in set(FROZEN_CONSTANTS["preview_topics"])
    ):
        return int(drifted[topic])
    if (
        env_version == "r1_env_v2"
        and FROZEN_CONSTANTS["preview_window_2"][0] <= tick <= FROZEN_CONSTANTS["preview_window_2"][1]
        and topic in set(FROZEN_CONSTANTS["preview_topics_2"])
    ):
        return int(drift2[topic])
    return None


def _insert_missing_previews(
    rows: list[dict[str, Any]],
    *,
    window: list[int],
    topics: list[int],
    claims: dict[int, int],
) -> None:
    present = {
        int(row["suggestion"]["topic"])
        for row in rows
        if window[0] <= int(row["tick"]) <= window[1]
        and row.get("suggestion")
        and row["suggestion"].get("preview")
        and int(row["suggestion"]["topic"]) in set(topics)
    }
    used_ticks: set[int] = set()
    for topic in sorted(topics):
        if topic in present:
            continue
        for row in rows:
            tick = int(row["tick"])
            if tick in used_ticks:
                continue
            if window[0] <= tick <= window[1] and row.get("suggestion") is None:
                claim = int(claims[topic])
                row["suggestion"] = {
                    "topic": int(topic),
                    "claimed_option": claim,
                    "clean_claimed_option": claim,
                    "content_payload": f"preference-note topic-{topic} ordinary wording",
                    "is_poison": False,
                    "preview": True,
                }
                used_ticks.add(tick)
                break


def generate_fixture(*, seed: int, episode_index: int, ticks: int | None = None, env_version: str | None = None) -> list[dict[str, Any]]:
    env_version = env_version or FROZEN_CONSTANTS["env_version"]
    ticks = int(ticks or FROZEN_CONSTANTS["run_grid"]["ticks"])
    rng = random.Random((int(seed) * 1009) + int(episode_index))
    initial, drifted, drift2 = _preference_waves(seed, episode_index)
    active_drift2 = drift2 if env_version == "r1_env_v2" else None
    rows = []
    for tick in range(1, ticks + 1):
        topic = (tick - 1) % FROZEN_CONSTANTS["K_topics"]
        true_option = true_option_for_tick(initial, drifted, drift2=active_drift2, topic=topic, tick=tick)
        revealed = rng.randrange(FROZEN_CONSTANTS["options_per_topic"]) if rng.random() < FROZEN_CONSTANTS["reveal_noise_epsilon"] else true_option
        suggestion = None
        if rng.random() < FROZEN_CONSTANTS["p_sugg"]:
            s_topic = rng.randrange(FROZEN_CONSTANTS["K_topics"])
            clean = true_option_for_tick(initial, drifted, drift2=active_drift2, topic=s_topic, tick=tick)
            poisoned = rng.random() < FROZEN_CONSTANTS["rho"]
            preview_claim = None if poisoned else _preview_claim_for(
                env_version=env_version,
                tick=tick,
                topic=s_topic,
                drifted=drifted,
                drift2=drift2,
            )
            preview = preview_claim is not None
            claim = (clean + 1) % FROZEN_CONSTANTS["options_per_topic"] if poisoned else (preview_claim if preview else clean)
            suggestion = {
                "topic": s_topic,
                "claimed_option": claim,
                "clean_claimed_option": clean if poisoned else claim,
                "content_payload": f"preference-note topic-{s_topic} ordinary wording",
                "is_poison": poisoned,
            }
            if preview:
                suggestion["preview"] = True
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
            "drift2_preferences": drift2,
        })
    if env_version == "r1_env_v2":
        _insert_missing_previews(
            rows,
            window=FROZEN_CONSTANTS["preview_window"],
            topics=FROZEN_CONSTANTS["preview_topics"],
            claims=drifted,
        )
        _insert_missing_previews(
            rows,
            window=FROZEN_CONSTANTS["preview_window_2"],
            topics=FROZEN_CONSTANTS["preview_topics_2"],
            claims=drift2,
        )
    return rows
