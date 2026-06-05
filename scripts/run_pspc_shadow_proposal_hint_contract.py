#!/usr/bin/env python3
"""Build PSPC shadow proposal-hint packets from v0.1 shadow observations.

This is a contract-only converter. It reads PSPC shadow evidence and writes
artifact-only proposal-hint packets. It never calls EgoOperator runtime, gates,
memory, approval, transport, proactive channels, adapter code, planner,
training, or model execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for candidate in (ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from pspc_shadow_contracts import SIDE_EFFECTS_FALSE, runtime_field_hits, scan_active_runtime_sources  # noqa: E402


SOURCE = "pspc_shadow_proposal_hint_contract_v0"
INPUT_SOURCE = "pspc_sequence_experience_eval_v0_1"
PACKET_TYPE = "shadow_proposal_hint"
CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only"
DEFAULT_INPUT = Path("artifacts") / "pspc_sequence_experience_eval_v0_1" / "sequence_experience_eval_v0_1.json"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_shadow_proposal_hint_contract_v0"
HUMAN_REQUIRED_STATUS = "PSPC-SHADOW-HOOK-007_human_required_preserved"
ACTIVE_RUNTIME_SCAN_MARKERS = (
    "run_pspc_shadow_proposal_hint_contract",
    "pspc_shadow_proposal_hint_contract",
)
FORBIDDEN_AUTHORITY_FLAGS = {
    "can_drive_runtime": False,
    "can_change_user_response": False,
    "can_write_memory": False,
    "can_invoke_gate": False,
    "can_mutate_plan": False,
    "can_trigger_proactive": False,
}
PROPOSAL_HINT_KEYS = {"suggested_interaction_style", "confidence", "basis", "reason_trace_refs", "audit_use_only"}
REJECTED_PACKET_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "runtime_registration",
    "mainline_authority",
    "enable",
    "plan_mutation",
}


def load_v0_1_artifact(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("status") != "pass":
        raise ValueError("v0.1 sequence experience artifact must have status=pass")
    if artifact.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("v0.1 sequence experience artifact has unexpected claim ceiling")
    if artifact.get("enabled") is not False or artifact.get("mainline_connected") is not False:
        raise ValueError("v0.1 artifact must remain disabled and mainline-disconnected")
    return artifact


def style_from_profile(profile: dict[str, Any]) -> str:
    dominant = profile.get("dominant_tendency")
    if dominant == "approach":
        return "warm_approach"
    if dominant == "avoidance":
        return "cautious_boundary"
    if dominant == "care":
        return "low_interrupt_care"
    if dominant == "boundary_expression":
        return "boundary_first"
    if dominant == "low_interrupt":
        return "observe_then_low_interrupt"
    return "observe_without_intervention"


def confidence_from_profile(profile: dict[str, Any]) -> float:
    score_keys = ("approach_tendency", "avoidance_tendency", "care_tendency", "boundary_expression", "low_interrupt")
    max_score = max(float(profile.get(key, 0.0)) for key in score_keys)
    return round(max(0.35, min(0.82, max_score * 0.72)), 4)


def infer_basis(observation: dict[str, Any]) -> str:
    if observation.get("resolution_basis"):
        return str(observation["resolution_basis"])
    category = str(observation.get("history_category") or "unknown")
    return f"recency_salience_recent_{category}"


def convert_observation_to_packet(observation: dict[str, Any], *, packet_id: str, input_artifact_path: str) -> dict[str, Any]:
    profile = observation["trigger_behavior_profile"]
    packet = {
        "source": INPUT_SOURCE,
        "contract_source": SOURCE,
        "packet_id": packet_id,
        "packet_type": PACKET_TYPE,
        "claim_ceiling": CLAIM_CEILING,
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "human_required_status": HUMAN_REQUIRED_STATUS,
        "trigger": observation.get("trigger"),
        "history_profile": {
            "history_category": observation.get("history_category"),
            "history_turn_count": observation.get("history_turn_count"),
            "dominant_tendency": profile.get("dominant_tendency"),
            "approach_tendency": profile.get("approach_tendency"),
            "avoidance_tendency": profile.get("avoidance_tendency"),
            "care_tendency": profile.get("care_tendency"),
            "boundary_expression": profile.get("boundary_expression"),
            "low_interrupt": profile.get("low_interrupt"),
            "conflict_score": observation.get("conflict_score", 0.0),
        },
        "proposal_hint": {
            "suggested_interaction_style": style_from_profile(profile),
            "confidence": confidence_from_profile(profile),
            "basis": infer_basis(observation),
            "reason_trace_refs": list(observation.get("reason_trace_refs") or []),
            "audit_use_only": True,
        },
        "evidence_refs": [input_artifact_path],
        "forbidden": dict(FORBIDDEN_AUTHORITY_FLAGS),
    }
    hits = runtime_field_hits(packet)
    if hits:
        raise ValueError(f"proposal-hint packet contains runtime-authority fields: {hits}")
    validate_packet(packet)
    return packet


def source_observations(v0_1_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    category_results = v0_1_artifact["paraphrase_trigger_robustness"]["category_results"]
    for group_id in ("gentle_interaction", "frequent_interruption", "late_night_care"):
        observations.append(category_results[group_id]["runs"][0]["shadow_observation"])
    mixed_scenarios = v0_1_artifact["mixed_history_resolution"]["scenarios"]
    for scenario_id in sorted(mixed_scenarios):
        observations.append(mixed_scenarios[scenario_id]["result"]["shadow_observation"])
    return observations


def validate_packet(packet: dict[str, Any]) -> None:
    required = {
        "source",
        "contract_source",
        "packet_id",
        "packet_type",
        "claim_ceiling",
        "enabled",
        "mainline_connected",
        "runtime_authority",
        "human_required_status",
        "trigger",
        "history_profile",
        "proposal_hint",
        "evidence_refs",
        "forbidden",
    }
    missing = sorted(required - set(packet))
    if missing:
        raise ValueError(f"proposal-hint packet missing required fields: {missing}")
    if packet["source"] != INPUT_SOURCE or packet["packet_type"] != PACKET_TYPE:
        raise ValueError("proposal-hint packet has unexpected source or packet_type")
    if packet["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("proposal-hint packet cannot raise claim ceiling")
    if packet["enabled"] is not False or packet["mainline_connected"] is not False:
        raise ValueError("proposal-hint packet must remain disabled and mainline-disconnected")
    if packet["runtime_authority"] != "none":
        raise ValueError("proposal-hint packet runtime_authority must be none")
    if packet["human_required_status"] != HUMAN_REQUIRED_STATUS:
        raise ValueError("proposal-hint packet must preserve human_required status")
    if packet["forbidden"] != FORBIDDEN_AUTHORITY_FLAGS:
        raise ValueError("proposal-hint packet forbidden authority flags must all be false")
    if set(packet["proposal_hint"]) != PROPOSAL_HINT_KEYS:
        raise ValueError("proposal_hint contains unexpected fields")
    if not packet["proposal_hint"]["reason_trace_refs"]:
        raise ValueError("proposal_hint must preserve reason_trace_refs")
    rejected_present = sorted(REJECTED_PACKET_FIELDS & set(packet))
    if rejected_present:
        raise ValueError(f"proposal-hint packet contains rejected top-level fields: {rejected_present}")
    hits = runtime_field_hits(packet)
    if hits:
        raise ValueError(f"proposal-hint packet contains runtime-authority fields: {hits}")


def build_contract(input_artifact_path: Path) -> dict[str, Any]:
    artifact = load_v0_1_artifact(input_artifact_path)
    input_ref = str(input_artifact_path)
    packets = [
        convert_observation_to_packet(observation, packet_id=f"proposal_hint_{index:03d}", input_artifact_path=input_ref)
        for index, observation in enumerate(source_observations(artifact), start=1)
    ]
    checks = {
        "input_v0_1_status_pass": artifact.get("status") == "pass",
        "packet_count_positive": len(packets) >= 3,
        "schema_valid": all(validate_packet_returns_true(packet) for packet in packets),
        "forbidden_flags_all_false": all(packet["forbidden"] == FORBIDDEN_AUTHORITY_FLAGS for packet in packets),
        "runtime_authority_absent": all(packet["runtime_authority"] == "none" for packet in packets),
        "non_executable_fields_absent": all(runtime_field_hits(packet) == [] for packet in packets),
        "claim_ceiling_preserved": all(packet["claim_ceiling"] == CLAIM_CEILING for packet in packets),
        "reason_trace_refs_preserved": all(packet["proposal_hint"]["reason_trace_refs"] for packet in packets),
        "human_required_preserved": all(packet["human_required_status"] == HUMAN_REQUIRED_STATUS for packet in packets),
        "enabled_false": all(packet["enabled"] is False for packet in packets),
        "mainline_connected_false": all(packet["mainline_connected"] is False for packet in packets),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "verdict": "proposal_hint_contract_pass__manual_review_only"
        if all(checks.values())
        else "no_go_keep_shadow_only_for_proposal_hint_contract",
        "source": SOURCE,
        "input_source": INPUT_SOURCE,
        "claim_ceiling": CLAIM_CEILING,
        "input_artifact_path": input_ref,
        "packet_count": len(packets),
        "packets": packets,
        "checks": checks,
        "artifact_only": True,
        "runtime_connected": False,
        "adapter_created": False,
        "enabled": False,
        "mainline_connected": False,
        "side_effects": dict(SIDE_EFFECTS_FALSE),
        "next_allowed_step": "manual_review_may_consider_product_only_local_behavior_prototype_design",
    }


def validate_packet_returns_true(packet: dict[str, Any]) -> bool:
    validate_packet(packet)
    return True


def run_proposal_hint_contract(
    repo_root: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
    *,
    input_artifact_path: Path = DEFAULT_INPUT,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    if not input_artifact_path.is_absolute():
        input_artifact_path = repo_root / input_artifact_path
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_contract(input_artifact_path)
    runtime_scan = scan_active_runtime_sources(repo_root, ACTIVE_RUNTIME_SCAN_MARKERS)
    result["runtime_scan"] = runtime_scan
    result["checks"]["active_runtime_scan_clean"] = bool(runtime_scan["ok"])
    result["checks"]["side_effects_absent"] = all(value is False for value in result["side_effects"].values())
    result["status"] = "pass" if all(result["checks"].values()) else "fail"
    result["verdict"] = (
        "proposal_hint_contract_pass__manual_review_only"
        if result["status"] == "pass"
        else "no_go_keep_shadow_only_for_proposal_hint_contract"
    )
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "proposal_hint_contract.json"
    report_path = Path(out_dir) / "PROPOSAL_HINT_CONTRACT_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    packets = "\n".join(
        "- `{packet_id}`: history=`{history}`, style=`{style}`, confidence=`{confidence}`, basis=`{basis}`".format(
            packet_id=packet["packet_id"],
            history=packet["history_profile"]["history_category"],
            style=packet["proposal_hint"]["suggested_interaction_style"],
            confidence=packet["proposal_hint"]["confidence"],
            basis=packet["proposal_hint"]["basis"],
        )
        for packet in result["packets"]
    )
    return f"""# PSPC Shadow Proposal Hint Contract v0

- status: `{result['status']}`
- verdict: `{result['verdict']}`
- claim_ceiling: `{result['claim_ceiling']}`
- input_artifact_path: `{result['input_artifact_path']}`
- packet_count: `{result['packet_count']}`
- artifact_only: `{result['artifact_only']}`
- enabled: `{result['enabled']}`
- mainline_connected: `{result['mainline_connected']}`
- adapter_created: `{result['adapter_created']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Packets

{packets}

## Checks

{checks}

## Manual Go/No-Go Checklist

- Confirm packet fields are useful as audit-only proposal hints.
- Confirm no packet can be interpreted as an executable action, user message, memory write, gate decision, approval, transport call, plan mutation, or proactive trigger.
- Confirm `enabled=false`, `mainline_connected=false`, `runtime_authority=none`, and `human_required_status={HUMAN_REQUIRED_STATUS}` remain present.
- Confirm reason trace refs point back to v0.1 shadow evidence.
- Confirm the next step remains a separate manual/product-only design decision, not runtime integration.

## What This Proves

This proves PSPC v0.1 shadow observations can be converted into read-only, non-executable proposal-hint packets as artifacts while preserving reason trace refs, disabled/mainline-disconnected flags, forbidden authority flags, and the existing claim ceiling.

## What This Does Not Prove

It does not prove EgoOperator runtime integration safety, adapter readiness, model learning, world/self model causality, planner causality, durable memory efficacy, real user benefit, live autonomy, consciousness, subjective experience, real emotion, or that any packet should influence a real user response.

## Failure Meaning

Failure means proposal-hint packets are not safe enough even as artifacts. PSPC should remain shadow-only and no product or runtime-adjacent design should consume these packets.

## Rollback

Delete `docs/codex/tasks/pspc-shadow-proposal-hint-contract-v0/`, `scripts/run_pspc_shadow_proposal_hint_contract.py`, `tests/test_pspc_shadow_proposal_hint_contract.py`, `artifacts/pspc_shadow_proposal_hint_contract_v0/`, and matching governance/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PSPC shadow proposal-hint contract packets.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for proposal-hint contract artifacts.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input PSPC v0.1 shadow observation artifact.")
    args = parser.parse_args()
    result = run_proposal_hint_contract(ROOT, Path(args.out), input_artifact_path=Path(args.input))
    print(
        json.dumps(
            {
                "status": result["status"],
                "verdict": result["verdict"],
                "out": args.out,
                "packet_count": result["packet_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
