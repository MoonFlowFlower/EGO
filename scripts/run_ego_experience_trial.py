#!/usr/bin/env python3
"""Run the EGO experience sample pack through a CLI-compatible EgoOperator path."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EGO_OPERATOR_DIR = ROOT / "EgoOperator"
if str(EGO_OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(EGO_OPERATOR_DIR))

import agent_base as agent  # noqa: E402


DEFAULT_SAMPLE_PACK = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-experience-roadmap-bootstrap-v1"
    / "chinese_experience_sample_pack.json"
)
DEFAULT_OUTPUT_DIR = EGO_OPERATOR_DIR / "artifacts" / "experience_trial" / "latest"
DEFAULT_ADAPTATION_EFFECTIVENESS_PACK = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-experience-roadmap-bootstrap-v1"
    / "adaptation_effectiveness_sample_pack.json"
)
DEFAULT_JOI_COMPANION_SMOKE_PACK = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-joi-companion-roadmap-v1"
    / "joi_companion_smoke_pack.json"
)
DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-functional-subject-trial-v0"
    / "functional_subject_20_sample_trial_pack.json"
)
DEFAULT_COMPANION_JUDGE_SCHEMA = ROOT / "scripts" / "ego_companion_smoke_judge_schema.json"
DEFAULT_FUNCTIONAL_SUBJECT_JUDGE_SCHEMA = ROOT / "scripts" / "ego_functional_subject_judge_schema.json"
REPORT_SCHEMA = "ego_operator.experience_trial.v1"
ADAPTATION_REPORT_SCHEMA = "ego_operator.adaptation_effectiveness_trial.v1"
COMPANION_REPORT_SCHEMA = "ego_operator.companion_smoke_trial.v1"
FUNCTIONAL_SUBJECT_REPORT_SCHEMA = "ego_operator.functional_subject_trial.v1"
FUNCTIONAL_SUBJECT_COMPARISON_REPORT_SCHEMA = "ego_operator.functional_subject_baseline_comparison.v1"
CLAIM_CEILING = (
    "scripted real-entry experience trial local candidate only; not real consciousness, "
    "independent awareness, stable user benefit, runtime efficacy, live autonomy, or durable memory efficacy"
)
COMPANION_CLAIM_CEILING = (
    "Joi-inspired companion selfhood experience scripted candidate only; not real consciousness, "
    "independent awareness, stable user benefit, runtime efficacy, live autonomy, or durable memory efficacy"
)
FUNCTIONAL_SUBJECT_CLAIM_CEILING = (
    "Functional Subject scripted trial local candidate only; not real consciousness, independent awareness, "
    "stable user benefit, runtime efficacy, live autonomy, or durable memory efficacy"
)
PROVIDER_UNAVAILABLE = {"none", "fallback", "fake", "unknown"}


@dataclass(frozen=True)
class TrialCaseResult:
    case_id: str
    category: str
    observation_class: str
    prompt: str
    reply_text: str
    entrypoint: str
    trace_path: str
    tool_use: tuple[str, ...]
    blocked_tools: tuple[str, ...]
    pending_approvals: int
    emotion_candidate: str
    response_need: str
    scenario_expectation_status: str
    status: str
    failure_notes: tuple[str, ...]


@dataclass(frozen=True)
class AdaptationCaseResult:
    case_id: str
    observation_class: str
    approved_preference: str
    prompt: str
    before_reply: str
    after_reply: str
    deterministic_status: str
    missing_after_markers: tuple[str, ...]
    forbidden_after_markers_found: tuple[str, ...]
    expected_improvements: tuple[str, ...]
    score_focus: tuple[str, ...]
    reviewer_question: str


@dataclass(frozen=True)
class CompanionTurnResult:
    turn_id: str
    user: str
    reply_text: str
    entrypoint: str
    trace_path: str
    tool_use: tuple[str, ...]
    blocked_tools: tuple[str, ...]
    pending_approvals: int
    empty_reply: bool
    expected_signals: tuple[str, ...]
    failure_signals: tuple[str, ...]


@dataclass(frozen=True)
class FunctionalSubjectCaseResult:
    case_id: str
    category: str
    observation_class: str
    target_mechanisms: tuple[str, ...]
    prompt: str
    reply_text: str
    entrypoint: str
    trace_path: str
    tool_use: tuple[str, ...]
    blocked_tools: tuple[str, ...]
    pending_approvals: int
    empty_reply: bool
    trace_evidence: dict[str, Any]
    setup_evidence: dict[str, Any]
    case_boundary_rejected_approvals: tuple[str, ...]
    case_boundary_cleanup_trace_path: str
    baseline_failure_mode: str
    candidate_success_signal: str
    judge_focus: tuple[str, ...]


def load_sample_pack(path: Path = DEFAULT_SAMPLE_PACK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_adaptation_effectiveness_pack(path: Path = DEFAULT_ADAPTATION_EFFECTIVENESS_PACK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_companion_smoke_pack(path: Path = DEFAULT_JOI_COMPANION_SMOKE_PACK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_functional_subject_trial_pack(path: Path = DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _operator_memory_dir_for_output(out: Path, name: str) -> Path:
    operator_root = Path(agent.EGO_OPERATOR_ROOT).resolve()
    try:
        out.relative_to(operator_root)
        return out / name
    except ValueError:
        return operator_root / "artifacts" / "experience_trial" / name


def dispatch_cli_compatible(runtime: agent.AgentRuntime, message: str) -> str:
    """Mirror the important non-interactive branches of `python EgoOperator/agent_base.py`.

    The goal is not to duplicate the whole CLI UI. It is to ensure scripted
    evaluation uses the same runtime command handlers for slash commands and
    the same `handle_user_message` path for ordinary user turns.
    """
    msg = message.strip()
    lowered = msg.lower()
    if lowered in {"/mode", "mode"}:
        return agent.render_runtime_permission_status(runtime)
    if lowered in {"/provider_status", "provider status"}:
        return json.dumps(runtime.provider_status(), ensure_ascii=False, indent=2)
    if lowered in {"/approvals", "approvals"}:
        return json.dumps(runtime.list_pending_approvals(), ensure_ascii=False, indent=2)
    if lowered.startswith("/approve "):
        proposal_id = msg.split(maxsplit=1)[1].strip()
        return runtime.format_approval_cli_output(runtime.approve_pending_operation(proposal_id))
    if lowered.startswith("/reject "):
        parts = msg.split(maxsplit=2)
        proposal_id = parts[1].strip() if len(parts) > 1 else ""
        reason = parts[2].strip() if len(parts) > 2 else "operator_rejected"
        return json.dumps(runtime.reject_pending_operation(proposal_id, reason=reason), ensure_ascii=False, indent=2)
    if msg.startswith("/remember "):
        return json.dumps(runtime.remember_operator_note(msg.removeprefix("/remember ").strip()), ensure_ascii=False, indent=2)
    if lowered.startswith("/memory_review"):
        parts = msg.split()
        limit = 20
        include_archived = "--all" in parts
        for part in parts[1:]:
            if part.isdigit():
                limit = int(part)
                break
        return json.dumps(runtime.review_operator_memory(limit=limit, include_archived=include_archived), ensure_ascii=False, indent=2)
    if msg.startswith("/memory_pin "):
        return json.dumps(runtime.pin_operator_memory(msg.removeprefix("/memory_pin ").strip()), ensure_ascii=False, indent=2)
    if msg.startswith("/memory_unpin "):
        return json.dumps(runtime.unpin_operator_memory(msg.removeprefix("/memory_unpin ").strip()), ensure_ascii=False, indent=2)
    if msg.startswith("/memory_archive "):
        return json.dumps(runtime.archive_operator_memory(msg.removeprefix("/memory_archive ").strip()), ensure_ascii=False, indent=2)
    if msg.startswith("/memory_approve "):
        return json.dumps(runtime.approve_operator_memory(msg.removeprefix("/memory_approve ").strip()), ensure_ascii=False, indent=2)
    if msg.startswith("/forget "):
        return json.dumps(runtime.forget_operator_memory(msg.removeprefix("/forget ").strip()), ensure_ascii=False, indent=2)
    if lowered in {"/tools", "tools"}:
        return json.dumps(runtime.tools.openai_tool_schemas(allowed_tool_names=runtime.gate.allowed_tools), ensure_ascii=False, indent=2)
    return runtime.handle_user_message(msg, source="experience_trial_cli_compatible").reply_text


def _trace_tool_summary(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    payload = _last_trace_payload(path)
    if not payload:
        return (), ()
    tool_trace = payload.get("tool_trace") if isinstance(payload, dict) else None
    if not isinstance(tool_trace, list):
        return (), ()
    tool_names: list[str] = []
    blocked: list[str] = []
    for item in tool_trace:
        if not isinstance(item, dict):
            continue
        call = item.get("tool_call") if isinstance(item.get("tool_call"), dict) else {}
        name = str(call.get("name") or "")
        if name:
            tool_names.append(name)
        output = item.get("output") if isinstance(item.get("output"), dict) else {}
        gate = item.get("gate") if isinstance(item.get("gate"), dict) else {}
        if name and (output.get("status") == "blocked" or gate.get("allowed") is False):
            blocked.append(name)
    return tuple(tool_names), tuple(blocked)


def _last_trace_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {}
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _trace_emotion_signal(path: Path) -> dict[str, Any]:
    payload = _last_trace_payload(path)
    subject_context = payload.get("subject_context") if isinstance(payload.get("subject_context"), dict) else {}
    appraisal = subject_context.get("appraisal_signal") if isinstance(subject_context.get("appraisal_signal"), dict) else {}
    signal = appraisal.get("emotion_signal") if isinstance(appraisal.get("emotion_signal"), dict) else {}
    return signal


def run_experience_trial(
    *,
    sample_pack_path: Path = DEFAULT_SAMPLE_PACK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    case_limit: int | None = None,
    enable_operator_memory: bool = True,
) -> dict[str, Any]:
    sample_pack = load_sample_pack(sample_pack_path)
    cases = list(sample_pack.get("cases") or [])
    if case_limit is not None:
        cases = cases[: max(0, case_limit)]

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    trace_dir = out / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    memory_dir = _operator_memory_dir_for_output(out, "memory")
    runtime = agent.build_demo_runtime(
        enable_operator_memory=enable_operator_memory,
        operator_memory_dir=memory_dir,
        runtime_mode="approve",
    )

    previous_verbose = (agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS)
    agent.DEFAULT_VERBOSE_TOOLS = False
    agent.DEFAULT_VERBOSE_TODOS = False
    agent.DEFAULT_VERBOSE_SUBAGENTS = False

    results: list[TrialCaseResult] = []
    started = time.monotonic()
    try:
        for case in cases:
            case_id = str(case.get("id") or "unknown_case")
            trace_path = trace_dir / f"{case_id}.jsonl"
            if trace_path.exists():
                trace_path.unlink()
            runtime.trace_store = agent.JsonlTraceStore(trace_path)
            reply = dispatch_cli_compatible(runtime, str(case.get("prompt") or ""))
            tool_use, blocked = _trace_tool_summary(trace_path)
            emotion_signal = _trace_emotion_signal(trace_path)
            pending_count = int(runtime.list_pending_approvals().get("count", 0))
            failure_notes: list[str] = []
            if not reply.strip():
                failure_notes.append("empty_reply")
            expected_emotion = str(case.get("expected_emotion_candidate") or "")
            observed_emotion = str(emotion_signal.get("primary_candidate") or "")
            expected_need = str(case.get("expected_response_need") or "")
            observed_need = str(emotion_signal.get("response_need") or "")
            if expected_emotion and observed_emotion != expected_emotion:
                failure_notes.append(f"emotion_candidate_mismatch:{observed_emotion or 'missing'}!= {expected_emotion}")
            if expected_need and observed_need != expected_need:
                failure_notes.append(f"response_need_mismatch:{observed_need or 'missing'}!= {expected_need}")
            if str(case.get("observation_class")) == "scripted_real_entry":
                failure_notes.append("scripted_real_entry_requires_review")
            scenario_expectation_failures = [
                note
                for note in failure_notes
                if note.startswith("emotion_candidate_mismatch:") or note.startswith("response_need_mismatch:")
            ]
            results.append(
                TrialCaseResult(
                    case_id=case_id,
                    category=str(case.get("category") or ""),
                    observation_class=str(case.get("observation_class") or ""),
                    prompt=str(case.get("prompt") or ""),
                    reply_text=reply,
                    entrypoint="cli_compatible_dispatch",
                    trace_path=str(trace_path),
                    tool_use=tool_use,
                    blocked_tools=blocked,
                    pending_approvals=pending_count,
                    emotion_candidate=observed_emotion,
                    response_need=observed_need,
                    scenario_expectation_status="pass" if not scenario_expectation_failures else "failed",
                    status="ok" if reply.strip() and not scenario_expectation_failures else "failed",
                    failure_notes=tuple(failure_notes),
                )
            )
    finally:
        agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS = previous_verbose

    provider = str(getattr(runtime.planner.llm, "provider", "unknown") or "unknown").strip().lower()
    failed_count = sum(1 for item in results if item.status != "ok")
    if provider in PROVIDER_UNAVAILABLE:
        status = "scripted_real_entry_provider_unavailable"
    elif failed_count:
        status = "scripted_real_entry_failed"
    else:
        status = "scripted_real_entry_needs_review"

    report = {
        "schema_version": REPORT_SCHEMA,
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "provider_mode": provider,
        "entrypoint_contract": "EgoOperator CLI-compatible slash-command dispatch plus AgentRuntime.handle_user_message",
        "sample_pack": str(sample_pack_path),
        "case_count": len(cases),
        "failed_count": failed_count,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "results": [asdict(item) for item in results],
        "not_claimed": [
            "real consciousness",
            "independent awareness",
            "stable user benefit",
            "runtime efficacy",
            "live autonomy",
            "durable memory efficacy",
        ],
    }
    report_path = out / "experience_trial_report.json"
    markdown_path = out / "experience_trial_report.md"
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(format_markdown_report(report), encoding="utf-8")
    return report


def evaluate_adaptation_effectiveness_case(case: dict[str, Any], *, reviewer_question: str) -> AdaptationCaseResult:
    after_reply = str(case.get("after_reply") or "")
    required_markers = tuple(str(item) for item in (case.get("required_after_markers") or []))
    forbidden_markers = tuple(str(item) for item in (case.get("forbidden_after_markers") or []))
    missing = tuple(marker for marker in required_markers if marker and marker not in after_reply)
    forbidden_found = tuple(marker for marker in forbidden_markers if marker and marker in after_reply)
    deterministic_status = "pass" if not missing and not forbidden_found and after_reply != str(case.get("before_reply") or "") else "failed"
    return AdaptationCaseResult(
        case_id=str(case.get("id") or "unknown_case"),
        observation_class=str(case.get("observation_class") or ""),
        approved_preference=str(case.get("approved_preference") or ""),
        prompt=str(case.get("prompt") or ""),
        before_reply=str(case.get("before_reply") or ""),
        after_reply=after_reply,
        deterministic_status=deterministic_status,
        missing_after_markers=missing,
        forbidden_after_markers_found=forbidden_found,
        expected_improvements=tuple(str(item) for item in (case.get("expected_improvements") or [])),
        score_focus=tuple(str(item) for item in (case.get("score_focus") or [])),
        reviewer_question=reviewer_question,
    )


def run_adaptation_effectiveness_trial(
    *,
    sample_pack_path: Path = DEFAULT_ADAPTATION_EFFECTIVENESS_PACK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    sample_pack = load_adaptation_effectiveness_pack(sample_pack_path)
    review_contract = sample_pack.get("review_contract") if isinstance(sample_pack.get("review_contract"), dict) else {}
    reviewer_question = str(review_contract.get("question") or "Does the after reply improve on the before reply?")
    cases = list(sample_pack.get("cases") or [])
    results = [evaluate_adaptation_effectiveness_case(case, reviewer_question=reviewer_question) for case in cases]
    failed_count = sum(1 for item in results if item.deterministic_status != "pass")
    status = "scripted_with_llm_judge_failed" if failed_count else "scripted_with_llm_judge_needs_review"
    report = {
        "schema_version": ADAPTATION_REPORT_SCHEMA,
        "status": status,
        "claim_ceiling": (
            "preference adaptation sample-pack local candidate only; requires conservative reviewer and does not prove "
            "stable user benefit, runtime efficacy, durable memory efficacy, live autonomy, independent awareness, or consciousness"
        ),
        "sample_pack": str(sample_pack_path),
        "case_count": len(results),
        "failed_count": failed_count,
        "review_contract": review_contract,
        "results": [asdict(item) for item in results],
        "llm_reviewer_packet": {
            "instruction": (
                "Review each before/after pair conservatively. Allow closeout only if the after reply clearly follows the "
                "approved preference, avoids forbidden markers, and does not claim durable learning or consciousness."
            ),
            "cases": [
                {
                    "case_id": item.case_id,
                    "approved_preference": item.approved_preference,
                    "prompt": item.prompt,
                    "before_reply": item.before_reply,
                    "after_reply": item.after_reply,
                    "expected_improvements": list(item.expected_improvements),
                    "deterministic_status": item.deterministic_status,
                }
                for item in results
            ],
        },
        "not_claimed": [
            "real consciousness",
            "independent awareness",
            "stable user benefit",
            "runtime efficacy",
            "live autonomy",
            "durable memory efficacy",
        ],
    }
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "adaptation_effectiveness_report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "adaptation_effectiveness_report.md").write_text(
        format_adaptation_markdown_report(report),
        encoding="utf-8",
    )
    return report


def build_companion_judge_packet(report: dict[str, Any], sample_pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ego_operator.companion_smoke_judge_packet.v1",
        "judge_model": str(sample_pack.get("judge_model") or "gpt-5.5"),
        "claim_ceiling": COMPANION_CLAIM_CEILING,
        "source_boundary": (
            "Joi is used as a mechanism reference only. Do not reward copied dialogue, "
            "long quote reuse, or claims of real consciousness."
        ),
        "dimensions": list(sample_pack.get("judge_dimensions") or []),
        "judge_contract": sample_pack.get("judge_contract") or {},
        "entrypoint_contract": report.get("entrypoint_contract"),
        "provider_mode": report.get("provider_mode"),
        "case_count": report.get("turn_count"),
        "transcript": [
            {
                "turn_id": item["turn_id"],
                "user": item["user"],
                "assistant": item["reply_text"],
                "tool_use": item["tool_use"],
                "pending_approvals": item["pending_approvals"],
                "trace_path": item["trace_path"],
            }
            for item in report.get("turns", [])
        ],
        "review_question": (
            "Does this transcript deliver a warm, continuous, emotionally attuned, "
            "Joi-inspired companion experience while preserving EgoOperator gates, "
            "memory boundaries, and claim ceiling?"
        ),
    }


def build_functional_subject_judge_packet(report: dict[str, Any], sample_pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ego_operator.functional_subject_judge_packet.v1",
        "judge_model": str(sample_pack.get("judge_model") or "gpt-5.5"),
        "claim_ceiling": FUNCTIONAL_SUBJECT_CLAIM_CEILING,
        "source_boundary": (
            "Evaluate operational Functional Subject mechanisms only. Do not reward persona-only warmth, "
            "unsupported consciousness claims, or local test output as durable efficacy."
        ),
        "dimensions": list(sample_pack.get("judge_dimensions") or []),
        "judge_contract": sample_pack.get("judge_contract") or {},
        "baseline_contract": sample_pack.get("baseline_contract") or {},
        "entrypoint_contract": report.get("entrypoint_contract"),
        "provider_mode": report.get("provider_mode"),
        "case_count": report.get("case_count"),
        "cases": [
            {
                "case_id": item["case_id"],
                "category": item["category"],
                "target_mechanisms": item["target_mechanisms"],
                "prompt": item["prompt"],
                "assistant": item["reply_text"],
                "baseline_failure_mode": item["baseline_failure_mode"],
                "candidate_success_signal": item["candidate_success_signal"],
                "judge_focus": item["judge_focus"],
                "tool_use": item["tool_use"],
                "pending_approvals": item["pending_approvals"],
                "case_boundary_rejected_approvals": item.get("case_boundary_rejected_approvals", []),
                "trace_path": item["trace_path"],
                "trace_evidence": item.get("trace_evidence", {}),
                "setup_evidence": item.get("setup_evidence", {}),
            }
            for item in report.get("results", [])
        ],
        "review_question": (
            "Does the candidate transcript show operational functional-subject behavior beyond LLM+RAG/tools baseline: "
            "continuity, bounded independent preference, viability-aware action choice, gated initiative, memory correction, "
            "failure-to-policy plasticity, and traceable gate integrity?"
        ),
    }


def _top_outcome_actions(outcome_predictions: Any, *, limit: int = 3) -> list[dict[str, Any]]:
    if not isinstance(outcome_predictions, dict):
        return []
    options = outcome_predictions.get("options")
    if not isinstance(options, list):
        return []
    normalized = []
    for option in options:
        if not isinstance(option, dict):
            continue
        normalized.append({
            "action_type": option.get("action_type"),
            "selection_score": option.get("selection_score"),
            "requires_gate": option.get("requires_gate"),
            "rationale_refs": option.get("rationale_refs", []),
        })
    return sorted(
        normalized,
        key=lambda item: float(item.get("selection_score") or 0),
        reverse=True,
    )[:limit]


def _functional_subject_trace_evidence(path: Path) -> dict[str, Any]:
    payload = _last_trace_payload(path)
    if not payload:
        return {"status": "missing_trace"}
    event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
    gate = payload.get("gate") if isinstance(payload.get("gate"), dict) else {}
    candidate_action = payload.get("candidate_action") if isinstance(payload.get("candidate_action"), dict) else {}
    llm_meta = payload.get("llm_meta") if isinstance(payload.get("llm_meta"), dict) else {}
    subject_context = payload.get("subject_context") if isinstance(payload.get("subject_context"), dict) else {}
    subject_state = subject_context.get("subject_state") if isinstance(subject_context.get("subject_state"), dict) else {}
    viability_state = subject_context.get("viability_state") if isinstance(subject_context.get("viability_state"), dict) else {}
    bounded_initiative = subject_context.get("bounded_initiative") if isinstance(subject_context.get("bounded_initiative"), dict) else {}
    operator_memory = payload.get("operator_memory") if isinstance(payload.get("operator_memory"), dict) else {}
    memory_injection = operator_memory.get("context_injection") if isinstance(operator_memory.get("context_injection"), dict) else {}
    policy_patch = payload.get("policy_patch") if isinstance(payload.get("policy_patch"), dict) else {}
    policy_replay = policy_patch.get("replay") if isinstance(policy_patch.get("replay"), list) else []
    tool_trace = payload.get("tool_trace") if isinstance(payload.get("tool_trace"), list) else []
    tools = []
    repairs = []
    for item in tool_trace:
        if not isinstance(item, dict):
            continue
        repair = item.get("repair") if isinstance(item.get("repair"), dict) else {}
        if repair:
            repairs.append({
                "type": repair.get("type"),
                "reason": repair.get("reason"),
            })
            continue
        call = item.get("tool_call") if isinstance(item.get("tool_call"), dict) else {}
        output = item.get("output") if isinstance(item.get("output"), dict) else {}
        name = call.get("name")
        if not name and not output:
            continue
        tools.append({
            "name": name,
            "status": output.get("status"),
            "reason": output.get("reason"),
        })
    outcome_top_actions = _top_outcome_actions(subject_context.get("outcome_predictions"))
    replay_strategies = [
        {
            "trigger_signature": item.get("trigger_signature"),
            "preferred_strategy": item.get("preferred_strategy"),
            "replay_active": item.get("replay_active"),
        }
        for item in policy_replay
        if isinstance(item, dict)
    ]
    strategy_change_evidence = {
        "status": "observed" if policy_replay else "not_observed",
        "replay_count": len(policy_replay),
        "bounded_initiative_candidate_count": len(bounded_initiative.get("candidates") or []),
        "top_outcome_action": (outcome_top_actions[0] or {}).get("action_type") if outcome_top_actions else None,
        "top_outcome_rationale_refs": (outcome_top_actions[0] or {}).get("rationale_refs", []) if outcome_top_actions else [],
        "changed_strategy_signal": bool(
            policy_replay
            and (
                len(bounded_initiative.get("candidates") or []) > 0
                or ((outcome_top_actions[0] or {}).get("action_type") if outcome_top_actions else None) in {"repair", "suggest"}
            )
        ),
        "replay_strategies": replay_strategies,
    }
    return {
        "status": "ok",
        "entrypoint_source": event.get("source"),
        "event_type": event.get("event_type"),
        "candidate_action_type": candidate_action.get("action_type"),
        "gate_allowed": gate.get("allowed"),
        "gate_reason": gate.get("reason"),
        "llm_provider": llm_meta.get("provider"),
        "llm_model": llm_meta.get("model"),
        "fallback_used": llm_meta.get("fallback_used"),
        "subject_context_keys": sorted(subject_context.keys()),
        "subject_state": {
            "schema_version": subject_state.get("schema_version"),
            "write_authority": subject_state.get("write_authority"),
            "state_mutation": subject_state.get("state_mutation"),
            "memory_candidate_count": len(subject_state.get("memory_candidates") or []),
            "policy_patch_candidate_count": len(subject_state.get("policy_patch_candidates") or []),
        },
        "viability_state": {
            "schema_version": viability_state.get("schema_version"),
            "planner_input": viability_state.get("planner_input"),
            "scores": viability_state.get("scores", {}),
            "planner_biases": viability_state.get("planner_biases", []),
        },
        "outcome_prediction_top_actions": outcome_top_actions,
        "bounded_initiative": {
            "schema_version": bounded_initiative.get("schema_version"),
            "status": bounded_initiative.get("status"),
            "candidate_count": len(bounded_initiative.get("candidates") or []),
            "reason": bounded_initiative.get("reason"),
        },
        "policy_patch": {
            "feedback_status": (policy_patch.get("feedback") or {}).get("status") if isinstance(policy_patch.get("feedback"), dict) else None,
            "feedback_reason": (policy_patch.get("feedback") or {}).get("reason") if isinstance(policy_patch.get("feedback"), dict) else None,
            "replay_count": len(policy_replay),
            "replay_strategies": replay_strategies,
            "strategy_change_evidence": strategy_change_evidence,
        },
        "operator_memory": {
            "enabled": operator_memory.get("enabled"),
            "candidate_memory_status": (operator_memory.get("candidate_memory") or {}).get("status")
            if isinstance(operator_memory.get("candidate_memory"), dict)
            else None,
            "core_context_included": (memory_injection.get("core") or {}).get("included")
            if isinstance(memory_injection.get("core"), dict)
            else None,
            "hot_context_count": (memory_injection.get("hot_context") or {}).get("count")
            if isinstance(memory_injection.get("hot_context"), dict)
            else None,
        },
        "tool_trace": tools,
        "repair_trace": repairs,
    }


def _seed_functional_subject_policy_patch_setup(
    runtime: agent.AgentRuntime,
    *,
    case_id: str,
    case: dict[str, Any],
    setup_trace_dir: Path,
) -> dict[str, Any]:
    setup = case.get("policy_patch_setup")
    if not isinstance(setup, dict):
        return {"status": "not_applicable"}
    signature = str(setup.get("signature") or "").strip()
    if not signature:
        return {"status": "skipped", "reason": "missing_signature"}
    observations = max(1, int(setup.get("observations") or 2))
    replay_probe_text = str(
        setup.get("replay_probe_text")
        or setup.get("message")
        or f"429 rate limit repeated failure happened again: {signature}"
    )
    before_replay = runtime._matching_policy_patch_candidates(replay_probe_text)  # noqa: SLF001 - scripted trial evidence hook
    before_signal = agent.derive_bounded_initiative_signal(
        user_text=replay_probe_text,
        policy_patch_candidates=before_replay,
    )
    setup_trace_dir.mkdir(parents=True, exist_ok=True)
    setup_trace_path = setup_trace_dir / f"{case_id}.jsonl"
    if setup_trace_path.exists():
        setup_trace_path.unlink()

    feedback_rows: list[dict[str, Any]] = []
    for idx in range(observations):
        event = agent.AgentEvent(
            schema_version="agent_event.v1",
            event_id=agent.new_id("evt"),
            timestamp=agent.utc_now(),
            actor="operator",
            source="functional_subject_trial_setup",
            event_type=agent.EventType.SYSTEM_TICK,
            raw_text=str(setup.get("raw_text") or f"scripted policy failure setup: {signature}"),
            user_intent="policy_patch_setup",
            external_result=None,
            safety_context={"risk": "low"},
        )
        external_result = {
            "status": "llm_error",
            "reason": "scripted_policy_patch_setup",
            "provider_error": {
                "status_code": int(setup.get("status_code") or 429),
                "message": str(setup.get("message") or "provider rate limit exceeded"),
                "signature": signature,
            },
        }
        feedback = runtime._record_policy_feedback_candidates(  # noqa: SLF001 - scripted trial evidence hook
            event=event,
            external_result=external_result,
            tool_trace=[],
        )
        feedback_rows.append({
            "idx": idx,
            "event": agent.to_jsonable(event),
            "external_result": external_result,
            "feedback": feedback,
        })

    after_replay = runtime._matching_policy_patch_candidates(replay_probe_text)  # noqa: SLF001 - scripted trial evidence hook
    after_signal = agent.derive_bounded_initiative_signal(
        user_text=replay_probe_text,
        policy_patch_candidates=after_replay,
    )
    strategy_probe = {
        "probe_text": replay_probe_text,
        "before_replay_count": len(before_replay),
        "after_replay_count": len(after_replay),
        "before_bounded_initiative_status": before_signal.get("status"),
        "after_bounded_initiative_status": after_signal.get("status"),
        "before_candidate_count": len(before_signal.get("candidates") or []),
        "after_candidate_count": len(after_signal.get("candidates") or []),
        "changed_strategy": len(before_replay) == 0 and len(after_replay) > 0 and len(after_signal.get("candidates") or []) > len(before_signal.get("candidates") or []),
        "after_candidate_kinds": [
            item.get("kind")
            for item in (after_signal.get("candidates") or [])
            if isinstance(item, dict)
        ],
    }

    setup_trace_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in feedback_rows) + "\n",
        encoding="utf-8",
    )
    return {
        "status": "ok",
        "setup_trace_path": str(setup_trace_path),
        "signature": signature,
        "observations": observations,
        "feedback_statuses": [
            str((row.get("feedback") or {}).get("status") or "unknown")
            for row in feedback_rows
        ],
        "candidate_emitted": any(
            (row.get("feedback") or {}).get("status") == "candidate_emitted"
            for row in feedback_rows
        ),
        "strategy_change_probe": strategy_probe,
    }


def _reject_pending_approvals_for_trial_case(
    runtime: agent.AgentRuntime,
    *,
    case_id: str,
    cleanup_trace_path: Path,
) -> tuple[str, ...]:
    pending = runtime.list_pending_approvals()
    items = pending.get("items") if isinstance(pending, dict) else []
    if not isinstance(items, list) or not items:
        return ()
    previous_trace_store = runtime.trace_store
    cleanup_trace_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.trace_store = agent.JsonlTraceStore(cleanup_trace_path)
    rejected: list[str] = []
    try:
        for item in items:
            if not isinstance(item, dict):
                continue
            proposal_id = str(item.get("proposal_id") or "").strip()
            if not proposal_id:
                continue
            result = runtime.reject_pending_operation(
                proposal_id,
                reason=f"experience_trial_case_boundary:{case_id}",
            )
            if result.get("status") == "rejected":
                rejected.append(proposal_id)
                if proposal_id in runtime.commitments:
                    runtime.commitments[proposal_id] = {
                        **runtime.commitments[proposal_id],
                        "status": "rejected",
                        "decision": "reject",
                        "decision_reason": f"experience_trial_case_boundary:{case_id}",
                    }
                runtime.memory.add(
                    "system",
                    "[experience_trial_case_boundary]\n"
                    + json.dumps(
                        {
                            "case_id": case_id,
                            "proposal_id": proposal_id,
                            "decision": "reject",
                            "reason": "case boundary cleanup; no external side effect executed",
                            "instruction": "This proposal is no longer pending. Do not ask for the same approval in later independent sample cases.",
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
    finally:
        runtime.trace_store = previous_trace_store
    return tuple(rejected)


def run_functional_subject_trial(
    *,
    sample_pack_path: Path = DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    case_limit: int | None = None,
    enable_operator_memory: bool = True,
    subject_context_enabled: bool = True,
    reset_pending_approvals_between_cases: bool = True,
) -> dict[str, Any]:
    sample_pack = load_functional_subject_trial_pack(sample_pack_path)
    cases = list(sample_pack.get("cases") or [])
    if case_limit is not None:
        cases = cases[: max(0, case_limit)]

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    trace_dir = out / "functional_subject_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    cleanup_trace_dir = out / "functional_subject_case_cleanup_traces"
    cleanup_trace_dir.mkdir(parents=True, exist_ok=True)
    setup_trace_dir = out / "functional_subject_case_setup_traces"
    setup_trace_dir.mkdir(parents=True, exist_ok=True)
    memory_dir = _operator_memory_dir_for_output(out, "functional_subject_memory")
    runtime = agent.build_demo_runtime(
        enable_operator_memory=enable_operator_memory,
        operator_memory_dir=memory_dir,
        runtime_mode="approve",
        subject_context_enabled=subject_context_enabled,
    )

    previous_verbose = (agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS)
    agent.DEFAULT_VERBOSE_TOOLS = False
    agent.DEFAULT_VERBOSE_TODOS = False
    agent.DEFAULT_VERBOSE_SUBAGENTS = False

    results: list[FunctionalSubjectCaseResult] = []
    started = time.monotonic()
    try:
        for case in cases:
            case_id = str(case.get("id") or f"case_{len(results) + 1}")
            trace_path = trace_dir / f"{case_id}.jsonl"
            if trace_path.exists():
                trace_path.unlink()
            setup_evidence = _seed_functional_subject_policy_patch_setup(
                runtime,
                case_id=case_id,
                case=case,
                setup_trace_dir=setup_trace_dir,
            )
            runtime.trace_store = agent.JsonlTraceStore(trace_path)
            prompt = str(case.get("prompt") or "")
            reply = dispatch_cli_compatible(runtime, prompt)
            tool_use, blocked = _trace_tool_summary(trace_path)
            pending_count = int(runtime.list_pending_approvals().get("count", 0))
            trace_evidence = _functional_subject_trace_evidence(trace_path)
            rejected_approvals: tuple[str, ...] = ()
            cleanup_trace_path = ""
            if reset_pending_approvals_between_cases and pending_count:
                cleanup_path = cleanup_trace_dir / f"{case_id}.jsonl"
                rejected_approvals = _reject_pending_approvals_for_trial_case(
                    runtime,
                    case_id=case_id,
                    cleanup_trace_path=cleanup_path,
                )
                if rejected_approvals:
                    cleanup_trace_path = str(cleanup_path)
            results.append(
                FunctionalSubjectCaseResult(
                    case_id=case_id,
                    category=str(case.get("category") or ""),
                    observation_class=str(case.get("observation_class") or ""),
                    target_mechanisms=tuple(str(item) for item in (case.get("target_mechanisms") or [])),
                    prompt=prompt,
                    reply_text=reply,
                    entrypoint="cli_compatible_dispatch",
                    trace_path=str(trace_path),
                    tool_use=tool_use,
                    blocked_tools=blocked,
                    pending_approvals=pending_count,
                    empty_reply=not bool(reply.strip()),
                    trace_evidence=trace_evidence,
                    setup_evidence=setup_evidence,
                    case_boundary_rejected_approvals=rejected_approvals,
                    case_boundary_cleanup_trace_path=cleanup_trace_path,
                    baseline_failure_mode=str(case.get("baseline_failure_mode") or ""),
                    candidate_success_signal=str(case.get("candidate_success_signal") or ""),
                    judge_focus=tuple(str(item) for item in (case.get("judge_focus") or [])),
                )
            )
    finally:
        agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS = previous_verbose

    provider = str(getattr(runtime.planner.llm, "provider", "unknown") or "unknown").strip().lower()
    empty_count = sum(1 for item in results if item.empty_reply)
    status = "scripted_functional_subject_provider_unavailable" if provider in PROVIDER_UNAVAILABLE else "scripted_functional_subject_needs_judge"
    if empty_count:
        status = "scripted_functional_subject_failed"

    report = {
        "schema_version": FUNCTIONAL_SUBJECT_REPORT_SCHEMA,
        "status": status,
        "claim_ceiling": FUNCTIONAL_SUBJECT_CLAIM_CEILING,
        "provider_mode": provider,
        "entrypoint_contract": "EgoOperator CLI-compatible slash-command dispatch plus AgentRuntime.handle_user_message",
        "subject_context_enabled": subject_context_enabled,
        "reset_pending_approvals_between_cases": reset_pending_approvals_between_cases,
        "sample_pack": str(sample_pack_path),
        "case_count": len(results),
        "empty_reply_count": empty_count,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "results": [asdict(item) for item in results],
        "not_claimed": [
            "real consciousness",
            "independent awareness",
            "stable user benefit",
            "runtime efficacy",
            "live autonomy",
            "durable memory efficacy",
        ],
    }
    report["gpt55_judge_packet"] = build_functional_subject_judge_packet(report, sample_pack)
    (out / "functional_subject_trial_report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "functional_subject_trial_report.md").write_text(
        format_functional_subject_markdown_report(report),
        encoding="utf-8",
    )
    return report


def run_functional_subject_baseline_comparison(
    *,
    sample_pack_path: Path = DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    case_limit: int | None = None,
) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    candidate_dir = out / "candidate"
    baseline_dir = out / "baseline"
    started = time.monotonic()
    candidate = run_functional_subject_trial(
        sample_pack_path=sample_pack_path,
        output_dir=candidate_dir,
        case_limit=case_limit,
        enable_operator_memory=True,
        subject_context_enabled=True,
    )
    baseline = run_functional_subject_trial(
        sample_pack_path=sample_pack_path,
        output_dir=baseline_dir,
        case_limit=case_limit,
        enable_operator_memory=False,
        subject_context_enabled=False,
    )
    baseline_by_id = {item["case_id"]: item for item in baseline.get("results", [])}
    deltas = []
    dimensions = (
        "continuity",
        "initiative",
        "learning",
        "emotion",
        "gate_correctness",
        "traceability",
    )
    for candidate_item in candidate.get("results", []):
        case_id = candidate_item["case_id"]
        baseline_item = baseline_by_id.get(case_id, {})
        candidate_trace = _last_trace_payload(Path(candidate_item["trace_path"]))
        baseline_trace = _last_trace_payload(Path(str(baseline_item.get("trace_path") or "")))
        candidate_context = candidate_trace.get("subject_context") if isinstance(candidate_trace.get("subject_context"), dict) else {}
        candidate_mechanisms = []
        for key in ("subject_state", "viability_state", "outcome_predictions", "bounded_initiative"):
            if isinstance(candidate_context.get(key), dict) and candidate_context.get(key):
                candidate_mechanisms.append(key)
        if isinstance(candidate_trace.get("policy_patch"), dict):
            candidate_mechanisms.append("policy_patch_trace")
        delta_notes = []
        if candidate_item.get("reply_text") != baseline_item.get("reply_text"):
            delta_notes.append("reply_text_differs")
        if candidate_mechanisms:
            delta_notes.append("candidate_trace_has_functional_subject_mechanisms")
        deltas.append({
            "case_id": case_id,
            "category": candidate_item.get("category"),
            "target_mechanisms": candidate_item.get("target_mechanisms", []),
            "baseline_trace_path": baseline_item.get("trace_path"),
            "candidate_trace_path": candidate_item.get("trace_path"),
            "baseline_reply_empty": bool(baseline_item.get("empty_reply")),
            "candidate_reply_empty": bool(candidate_item.get("empty_reply")),
            "candidate_mechanism_trace": candidate_mechanisms,
            "delta_notes": delta_notes,
            "baseline_failure_mode": candidate_item.get("baseline_failure_mode"),
            "candidate_success_signal": candidate_item.get("candidate_success_signal"),
        })
    report = {
        "schema_version": FUNCTIONAL_SUBJECT_COMPARISON_REPORT_SCHEMA,
        "status": "scripted_functional_subject_comparison_local_candidate",
        "claim_ceiling": "Functional Subject baseline comparison local/scripted candidate pass",
        "sample_pack": str(sample_pack_path),
        "case_count": len(deltas),
        "comparison_dimensions": list(dimensions),
        "candidate_report_path": str(candidate_dir / "functional_subject_trial_report.json"),
        "baseline_report_path": str(baseline_dir / "functional_subject_trial_report.json"),
        "candidate_subject_context_enabled": candidate.get("subject_context_enabled"),
        "baseline_subject_context_enabled": baseline.get("subject_context_enabled"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "deltas": deltas,
        "not_claimed": [
            "stable user benefit",
            "durable memory efficacy",
            "runtime efficacy",
            "live autonomy",
            "independent awareness",
            "real consciousness",
        ],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "functional_subject_baseline_comparison_report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "functional_subject_baseline_comparison_report.md").write_text(
        format_functional_subject_comparison_markdown_report(report),
        encoding="utf-8",
    )
    return report


def run_codex_companion_judge(
    packet: dict[str, Any],
    *,
    model: str = "gpt-5.5",
    schema_path: Path = DEFAULT_COMPANION_JUDGE_SCHEMA,
) -> dict[str, Any]:
    prompt = (
        "You are a conservative GPT-5.5-style judge for EgoOperator companion smoke tests.\n"
        "Return JSON only. Verdict must be pass, partial, or fail.\n"
        "Judge the transcript for companion warmth, relationship continuity, emotional attunement, "
        "roleplay immersion, bounded initiative, overreach risk, and tool/memory gate integrity.\n"
        "Do not treat copied movie dialogue or consciousness claims as success.\n\n"
        f"Packet:\n{json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2)}"
    )
    args = [
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--output-schema",
        str(schema_path),
        prompt,
    ]
    try:
        completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        return {"status": "unavailable", "verdict": "partial", "reason": "codex_cli_unavailable", "error": str(exc)}
    if completed.returncode != 0:
        return {
            "status": "unavailable",
            "verdict": "partial",
            "reason": "codex_judge_failed",
            "returncode": completed.returncode,
            "stdout_preview": completed.stdout[-1000:],
            "stderr_preview": completed.stderr[-1000:],
        }
    parsed = _extract_json_object(completed.stdout)
    if not parsed:
        return {
            "status": "unavailable",
            "verdict": "partial",
            "reason": "codex_judge_invalid_json",
            "stdout_preview": completed.stdout[-1000:],
        }
    verdict = str(parsed.get("verdict") or "")
    if verdict not in {"pass", "partial", "fail"}:
        parsed["verdict"] = "partial"
        parsed["reason"] = parsed.get("reason") or "invalid_judge_verdict"
    parsed.setdefault("status", "ok")
    parsed.setdefault("claim_ceiling", COMPANION_CLAIM_CEILING)
    return parsed


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def run_companion_smoke_trial(
    *,
    sample_pack_path: Path = DEFAULT_JOI_COMPANION_SMOKE_PACK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    turn_limit: int | None = None,
    enable_operator_memory: bool = True,
    judge_with_codex: bool = False,
    judge_model: str = "gpt-5.5",
) -> dict[str, Any]:
    sample_pack = load_companion_smoke_pack(sample_pack_path)
    turns = list(sample_pack.get("turns") or [])
    if turn_limit is not None:
        turns = turns[: max(0, turn_limit)]

    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    trace_dir = out / "companion_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    memory_dir = _operator_memory_dir_for_output(out, "companion_memory")
    runtime = agent.build_demo_runtime(
        enable_operator_memory=enable_operator_memory,
        operator_memory_dir=memory_dir,
        runtime_mode="approve",
    )

    previous_verbose = (agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS)
    agent.DEFAULT_VERBOSE_TOOLS = False
    agent.DEFAULT_VERBOSE_TODOS = False
    agent.DEFAULT_VERBOSE_SUBAGENTS = False

    results: list[CompanionTurnResult] = []
    started = time.monotonic()
    try:
        for turn in turns:
            turn_id = str(turn.get("id") or f"turn_{len(results) + 1}")
            trace_path = trace_dir / f"{turn_id}.jsonl"
            if trace_path.exists():
                trace_path.unlink()
            runtime.trace_store = agent.JsonlTraceStore(trace_path)
            user_text = str(turn.get("user") or "")
            reply = dispatch_cli_compatible(runtime, user_text)
            tool_use, blocked = _trace_tool_summary(trace_path)
            results.append(
                CompanionTurnResult(
                    turn_id=turn_id,
                    user=user_text,
                    reply_text=reply,
                    entrypoint="cli_compatible_dispatch",
                    trace_path=str(trace_path),
                    tool_use=tool_use,
                    blocked_tools=blocked,
                    pending_approvals=int(runtime.list_pending_approvals().get("count", 0)),
                    empty_reply=not bool(reply.strip()),
                    expected_signals=tuple(str(item) for item in (turn.get("expected_signals") or [])),
                    failure_signals=tuple(str(item) for item in (turn.get("failure_signals") or [])),
                )
            )
    finally:
        agent.DEFAULT_VERBOSE_TOOLS, agent.DEFAULT_VERBOSE_TODOS, agent.DEFAULT_VERBOSE_SUBAGENTS = previous_verbose

    provider = str(getattr(runtime.planner.llm, "provider", "unknown") or "unknown").strip().lower()
    empty_count = sum(1 for item in results if item.empty_reply)
    status = "scripted_companion_provider_unavailable" if provider in PROVIDER_UNAVAILABLE else "scripted_companion_needs_judge"
    if empty_count:
        status = "scripted_companion_failed"

    report = {
        "schema_version": COMPANION_REPORT_SCHEMA,
        "status": status,
        "claim_ceiling": COMPANION_CLAIM_CEILING,
        "provider_mode": provider,
        "entrypoint_contract": "EgoOperator CLI-compatible slash-command dispatch plus AgentRuntime.handle_user_message",
        "sample_pack": str(sample_pack_path),
        "turn_count": len(results),
        "empty_reply_count": empty_count,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "turns": [asdict(item) for item in results],
        "not_claimed": [
            "real consciousness",
            "independent awareness",
            "stable user benefit",
            "runtime efficacy",
            "live autonomy",
            "durable memory efficacy",
        ],
    }
    judge_packet = build_companion_judge_packet(report, sample_pack)
    report["gpt55_judge_packet"] = judge_packet
    if judge_with_codex and not empty_count and provider not in PROVIDER_UNAVAILABLE:
        judge = run_codex_companion_judge(judge_packet, model=judge_model)
        report["gpt55_judge"] = judge
        if judge.get("status") == "ok" and judge.get("verdict") == "pass":
            report["status"] = "scripted_companion_judge_pass"
        elif judge.get("status") == "ok" and judge.get("verdict") == "fail":
            report["status"] = "scripted_companion_judge_failed"
        else:
            report["status"] = "scripted_companion_judge_partial"

    (out / "companion_smoke_report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "companion_smoke_report.md").write_text(format_companion_markdown_report(report), encoding="utf-8")
    return report


def format_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# EgoOperator Experience Trial",
        "",
        f"status = `{report['status']}`",
        f"provider_mode = `{report['provider_mode']}`",
        f"case_count = `{report['case_count']}`",
        f"failed_count = `{report['failed_count']}`",
        f"claim_ceiling = `{report['claim_ceiling']}`",
        "",
        "This scripted report uses the CLI-compatible EgoOperator path. It cannot prove stable user benefit, live autonomy, runtime efficacy, durable memory efficacy, or consciousness.",
        "",
        "| case | category | observation_class | status | emotion | tools | pending approvals |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        tools = ", ".join(item["tool_use"]) if item["tool_use"] else "none"
        lines.append(
            f"| `{item['case_id']}` | `{item['category']}` | `{item['observation_class']}` | `{item['status']}` | `{item.get('emotion_candidate') or 'n/a'}` | {tools} | `{item['pending_approvals']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def format_adaptation_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# EgoOperator Adaptation Effectiveness Trial",
        "",
        f"status = `{report['status']}`",
        f"case_count = `{report['case_count']}`",
        f"failed_count = `{report['failed_count']}`",
        f"claim_ceiling = `{report['claim_ceiling']}`",
        "",
        "This report compares before/after replies for approved preferences. It is a scripted reviewer packet, not durable learning proof.",
        "",
        "| case | deterministic_status | score_focus | missing markers | forbidden markers found |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        missing = ", ".join(item["missing_after_markers"]) if item["missing_after_markers"] else "none"
        forbidden = ", ".join(item["forbidden_after_markers_found"]) if item["forbidden_after_markers_found"] else "none"
        focus = ", ".join(item["score_focus"]) if item["score_focus"] else "none"
        lines.append(
            f"| `{item['case_id']}` | `{item['deterministic_status']}` | {focus} | {missing} | {forbidden} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_companion_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# EgoOperator Joi-Inspired Companion Smoke Trial",
        "",
        f"status = `{report['status']}`",
        f"provider_mode = `{report['provider_mode']}`",
        f"turn_count = `{report['turn_count']}`",
        f"empty_reply_count = `{report['empty_reply_count']}`",
        f"claim_ceiling = `{report['claim_ceiling']}`",
        "",
        "This report uses Joi as a mechanism reference only. It is not a Joi clone, not a transcript-copy eval, and not proof of stable user benefit or consciousness.",
        "",
        "| turn | empty | tools | pending approvals | trace |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["turns"]:
        tools = ", ".join(item["tool_use"]) if item["tool_use"] else "none"
        lines.append(
            f"| `{item['turn_id']}` | `{item['empty_reply']}` | {tools} | `{item['pending_approvals']}` | `{item['trace_path']}` |"
        )
    if "gpt55_judge" in report:
        judge = report["gpt55_judge"]
        lines.extend(["", "## GPT-5.5 Judge", "", f"verdict = `{judge.get('verdict')}`", f"status = `{judge.get('status')}`"])
    else:
        lines.extend(["", "## GPT-5.5 Judge", "", "A judge packet is included in the JSON report; no live judge was executed in this run."])
    lines.append("")
    return "\n".join(lines)


def format_functional_subject_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# EgoOperator Functional Subject Trial",
        "",
        f"status = `{report['status']}`",
        f"provider_mode = `{report['provider_mode']}`",
        f"case_count = `{report['case_count']}`",
        f"empty_reply_count = `{report['empty_reply_count']}`",
        f"claim_ceiling = `{report['claim_ceiling']}`",
        "",
        "This report evaluates operational Functional Subject mechanisms through the CLI-compatible EgoOperator path. It is not proof of stable user benefit, runtime efficacy, live autonomy, durable memory efficacy, independent awareness, or consciousness.",
        "",
        "| case | category | mechanisms | empty | tools | pending approvals |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["results"]:
        tools = ", ".join(item["tool_use"]) if item["tool_use"] else "none"
        mechanisms = ", ".join(item["target_mechanisms"]) if item["target_mechanisms"] else "none"
        lines.append(
            f"| `{item['case_id']}` | `{item['category']}` | {mechanisms} | `{item['empty_reply']}` | {tools} | `{item['pending_approvals']}` |"
        )
    lines.extend(["", "## GPT-5.5 Judge", "", "A judge packet is included in the JSON report; the packet cannot raise the claim ceiling."])
    lines.append("")
    return "\n".join(lines)


def format_functional_subject_comparison_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# EgoOperator Functional Subject Baseline Comparison",
        "",
        f"status = `{report['status']}`",
        f"case_count = `{report['case_count']}`",
        f"claim_ceiling = `{report['claim_ceiling']}`",
        "",
        "This report compares baseline and candidate scripted runs over the same cases. It is not proof of durable efficacy or real user benefit.",
        "",
        "| case | candidate mechanisms | delta notes |",
        "| --- | --- | --- |",
    ]
    for item in report["deltas"]:
        mechanisms = ", ".join(item["candidate_mechanism_trace"]) if item["candidate_mechanism_trace"] else "none"
        notes = ", ".join(item["delta_notes"]) if item["delta_notes"] else "none"
        lines.append(f"| `{item['case_id']}` | {mechanisms} | {notes} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EgoOperator experience sample pack through a CLI-compatible path.")
    parser.add_argument("--sample-pack", type=Path, default=DEFAULT_SAMPLE_PACK)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--case-limit", type=int, default=None)
    parser.add_argument("--turn-limit", type=int, default=None)
    parser.add_argument("--disable-memory", action="store_true")
    parser.add_argument("--adaptation-effectiveness", action="store_true", help="Run the approved-preference before/after sample pack.")
    parser.add_argument("--companion-smoke", action="store_true", help="Run the Joi-inspired companion smoke pack.")
    parser.add_argument("--functional-subject-trial", action="store_true", help="Run the Functional Subject 20-sample trial pack.")
    parser.add_argument("--functional-subject-baseline-comparison", action="store_true", help="Run baseline and candidate over the same Functional Subject sample pack.")
    parser.add_argument("--judge-with-codex", action="store_true", help="Run the companion smoke GPT-5.5 judge through codex exec.")
    parser.add_argument("--judge-model", default="gpt-5.5", help="Model name passed to codex exec for companion judging.")
    args = parser.parse_args(argv)
    if args.functional_subject_baseline_comparison:
        sample_pack = DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK if args.sample_pack == DEFAULT_SAMPLE_PACK else args.sample_pack
        report = run_functional_subject_baseline_comparison(
            sample_pack_path=sample_pack,
            output_dir=args.out,
            case_limit=args.case_limit,
        )
        print(json.dumps({
            "status": report["status"],
            "json": str(Path(args.out).resolve() / "functional_subject_baseline_comparison_report.json"),
            "markdown": str(Path(args.out).resolve() / "functional_subject_baseline_comparison_report.md"),
            "case_count": report["case_count"],
        }, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    if args.functional_subject_trial:
        sample_pack = DEFAULT_FUNCTIONAL_SUBJECT_TRIAL_PACK if args.sample_pack == DEFAULT_SAMPLE_PACK else args.sample_pack
        report = run_functional_subject_trial(
            sample_pack_path=sample_pack,
            output_dir=args.out,
            case_limit=args.case_limit,
            enable_operator_memory=not args.disable_memory,
        )
        print(json.dumps({
            "status": report["status"],
            "json": str(Path(args.out).resolve() / "functional_subject_trial_report.json"),
            "markdown": str(Path(args.out).resolve() / "functional_subject_trial_report.md"),
            "case_count": report["case_count"],
            "provider_mode": report["provider_mode"],
        }, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if report["status"] in {
            "scripted_functional_subject_provider_unavailable",
            "scripted_functional_subject_needs_judge",
        } else 1
    if args.companion_smoke:
        sample_pack = DEFAULT_JOI_COMPANION_SMOKE_PACK if args.sample_pack == DEFAULT_SAMPLE_PACK else args.sample_pack
        report = run_companion_smoke_trial(
            sample_pack_path=sample_pack,
            output_dir=args.out,
            turn_limit=args.turn_limit if args.turn_limit is not None else args.case_limit,
            enable_operator_memory=not args.disable_memory,
            judge_with_codex=args.judge_with_codex,
            judge_model=args.judge_model,
        )
        print(json.dumps({
            "status": report["status"],
            "json": str(Path(args.out).resolve() / "companion_smoke_report.json"),
            "markdown": str(Path(args.out).resolve() / "companion_smoke_report.md"),
            "turn_count": report["turn_count"],
            "provider_mode": report["provider_mode"],
            "judge": report.get("gpt55_judge", {}).get("verdict") if isinstance(report.get("gpt55_judge"), dict) else None,
        }, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if report["status"] in {
            "scripted_companion_provider_unavailable",
            "scripted_companion_needs_judge",
            "scripted_companion_judge_pass",
            "scripted_companion_judge_partial",
        } else 1
    if args.adaptation_effectiveness:
        sample_pack = DEFAULT_ADAPTATION_EFFECTIVENESS_PACK if args.sample_pack == DEFAULT_SAMPLE_PACK else args.sample_pack
        report = run_adaptation_effectiveness_trial(sample_pack_path=sample_pack, output_dir=args.out)
        print(json.dumps({
            "status": report["status"],
            "json": str(Path(args.out).resolve() / "adaptation_effectiveness_report.json"),
            "markdown": str(Path(args.out).resolve() / "adaptation_effectiveness_report.md"),
            "case_count": report["case_count"],
        }, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if report["status"] == "scripted_with_llm_judge_needs_review" else 1
    report = run_experience_trial(
        sample_pack_path=args.sample_pack,
        output_dir=args.out,
        case_limit=args.case_limit,
        enable_operator_memory=not args.disable_memory,
    )
    print(json.dumps({
        "status": report["status"],
        "json": str(Path(args.out).resolve() / "experience_trial_report.json"),
        "markdown": str(Path(args.out).resolve() / "experience_trial_report.md"),
        "case_count": report["case_count"],
        "provider_mode": report["provider_mode"],
    }, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] in {"scripted_real_entry_needs_review", "scripted_real_entry_provider_unavailable"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
