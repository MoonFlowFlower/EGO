import json
from pathlib import Path

from scripts.ego_kernel.memory_substate import (
    apply_memory_policy,
    detect_quarantine_contract,
    zero_memory_owned,
    zero_memory_quarantine,
)
from scripts.ego_kernel.pref_learner import PrefLearner, static_pref_standin
from scripts.ego_kernel.suggestion_env import FROZEN_CONSTANTS, generate_fixture
from scripts.run_ego_r1_memory_validation import build_config, run_episode, replay_episode


def test_frozen_config_contains_card_constants_and_pooled_containment_pin():
    config = build_config(code_path_hash="unit-hash")
    constants = {row["constant"]: row["value"] for row in config["threshold_source_table"]}

    assert constants == {
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
    }
    assert FROZEN_CONSTANTS["containment_aggregation"] == "pooled_over_episodes"
    assert config["containment_aggregation"] == "pooled_over_episodes"
    assert config["claim_ceiling"] == "memory_ownership_engineering_only"


def test_external_writes_quarantine_until_two_kernel_corroborations():
    owned = zero_memory_owned()
    quarantine = zero_memory_quarantine()
    suggestion = {"topic": 3, "claimed_option": 2, "content_payload": "mimetic", "is_poison": False}

    owned, quarantine, events = apply_memory_policy(
        owned,
        quarantine,
        tick=10,
        episode_id="unit",
        user_event={"topic": 3, "revealed_option": 1},
        suggestion=suggestion,
        policy_id="ownership_v0",
    )
    assert events["write_event"]["class"] == "quarantined_external"
    assert owned["entries"] == []
    assert len(quarantine["entries"]) == 1

    for tick in (11, 12):
        owned, quarantine, events = apply_memory_policy(
            owned,
            quarantine,
            tick=tick,
            episode_id="unit",
            user_event={"topic": 3, "revealed_option": 2},
            suggestion=None,
            policy_id="ownership_v0",
        )
    assert len(owned["entries"]) == 1
    assert events["promotion_events"][0]["corroboration_count"] == 2
    assert detect_quarantine_contract([events], variant="ownership_v0")["candidate_contract_ok"] is True


def test_permissive_policy_is_detected_as_quarantine_contract_violation():
    owned, quarantine, events = apply_memory_policy(
        zero_memory_owned(),
        zero_memory_quarantine(),
        tick=1,
        episode_id="unit",
        user_event={"topic": 1, "revealed_option": 2},
        suggestion={"topic": 1, "claimed_option": 2, "content_payload": "mimetic", "is_poison": False},
        policy_id="permissive_write_v0",
    )
    assert quarantine["entries"] == []
    assert owned["entries"][0]["origin_class"] == "quarantined_external"
    report = detect_quarantine_contract([events], variant="permissive_write_v0")
    assert report["candidate_contract_ok"] is False
    assert report["direct_external_owned_writes"] == 1


def test_pref_learner_fit_tracks_drift_better_than_static_standin():
    learner = PrefLearner(topic_count=2, option_count=4, alpha=0.2)
    for _ in range(8):
        learner.fit(topic=0, option=1)
    before = learner.predict(0)
    for _ in range(8):
        learner.fit(topic=0, option=3)
    after = learner.predict(0)

    assert before == 1
    assert after == 3
    assert static_pref_standin({0: 1}, topic=0) == 1


def test_tiny_episode_replay_recomputes_actions_from_serialized_state(tmp_path):
    fixture = generate_fixture(seed=31, episode_index=0, ticks=32)
    result = run_episode(
        fixture=fixture,
        run_id="unit-run",
        episode_id="unit-ep",
        policy_id="ownership_v0",
        variant="candidate_injected",
        checkpoints={16},
    )
    replayed = replay_episode(result["initial_state"], fixture)
    assert [row["action"] for row in result["trace_rows"]] == [row["action"] for row in replayed["trace_rows"]]

    resumed = replay_episode(result["checkpoints"]["16"], fixture[16:])
    assert [row["action"] for row in result["trace_rows"][16:]] == [row["action"] for row in resumed["trace_rows"]]

    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in result["trace_rows"]) + "\n")
    assert trace_path.read_text(encoding="utf-8").count("\n") == len(result["trace_rows"])
