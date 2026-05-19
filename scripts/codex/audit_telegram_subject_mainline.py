#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
REAL_TELEGRAM_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
LEGACY_ROOT = ROOT / "legacy" / "ego-pre-handmade-mainline"

RUNS_PATH = DASHBOARD_ROOT / "runs.jsonl"
GROWTH_PATH = DASHBOARD_ROOT / "growth_signals.jsonl"
AGENCY_PATH = DASHBOARD_ROOT / "agency_runs.jsonl"
REPORT_MD_PATH = DASHBOARD_ROOT / "SUBJECT_MAINLINE_AUDIT_CURRENT.md"
REPORT_JSON_PATH = DASHBOARD_ROOT / "SUBJECT_MAINLINE_AUDIT_CURRENT.json"

def _repo_or_legacy_path(*parts: str) -> Path:
    path = ROOT.joinpath(*parts)
    if path.exists():
        return path
    return LEGACY_ROOT.joinpath(*parts)


README_PATH = ROOT / "README.md"
INDEX_BUILDER_PATH = _repo_or_legacy_path("EgoCore", "app", "dashboard", "index_builder.py")
RUNTIME_BRIDGE_PATH = _repo_or_legacy_path("EgoCore", "app", "telegram_runtime_bridge.py")
BOT_PATH = _repo_or_legacy_path("EgoCore", "app", "telegram_bot.py")
HOOKS_PATH = _repo_or_legacy_path("EgoCore", "app", "openemotion_hooks", "native_hooks.py")

EXPECTED_BASELINE = {
    "runs": 1097,
    "host_only": 484,
    "oe_available": 580,
    "control_plane_expected": 206,
    "policy_driven_host_interception": 228,
    "unexpected_subject_miss": 50,
    "telegram_subject_rows": 104,
    "telegram_subject_revision_gt_0": 0,
    "telegram_subject_non_ask_modes": 0,
}

CONTROL_PLANE_STATUSES = {
    "profile_rule_registered",
    "command_result",
    "profile_rule_unsupported",
    "return_runtime_status",
}
POLICY_STATUSES = {"profile_rule_enforced"}
UNEXPECTED_STATUSES = {"pre_runtime", "delivered_without_explicit_plan", "chat", "evidence_followup"}

PRIORITY_UNEXPECTED_TEXTS = ("继续", "在吗", "什么意思")
PRIORITY_UNEXPECTED_SUBSTRINGS = ("创建一个参照", "html页面")
FIELD_CANDIDATES = [
    "self_model_delta",
    "response_tendency",
    "policy_hint",
    "reflection_note",
    "memory_update",
    "relationship_update",
    "identity_state_delta",
    "appraisal_state_delta",
    "endogenous_drive_delta",
    "reflective_self_delta",
    "developmental_self_delta",
    "social_self_delta",
    "embodied_self_delta",
    "self_integration_delta",
    "initiative_self_delta",
    "initiative_realization_delta",
    "revision_proposal_candidates",
    "developmental_proposal_candidates",
    "relation_update_candidates",
    "consequence_update_candidates",
    "integrated_tendency_proposal",
    "initiative_proposal_candidates",
    "controlled_delivery_candidate",
]


@dataclass
class SampleContext:
    sample_id: str
    response_plan_status: str | None
    host_only: bool
    oe_available: bool
    timestamp: str | None
    text: str | None
    entrypoint: str | None = None
    source_kind: str | None = None
    category: str | None = None
    stage1_bucket: str | None = None
    stage1_reason: str | None = None


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in _read_text(path).splitlines() if line.strip()]


def _sample_dir(sample_id: str) -> Path:
    return REAL_TELEGRAM_ROOT / sample_id


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _load_response_plan(sample_id: str) -> dict[str, Any]:
    return _load_optional_json(_sample_dir(sample_id) / "response_plan.json") or {}


def _raw_text(sample_id: str) -> str | None:
    payload = _load_optional_json(_sample_dir(sample_id) / "raw_update.json") or {}
    message = payload.get("message") or {}
    text = message.get("text")
    return text if isinstance(text, str) else None


def _infer_entrypoint_from_row(row: dict[str, Any]) -> str:
    explicit = str(row.get("entrypoint") or "").strip()
    if explicit:
        return explicit

    source_kind = str(row.get("source_kind") or "").strip().lower()
    if source_kind.startswith("dashboard"):
        return "dashboard_chat"
    if source_kind.startswith("telegram"):
        return "telegram"

    for key in ("session_id", "thread_id"):
        value = str(row.get(key) or "").strip().lower()
        if value.startswith("dashboard:"):
            return "dashboard_chat"
        if value.startswith("telegram:"):
            return "telegram"

    source_type = str(row.get("source_type") or "").strip().lower()
    if source_type == "real_channel":
        return "other_real_entry"
    return "unknown"


def _host_only_category(status: str | None) -> str:
    if status in CONTROL_PLANE_STATUSES:
        return "control_plane_expected"
    if status in POLICY_STATUSES:
        return "policy_driven_host_interception"
    if status in UNEXPECTED_STATUSES:
        return "unexpected_subject_miss"
    return "unexpected_subject_miss"


def _is_profile_rule_registration(text: str | None) -> bool:
    if not text:
        return False
    stripped = text.strip()
    return (("以后凡是" in stripped) or stripped.startswith("以后")) and ("默认走" in stripped)


def _is_ordinary_chat_turn(text: str | None) -> bool:
    if not text or not text.strip():
        return False
    if text.lstrip().startswith("/"):
        return False
    if _is_profile_rule_registration(text):
        return False
    return True


PATH_LIKE_RE = re.compile(
    r"([A-Za-z]:\\|/mnt/|/tmp/|/Users/|/home/|\\Users\\|[A-Za-z0-9_.-]+\.(html|md|py|txt|json|yaml|yml|log))",
    re.IGNORECASE,
)
MUTATION_HINTS = (
    "删除",
    "重写",
    "改",
    "修改",
    "创建",
    "写入",
    "替换",
    "追加",
    "rewrite",
    "delete",
    "remove",
    "edit",
    "modify",
    "create",
    "write",
    "replace",
    "append",
)


def _looks_like_path_targeted_mutation(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    if not any((token in text) or (token in lowered) for token in MUTATION_HINTS):
        return False
    return bool(PATH_LIKE_RE.search(text))


def _classify_stage1_host_only_sample(sample: SampleContext) -> tuple[str, str]:
    response_plan = _load_response_plan(sample.sample_id)
    metadata = response_plan.get("metadata") or {}
    response_plan_status = response_plan.get("status") or sample.response_plan_status
    intercept_kind = metadata.get("pre_runtime_intercept_kind")
    rule_enforcement = response_plan.get("rule_enforcement") or {}
    rule_kind = rule_enforcement.get("kind")

    if response_plan_status in CONTROL_PLANE_STATUSES or intercept_kind == "control_plane":
        return ("isolated_host_only", "control_plane")
    if response_plan_status in POLICY_STATUSES:
        return ("isolated_host_only", "policy_enforcement")
    if intercept_kind in {"policy_registration", "policy_enforcement"}:
        return ("isolated_host_only", str(intercept_kind))
    if rule_kind in {"profile_rule_registered", "profile_rule_unsupported", "reply_only_once", "read_only_preflight"}:
        return ("isolated_host_only", str(rule_kind))
    if _is_profile_rule_registration(sample.text):
        return ("isolated_host_only", "legacy_profile_rule_registration")
    if _looks_like_path_targeted_mutation(sample.text):
        if response_plan_status in {"pre_runtime", "waiting_input", "force_waiting_input"}:
            return ("isolated_host_only", "mutation_targeted_preflight")
        return ("isolated_host_only", "path_targeted_request")
    return ("mainline_candidate", "ordinary_chat_mainline_candidate")


def _git_commit_short() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _find_line(path: Path, needle: str) -> str | None:
    for idx, line in enumerate(_read_text(path).splitlines(), start=1):
        if needle in line:
            return f"{_display_path(path)}:{idx}"
    return None


def _collect_present_fields(sample_id: str) -> dict[str, list[str]]:
    sample_root = _sample_dir(sample_id)
    ledger = _load_optional_json(sample_root / "ledger.json") or {}
    result_payload = (_load_optional_json(sample_root / "openemotion_result.json") or {})
    trace_payload = (_load_optional_json(sample_root / "openemotion_trace.json") or {})
    ledger_result = ((ledger.get("openemotion") or {}).get("result") or {})
    ledger_trace = ((ledger.get("openemotion") or {}).get("trace_payload") or {})

    result_fields = [field for field in FIELD_CANDIDATES if field in result_payload or field in ledger_result]
    trace_fields = [field for field in FIELD_CANDIDATES if field in trace_payload or field in ledger_trace]

    return {
        "result_fields": result_fields,
        "trace_fields": trace_fields,
        "has_ledger_result": bool(ledger_result),
        "has_ledger_trace_payload": bool(ledger_trace),
    }


def _subject_trace_writeback_proved(sample_id: str) -> bool:
    sample_root = _sample_dir(sample_id)
    ledger = _load_optional_json(sample_root / "ledger.json") or {}
    openemotion = ledger.get("openemotion") or {}
    return bool(openemotion.get("result") or openemotion.get("trace_payload"))


def _subject_ingress_proved(sample_id: str, oe_available: bool) -> bool:
    if not oe_available:
        return False
    sample_root = _sample_dir(sample_id)
    return (sample_root / "openemotion_result.json").exists() or (sample_root / "openemotion_trace.json").exists()


def _pick_representatives(rows: list[SampleContext], *, limit: int = 3) -> list[SampleContext]:
    prioritized: list[SampleContext] = []
    remaining: list[SampleContext] = []
    for row in rows:
        text = (row.text or "").strip()
        if text in PRIORITY_UNEXPECTED_TEXTS or any(token in text for token in PRIORITY_UNEXPECTED_SUBSTRINGS):
            prioritized.append(row)
        else:
            remaining.append(row)
    deduped: list[SampleContext] = []
    seen: set[str] = set()
    for row in prioritized + remaining:
        if row.sample_id in seen:
            continue
        deduped.append(row)
        seen.add(row.sample_id)
        if len(deduped) >= limit:
            break
    return deduped


def _build_sample_context(row: dict[str, Any]) -> SampleContext:
    return SampleContext(
        sample_id=row.get("sample_id") or "",
        response_plan_status=row.get("response_plan_status"),
        host_only=bool(row.get("host_only")),
        oe_available=bool(row.get("oe_available")),
        timestamp=row.get("timestamp"),
        text=_raw_text(row.get("sample_id") or ""),
        entrypoint=_infer_entrypoint_from_row(row),
        source_kind=row.get("source_kind"),
        category=None,
    )


def _sample_entry(row: SampleContext) -> dict[str, Any]:
    return {
        "sample_id": row.sample_id,
        "timestamp": row.timestamp,
        "entrypoint": row.entrypoint,
        "source_kind": row.source_kind,
        "response_plan_status": row.response_plan_status,
        "category": row.category,
        "stage1_bucket": row.stage1_bucket,
        "stage1_reason": row.stage1_reason,
        "text": row.text,
        "artifacts": {
            "ledger": _display_path(_sample_dir(row.sample_id) / "ledger.json"),
            "raw_update": _display_path(_sample_dir(row.sample_id) / "raw_update.json"),
            "openemotion_result": _display_path(_sample_dir(row.sample_id) / "openemotion_result.json"),
            "openemotion_trace": _display_path(_sample_dir(row.sample_id) / "openemotion_trace.json"),
            "response_plan": _display_path(_sample_dir(row.sample_id) / "response_plan.json"),
        },
    }


def _tendency_tuple(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    tendency = row.get("response_tendency_summary") or {}
    return (
        row.get("revision_counter"),
        tendency.get("preferred_mode"),
        tendency.get("preferred_tone"),
        tendency.get("suggested_next_step"),
    )


def build_payload() -> dict[str, Any]:
    runs = _load_jsonl(RUNS_PATH)
    growth_rows = _load_jsonl(GROWTH_PATH)
    agency_rows = _load_jsonl(AGENCY_PATH)
    run_entrypoint_counts = Counter(_infer_entrypoint_from_row(row) for row in runs)
    growth_entrypoint_counts = Counter(_infer_entrypoint_from_row(row) for row in growth_rows)
    agency_entrypoint_counts = Counter(_infer_entrypoint_from_row(row) for row in agency_rows)

    host_only_rows: list[SampleContext] = []
    ordinary_host_only_rows: list[SampleContext] = []
    ordinary_chat_unexpected_rows: list[SampleContext] = []
    stage1_isolated_rows: list[SampleContext] = []
    stage1_mainline_candidate_rows: list[SampleContext] = []
    stage1_mainline_candidate_unexpected_rows: list[SampleContext] = []
    control_plane_rows: list[SampleContext] = []
    policy_rows: list[SampleContext] = []

    for row in runs:
        sample = _build_sample_context(row)
        if sample.host_only:
            sample.category = _host_only_category(sample.response_plan_status)
            host_only_rows.append(sample)
            if sample.category == "control_plane_expected":
                control_plane_rows.append(sample)
            elif sample.category == "policy_driven_host_interception":
                policy_rows.append(sample)
            if _is_ordinary_chat_turn(sample.text):
                sample.stage1_bucket, sample.stage1_reason = _classify_stage1_host_only_sample(sample)
                ordinary_host_only_rows.append(sample)
                if sample.stage1_bucket == "isolated_host_only":
                    stage1_isolated_rows.append(sample)
                else:
                    stage1_mainline_candidate_rows.append(sample)
                if sample.category == "unexpected_subject_miss":
                    ordinary_chat_unexpected_rows.append(sample)
                    if sample.stage1_bucket == "mainline_candidate":
                        stage1_mainline_candidate_unexpected_rows.append(sample)

    host_only_counts = Counter(sample.category for sample in host_only_rows)
    ordinary_host_only_counts = Counter(sample.category for sample in ordinary_host_only_rows)
    host_only_entrypoint_counts = Counter(sample.entrypoint for sample in host_only_rows)
    ordinary_host_only_entrypoint_counts = Counter(sample.entrypoint for sample in ordinary_host_only_rows)

    telegram_subject_rows = [
        row for row in growth_rows if _infer_entrypoint_from_row(row) == "telegram"
    ]
    telegram_subject_revision_gt_0 = sum(1 for row in telegram_subject_rows if (row.get("revision_counter") or 0) > 0)
    telegram_subject_non_ask_modes = sum(
        1 for row in telegram_subject_rows if (row.get("response_tendency_summary") or {}).get("preferred_mode") != "ask"
    )
    telegram_subject_mode_counts = Counter(
        (row.get("response_tendency_summary") or {}).get("preferred_mode") for row in telegram_subject_rows
    )
    telegram_subject_tone_counts = Counter(
        (row.get("response_tendency_summary") or {}).get("preferred_tone") for row in telegram_subject_rows
    )
    telegram_subject_next_step_counts = Counter(
        (row.get("response_tendency_summary") or {}).get("suggested_next_step") for row in telegram_subject_rows
    )

    session_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in telegram_subject_rows:
        session_groups[str(row.get("session_id"))].append(row)
    sessions_with_multiple = {
        session_id: sorted(rows, key=lambda item: item.get("timestamp") or "")
        for session_id, rows in session_groups.items()
        if len(rows) >= 2
    }
    weak_shift_sessions = []
    strong_shift_sessions = []
    unchanged_sessions = []
    for session_id, rows in sessions_with_multiple.items():
        tuples = [_tendency_tuple(row) for row in rows]
        unique = []
        for item in tuples:
            if item not in unique:
                unique.append(item)
        summary = {
            "session_id": session_id,
            "sample_ids": [row.get("sample_id") for row in rows],
            "tendency_tuples": [
                {
                    "revision_counter": item[0],
                    "preferred_mode": item[1],
                    "preferred_tone": item[2],
                    "suggested_next_step": item[3],
                }
                for item in unique
            ],
        }
        if len(unique) > 1:
            if any((item[0] or 0) > 0 or item[1] != "ask" for item in unique):
                strong_shift_sessions.append(summary)
            else:
                weak_shift_sessions.append(summary)
        else:
            unchanged_sessions.append(summary)

    ordinary_subject_ingress_rows: list[SampleContext] = []
    for row in runs:
        sample = _build_sample_context(row)
        if _is_ordinary_chat_turn(sample.text) and _subject_ingress_proved(sample.sample_id, sample.oe_available):
            ordinary_subject_ingress_rows.append(sample)

    confirmed_subject_ingress_chat_samples = []
    for sample in ordinary_subject_ingress_rows[:8]:
        fields = _collect_present_fields(sample.sample_id)
        confirmed_subject_ingress_chat_samples.append(
            {
                **_sample_entry(sample),
                "subject_ingress_proved": True,
                "subject_trace_writeback_proved": _subject_trace_writeback_proved(sample.sample_id),
                "present_fields": fields,
            }
        )

    other_real_entry_rows = [row for row in growth_rows if _infer_entrypoint_from_row(row) not in {"telegram", "dashboard_chat"}]
    other_real_entry_summary = {
        "count": len(other_real_entry_rows),
        "revision_counter_gt_0": sum(1 for row in other_real_entry_rows if (row.get("revision_counter") or 0) > 0),
        "mode_counts": dict(
            Counter((row.get("response_tendency_summary") or {}).get("preferred_mode") for row in other_real_entry_rows)
        ),
        "entrypoint_counts": dict(Counter(_infer_entrypoint_from_row(row) for row in other_real_entry_rows)),
    }
    agency_summary = {
        "rows": len(agency_rows),
        "writeback_applied_true": sum(1 for row in agency_rows if row.get("writeback_applied") is True),
        "candidate_generated_true": sum(1 for row in agency_rows if row.get("candidate_generated") is True),
    }

    unexpected_representatives = _pick_representatives(ordinary_chat_unexpected_rows, limit=6)
    stage1_isolated_representatives = _pick_representatives(stage1_isolated_rows, limit=6)
    stage1_candidate_representatives = _pick_representatives(stage1_mainline_candidate_unexpected_rows, limit=6)
    control_plane_representative = control_plane_rows[:1]
    policy_representative = policy_rows[:1]

    wording_drift = {
        "readme_nominal_chain_ref": _find_line(
            README_PATH,
            "telegram_bot -> telegram_runtime_bridge -> native_loop -> contract_runtime -> openemotion hooks -> delivery",
        ),
        "pre_runtime_rule_registration_ref": _find_line(RUNTIME_BRIDGE_PATH, "status\": \"profile_rule_registered\""),
        "pre_runtime_rule_enforced_ref": _find_line(RUNTIME_BRIDGE_PATH, "status\": \"profile_rule_enforced\""),
        "telegram_early_return_ref": _find_line(BOT_PATH, "if await self._maybe_handle_runtime_v2_pre_runtime(update, state, pre_runtime):"),
        "openemotion_ingress_ref": _find_line(BOT_PATH, "native_hooks.process_ingress("),
        "native_hooks_runtime_ref": _find_line(HOOKS_PATH, "self.runtime.process_ingress("),
        "drift_detected": True,
        "summary": (
            "README advertises the nominal Telegram mainline chain, but implementation routes many turns through "
            "pre-runtime early-return handling before the native OpenEmotion ingress hook is invoked."
        ),
    }

    observed = {
        "runs": len(runs),
        "host_only": len(host_only_rows),
        "oe_available": sum(1 for row in runs if row.get("oe_available")),
        "control_plane_expected": host_only_counts["control_plane_expected"],
        "policy_driven_host_interception": host_only_counts["policy_driven_host_interception"],
        "unexpected_subject_miss": host_only_counts["unexpected_subject_miss"],
        "telegram_subject_rows": len(telegram_subject_rows),
        "telegram_subject_revision_gt_0": telegram_subject_revision_gt_0,
        "telegram_subject_non_ask_modes": telegram_subject_non_ask_modes,
    }
    baseline_matches = {key: observed[key] == value for key, value in EXPECTED_BASELINE.items()}

    verdict = {
        "headline": (
            "当前 live Telegram 路径中，大量 turn 仍在宿主 pre-runtime / policy interception 层结束；"
            "可以证明一部分真实聊天已进入主体，但还不能证明 live 聊天已稳定表现出 downstream tendency change。"
        ),
        "can_claim": [
            "真实 Telegram 路径里存在 subject ingress 样本",
            "部分真实聊天样本已经生成 openemotion result/trace 和结构化字段",
            "host_only 里可区分控制面预期、策略性宿主拦截、以及异常主体漏接",
        ],
        "cannot_claim": [
            "大多数 Telegram 聊天都进入主体",
            "当前 live Telegram 聊天已稳定体现 downstream tendency change",
            "controlled-axis 能力已经等价转化成 live Telegram 主体主导体验",
        ],
    }

    payload = {
        "status": "pass",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_short": _git_commit_short(),
        "inputs": {
            "runs": _display_path(RUNS_PATH),
            "growth_signals": _display_path(GROWTH_PATH),
            "agency_runs": _display_path(AGENCY_PATH),
            "real_telegram_root": _display_path(REAL_TELEGRAM_ROOT),
        },
        "baseline_expected": EXPECTED_BASELINE,
        "baseline_observed": observed,
        "baseline_matches": baseline_matches,
        "current_verdict": verdict,
        "entrypoint_contract": {
            "accepted_stage1_entrypoints": ["telegram", "dashboard_chat"],
            "run_counts": dict(run_entrypoint_counts),
            "host_only_counts": dict(host_only_entrypoint_counts),
            "ordinary_host_only_counts": dict(ordinary_host_only_entrypoint_counts),
            "growth_signal_counts": dict(growth_entrypoint_counts),
            "agency_run_counts": dict(agency_entrypoint_counts),
            "rule": (
                "Stage 1-3 live evidence must be entrypoint-tagged. Telegram and dashboard chat are equivalent "
                "validation entries only when they traverse the same unified ingress / formal runtime mainline, "
                "and single-entry evidence must not be auto-promoted into cross-entry proof."
            ),
        },
        "host_only_breakdown": {
            "total": len(host_only_rows),
            "counts": dict(host_only_counts),
            "representative_samples": {
                "control_plane_expected": [_sample_entry(sample) for sample in control_plane_representative],
                "policy_driven_host_interception": [_sample_entry(sample) for sample in policy_representative],
                "unexpected_subject_miss": [_sample_entry(sample) for sample in unexpected_representatives[:3]],
            },
        },
        "ordinary_chat_breakdown": {
            "ordinary_host_only_total": len(ordinary_host_only_rows),
            "ordinary_host_only_counts": dict(ordinary_host_only_counts),
            "unexpected_subject_miss_total": len(ordinary_chat_unexpected_rows),
            "unexpected_subject_miss_samples": [_sample_entry(sample) for sample in unexpected_representatives],
            "unexpected_subject_miss_full_list": [_sample_entry(sample) for sample in ordinary_chat_unexpected_rows],
        },
        "stage1_activation_lens": {
            "ordinary_host_only_total": len(ordinary_host_only_rows),
            "isolated_host_only_total": len(stage1_isolated_rows),
            "isolated_host_only_reasons": dict(Counter(sample.stage1_reason for sample in stage1_isolated_rows)),
            "mainline_candidate_host_only_total": len(stage1_mainline_candidate_rows),
            "mainline_candidate_unexpected_miss_total": len(stage1_mainline_candidate_unexpected_rows),
            "isolated_host_only_samples": [_sample_entry(sample) for sample in stage1_isolated_representatives],
            "mainline_candidate_unexpected_miss_samples": [
                _sample_entry(sample) for sample in stage1_candidate_representatives
            ],
            "note": (
                "This supplemental lens isolates policy/control-plane/path-targeted host-only turns from ordinary-chat "
                "mainline-candidate misses. It does not replace the historical baseline and does not itself prove fresh live improvement."
            ),
        },
        "confirmed_subject_ingress_chat_samples": confirmed_subject_ingress_chat_samples,
        "chat_level_tendency_proof": {
            "entrypoint": "telegram",
            "telegram_subject_rows": len(telegram_subject_rows),
            "telegram_subject_revision_gt_0": telegram_subject_revision_gt_0,
            "telegram_subject_non_ask_modes": telegram_subject_non_ask_modes,
            "telegram_subject_mode_counts": dict(telegram_subject_mode_counts),
            "telegram_subject_tone_counts": dict(telegram_subject_tone_counts),
            "telegram_subject_next_step_counts": dict(telegram_subject_next_step_counts),
            "sessions_with_multiple_subject_rows": len(sessions_with_multiple),
            "weak_shift_sessions": weak_shift_sessions,
            "strong_shift_sessions": strong_shift_sessions,
            "unchanged_sessions": unchanged_sessions[:5],
            "downstream_tendency_change_proved_for_live_telegram_chat": bool(strong_shift_sessions),
            "verdict": (
                "当前 live Telegram chat 有 subject ingress 证据，但缺少 downstream tendency change 的强证明。"
            ),
        },
        "other_real_entry_evidence": {
            "growth_signals_session_none": other_real_entry_summary,
            "agency_runs": agency_summary,
            "note": "这些样本可以证明其他真实入口存在 writeback / tendency 证据，但不能冒充直接聊天证明。",
        },
        "wording_drift": wording_drift,
        "next_corrective_slice": {
            "priority": [
                "修复 unexpected_subject_miss，让普通聊天 turn 更稳定进入主体",
                "减少 profile/policy 宿主拦截对普通聊天的覆盖面，或至少把这部分明确隔离出主聊天体验",
                "补 live Telegram chat 下同 session 的 downstream tendency change 强证明",
            ],
            "do_not_do_yet": [
                "继续扩 WP17+ 新能力",
                "把 controlled-axis 结论说成 live Telegram 已成熟",
            ],
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    observed = payload["baseline_observed"]
    entrypoint_contract = payload["entrypoint_contract"]
    host = payload["host_only_breakdown"]
    ordinary = payload["ordinary_chat_breakdown"]
    stage1 = payload["stage1_activation_lens"]
    tendency = payload["chat_level_tendency_proof"]
    drift = payload["wording_drift"]

    def sample_lines(samples: list[dict[str, Any]]) -> str:
        if not samples:
            return "- none"
        return "\n".join(
            f"- `{sample['sample_id']}` | entrypoint=`{sample.get('entrypoint')}` | `{sample['response_plan_status']}` | {sample['text'] or '<no text>'}"
            for sample in samples
        )

    confirmed_lines = "\n".join(
        f"- `{item['sample_id']}` | entrypoint=`{item.get('entrypoint')}` | ingress=`{item['subject_ingress_proved']}` | trace/writeback=`{item['subject_trace_writeback_proved']}` | "
        f"result_fields=`{', '.join(item['present_fields']['result_fields']) or 'none'}` | "
        f"trace_fields=`{', '.join(item['present_fields']['trace_fields']) or 'none'}` | "
        f"text={item['text'] or '<no text>'}"
        for item in payload["confirmed_subject_ingress_chat_samples"][:6]
    )

    ordinary_full_list = "\n".join(
        f"- `{item['sample_id']}` | entrypoint=`{item.get('entrypoint')}` | `{item['response_plan_status']}` | {item['text'] or '<no text>'}"
        for item in ordinary["unexpected_subject_miss_full_list"]
    )

    weak_shift_sessions = tendency["weak_shift_sessions"]
    strong_shift_sessions = tendency["strong_shift_sessions"]
    unchanged_sessions = tendency["unchanged_sessions"]
    if strong_shift_sessions:
        tendency_lines = "\n".join(
            f"- `{item['session_id']}` -> `{json.dumps(item['tendency_tuples'], ensure_ascii=False)}`"
            for item in strong_shift_sessions
        )
    elif weak_shift_sessions:
        tendency_lines = "\n".join(
            f"- `{item['session_id']}` -> `{json.dumps(item['tendency_tuples'], ensure_ascii=False)}`"
            for item in weak_shift_sessions
        )
    else:
        tendency_lines = "\n".join(
            f"- `{item['session_id']}` -> `{json.dumps(item['tendency_tuples'], ensure_ascii=False)}`"
            for item in unchanged_sessions
        ) or "- none"

    return f"""# Telegram Subject Mainline Audit

## 1. Current verdict

- generated_at: `{payload['generated_at']}`
- git_commit_short: `{payload['git_commit_short']}`
- Stage 1 entrypoint contract:
  - accepted entries: `{', '.join(entrypoint_contract['accepted_stage1_entrypoints'])}`
  - runs by entrypoint: `{json.dumps(entrypoint_contract['run_counts'], ensure_ascii=False)}`
  - host-only by entrypoint: `{json.dumps(entrypoint_contract['host_only_counts'], ensure_ascii=False)}`
  - growth signals by entrypoint: `{json.dumps(entrypoint_contract['growth_signal_counts'], ensure_ascii=False)}`
  - agency runs by entrypoint: `{json.dumps(entrypoint_contract['agency_run_counts'], ensure_ascii=False)}`
  - rule: `{entrypoint_contract['rule']}`
- current verdict:
  - {payload['current_verdict']['headline']}
- current baseline:
  - `runs = {observed['runs']}`
  - `host_only = {observed['host_only']}`
  - `oe_available = {observed['oe_available']}`
  - `control_plane_expected = {observed['control_plane_expected']}`
  - `policy_driven_host_interception = {observed['policy_driven_host_interception']}`
  - `unexpected_subject_miss = {observed['unexpected_subject_miss']}`
  - `telegram_subject_rows = {observed['telegram_subject_rows']}`
  - `telegram_subject_revision_gt_0 = {observed['telegram_subject_revision_gt_0']}`
  - `telegram_subject_non_ask_modes = {observed['telegram_subject_non_ask_modes']}`
- can claim:
  - {"; ".join(payload['current_verdict']['can_claim'])}
- cannot claim:
  - {"; ".join(payload['current_verdict']['cannot_claim'])}

## 2. Host-only breakdown

- host-only total: `{host['total']}`
- breakdown:
  - `control_plane_expected = {host['counts'].get('control_plane_expected', 0)}`
  - `policy_driven_host_interception = {host['counts'].get('policy_driven_host_interception', 0)}`
  - `unexpected_subject_miss = {host['counts'].get('unexpected_subject_miss', 0)}`
- representative samples:
  - control_plane_expected:
{sample_lines(host['representative_samples']['control_plane_expected'])}
  - policy_driven_host_interception:
{sample_lines(host['representative_samples']['policy_driven_host_interception'])}
  - unexpected_subject_miss:
{sample_lines(host['representative_samples']['unexpected_subject_miss'])}

## 3. Ordinary chat misses

- ordinary chat host-only total: `{ordinary['ordinary_host_only_total']}`
- ordinary chat host-only breakdown:
  - `control_plane_expected = {ordinary['ordinary_host_only_counts'].get('control_plane_expected', 0)}`
  - `policy_driven_host_interception = {ordinary['ordinary_host_only_counts'].get('policy_driven_host_interception', 0)}`
  - `unexpected_subject_miss = {ordinary['ordinary_host_only_counts'].get('unexpected_subject_miss', 0)}`
- current unexpected ordinary-chat miss list:
{ordinary_full_list or '- none'}

## 3.5. Stage 1 activation lens

- ordinary chat host-only total: `{stage1['ordinary_host_only_total']}`
- isolated host-only total: `{stage1['isolated_host_only_total']}`
- isolated host-only reasons: `{json.dumps(stage1['isolated_host_only_reasons'], ensure_ascii=False)}`
- mainline-candidate host-only total: `{stage1['mainline_candidate_host_only_total']}`
- mainline-candidate unexpected miss total: `{stage1['mainline_candidate_unexpected_miss_total']}`
- isolated host-only samples:
{sample_lines(stage1['isolated_host_only_samples'])}
- mainline-candidate unexpected miss samples:
{sample_lines(stage1['mainline_candidate_unexpected_miss_samples'])}
- note:
  - `{stage1['note']}`

## 4. Confirmed subject-ingress chat samples

- current confirmed samples:
{confirmed_lines or '- none'}
- proof rule:
  - `oe_available = true`
  - `openemotion_result.json` or `openemotion_trace.json` exists
  - `ledger.json.openemotion.result` or `trace_payload` is non-empty for trace/writeback proof

## 5. Chat-level writeback / tendency proof

- `telegram_subject_rows = {tendency['telegram_subject_rows']}`
- `tendency_entrypoint = {tendency['entrypoint']}`
- `telegram_subject_revision_gt_0 = {tendency['telegram_subject_revision_gt_0']}`
- `telegram_subject_non_ask_modes = {tendency['telegram_subject_non_ask_modes']}`
- mode counts: `{json.dumps(tendency['telegram_subject_mode_counts'], ensure_ascii=False)}`
- tone counts: `{json.dumps(tendency['telegram_subject_tone_counts'], ensure_ascii=False)}`
- next-step counts: `{json.dumps(tendency['telegram_subject_next_step_counts'], ensure_ascii=False)}`
- sessions with multiple subject rows: `{tendency['sessions_with_multiple_subject_rows']}`
- weak structural shift sessions: `{len(weak_shift_sessions)}`
- strong proof sessions: `{len(strong_shift_sessions)}`
- live Telegram downstream tendency proof:
  - `{tendency['verdict']}`
- session evidence:
{tendency_lines}
- other real entrypoints:
  - `growth_signals session_id=None count = {payload['other_real_entry_evidence']['growth_signals_session_none']['count']}`
  - `growth_signals session_id=None revision_counter_gt_0 = {payload['other_real_entry_evidence']['growth_signals_session_none']['revision_counter_gt_0']}`
  - `other entrypoint counts = {json.dumps(payload['other_real_entry_evidence']['growth_signals_session_none']['entrypoint_counts'], ensure_ascii=False)}`
  - `agency_runs writeback_applied_true = {payload['other_real_entry_evidence']['agency_runs']['writeback_applied_true']}`
  - note: `{payload['other_real_entry_evidence']['note']}`

## 6. Residual gap and next corrective slice

- wording drift:
  - README nominal chain: `{drift['readme_nominal_chain_ref']}`
  - pre-runtime rule registration: `{drift['pre_runtime_rule_registration_ref']}`
  - pre-runtime rule enforcement: `{drift['pre_runtime_rule_enforced_ref']}`
  - telegram early return: `{drift['telegram_early_return_ref']}`
  - openemotion ingress call: `{drift['openemotion_ingress_ref']}`
  - native hooks runtime: `{drift['native_hooks_runtime_ref']}`
  - drift summary: {drift['summary']}
- next corrective slice:
  - {"; ".join(payload['next_corrective_slice']['priority'])}
- do not do yet:
  - {"; ".join(payload['next_corrective_slice']['do_not_do_yet'])}
"""


def main() -> int:
    payload = build_payload()
    REPORT_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "report_md": _display_path(REPORT_MD_PATH),
        "report_json": _display_path(REPORT_JSON_PATH),
        "baseline_observed": payload["baseline_observed"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
