#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import fnmatch
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "e4-shadow-h1-formal-mainline-sampling"
REPORTS_DIR = ROOT / "artifacts" / "telegram_real_mainline_v1" / "reports"
REAL_TELEGRAM_DIR = ROOT / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
LIVE_PROCESS_VERSION_PATH = ROOT / "EgoCore" / "artifacts" / "proto_self_v2" / "LIVE_TELEGRAM_PROCESS_VERSION.json"
FROZEN_SAMPLE_MATRIX_PATH = TASK_DIR / "FROZEN_SAMPLE_MATRIX.json"

ALLOWED_RUNTIME_DIRTY_PATHS = {
    "EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json",
    "EgoCore/logs/egocore_err.log",
    "EgoCore/logs/egocore_run.log",
    "EgoCore/logs/telegram_launcher_meta.json",
}

ALLOWED_RUNTIME_DIRTY_PATTERNS = [
    "OpenEmotion/artifacts/mvp19/**/formal_selfhood_integration/openemotion/selfhood_integration_revisions.jsonl",
    "OpenEmotion/artifacts/mvp19/**/formal_selfhood_integration/openemotion/selfhood_integration_state.json",
    "OpenEmotion/artifacts/mvp21/**/formal_initiative_realization/openemotion/initiative_realization_revisions.jsonl",
    "OpenEmotion/artifacts/mvp21/**/formal_initiative_realization/openemotion/initiative_realization_state.json",
]

PREFLIGHT_REPORT_JSON = REPORTS_DIR / "H1_E4_PREFLIGHT_CURRENT.json"
PREFLIGHT_REPORT_MD = REPORTS_DIR / "H1_E4_PREFLIGHT_CURRENT.md"
CAUSALITY_EXCLUSION_JSON = REPORTS_DIR / "H1_E4_CAUSALITY_EXCLUSION_CURRENT.json"
CAUSALITY_EXCLUSION_MD = REPORTS_DIR / "H1_E4_CAUSALITY_EXCLUSION_CURRENT.md"
SAMPLE_MANIFEST_JSON = REPORTS_DIR / "H1_E4_SAMPLE_MANIFEST_CURRENT.json"
SAMPLE_MANIFEST_MD = REPORTS_DIR / "H1_E4_SAMPLE_MANIFEST_CURRENT.md"
APPEARANCE_REPORT_JSON = REPORTS_DIR / "H1_E4_SHADOW_APPEARANCE_REPORT_CURRENT.json"
APPEARANCE_REPORT_MD = REPORTS_DIR / "H1_E4_SHADOW_APPEARANCE_REPORT_CURRENT.md"
FAILURES_TABLE_JSON = REPORTS_DIR / "H1_E4_FAILURES_TABLE_CURRENT.json"
FAILURES_TABLE_MD = REPORTS_DIR / "H1_E4_FAILURES_TABLE_CURRENT.md"
SAMPLE_LEVEL_REPORT_JSON = REPORTS_DIR / "H1_E4_SAMPLE_LEVEL_REPORT_CURRENT.json"
SAMPLE_LEVEL_REPORT_MD = REPORTS_DIR / "H1_E4_SAMPLE_LEVEL_REPORT_CURRENT.md"

REQUIRED_SAMPLE_FILES = [
    "raw_update.json",
    "normalized_event.json",
    "openemotion_result.json",
    "response_plan.json",
    "outbox_record.json",
    "timeline.json",
    "tape.json",
    "replay.json",
]

KNOWN_FULL_GATE_RESIDUALS = [
    {
        "surface": "dashboard_flow_detail",
        "category": "derived_only_non_blocking",
        "source": "tests/test_dashboard_server.py::*flow_detail*",
        "why": "dashboard_v1 is a derived index and not the authority source for H1 E4 sample admission.",
    },
    {
        "surface": "developmental_writeback",
        "category": "historical_unrelated",
        "source": "tests/test_developmental_writeback.py::test_real_telegram_mainline_turn_writes_developmental_projection",
        "why": "developmental_writeback is outside the shadow_h1 telemetry-only sampling claim.",
    },
    {
        "surface": "doc_system_inventory_builder",
        "category": "historical_unrelated",
        "source": "tests/test_doc_system_inventory_builder.py::test_doc_system_inventory_builder_generates_key_outputs",
        "why": "doc inventory generation does not affect Telegram E4 sample bundle authority.",
    },
]


@dataclass
class SampleBundle:
    sample_id: str
    sample_dir: Path
    timestamp: Optional[str]
    raw_text: str
    session_id: Optional[str]
    file_status: Dict[str, bool]
    is_complete: bool
    raw_update: Dict[str, Any]
    normalized_event: Dict[str, Any]
    openemotion_result: Dict[str, Any]
    response_plan: Dict[str, Any]
    outbox_record: Dict[str, Any]
    timeline: Any
    tape: Dict[str, Any]
    replay: Dict[str, Any]
    ledger: Dict[str, Any]

    def artifact_refs(self) -> Dict[str, str]:
        refs = {"sample_dir": rel_path(self.sample_dir)}
        for filename in (
            "ledger.json",
            "raw_update.json",
            "normalized_event.json",
            "openemotion_result.json",
            "openemotion_trace.json",
            "response_plan.json",
            "outbox_record.json",
            "timeline.json",
            "tape.json",
            "replay.json",
            "summary.md",
            "sample.json",
        ):
            path = self.sample_dir / filename
            refs[filename.replace(".json", "").replace(".md", "")] = rel_path(path) if path.exists() else None
        return refs


def now_iso() -> str:
    return datetime.now().isoformat()


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return read_json(path)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolve_sampling_source_root(
    *,
    explicit_repo_root: Optional[Path] = None,
    preflight_payload: Optional[Dict[str, Any]] = None,
) -> Path:
    if explicit_repo_root is not None:
        return explicit_repo_root.resolve()
    payload = preflight_payload or {}
    evaluated = payload.get("evaluated_repo_root")
    if payload.get("decision") == "continue" and isinstance(evaluated, str) and evaluated.strip():
        candidate = Path(evaluated).resolve()
        if candidate.exists():
            return candidate
    return ROOT


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def git_output(args: Iterable[str], *, repo_root: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def git_head_short(*, repo_root: Path = ROOT) -> str:
    return git_output(["rev-parse", "--short", "HEAD"], repo_root=repo_root) or "unknown"


def git_dirty_paths(*, tracked_only: bool = True, repo_root: Path = ROOT) -> List[str]:
    args = ["status", "--short"]
    if tracked_only:
        args.append("--untracked-files=no")
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    output = completed.stdout
    rows: List[str] = []
    for line in output.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        path = line[3:] if len(line) > 3 else line
        rows.append(path)
    return rows


def classify_tracked_dirty_paths(paths: List[str]) -> Dict[str, List[str]]:
    def is_allowed(path: str) -> bool:
        if path in ALLOWED_RUNTIME_DIRTY_PATHS:
            return True
        return any(fnmatch.fnmatch(path, pattern) for pattern in ALLOWED_RUNTIME_DIRTY_PATTERNS)

    allowed_runtime = [path for path in paths if is_allowed(path)]
    unexpected = [path for path in paths if not is_allowed(path)]
    return {
        "allowed_runtime_dirty_paths": allowed_runtime,
        "unexpected_tracked_dirty_paths": unexpected,
    }


def parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def load_live_process_version(path: Path = LIVE_PROCESS_VERSION_PATH) -> Dict[str, Any]:
    return read_optional_json(path)


def load_frozen_sample_matrix(path: Path = FROZEN_SAMPLE_MATRIX_PATH) -> Dict[str, Any]:
    return read_json(path)


def iter_sample_dirs(real_dir: Path = REAL_TELEGRAM_DIR) -> List[Path]:
    if not real_dir.exists():
        return []
    return sorted(
        [path for path in real_dir.iterdir() if path.is_dir() and path.name.startswith("sample_")],
        key=lambda item: item.name,
    )


def load_sample_bundle(sample_dir: Path) -> SampleBundle:
    raw_update = read_optional_json(sample_dir / "raw_update.json")
    normalized_event = read_optional_json(sample_dir / "normalized_event.json")
    openemotion_result = read_optional_json(sample_dir / "openemotion_result.json")
    response_plan = read_optional_json(sample_dir / "response_plan.json")
    outbox_record = read_optional_json(sample_dir / "outbox_record.json")
    timeline = read_optional_json(sample_dir / "timeline.json")
    tape = read_optional_json(sample_dir / "tape.json")
    replay = read_optional_json(sample_dir / "replay.json")
    ledger = read_optional_json(sample_dir / "ledger.json")
    file_status = {name: (sample_dir / name).exists() for name in REQUIRED_SAMPLE_FILES}
    message = raw_update.get("message") or {}
    context = normalized_event.get("conversation_context") or {}
    timestamp = (
        ledger.get("timestamp")
        or tape.get("timestamp")
        or context.get("timestamp")
        or raw_update.get("timestamp")
    )
    return SampleBundle(
        sample_id=sample_dir.name,
        sample_dir=sample_dir,
        timestamp=timestamp,
        raw_text=str(message.get("text") or ""),
        session_id=context.get("session_id") or (ledger.get("ids") or {}).get("session_id"),
        file_status=file_status,
        is_complete=all(file_status.values()),
        raw_update=raw_update,
        normalized_event=normalized_event,
        openemotion_result=openemotion_result,
        response_plan=response_plan,
        outbox_record=outbox_record,
        timeline=timeline,
        tape=tape,
        replay=replay,
        ledger=ledger,
    )


def load_sample_bundles(real_dir: Path = REAL_TELEGRAM_DIR) -> List[SampleBundle]:
    return [load_sample_bundle(path) for path in iter_sample_dirs(real_dir)]


def extract_shadow_h1(bundle: SampleBundle) -> Dict[str, Any]:
    trace_payload = dict(bundle.openemotion_result.get("trace_payload") or {})
    confidence_meta = dict(bundle.openemotion_result.get("confidence_meta") or {})
    shadow = dict(trace_payload.get("shadow_h1") or {})
    if not shadow and confidence_meta.get("shadow_h1_enabled"):
        shadow = {
            "enabled": True,
            "action_key": confidence_meta.get("shadow_h1_action_key"),
            "predicted_success": confidence_meta.get("shadow_h1_predicted_success"),
            "threshold": confidence_meta.get("shadow_h1_threshold"),
            "would_guard": confidence_meta.get("shadow_h1_would_guard"),
            "would_ask": confidence_meta.get("shadow_h1_would_ask"),
            "source": "confidence_meta_fallback",
        }
    return shadow


def shadow_h1_presence(bundle: SampleBundle) -> Dict[str, Any]:
    shadow = extract_shadow_h1(bundle)
    policy_hint = dict(bundle.openemotion_result.get("policy_hint") or {})
    response_tendency = dict(bundle.openemotion_result.get("response_tendency") or {})
    return {
        "present": bool(shadow),
        "action_key": shadow.get("action_key"),
        "predicted_success": shadow.get("predicted_success"),
        "threshold": shadow.get("threshold"),
        "would_guard": shadow.get("would_guard"),
        "would_ask": shadow.get("would_ask"),
        "source": shadow.get("source"),
        "policy_hint_ask_preferred": policy_hint.get("ask_preferred"),
        "response_tendency_ask_needed": response_tendency.get("ask_needed"),
        "response_plan_status": bundle.response_plan.get("status"),
        "delivery_kind": bundle.response_plan.get("delivery_kind"),
        "outbox_success": bundle.outbox_record.get("success"),
    }


def build_preflight_payload(
    *,
    sample_matrix: Dict[str, Any],
    head_short: str,
    dirty_paths: List[str],
    live_process_version: Dict[str, Any],
    targeted_checks: List[Dict[str, Any]],
    repo_root_ref: Optional[str] = None,
    live_process_version_ref: Optional[str] = None,
) -> Dict[str, Any]:
    live_commit = str(live_process_version.get("git_commit_short") or "")
    live_dirty = bool(live_process_version.get("git_dirty"))
    dirty_classification = classify_tracked_dirty_paths(dirty_paths)
    allowed_runtime_dirty_paths = dirty_classification["allowed_runtime_dirty_paths"]
    unexpected_tracked_dirty_paths = dirty_classification["unexpected_tracked_dirty_paths"]
    live_process_ok = (
        bool(live_process_version)
        and live_process_version.get("process_kind") == "telegram"
        and live_commit == head_short
        and not live_dirty
    )
    workspace_clean = not unexpected_tracked_dirty_paths

    rows = list(sample_matrix.get("rows") or [])
    positive_rows = [row for row in rows if not row.get("negative_control")]
    requires_native_loop = any("native_loop" in (row.get("expected_path") or []) for row in positive_rows)
    requires_runtime_observation = any("runtime_observation" in (row.get("expected_path") or []) for row in positive_rows)

    checks_by_name = {item["name"]: item for item in targeted_checks}
    surface_records: List[Dict[str, Any]] = []

    if requires_native_loop:
        native_check = checks_by_name.get("native_path_surface")
        native_failed = native_check is None or native_check.get("status") != "passed"
        surface_records.append(
            {
                "surface": "native_loop",
                "category": "same_surface_blocking" if native_failed else "same_surface_cleared",
                "source": "targeted_check:native_path_surface",
                "why": (
                    "positive H1 sample rows require explicit-path execute turns that route through native_loop."
                    if native_failed
                    else "current scoped native path checks passed for the frozen H1-positive sample families."
                ),
            }
        )
    if requires_runtime_observation:
        observation_check = checks_by_name.get("runtime_mainline_observation")
        observation_failed = observation_check is None or observation_check.get("status") != "passed"
        surface_records.append(
            {
                "surface": "runtime_observation",
                "category": "same_surface_blocking" if observation_failed else "same_surface_cleared",
                "source": "targeted_check:runtime_mainline_observation",
                "why": (
                    "sample admission relies on the formal observation bundle contract and the current check is failing."
                    if observation_failed
                    else "current observation record construction and H1 hook checks passed."
                ),
            }
        )
    surface_records.extend(KNOWN_FULL_GATE_RESIDUALS)

    targeted_failures = [item for item in targeted_checks if item.get("status") != "passed"]
    contamination_detected = any(record["category"] == "same_surface_blocking" for record in surface_records)
    clean_bind_ready = workspace_clean and live_process_ok

    decision = "continue"
    blocker_reason = None
    report_kind = "preflight"
    if contamination_detected:
        decision = "close"
        blocker_reason = "same_surface_contamination_detected"
        report_kind = "causality_exclusion"
    elif not clean_bind_ready:
        decision = "close"
        blocker_reason = "clean_bind_not_ready"
    elif targeted_failures:
        decision = "close"
        blocker_reason = "targeted_checks_failed"

    return {
        "schema_version": "h1_e4_sampling.preflight.v1",
        "generated_at": now_iso(),
        "binding_mode": sample_matrix.get("binding_mode") or "require_clean_commit",
        "task_slug": "e4-shadow-h1-formal-mainline-sampling",
        "evaluated_repo_root": repo_root_ref or rel_path(ROOT),
        "head_git_commit_short": head_short,
        "tracked_dirty_paths": dirty_paths,
        "allowed_runtime_dirty_paths": allowed_runtime_dirty_paths,
        "unexpected_tracked_dirty_paths": unexpected_tracked_dirty_paths,
        "workspace_clean": workspace_clean,
        "live_process_version_ref": live_process_version_ref or rel_path(LIVE_PROCESS_VERSION_PATH),
        "live_process_version": live_process_version,
        "live_process_ok": live_process_ok,
        "clean_bind_ready": clean_bind_ready,
        "targeted_checks": targeted_checks,
        "surface_classification": {
            "requires_native_loop": requires_native_loop,
            "requires_runtime_observation": requires_runtime_observation,
            "records": surface_records,
            "contamination_detected": contamination_detected,
        },
        "decision": decision,
        "blocker_reason": blocker_reason,
        "report_kind": report_kind,
    }


def render_preflight_markdown(payload: Dict[str, Any]) -> str:
    live = dict(payload.get("live_process_version") or {})
    surface_rows = []
    for item in payload.get("surface_classification", {}).get("records", []):
        surface_rows.append(
            f"| `{item['surface']}` | `{item['category']}` | `{item['source']}` | {item['why']} |"
        )
    check_rows = []
    for item in payload.get("targeted_checks", []):
        check_rows.append(
            f"| `{item['name']}` | `{item['status']}` | `{item['command']}` | {item.get('note') or ''} |"
        )
    dirty_rows = "\n".join(f"- `{path}`" for path in payload.get("tracked_dirty_paths", [])) or "- none"
    allowed_dirty_rows = "\n".join(f"- `{path}`" for path in payload.get("allowed_runtime_dirty_paths", [])) or "- none"
    unexpected_dirty_rows = "\n".join(f"- `{path}`" for path in payload.get("unexpected_tracked_dirty_paths", [])) or "- none"
    return f"""# H1 E4 Sampling Preflight

- generated_at: `{payload['generated_at']}`
- binding_mode: `{payload['binding_mode']}`
- decision: `{payload['decision']}`
- blocker_reason: `{payload.get('blocker_reason') or 'none'}`

## Live Binding

- repo HEAD: `{payload['head_git_commit_short']}`
- live process ref: `{payload['live_process_version_ref']}`
- live process commit: `{live.get('git_commit_short') or 'unknown'}`
- live process git_dirty: `{live.get('git_dirty')}`
- workspace_clean: `{payload['workspace_clean']}`
- live_process_ok: `{payload['live_process_ok']}`
- clean_bind_ready: `{payload['clean_bind_ready']}`

Tracked dirty paths:
{dirty_rows}

Allowed runtime-generated dirty paths:
{allowed_dirty_rows}

Unexpected tracked dirty paths:
{unexpected_dirty_rows}

## Targeted Checks

| check | status | command | note |
|---|---|---|---|
{chr(10).join(check_rows) if check_rows else '| none | skipped | n/a | n/a |'}

## Surface Classification

| surface | category | source | why |
|---|---|---|---|
{chr(10).join(surface_rows)}

## Conclusion

- current ceiling: `preflight only`
- not proven:
  - `runtime efficacy`
  - `repo-level enablement`
  - `live decision promotion`
- next action: `{'collect bounded real samples' if payload['decision'] == 'continue' else 'stop and fix preflight blocker or produce causality exclusion review'}`
"""


def _bundle_sort_key(bundle: SampleBundle) -> tuple[int, str]:
    parsed = parse_iso8601(bundle.timestamp)
    if parsed is None:
        return (0, bundle.sample_id)
    return (1, parsed.isoformat())


def _prompt_hash(text: str) -> str:
    return short_hash(text.strip())


def build_sample_manifest_payload(
    *,
    sample_matrix: Dict[str, Any],
    bundles: List[SampleBundle],
    live_process_version: Dict[str, Any],
) -> Dict[str, Any]:
    observed_after = parse_iso8601(live_process_version.get("observed_at"))
    filtered_bundles: List[SampleBundle] = []
    for bundle in bundles:
        bundle_ts = parse_iso8601(bundle.timestamp)
        if observed_after is not None and bundle_ts is not None and bundle_ts < observed_after:
            continue
        filtered_bundles.append(bundle)

    rows_payload: List[Dict[str, Any]] = []
    summary = {"expected_rows": 0, "matched_complete": 0, "matched_incomplete": 0, "missing": 0, "ambiguous": 0}

    for row in sample_matrix.get("rows") or []:
        summary["expected_rows"] += 1
        prompt_text = str(row.get("prompt_text") or "")
        prompt_hash = _prompt_hash(prompt_text)
        candidates = [bundle for bundle in filtered_bundles if _prompt_hash(bundle.raw_text) == prompt_hash]
        candidates = sorted(candidates, key=_bundle_sort_key)
        status = "missing"
        matched: Optional[SampleBundle] = None
        reason = "no post-bind sample matched frozen prompt text"
        if len(candidates) == 1:
            matched = candidates[0]
            if matched.is_complete:
                status = "matched_complete"
                reason = "exact prompt-text match and complete E4 bundle"
                summary["matched_complete"] += 1
            else:
                status = "matched_incomplete"
                reason = "exact prompt-text match but required E4 files are missing"
                summary["matched_incomplete"] += 1
        elif len(candidates) > 1:
            status = "ambiguous"
            reason = "multiple post-bind samples matched the same frozen prompt text"
            summary["ambiguous"] += 1
        else:
            summary["missing"] += 1

        rows_payload.append(
            {
                "manifest_id": row.get("manifest_id"),
                "bucket": row.get("bucket"),
                "negative_control": bool(row.get("negative_control")),
                "prompt_text_hash": prompt_hash,
                "status": status,
                "reason": reason,
                "expected_path": list(row.get("expected_path") or []),
                "expected_action_key": row.get("expected_action_key"),
                "expected_shadow_mode": row.get("expected_shadow_mode"),
                "matched_sample_id": matched.sample_id if matched else None,
                "matched_sample_timestamp": matched.timestamp if matched else None,
                "artifact_refs": matched.artifact_refs() if matched else {},
                "matched_shadow_h1": shadow_h1_presence(matched) if matched else {},
                "missing_files": [name for name, present in matched.file_status.items() if not present] if matched else [],
            }
        )

    return {
        "schema_version": "h1_e4.sample_manifest.v1",
        "generated_at": now_iso(),
        "binding_mode": sample_matrix.get("binding_mode") or "require_clean_commit",
        "process_observed_at": live_process_version.get("observed_at"),
        "process_commit_short": live_process_version.get("git_commit_short"),
        "rows": rows_payload,
        "summary": summary,
    }


def render_sample_manifest_markdown(payload: Dict[str, Any]) -> str:
    row_lines = []
    for item in payload.get("rows", []):
        row_lines.append(
            "| `{manifest_id}` | `{bucket}` | `{status}` | `{matched}` | {reason} |".format(
                manifest_id=item["manifest_id"],
                bucket=item["bucket"],
                status=item["status"],
                matched=item.get("matched_sample_id") or "none",
                reason=item["reason"],
            )
        )
    summary = payload.get("summary") or {}
    return f"""# H1 E4 Sample Manifest

- generated_at: `{payload['generated_at']}`
- process_observed_at: `{payload.get('process_observed_at') or 'unknown'}`
- process_commit_short: `{payload.get('process_commit_short') or 'unknown'}`

## Summary

- expected_rows: `{summary.get('expected_rows', 0)}`
- matched_complete: `{summary.get('matched_complete', 0)}`
- matched_incomplete: `{summary.get('matched_incomplete', 0)}`
- missing: `{summary.get('missing', 0)}`
- ambiguous: `{summary.get('ambiguous', 0)}`

## Rows

| manifest_id | bucket | status | matched_sample | reason |
|---|---|---|---|---|
{chr(10).join(row_lines) if row_lines else '| none | none | none | none | none |'}
"""


def build_appearance_payload(manifest_payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    summary = {
        "matched_samples": 0,
        "shadow_present": 0,
        "guard_true_count": 0,
        "negative_control_shadow_count": 0,
        "live_policy_promoted_count": 0,
    }
    for item in manifest_payload.get("rows", []):
        if item.get("status") not in {"matched_complete", "matched_incomplete"}:
            continue
        summary["matched_samples"] += 1
        shadow = dict(item.get("matched_shadow_h1") or {})
        present = bool(shadow.get("present"))
        if present:
            summary["shadow_present"] += 1
        if shadow.get("would_guard") is True:
            summary["guard_true_count"] += 1
        if item.get("negative_control") and present:
            summary["negative_control_shadow_count"] += 1
        if shadow.get("policy_hint_ask_preferred") or shadow.get("response_tendency_ask_needed"):
            summary["live_policy_promoted_count"] += 1
        rows.append(
            {
                "manifest_id": item.get("manifest_id"),
                "sample_id": item.get("matched_sample_id"),
                "bucket": item.get("bucket"),
                "negative_control": item.get("negative_control"),
                "shadow_h1": shadow,
                "why_scored": (
                    "matched sample provides canonical shadow_h1 telemetry from openemotion_result.trace_payload/confidence_meta"
                    if present
                    else "matched sample has no canonical shadow_h1 telemetry"
                ),
            }
        )
    return {
        "schema_version": "h1_e4.shadow_appearance.v1",
        "generated_at": now_iso(),
        "summary": summary,
        "rows": rows,
    }


def render_appearance_markdown(payload: Dict[str, Any]) -> str:
    row_lines = []
    for item in payload.get("rows", []):
        shadow = dict(item.get("shadow_h1") or {})
        row_lines.append(
            "| `{manifest_id}` | `{sample_id}` | `{present}` | `{action_key}` | `{would_guard}` | `{policy}` | {why} |".format(
                manifest_id=item["manifest_id"],
                sample_id=item["sample_id"],
                present=shadow.get("present"),
                action_key=shadow.get("action_key"),
                would_guard=shadow.get("would_guard"),
                policy=shadow.get("policy_hint_ask_preferred"),
                why=item["why_scored"],
            )
        )
    summary = payload.get("summary") or {}
    return f"""# H1 E4 Shadow Appearance Report

- generated_at: `{payload['generated_at']}`
- matched_samples: `{summary.get('matched_samples', 0)}`
- shadow_present: `{summary.get('shadow_present', 0)}`
- guard_true_count: `{summary.get('guard_true_count', 0)}`
- negative_control_shadow_count: `{summary.get('negative_control_shadow_count', 0)}`
- live_policy_promoted_count: `{summary.get('live_policy_promoted_count', 0)}`

| manifest_id | sample_id | shadow_present | action_key | would_guard | policy_hint.ask_preferred | why_scored |
|---|---|---|---|---|---|---|
{chr(10).join(row_lines) if row_lines else '| none | none | false | none | false | false | no matched samples |'}
"""


def build_failures_payload(manifest_payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in manifest_payload.get("rows", []):
        status = item.get("status")
        shadow = dict(item.get("matched_shadow_h1") or {})
        if status == "missing":
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "missing_sample",
                    "status": status,
                    "sample_id": None,
                    "why": item.get("reason"),
                }
            )
            continue
        if status == "ambiguous":
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "sample_match_ambiguous",
                    "status": status,
                    "sample_id": None,
                    "why": item.get("reason"),
                }
            )
            continue
        if status == "matched_incomplete":
            missing = list(item.get("missing_files") or [])
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "delivery_missing" if "outbox_record.json" in missing else "evidence_incomplete",
                    "status": status,
                    "sample_id": item.get("matched_sample_id"),
                    "why": f"missing files: {', '.join(missing)}",
                }
            )
        if item.get("negative_control") and shadow.get("present"):
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "shadow_h1_unexpected_on_negative_control",
                    "status": status,
                    "sample_id": item.get("matched_sample_id"),
                    "why": "negative control produced shadow_h1 telemetry",
                }
            )
        expected_mode = item.get("expected_shadow_mode")
        if expected_mode in {"guard_true", "present"} and not shadow.get("present"):
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "shadow_h1_missing_when_expected",
                    "status": status,
                    "sample_id": item.get("matched_sample_id"),
                    "why": "expected canonical shadow_h1 telemetry is absent from the matched sample",
                }
            )
        if expected_mode == "guard_true" and shadow.get("present") and shadow.get("would_guard") is not True:
            rows.append(
                {
                    "manifest_id": item.get("manifest_id"),
                    "cause_classification": "shadow_h1_guard_false_when_expected_true",
                    "status": status,
                    "sample_id": item.get("matched_sample_id"),
                    "why": "shadow_h1 is present but does not mark would_guard=true on a positive guard sample",
                }
            )
        if status in {"matched_complete", "matched_incomplete"} and not shadow.get("present"):
            if not item.get("negative_control") and not item.get("artifact_refs", {}).get("openemotion_result"):
                rows.append(
                    {
                        "manifest_id": item.get("manifest_id"),
                        "cause_classification": "host_only_interception",
                        "status": status,
                        "sample_id": item.get("matched_sample_id"),
                        "why": "matched sample did not preserve a usable OpenEmotion structured output for H1 review",
                    }
                )
    return {
        "schema_version": "h1_e4.failures_table.v1",
        "generated_at": now_iso(),
        "rows": rows,
        "summary": {
            "failure_count": len(rows),
            "classifications": _counter_to_dict(row["cause_classification"] for row in rows),
        },
    }


def render_failures_markdown(payload: Dict[str, Any]) -> str:
    row_lines = []
    for item in payload.get("rows", []):
        row_lines.append(
            f"| `{item['manifest_id']}` | `{item['cause_classification']}` | `{item.get('sample_id') or 'none'}` | {item['why']} |"
        )
    return f"""# H1 E4 Failures Table

- generated_at: `{payload['generated_at']}`
- failure_count: `{payload.get('summary', {}).get('failure_count', 0)}`

| manifest_id | cause_classification | sample_id | why |
|---|---|---|---|
{chr(10).join(row_lines) if row_lines else '| none | none | none | none |'}
"""


def _counter_to_dict(values: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_final_sample_report(
    *,
    preflight_payload: Dict[str, Any],
    manifest_payload: Dict[str, Any],
    appearance_payload: Dict[str, Any],
    failures_payload: Dict[str, Any],
) -> Dict[str, Any]:
    manifest_summary = dict(manifest_payload.get("summary") or {})
    appearance_summary = dict(appearance_payload.get("summary") or {})
    failures_summary = dict(failures_payload.get("summary") or {})
    qualifying_rows = [
        row for row in manifest_payload.get("rows", [])
        if row.get("status") == "matched_complete"
    ]
    return {
        "schema_version": "h1_e4.sample_level_report.v1",
        "generated_at": now_iso(),
        "decision": (
            "sample_level_observation_ready"
            if preflight_payload.get("decision") == "continue" and not failures_summary.get("failure_count")
            else "sample_collection_blocked_or_incomplete"
        ),
        "claim_ceiling": "canonical shadow_h1 telemetry observed on the formal Telegram mainline at E4 sample level",
        "preflight_ref": rel_path(PREFLIGHT_REPORT_JSON),
        "summary": {
            "matched_complete": manifest_summary.get("matched_complete", 0),
            "matched_incomplete": manifest_summary.get("matched_incomplete", 0),
            "missing": manifest_summary.get("missing", 0),
            "ambiguous": manifest_summary.get("ambiguous", 0),
            "shadow_present": appearance_summary.get("shadow_present", 0),
            "guard_true_count": appearance_summary.get("guard_true_count", 0),
            "failure_count": failures_summary.get("failure_count", 0),
            "qualifying_sample_ids": [row.get("matched_sample_id") for row in qualifying_rows if row.get("matched_sample_id")],
        },
        "not_proven": [
            "runtime efficacy",
            "live decision promotion",
            "repo-level enablement",
            "stability / E5",
        ],
    }


def render_final_sample_markdown(payload: Dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    qualifying = "\n".join(f"- `{sample_id}`" for sample_id in summary.get("qualifying_sample_ids", [])) or "- none"
    not_proven = "\n".join(f"- {item}" for item in payload.get("not_proven", []))
    return f"""# H1 E4 Sample-Level Report

- generated_at: `{payload['generated_at']}`
- decision: `{payload['decision']}`
- claim_ceiling: `{payload['claim_ceiling']}`
- preflight_ref: `{payload['preflight_ref']}`

## Summary

- matched_complete: `{summary.get('matched_complete', 0)}`
- matched_incomplete: `{summary.get('matched_incomplete', 0)}`
- missing: `{summary.get('missing', 0)}`
- ambiguous: `{summary.get('ambiguous', 0)}`
- shadow_present: `{summary.get('shadow_present', 0)}`
- guard_true_count: `{summary.get('guard_true_count', 0)}`
- failure_count: `{summary.get('failure_count', 0)}`

Qualifying sample ids:
{qualifying}

## Not Proven

{not_proven}
"""
