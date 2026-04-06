#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REAL_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
DASHBOARD_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
REPORT_MD = DASHBOARD_ROOT / "LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.md"
REPORT_JSON = DASHBOARD_ROOT / "LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.json"


@dataclass
class SampleRow:
    sample_id: str
    timestamp: str
    text: str | None
    response_plan_status: str | None
    reply_authority: str | None
    reply_origin: str | None
    delivery_kind: str | None
    oe_available: bool
    preferred_mode: str | None
    preferred_tone: str | None
    next_step: str | None
    chat_cadence_mode: str | None
    richer_field_presence: dict[str, bool]
    session_key: str | None


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_short_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _git_commit_timestamp(commitish: str) -> str:
    completed = subprocess.run(
        ["git", "show", "-s", "--format=%cI", commitish],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"unable to resolve commit timestamp for {commitish}")
    return completed.stdout.strip()


def _is_profile_rule_registration(text: str | None) -> bool:
    if not text:
        return False
    stripped = text.strip()
    return (("以后凡是" in stripped) or stripped.startswith("以后")) and ("默认走" in stripped)


def _is_ordinary_chat_text(text: str | None) -> bool:
    if not text or not text.strip():
        return False
    if text.lstrip().startswith("/"):
        return False
    if _is_profile_rule_registration(text):
        return False
    return True


def _load_rows(since_commit: str) -> list[SampleRow]:
    commit_ts = datetime.fromisoformat(_git_commit_timestamp(since_commit).replace("Z", "+00:00"))
    commit_ts_local = commit_ts.astimezone().replace(tzinfo=None)
    rows: list[SampleRow] = []

    for sample_dir in sorted(REAL_ROOT.iterdir()):
        if not sample_dir.is_dir() or not sample_dir.name.startswith("sample_"):
            continue

        ledger_path = sample_dir / "ledger.json"
        if not ledger_path.exists():
            continue

        ledger = _read_json(ledger_path)
        ts = ledger.get("timestamp")
        if not isinstance(ts, str):
            continue
        sample_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if sample_ts.tzinfo is not None:
            sample_ts_cmp = sample_ts.astimezone().replace(tzinfo=None)
        else:
            sample_ts_cmp = sample_ts
        if sample_ts_cmp <= commit_ts_local:
            continue

        raw_update = _read_json(sample_dir / "raw_update.json") if (sample_dir / "raw_update.json").exists() else {}
        response_plan = _read_json(sample_dir / "response_plan.json") if (sample_dir / "response_plan.json").exists() else {}

        openemotion = ledger.get("openemotion") or {}
        result_payload = _read_json(sample_dir / "openemotion_result.json") if (sample_dir / "openemotion_result.json").exists() else (openemotion.get("result") or {})
        trace_payload = _read_json(sample_dir / "openemotion_trace.json") if (sample_dir / "openemotion_trace.json").exists() else (openemotion.get("trace_payload") or {})

        message = raw_update.get("message") or {}
        text = message.get("text")
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        chat_type = chat.get("type")
        session_key = None
        if chat_id is not None and chat_type:
            session_key = f"telegram:{chat_type}:{chat_id}"

        tendency = (result_payload.get("response_tendency") or trace_payload.get("response_tendency") or {})
        metadata = response_plan.get("metadata") or {}
        richer_field_presence = {
            field: field in result_payload or field in trace_payload
            for field in (
                "social_policy_hints",
                "embodied_policy_hints",
                "integrated_policy_hints",
                "initiative_policy_hints",
            )
        }

        rows.append(
            SampleRow(
                sample_id=sample_dir.name,
                timestamp=ts,
                text=text if isinstance(text, str) else None,
                response_plan_status=response_plan.get("status"),
                reply_authority=response_plan.get("reply_authority"),
                reply_origin=response_plan.get("reply_origin"),
                delivery_kind=response_plan.get("delivery_kind"),
                oe_available=bool(openemotion),
                preferred_mode=tendency.get("preferred_mode"),
                preferred_tone=tendency.get("preferred_tone"),
                next_step=tendency.get("suggested_next_step"),
                chat_cadence_mode=response_plan.get("chat_cadence_mode") or metadata.get("chat_cadence_mode"),
                richer_field_presence=richer_field_presence,
                session_key=session_key,
            )
        )

    return rows


def _tendency_signature(row: SampleRow) -> tuple[str | None, str | None, str | None]:
    return (row.preferred_mode, row.preferred_tone, row.next_step)


def _classify_row(row: SampleRow) -> str:
    if not _is_ordinary_chat_text(row.text):
        return "non_ordinary"
    if row.response_plan_status == "chat":
        return "ordinary_chat_mainline"
    if row.response_plan_status in {"profile_rule_enforced", "profile_rule_registered"}:
        return "ordinary_text_policy_or_control"
    return "ordinary_text_non_chat"


def build_payload(since_commit: str) -> dict[str, Any]:
    rows = _load_rows(since_commit)
    by_class = defaultdict(list)
    for row in rows:
        by_class[_classify_row(row)].append(row)

    ordinary_chat_rows = by_class["ordinary_chat_mainline"]
    sessions: dict[str, list[SampleRow]] = defaultdict(list)
    for row in ordinary_chat_rows:
        sessions[row.session_key or "unknown"].append(row)

    tendency_delta_sessions: list[dict[str, Any]] = []
    cadence_delta_sessions: list[dict[str, Any]] = []
    for session_key, session_rows in sessions.items():
        ordered = sorted(session_rows, key=lambda item: item.timestamp)
        tendency_values = {_tendency_signature(item) for item in ordered}
        cadence_values = {item.chat_cadence_mode for item in ordered}
        if len(tendency_values) >= 2:
            tendency_delta_sessions.append(
                {
                    "session_key": session_key,
                    "sample_ids": [item.sample_id for item in ordered],
                    "tendency_values": sorted(list(tendency_values)),
                }
            )
        if len({value for value in cadence_values if value}) >= 2:
            cadence_delta_sessions.append(
                {
                    "session_key": session_key,
                    "sample_ids": [item.sample_id for item in ordered],
                    "cadence_values": sorted([value for value in cadence_values if value]),
                }
            )

    richer_rows = [
        row for row in ordinary_chat_rows if any(row.richer_field_presence.values())
    ]

    met = (
        bool(ordinary_chat_rows)
        and bool(richer_rows)
        and bool(tendency_delta_sessions)
        and bool(cadence_delta_sessions)
    )

    sample_mix = Counter(_classify_row(row) for row in rows)
    representative_rows = rows[: min(6, len(rows))]

    verdict = (
        "M5 acceptance met"
        if met
        else "M5 acceptance not met: fresh window lacks qualifying ordinary-chat evidence for richer fields plus tendency/cadence deltas"
    )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "git_commit_short": _git_short_head(),
        "since_commit": since_commit,
        "since_commit_timestamp": _git_commit_timestamp(since_commit),
        "fresh_sample_count": len(rows),
        "sample_mix": dict(sample_mix),
        "ordinary_chat_rows": len(ordinary_chat_rows),
        "ordinary_chat_with_richer_fields": len(richer_rows),
        "tendency_delta_sessions": tendency_delta_sessions,
        "cadence_delta_sessions": cadence_delta_sessions,
        "acceptance_met": met,
        "verdict": verdict,
        "representative_samples": [
            {
                "sample_id": row.sample_id,
                "timestamp": row.timestamp,
                "class": _classify_row(row),
                "text": row.text,
                "response_plan_status": row.response_plan_status,
                "reply_authority": row.reply_authority,
                "reply_origin": row.reply_origin,
                "delivery_kind": row.delivery_kind,
                "oe_available": row.oe_available,
                "preferred_mode": row.preferred_mode,
                "preferred_tone": row.preferred_tone,
                "next_step": row.next_step,
                "chat_cadence_mode": row.chat_cadence_mode,
                "richer_field_presence": row.richer_field_presence,
                "session_key": row.session_key,
            }
            for row in representative_rows
        ],
        "remaining_gap": [
            "need at least one fresh ordinary-chat mainline window after deployment",
            "need richer bounded fields visible in fresh ordinary-chat samples",
            "need at least one tendency delta within a real Telegram session",
            "need at least one cadence delta within a real Telegram session or verified hold_for_followup artifact",
        ]
        if not met
        else [],
    }


def write_reports(payload: dict[str, Any]) -> None:
    DASHBOARD_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mix_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in sorted(payload["sample_mix"].items())
    ) or "- none"
    sample_lines = "\n".join(
        f"- `{row['sample_id']}` | `{row['class']}` | `{row['response_plan_status']}` | `{row['text']}`"
        for row in payload["representative_samples"]
    ) or "- none"
    tendency_lines = "\n".join(
        f"- `{item['session_key']}` -> `{item['tendency_values']}`"
        for item in payload["tendency_delta_sessions"]
    ) or "- none"
    cadence_lines = "\n".join(
        f"- `{item['session_key']}` -> `{item['cadence_values']}`"
        for item in payload["cadence_delta_sessions"]
    ) or "- none"
    gap_lines = "\n".join(f"- {item}" for item in payload["remaining_gap"]) or "- none"

    report = f"""# Live Chat Subjective Variability Current

## Current verdict

- verdict: `{payload['verdict']}`
- acceptance_met: `{payload['acceptance_met']}`
- since_commit: `{payload['since_commit']}`
- since_commit_timestamp: `{payload['since_commit_timestamp']}`
- fresh_sample_count: `{payload['fresh_sample_count']}`

## Sample mix

{mix_lines}

## Ordinary chat proof

- ordinary_chat_rows: `{payload['ordinary_chat_rows']}`
- ordinary_chat_with_richer_fields: `{payload['ordinary_chat_with_richer_fields']}`

## Tendency delta sessions

{tendency_lines}

## Cadence delta sessions

{cadence_lines}

## Representative samples

{sample_lines}

## Remaining gap

{gap_lines}
"""
    REPORT_MD.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove live-chat subjective variability on a fresh real Telegram window")
    parser.add_argument("--since-commit", required=True, help="Commit hash whose deployment window should be used")
    args = parser.parse_args()

    payload = build_payload(args.since_commit)
    write_reports(payload)
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print(payload["verdict"])
    return 0 if payload["acceptance_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
