#!/usr/bin/env python3
"""Thin GitHub Issue + Project v2 task wrapper for Codex operators."""

from __future__ import annotations

import argparse
import os
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO


DEFAULT_REPO = "pen364692088/EGO"
DEFAULT_OWNER = "pen364692088"
DEFAULT_PROJECT_NUMBER = "1"
DEFAULT_STATUS_FIELD = "Status"

STATUS_ALIASES = {
    "todo": "Todo",
    "pending": "Todo",
    "progress": "In Progress",
    "in_progress": "In Progress",
    "in-progress": "In Progress",
    "done": "Done",
}


class UserError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


class GhCommandError(Exception):
    def __init__(self, args: list[str], returncode: int, stdout: str, stderr: str) -> None:
        super().__init__(stderr.strip() or stdout.strip() or f"gh exited {returncode}")
        self.args_list = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class GhRateLimitError(Exception):
    def __init__(
        self,
        args: list[str],
        original: GhCommandError,
        rate_limit: dict[str, Any],
        waits: list[dict[str, Any]],
    ) -> None:
        super().__init__("GitHub GraphQL/API rate limit exceeded")
        self.args_list = args
        self.original = original
        self.rate_limit = rate_limit
        self.waits = waits


@dataclass(frozen=True)
class Config:
    repo: str
    owner: str
    project_number: str
    status_field: str
    dry_run: bool = False
    rate_limit_wait_mode: str = "bounded"
    rate_limit_max_wait_seconds: int = 2100
    rate_limit_grace_seconds: int = 5
    rate_limit_max_retries: int = 1


@dataclass(frozen=True)
class RateLimitPolicy:
    mode: str = "bounded"
    max_wait_seconds: int = 2100
    grace_seconds: int = 5
    max_retries: int = 1
    now: Any = field(default_factory=lambda: time.time)
    sleeper: Any = field(default_factory=lambda: time.sleep)


def rate_limit_policy_from_config(cfg: Config) -> RateLimitPolicy:
    return RateLimitPolicy(
        mode=cfg.rate_limit_wait_mode,
        max_wait_seconds=cfg.rate_limit_max_wait_seconds,
        grace_seconds=cfg.rate_limit_grace_seconds,
        max_retries=cfg.rate_limit_max_retries,
    )


class GhClient:
    def run(self, args: list[str]) -> str:
        completed = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise GhCommandError(args, completed.returncode, completed.stdout, completed.stderr)
        return completed.stdout


def _is_rate_limit_error(exc: GhCommandError) -> bool:
    text = f"{exc.stdout}\n{exc.stderr}\n{exc}".casefold()
    return "rate limit" in text and ("exceeded" in text or "secondary" in text or "graphql" in text)


def _rate_limit_reset_iso(reset_unix: int | None) -> str | None:
    if reset_unix is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(reset_unix))


def _graphql_rate_limit_snapshot(client: GhClient, policy: RateLimitPolicy) -> dict[str, Any]:
    try:
        payload = json.loads(client.run(["api", "rate_limit"]) or "{}")
    except Exception as exc:
        return {
            "status": "rate_limit_metadata_unavailable",
            "metadata_error": str(exc),
            "wait_seconds": None,
        }
    resources = payload.get("resources") if isinstance(payload, dict) else None
    graphql = resources.get("graphql") if isinstance(resources, dict) else None
    if not isinstance(graphql, dict):
        return {
            "status": "rate_limit_metadata_unavailable",
            "metadata_error": "resources.graphql missing",
            "wait_seconds": None,
        }
    reset_raw = graphql.get("reset")
    reset_unix = int(reset_raw) if isinstance(reset_raw, (int, float, str)) and str(reset_raw).isdigit() else None
    wait_seconds = None
    if reset_unix is not None:
        wait_seconds = max(0, int(reset_unix - int(policy.now()))) + int(policy.grace_seconds)
    return {
        "status": "rate_limited",
        "resource": "graphql",
        "limit": graphql.get("limit"),
        "remaining": graphql.get("remaining"),
        "used": graphql.get("used"),
        "reset": reset_unix,
        "reset_iso": _rate_limit_reset_iso(reset_unix),
        "wait_seconds": wait_seconds,
        "max_wait_seconds": policy.max_wait_seconds,
        "grace_seconds": policy.grace_seconds,
    }


def rate_limit_resume_guidance(args: list[str], rate_limit: dict[str, Any]) -> str:
    reset_iso = rate_limit.get("reset_iso") or "unknown reset time"
    return f"Retry after GitHub GraphQL reset ({reset_iso}): gh {' '.join(args)}"


class RateLimitingGhClient(GhClient):
    def __init__(self, inner: GhClient, policy: RateLimitPolicy) -> None:
        self.inner = inner
        self.policy = policy
        self.rate_limit_waits: list[dict[str, Any]] = []

    def run(self, args: list[str]) -> str:
        attempts = 0
        while True:
            try:
                return self.inner.run(args)
            except GhCommandError as exc:
                if args[:2] == ["api", "rate_limit"] or self.policy.mode == "off" or not _is_rate_limit_error(exc):
                    raise
                snapshot = _graphql_rate_limit_snapshot(self.inner, self.policy)
                snapshot["gh_args"] = args
                snapshot["attempt"] = attempts
                wait_seconds = snapshot.get("wait_seconds")
                if (
                    attempts >= int(self.policy.max_retries)
                    or wait_seconds is None
                    or int(wait_seconds) > int(self.policy.max_wait_seconds)
                ):
                    raise GhRateLimitError(args, exc, snapshot, list(self.rate_limit_waits)) from exc
                wait_event = {
                    "gh_args": args,
                    "attempt": attempts,
                    "wait_seconds": int(wait_seconds),
                    "reset": snapshot.get("reset"),
                    "reset_iso": snapshot.get("reset_iso"),
                    "remaining": snapshot.get("remaining"),
                    "limit": snapshot.get("limit"),
                }
                self.rate_limit_waits.append(wait_event)
                self.policy.sleeper(int(wait_seconds))
                attempts += 1


def _json_loads(text: str, *, command: str) -> dict[str, Any]:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise UserError(
            "invalid_gh_json",
            f"gh {command} did not return valid JSON",
            raw=text,
        ) from exc
    if not isinstance(payload, dict):
        raise UserError("invalid_gh_json", f"gh {command} returned non-object JSON", raw=text)
    return payload


def gh_json(client: GhClient, args: list[str]) -> dict[str, Any]:
    return _json_loads(client.run(args), command=" ".join(args[:2]))


def normalize_status(raw: str, options: list[dict[str, Any]]) -> tuple[str, str]:
    names = {str(option.get("name", "")): str(option.get("id", "")) for option in options}
    if raw in names:
        return raw, names[raw]

    normalized_names = {name.casefold(): name for name in names}
    alias_key = raw.strip().replace(" ", "_").casefold()
    canonical = STATUS_ALIASES.get(alias_key)
    if canonical and canonical in names:
        return canonical, names[canonical]

    casefold_name = raw.strip().casefold()
    if casefold_name in normalized_names:
        canonical = normalized_names[casefold_name]
        return canonical, names[canonical]

    raise UserError(
        "unknown_status",
        f"Unknown status: {raw}",
        available_statuses=sorted(names),
    )


def project_view(client: GhClient, cfg: Config) -> dict[str, Any]:
    return gh_json(
        client,
        ["project", "view", cfg.project_number, "--owner", cfg.owner, "--format", "json"],
    )


def field_list(client: GhClient, cfg: Config) -> list[dict[str, Any]]:
    payload = gh_json(
        client,
        ["project", "field-list", cfg.project_number, "--owner", cfg.owner, "--format", "json"],
    )
    fields = payload.get("fields")
    if not isinstance(fields, list):
        raise UserError("missing_project_fields", "Project field-list response has no fields array")
    return fields


def status_field(client: GhClient, cfg: Config) -> dict[str, Any]:
    for field in field_list(client, cfg):
        if field.get("name") == cfg.status_field:
            options = field.get("options")
            if not isinstance(options, list):
                raise UserError(
                    "status_field_not_single_select",
                    f"Project field {cfg.status_field!r} has no single-select options",
                )
            return field
    raise UserError("status_field_not_found", f"Project field not found: {cfg.status_field}")


def issue_view(client: GhClient, cfg: Config, issue: str) -> dict[str, Any]:
    return gh_json(
        client,
        [
            "issue",
            "view",
            issue,
            "--repo",
            cfg.repo,
            "--json",
            "number,title,state,url",
        ],
    )


def project_items(client: GhClient, cfg: Config, *, limit: int = 200) -> list[dict[str, Any]]:
    payload = gh_json(
        client,
        [
            "project",
            "item-list",
            cfg.project_number,
            "--owner",
            cfg.owner,
            "--limit",
            str(limit),
            "--format",
            "json",
        ],
    )
    items = payload.get("items")
    if not isinstance(items, list):
        raise UserError("missing_project_items", "Project item-list response has no items array")
    return items


def find_project_item(items: list[dict[str, Any]], issue: dict[str, Any]) -> dict[str, Any] | None:
    issue_url = issue.get("url")
    issue_number = issue.get("number")
    for item in items:
        content = item.get("content")
        if not isinstance(content, dict):
            continue
        if issue_url and content.get("url") == issue_url:
            return item
        if issue_number and content.get("number") == issue_number and content.get("type") == "Issue":
            return item
    return None


def ensure_project_item(client: GhClient, cfg: Config, issue: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    found = find_project_item(project_items(client, cfg), issue)
    if found:
        return found, False

    if cfg.dry_run:
        return {
            "id": "<dry-run-item-id>",
            "status": None,
            "content": issue,
            "dry_run": True,
        }, True

    client.run(
        [
            "project",
            "item-add",
            cfg.project_number,
            "--owner",
            cfg.owner,
            "--url",
            str(issue["url"]),
        ]
    )
    found = find_project_item(project_items(client, cfg), issue)
    if not found:
        raise UserError(
            "project_item_not_found_after_add",
            "Issue was added to project but could not be found in item-list",
            issue=issue,
        )
    return found, True


def set_project_status(
    client: GhClient,
    cfg: Config,
    *,
    item: dict[str, Any],
    status_name: str,
    status_option_id: str,
    project_id: str,
    field_id: str,
) -> dict[str, Any]:
    current = item.get("status")
    if current == status_name:
        return {"changed": False, "observed_status": current}

    if cfg.dry_run:
        return {
            "changed": True,
            "dry_run": True,
            "planned_status": status_name,
            "observed_status": current,
        }

    client.run(
        [
            "project",
            "item-edit",
            "--id",
            str(item["id"]),
            "--project-id",
            project_id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            status_option_id,
        ]
    )
    return {"changed": True, "observed_status": current}


def command_doctor(client: GhClient, cfg: Config, _args: argparse.Namespace) -> dict[str, Any]:
    gh_path = shutil.which("gh")
    if not gh_path:
        raise UserError("gh_not_found", "gh is not available on PATH")

    version = client.run(["--version"]).splitlines()[0]
    auth = client.run(["auth", "status"])
    if "Logged in to github.com account" not in auth:
        raise UserError("gh_not_logged_in", "gh auth status did not report an active login")
    if "project" not in auth:
        raise UserError("missing_project_scope", "gh token is missing project scope")

    project = project_view(client, cfg)
    field = status_field(client, cfg)
    return {
        "status": "ok",
        "gh_path": gh_path,
        "gh_version": version,
        "repo": cfg.repo,
        "project": {
            "id": project.get("id"),
            "number": project.get("number"),
            "owner": cfg.owner,
            "title": project.get("title"),
            "url": project.get("url"),
        },
        "status_field": {
            "id": field.get("id"),
            "name": field.get("name"),
            "options": [option.get("name") for option in field.get("options", [])],
        },
    }


def command_verify(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    issue = issue_view(client, cfg, args.issue)
    item = find_project_item(project_items(client, cfg), issue)
    if not item:
        raise UserError("project_item_not_found", "Issue is not in the configured project", issue=issue)

    observed = item.get("status")
    if args.expect_status:
        field = status_field(client, cfg)
        expected, _ = normalize_status(args.expect_status, field["options"])
        if observed != expected:
            raise UserError(
                "status_mismatch",
                f"Expected status {expected!r}, observed {observed!r}",
                expected_status=expected,
                observed_status=observed,
                issue=issue,
                item_id=item.get("id"),
            )

    return {
        "status": "ok",
        "issue": issue,
        "project_item": {
            "id": item.get("id"),
            "status": observed,
            "title": item.get("title"),
        },
    }


def command_add(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    issue = issue_view(client, cfg, args.issue)
    item, added = ensure_project_item(client, cfg, issue)
    status_result: dict[str, Any] | None = None

    if args.status:
        project = project_view(client, cfg)
        field = status_field(client, cfg)
        status_name, option_id = normalize_status(args.status, field["options"])
        status_result = set_project_status(
            client,
            cfg,
            item=item,
            status_name=status_name,
            status_option_id=option_id,
            project_id=str(project["id"]),
            field_id=str(field["id"]),
        )
        if not cfg.dry_run:
            item = find_project_item(project_items(client, cfg), issue) or item

    return {
        "status": "dry_run" if cfg.dry_run else "ok",
        "issue": issue,
        "project_item": {
            "id": item.get("id"),
            "status": item.get("status"),
            "added": added,
        },
        "status_update": status_result,
    }


def command_set_status(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    issue = issue_view(client, cfg, args.issue)
    project = project_view(client, cfg)
    field = status_field(client, cfg)
    status_name, option_id = normalize_status(args.status, field["options"])
    item, added = ensure_project_item(client, cfg, issue)

    status_result = set_project_status(
        client,
        cfg,
        item=item,
        status_name=status_name,
        status_option_id=option_id,
        project_id=str(project["id"]),
        field_id=str(field["id"]),
    )
    if not cfg.dry_run:
        item = find_project_item(project_items(client, cfg), issue) or item
        observed = item.get("status")
        if observed != status_name:
            raise UserError(
                "status_write_not_observed",
                f"Status write did not read back as {status_name!r}",
                expected_status=status_name,
                observed_status=observed,
            )

    return {
        "status": "dry_run" if cfg.dry_run else "ok",
        "issue": issue,
        "project_item": {
            "id": item.get("id"),
            "status": item.get("status") if not cfg.dry_run else status_name,
            "added": added,
        },
        "status_update": status_result,
    }


def command_create(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    if cfg.dry_run:
        return {
            "status": "dry_run",
            "planned": [
                {"gh": ["issue", "create", "--repo", cfg.repo, "--title", args.title, "--body", args.body]},
                {"gh": ["project", "item-add", cfg.project_number, "--owner", cfg.owner, "--url", "<issue-url>"]},
                *(
                    [
                        {
                            "gh": [
                                "project",
                                "item-edit",
                                "--id",
                                "<project-item-id>",
                                "--project-id",
                                "<project-id>",
                                "--field-id",
                                "<status-field-id>",
                                "--single-select-option-id",
                                "<status-option-id>",
                            ],
                            "status": args.status,
                        }
                    ]
                    if args.status
                    else []
                ),
            ],
        }

    create_output = client.run(
        ["issue", "create", "--repo", cfg.repo, "--title", args.title, "--body", args.body]
    )
    issue_url = next(
        (line.strip() for line in reversed(create_output.splitlines()) if line.strip().startswith("http")),
        None,
    )
    if not issue_url:
        raise UserError("issue_create_url_not_found", "gh issue create did not return an issue URL", raw=create_output)
    add_args = argparse.Namespace(issue=issue_url, status=args.status)
    result = command_add(client, cfg, add_args)
    result["created"] = True
    return result


def _read_comment_body(args: argparse.Namespace) -> str:
    if args.comment_file:
        return Path(args.comment_file).read_text(encoding="utf-8").strip()
    return (args.comment or "").strip()


def command_closeout(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    comment_body = _read_comment_body(args)
    if not comment_body:
        raise UserError("missing_closeout_comment", "closeout requires --comment-file or --comment")

    if cfg.dry_run:
        return {
            "status": "dry_run",
            "planned": [
                {"gh": ["issue", "comment", args.issue, "--repo", cfg.repo, "--body", comment_body]},
                {
                    "wrapper": [
                        "set-status",
                        "--issue",
                        args.issue,
                        "--status",
                        args.status,
                    ]
                },
                {"gh": ["issue", "close", args.issue, "--repo", cfg.repo]},
                {"wrapper": ["verify", "--issue", args.issue, "--expect-status", args.status]},
            ],
        }

    client.run(["issue", "comment", args.issue, "--repo", cfg.repo, "--body", comment_body])
    status_result = command_set_status(client, cfg, argparse.Namespace(issue=args.issue, status=args.status))
    client.run(["issue", "close", args.issue, "--repo", cfg.repo])
    try:
        verify_result = command_verify(client, cfg, argparse.Namespace(issue=args.issue, expect_status=args.status))
        issue = issue_view(client, cfg, args.issue)
    except GhRateLimitError as exc:
        return {
            "status": "github_rate_limited_after_mutation",
            "issue_ref": args.issue,
            "commented": True,
            "status_update": status_result.get("status_update"),
            "closed_attempted": True,
            "rate_limit": exc.rate_limit,
            "rate_limit_waits": exc.waits,
            "resume_command": f"python3 scripts/github_project_task.py verify --issue {args.issue} --expect-status {args.status}",
            "message": "Closeout mutation was attempted; resume with verify/readback before repeating comment or close.",
        }
    if issue.get("state") != "CLOSED":
        raise UserError("issue_close_not_observed", "Issue close did not read back as CLOSED", issue=issue)
    return {
        "status": "ok",
        "issue": issue,
        "project_item": verify_result["project_item"],
        "status_update": status_result.get("status_update"),
        "commented": True,
        "closed": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage GitHub issues as Project v2 task items.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub repo, default: {DEFAULT_REPO}")
    parser.add_argument("--owner", default=DEFAULT_OWNER, help=f"Project owner, default: {DEFAULT_OWNER}")
    parser.add_argument(
        "--project-number",
        default=DEFAULT_PROJECT_NUMBER,
        help=f"Project number, default: {DEFAULT_PROJECT_NUMBER}",
    )
    parser.add_argument(
        "--status-field",
        default=DEFAULT_STATUS_FIELD,
        help=f"Project status field name, default: {DEFAULT_STATUS_FIELD}",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan mutations without writing GitHub state")
    parser.add_argument(
        "--rate-limit-wait-mode",
        default=os.environ.get("GITHUB_RATE_LIMIT_WAIT_MODE", "bounded"),
        choices=["off", "bounded"],
        help="GitHub rate-limit recovery mode, default: bounded",
    )
    parser.add_argument(
        "--rate-limit-max-wait-seconds",
        type=int,
        default=int(os.environ.get("GITHUB_RATE_LIMIT_MAX_WAIT_SECONDS", "2100")),
        help="Maximum bounded wait for GitHub GraphQL reset",
    )
    parser.add_argument(
        "--rate-limit-grace-seconds",
        type=int,
        default=int(os.environ.get("GITHUB_RATE_LIMIT_GRACE_SECONDS", "5")),
        help="Extra seconds to wait after reset",
    )
    parser.add_argument(
        "--rate-limit-max-retries",
        type=int,
        default=int(os.environ.get("GITHUB_RATE_LIMIT_MAX_RETRIES", "1")),
        help="Maximum automatic retries after bounded wait",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Check gh auth and Project v2 access")

    create = subparsers.add_parser("create", help="Create an issue, add it to Project, and optionally set status")
    create.add_argument("--title", required=True)
    create.add_argument("--body", default="")
    create.add_argument("--status")

    add = subparsers.add_parser("add", help="Add an existing issue to Project and optionally set status")
    add.add_argument("--issue", required=True)
    add.add_argument("--status")

    set_status = subparsers.add_parser("set-status", help="Set Project Status for an issue")
    set_status.add_argument("--issue", required=True)
    set_status.add_argument("--status", required=True)

    verify = subparsers.add_parser("verify", help="Verify an issue's Project item and status")
    verify.add_argument("--issue", required=True)
    verify.add_argument("--expect-status")

    closeout = subparsers.add_parser("closeout", help="Comment, set Project Status, close, and verify")
    closeout.add_argument("--issue", required=True)
    closeout.add_argument("--status", default="Done")
    closeout.add_argument("--comment-file")
    closeout.add_argument("--comment")
    return parser


def dispatch(client: GhClient, cfg: Config, args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "doctor":
        return command_doctor(client, cfg, args)
    if args.command == "create":
        return command_create(client, cfg, args)
    if args.command == "add":
        return command_add(client, cfg, args)
    if args.command == "set-status":
        return command_set_status(client, cfg, args)
    if args.command == "verify":
        return command_verify(client, cfg, args)
    if args.command == "closeout":
        return command_closeout(client, cfg, args)
    raise UserError("unknown_command", f"Unknown command: {args.command}")


def write_json(payload: dict[str, Any], stream: TextIO) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    stream.write("\n")


def main(argv: list[str] | None = None, *, client: GhClient | None = None, stdout: TextIO | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = Config(
        repo=args.repo,
        owner=args.owner,
        project_number=args.project_number,
        status_field=args.status_field,
        dry_run=args.dry_run,
        rate_limit_wait_mode=args.rate_limit_wait_mode,
        rate_limit_max_wait_seconds=args.rate_limit_max_wait_seconds,
        rate_limit_grace_seconds=args.rate_limit_grace_seconds,
        rate_limit_max_retries=args.rate_limit_max_retries,
    )
    out = stdout or sys.stdout
    gh_client = RateLimitingGhClient(client or GhClient(), rate_limit_policy_from_config(cfg))
    try:
        payload = dispatch(gh_client, cfg, args)
        if gh_client.rate_limit_waits:
            payload["rate_limit_waits"] = gh_client.rate_limit_waits
        write_json(payload, out)
        return 0
    except UserError as exc:
        write_json({"status": "error", "error": exc.code, "message": exc.message, **exc.details}, out)
        return 2
    except GhCommandError as exc:
        write_json(
            {
                "status": "error",
                "error": "gh_command_failed",
                "message": str(exc),
                "returncode": exc.returncode,
                "gh_args": exc.args_list,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
            out,
        )
        return 1
    except GhRateLimitError as exc:
        write_json(
            {
                "status": "error",
                "error": "github_rate_limited",
                "message": str(exc),
                "gh_args": exc.args_list,
                "rate_limit": exc.rate_limit,
                "rate_limit_waits": exc.waits,
                "resume_command": rate_limit_resume_guidance(exc.args_list, exc.rate_limit),
            },
            out,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
