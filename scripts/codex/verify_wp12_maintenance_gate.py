#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
WP12_ROOT = ROOT / "Tasks" / "active" / "mvp17_social_self_other_modeling"
DEFAULT_BASELINE = WP12_ROOT / "WP12_QA_BASELINE.md"
DEFAULT_REPORT_MD = WP12_ROOT / "MAINTENANCE_VERIFICATION_CURRENT.md"
DEFAULT_REPORT_JSON = WP12_ROOT / "MAINTENANCE_VERIFICATION_CURRENT.json"
DEFAULT_LEDGER = WP12_ROOT / "MAINTENANCE_LEDGER.md"
DEFAULT_STATUS = WP12_ROOT / "STATUS.md"
DEFAULT_README = WP12_ROOT / "README.md"

REQUIRED_BASELINE_HEADINGS = [
    "## 1. 文档定位",
    "## 2. 当前正式口径",
    "## 3. 已证实功能边界",
    "## 4. 五层测试矩阵",
    "## 5. 十项 Checklist",
    "## 6. 失败分级与 Reopen 规则",
    "## 7. 维护态允许与禁止",
    "## 8. 标准汇报模板",
    "## 9. Canonical Maintenance Commands",
    "## 10. Publish Gate",
]
REQUIRED_REPORT_FIELDS = [
    "generated_at",
    "git_commit_short",
    "authority_source",
    "baseline",
    "layers_run",
    "commands_run",
    "checklist_pass_count",
    "reopen",
    "current_claim",
    "does_not_prove",
]
MUST_NOT_PROVE = [
    "live autonomy",
    "OpenEmotion direct reply authority",
    "broader transport claims",
]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _latest_ledger_block(ledger_text: str) -> str:
    blocks = [block.strip() for block in ledger_text.split("\n### ") if block.strip()]
    if not blocks:
        return ""
    latest = blocks[-1]
    if not latest.startswith("### "):
        latest = "### " + latest
    return latest


def verify_gate(
    *,
    baseline_path: Path = DEFAULT_BASELINE,
    report_md_path: Path = DEFAULT_REPORT_MD,
    report_json_path: Path = DEFAULT_REPORT_JSON,
    ledger_path: Path = DEFAULT_LEDGER,
    status_path: Path = DEFAULT_STATUS,
    readme_path: Path = DEFAULT_README,
) -> dict[str, Any]:
    errors: list[str] = []
    baseline_text = ""
    report_md = ""
    report_json: dict[str, Any] = {}
    ledger_text = ""
    status_text = ""
    readme_text = ""

    for path in [baseline_path, report_md_path, report_json_path, ledger_path, status_path, readme_path]:
        if not path.exists():
            errors.append(f"missing required file: {_display_path(path)}")

    if not errors:
        baseline_text = _read_text(baseline_path)
        report_md = _read_text(report_md_path)
        report_json = _load_json(report_json_path)
        ledger_text = _read_text(ledger_path)
        status_text = _read_text(status_path)
        readme_text = _read_text(readme_path)

    baseline_sections_ok = True
    if baseline_text:
        missing = [heading for heading in REQUIRED_BASELINE_HEADINGS if heading not in baseline_text]
        if missing:
            baseline_sections_ok = False
            errors.append(f"baseline missing headings: {missing}")

    current_report_ok = True
    if report_json:
        missing = [field for field in REQUIRED_REPORT_FIELDS if field not in report_json]
        if missing:
            current_report_ok = False
            errors.append(f"report json missing fields: {missing}")
        if report_json.get("baseline") != _display_path(baseline_path):
            current_report_ok = False
            errors.append("report baseline path mismatch")
        if report_json.get("status") != "pass":
            current_report_ok = False
            errors.append("report status is not pass")
        if report_json.get("checklist_pass_count") != 10:
            current_report_ok = False
            errors.append("checklist_pass_count is not 10")
        if dict(report_json.get("reopen") or {}).get("decision") != "no":
            current_report_ok = False
            errors.append("reopen decision is not no")
    else:
        current_report_ok = False

    claim_ceiling_ok = True
    if report_json:
        does_not_prove = list(report_json.get("does_not_prove") or [])
        current_claim = dict(report_json.get("current_claim") or {})
        allowed_text = json.dumps(
            {
                "allowed": current_claim.get("allowed") or [],
                "conditional": current_claim.get("conditional") or [],
            },
            ensure_ascii=False,
        )
        for phrase in MUST_NOT_PROVE:
            if phrase not in does_not_prove:
                claim_ceiling_ok = False
                errors.append(f"does_not_prove missing required phrase: {phrase}")
            if phrase in allowed_text:
                claim_ceiling_ok = False
                errors.append(f"current_claim overclaims forbidden phrase: {phrase}")
        if "maintenance_mode" not in json.dumps(current_claim, ensure_ascii=False):
            claim_ceiling_ok = False
            errors.append("current_claim does not restate maintenance_mode ceiling")
        if "WP12_QA_BASELINE.md" not in report_md:
            claim_ceiling_ok = False
            errors.append("report markdown does not cite WP12_QA_BASELINE.md")
    else:
        claim_ceiling_ok = False

    ledger_reference_ok = True
    latest_block = _latest_ledger_block(ledger_text)
    if latest_block:
        required_refs = [
            "MAINTENANCE_VERIFICATION_CURRENT.md",
            "MAINTENANCE_VERIFICATION_CURRENT.json",
        ]
        for ref in required_refs:
            if ref not in latest_block:
                ledger_reference_ok = False
                errors.append(f"latest ledger block missing reference: {ref}")
        generated_at = str(report_json.get("generated_at") or "")
        if generated_at and generated_at not in latest_block:
            ledger_reference_ok = False
            errors.append("latest ledger block does not reference current report timestamp")
    else:
        ledger_reference_ok = False
        errors.append("ledger has no entry blocks")

    publish_docs_ok = True
    docs_text = "\n".join([baseline_text, status_text, readme_text])
    if "run_wp12_maintenance_verification.py" not in docs_text:
        publish_docs_ok = False
        errors.append("WP12 docs missing canonical runner reference")
    if "verify_wp12_maintenance_gate.py --json" not in docs_text:
        publish_docs_ok = False
        errors.append("WP12 docs missing gate verifier reference")
    if "maintenance_mode" not in status_text:
        publish_docs_ok = False
        errors.append("STATUS.md no longer states maintenance_mode")

    publish_gate_ready = not errors
    return {
        "status": "pass" if publish_gate_ready else "fail",
        "baseline_path": _display_path(baseline_path),
        "report_md_path": _display_path(report_md_path),
        "report_json_path": _display_path(report_json_path),
        "ledger_path": _display_path(ledger_path),
        "baseline_sections_ok": baseline_sections_ok,
        "current_report_ok": current_report_ok,
        "ledger_reference_ok": ledger_reference_ok,
        "claim_ceiling_ok": claim_ceiling_ok,
        "publish_docs_ok": publish_docs_ok,
        "publish_gate_ready": publish_gate_ready,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the WP12 maintenance publish gate.")
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--status-file", default=str(DEFAULT_STATUS))
    parser.add_argument("--readme-file", default=str(DEFAULT_README))
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    payload = verify_gate(
        baseline_path=Path(args.baseline),
        report_md_path=Path(args.report_md),
        report_json_path=Path(args.report_json),
        ledger_path=Path(args.ledger),
        status_path=Path(args.status_file),
        readme_path=Path(args.readme_file),
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"WP12 maintenance gate: {payload['status']}")
        for key in [
            "baseline_sections_ok",
            "current_report_ok",
            "ledger_reference_ok",
            "claim_ceiling_ok",
            "publish_docs_ok",
            "publish_gate_ready",
        ]:
            print(f"- {key}: {payload[key]}")
        if payload["errors"]:
            print("- errors:")
            for entry in payload["errors"]:
                print(f"  - {entry}")
    return 0 if payload["publish_gate_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
