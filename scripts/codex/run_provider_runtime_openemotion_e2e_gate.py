#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
EGOCORE_ROOT = ROOT / "EgoCore"
REAL_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
DASHBOARD_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
REPORT_JSON = DASHBOARD_ROOT / "PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.json"
REPORT_MD = DASHBOARD_ROOT / "PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.md"

sys.path.insert(0, str(EGOCORE_ROOT))

from app.config import get_config, load_config  # noqa: E402
from app.llm_client import get_llm_client  # noqa: E402


USE_CASES = ("planning", "execution", "reporting", "memory_summary", "chat")
FOLLOWUP_HINT_RE = re.compile(r"(刚刚|这个|那个|页面|网页|看看|记得|怎么样)", re.IGNORECASE)
LEGACY_FALLBACK_RULES = (
    (
        ROOT / "EgoCore" / "app" / "runtime_v2" / "decision_engine.py",
        'config.llm.get("default_provider", "qianfan")',
        "legacy qianfan provider fallback in runtime_v2 decision path",
    ),
    (
        ROOT / "EgoCore" / "app" / "runtime_v2" / "decision_engine.py",
        'config.llm.get("default_model", "glm-5")',
        "legacy glm-5 model fallback in runtime_v2 decision path",
    ),
    (
        ROOT / "EgoCore" / "app" / "runtime_v2" / "chat_reply_engine.py",
        'config.llm.get("default_provider", "qianfan")',
        "legacy qianfan provider fallback in chat mainline",
    ),
    (
        ROOT / "EgoCore" / "app" / "runtime_v2" / "chat_reply_engine.py",
        'config.llm.get("default_model", "glm-5")',
        "legacy glm-5 model fallback in chat mainline",
    ),
    (
        ROOT / "EgoCore" / "app" / "agent_core" / "native_loop.py",
        'get_llm_client(provider="qianfan", model="glm-5")',
        "legacy native loop hardcoded qianfan/glm-5 client",
    ),
)


@dataclass
class SampleRow:
    sample_id: str
    timestamp: str
    session_key: str | None
    text: str | None
    response_plan_status: str | None
    reply_origin: str | None
    reply_authority: str | None
    delivery_kind: str | None
    metadata: dict[str, Any]
    oe_available: bool
    has_result: bool
    has_trace: bool
    has_response_plan: bool


def _git_short_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _git_commit_timestamp(commitish: str) -> datetime:
    completed = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commitish],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"unable to resolve commit timestamp for {commitish}")
    return datetime.fromisoformat(completed.stdout.strip().replace("Z", "+00:00"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_llm_yaml() -> dict[str, Any]:
    return yaml.safe_load((EGOCORE_ROOT / "config" / "llm.yaml").read_text(encoding="utf-8")) or {}


def _load_config():
    try:
        return get_config()
    except Exception:
        return load_config(
            config_dir=str(EGOCORE_ROOT / "config"),
            env_file=str(EGOCORE_ROOT / ".env"),
            validate=False,
        )


def _use_case_matrix(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    providers_cfg = cfg.get("providers") or {}
    default_provider = cfg.get("default_provider")
    default_model = cfg.get("default_model")
    out: dict[str, dict[str, Any]] = {}
    for use_case in USE_CASES:
        use_case_cfg = ((cfg.get("use_cases") or {}).get(use_case) or {})
        provider = use_case_cfg.get("provider") or default_provider
        model = use_case_cfg.get("model") or default_model
        provider_cfg = providers_cfg.get(provider) or {}
        known_models = {str(item.get("id")) for item in provider_cfg.get("models") or [] if item.get("id")}
        out[use_case] = {
            "provider": provider,
            "model": model,
            "provider_enabled": provider_cfg.get("enabled") is not False,
            "model_known": model in known_models,
            "split_from_default": provider != default_provider or model != default_model,
        }
    return out


def _check_config_consistency(allow_provider_split: bool) -> tuple[bool, dict[str, Any]]:
    llm_cfg = _load_llm_yaml()
    matrix = _use_case_matrix(llm_cfg)
    default_provider = llm_cfg.get("default_provider")
    default_model = llm_cfg.get("default_model")
    issues: list[str] = []
    split_use_cases = [name for name, row in matrix.items() if row["split_from_default"]]
    for use_case, row in matrix.items():
        if not row["provider_enabled"]:
            issues.append(f"{use_case} provider disabled: {row['provider']}")
        if not row["model_known"]:
            issues.append(f"{use_case} model not declared under provider: {row['provider']} / {row['model']}")
    if split_use_cases and not allow_provider_split:
        issues.append(f"use-case provider/model split detected: {', '.join(split_use_cases)}")

    legacy_hits: list[dict[str, str]] = []
    for path, needle, reason in LEGACY_FALLBACK_RULES:
        if needle in path.read_text(encoding="utf-8"):
            legacy_hits.append({"path": str(path.relative_to(ROOT)), "reason": reason})
            issues.append(reason)

    return (not issues), {
        "default_provider": default_provider,
        "default_model": default_model,
        "use_case_matrix": matrix,
        "split_use_cases": split_use_cases,
        "legacy_fallback_hits": legacy_hits,
        "issues": issues,
    }


def _run_chat_smoke(cfg) -> tuple[bool, dict[str, Any]]:
    use_case = cfg.get_llm_config_for_use_case("chat")
    provider = str(use_case.get("provider") or cfg.llm.get("default_provider"))
    model = str(use_case.get("model") or cfg.llm.get("default_model"))
    client = get_llm_client(provider=provider, model=model)
    response = client.generate_with_messages(
        [
            {"role": "system", "content": "Do not explain. Do not reason aloud. Reply with exactly: pong"},
            {"role": "user", "content": "Reply with exactly: pong"},
        ],
        temperature=float(use_case.get("temperature") or 0.0),
        max_tokens=min(int(use_case.get("max_tokens") or 256), 256),
        timeout=max(30, int((cfg.llm.get("request") or {}).get("timeout") or 60)),
    )
    content = (response.content or "").strip()
    passed = "pong" in content.lower()
    return passed, {
        "provider": provider,
        "model": model,
        "content": content,
        "finish_reason": response.finish_reason,
        "usage": response.usage,
    }


def _run_execution_tool_smoke(cfg) -> tuple[bool, dict[str, Any]]:
    use_case = cfg.get_llm_config_for_use_case("execution")
    provider = str(use_case.get("provider") or cfg.llm.get("default_provider"))
    model = str(use_case.get("model") or cfg.llm.get("default_model"))
    client = get_llm_client(provider=provider, model=model)
    response = client.chat_with_tools(
        messages=[
            {
                "role": "user",
                "content": "Call the provided function exactly once with path D:/Project/AIProject/MyProject/Test2/bilili_lookalike.html and no extra text.",
            }
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "file_exists",
                    "description": "Check whether a file exists.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                    },
                },
            }
        ],
        temperature=float(use_case.get("temperature") or 0.0),
        max_tokens=min(int(use_case.get("max_tokens") or 256), 256),
        timeout=max(30, int((cfg.llm.get("request") or {}).get("timeout") or 60)),
    )
    first_call = response.tool_calls[0] if response.tool_calls else {}
    passed = bool(response.tool_calls) and first_call.get("name") == "file_exists"
    return passed, {
        "provider": provider,
        "model": model,
        "finish_reason": response.finish_reason,
        "tool_calls": response.tool_calls,
        "usage": response.usage,
    }


def _extract_session_key(raw_update: dict[str, Any]) -> str | None:
    message = raw_update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    chat_type = chat.get("type")
    if chat_id is None or not chat_type:
        return None
    return f"telegram:{chat_type}:{chat_id}"


def _normalize_session_key(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("telegram:dm:"):
        return value.replace("telegram:dm:", "telegram:private:", 1)
    return value


def _is_ordinary_chat_text(text: str | None) -> bool:
    if not text or not text.strip():
        return False
    return not text.lstrip().startswith("/")


def _is_followup_text(text: str | None) -> bool:
    return bool(text and FOLLOWUP_HINT_RE.search(text))


def _load_rows(session_key: str | None, since_commit: str | None) -> list[SampleRow]:
    commit_ts = _git_commit_timestamp(since_commit) if since_commit else None
    normalized_target_session = _normalize_session_key(session_key)
    rows: list[SampleRow] = []
    for sample_dir in sorted(REAL_ROOT.iterdir()):
        if not sample_dir.is_dir() or not sample_dir.name.startswith("sample_"):
            continue
        ledger_path = sample_dir / "ledger.json"
        raw_path = sample_dir / "raw_update.json"
        if not ledger_path.exists() or not raw_path.exists():
            continue
        ledger = _read_json(ledger_path)
        timestamp = ledger.get("timestamp")
        if not isinstance(timestamp, str):
            continue
        sample_ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if commit_ts and sample_ts <= commit_ts:
            continue
        raw_update = _read_json(raw_path)
        sample_session_key = _extract_session_key(raw_update)
        if normalized_target_session and _normalize_session_key(sample_session_key) != normalized_target_session:
            continue
        response_plan_path = sample_dir / "response_plan.json"
        result_path = sample_dir / "openemotion_result.json"
        trace_path = sample_dir / "openemotion_trace.json"
        response_plan = _read_json(response_plan_path) if response_plan_path.exists() else {}
        message = raw_update.get("message") or {}
        rows.append(
            SampleRow(
                sample_id=sample_dir.name,
                timestamp=timestamp,
                session_key=sample_session_key,
                text=message.get("text") if isinstance(message.get("text"), str) else None,
                response_plan_status=response_plan.get("status"),
                reply_origin=response_plan.get("reply_origin"),
                reply_authority=response_plan.get("reply_authority"),
                delivery_kind=response_plan.get("delivery_kind"),
                metadata=response_plan.get("metadata") or {},
                oe_available=bool((ledger.get("openemotion") or {})),
                has_result=result_path.exists(),
                has_trace=trace_path.exists(),
                has_response_plan=response_plan_path.exists(),
            )
        )
    return rows


def _latest_session_key() -> str | None:
    rows = _load_rows(session_key=None, since_commit=None)
    if not rows:
        return None
    return rows[-1].session_key


def _restrict_to_latest_reset_window(rows: list[SampleRow]) -> tuple[list[SampleRow], str | None]:
    ordered = sorted(rows, key=lambda item: item.timestamp)
    latest_reset_index = None
    for index, row in enumerate(ordered):
        if (row.text or "").lstrip().startswith("/new"):
            latest_reset_index = index
    if latest_reset_index is None:
        return ordered, None
    return ordered[latest_reset_index:], ordered[latest_reset_index].sample_id


def _check_telegram_task_flow(rows: list[SampleRow]) -> tuple[bool, dict[str, Any]]:
    has_reset = any((row.text or "").lstrip().startswith("/new") for row in rows)
    ordinary_chat_samples = [
        row for row in rows if _is_ordinary_chat_text(row.text) and row.response_plan_status == "chat"
    ]
    task_samples = [row for row in rows if row.reply_origin == "task_mainline" or row.delivery_kind == "final"]
    passed = bool(has_reset and ordinary_chat_samples and task_samples)
    return passed, {
        "session_key": rows[0].session_key if rows else None,
        "sample_ids": [row.sample_id for row in rows],
        "has_new_reset": has_reset,
        "ordinary_chat_samples": [row.sample_id for row in ordinary_chat_samples],
        "task_samples": [row.sample_id for row in task_samples],
    }


def _check_openemotion_evidence(rows: list[SampleRow]) -> tuple[bool, dict[str, Any]]:
    target_rows = [
        row for row in rows if row.response_plan_status == "chat" or row.reply_origin == "task_mainline" or row.delivery_kind == "final"
    ]
    failures = []
    for row in target_rows:
        if not (row.has_result and row.has_trace and row.has_response_plan and row.oe_available):
            failures.append(
                {
                    "sample_id": row.sample_id,
                    "has_result": row.has_result,
                    "has_trace": row.has_trace,
                    "has_response_plan": row.has_response_plan,
                    "oe_available": row.oe_available,
                }
            )
    return (bool(target_rows) and not failures), {
        "checked_sample_ids": [row.sample_id for row in target_rows],
        "failures": failures,
    }


def _check_followup_continuity(rows: list[SampleRow]) -> tuple[bool, dict[str, Any]]:
    ordered = sorted(rows, key=lambda item: item.timestamp)
    task_rows = [
        row
        for row in ordered
        if row.reply_origin == "task_mainline" and isinstance((row.metadata or {}).get("recent_result_context"), dict)
    ]
    followup_rows = [
        row
        for row in ordered
        if _is_ordinary_chat_text(row.text) and _is_followup_text(row.text) and row.response_plan_status == "chat"
    ]
    accepted: list[dict[str, Any]] = []
    for task_row in task_rows:
        recent_ctx = (task_row.metadata or {}).get("recent_result_context") or {}
        target_name = recent_ctx.get("target_name")
        target_path = recent_ctx.get("target_path")
        for followup in followup_rows:
            if followup.timestamp <= task_row.timestamp:
                continue
            tendency_summary = (followup.metadata or {}).get("response_tendency_summary") or {}
            if followup.reply_authority == "host_degraded_fallback":
                continue
            if not followup.oe_available:
                continue
            if tendency_summary.get("suggested_next_step") not in {"continue_pending_commitment", "continue_thread", "clarify_or_repair"}:
                continue
            accepted.append(
                {
                    "task_sample_id": task_row.sample_id,
                    "followup_sample_id": followup.sample_id,
                    "target_name": target_name,
                    "target_path": target_path,
                    "followup_text": followup.text,
                    "suggested_next_step": tendency_summary.get("suggested_next_step"),
                }
            )
            break
    return bool(accepted), {
        "task_samples_with_recent_result_context": [row.sample_id for row in task_rows],
        "followup_candidates": [row.sample_id for row in followup_rows],
        "accepted_pairs": accepted,
    }


def _check_artifact_consistency(rows: list[SampleRow]) -> tuple[bool, dict[str, Any]]:
    issues = []
    for row in rows:
        if row.reply_authority == "host_degraded_fallback":
            issues.append({"sample_id": row.sample_id, "reason": "host_degraded_fallback"})
        if row.response_plan_status in {"pre_runtime", "delivered_without_explicit_plan"}:
            issues.append({"sample_id": row.sample_id, "reason": f"unexpected_status:{row.response_plan_status}"})
        if (row.response_plan_status == "chat" or row.reply_origin == "task_mainline") and not row.oe_available:
            issues.append({"sample_id": row.sample_id, "reason": "missing_openemotion_ledger"})
    return (not issues), {"issues": issues}


def _render_markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    def mark(value: bool) -> str:
        return "pass" if value else "fail"

    lines = [
        "# Provider / Runtime OpenEmotion E2E Gate",
        "",
        "## Current verdict",
        "",
        f"- result: `{mark(payload['all_passed'])}`",
        f"- git_commit_short: `{payload['git_commit_short']}`",
        f"- session_key: `{payload.get('session_key')}`",
        f"- since_commit: `{payload.get('since_commit')}`",
        "",
        "## Gate results",
        "",
    ]
    for name in (
        "config_consistent",
        "chat_smoke_pass",
        "execution_tool_call_pass",
        "telegram_task_flow_pass",
        "openemotion_evidence_pass",
        "followup_continuity_pass",
        "artifact_consistency_pass",
    ):
        lines.append(f"- `{name}`: `{mark(checks[name]['passed'])}`")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- config issues: `{len(checks['config_consistent']['details'].get('issues') or [])}`",
            f"- sample count: `{payload.get('sample_count')}`",
            f"- task sample count: `{len(checks['telegram_task_flow_pass']['details'].get('task_samples') or [])}`",
            f"- accepted continuity pairs: `{len(checks['followup_continuity_pass']['details'].get('accepted_pairs') or [])}`",
            "",
            "## Artifact paths",
            "",
            f"- json: `{REPORT_JSON}`",
            f"- md: `{REPORT_MD}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(since_commit: str | None, session_key: str | None, allow_provider_split: bool) -> dict[str, Any]:
    cfg = _load_config()
    selected_session = session_key or _latest_session_key()
    all_rows = _load_rows(selected_session, since_commit)
    rows, reset_sample_id = _restrict_to_latest_reset_window(all_rows)

    config_ok, config_details = _check_config_consistency(allow_provider_split=allow_provider_split)
    chat_ok, chat_details = _run_chat_smoke(cfg)
    execution_ok, execution_details = _run_execution_tool_smoke(cfg)
    task_flow_ok, task_flow_details = _check_telegram_task_flow(rows)
    evidence_ok, evidence_details = _check_openemotion_evidence(rows)
    continuity_ok, continuity_details = _check_followup_continuity(rows)
    artifact_ok, artifact_details = _check_artifact_consistency(rows)

    checks = {
        "config_consistent": {"passed": config_ok, "details": config_details},
        "chat_smoke_pass": {"passed": chat_ok, "details": chat_details},
        "execution_tool_call_pass": {"passed": execution_ok, "details": execution_details},
        "telegram_task_flow_pass": {"passed": task_flow_ok, "details": task_flow_details},
        "openemotion_evidence_pass": {"passed": evidence_ok, "details": evidence_details},
        "followup_continuity_pass": {"passed": continuity_ok, "details": continuity_details},
        "artifact_consistency_pass": {"passed": artifact_ok, "details": artifact_details},
    }
    all_passed = all(item["passed"] for item in checks.values())
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": _git_short_head(),
        "since_commit": since_commit,
        "session_key": selected_session,
        "window_start_sample_id": reset_sample_id,
        "allow_provider_split": allow_provider_split,
        "sample_count": len(rows),
        "raw_session_sample_count": len(all_rows),
        "sample_ids": [row.sample_id for row in rows],
        "checks": checks,
        "all_passed": all_passed,
        "claim_ceiling": (
            "provider/runtime admission gate passed"
            if all_passed
            else "only conditional completion is allowed; do not claim live restored/stable"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run provider/runtime OpenEmotion E2E admission gate.")
    parser.add_argument("--since-commit", help="Only inspect real Telegram samples after this commit timestamp.")
    parser.add_argument("--session-key", help="Limit sample audit to one Telegram session key.")
    parser.add_argument("--allow-provider-split", action="store_true", help="Permit intentional use-case provider/model split.")
    args = parser.parse_args()

    payload = build_payload(
        since_commit=args.since_commit,
        session_key=args.session_key,
        allow_provider_split=args.allow_provider_split,
    )
    DASHBOARD_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
