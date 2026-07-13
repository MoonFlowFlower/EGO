"""One deterministic prediction/update/replay path for the bounded utility."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_OBSERVATION_KEYS = {
    "schema_version",
    "observation_id",
    "episode_id",
    "step_id",
    "context_id",
    "legal_action_ids",
}
_FEEDBACK_KEYS = {
    "schema_version",
    "feedback_id",
    "observation_id",
    "episode_id",
    "step_id",
    "context_id",
    "action_id",
    "outcome_micros",
}
_STATE_KEYS = {
    "schema_version",
    "model_id",
    "revision",
    "cells",
    "applied_feedback_ids",
    "state_hash",
}
_CELL_KEYS = {
    "context_id",
    "action_id",
    "outcome_sum_micros",
    "observation_count",
}
_PREDICTION_KEYS = {
    "schema_version",
    "model_id",
    "observation_id",
    "episode_id",
    "step_id",
    "context_id",
    "pre_state_hash",
    "scores",
    "selected_action_id",
    "producer_function",
}
_SCORE_KEYS = {
    "action_id",
    "score_numerator",
    "score_denominator",
    "observation_count",
}


def _fail(code: str, message: str) -> None:
    raise ValueError(f"EOU_{code}:{message}")


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _fail("CANONICAL_JSON", str(exc))


def _canonical_text(value: Any) -> str:
    return _canonical_bytes(value).decode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], code: str) -> None:
    if type(value) is not dict or set(value) != keys:
        _fail(code, "exact key set required")


def _require_identifier(value: Any, field: str) -> str:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        _fail("IDENTIFIER", f"invalid {field}")
    return value


def _require_int(value: Any, field: str, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        _fail("INTEGER", f"invalid {field}")
    return value


def _load_canonical_json(payload: bytes, code: str) -> Any:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf"):
        _fail(code, "bytes without BOM required")
    duplicates: list[str] = []

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_constant=lambda constant: _fail(code, f"nonfinite {constant}"),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(code, str(exc))
    if duplicates:
        _fail("DUPLICATE_KEY", duplicates[0])
    if _canonical_bytes(value) != payload:
        _fail(code, "noncanonical bytes")
    return value


def _validate_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_keys(observation, _OBSERVATION_KEYS, "OBSERVATION_SCHEMA")
    if observation["schema_version"] != "ego.outcome_utility.observation.v1":
        _fail("OBSERVATION_SCHEMA", "schema_version")
    for field in ("observation_id", "episode_id", "context_id"):
        _require_identifier(observation[field], field)
    _require_int(observation["step_id"], "step_id", 1)
    actions = observation["legal_action_ids"]
    if type(actions) is not list or not actions:
        _fail("OBSERVATION_SCHEMA", "nonempty legal_action_ids required")
    for action in actions:
        _require_identifier(action, "legal_action_id")
    if actions != sorted(actions) or len(actions) != len(set(actions)):
        _fail("OBSERVATION_SCHEMA", "canonical unique legal_action_ids required")
    return deepcopy(dict(observation))


def _validate_feedback(
    feedback: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    _require_exact_keys(feedback, _FEEDBACK_KEYS, "FEEDBACK_SCHEMA")
    if feedback["schema_version"] != "ego.outcome_utility.feedback.v1":
        _fail("FEEDBACK_SCHEMA", "schema_version")
    for field in (
        "feedback_id",
        "observation_id",
        "episode_id",
        "context_id",
        "action_id",
    ):
        _require_identifier(feedback[field], field)
    _require_int(feedback["step_id"], "step_id", 1)
    outcome = _require_int(feedback["outcome_micros"], "outcome_micros")
    if outcome < -1_000_000 or outcome > 1_000_000:
        _fail("OUTCOME_RANGE", "outcome_micros")
    for field in ("observation_id", "episode_id", "step_id", "context_id"):
        if feedback[field] != observation[field]:
            _fail("FEEDBACK_MISMATCH", field)
    if feedback["action_id"] not in observation["legal_action_ids"]:
        _fail("ILLEGAL_ACTION", "feedback action")
    return deepcopy(dict(feedback))


def _state_body(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": state["schema_version"],
        "model_id": state["model_id"],
        "revision": state["revision"],
        "cells": state["cells"],
        "applied_feedback_ids": state["applied_feedback_ids"],
    }


def _validate_state(state: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_keys(state, _STATE_KEYS, "STATE_SCHEMA")
    if state["schema_version"] != "ego.outcome_utility.state.v1":
        _fail("STATE_SCHEMA", "schema_version")
    _require_identifier(state["model_id"], "model_id")
    revision = _require_int(state["revision"], "revision", 0)
    cells = state["cells"]
    if type(cells) is not list:
        _fail("STATE_SCHEMA", "cells")
    pairs: list[tuple[str, str]] = []
    for cell in cells:
        _require_exact_keys(cell, _CELL_KEYS, "CELL_SCHEMA")
        context_id = _require_identifier(cell["context_id"], "context_id")
        action_id = _require_identifier(cell["action_id"], "action_id")
        total = _require_int(cell["outcome_sum_micros"], "outcome_sum_micros")
        count = _require_int(cell["observation_count"], "observation_count", 1)
        if abs(total) > count * 1_000_000:
            _fail("STATE_BOUND", "outcome sum")
        pairs.append((context_id, action_id))
    if pairs != sorted(pairs) or len(pairs) != len(set(pairs)):
        _fail("STATE_SCHEMA", "canonical unique cells required")
    feedback_ids = state["applied_feedback_ids"]
    if type(feedback_ids) is not list:
        _fail("STATE_SCHEMA", "applied_feedback_ids")
    for feedback_id in feedback_ids:
        _require_identifier(feedback_id, "feedback_id")
    if feedback_ids != sorted(feedback_ids) or len(feedback_ids) != len(set(feedback_ids)):
        _fail("STATE_SCHEMA", "canonical unique feedback ids required")
    if revision != len(feedback_ids):
        _fail("STATE_REVISION", "revision must equal feedback count")
    state_hash = state["state_hash"]
    if type(state_hash) is not str or re.fullmatch(r"[0-9a-f]{64}", state_hash) is None:
        _fail("STATE_HASH", "format")
    if hashlib.sha256(_canonical_bytes(_state_body(state))).hexdigest() != state_hash:
        _fail("STATE_HASH", "mismatch")
    return deepcopy(dict(state))


def _validate_prediction(
    prediction: Mapping[str, Any], state: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    _require_exact_keys(prediction, _PREDICTION_KEYS, "PREDICTION_SCHEMA")
    if prediction["schema_version"] != "ego.outcome_utility.prediction.v1":
        _fail("PREDICTION_SCHEMA", "schema_version")
    bindings = {
        "model_id": state["model_id"],
        "observation_id": observation["observation_id"],
        "episode_id": observation["episode_id"],
        "step_id": observation["step_id"],
        "context_id": observation["context_id"],
        "pre_state_hash": state["state_hash"],
    }
    for field, expected in bindings.items():
        if prediction[field] != expected:
            _fail("PREDICTION_MISMATCH", field)
    if prediction["producer_function"] != "ego_outcome_utility.utility.predict":
        _fail("PREDICTION_SCHEMA", "producer_function")
    scores = prediction["scores"]
    if type(scores) is not list or len(scores) != len(observation["legal_action_ids"]):
        _fail("PREDICTION_SCHEMA", "scores")
    for action, score in zip(observation["legal_action_ids"], scores, strict=True):
        _require_exact_keys(score, _SCORE_KEYS, "PREDICTION_SCORE_SCHEMA")
        if score["action_id"] != action:
            _fail("PREDICTION_SCHEMA", "score order")
        _require_int(score["score_numerator"], "score_numerator")
        _require_int(score["score_denominator"], "score_denominator", 1)
        _require_int(score["observation_count"], "observation_count", 0)
    if prediction["selected_action_id"] not in observation["legal_action_ids"]:
        _fail("PREDICTION_SCHEMA", "selected action")
    return deepcopy(dict(prediction))


def new_state(model_id: str) -> dict[str, Any]:
    """Return a canonical empty state."""
    _require_identifier(model_id, "model_id")
    body = {
        "schema_version": "ego.outcome_utility.state.v1",
        "model_id": model_id,
        "revision": 0,
        "cells": [],
        "applied_feedback_ids": [],
    }
    return {**body, "state_hash": hashlib.sha256(_canonical_bytes(body)).hexdigest()}


def _cell_map(state: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (cell["context_id"], cell["action_id"]): deepcopy(cell)
        for cell in state["cells"]
    }


def predict(
    state: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, Any]:
    """Predict by exact rational comparison of the keyed running table."""
    validated_state = _validate_state(state)
    validated_observation = _validate_observation(observation)
    cells = _cell_map(validated_state)
    scores: list[dict[str, Any]] = []
    best_action: str | None = None
    best_numerator = 0
    best_denominator = 1
    for action_id in validated_observation["legal_action_ids"]:
        cell = cells.get((validated_observation["context_id"], action_id))
        numerator = 0 if cell is None else cell["outcome_sum_micros"]
        denominator = 1 if cell is None else cell["observation_count"]
        count = 0 if cell is None else cell["observation_count"]
        scores.append(
            {
                "action_id": action_id,
                "score_numerator": numerator,
                "score_denominator": denominator,
                "observation_count": count,
            }
        )
        if best_action is None or numerator * best_denominator > best_numerator * denominator:
            best_action = action_id
            best_numerator = numerator
            best_denominator = denominator
    assert best_action is not None
    return {
        "schema_version": "ego.outcome_utility.prediction.v1",
        "model_id": validated_state["model_id"],
        "observation_id": validated_observation["observation_id"],
        "episode_id": validated_observation["episode_id"],
        "step_id": validated_observation["step_id"],
        "context_id": validated_observation["context_id"],
        "pre_state_hash": validated_state["state_hash"],
        "scores": scores,
        "selected_action_id": best_action,
        "producer_function": "ego_outcome_utility.utility.predict",
    }


def observe_outcome(
    state: Mapping[str, Any],
    observation: Mapping[str, Any],
    prediction: Mapping[str, Any],
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a new state after one legal outcome observation."""
    validated_state = _validate_state(state)
    validated_observation = _validate_observation(observation)
    validated_prediction = _validate_prediction(
        prediction, validated_state, validated_observation
    )
    validated_feedback = _validate_feedback(feedback, validated_observation)
    if validated_feedback["feedback_id"] in validated_state["applied_feedback_ids"]:
        _fail("DUPLICATE_FEEDBACK", validated_feedback["feedback_id"])
    if validated_feedback["action_id"] != validated_prediction["selected_action_id"]:
        _fail("FEEDBACK_ACTION", "feedback must target selected action")
    cells = _cell_map(validated_state)
    key = (validated_feedback["context_id"], validated_feedback["action_id"])
    old = cells.get(key)
    cells[key] = {
        "context_id": key[0],
        "action_id": key[1],
        "outcome_sum_micros": (0 if old is None else old["outcome_sum_micros"])
        + validated_feedback["outcome_micros"],
        "observation_count": (0 if old is None else old["observation_count"]) + 1,
    }
    body = {
        "schema_version": "ego.outcome_utility.state.v1",
        "model_id": validated_state["model_id"],
        "revision": validated_state["revision"] + 1,
        "cells": [cells[cell_key] for cell_key in sorted(cells)],
        "applied_feedback_ids": sorted(
            [*validated_state["applied_feedback_ids"], validated_feedback["feedback_id"]]
        ),
    }
    next_state = {
        **body,
        "state_hash": hashlib.sha256(_canonical_bytes(body)).hexdigest(),
    }
    return _validate_state(next_state)


def _cell_values(
    state: Mapping[str, Any], context_id: str, action_id: str
) -> tuple[int, int]:
    cell = _cell_map(state).get((context_id, action_id))
    if cell is None:
        return 0, 0
    return cell["outcome_sum_micros"], cell["observation_count"]


def run_step(
    state: Mapping[str, Any],
    observation: Mapping[str, Any],
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the sole prediction/update path exactly once each."""
    before = _validate_state(state)
    obs = _validate_observation(observation)
    prediction = predict(before, obs)
    next_state = observe_outcome(before, obs, prediction, feedback)
    old_sum, old_count = _cell_values(
        before, feedback["context_id"], feedback["action_id"]
    )
    new_sum, new_count = _cell_values(
        next_state, feedback["context_id"], feedback["action_id"]
    )
    update_delta = {
        "schema_version": "ego.outcome_utility.update_delta.v1",
        "context_id": feedback["context_id"],
        "action_id": feedback["action_id"],
        "old_sum_micros": old_sum,
        "old_count": old_count,
        "new_sum_micros": new_sum,
        "new_count": new_count,
        "revision_before": before["revision"],
        "revision_after": next_state["revision"],
    }
    trace_record = {
        "schema_version": "ego.outcome_utility.trace_record.v1",
        "model_id": before["model_id"],
        "observation_id": obs["observation_id"],
        "feedback_id": feedback["feedback_id"],
        "episode_id": obs["episode_id"],
        "step_id": obs["step_id"],
        "context_id": obs["context_id"],
        "legal_action_ids": deepcopy(obs["legal_action_ids"]),
        "pre_state_hash": before["state_hash"],
        "prediction_scores": deepcopy(prediction["scores"]),
        "selected_action_id": prediction["selected_action_id"],
        "feedback_action_id": feedback["action_id"],
        "outcome_micros": feedback["outcome_micros"],
        "update_delta": update_delta,
        "post_state_hash": next_state["state_hash"],
        "producer_functions": [
            "ego_outcome_utility.utility.predict",
            "ego_outcome_utility.utility.observe_outcome",
        ],
    }
    return {
        "prediction": prediction,
        "next_state": next_state,
        "trace_record": trace_record,
    }


def serialize_state(state: Mapping[str, Any]) -> bytes:
    """Return canonical state bytes without a trailing line feed."""
    return _canonical_bytes(_validate_state(state))


def deserialize_state(payload: bytes) -> dict[str, Any]:
    """Load only exact canonical state bytes with a valid hash."""
    value = _load_canonical_json(payload, "STATE_BYTES")
    if type(value) is not dict:
        _fail("STATE_SCHEMA", "object required")
    state = _validate_state(value)
    if serialize_state(state) != payload:
        _fail("STATE_BYTES", "roundtrip mismatch")
    return state


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _mismatch(
    index: int,
    path: str,
    expected_present: bool,
    expected: Any,
    actual_present: bool,
    actual: Any,
) -> dict[str, Any]:
    return {
        "index": index,
        "path": path,
        "expected_present": expected_present,
        "expected_json": _canonical_text(expected) if expected_present else "",
        "actual_present": actual_present,
        "actual_json": _canonical_text(actual) if actual_present else "",
    }


def _compare_value(
    index: int, path: str, expected: Any, actual: Any, output: list[dict[str, Any]]
) -> None:
    if type(expected) is not type(actual):
        output.append(_mismatch(index, path, True, expected, True, actual))
        return
    if isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            child = path + "/" + _pointer_escape(key)
            if key not in expected:
                output.append(_mismatch(index, child, False, None, True, actual[key]))
            elif key not in actual:
                output.append(_mismatch(index, child, True, expected[key], False, None))
            else:
                _compare_value(index, child, expected[key], actual[key], output)
        return
    if isinstance(expected, list):
        if len(expected) != len(actual):
            output.append(_mismatch(index, path + "/length", True, len(expected), True, len(actual)))
        for offset in range(min(len(expected), len(actual))):
            _compare_value(index, path + f"/{offset}", expected[offset], actual[offset], output)
        return
    if expected != actual:
        output.append(_mismatch(index, path or "/", True, expected, True, actual))


def replay(
    checkpoint_payload: bytes,
    ordered_steps: Sequence[Mapping[str, Any]],
    expected_trace: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Recompute every step from a serialized checkpoint."""
    state = deserialize_state(checkpoint_payload)
    initial_hash = state["state_hash"]
    trace: list[dict[str, Any]] = []
    if isinstance(ordered_steps, (str, bytes)) or not isinstance(ordered_steps, Sequence):
        _fail("REPLAY_STEPS", "sequence required")
    for step in ordered_steps:
        _require_exact_keys(step, {"observation", "feedback"}, "TRANSCRIPT_STEP")
        result = run_step(state, step["observation"], step["feedback"])
        state = result["next_state"]
        trace.append(result["trace_record"])
    mismatches: list[dict[str, Any]] = []
    if expected_trace is not None:
        if isinstance(expected_trace, (str, bytes)) or not isinstance(expected_trace, Sequence):
            _fail("REPLAY_TRACE", "sequence required")
        if len(expected_trace) != len(trace):
            mismatches.append(
                _mismatch(0, "/length", True, len(expected_trace), True, len(trace))
            )
        for index in range(min(len(expected_trace), len(trace))):
            _compare_value(index, "", expected_trace[index], trace[index], mismatches)
    mismatches.sort(key=lambda item: (item["index"], item["path"]))
    return {
        "schema_version": "ego.outcome_utility.replay_result.v1",
        "initial_state_hash": initial_hash,
        "final_state": state,
        "final_state_hash": state["state_hash"],
        "trace": trace,
        "comparator_provided": expected_trace is not None,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "producer_function": "ego_outcome_utility.utility.replay",
    }
