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
DEFAULT_PROJECT_OWNER = "pen364692088"
DEFAULT_PROJECT_NUMBER = "1"
DEFAULT_STATUS_FIELD = "Status"
VALID_SCOPES = {"all", "existing"}

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


def task_has_cached_issue(task: dict[str, Any], state: dict[str, Any]) -> bool:
    task_id = str(task.get("id") or "")
    cached = state.get("issues", {}).get(task_id)
    return isinstance(cached, dict) and cached.get("number") is not None


def task_in_scope(task: dict[str, Any], state: dict[str, Any], scope: str) -> bool:
    if scope not in VALID_SCOPES:
        raise SyncError("invalid_sync_scope", f"Unknown sync scope: {scope}", valid_scopes=sorted(VALID_SCOPES))
    if scope == "existing":
        return task_has_cached_issue(task, state)
    return True


def scoped_tasks(
    board: dict[str, Any],
    state: dict[str, Any],
    scope: str,
    task_ids: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    included: list[dict[str, Any]] = []
    skipped: list[str] = []
    selected = {str(task_id) for task_id in (task_ids or []) if str(task_id)}
    for task in board.get("tasks") or []:
        task_id = str(task.get("id") or "")
        if not task_id:
            continue
        if selected and task_id not in selected:
            skipped.append(task_id)
            continue
        if task_in_scope(task, state, scope):
            included.append(task)
        else:
            skipped.append(task_id)
    return included, skipped


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


def desired_project_status(task: dict[str, Any]) -> str:
    status = str(task.get("status") or "")
    if status == "accepted":
        return "Done"
    if status == "active":
        return "In Progress"
    return "Todo"


def build_plan(
    board: dict[str, Any],
    state: dict[str, Any],
    *,
    scope: str = "all",
    include_project_status: bool = False,
    task_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    issues = state.setdefault("issues", {})
    tasks, _skipped = scoped_tasks(board, state, scope, task_ids=task_ids)
    for task in tasks:
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
            operation = {
                "op": "create_issue",
                "task_id": task_id,
                "title": title,
                "body_hash": body_hash,
                "desired_state": desired_state,
            }
            if include_project_status:
                operation["project_status"] = desired_project_status(task)
            operations.append(operation)
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
        if include_project_status and number is not None:
            project_status = desired_project_status(task)
            if cached.get("project_status") != project_status:
                operations.append(
                    {
                        "op": "set_project_status",
                        "task_id": task_id,
                        "issue": number,
                        "project_status": project_status,
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
    project_owner: str,
    project_number: str,
    status_field: str,
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
            if operation.get("project_status"):
                project_status = str(operation["project_status"])
                project_cfg = github_project_task.Config(
                    repo=repo,
                    owner=project_owner,
                    project_number=project_number,
                    status_field=status_field,
                )
                status_result = github_project_task.command_set_status(
                    client,
                    project_cfg,
                    argparse.Namespace(issue=str(issue_number), status=project_status),
                )
                issues.setdefault(task_id, {})["project_status"] = project_status
                result["project_status"] = project_status
                result["project_result"] = status_result
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
        elif operation["op"] == "set_project_status":
            issue_number = int(operation["issue"])
            project_status = str(operation["project_status"])
            project_cfg = github_project_task.Config(
                repo=repo,
                owner=project_owner,
                project_number=project_number,
                status_field=status_field,
            )
            status_result = github_project_task.command_set_status(
                client,
                project_cfg,
                argparse.Namespace(issue=str(issue_number), status=project_status),
            )
            issues.setdefault(task_id, {})["number"] = issue_number
            issues.setdefault(task_id, {})["project_status"] = project_status
            result = {
                "op": "set_project_status",
                "task_id": task_id,
                "issue": issue_number,
                "project_status": project_status,
                "status": "ok",
                "project_result": status_result,
            }
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
    tasks, skipped = scoped_tasks(board, state, args.scope, task_ids=args.task_id)
    operations = build_plan(
        board,
        state,
        scope=args.scope,
        include_project_status=args.project_status,
        task_ids=args.task_id,
    )
    if args.write_outbox:
        write_outbox(Path(args.outbox), operations)
    return {
        "status": "ok",
        "mode": "plan",
        "scope": args.scope,
        "task_ids": args.task_id,
        "project_status": bool(args.project_status),
        "task_count": len(tasks),
        "skipped_task_count": len(skipped),
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
    tasks, skipped = scoped_tasks(board, state, args.scope, task_ids=args.task_id)
    operations = build_plan(
        board,
        state,
        scope=args.scope,
        include_project_status=args.project_status,
        task_ids=args.task_id,
    )
    write_outbox(Path(args.outbox), operations)
    log_entry: dict[str, Any] = {
        "created_at_unix": int(time.time()),
        "mode": "execute" if args.execute else "dry_run",
        "scope": args.scope,
        "task_ids": args.task_id,
        "project_status": bool(args.project_status),
        "task_count": len(tasks),
        "skipped_task_count": len(skipped),
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
            project_owner=args.project_owner,
            project_number=args.project_number,
            status_field=args.status_field,
            min_interval_seconds=float(args.min_interval_seconds),
        )
        write_state(state_path, state)
        log_entry["results"] = results
    else:
        results = []
    append_jsonl(Path(args.sync_log), log_entry)
    return {
        "status": "ok",
        "mode": "execute" if args.execute else "dry_run",
        "scope": args.scope,
        "task_ids": args.task_id,
        "project_status": bool(args.project_status),
        "task_count": len(tasks),
        "skipped_task_count": len(skipped),
        "operation_count": len(operations),
        "operations": operations,
        "state_path": str(state_path),
        "outbox_path": args.outbox,
        "sync_log_path": args.sync_log,
        "results": results,
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
    parser.add_argument("--project-owner", default=DEFAULT_PROJECT_OWNER)
    parser.add_argument("--project-number", default=DEFAULT_PROJECT_NUMBER)
    parser.add_argument("--status-field", default=DEFAULT_STATUS_FIELD)
    parser.add_argument("--min-interval-seconds", type=float, default=1.0)
    parser.add_argument("--rate-limit-wait-mode", default="bounded")
    parser.add_argument("--rate-limit-max-wait-seconds", type=int, default=2100)
    parser.add_argument("--rate-limit-grace-seconds", type=int, default=5)
    parser.add_argument("--rate-limit-max-retries", type=int, default=1)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor")
    plan = subparsers.add_parser("plan")
    plan.add_argument("--write-outbox", action="store_true")
    plan.add_argument("--scope", choices=sorted(VALID_SCOPES), default="all")
    plan.add_argument("--task-id", action="append", default=[])
    plan.add_argument("--project-status", action="store_true")
    sync = subparsers.add_parser("sync")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--execute", action="store_true")
    sync.add_argument("--scope", choices=sorted(VALID_SCOPES), default="all")
    sync.add_argument("--task-id", action="append", default=[])
    sync.add_argument("--project-status", action="store_true")
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
