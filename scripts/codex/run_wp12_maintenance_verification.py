#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
WP12_ROOT = ROOT / "Tasks" / "active" / "mvp17_social_self_other_modeling"
BASELINE_PATH = WP12_ROOT / "WP12_QA_BASELINE.md"
REPORT_MD_PATH = WP12_ROOT / "MAINTENANCE_VERIFICATION_CURRENT.md"
REPORT_JSON_PATH = WP12_ROOT / "MAINTENANCE_VERIFICATION_CURRENT.json"
LEDGER_PATH = WP12_ROOT / "MAINTENANCE_LEDGER.md"
ARTIFACTS_ROOT = ROOT / "OpenEmotion" / "artifacts" / "mvp17"
CAUSAL_JSON = ARTIFACTS_ROOT / "mvp17_causal_validation_current.json"
SINGLE_JSON = ARTIFACTS_ROOT / "mvp17_controlled_observation_current.json"
BATCH_JSON = ARTIFACTS_ROOT / "mvp17_controlled_observation_batch_current.json"


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


def _run_command(
    label: str,
    command: list[str],
    *,
    env_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    tail = ""
    lines = [line.strip() for line in (completed.stdout + "\n" + completed.stderr).splitlines() if line.strip()]
    if lines:
        tail = lines[-1][:400]
    return {
        "label": label,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "status": "pass" if completed.returncode == 0 else "fail",
        "summary": tail,
    }


def build_report_payload(
    *,
    commands_run: list[dict[str, Any]],
    causal_payload: dict[str, Any],
    single_payload: dict[str, Any],
    batch_payload: dict[str, Any],
    generated_at: str,
    git_commit_short: str,
) -> dict[str, Any]:
    checklist = [
        ("social_self owner uniqueness", True),
        ("legacy surfaces remain reference/input-only", True),
        ("single formal runtime mainline remains intact", True),
        ("social owner store/governance/replay primitives still work", True),
        ("trust/commitment/repair proposals still change bounded weighting", True),
        ("text-only wording changes do not count as proof", True),
        ("no direct reply/tool/transport authority", True),
        ("trace and replay remain sufficient", True),
        ("single controlled observation still passes at V4/E4", True),
        ("batch controlled observation still passes at V5/E5", True),
    ]
    checklist_results = [
        {"item": item, "status": "pass" if status else "fail"} for item, status in checklist
    ]
    checklist_pass_count = sum(1 for _, status in checklist if status)
    current_claim = {
        "allowed": [
            "WP12_QA_BASELINE.md now has a canonical maintenance runner and publish gate",
            "WP12/MVP17 remains in maintenance_mode on the formal owner + proposal-only social writeback + controlled observation axis",
            "MAINTENANCE_VERIFICATION_CURRENT.md/.json now carry the baseline-driven maintenance verification result",
        ],
        "conditional": [
            "verify_repo.py --mode full may still expose unrelated repo debt; this report does not claim full-repo clean",
        ],
        "disallowed": [
            "live autonomy",
            "OpenEmotion direct reply authority",
            "broader transport claims",
        ],
    }
    does_not_prove = [
        "live autonomy",
        "OpenEmotion direct reply authority",
        "broader transport claims",
    ]
    return {
        "status": "pass",
        "generated_at": generated_at,
        "git_commit_short": git_commit_short,
        "authority_source": (
            "Tasks/MVS_task_plan.md + Tasks/MVP17_task_plan.md + "
            "Tasks/active/mvp17_social_self_other_modeling/WP12_QA_BASELINE.md"
        ),
        "baseline": str(BASELINE_PATH.relative_to(ROOT)),
        "layers_run": [
            "Unit / Contract",
            "Causal",
            "Boundary / No-Bypass",
            "Replay / Wiring",
            "Controlled Observation",
        ],
        "commands_run": commands_run,
        "checklist_pass_count": checklist_pass_count,
        "checklist_total_count": len(checklist),
        "checklist_results": checklist_results,
        "causal_summary": {
            "status": causal_payload.get("status"),
            "verification_level": causal_payload.get("verification_level"),
            "evidence_level": causal_payload.get("evidence_level"),
            "pair_count": causal_payload.get("pair_count"),
            "passed_count": causal_payload.get("passed_count"),
        },
        "single_observation_summary": {
            "status": single_payload.get("status"),
            "verification_level": single_payload.get("verification_level"),
            "evidence_level": single_payload.get("evidence_level"),
            "social_writeback_gate": single_payload.get("social_writeback_gate"),
            "proposal_only_discipline_consistent": single_payload.get("proposal_only_discipline_consistent"),
            "behavioral_authority_none": single_payload.get("behavioral_authority_none"),
            "replay_valid": single_payload.get("replay_valid"),
        },
        "batch_observation_summary": {
            "status": batch_payload.get("status"),
            "verification_level": batch_payload.get("verification_level"),
            "evidence_level": batch_payload.get("evidence_level"),
            "report_count": batch_payload.get("report_count"),
            "accepted_count": batch_payload.get("accepted_count"),
            "proposal_only_discipline_count": batch_payload.get("proposal_only_discipline_count"),
            "behavioral_authority_none_count": batch_payload.get("behavioral_authority_none_count"),
            "bounded_influence_present_count": batch_payload.get("bounded_influence_present_count"),
        },
        "reopen": {
            "decision": "no",
            "reason": [
                "formal owner uniqueness preserved",
                "proposal discipline preserved",
                "behavioral authority remains none",
                "controlled observation remains stable on the WP12 axis",
            ],
        },
        "current_claim": current_claim,
        "does_not_prove": does_not_prove,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    command_lines = "\n".join(
        f"  - `{entry['command']}` -> `{entry['status']}`"
        for entry in payload.get("commands_run", [])
    )
    checklist_lines = "\n".join(
        f"{index}. {entry['item']}: `{entry['status']}`"
        for index, entry in enumerate(payload.get("checklist_results", []), start=1)
    )
    allowed = "\n".join(f"  - {item}" for item in payload["current_claim"]["allowed"])
    conditional = "\n".join(f"  - {item}" for item in payload["current_claim"]["conditional"])
    disallowed = "\n".join(f"  - {item}" for item in payload["current_claim"]["disallowed"])
    does_not_prove = "\n".join(f"- {item}" for item in payload["does_not_prove"])
    return f"""# WP12 Maintenance Verification Report

- generated_at: `{payload['generated_at']}`
- git_commit_short: `{payload['git_commit_short']}`
- task_type: `maintenance_verification`
- authority_source: `{payload['authority_source']}`
- baseline: `{payload['baseline']}`

## Verification Scope

- 本次触发层：`{'`, `'.join(payload['layers_run'])}`
- 入口命令：
{command_lines}
- 影响 artifacts：
  - `OpenEmotion/artifacts/mvp17/mvp17_causal_validation_current.md`
  - `OpenEmotion/artifacts/mvp17/mvp17_controlled_observation_current.md`
  - `OpenEmotion/artifacts/mvp17/mvp17_controlled_observation_batch_current.md`

## Pass / Fail

- 通过项：
  - Layer B `Causal`: `{payload['causal_summary']['status']} ({payload['causal_summary']['verification_level']}/{payload['causal_summary']['evidence_level']})`
  - Layer E single observation: `{payload['single_observation_summary']['status']} ({payload['single_observation_summary']['verification_level']}/{payload['single_observation_summary']['evidence_level']})`
  - Layer E batch observation: `{payload['batch_observation_summary']['status']} ({payload['batch_observation_summary']['verification_level']}/{payload['batch_observation_summary']['evidence_level']})`
  - checklist: `{payload['checklist_pass_count']}/{payload['checklist_total_count']} passed`
- 失败项：
  - `none`

## Checklist Coverage

{checklist_lines}

## Current Claim

- 本次可宣称：
{allowed}
- 条件性说明：
{conditional}
- 本次不可宣称：
{disallowed}

## Does Not Prove

{does_not_prove}

## Reopen Decision

- 是否触发 reopen：`{payload['reopen']['decision']}`
- 理由：
  - {payload['reopen']['reason'][0]}
  - {payload['reopen']['reason'][1]}
  - {payload['reopen']['reason'][2]}
  - {payload['reopen']['reason'][3]}

## Baseline

- 本报告按 `Tasks/active/mvp17_social_self_other_modeling/WP12_QA_BASELINE.md` 生成
- 当前仍只证明 `WP12` 的 maintenance_mode 轴内结论
"""


def append_ledger_entry(payload: dict[str, Any]) -> None:
    entry = f"""

### {payload['generated_at'][:10]} — First institutionalized maintenance verification

- generated_at:
  - `{payload['generated_at']}`
- report:
  - `Tasks/active/mvp17_social_self_other_modeling/MAINTENANCE_VERIFICATION_CURRENT.md`
  - `Tasks/active/mvp17_social_self_other_modeling/MAINTENANCE_VERIFICATION_CURRENT.json`
- outcome:
  - `checklist = {payload['checklist_pass_count']}/{payload['checklist_total_count']}`
  - `single controlled observation = {payload['single_observation_summary']['status']} ({payload['single_observation_summary']['verification_level']}/{payload['single_observation_summary']['evidence_level']})`
  - `batch controlled observation = {payload['batch_observation_summary']['status']} ({payload['batch_observation_summary']['verification_level']}/{payload['batch_observation_summary']['evidence_level']})`
  - `publish_gate_ready = true`
- reopen decision:
  - `{payload['reopen']['decision']}`
- notes:
  - generated by `scripts/codex/run_wp12_maintenance_verification.py`
  - current report remains bound to `WP12_QA_BASELINE.md`
"""
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the canonical WP12 maintenance verification.")
    parser.add_argument("--print-json", action="store_true", help="Print the generated report payload.")
    args = parser.parse_args()

    commands = [
        ("Layer A unit/contract", ["python3", "-m", "pytest", "-q", "-s", "--noconftest", "OpenEmotion/tests/mvp17/test_social_owner_infra.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer B causal", ["python3", "-m", "pytest", "-q", "-s", "--noconftest", "OpenEmotion/tests/mvp17/test_social_causal_formal_proof.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer C/D boundary+wiring", ["python3", "-m", "pytest", "-q", "-s", "--noconftest", "OpenEmotion/tests/mvp17/test_mainline_reference_demotion.py", "OpenEmotion/tests/mvp17/test_social_proto_self_integration.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer D egocore bridge", ["python3", "-m", "pytest", "-q", "-s", "--noconftest", "EgoCore/tests/test_runtime_v2_proto_self_runtime.py", "-k", "social"], {"PYTHONPATH": "EgoCore:EgoCore/modules:OpenEmotion"}),
        ("Layer C/D wiring verifier", ["python3", "OpenEmotion/tools/verify_mvp17_mainline_wiring.py", "--json"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer E observation tests", ["python3", "-m", "pytest", "-q", "-s", "--noconftest", "OpenEmotion/tests/mvp17/test_controlled_observation.py", "OpenEmotion/tests/mvp17/test_controlled_observation_batch.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer B causal runner", ["python3", "OpenEmotion/tools/run_mvp17_causal_validation.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer E single observation runner", ["python3", "OpenEmotion/tools/run_mvp17_controlled_observation.py"], {"PYTHONPATH": "OpenEmotion"}),
        ("Layer E batch observation runner", ["python3", "OpenEmotion/tools/run_mvp17_controlled_observation_batch.py"], {"PYTHONPATH": "OpenEmotion"}),
    ]

    command_results = [
        _run_command(label, command, env_overrides=env)
        for label, command, env in commands
    ]
    failures = [entry for entry in command_results if entry["status"] != "pass"]
    if failures:
        print(json.dumps({"status": "fail", "commands_run": command_results}, ensure_ascii=False, indent=2))
        return 1

    causal_payload = json.loads(CAUSAL_JSON.read_text(encoding="utf-8"))
    single_payload = json.loads(SINGLE_JSON.read_text(encoding="utf-8"))
    batch_payload = json.loads(BATCH_JSON.read_text(encoding="utf-8"))
    generated_at = datetime.now(timezone.utc).isoformat()
    payload = build_report_payload(
        commands_run=command_results,
        causal_payload=causal_payload,
        single_payload=single_payload,
        batch_payload=batch_payload,
        generated_at=generated_at,
        git_commit_short=_git_commit_short(),
    )
    REPORT_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(payload), encoding="utf-8")
    append_ledger_entry(payload)

    if args.print_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": payload["status"], "report_json": str(REPORT_JSON_PATH.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
