#!/usr/bin/env python3
"""Low-frequency GitHub issue mirror for the repo-local task board."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BOARD_PATH = ROOT / "Tasks" / "TASK_BOARD.yaml"
DEFAULT_STATE_PATH = ROOT / "artifacts" / "task_board" / "sync_state.json"
DEFAULT_LOG_PATH = ROOT / "artifacts" / "task_board" / "sync_log.jsonl"
DEFAULT_OUTBOX_PATH = ROOT / "artifacts" / "task_board" / "outbox.jsonl"
DEFAULT_REPO = "pen364692088/EGO"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import github_project_task  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


class SyncError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SyncError("yaml_unavailable", "PyYAML is required")
    if not path.exists():
        raise SyncError("missing_task_board", f"Task board not found: {path}", path=str(path))
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
        raise SyncError("invalid_task_board", "Task board must contain a tasks array", path=str(path))
    return payload


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "repo": DEFAULT_REPO, "issues": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SyncError("invalid_sync_state", f"Sync state is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise SyncError("invalid_sync_state", "Sync state must be a JSON object", path=str(path))
    payload.setdefault("issues", {})
    return payload


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def task_issue_number(task: dict[str, Any], state: dict[str, Any]) -> int | None:
    task_id = str(task.get("id") or "")
    cached = state.get("issues", {}).get(task_id)
    if isinstance(cached, dict) and cached.get("number") is not None:
        return int(cached["number"])
    refs = task.get("external_refs") if isinstance(task.get("external_refs"), dict) else {}
    url = str(refs.get("github_issue") or "")
    match = re.search(r"/issues/(\d+)", url)
    return int(match.group(1)) if match else None


def desired_issue_body(task: dict[str, Any]) -> str:
    lines = [
        "<!-- synced-from: Tasks/TASK_BOARD.yaml -->",
        "",
        "## Canonical source",
    ]
    for source in task.get("canonical_sources") or []:
        lines.append(f"- `{source}`")
    lines.extend(
        [
            "",
            "## Positive mechanism goal",
            str(task.get("next_action") or task.get("title") or ""),
            "",
            "## Local task state",
            f"- task_id: `{task.get('id')}`",
            f"- status: `{task.get('status')}`",
            f"- kind: `{task.get('kind')}`",
            f"- layer: `{task.get('layer')}`",
            f"- owner: `{task.get('owner')}`",
            f"- observation_class: `{task.get('observation_class')}`",
            f"- evidence_level: `{task.get('evidence_level')}`",
            "",
            "## Acceptance gate",
        ]
    )
    for item in task.get("acceptance") or []:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Rollback",
            str(task.get("rollback") or ""),
            "",
            "## Claim ceiling",
            f"`{task.get('claim_ceiling')}`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def desired_issue_state(task: dict[str, Any]) -> str:
    return "closed" if str(task.get("status")) == "accepted" else "open"


def build_plan(board: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    issues = state.setdefault("issues", {})
    for task in board.get("tasks") or []:
        task_id = str(task.get("id") or "")
        if not task_id:
            continue
        number = task_issue_number(task, state)
        body = desired_issue_body(task)
        body_hash = sha256_text(body)
        title = str(task.get("title") or task_id)
        desired_state = desired_issue_state(task)
        cached = issues.get(task_id) if isinstance(issues.get(task_id), dict) else {}
        if number is None:
            operations.append(
                {
                    "op": "create_issue",
                    "task_id": task_id,
                    "title": title,
                    "body_hash": body_hash,
                    "desired_state": desired_state,
                }
            )
            continue
        if cached.get("title_hash") != sha256_text(title) or cached.get("body_hash") != body_hash:
            operations.append(
                {
                    "op": "update_issue",
                    "task_id": task_id,
                    "issue": number,
                    "title": title,
                    "body_hash": body_hash,
                }
            )
        if cached.get("state") and cached.get("state") != desired_state:
            operations.append(
                {
                    "op": "set_issue_state",
                    "task_id": task_id,
                    "issue": number,
                    "desired_state": desired_state,
                }
            )
    return operations


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def write_outbox(path: Path, operations: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for operation in operations:
            handle.write(json.dumps(operation, ensure_ascii=False, sort_keys=True) + "\n")


def apply_operations(
    client: github_project_task.GhClient,
    board: dict[str, Any],
    state: dict[str, Any],
    operations: list[dict[str, Any]],
    *,
    repo: str,
    min_interval_seconds: float,
) -> list[dict[str, Any]]:
    tasks = {str(task.get("id")): task for task in board.get("tasks") or []}
    results = []
    issues = state.setdefault("issues", {})
    last_mutation = 0.0
    for operation in operations:
        elapsed = time.monotonic() - last_mutation
        if last_mutation and elapsed < min_interval_seconds:
            time.sleep(min_interval_seconds - elapsed)
        task = tasks.get(str(operation["task_id"]))
        if task is None:
            raise SyncError("task_missing_for_operation", "Operation references missing task", operation=operation)
        task_id = str(task["id"])
        body = desired_issue_body(task)
        title = str(task.get("title") or task_id)
        if operation["op"] == "create_issue":
            output = client.run(["issue", "create", "--repo", repo, "--title", title, "--body", body])
            url = next((line.strip() for line in output.splitlines() if "/issues/" in line), "")
            match = re.search(r"/issues/(\d+)", url)
            if not match:
                raise SyncError("issue_create_url_not_found", "gh issue create did not return an issue URL", raw=output)
            issue_number = int(match.group(1))
            issues[task_id] = {"number": issue_number, "url": url}
            result = {"op": "create_issue", "task_id": task_id, "issue": issue_number, "status": "ok"}
        elif operation["op"] == "update_issue":
            issue_number = int(operation["issue"])
            client.run(["issue", "edit", str(issue_number), "--repo", repo, "--title", title, "--body", body])
            issues.setdefault(task_id, {})["number"] = issue_number
            result = {"op": "update_issue", "task_id": task_id, "issue": issue_number, "status": "ok"}
        elif operation["op"] == "set_issue_state":
            issue_number = int(operation["issue"])
            verb = "close" if operation["desired_state"] == "closed" else "reopen"
            client.run(["issue", verb, str(issue_number), "--repo", repo])
            issues.setdefault(task_id, {})["state"] = operation["desired_state"]
            result = {"op": "set_issue_state", "task_id": task_id, "issue": issue_number, "status": "ok"}
        else:
            raise SyncError("unknown_sync_operation", "Unknown sync operation", operation=operation)
        issues.setdefault(task_id, {}).update(
            {
                "title_hash": sha256_text(title),
                "body_hash": sha256_text(body),
                "state": desired_issue_state(task),
            }
        )
        results.append(result)
        last_mutation = time.monotonic()
    return results


def command_doctor(args: argparse.Namespace) -> dict[str, Any]:
    board = load_yaml(Path(args.board))
    state = load_state(Path(args.state))
    return {
        "status": "ok",
        "board_path": args.board,
        "state_path": args.state,
        "task_count": len(board.get("tasks") or []),
        "cached_issue_count": len(state.get("issues") or {}),
        "github_role": "mirror",
    }


def command_plan(args: argparse.Namespace) -> dict[str, Any]:
    board = load_yaml(Path(args.board))
    state = load_state(Path(args.state))
    operations = build_plan(board, state)
    if args.write_outbox:
        write_outbox(Path(args.outbox), operations)
    return {
        "status": "ok",
        "mode": "plan",
        "operation_count": len(operations),
        "operations": operations,
        "used_cached_ids": True,
    }


def command_sync(args: argparse.Namespace, client: github_project_task.GhClient) -> dict[str, Any]:
    if args.dry_run and args.execute:
        raise SyncError("invalid_sync_mode", "Choose either --dry-run or --execute")
    board = load_yaml(Path(args.board))
    state_path = Path(args.state)
    state = load_state(state_path)
    operations = build_plan(board, state)
    write_outbox(Path(args.outbox), operations)
    log_entry: dict[str, Any] = {
        "created_at_unix": int(time.time()),
        "mode": "execute" if args.execute else "dry_run",
        "operation_count": len(operations),
        "operations": operations,
    }
    if args.execute:
        results = apply_operations(
            client,
            board,
            state,
            operations,
            repo=args.repo,
            min_interval_seconds=float(args.min_interval_seconds),
        )
        write_state(state_path, state)
        log_entry["results"] = results
    append_jsonl(Path(args.sync_log), log_entry)
    return {
        "status": "ok",
        "mode": "execute" if args.execute else "dry_run",
        "operation_count": len(operations),
        "operations": operations,
        "state_path": str(state_path),
        "outbox_path": args.outbox,
        "sync_log_path": args.sync_log,
    }


def command_import_github(args: argparse.Namespace) -> dict[str, Any]:
    state = load_state(Path(args.state))
    return {
        "status": "dry_run" if args.dry_run else "stopped",
        "mode": "import_github",
        "note": "v1 import uses cached issue refs only; full Project discovery is intentionally not a default operation.",
        "cached_issue_count": len(state.get("issues") or {}),
        "cached_issues": state.get("issues") or {},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Low-frequency GitHub mirror sync for Tasks/TASK_BOARD.yaml")
    parser.add_argument("--board", default=str(DEFAULT_BOARD_PATH))
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--sync-log", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--outbox", default=str(DEFAULT_OUTBOX_PATH))
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--min-interval-seconds", type=float, default=1.0)
    parser.add_argument("--rate-limit-wait-mode", default="bounded")
    parser.add_argument("--rate-limit-max-wait-seconds", type=int, default=2100)
    parser.add_argument("--rate-limit-grace-seconds", type=int, default=5)
    parser.add_argument("--rate-limit-max-retries", type=int, default=1)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor")
    plan = subparsers.add_parser("plan")
    plan.add_argument("--write-outbox", action="store_true")
    sync = subparsers.add_parser("sync")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--execute", action="store_true")
    import_github = subparsers.add_parser("import-github")
    import_github.add_argument("--dry-run", action="store_true")
    return parser


def write_json(payload: dict[str, Any], stream: TextIO) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    stream.write("\n")


def main(
    argv: list[str] | None = None,
    *,
    client: github_project_task.GhClient | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout
    try:
        cfg = github_project_task.Config(
            repo=args.repo,
            owner="",
            project_number="",
            status_field="",
            rate_limit_wait_mode=args.rate_limit_wait_mode,
            rate_limit_max_wait_seconds=args.rate_limit_max_wait_seconds,
            rate_limit_grace_seconds=args.rate_limit_grace_seconds,
            rate_limit_max_retries=args.rate_limit_max_retries,
        )
        gh_client = github_project_task.RateLimitingGhClient(
            client or github_project_task.GhClient(),
            github_project_task.rate_limit_policy_from_config(cfg),
        )
        if args.command == "doctor":
            payload = command_doctor(args)
        elif args.command == "plan":
            payload = command_plan(args)
        elif args.command == "sync":
            payload = command_sync(args, gh_client)
        elif args.command == "import-github":
            payload = command_import_github(args)
        else:
            raise SyncError("unknown_command", f"Unknown command: {args.command}")
        if gh_client.rate_limit_waits:
            payload["rate_limit_waits"] = gh_client.rate_limit_waits
        write_json(payload, out)
        return 0
    except SyncError as exc:
        write_json({"status": "error", "error": exc.code, "message": exc.message, **exc.details}, out)
        return 2
    except github_project_task.GhCommandError as exc:
        write_json(
            {
                "status": "error",
                "error": "gh_command_failed",
                "message": str(exc),
                "gh_args": exc.args_list,
                "returncode": exc.returncode,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
            out,
        )
        return 1
    except github_project_task.GhRateLimitError as exc:
        write_json(
            {
                "status": "error",
                "error": "github_rate_limited",
                "message": str(exc),
                "gh_args": exc.args_list,
                "rate_limit": exc.rate_limit,
                "rate_limit_waits": exc.waits,
                "resume_command": github_project_task.rate_limit_resume_guidance(exc.args_list, exc.rate_limit),
            },
            out,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
