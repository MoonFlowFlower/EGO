"""Replayable, default-off causal-nursery runtime for one bounded V2 demo.

The learner sees only :data:`PUBLIC_OBSERVATION_FIELDS`.  Hidden mechanism
assignments live in the environment/evaluator state and are never copied into
the learner or equal-access baseline inputs.  This module is product-demo
engineering with ``science_weight=0``; it is not a general causal-reasoning or
electronic-life claim.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .engine import EngineInvariantError, StepResult


ACTIONS = ("consume", "interact", "wait")
PUBLIC_OBSERVATION_FIELDS = (
    "feature_a",
    "feature_b",
    "local_state",
    "energy",
    "last_action",
    "last_observed_delta",
)
RUNTIME_PROFILE = "causal_sprout_v1"
STATE_SCHEMA_VERSION = "ego.causal_sprout.state.v1"
RUN_SCHEMA_VERSION = "ego.causal_sprout.run.v1"
COMMAND_SCHEMA_VERSION = "ego.causal_sprout.command.v1"
TRACE_SCHEMA_VERSION = "ego.causal_sprout.trace.v1"
LEARNER_SCHEMA_VERSION = "ego.causal_sprout.tiny_rnn.v1"
INPUT_DIM = 12
NUMERIC_BACKEND_VERSION = "2.2.6"

FORBIDDEN_INPUT_FRAGMENTS = (
    "hidden",
    "causal",
    "spurious",
    "context",
    "world",
    "seed",
    "split",
    "oracle",
    "future",
    "verdict",
    "fixture",
    "file",
    "hash",
    "mechanism",
)

DEFAULT_INTERVENTIONS = {
    "update_mode": "canonical",
    "history_mode": "canonical",
    "feedback_mode": "canonical",
    "weights_mode": "canonical",
    "nuisance_mode": "canonical",
    "mechanism_mode": "canonical",
}

BASELINE_NAMES = (
    "no_update_neural",
    "feed_forward_no_history",
    "feature_action_lookup",
    "nearest_neighbour",
    "surface_only",
    "shuffled_feedback",
    "random_policy",
    "bayesian_causal_reference",
    "constant_zero",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _round(value: float) -> float:
    return float(round(float(value), 12))


def _stable_u64(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _stable_unit(*parts: Any) -> float:
    return _stable_u64(*parts) / float(2**64 - 1)


@dataclass(frozen=True)
class CausalSproutConfig:
    namespace_prefix: str
    split: str
    context_count: int
    steps_per_context: int
    hidden_size: int = 24
    bptt_steps: int = 8
    learning_rate: float = 0.012
    correlation_probability: float = 0.9
    seed: int = 918273
    momentum: float = 0.85
    exploration_rate: float = 0.45

    def __post_init__(self) -> None:
        if not self.namespace_prefix.startswith("causal_sprout_"):
            raise ValueError("causal nursery namespace must start with causal_sprout_")
        if self.split not in {"dev", "heldout"}:
            raise ValueError("split must be dev or heldout")
        if type(self.context_count) is not int or self.context_count <= 0:
            raise ValueError("context_count must be positive")
        if type(self.steps_per_context) is not int or self.steps_per_context < 4:
            raise ValueError("steps_per_context must be at least four")
        if not 16 <= self.hidden_size <= 32:
            raise ValueError("hidden_size must remain within 16..32")
        if type(self.bptt_steps) is not int or not 1 <= self.bptt_steps <= 16:
            raise ValueError("bptt_steps must be within 1..16")
        if not math.isfinite(self.learning_rate) or self.learning_rate < 0.0:
            raise ValueError("learning_rate must be non-negative and finite")
        if not 0.0 <= self.correlation_probability <= 1.0:
            raise ValueError("correlation_probability must be within 0..1")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer RNG parameter")
        if not 0.0 <= self.momentum < 1.0:
            raise ValueError("momentum must be within [0,1)")
        if not 0.0 <= self.exploration_rate <= 1.0:
            raise ValueError("exploration_rate must be within [0,1]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_contexts(config: CausalSproutConfig) -> list[dict[str, Any]]:
    """Generate private evaluator contexts from a task-local string namespace."""

    contexts: list[dict[str, Any]] = []
    for index in range(config.context_count):
        context_name = f"{config.namespace_prefix}_{index:04d}"
        channel = "feature_a" if _stable_u64(config.seed, context_name, "channel") % 2 == 0 else "feature_b"
        sign = 1 if _stable_u64(config.seed, context_name, "mapping") % 2 == 0 else -1
        channel_order = (
            ["inner_left", "inner_right"]
            if _stable_u64(config.seed, context_name, "order") % 2 == 0
            else ["inner_right", "inner_left"]
        )
        glyph_values = [
            f"g{_stable_u64(config.seed, context_name, 'glyph', value) % 997:03d}"
            for value in (-1, 1)
        ]
        contexts.append(
            {
                "schema_version": "ego.causal_sprout.private_context.v1",
                "context_name": context_name,
                "hidden_mechanism_channel": channel,
                "hidden_mapping_sign": sign,
                "channel_order": channel_order,
                "glyph_encoding": {"negative": glyph_values[0], "positive": glyph_values[1]},
                "nuisance_correlation_probability": float(config.correlation_probability),
                "mechanism_shift_at": (
                    config.steps_per_context // 2
                    if config.split == "heldout" and index % 4 == 3
                    else None
                ),
                "feature_permutation": index % 2 == 1,
            }
        )
    return contexts


def _feature_values(
    context: Mapping[str, Any],
    row_index: int,
    *,
    nuisance_mode: str = "canonical",
) -> tuple[float, float]:
    # Every context begins with the same public factorial stimulus block.  It
    # is independent of the hidden channel/mapping and therefore supplies
    # information without telling the learner which feature is relevant.
    if row_index < 4:
        return (
            (-1.0, -1.0),
            (-1.0, 1.0),
            (1.0, -1.0),
            (1.0, 1.0),
        )[row_index]
    causal_value = -1.0 if _stable_u64(context["context_name"], row_index, "causal") % 2 == 0 else 1.0
    probability = float(context["nuisance_correlation_probability"])
    correlated = _stable_unit(context["context_name"], row_index, "nuisance") < probability
    nuisance_value = causal_value if correlated else -causal_value
    if nuisance_mode == "permuted":
        nuisance_value *= -1.0
    channel = str(context["hidden_mechanism_channel"])
    if channel == "feature_a":
        return causal_value, nuisance_value
    return nuisance_value, causal_value


def _public_observation(
    context: Mapping[str, Any],
    row_index: int,
    *,
    steps_per_context: int,
    energy: float,
    last_action: str | None,
    last_observed_delta: float,
    nuisance_mode: str = "canonical",
) -> dict[str, Any]:
    feature_a, feature_b = _feature_values(context, row_index, nuisance_mode=nuisance_mode)
    return {
        "feature_a": float(feature_a),
        "feature_b": float(feature_b),
        "local_state": _round(row_index / max(1, steps_per_context - 1)),
        "energy": _round(energy),
        "last_action": last_action,
        "last_observed_delta": _round(last_observed_delta),
    }


def _mapping_sign(context: Mapping[str, Any], row_index: int, mechanism_mode: str) -> int:
    sign = int(context["hidden_mapping_sign"])
    shift_at = context.get("mechanism_shift_at")
    if mechanism_mode == "shifted" or (shift_at is not None and row_index >= int(shift_at)):
        sign *= -1
    return sign


def _oracle_delta(
    context: Mapping[str, Any],
    observation: Mapping[str, Any],
    action: str,
    *,
    row_index: int,
    mechanism_mode: str = "canonical",
) -> float:
    if action == "wait":
        return -0.025
    action_sign = 1.0 if action == "consume" else -1.0
    causal_value = float(observation[str(context["hidden_mechanism_channel"])])
    return _round(0.30 * action_sign * _mapping_sign(context, row_index, mechanism_mode) * causal_value)


def build_paired_interventions(
    context: Mapping[str, Any],
    row_index: int,
    *,
    base_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build exact nuisance-only and mechanism-variable pairs for the evaluator."""

    if base_observation is None:
        base_a, base_b = _feature_values(context, row_index)
        held_equal = {
            "local_state": 0.5,
            "energy": 0.6,
            "last_action": "wait",
            "last_observed_delta": -0.025,
        }
    else:
        if set(base_observation) != set(PUBLIC_OBSERVATION_FIELDS):
            raise EngineInvariantError("paired-intervention base observation schema mismatch")
        base_a = float(base_observation["feature_a"])
        base_b = float(base_observation["feature_b"])
        held_equal = {
            key: deepcopy(base_observation[key])
            for key in (
                "local_state",
                "energy",
                "last_action",
                "last_observed_delta",
            )
        }
    channel = str(context["hidden_mechanism_channel"])
    nuisance = "feature_b" if channel == "feature_a" else "feature_a"

    def make(a: float, b: float) -> dict[str, Any]:
        observation = {
            "feature_a": float(a),
            "feature_b": float(b),
            **held_equal,
        }
        return {
            "public_observation": observation,
            "oracle_delta_by_action": {
                action: _oracle_delta(context, observation, action, row_index=row_index)
                for action in ACTIONS
            },
        }

    nuisance_values = {"feature_a": base_a, "feature_b": base_b}
    nuisance_flipped = dict(nuisance_values)
    nuisance_flipped[nuisance] *= -1.0
    mechanism_flipped = dict(nuisance_values)
    mechanism_flipped[channel] *= -1.0
    return {
        "nuisance_only": (
            make(nuisance_values["feature_a"], nuisance_values["feature_b"]),
            make(nuisance_flipped["feature_a"], nuisance_flipped["feature_b"]),
        ),
        "mechanism": (
            make(nuisance_values["feature_a"], nuisance_values["feature_b"]),
            make(mechanism_flipped["feature_a"], mechanism_flipped["feature_b"]),
        ),
    }


def scan_public_input_leakage(payload: Any, *, positive_control: bool = False) -> dict[str, Any]:
    forbidden: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                key_text = str(key).lower()
                child = f"{path}.{key}" if path else str(key)
                if any(fragment in key_text for fragment in FORBIDDEN_INPUT_FRAGMENTS):
                    forbidden.append(child)
                visit(nested, child)
        elif isinstance(value, (list, tuple)):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]")

    visit(payload, "")
    return {
        "accepted": not forbidden,
        "forbidden_paths": sorted(forbidden),
        "positive_control": bool(positive_control),
    }


def _encode_observation(observation: Mapping[str, Any]) -> np.ndarray:
    if set(observation) != set(PUBLIC_OBSERVATION_FIELDS):
        raise EngineInvariantError("learner observation schema mismatch")
    leakage = scan_public_input_leakage(observation)
    if not leakage["accepted"]:
        raise EngineInvariantError(f"learner input leakage: {leakage['forbidden_paths']}")
    action = observation["last_action"]
    if action is not None and action not in ACTIONS:
        raise EngineInvariantError("last_action is not public/canonical")
    action_vector = [1.0 if action == candidate else 0.0 for candidate in ACTIONS]
    feature_a = float(observation["feature_a"])
    feature_b = float(observation["feature_b"])
    local_state = float(observation["local_state"])
    energy = float(observation["energy"])
    last_delta = float(observation["last_observed_delta"])
    values = np.asarray(
        [
            feature_a,
            feature_b,
            local_state,
            energy,
            last_delta,
            *action_vector,
            feature_a * feature_b,
            feature_a * last_delta,
            feature_b * last_delta,
            1.0,
        ],
        dtype=np.float64,
    )
    if values.shape != (INPUT_DIM,) or not np.all(np.isfinite(values)):
        raise EngineInvariantError("encoded public observation is invalid")
    return values


def _weight_shapes(hidden_size: int) -> dict[str, tuple[int, ...]]:
    action_count = len(ACTIONS)
    return {
        "w_xh": (hidden_size, INPUT_DIM),
        "w_hh": (hidden_size, hidden_size),
        "b_h": (hidden_size,),
        "w_delta": (action_count, hidden_size),
        "b_delta": (action_count,),
        "w_risk": (action_count, hidden_size),
        "b_risk": (action_count,),
        "w_policy": (action_count, hidden_size),
        "b_policy": (action_count,),
    }


def _arrays(mapping: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return {key: np.asarray(value, dtype=np.float64) for key, value in mapping.items()}


def _lists(mapping: Mapping[str, np.ndarray]) -> dict[str, list[Any]]:
    return {key: value.astype(np.float64).tolist() for key, value in mapping.items()}


def _model_payload(learner: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": learner["schema_version"],
        "hidden_size": learner["hidden_size"],
        "weights": learner["weights"],
    }


def _optimizer_payload(learner: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "optimizer_state": learner["optimizer_state"],
        "learning_rate": learner["learning_rate"],
        "momentum": learner["momentum"],
        "update_count": learner["update_count"],
    }


def _refresh_learner_hashes(learner: Mapping[str, Any]) -> dict[str, Any]:
    refreshed = deepcopy(dict(learner))
    refreshed["model_hash"] = canonical_hash(_model_payload(refreshed))
    refreshed["optimizer_hash"] = canonical_hash(_optimizer_payload(refreshed))
    refreshed["recurrent_state_hash"] = canonical_hash(refreshed["hidden_state"])
    return refreshed


def create_learner(
    *, hidden_size: int = 24, seed: int = 17, learning_rate: float = 0.012, bptt_steps: int = 8
) -> dict[str, Any]:
    if not 16 <= hidden_size <= 32:
        raise ValueError("hidden_size must be within 16..32")
    rng = np.random.Generator(np.random.PCG64(seed))
    shapes = _weight_shapes(hidden_size)
    weights: dict[str, np.ndarray] = {}
    for name, shape in shapes.items():
        if name.startswith("b_"):
            weights[name] = np.zeros(shape, dtype=np.float64)
        else:
            # Hidden dynamics need expressive variance; prediction/value heads
            # start near the honest zero predictor so untrained random logits
            # cannot masquerade as a learned effect and early online gradients
            # remain well scaled.
            scale = (
                0.025
                if name in {"w_delta", "w_risk", "w_policy"}
                else 1.0 / math.sqrt(shape[-1])
            )
            weights[name] = rng.normal(0.0, scale, size=shape).astype(np.float64)
    # A generic leaky-memory initialization preserves recent public history
    # long enough for BPTT to discover a decoder. It is feature/token agnostic:
    # no cell is assigned a causal channel, mapping, action, or context class.
    weights["w_hh"] = (
        0.72 * np.eye(hidden_size, dtype=np.float64)
        + 0.02 * weights["w_hh"]
    )
    optimizer = {name: np.zeros(shape, dtype=np.float64) for name, shape in shapes.items()}
    learner = {
        "schema_version": LEARNER_SCHEMA_VERSION,
        "hidden_size": hidden_size,
        "weights": _lists(weights),
        "optimizer_state": _lists(optimizer),
        "hidden_state": np.zeros(hidden_size, dtype=np.float64).tolist(),
        "bptt_buffer": [],
        "rng_state": deepcopy(rng.bit_generator.state),
        "learning_rate": float(learning_rate),
        "momentum": 0.85,
        "bptt_steps": int(bptt_steps),
        "update_count": 0,
        "forward_count": 0,
        "model_hash": "",
        "optimizer_hash": "",
        "recurrent_state_hash": "",
    }
    return _refresh_learner_hashes(learner)


def _validate_learner(learner: Mapping[str, Any]) -> None:
    if learner.get("schema_version") != LEARNER_SCHEMA_VERSION:
        raise EngineInvariantError("learner schema mismatch")
    hidden_size = int(learner["hidden_size"])
    shapes = _weight_shapes(hidden_size)
    for field in ("weights", "optimizer_state"):
        arrays = _arrays(learner[field])
        if set(arrays) != set(shapes):
            raise EngineInvariantError(f"learner {field} keys mismatch")
        for name, shape in shapes.items():
            if arrays[name].shape != shape or not np.all(np.isfinite(arrays[name])):
                raise EngineInvariantError(f"learner {field}.{name} shape/value mismatch")
    hidden = np.asarray(learner["hidden_state"], dtype=np.float64)
    if hidden.shape != (hidden_size,) or not np.all(np.isfinite(hidden)):
        raise EngineInvariantError("learner hidden state mismatch")
    if learner.get("model_hash") != canonical_hash(_model_payload(learner)):
        raise EngineInvariantError("learner model hash mismatch")
    if learner.get("optimizer_hash") != canonical_hash(_optimizer_payload(learner)):
        raise EngineInvariantError("learner optimizer hash mismatch")
    if learner.get("recurrent_state_hash") != canonical_hash(learner["hidden_state"]):
        raise EngineInvariantError("learner recurrent state hash mismatch")


def reset_recurrent_state(learner: Mapping[str, Any]) -> dict[str, Any]:
    reset = deepcopy(dict(learner))
    reset["hidden_state"] = np.zeros(int(reset["hidden_size"]), dtype=np.float64).tolist()
    reset["bptt_buffer"] = []
    return _refresh_learner_hashes(reset)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def forward_learner(
    learner: Mapping[str, Any], observation: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _validate_learner(learner)
    x = _encode_observation(observation)
    weights = _arrays(learner["weights"])
    h_prev = np.asarray(learner["hidden_state"], dtype=np.float64)
    h = np.tanh(weights["w_xh"] @ x + weights["w_hh"] @ h_prev + weights["b_h"])
    delta = weights["w_delta"] @ h + weights["b_delta"]
    risk = _sigmoid(weights["w_risk"] @ h + weights["b_risk"])
    policy = weights["w_policy"] @ h + weights["b_policy"]
    prediction = {
        "predicted_delta_by_action": {
            action: _round(delta[index]) for index, action in enumerate(ACTIONS)
        },
        "terminal_risk_by_action": {
            action: _round(risk[index]) for index, action in enumerate(ACTIONS)
        },
        "policy_logits_by_action": {
            action: _round(policy[index]) for index, action in enumerate(ACTIONS)
        },
    }
    cache = {
        "x": x.tolist(),
        "h_prev": h_prev.tolist(),
        "h": h.tolist(),
        "prediction": deepcopy(prediction),
        "public_input_hash": canonical_hash(dict(observation)),
    }
    advanced = deepcopy(dict(learner))
    advanced["hidden_state"] = h.tolist()
    advanced["forward_count"] = int(advanced["forward_count"]) + 1
    advanced = _refresh_learner_hashes(advanced)
    return prediction, cache, advanced


def _training_record(cache: Mapping[str, Any], action_index: int, target: float) -> dict[str, Any]:
    return {
        "x": deepcopy(cache["x"]),
        "h_prev": deepcopy(cache["h_prev"]),
        "h": deepcopy(cache["h"]),
        "action_index": int(action_index),
        "target": float(target),
    }


def _bptt_gradients(
    weights: Mapping[str, np.ndarray], records: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, np.ndarray], float]:
    gradients = {name: np.zeros_like(value) for name, value in weights.items()}
    dh_next = np.zeros(weights["w_hh"].shape[0], dtype=np.float64)
    total_loss = 0.0
    for record in reversed(records):
        x = np.asarray(record["x"], dtype=np.float64)
        h_prev = np.asarray(record["h_prev"], dtype=np.float64)
        h = np.asarray(record["h"], dtype=np.float64)
        index = int(record["action_index"])
        target = float(record["target"])

        delta_values = weights["w_delta"] @ h + weights["b_delta"]
        risk_values = _sigmoid(weights["w_risk"] @ h + weights["b_risk"])
        policy_values = weights["w_policy"] @ h + weights["b_policy"]
        delta_error = float(delta_values[index] - target)
        risk_target = 1.0 if target <= -0.15 else 0.0
        risk_error = float(risk_values[index] - risk_target)
        policy_error = float(policy_values[index] - target)
        total_loss += 0.5 * delta_error**2 + 0.05 * risk_error**2 + 0.025 * policy_error**2

        g_delta = np.zeros(len(ACTIONS), dtype=np.float64)
        g_risk = np.zeros(len(ACTIONS), dtype=np.float64)
        g_policy = np.zeros(len(ACTIONS), dtype=np.float64)
        g_delta[index] = delta_error
        g_risk[index] = 0.10 * risk_error * risk_values[index] * (1.0 - risk_values[index])
        g_policy[index] = 0.05 * policy_error

        gradients["w_delta"] += np.outer(g_delta, h)
        gradients["b_delta"] += g_delta
        gradients["w_risk"] += np.outer(g_risk, h)
        gradients["b_risk"] += g_risk
        gradients["w_policy"] += np.outer(g_policy, h)
        gradients["b_policy"] += g_policy
        dh = (
            weights["w_delta"].T @ g_delta
            + weights["w_risk"].T @ g_risk
            + weights["w_policy"].T @ g_policy
            + dh_next
        )
        dz = dh * (1.0 - h**2)
        gradients["w_xh"] += np.outer(dz, x)
        gradients["w_hh"] += np.outer(dz, h_prev)
        gradients["b_h"] += dz
        dh_next = weights["w_hh"].T @ dz

    scale = 1.0 / max(1, len(records))
    for name in gradients:
        gradients[name] *= scale
    return gradients, total_loss * scale


def update_learner(
    learner: Mapping[str, Any],
    cache: Mapping[str, Any],
    *,
    selected_action: str,
    actual_delta: float,
    update_mode: str = "canonical",
    defer_until_full: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _validate_learner(learner)
    if selected_action not in ACTIONS:
        raise EngineInvariantError("selected_action is not canonical")
    if update_mode not in {"canonical", "frozen"}:
        raise EngineInvariantError("update_mode is not canonical")
    if update_mode == "frozen" or float(learner["learning_rate"]) == 0.0:
        return deepcopy(dict(learner)), {
            "applied": False,
            "reason": "updates_frozen" if update_mode == "frozen" else "zero_learning_rate",
            "gradient_norm": 0.0,
            "loss": _round(
                0.5
                * (
                    float(cache["prediction"]["predicted_delta_by_action"][selected_action])
                    - float(actual_delta)
                )
                ** 2
            ),
        }

    updated = deepcopy(dict(learner))
    records = list(updated["bptt_buffer"])
    records.append(_training_record(cache, ACTIONS.index(selected_action), float(actual_delta)))
    records = records[-int(updated["bptt_steps"]) :]
    if defer_until_full and len(records) < int(updated["bptt_steps"]):
        updated["bptt_buffer"] = records
        updated = _refresh_learner_hashes(updated)
        return updated, {
            "applied": False,
            "reason": "accumulating_truncated_bptt",
            "gradient_norm": 0.0,
            "loss": _round(
                0.5
                * (
                    float(cache["prediction"]["predicted_delta_by_action"][selected_action])
                    - float(actual_delta)
                )
                ** 2
            ),
            "bptt_record_count": len(records),
        }
    weights = _arrays(updated["weights"])
    optimizer = _arrays(updated["optimizer_state"])
    gradients, loss = _bptt_gradients(weights, records)
    norm = math.sqrt(sum(float(np.sum(gradient**2)) for gradient in gradients.values()))
    clip_scale = 1.0 if norm <= 5.0 or norm == 0.0 else 5.0 / norm
    learning_rate = float(updated["learning_rate"])
    momentum = float(updated["momentum"])
    for name in weights:
        optimizer[name] = momentum * optimizer[name] + clip_scale * gradients[name]
        weights[name] -= learning_rate * optimizer[name]
    updated["weights"] = _lists(weights)
    updated["optimizer_state"] = _lists(optimizer)
    updated["bptt_buffer"] = [] if defer_until_full else records
    updated["update_count"] = int(updated["update_count"]) + 1
    updated = _refresh_learner_hashes(updated)
    return updated, {
        "applied": True,
        "reason": "online_truncated_bptt_sgd",
        "gradient_norm": _round(norm),
        "gradient_clip_scale": _round(clip_scale),
        "loss": _round(loss),
        "bptt_record_count": len(records),
    }


def finite_difference_gradient_check(*, seed: int = 17) -> dict[str, Any]:
    learner = create_learner(seed=seed)
    observation = {
        "feature_a": -1.0,
        "feature_b": 1.0,
        "local_state": 0.25,
        "energy": 0.6,
        "last_action": "interact",
        "last_observed_delta": -0.2,
    }
    _, cache, _ = forward_learner(learner, observation)
    weights = _arrays(learner["weights"])
    records = [_training_record(cache, 0, 0.3)]
    gradients, _ = _bptt_gradients(weights, records)
    epsilon = 1e-6

    def loss_at(value: float) -> float:
        local = {name: array.copy() for name, array in weights.items()}
        local["w_delta"][0, 0] = value
        _, loss = _bptt_gradients(local, records)
        return float(loss)

    original = float(weights["w_delta"][0, 0])
    numerical = (loss_at(original + epsilon) - loss_at(original - epsilon)) / (2.0 * epsilon)
    analytic = float(gradients["w_delta"][0, 0])
    denominator = max(1e-12, abs(numerical) + abs(analytic))
    return {
        "parameter": "w_delta[0,0]",
        "analytic": analytic,
        "numerical": numerical,
        "max_relative_error": abs(numerical - analytic) / denominator,
        "positive_control": True,
    }


def _empty_baselines(config: CausalSproutConfig) -> dict[str, Any]:
    return {
        "no_update_neural": create_learner(
            hidden_size=config.hidden_size,
            seed=config.seed + 101,
            learning_rate=config.learning_rate,
            bptt_steps=config.bptt_steps,
        ),
        "feed_forward_no_history": create_learner(
            hidden_size=config.hidden_size,
            seed=config.seed + 202,
            learning_rate=config.learning_rate,
            bptt_steps=1,
        ),
        "feature_action_lookup": {"table": {}},
        "nearest_neighbour": {"rows": []},
        "surface_only": {
            "weights": np.zeros((len(ACTIONS), 5), dtype=np.float64).tolist(),
            "counts": [0 for _ in ACTIONS],
        },
        "shuffled_feedback": create_learner(
            hidden_size=config.hidden_size,
            seed=config.seed + 303,
            learning_rate=config.learning_rate,
            bptt_steps=config.bptt_steps,
        ),
        "random_policy": {"calls": 0},
        "bayesian_causal_reference": {"log_scores": [0.0, 0.0, 0.0, 0.0]},
        "constant_zero": {"calls": 0},
    }


def _lookup_key(observation: Mapping[str, Any], action: str) -> str:
    return canonical_json(
        {
            "feature_a": observation["feature_a"],
            "feature_b": observation["feature_b"],
            "local_bucket": int(round(float(observation["local_state"]) * 4)),
            "action": action,
        }
    )


def _baseline_predictions(
    baselines: Mapping[str, Any], observation: Mapping[str, Any]
) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    # Read-only baseline components are shared until their updated replacements
    # are constructed below.  The update phase performs the single defensive
    # copy; copying the growing nearest-neighbour rows three times per tick
    # would make the replayable demo needlessly quadratic.
    working = dict(baselines)
    predictions: dict[str, dict[str, float]] = {}

    no_update_prediction, _, no_update = forward_learner(working["no_update_neural"], observation)
    working["no_update_neural"] = no_update
    predictions["no_update_neural"] = no_update_prediction["predicted_delta_by_action"]

    feed_forward = reset_recurrent_state(working["feed_forward_no_history"])
    feed_prediction, feed_cache, feed_advanced = forward_learner(feed_forward, observation)
    working["feed_forward_no_history"] = feed_advanced
    predictions["feed_forward_no_history"] = feed_prediction["predicted_delta_by_action"]
    working["_feed_forward_cache"] = feed_cache

    table = working["feature_action_lookup"]["table"]
    predictions["feature_action_lookup"] = {}
    for action in ACTIONS:
        cell = table.get(_lookup_key(observation, action), {"sum": 0.0, "count": 0})
        predictions["feature_action_lookup"][action] = _round(
            float(cell["sum"]) / max(1, int(cell["count"]))
        )

    vector = _encode_observation(observation)
    nearest_rows = working["nearest_neighbour"]["rows"]
    predictions["nearest_neighbour"] = {}
    for action in ACTIONS:
        candidates = [row for row in nearest_rows if row["action"] == action]
        if not candidates:
            predictions["nearest_neighbour"][action] = 0.0
        else:
            closest = min(
                candidates,
                key=lambda row: float(
                    np.sum((np.asarray(row["vector"], dtype=np.float64) - vector) ** 2)
                ),
            )
            predictions["nearest_neighbour"][action] = _round(closest["delta"])

    surface_features = np.asarray(
        [observation["feature_a"], observation["feature_b"], observation["local_state"], observation["energy"], 1.0],
        dtype=np.float64,
    )
    surface_weights = np.asarray(working["surface_only"]["weights"], dtype=np.float64)
    predictions["surface_only"] = {
        action: _round(surface_weights[index] @ surface_features)
        for index, action in enumerate(ACTIONS)
    }

    shuffled_prediction, shuffled_cache, shuffled_advanced = forward_learner(
        working["shuffled_feedback"], observation
    )
    working["shuffled_feedback"] = shuffled_advanced
    working["_shuffled_cache"] = shuffled_cache
    predictions["shuffled_feedback"] = shuffled_prediction["predicted_delta_by_action"]

    predictions["random_policy"] = {action: 0.0 for action in ACTIONS}
    hypotheses = (("feature_a", 1), ("feature_a", -1), ("feature_b", 1), ("feature_b", -1))
    scores = np.asarray(working["bayesian_causal_reference"]["log_scores"], dtype=np.float64)
    probabilities = np.exp(scores - np.max(scores))
    probabilities /= np.sum(probabilities)
    bayesian: dict[str, float] = {}
    for action in ACTIONS:
        if action == "wait":
            bayesian[action] = -0.025
            continue
        action_sign = 1.0 if action == "consume" else -1.0
        bayesian[action] = _round(
            sum(
                probability * 0.30 * action_sign * sign * float(observation[channel])
                for probability, (channel, sign) in zip(probabilities, hypotheses)
            )
        )
    predictions["bayesian_causal_reference"] = bayesian
    predictions["constant_zero"] = {action: 0.0 for action in ACTIONS}
    return predictions, working


def _update_baselines(
    baselines: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    action: str,
    actual_delta: float,
) -> dict[str, Any]:
    updated = deepcopy(dict(baselines))
    feed_cache = updated.pop("_feed_forward_cache")
    feed, _ = update_learner(
        updated["feed_forward_no_history"],
        feed_cache,
        selected_action=action,
        actual_delta=actual_delta,
        defer_until_full=True,
    )
    updated["feed_forward_no_history"] = reset_recurrent_state(feed)

    key = _lookup_key(observation, action)
    table = updated["feature_action_lookup"]["table"]
    cell = dict(table.get(key, {"sum": 0.0, "count": 0}))
    cell["sum"] = _round(float(cell["sum"]) + actual_delta)
    cell["count"] = int(cell["count"]) + 1
    table[key] = cell

    rows = updated["nearest_neighbour"]["rows"]
    rows.append({"vector": _encode_observation(observation).tolist(), "action": action, "delta": actual_delta})
    updated["nearest_neighbour"]["rows"] = rows[-512:]

    features = np.asarray(
        [observation["feature_a"], observation["feature_b"], observation["local_state"], observation["energy"], 1.0],
        dtype=np.float64,
    )
    surface = updated["surface_only"]
    weights = np.asarray(surface["weights"], dtype=np.float64)
    index = ACTIONS.index(action)
    error = float(weights[index] @ features - actual_delta)
    weights[index] -= 0.02 * error * features
    surface["weights"] = weights.tolist()
    surface["counts"][index] += 1

    shuffled_cache = updated.pop("_shuffled_cache")
    shuffled_target = -actual_delta
    shuffled, _ = update_learner(
        updated["shuffled_feedback"],
        shuffled_cache,
        selected_action=action,
        actual_delta=shuffled_target,
        defer_until_full=True,
    )
    updated["shuffled_feedback"] = shuffled

    hypotheses = (("feature_a", 1), ("feature_a", -1), ("feature_b", 1), ("feature_b", -1))
    scores = np.asarray(updated["bayesian_causal_reference"]["log_scores"], dtype=np.float64)
    for hypothesis_index, (channel, sign) in enumerate(hypotheses):
        expected = -0.025 if action == "wait" else (
            0.30 * (1.0 if action == "consume" else -1.0) * sign * float(observation[channel])
        )
        scores[hypothesis_index] += -20.0 * (actual_delta - expected) ** 2
    updated["bayesian_causal_reference"]["log_scores"] = scores.tolist()
    updated["random_policy"]["calls"] += 1
    updated["constant_zero"]["calls"] += 1
    return updated


def _reset_baseline_history(baselines: Mapping[str, Any]) -> dict[str, Any]:
    reset = deepcopy(dict(baselines))
    for name in ("no_update_neural", "feed_forward_no_history", "shuffled_feedback"):
        reset[name] = reset_recurrent_state(reset[name])
    reset["bayesian_causal_reference"]["log_scores"] = [0.0, 0.0, 0.0, 0.0]
    return reset


def _rng_from_state(state: Mapping[str, Any]) -> np.random.Generator:
    generator = np.random.Generator(np.random.PCG64())
    generator.bit_generator.state = deepcopy(dict(state))
    return generator


class CausalSproutRuntime:
    """Duck-typed reducer adapter shared by controller live dispatch and store replay."""

    runtime_profile = RUNTIME_PROFILE
    default_interventions = DEFAULT_INTERVENTIONS

    def __init__(self, config: CausalSproutConfig, *, initial_learner: Mapping[str, Any] | None = None) -> None:
        if np.__version__ != NUMERIC_BACKEND_VERSION:
            raise EngineInvariantError(
                f"causal sprout requires numpy {NUMERIC_BACKEND_VERSION}; got {np.__version__}"
            )
        self.config = config
        self.contexts = generate_contexts(config)
        self._initial_learner = (
            deepcopy(dict(initial_learner))
            if initial_learner is not None
            else create_learner(
                hidden_size=config.hidden_size,
                seed=config.seed,
                learning_rate=config.learning_rate,
                bptt_steps=config.bptt_steps,
            )
        )
        _validate_learner(self._initial_learner)
        self.initial_model_hash = str(self._initial_learner["model_hash"])

    def compute_code_path_hash(self) -> str:
        paths = (
            Path(__file__),
            Path(__file__).with_name("controller.py"),
            Path(__file__).with_name("store.py"),
        )
        manifest = [
            {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in paths
        ]
        return canonical_hash({"schema_version": "ego.causal_sprout.code_path.v1", "files": manifest})

    def compute_trace_hash(self, trace: Mapping[str, Any]) -> str:
        return canonical_hash({key: value for key, value in trace.items() if key != "trace_hash"})

    def make_run_metadata(self, run_id: str, seed: int) -> dict[str, Any]:
        if type(run_id) is not str or not run_id:
            raise EngineInvariantError("run_id must be non-empty")
        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "runtime_profile": RUNTIME_PROFILE,
            "run_id": run_id,
            "seed": int(seed),
            "config": self.config.to_dict(),
            "config_hash": canonical_hash(self.config.to_dict()),
            "initial_model_hash": self.initial_model_hash,
            "context_assignment_hash": canonical_hash(self.contexts),
            "producer_function": "ego_life_playground_v0.causal_sprout.CausalSproutRuntime.compute_step",
            "aggregation_rule": "single_shared_controller_store_recomputing_reducer",
            "code_path_hash": self.compute_code_path_hash(),
            "science_weight": 0,
            "numeric_runtime": {
                "backend": "numpy",
                "version": NUMERIC_BACKEND_VERSION,
                "dtype": "float64",
            },
        }

    def initial_state(self, *, run_id: str, seed: int) -> dict[str, Any]:
        rng = np.random.Generator(np.random.PCG64(int(seed)))
        learner = deepcopy(self._initial_learner)
        learner["rng_state"] = deepcopy(rng.bit_generator.state)
        learner = _refresh_learner_hashes(learner)
        contexts = deepcopy(self.contexts)
        context_hash = canonical_hash(contexts)
        state = {
            "schema_version": STATE_SCHEMA_VERSION,
            "runtime_profile": RUNTIME_PROFILE,
            "clock": {
                "global_tick": 0,
                "episode_index": 0,
                "episode_id": f"causal-sprout-{canonical_hash([run_id, 0])[:16]}",
                "episode_tick": 0,
            },
            "organism": {"energy": 0.60},
            "learner": learner,
            "baselines": _empty_baselines(self.config),
            "evaluator": {
                "contexts": contexts,
                "context_assignment_hash": context_hash,
                "context_index": 0,
                "row_index": 0,
                "namespace_kind": "task_local_string_context",
            },
            "lifecycle": {
                "trial_status": "active",
                "life_index": 1,
                "awaiting_respawn": False,
                "life_results": [],
                "terminal_life_result": None,
            },
            "last_action": None,
            "last_observed_delta": 0.0,
            "last_command_hash": None,
            "last_trace_hash": None,
            "trace_chain_hash": None,
            "integrity": {
                "initial_model_hash": learner["model_hash"],
                "context_assignment_hash": context_hash,
                "config_hash": canonical_hash(self.config.to_dict()),
            },
        }
        self.verify_replay_boundary(state, self.make_run_metadata(run_id, seed))
        return state

    def make_command(
        self,
        *,
        sequence: int,
        trigger_source: str,
        interventions: Mapping[str, str],
        prev_command_hash: str | None,
        injected_event: str | None = None,
    ) -> dict[str, Any]:
        if injected_event is not None:
            raise EngineInvariantError("causal nursery does not accept operator world events")
        if type(sequence) is not int or sequence <= 0:
            raise EngineInvariantError("command sequence must be positive")
        if type(trigger_source) is not str or not trigger_source:
            raise EngineInvariantError("trigger_source must be non-empty")
        if sequence == 1 and prev_command_hash is not None:
            raise EngineInvariantError("initial command chain must start with null")
        if sequence > 1 and not _is_sha256(prev_command_hash):
            raise EngineInvariantError("command chain hash missing")
        normalized = self._normalize_interventions(interventions)
        command = {
            "schema_version": COMMAND_SCHEMA_VERSION,
            "sequence": sequence,
            "trigger_source": trigger_source,
            "interventions": normalized,
            "prev_command_hash": prev_command_hash,
        }
        command["command_hash"] = canonical_hash(command)
        return command

    def _normalize_interventions(self, interventions: Mapping[str, str]) -> dict[str, str]:
        if set(interventions) != set(DEFAULT_INTERVENTIONS):
            raise EngineInvariantError("causal intervention schema mismatch")
        allowed = {
            "update_mode": {"canonical", "frozen"},
            "history_mode": {"canonical", "reset_each_step"},
            "feedback_mode": {"canonical", "shuffled"},
            "weights_mode": {"canonical", "deleted"},
            "nuisance_mode": {"canonical", "permuted"},
            "mechanism_mode": {"canonical", "shifted"},
        }
        normalized = {key: str(value) for key, value in interventions.items()}
        for key, values in allowed.items():
            if normalized[key] not in values:
                raise EngineInvariantError(f"invalid causal intervention {key}")
        return normalized

    def _verify_metadata(self, run_meta: Mapping[str, Any]) -> None:
        required = {
            "schema_version",
            "runtime_profile",
            "run_id",
            "seed",
            "config",
            "config_hash",
            "initial_model_hash",
            "context_assignment_hash",
            "producer_function",
            "aggregation_rule",
            "code_path_hash",
            "science_weight",
            "numeric_runtime",
        }
        if set(run_meta) != required or run_meta.get("schema_version") != RUN_SCHEMA_VERSION:
            raise EngineInvariantError("causal run metadata schema mismatch")
        if run_meta.get("runtime_profile") != RUNTIME_PROFILE:
            raise EngineInvariantError("causal runtime profile mismatch")
        if canonical_hash(run_meta["config"]) != run_meta["config_hash"]:
            raise EngineInvariantError("causal config hash mismatch")
        if canonical_json(run_meta["config"]) != canonical_json(self.config.to_dict()):
            raise EngineInvariantError("runtime adapter config differs from persisted config")
        if run_meta["context_assignment_hash"] != canonical_hash(self.contexts):
            raise EngineInvariantError("runtime context assignment differs from metadata")
        if run_meta["code_path_hash"] != self.compute_code_path_hash():
            raise EngineInvariantError("causal code-path drift")
        if run_meta["science_weight"] != 0:
            raise EngineInvariantError("science_weight must remain zero")
        if run_meta["numeric_runtime"] != {
            "backend": "numpy",
            "version": NUMERIC_BACKEND_VERSION,
            "dtype": "float64",
        }:
            raise EngineInvariantError("causal numeric runtime metadata mismatch")

    def _verify_state(self, state: Mapping[str, Any], run_meta: Mapping[str, Any]) -> None:
        required = {
            "schema_version",
            "runtime_profile",
            "clock",
            "organism",
            "learner",
            "baselines",
            "evaluator",
            "lifecycle",
            "last_action",
            "last_observed_delta",
            "last_command_hash",
            "last_trace_hash",
            "trace_chain_hash",
            "integrity",
        }
        if set(state) != required or state.get("schema_version") != STATE_SCHEMA_VERSION:
            raise EngineInvariantError("causal state schema mismatch")
        if state.get("runtime_profile") != RUNTIME_PROFILE:
            raise EngineInvariantError("causal state runtime profile mismatch")
        _validate_learner(state["learner"])
        evaluator = state["evaluator"]
        if evaluator.get("context_assignment_hash") != canonical_hash(evaluator.get("contexts")):
            raise EngineInvariantError("state context assignment hash mismatch")
        if evaluator["context_assignment_hash"] != run_meta["context_assignment_hash"]:
            raise EngineInvariantError("state context assignment differs from metadata")
        integrity = state["integrity"]
        if integrity.get("context_assignment_hash") != evaluator["context_assignment_hash"]:
            raise EngineInvariantError("integrity context assignment mismatch")
        if integrity.get("config_hash") != run_meta["config_hash"]:
            raise EngineInvariantError("integrity config mismatch")
        if int(state["clock"]["global_tick"]) == 0:
            if integrity.get("initial_model_hash") != state["learner"]["model_hash"]:
                raise EngineInvariantError("initial learner bytes differ from integrity commitment")
            if state["learner"]["model_hash"] != run_meta["initial_model_hash"]:
                raise EngineInvariantError("initial learner differs from run metadata")
        if set(state["baselines"]) != set(BASELINE_NAMES):
            raise EngineInvariantError("baseline state schema mismatch")
        total = self.config.context_count * self.config.steps_per_context
        tick = int(state["clock"]["global_tick"])
        if not 0 <= tick <= total:
            raise EngineInvariantError("causal clock outside frozen schedule")
        expected_context = min(self.config.context_count - 1, tick // self.config.steps_per_context)
        expected_row = tick % self.config.steps_per_context
        if tick == total:
            expected_context = self.config.context_count - 1
            expected_row = self.config.steps_per_context
        if int(evaluator["context_index"]) != expected_context or int(evaluator["row_index"]) != expected_row:
            raise EngineInvariantError("causal schedule cursor mismatch")
        terminal = state["lifecycle"]["trial_status"] == "terminal"
        if terminal != (tick == total):
            raise EngineInvariantError("causal lifecycle/clock mismatch")
        if tick == 0 and any(
            state[field] is not None for field in ("last_command_hash", "last_trace_hash", "trace_chain_hash")
        ):
            raise EngineInvariantError("initial trace/command chain must be empty")
        if tick > 0 and (
            not _is_sha256(state["last_command_hash"])
            or not _is_sha256(state["last_trace_hash"])
            or state["trace_chain_hash"] != state["last_trace_hash"]
        ):
            raise EngineInvariantError("causal trace/command chain mismatch")

    def verify_replay_boundary(self, state: Mapping[str, Any], run_meta: Mapping[str, Any]) -> None:
        self._verify_metadata(run_meta)
        self._verify_state(state, run_meta)

    def _verify_command(self, command: Mapping[str, Any], state: Mapping[str, Any]) -> None:
        required = {
            "schema_version",
            "sequence",
            "trigger_source",
            "interventions",
            "prev_command_hash",
            "command_hash",
        }
        if set(command) != required or command.get("schema_version") != COMMAND_SCHEMA_VERSION:
            raise EngineInvariantError("causal command schema mismatch")
        if int(command["sequence"]) != int(state["clock"]["global_tick"]) + 1:
            raise EngineInvariantError("causal command sequence mismatch")
        if command["prev_command_hash"] != state["last_command_hash"]:
            raise EngineInvariantError("causal command chain mismatch")
        if command["command_hash"] != canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        ):
            raise EngineInvariantError("causal command hash mismatch")
        self._normalize_interventions(command["interventions"])

    def compute_step(
        self, state: Mapping[str, Any], command: Mapping[str, Any], run_meta: Mapping[str, Any]
    ) -> StepResult:
        self.verify_replay_boundary(state, run_meta)
        self._verify_command(command, state)
        if state["lifecycle"]["trial_status"] == "terminal":
            raise EngineInvariantError("causal trial is terminal")

        # The verified input is immutable.  Copy only the components changed by
        # this transition; this mirrors the ordinary V2 reducer's incremental
        # approach and keeps recovery cost linear in trace length.
        before = dict(state)
        context_index = int(before["evaluator"]["context_index"])
        row_index = int(before["evaluator"]["row_index"])
        context = before["evaluator"]["contexts"][context_index]
        interventions = self._normalize_interventions(command["interventions"])
        learner = deepcopy(before["learner"])
        baselines = before["baselines"]
        context_reset = row_index == 0
        if context_reset:
            learner = reset_recurrent_state(learner)
            baselines = _reset_baseline_history(baselines)
        if interventions["history_mode"] == "reset_each_step":
            learner = reset_recurrent_state(learner)
        if interventions["weights_mode"] == "deleted":
            blank = create_learner(
                hidden_size=self.config.hidden_size,
                seed=self.config.seed,
                learning_rate=self.config.learning_rate,
                bptt_steps=self.config.bptt_steps,
            )
            blank["rng_state"] = deepcopy(learner["rng_state"])
            learner = _refresh_learner_hashes(blank)

        observation = _public_observation(
            context,
            row_index,
            steps_per_context=self.config.steps_per_context,
            energy=float(before["organism"]["energy"]),
            last_action=before["last_action"],
            last_observed_delta=float(before["last_observed_delta"]),
            nuisance_mode=interventions["nuisance_mode"],
        )
        public_input_hash = canonical_hash(observation)
        recurrent_hash_before = learner["recurrent_state_hash"]
        model_hash_before = learner["model_hash"]
        prediction, cache, advanced = forward_learner(learner, observation)
        baseline_predictions, baseline_working = _baseline_predictions(baselines, observation)

        rng = _rng_from_state(advanced["rng_state"])
        planner_scores = {
            action: (
                float(prediction["predicted_delta_by_action"][action])
                + 0.05 * float(prediction["policy_logits_by_action"][action])
                - 0.10 * float(prediction["terminal_risk_by_action"][action])
            )
            for action in ACTIONS
        }
        exploration_draw = float(rng.random())
        if row_index < 4:
            selected_action = ("consume", "consume", "interact", "interact")[row_index]
            selection_reason = "generic_factorial_bootstrap"
        elif exploration_draw < self.config.exploration_rate:
            selected_action = ACTIONS[int(rng.integers(0, len(ACTIONS)))]
            selection_reason = "generic_rng_exploration"
        else:
            selected_action = max(ACTIONS, key=lambda action: (planner_scores[action], -ACTIONS.index(action)))
            selection_reason = "learned_prediction_plus_policy_value"
        advanced["rng_state"] = deepcopy(rng.bit_generator.state)
        advanced = _refresh_learner_hashes(advanced)

        actual_delta = _oracle_delta(
            context,
            observation,
            selected_action,
            row_index=row_index,
            mechanism_mode=interventions["mechanism_mode"],
        )
        feedback_target = actual_delta
        if interventions["feedback_mode"] == "shuffled":
            feedback_target = -actual_delta
        updated_learner, update_receipt = update_learner(
            advanced,
            cache,
            selected_action=selected_action,
            actual_delta=feedback_target,
            update_mode=interventions["update_mode"],
            defer_until_full=True,
        )
        updated_baselines = _update_baselines(
            baseline_working,
            observation,
            action=selected_action,
            actual_delta=actual_delta,
        )

        next_state = dict(before)
        next_tick = int(before["clock"]["global_tick"]) + 1
        next_context_index = context_index
        next_row_index = row_index + 1
        if next_row_index >= self.config.steps_per_context and next_tick < (
            self.config.context_count * self.config.steps_per_context
        ):
            next_context_index += 1
            next_row_index = 0
        terminal = next_tick == self.config.context_count * self.config.steps_per_context
        next_state["clock"] = {
            "global_tick": next_tick,
            "episode_index": next_context_index,
            "episode_id": f"causal-sprout-{canonical_hash([run_meta['run_id'], next_context_index])[:16]}",
            "episode_tick": next_row_index,
        }
        next_state["organism"] = {
            "energy": _round(min(1.0, max(0.0, float(before["organism"]["energy"]) + actual_delta)))
        }
        next_state["learner"] = updated_learner
        next_state["baselines"] = updated_baselines
        next_state["evaluator"] = dict(before["evaluator"])
        next_state["evaluator"]["context_index"] = next_context_index
        next_state["evaluator"]["row_index"] = next_row_index
        next_state["lifecycle"] = {
            "trial_status": "terminal" if terminal else "active",
            "life_index": 1,
            "awaiting_respawn": False,
            "life_results": (
                [{"life_index": 1, "survival_ticks": next_tick, "censored": True, "termination": "schedule_complete"}]
                if terminal
                else []
            ),
            "terminal_life_result": (
                {"life_index": 1, "survival_ticks": next_tick, "censored": True, "termination": "schedule_complete"}
                if terminal
                else None
            ),
        }
        next_state["last_action"] = selected_action
        next_state["last_observed_delta"] = actual_delta
        next_state["last_command_hash"] = command["command_hash"]

        baseline_receipts = {
            name: {
                "called": True,
                "public_input_hash": public_input_hash,
                "predicted_delta_by_action": deepcopy(baseline_predictions[name]),
                "selected_action_error": _round(
                    float(baseline_predictions[name][selected_action]) - actual_delta
                ),
            }
            for name in BASELINE_NAMES
        }
        trace: dict[str, Any] = {
            "schema_version": TRACE_SCHEMA_VERSION,
            "runtime_profile": RUNTIME_PROFILE,
            "producer_function": "ego_life_playground_v0.causal_sprout.CausalSproutRuntime.compute_step",
            "run_id": run_meta["run_id"],
            "sequence": next_tick,
            "command": deepcopy(dict(command)),
            "command_hash": command["command_hash"],
            "prev_command_hash": command["prev_command_hash"],
            "prev_trace_hash": before["last_trace_hash"],
            "state_before_hash": canonical_hash(before),
            "public_observation": deepcopy(observation),
            "public_input_hash": public_input_hash,
            "learner_input_fields": list(PUBLIC_OBSERVATION_FIELDS),
            "predicted_delta_by_action": deepcopy(prediction["predicted_delta_by_action"]),
            "terminal_risk_by_action": deepcopy(prediction["terminal_risk_by_action"]),
            "policy_logits_by_action": deepcopy(prediction["policy_logits_by_action"]),
            "planner_scores": {key: _round(value) for key, value in planner_scores.items()},
            "selected_action": selected_action,
            "selection_reason": selection_reason,
            "exploration_draw": _round(exploration_draw),
            "actual_delta": actual_delta,
            "prediction_error": _round(
                float(prediction["predicted_delta_by_action"][selected_action]) - actual_delta
            ),
            "energy_before": before["organism"]["energy"],
            "energy_after": next_state["organism"]["energy"],
            "recurrent_state_hash_before": recurrent_hash_before,
            "recurrent_state_hash_after": updated_learner["recurrent_state_hash"],
            "model_weight_hash_before": model_hash_before,
            "model_weight_hash_after": updated_learner["model_hash"],
            "optimizer_hash_after": updated_learner["optimizer_hash"],
            "update_count": updated_learner["update_count"],
            "update_receipt": update_receipt,
            "baselines": baseline_receipts,
            "interventions": deepcopy(interventions),
            "context_reset_observable": context_reset,
            "evaluator_only": {
                "context_commitment": canonical_hash(context),
                "row_index": row_index,
                "hidden_effect_range": 0.60,
                "glyph_encoding_commitment": canonical_hash(context["glyph_encoding"]),
                "mechanism_shift_active": (
                    context.get("mechanism_shift_at") is not None
                    and row_index >= int(context["mechanism_shift_at"])
                ),
                "oracle_delta_by_action": {
                    action: _oracle_delta(
                        context,
                        observation,
                        action,
                        row_index=row_index,
                        mechanism_mode=interventions["mechanism_mode"],
                    )
                    for action in ACTIONS
                },
            },
            "code_path_hash": run_meta["code_path_hash"],
            "science_weight": 0,
        }
        trace["trace_hash"] = self.compute_trace_hash(trace)
        next_state["last_trace_hash"] = trace["trace_hash"]
        next_state["trace_chain_hash"] = trace["trace_hash"]
        self._verify_state(next_state, run_meta)
        return StepResult(next_state=next_state, trace=trace)


def reduce_trace_rows(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    candidate_losses: list[float] = []
    lookup_losses: list[float] = []
    no_update_losses: list[float] = []
    for trace in traces:
        error = float(trace["prediction_error"])
        lookup_error = float(trace["baselines"]["feature_action_lookup"]["selected_action_error"])
        no_update_error = float(trace["baselines"]["no_update_neural"]["selected_action_error"])
        candidate_losses.append(error**2)
        lookup_losses.append(lookup_error**2)
        no_update_losses.append(no_update_error**2)
        rows.append(
            {
                "sequence": trace["sequence"],
                "energy": trace["energy_after"],
                "feature_a": trace["public_observation"]["feature_a"],
                "feature_b": trace["public_observation"]["feature_b"],
                "predicted_delta_by_action": trace["predicted_delta_by_action"],
                "selected_action": trace["selected_action"],
                "actual_delta": trace["actual_delta"],
                "prediction_error": trace["prediction_error"],
                "recurrent_state_hash": trace["recurrent_state_hash_after"],
                "model_weight_hash": trace["model_weight_hash_after"],
                "update_count": trace["update_count"],
                "candidate_mse_so_far": _round(sum(candidate_losses) / len(candidate_losses)),
                "lookup_mse_so_far": _round(sum(lookup_losses) / len(lookup_losses)),
                "no_update_mse_so_far": _round(sum(no_update_losses) / len(no_update_losses)),
            }
        )
    source_trace_hash = canonical_hash(list(traces))
    early_count = max(1, len(candidate_losses) // 4)
    late_start = max(0, len(candidate_losses) - early_count)
    report = {
        "schema_version": "ego.causal_sprout.trace_reducer.v1",
        "source_trace_hash": source_trace_hash,
        "row_count": len(rows),
        "rows": rows,
        "early_window_mse": _round(sum(candidate_losses[:early_count]) / max(1, early_count)),
        "late_window_mse": _round(sum(candidate_losses[late_start:]) / max(1, len(candidate_losses[late_start:]))),
    }
    report["reducer_hash"] = canonical_hash(report)
    return report


def render_trace_html(report: Mapping[str, Any]) -> str:
    """Render only reduced trace data; no policy, transition, or update code."""

    payload = html.escape(canonical_json(report))
    rows = list(report.get("rows", []))
    table_rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in (
                "sequence",
                "energy",
                "feature_a",
                "feature_b",
                "selected_action",
                "actual_delta",
                "prediction_error",
                "update_count",
                "candidate_mse_so_far",
                "lookup_mse_so_far",
                "no_update_mse_so_far",
            )
        )
        + "</tr>"
        for row in rows
    )
    judgment = html.escape(str(report.get("current_judgment", "INCONCLUSIVE")))
    intervention = report.get("intervention_summary", {})
    nuisance_ratio = html.escape(str(intervention.get("nuisance_ratio", "not-run"))) if isinstance(intervention, Mapping) else "not-run"
    mechanism_accuracy = html.escape(str(intervention.get("mechanism_sign_accuracy", "not-run"))) if isinstance(intervention, Mapping) else "not-run"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Causal Sprout trace report</title>
<style>body{{font-family:system-ui;background:#0b1220;color:#dce7f7;margin:24px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{border:1px solid #33445f;padding:5px}}th{{background:#18304e;position:sticky;top:0}}.note{{color:#8fd3ff}}</style>
</head><body><h1>Causal Sprout</h1><p class="note">trace-only renderer; no second behavior engine</p>
<p>reducer_hash: <code>{html.escape(str(report['reducer_hash']))}</code></p>
<p>early MSE: {report.get('early_window_mse')} | late MSE: {report.get('late_window_mse')}</p>
<p><strong>current judgment: {judgment}</strong></p>
<p>nuisance intervention ratio: {nuisance_ratio} | mechanism intervention sign accuracy: {mechanism_accuracy}</p>
<table><thead><tr><th>tick</th><th>energy</th><th>feature_a</th><th>feature_b</th><th>action</th><th>delta</th><th>error</th><th>updates</th><th>candidate MSE</th><th>lookup MSE</th><th>no-update MSE</th></tr></thead><tbody>{table_rows}</tbody></table>
<details><summary>reduced trace payload</summary><pre id="trace-data">{payload}</pre></details>
</body></html>"""
