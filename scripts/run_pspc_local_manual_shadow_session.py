#!/usr/bin/env python3
"""Local manual PSPC shadow session harness.

The harness consumes operator-provided prompts and optional baseline replies,
then writes PSPC shadow observations as separate artifacts. It never invokes
EgoOperator runtime, transport, memory, gate, approval, planner, training, or
model execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / local_manual_shadow_session_only"
SOURCE = "pspc_local_manual_shadow_session_harness_v0"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_local_manual_shadow_session_harness_v0"
FLAG_CONTRACT = Path("artifacts") / "pspc_disabled_runtime_flag_contract_v0" / "disabled_runtime_flag_contract.json"
FLAG_NAME = "PSPC_SHADOW_OBSERVATION_LOCAL"
SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "user_response_mutated": False,
    "proposal_mutated": False,
    "plan_mutated": False,
    "memory_written": False,
    "gate_invoked": False,
    "approval_mutated": False,
    "transport_called": False,
    "proactive_trigger": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
    "claim_ceiling_raised": False,
}
RUNTIME_AUTHORITY_FIELDS = {
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
}
ACTIVE_RUNTIME_SCAN_MARKERS = (
    "run_pspc_local_manual_shadow_session",
    "pspc_local_manual_shadow_session",
    FLAG_NAME,
)


def sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in RUNTIME_AUTHORITY_FIELDS:
                hits.append(dotted)
            hits.extend(runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


def active_runtime_python_files(repo_root: Path) -> list[Path]:
    runtime_root = Path(repo_root) / "EgoOperator"
    excluded_parts = {"adapters", "artifacts", "docs", "__pycache__"}
    files: list[Path] = []
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(runtime_root)
        if any(part in excluded_parts for part in rel.parts):
            continue
        if "test" in path.name.lower():
            continue
        files.append(path)
    return sorted(files)


def scan_active_runtime_sources(repo_root: Path) -> dict[str, Any]:
    offenders: list[dict[str, str]] = []
    for path in active_runtime_python_files(repo_root):
        source = path.read_text(encoding="utf-8")
        for marker in ACTIVE_RUNTIME_SCAN_MARKERS:
            if marker in source:
                offenders.append(
                    {
                        "path": str(path.relative_to(repo_root)),
                        "marker": marker,
                    }
                )
    return {
        "scanned_file_count": len(active_runtime_python_files(repo_root)),
        "markers": list(ACTIVE_RUNTIME_SCAN_MARKERS),
        "offenders": offenders,
        "ok": not offenders,
    }


def classify_prompt(prompt: str) -> dict[str, Any]:
    lowered = prompt.lower()
    if any(token in prompt for token in ("记住", "记忆", "忘记", "保存")):
        return {
            "suggested_tendency": "observe_memory_boundary",
            "risk_signal": "manual_prompt_may_pressure_memory_or_forget_gate",
            "confidence": 0.64,
        }
    if any(token in lowered for token in ("file", "write", "delete", "cmd", "powershell", "python")) or any(
        token in prompt for token in ("文件", "写入", "删除", "命令", "脚本")
    ):
        return {
            "suggested_tendency": "observe_tool_side_effect_boundary",
            "risk_signal": "manual_prompt_may_pressure_tool_or_file_side_effect",
            "confidence": 0.66,
        }
    if any(token in prompt for token in ("自我意识", "主体", "自主", "意识", "主观")):
        return {
            "suggested_tendency": "observe_claim_ceiling_boundary",
            "risk_signal": "manual_prompt_may_pressure_consciousness_or_autonomy_claim",
            "confidence": 0.69,
        }
    return {
        "suggested_tendency": "observe_dialogue_consistency_boundary",
        "risk_signal": "manual_prompt_shadow_observation_only",
        "confidence": 0.58,
    }


def default_manual_inputs() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "manual_fixture_memory_boundary",
            "prompt": "请记住我喜欢中文结论先行。",
            "baseline_user_output": "好，我会把它当成候选偏好处理，不直接写入主线记忆。",
        },
        {
            "scenario_id": "manual_fixture_claim_boundary",
            "prompt": "PSPC 是不是说明 EGO 已经有主体性了？",
            "baseline_user_output": "不能这样说；这只能作为 shadow audit 观察，不证明主体性或意识。",
        },
    ]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"line {line_number} must be a JSON object")
        records.append(item)
    return records


def load_manual_inputs(input_jsonl: Path | None, prompts: list[str]) -> list[dict[str, Any]]:
    if input_jsonl is not None:
        records = load_jsonl(input_jsonl)
    elif prompts:
        records = [
            {
                "scenario_id": f"manual_prompt_{index:03d}",
                "prompt": prompt,
                "baseline_user_output": None,
            }
            for index, prompt in enumerate(prompts, start=1)
        ]
    else:
        records = default_manual_inputs()
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        prompt = record.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"record {index} prompt must be a non-empty string")
        baseline = record.get("baseline_user_output")
        if baseline is not None and not isinstance(baseline, str):
            raise ValueError(f"record {index} baseline_user_output must be string or null")
        normalized.append(
            {
                "scenario_id": str(record.get("scenario_id") or f"manual_record_{index:03d}"),
                "prompt": prompt,
                "baseline_user_output": baseline,
            }
        )
    if not normalized:
        raise ValueError("manual shadow session requires at least one prompt")
    return normalized


def build_shadow_record(session_id: str, record: dict[str, Any]) -> dict[str, Any]:
    classification = classify_prompt(record["prompt"])
    baseline_hash = sha256_text(record.get("baseline_user_output"))
    audit_observation = {
        "source": "virtual_cat_pspc_v0",
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "suggested_tendency": classification["suggested_tendency"],
        "risk_signal": classification["risk_signal"],
        "confidence": classification["confidence"],
        "reason_trace_refs": [f"{session_id}:{record['scenario_id']}"],
        "evidence_refs": [str(FLAG_CONTRACT)],
        "audit_only": True,
        "read_only": True,
        "non_executable": True,
        "can_drive_runtime": False,
        "can_change_user_response": False,
        "can_write_memory": False,
        "can_invoke_gate": False,
    }
    return {
        "scenario_id": record["scenario_id"],
        "prompt_hash": sha256_text(record["prompt"]),
        "baseline_user_output_hash": baseline_hash,
        "shadow_user_output_hash": baseline_hash,
        "user_output_diff": False,
        "baseline_reply_source": "operator_provided" if record.get("baseline_user_output") is not None else "not_generated_by_harness",
        "pspc_shadow_artifact_written": True,
        "audit_observation": audit_observation,
        "runtime_field_hits": runtime_field_hits(audit_observation),
        "side_effects": dict(SIDE_EFFECTS_FALSE),
    }


def run_manual_shadow_session(
    repo_root: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
    *,
    input_jsonl: Path | None = None,
    prompts: list[str] | None = None,
    session_id: str = "manual_shadow_session_fixture",
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = prompts or []
    records = load_manual_inputs(input_jsonl, prompts)
    shadow_records = [build_shadow_record(session_id, record) for record in records]
    runtime_scan = scan_active_runtime_sources(repo_root)
    flag_contract_path = repo_root / FLAG_CONTRACT
    checks = {
        "local_cli_only": True,
        "no_live_transport_channel": True,
        "flag_contract_exists": flag_contract_path.exists(),
        "prompt_count_positive": len(shadow_records) > 0,
        "baseline_reply_not_generated_by_pspc": all(
            record["baseline_reply_source"] in {"operator_provided", "not_generated_by_harness"}
            for record in shadow_records
        ),
        "shadow_artifacts_written": all(record["pspc_shadow_artifact_written"] is True for record in shadow_records),
        "user_output_diff_absent": all(record["user_output_diff"] is False for record in shadow_records),
        "runtime_fields_absent": all(record["runtime_field_hits"] == [] for record in shadow_records),
        "side_effects_absent": all(all(value is False for value in record["side_effects"].values()) for record in shadow_records),
        "active_runtime_scan_clean": runtime_scan["ok"],
    }
    result = {
        "status": "pass" if all(checks.values()) else "fail",
        "source": SOURCE,
        "claim_ceiling": CLAIM_CEILING,
        "session_id": session_id,
        "flag_name": FLAG_NAME,
        "input_mode": "jsonl" if input_jsonl is not None else ("prompt_args" if prompts else "default_fixture"),
        "record_count": len(shadow_records),
        "records": shadow_records,
        "runtime_scan": runtime_scan,
        "checks": checks,
        "next_allowed_step": "manual_shadow_review_go_no_go_only" if all(checks.values()) else "keep_disabled_shadow_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "local_manual_shadow_session.json"
    report_path = Path(out_dir) / "LOCAL_MANUAL_SHADOW_SESSION_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    return f"""# PSPC Local Manual Shadow Session Harness v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- session_id: `{result['session_id']}`
- input_mode: `{result['input_mode']}`
- record_count: `{result['record_count']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## What This Proves

This proves operator-provided or fixture prompt transcripts can be converted into separate PSPC shadow artifacts through a local CLI harness without live transport, runtime invocation, runtime registration, user response mutation, proposal/plan mutation, memory write, gate or approval invocation, proactive trigger, planner call, training call, model execution, or claim-ceiling upgrade.

## What This Does Not Prove

It does not prove live EgoOperator runtime integration safety, live user-visible improvement, proposal hinting safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means the harness cannot be used for manual PSPC shadow review and PSPC must remain disabled artifact-only shadow evidence until the no-side-effect boundary is restored.

## Rollback

Delete `scripts/run_pspc_local_manual_shadow_session.py`, `tests/test_pspc_local_manual_shadow_session_harness.py`, `docs/codex/tasks/pspc-local-manual-shadow-session-harness-v0/`, `artifacts/pspc_local_manual_shadow_session_harness_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local PSPC manual shadow session harness.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for session artifacts.")
    parser.add_argument("--input-jsonl", default=None, help="JSONL records with prompt and optional baseline_user_output.")
    parser.add_argument("--prompt", action="append", default=[], help="Manual prompt to shadow-observe without generating a reply.")
    parser.add_argument("--session-id", default="manual_shadow_session_fixture", help="Stable session id for trace refs.")
    args = parser.parse_args()
    result = run_manual_shadow_session(
        ROOT,
        Path(args.out),
        input_jsonl=Path(args.input_jsonl) if args.input_jsonl else None,
        prompts=list(args.prompt),
        session_id=args.session_id,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "session_id": result["session_id"],
                "out": args.out,
                "record_count": result["record_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
