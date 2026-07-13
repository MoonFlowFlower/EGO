"""Explicit local CLI for the default-off outcome utility."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import utility

_TRANSCRIPT_KEYS = {"schema_version", "model_id", "steps"}
_WORKER_KEYS = {
    "schema_version",
    "checkpoint_state_base64",
    "ordered_steps",
    "expected_trace",
    "task_id",
    "run_id",
    "code_path_hash",
    "functional_contract_hash",
}


def _document_bytes(value: Any) -> bytes:
    return utility._canonical_bytes(value) + b"\n"


def _load_document(payload: bytes, code: str) -> Any:
    if type(payload) is not bytes or not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        utility._fail(code, "one terminal LF required")
    return utility._load_canonical_json(payload[:-1], code)


def parse_transcript(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the exact transcript schema without executing it."""
    utility._require_exact_keys(value, _TRANSCRIPT_KEYS, "TRANSCRIPT_SCHEMA")
    if value["schema_version"] != "ego.outcome_utility.transcript.v1":
        utility._fail("TRANSCRIPT_SCHEMA", "schema_version")
    utility._require_identifier(value["model_id"], "model_id")
    steps = value["steps"]
    if type(steps) is not list or not steps or len(steps) > 10_000:
        utility._fail("TRANSCRIPT_SCHEMA", "steps")
    episode_id: str | None = None
    previous_step = 0
    validated_steps: list[dict[str, Any]] = []
    for step in steps:
        utility._require_exact_keys(step, {"observation", "feedback"}, "TRANSCRIPT_STEP")
        observation = utility._validate_observation(step["observation"])
        feedback = utility._validate_feedback(step["feedback"], observation)
        if episode_id is None:
            episode_id = observation["episode_id"]
        if observation["episode_id"] != episode_id or observation["step_id"] <= previous_step:
            utility._fail("TRANSCRIPT_ORDER", "one episode and increasing step_id required")
        previous_step = observation["step_id"]
        validated_steps.append({"observation": observation, "feedback": feedback})
    return {
        "schema_version": value["schema_version"],
        "model_id": value["model_id"],
        "steps": validated_steps,
    }


def load_transcript(path: Path) -> dict[str, Any]:
    value = _load_document(path.read_bytes(), "TRANSCRIPT_BYTES")
    if type(value) is not dict:
        utility._fail("TRANSCRIPT_SCHEMA", "object required")
    return parse_transcript(value)


def process_transcript(transcript: Mapping[str, Any]) -> dict[str, Any]:
    """Fold the transcript through utility.run_step, with no side effects."""
    validated = parse_transcript(transcript)
    state = utility.new_state(validated["model_id"])
    trace: list[dict[str, Any]] = []
    selections: list[str] = []
    for step in validated["steps"]:
        result = utility.run_step(state, step["observation"], step["feedback"])
        state = result["next_state"]
        trace.append(result["trace_record"])
        selections.append(result["prediction"]["selected_action_id"])
    return {
        "schema_version": "ego.outcome_utility.process_response.v1",
        "model_id": validated["model_id"],
        "selection_sequence": selections,
        "final_state": state,
        "trace": trace,
        "producer_function": "ego_outcome_utility.cli.process_transcript",
    }


def _write_new_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()


def _run_process(input_path: Path, output_path: Path) -> int:
    response = process_transcript(load_transcript(input_path))
    _write_new_file(output_path, _document_bytes(response))
    return 0


def _run_replay_worker() -> int:
    payload = _load_document(sys.stdin.buffer.read(), "WORKER_PAYLOAD")
    utility._require_exact_keys(payload, _WORKER_KEYS, "WORKER_PAYLOAD")
    if payload["schema_version"] != "ego.outcome_utility.replay_worker_payload.v1":
        utility._fail("WORKER_PAYLOAD", "schema_version")
    for field in ("task_id", "run_id"):
        utility._require_identifier(payload[field], field)
    for field in ("code_path_hash", "functional_contract_hash"):
        if type(payload[field]) is not str or len(payload[field]) != 64:
            utility._fail("WORKER_PAYLOAD", field)
    try:
        checkpoint = base64.b64decode(
            payload["checkpoint_state_base64"], validate=True
        )
    except (TypeError, binascii.Error) as exc:
        utility._fail("WORKER_PAYLOAD", str(exc))
    result = utility.replay(
        checkpoint, payload["ordered_steps"], payload["expected_trace"]
    )
    sys.stdout.buffer.write(_document_bytes(result))
    sys.stdout.buffer.flush()
    return 0


def _run_validate(
    contract_path: Path, fixture_path: Path, output_dir: Path, run_id: str
) -> int:
    from .functional_checks import (
        ArtifactPathError,
        FunctionalValidationFailure,
        ProducerStructureAbort,
        run_functional_validation,
    )

    try:
        response = run_functional_validation(
            contract_path, fixture_path, output_dir, run_id
        )
    except ArtifactPathError as exc:
        print(f"EOU_ARTIFACT_PATH:{exc}", file=sys.stderr)
        return 4
    except ProducerStructureAbort as exc:
        print(f"EOU_PRODUCER_ABORT:{exc}", file=sys.stderr)
        return 4
    except FunctionalValidationFailure as exc:
        if exc.response is not None:
            sys.stdout.buffer.write(_document_bytes(exc.response))
            sys.stdout.buffer.flush()
        return 3
    sys.stdout.buffer.write(_document_bytes(response))
    sys.stdout.buffer.flush()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ego-outcome-utility")
    commands = parser.add_subparsers(dest="command", required=True)
    process = commands.add_parser("process")
    process.add_argument("--input", required=True, type=Path)
    process.add_argument("--output", required=True, type=Path)
    validate = commands.add_parser("validate")
    validate.add_argument("--contract", required=True, type=Path)
    validate.add_argument("--fixture", required=True, type=Path)
    validate.add_argument("--output-dir", required=True, type=Path)
    validate.add_argument("--run-id", required=True)
    commands.add_parser("replay-worker", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one explicitly selected local command."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "process":
            return _run_process(args.input, args.output)
        if args.command == "validate":
            return _run_validate(args.contract, args.fixture, args.output_dir, args.run_id)
        return _run_replay_worker()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc).splitlines()[0], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
