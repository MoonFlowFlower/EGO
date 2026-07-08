from pathlib import Path

from scripts.ego_pet.world import (
    apply_user_event,
    build_observation,
    load_world_config,
    quantize_tick,
    regime_id_for_tick,
    zero_world_state,
)


ROOT = Path(__file__).resolve().parents[1]


def test_world_config_loads_and_regime_switches_at_frozen_boundaries():
    config = load_world_config()

    assert config["world"]["K"] == 3
    assert config["time"]["window_W_ticks"] == 50
    assert regime_id_for_tick(config, 199) == "R0_pre_shift"
    assert regime_id_for_tick(config, 200) == "R1_shift_a"
    assert regime_id_for_tick(config, 399) == "R1_shift_a"
    assert regime_id_for_tick(config, 400) == "R2_shift_b"


def test_interaction_effects_rate_caps_and_tick_quantization():
    config = load_world_config()
    state = zero_world_state(config)

    state, first = apply_user_event(state, {"event_type": "feed", "tick_index": 0}, config)
    state, second = apply_user_event(state, {"event_type": "feed", "tick_index": 1}, config)

    assert first["admitted"] is True
    assert second["admitted"] is False
    assert second["reason"] == "rate_limited"
    assert quantize_tick(3.8, current_tick=2) == 3
    assert quantize_tick(1.1, current_tick=2) == 2


def test_observation_is_tick_indexed_without_wall_clock():
    config = load_world_config()
    state = zero_world_state(config)
    observation = build_observation(state, config)

    assert observation["tick_index"] == 0
    assert "wall_clock" not in observation
    assert observation["regime_id"] == "R0_pre_shift"

