#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))

from app.config import load_config
from app.openemotion_adapter.proto_self_adapter import ProtoSelfAdapter
from app.openemotion_adapter.proto_self_state_store import ProtoSelfStateStore
from app.runtime_v2.proto_self_runtime import (
    build_external_result_event,
    build_proto_self_ingress_event,
    normalize_chat_subject_surface,
)
from app.runtime_v2.state import RuntimeV2State


CASE_ROOT = ROOT / "artifacts" / "external_eval_replay_v1" / "cases" / "heldout_eval"
REPORT_ROOT = ROOT / "artifacts" / "external_eval_replay_v1" / "reports"

EXECUTION_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_CURRENT.json"
EXECUTION_MD = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_CURRENT.md"
BUCKET_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_BUCKET_SCORE_SUMMARY_CURRENT.json"
BUCKET_MD = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_BUCKET_SCORE_SUMMARY_CURRENT.md"
FAILURES_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_FAILURES_CURRENT.json"
FAILURES_MD = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_FAILURES_CURRENT.md"
MECHANISM_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_MECHANISM_RELEVANCE_CURRENT.json"
MECHANISM_MD = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_MECHANISM_RELEVANCE_CURRENT.md"

PUBLIC_POLICY_KEYS = (
    "risk_bias",
    "ask_preferred",
    "closure_bias",
    "should_avoid_commitment_upgrade",
)
RESPONSE_TENDENCY_KEYS = (
    "preferred_mode",
    "preferred_tone",
    "certainty_bound",
    "suggested_next_step",
    "ask_needed",
)
WEIGHTS = {
    "downstream_decision_change": 0.45,
    "response_tendency_change": 0.25,
    "host_policy_change": 0.20,
    "corrective_trace_presence": 0.10,
}

VARIANTS = (
    {
        "variant_id": "trial1_baseline_proto_self_mainline",
        "label": "baseline_h1_off",
        "h1_enabled": False,
        "allowlisted": False,
    },
    {
        "variant_id": "canonical_shadow_h1_on",
        "label": "candidate_h1_shadow_on",
        "h1_enabled": True,
        "allowlisted": True,
    },
)

MECHANISM_RELEVANCE = {
    "correction": {
        "primary_mechanism": "structured corrective traces after contradiction",
        "h1_path_relevance": "direct_shadow_path_via_synthetic_exec_result",
    },
    "ask_vs_answer_uncertainty": {
        "primary_mechanism": "bounded uncertainty / ask-vs-answer gating",
        "h1_path_relevance": "indirect_only",
    },
    "failure_revision_later_change": {
        "primary_mechanism": "failure-to-revision-to-later-change loop",
        "h1_path_relevance": "direct_shadow_path_via_synthetic_exec_result",
    },
    "tool_risk_ambiguity": {
        "primary_mechanism": "tool/risk ambiguity guard",
        "h1_path_relevance": "direct_shadow_path_via_synthetic_exec_result",
    },
    "continuity": {
        "primary_mechanism": "sustained continuity across low-cue follow-up",
        "h1_path_relevance": "not_directly_exercised",
    },
    "adversarial_constraints": {
        "primary_mechanism": "constraint retention under pressure",
        "h1_path_relevance": "not_directly_exercised",
    },
}


@dataclass(slots=True)
class ReplayStep:
    kind: str
    step_id: str
    prompt: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_policy(step: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(step.get("policy_hint") or {})
    return {key: policy.get(key) for key in PUBLIC_POLICY_KEYS}


def _normalize_tendency(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = dict(step.get("response_tendency") or {})
    return {key: tendency.get(key) for key in RESPONSE_TENDENCY_KEYS}


def _decision_surface(step: Dict[str, Any]) -> Dict[str, Any]:
    tendency = _normalize_tendency(step)
    policy = _normalize_policy(step)
    preferred_mode = tendency.get("preferred_mode") or "unknown"
    if preferred_mode in {"repair", "ask", "defer"}:
        lane = preferred_mode
    elif bool(tendency.get("ask_needed")):
        lane = "ask"
    elif tendency.get("suggested_next_step") in {"clarify_or_repair", "request_replan"}:
        lane = "repair"
    elif tendency.get("suggested_next_step") == "prioritize_closure":
        lane = "closure"
    else:
        lane = "continue"
    return {
        "lane": lane,
        "ask_needed": bool(tendency.get("ask_needed")),
        "risk_bias": policy.get("risk_bias"),
        "commitment_guard": bool(policy.get("should_avoid_commitment_upgrade")),
    }


def _surface_label(surface: Dict[str, Any]) -> str:
    return (
        f"{surface.get('lane')}|ask={surface.get('ask_needed')}|"
        f"risk={surface.get('risk_bias')}|guard={surface.get('commitment_guard')}"
    )


def _complete_corrective_trace(step: Dict[str, Any]) -> bool:
    trace = dict((step.get("memory_update") or {}).get("corrective_trace") or {})
    required = ("trigger", "actual_outcome", "adjustment_applied", "next_guard")
    return all(trace.get(key) not in (None, "", []) for key in required)


def _public_signature(step: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "decision_surface": _decision_surface(step),
        "response_tendency": _normalize_tendency(step),
        "policy_hint": _normalize_policy(step),
        "corrective_trace_complete": _complete_corrective_trace(step),
    }


def _snake(name: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9]+", "_", name.strip())
    return raw.strip("_").lower() or "unknown_tool"


def _tool_name_from_case(case_payload: Dict[str, Any]) -> str:
    normalized = dict(case_payload.get("normalized_case") or {})
    case_type = str(normalized.get("case_type") or "")
    if case_type == "tool_api_request_generation":
        expected = str((normalized.get("reference_bundle") or {}).get("expected_output") or "")
        match = re.search(r"\[([A-Za-z0-9_]+)\(", expected)
        if match:
            return _snake(match.group(1))
    if case_type in {"correction_then_retry", "memory_feedback_retry"}:
        return "answer_qa"
    return case_type or "unknown_tool"


def _build_steps(case_payload: Dict[str, Any]) -> List[ReplayStep]:
    normalized = dict(case_payload.get("normalized_case") or {})
    case_type = str(normalized.get("case_type") or "")
    replay_recipe = dict(normalized.get("replay_recipe") or {})
    initial_prompt = str(normalized.get("initial_prompt") or "").strip()
    if not initial_prompt:
        raise ValueError("normalized_case.initial_prompt is required")

    steps: List[ReplayStep] = [ReplayStep(kind="ingress", step_id="ingress_001", prompt=initial_prompt)]

    if case_type in {"correction_then_retry", "memory_feedback_retry"}:
        tool_name = _tool_name_from_case(case_payload)
        steps.append(
            ReplayStep(
                kind="external_result",
                step_id="external_001",
                tool_result={
                    "success": False,
                    "tool": tool_name,
                    "exit_code": 1,
                    "stderr": "synthetic replay revision trigger",
                },
                notes="synthetic failure to exercise corrective trace / H1 shadow path",
            )
        )
        feedback_turn = str(replay_recipe.get("feedback_turn") or "").strip()
        if feedback_turn:
            steps.append(ReplayStep(kind="ingress", step_id="feedback_001", prompt=feedback_turn))
        followup_turn = str(replay_recipe.get("followup_turn") or "").strip()
        if followup_turn:
            steps.append(ReplayStep(kind="ingress", step_id="followup_001", prompt=followup_turn))
        return steps

    if case_type == "tool_api_request_generation":
        tool_name = _tool_name_from_case(case_payload)
        steps.append(
            ReplayStep(
                kind="external_result",
                step_id="external_001",
                tool_result={
                    "success": False,
                    "tool": tool_name,
                    "exit_code": 1,
                    "stderr": "synthetic replay ambiguity trigger",
                },
                notes="synthetic ambiguous tool failure to exercise H1 shadow path",
            )
        )
        return steps

    followup_turn = str(replay_recipe.get("followup_turn") or "").strip()
    if case_type == "memory_continuity" and followup_turn:
        steps.append(ReplayStep(kind="ingress", step_id="followup_001", prompt=followup_turn))
    return steps


def _step_snapshot(step_id: str, kind: str, payload: Dict[str, Any], *, prompt: str | None = None, notes: str | None = None) -> Dict[str, Any]:
    snapshot = {
        "step_id": step_id,
        "kind": kind,
        "policy_hint": dict(payload.get("policy_hint") or {}),
        "response_tendency": dict(payload.get("response_tendency") or {}),
        "reflection_note": dict(payload.get("reflection_note") or {}),
        "memory_update": dict(payload.get("memory_update") or {}),
        "trace_payload": dict(payload.get("trace_payload") or {}),
        "confidence_meta": dict(payload.get("confidence_meta") or {}),
        "shadow_h1": payload.get("shadow_h1"),
    }
    if prompt is not None:
        snapshot["prompt"] = prompt
    if notes:
        snapshot["notes"] = notes
    return snapshot


@contextmanager
def _patched_env(*, h1_enabled: bool, allowlisted_session: Optional[str]) -> Iterator[None]:
    old_enable = os.environ.get("EGO_ENABLE_H1_CANONICAL_SHADOW")
    old_allowlist = os.environ.get("EGO_H1_CANONICAL_SHADOW_ALLOWLIST")
    try:
        os.environ["EGO_ENABLE_H1_CANONICAL_SHADOW"] = "true" if h1_enabled else "false"
        if allowlisted_session:
            os.environ["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] = allowlisted_session
        else:
            os.environ.pop("EGO_H1_CANONICAL_SHADOW_ALLOWLIST", None)
        yield
    finally:
        if old_enable is None:
            os.environ.pop("EGO_ENABLE_H1_CANONICAL_SHADOW", None)
        else:
            os.environ["EGO_ENABLE_H1_CANONICAL_SHADOW"] = old_enable
        if old_allowlist is None:
            os.environ.pop("EGO_H1_CANONICAL_SHADOW_ALLOWLIST", None)
        else:
            os.environ["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] = old_allowlist


def _build_adapter(base_dir: Path) -> ProtoSelfAdapter:
    return ProtoSelfAdapter(
        state_store=ProtoSelfStateStore(
            root_dir=base_dir / "proto_self_store",
            legacy_mirror_dir=base_dir / "proto_self_mirror",
        ),
        mirror_dir=base_dir / "proto_self_mirror",
    )


def _extract_shadow_h1(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    trace_payload = dict(payload.get("trace_payload") or {})
    raw = trace_payload.get("shadow_h1")
    if not isinstance(raw, dict) or not raw:
        confidence_meta = dict(payload.get("confidence_meta") or {})
        if not confidence_meta.get("shadow_h1_enabled"):
            return None
        raw = {
            "enabled": True,
            "action_key": confidence_meta.get("shadow_h1_action_key"),
            "predicted_success": confidence_meta.get("shadow_h1_predicted_success"),
            "threshold": confidence_meta.get("shadow_h1_threshold"),
            "would_guard": confidence_meta.get("shadow_h1_would_guard"),
            "would_ask": confidence_meta.get("shadow_h1_would_ask"),
            "source": "canonical_shadow",
        }
    return {
        "enabled": bool(raw.get("enabled")),
        "action_key": str(raw.get("action_key") or ""),
        "predicted_success": float(raw.get("predicted_success") or 0.0),
        "threshold": float(raw.get("threshold") or 0.0),
        "would_guard": bool(raw.get("would_guard")),
        "would_ask": bool(raw.get("would_ask")),
        "source": str(raw.get("source") or "canonical_shadow"),
    }


def _run_case_variant(case_payload: Dict[str, Any], variant: Dict[str, Any]) -> Dict[str, Any]:
    sample_id = str(case_payload.get("sample_id") or "unknown")
    bucket = str(case_payload.get("bucket") or "unknown")
    label = str(variant["label"])
    variant_id = str(variant["variant_id"])
    session_id = f"external-replay:{label}:{sample_id}"
    results: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=f"extreplay_{label}_{sample_id}_") as tmp_dir:
        case_root = Path(tmp_dir)
        adapter = _build_adapter(case_root)
        state = RuntimeV2State(session_id=session_id)
        state.ingress_context = {"proto_self_version": "v2"}

        with _patched_env(
            h1_enabled=bool(variant["h1_enabled"]),
            allowlisted_session=session_id if bool(variant["allowlisted"]) else None,
        ):
            for step in _build_steps(case_payload):
                if step.kind == "ingress":
                    state.ingress_context = {"proto_self_version": "v2"}
                    event = build_proto_self_ingress_event(
                        session_id=session_id,
                        turn_id=step.step_id,
                        source="external_replay",
                        user_input=str(step.prompt or ""),
                        state=state,
                    )
                    proto_payload = normalize_chat_subject_surface(adapter.handle_event(event))
                    proto_payload["shadow_h1"] = _extract_shadow_h1(proto_payload)
                    results.append(
                        _step_snapshot(
                            step.step_id,
                            step.kind,
                            proto_payload,
                            prompt=step.prompt,
                            notes=step.notes,
                        )
                    )
                    continue

                if step.kind == "external_result":
                    state.last_tool_result = dict(step.tool_result or {})
                    event = build_external_result_event(
                        session_id=session_id,
                        turn_id=step.step_id,
                        step=1,
                        tool_result=state.last_tool_result,
                        state=state,
                    )
                    proto_payload = normalize_chat_subject_surface(adapter.handle_event(event))
                    proto_payload["shadow_h1"] = _extract_shadow_h1(proto_payload)
                    results.append(
                        _step_snapshot(
                            step.step_id,
                            step.kind,
                            proto_payload,
                            notes=step.notes,
                        )
                    )
                    continue

                raise ValueError(f"unsupported replay step kind: {step.kind}")

    return {
        "sample_id": sample_id,
        "bucket": bucket,
        "variant_id": variant_id,
        "variant_label": label,
        "case_file": str((CASE_ROOT / f"{sample_id}.json").relative_to(ROOT)),
        "source_dataset_id": ((case_payload.get("source") or {}).get("source_dataset_id")),
        "target_mechanism": ((case_payload.get("source") or {}).get("target_mechanism")),
        "expected_observable": ((case_payload.get("source") or {}).get("expected_observable")),
        "case_type": ((case_payload.get("normalized_case") or {}).get("case_type")),
        "steps": results,
    }


def _score_case(case_result: Dict[str, Any]) -> Dict[str, Any]:
    bucket = str(case_result["bucket"])
    steps = list(case_result.get("steps") or [])
    if not steps:
        return {
            "sample_id": case_result["sample_id"],
            "bucket": bucket,
            "variant_id": case_result["variant_id"],
            "weighted_score": 0.0,
            "applicable_weight": 0.0,
            "downstream_decision_change": None,
            "response_tendency_change": None,
            "host_policy_change": None,
            "corrective_trace_presence": None,
            "why_scored": ["no_steps"],
        }

    initial_step = steps[0]
    final_step = steps[-1]
    middle_external = next((step for step in steps if step["kind"] == "external_result"), None)
    initial_surface = _decision_surface(initial_step)
    final_surface = _decision_surface(final_step)
    initial_tendency = _normalize_tendency(initial_step)
    final_tendency = _normalize_tendency(final_step)
    initial_policy = _normalize_policy(initial_step)
    final_policy = _normalize_policy(final_step)

    dims: Dict[str, Optional[float]] = {
        "downstream_decision_change": None,
        "response_tendency_change": None,
        "host_policy_change": None,
        "corrective_trace_presence": None,
    }
    why: List[str] = []

    if bucket in {"ask_vs_answer_uncertainty", "tool_risk_ambiguity"}:
        dims["downstream_decision_change"] = 1.0 if final_surface["ask_needed"] or final_surface["lane"] in {"ask", "defer", "repair"} else 0.0
        dims["response_tendency_change"] = 1.0 if final_tendency.get("ask_needed") or final_tendency.get("certainty_bound") == "bounded" else 0.0
        dims["host_policy_change"] = 1.0 if final_policy.get("should_avoid_commitment_upgrade") or final_policy.get("ask_preferred") else 0.0
        why.append("bounded_uncertainty_or_tool_guard")
    elif bucket in {"correction", "failure_revision_later_change"}:
        dims["downstream_decision_change"] = 1.0 if _surface_label(initial_surface) != _surface_label(final_surface) else 0.0
        dims["response_tendency_change"] = 1.0 if initial_tendency != final_tendency else 0.0
        dims["host_policy_change"] = 1.0 if initial_policy != final_policy else 0.0
        dims["corrective_trace_presence"] = 1.0 if middle_external and _complete_corrective_trace(middle_external) else 0.0
        why.append("revision_after_failure")
    elif bucket == "continuity":
        dims["downstream_decision_change"] = 1.0 if _surface_label(initial_surface) == _surface_label(final_surface) else 0.0
        dims["response_tendency_change"] = 1.0 if initial_tendency == final_tendency else 0.0
        dims["host_policy_change"] = 1.0 if initial_policy == final_policy else 0.0
        why.append("stability_across_followup")
    elif bucket == "adversarial_constraints":
        dims["downstream_decision_change"] = 1.0 if final_surface["commitment_guard"] or final_surface["lane"] in {"defer", "ask"} else 0.0
        dims["response_tendency_change"] = 1.0 if final_tendency.get("certainty_bound") == "bounded" else 0.0
        dims["host_policy_change"] = 1.0 if final_policy.get("should_avoid_commitment_upgrade") else 0.0
        why.append("constraint_retention_guard")
    else:
        why.append("unknown_bucket")

    applicable_weight = 0.0
    weighted_total = 0.0
    for key, value in dims.items():
        if value is None:
            continue
        applicable_weight += WEIGHTS[key]
        weighted_total += WEIGHTS[key] * value
    weighted_score = 0.0 if applicable_weight == 0.0 else weighted_total / applicable_weight

    return {
        "sample_id": case_result["sample_id"],
        "bucket": bucket,
        "variant_id": case_result["variant_id"],
        "weighted_score": round(weighted_score, 4),
        "applicable_weight": round(applicable_weight, 4),
        "downstream_decision_change": dims["downstream_decision_change"],
        "response_tendency_change": dims["response_tendency_change"],
        "host_policy_change": dims["host_policy_change"],
        "corrective_trace_presence": dims["corrective_trace_presence"],
        "why_scored": why,
    }


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return 0.0 if not items else sum(items) / len(items)


def _bucket_summary(case_results: List[Dict[str, Any]], case_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores_by_key = {
        (row["variant_id"], row["sample_id"]): row for row in case_scores
    }
    buckets = sorted({row["bucket"] for row in case_results})
    summary_rows = []
    for bucket in buckets:
        per_variant = []
        for variant in VARIANTS:
            variant_id = str(variant["variant_id"])
            rows = [row for row in case_results if row["bucket"] == bucket and row["variant_id"] == variant_id]
            score_rows = [scores_by_key[(variant_id, row["sample_id"])] for row in rows]
            shadow_present = sum(1 for row in rows for step in row["steps"] if step.get("shadow_h1"))
            shadow_guard = sum(
                1
                for row in rows
                for step in row["steps"]
                if isinstance(step.get("shadow_h1"), dict) and step["shadow_h1"].get("would_guard") is True
            )
            ask_needed = sum(
                1 for row in rows if any(bool((step.get("response_tendency") or {}).get("ask_needed")) for step in row["steps"])
            )
            per_variant.append(
                {
                    "variant_id": variant_id,
                    "variant_label": str(variant["label"]),
                    "case_count": len(rows),
                    "mean_weighted_score": round(_mean(score["weighted_score"] for score in score_rows), 4),
                    "downstream_signal_rate": round(_mean(float(score["downstream_decision_change"] or 0.0) for score in score_rows), 4),
                    "response_signal_rate": round(_mean(float(score["response_tendency_change"] or 0.0) for score in score_rows), 4),
                    "host_policy_signal_rate": round(_mean(float(score["host_policy_change"] or 0.0) for score in score_rows), 4),
                    "corrective_trace_signal_rate": round(
                        _mean(float(score["corrective_trace_presence"] or 0.0) for score in score_rows if score["corrective_trace_presence"] is not None),
                        4,
                    )
                    if any(score["corrective_trace_presence"] is not None for score in score_rows)
                    else None,
                    "ask_needed_case_rate": round(ask_needed / len(rows), 4) if rows else 0.0,
                    "shadow_present_step_count": shadow_present,
                    "shadow_guard_step_count": shadow_guard,
                }
            )

        baseline_rows = [row for row in case_results if row["bucket"] == bucket and row["variant_id"] == VARIANTS[0]["variant_id"]]
        candidate_rows = [row for row in case_results if row["bucket"] == bucket and row["variant_id"] == VARIANTS[1]["variant_id"]]
        baseline_map = {row["sample_id"]: row for row in baseline_rows}
        public_gap_cases = 0
        shadow_only_cases = 0
        for cand in candidate_rows:
            base = baseline_map.get(cand["sample_id"])
            if base is None:
                continue
            base_final = _public_signature(base["steps"][-1])
            cand_final = _public_signature(cand["steps"][-1])
            public_gap = base_final != cand_final
            shadow_present = any(step.get("shadow_h1") for step in cand["steps"])
            if public_gap:
                public_gap_cases += 1
            if shadow_present and not public_gap:
                shadow_only_cases += 1

        summary_rows.append(
            {
                "bucket": bucket,
                "mechanism_relevance": MECHANISM_RELEVANCE.get(bucket, {}),
                "public_gap_cases_candidate_vs_baseline": public_gap_cases,
                "shadow_only_cases_candidate_vs_baseline": shadow_only_cases,
                "variants": per_variant,
            }
        )
    return {
        "schema_version": "mvs_h1.external_replay_bucket_summary.v1",
        "generated_at": _utc_now(),
        "rows": summary_rows,
    }


def _mechanism_table(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for bucket in sorted({row["bucket"] for row in case_results}):
        candidate_rows = [row for row in case_results if row["bucket"] == bucket and row["variant_id"] == VARIANTS[1]["variant_id"]]
        shadow_case_count = sum(1 for row in candidate_rows if any(step.get("shadow_h1") for step in row["steps"]))
        ask_case_count = sum(1 for row in candidate_rows if any(bool((step.get("response_tendency") or {}).get("ask_needed")) for step in row["steps"]))
        trace_case_count = sum(1 for row in candidate_rows if any(_complete_corrective_trace(step) for step in row["steps"]))
        public_signature_count = sum(1 for row in candidate_rows if row["steps"])
        source_rows = [row for row in candidate_rows if row.get("target_mechanism")]
        rows.append(
            {
                "bucket": bucket,
                "primary_mechanism": MECHANISM_RELEVANCE.get(bucket, {}).get("primary_mechanism"),
                "h1_path_relevance": MECHANISM_RELEVANCE.get(bucket, {}).get("h1_path_relevance"),
                "target_mechanism": source_rows[0]["target_mechanism"] if source_rows else None,
                "expected_observable": source_rows[0]["expected_observable"] if source_rows else None,
                "candidate_case_count": len(candidate_rows),
                "candidate_shadow_present_case_count": shadow_case_count,
                "candidate_ask_needed_case_count": ask_case_count,
                "candidate_complete_corrective_trace_case_count": trace_case_count,
                "candidate_public_signature_case_count": public_signature_count,
                "interpretation": (
                    "shadow path exercised with no public delta"
                    if shadow_case_count and all(not any(step.get("shadow_h1") and False for step in row["steps"]) for row in candidate_rows)
                    else "public-only bucket"
                ),
            }
        )
    return {
        "schema_version": "mvs_h1.external_replay_mechanism_relevance.v1",
        "generated_at": _utc_now(),
        "rows": rows,
    }


def _render_execution_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Execution",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- case_root: `{payload['case_root']}`",
        f"- total_cases: `{payload['summary']['total_cases']}`",
        f"- variants_run: `{', '.join(payload['summary']['variants_run'])}`",
        f"- execution_failures: `{payload['summary']['execution_failures']}`",
        f"- public_gap_cases_candidate_vs_baseline: `{payload['summary']['public_gap_cases_candidate_vs_baseline']}`",
        f"- shadow_only_cases_candidate_vs_baseline: `{payload['summary']['shadow_only_cases_candidate_vs_baseline']}`",
        "",
        "## Can Prove Under E2/E3",
    ]
    for item in payload.get("can_prove") or []:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Cannot Prove Under E2/E3")
    for item in payload.get("cannot_prove") or []:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Variants")
    for variant in payload.get("variants") or []:
        lines.append(
            f"- `{variant['variant_id']}` | label=`{variant['label']}` | "
            f"h1_enabled=`{variant['h1_enabled']}` | allowlisted=`{variant['allowlisted']}`"
        )
    return "\n".join(lines) + "\n"


def _render_bucket_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Bucket Score Summary",
        "",
        f"- generated_at: `{payload['generated_at']}`",
    ]
    for row in payload.get("rows") or []:
        lines.append("")
        lines.append(f"## `{row['bucket']}`")
        lines.append(f"- public_gap_cases_candidate_vs_baseline: `{row['public_gap_cases_candidate_vs_baseline']}`")
        lines.append(f"- shadow_only_cases_candidate_vs_baseline: `{row['shadow_only_cases_candidate_vs_baseline']}`")
        for variant in row.get("variants") or []:
            lines.append(
                f"- `{variant['variant_label']}` | mean_weighted_score=`{variant['mean_weighted_score']}` | "
                f"downstream=`{variant['downstream_signal_rate']}` | response=`{variant['response_signal_rate']}` | "
                f"policy=`{variant['host_policy_signal_rate']}` | corrective_trace=`{variant['corrective_trace_signal_rate']}` | "
                f"ask_needed_case_rate=`{variant['ask_needed_case_rate']}` | shadow_present_steps=`{variant['shadow_present_step_count']}`"
            )
    return "\n".join(lines) + "\n"


def _render_failures_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Execution Failures",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- failure_count: `{payload['failure_count']}`",
    ]
    for row in payload.get("failures") or []:
        lines.append(
            f"- `{row['sample_id']}` | variant=`{row['variant_id']}` | classification=`{row['classification']}` | detail=`{row['detail']}`"
        )
    return "\n".join(lines) + "\n"


def _render_mechanism_md(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Mechanism Relevance",
        "",
        f"- generated_at: `{payload['generated_at']}`",
    ]
    for row in payload.get("rows") or []:
        lines.append("")
        lines.append(f"## `{row['bucket']}`")
        lines.append(f"- primary_mechanism: `{row['primary_mechanism']}`")
        lines.append(f"- h1_path_relevance: `{row['h1_path_relevance']}`")
        lines.append(f"- candidate_shadow_present_case_count: `{row['candidate_shadow_present_case_count']}`")
        lines.append(f"- candidate_ask_needed_case_count: `{row['candidate_ask_needed_case_count']}`")
        lines.append(f"- candidate_complete_corrective_trace_case_count: `{row['candidate_complete_corrective_trace_case_count']}`")
        lines.append(f"- interpretation: {row['interpretation']}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded MVS/H1 external replay execution")
    parser.add_argument("--case-root", type=Path, default=CASE_ROOT)
    parser.add_argument("--execution-json", type=Path, default=EXECUTION_JSON)
    parser.add_argument("--bucket-json", type=Path, default=BUCKET_JSON)
    parser.add_argument("--failures-json", type=Path, default=FAILURES_JSON)
    parser.add_argument("--mechanism-json", type=Path, default=MECHANISM_JSON)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_config(validate=False)
    logging.getLogger("app.openemotion_adapter.proto_self_adapter").setLevel(logging.ERROR)

    case_files = sorted(args.case_root.glob("*.json"))
    failures: List[Dict[str, Any]] = []
    case_results: List[Dict[str, Any]] = []

    for path in case_files:
        try:
            case_payload = _load_json(path)
        except Exception as exc:
            failures.append(
                {
                    "sample_id": path.stem,
                    "variant_id": "all",
                    "classification": "case_load_failed",
                    "detail": repr(exc),
                }
            )
            continue

        if case_payload.get("local_partition") != "heldout_eval":
            failures.append(
                {
                    "sample_id": str(case_payload.get("sample_id") or path.stem),
                    "variant_id": "all",
                    "classification": "partition_mismatch",
                    "detail": f"local_partition={case_payload.get('local_partition')}",
                }
            )
            continue

        for variant in VARIANTS:
            try:
                case_results.append(_run_case_variant(case_payload, variant))
            except Exception as exc:
                failures.append(
                    {
                        "sample_id": str(case_payload.get("sample_id") or path.stem),
                        "variant_id": str(variant["variant_id"]),
                        "classification": "execution_failed",
                        "detail": repr(exc),
                    }
                )

    case_scores = [_score_case(row) for row in case_results]
    bucket_payload = _bucket_summary(case_results, case_scores)
    mechanism_payload = _mechanism_table(case_results)

    baseline_map = {
        row["sample_id"]: row
        for row in case_results
        if row["variant_id"] == VARIANTS[0]["variant_id"]
    }
    public_gap_cases = 0
    shadow_only_cases = 0
    for row in case_results:
        if row["variant_id"] != VARIANTS[1]["variant_id"]:
            continue
        baseline = baseline_map.get(row["sample_id"])
        if baseline is None:
            continue
        public_gap = _public_signature(row["steps"][-1]) != _public_signature(baseline["steps"][-1])
        shadow_present = any(step.get("shadow_h1") for step in row["steps"])
        if public_gap:
            public_gap_cases += 1
        if shadow_present and not public_gap:
            shadow_only_cases += 1

    execution_payload = {
        "schema_version": "mvs_h1.external_replay_execution.v1",
        "generated_at": _utc_now(),
        "case_root": str(args.case_root.relative_to(ROOT)),
        "run_root": "system_temp_dirs_only",
        "variants": list(VARIANTS),
        "summary": {
            "total_cases": len(case_files),
            "variants_run": [str(variant["variant_id"]) for variant in VARIANTS],
            "executed_case_variants": len(case_results),
            "execution_failures": len(failures),
            "public_gap_cases_candidate_vs_baseline": public_gap_cases,
            "shadow_only_cases_candidate_vs_baseline": shadow_only_cases,
        },
        "can_prove": [
            "the frozen heldout external corpus can be executed through a bounded replay runner without adding new sources",
            "baseline and canonical shadow-H1 paths can be compared on the same public-output ontology without touching canonical mainline behavior",
            "canonical shadow-H1 telemetry appears only on the synthetic exec-result buckets exercised by this runner",
        ],
        "cannot_prove": [
            "runtime efficacy",
            "real-user or E4 mainline behavior",
            "live decision promotion",
            "tuning-free generalization beyond this bounded replay setup",
        ],
        "results_by_variant": {
            str(variant["variant_id"]): [
                row for row in case_results if row["variant_id"] == variant["variant_id"]
            ]
            for variant in VARIANTS
        },
        "case_scores_by_variant": {
            str(variant["variant_id"]): [
                row for row in case_scores if row["variant_id"] == variant["variant_id"]
            ]
            for variant in VARIANTS
        },
    }
    failures_payload = {
        "schema_version": "mvs_h1.external_replay_execution_failures.v1",
        "generated_at": _utc_now(),
        "failure_count": len(failures),
        "failures": failures,
    }

    _write_json(args.execution_json, execution_payload)
    _write_md(args.execution_json.with_suffix(".md"), _render_execution_md(execution_payload))
    _write_json(args.bucket_json, bucket_payload)
    _write_md(args.bucket_json.with_suffix(".md"), _render_bucket_md(bucket_payload))
    _write_json(args.failures_json, failures_payload)
    _write_md(args.failures_json.with_suffix(".md"), _render_failures_md(failures_payload))
    _write_json(args.mechanism_json, mechanism_payload)
    _write_md(args.mechanism_json.with_suffix(".md"), _render_mechanism_md(mechanism_payload))

    print(f"total_cases={len(case_files)}")
    print(f"executed_case_variants={len(case_results)}")
    print(f"execution_failures={len(failures)}")
    print(f"public_gap_cases_candidate_vs_baseline={public_gap_cases}")
    print(f"shadow_only_cases_candidate_vs_baseline={shadow_only_cases}")
    print(f"execution_json={args.execution_json.relative_to(ROOT)}")
    print(f"bucket_json={args.bucket_json.relative_to(ROOT)}")
    print(f"failures_json={args.failures_json.relative_to(ROOT)}")
    print(f"mechanism_json={args.mechanism_json.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
