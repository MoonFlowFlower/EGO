#!/usr/bin/env python3
"""
Codex assistant memory helpers.

This tool manages assistant-side structured memory only.
It does not touch EgoCore/OpenEmotion runtime memory.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


ALLOWED_LONG_RECORD_SCOPES = {"project", "preference"}
ALLOWED_SOURCE_TYPES = {"repo_file", "user_confirmation", "task_closure"}
TASK_HANDOFF_SCHEMA = "codex.task_handoff.v1"
TASK_CLOSURE_SCHEMA = "codex.task_closure.v1"
SESSION_CAPSULE_SCHEMA = "codex.session_capsule.v1"
PLACEHOLDER_TOKEN = "<fill-me>"

LONG_RECORD_REQUIRED_FIELDS = (
    "record_id",
    "scope",
    "title",
    "content",
    "source_type",
    "source_ref",
    "last_verified_at",
    "owner",
    "expiry_or_revalidate_rule",
)

TASK_HANDOFF_REQUIRED_FIELDS = (
    "schema_version",
    "task_id",
    "title",
    "status",
    "owner",
    "source_ref",
    "last_verified_at",
    "expiry_or_revalidate_rule",
    "real_goal",
    "success_criteria",
    "current_layer",
    "main_chain_status",
    "authority_source",
    "confirmed",
    "unknowns",
    "blockers",
    "next_minimal_closure_action",
    "related_refs",
)

TASK_CLOSURE_REQUIRED_FIELDS = (
    "schema_version",
    "task_id",
    "title",
    "status",
    "owner",
    "source_ref",
    "last_verified_at",
    "expiry_or_revalidate_rule",
    "real_goal",
    "proved",
    "not_proved",
    "current_layer",
    "main_chain_status",
    "verification_level",
    "next_action",
    "related_refs",
)

SESSION_CAPSULE_REQUIRED_FIELDS = (
    "schema_version",
    "capsule_id",
    "task_id",
    "owner",
    "source_ref",
    "last_verified_at",
    "expiry_or_revalidate_rule",
    "authority_source_unchanged",
    "summary",
    "confirmed",
    "raw_refs",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_dump(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _is_placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.strip() == PLACEHOLDER_TOKEN


class CodexMemoryWorkspace:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.codex_dir = self.root / ".codex"
        self.memory_dir = self.codex_dir / "memory"
        self.project_truth_path = self.memory_dir / "project_truth.jsonl"
        self.user_preferences_path = self.memory_dir / "user_preferences.jsonl"
        self.tasks_dir = self.memory_dir / "tasks"
        self.tasks_active_dir = self.tasks_dir / "active"
        self.tasks_archive_dir = self.tasks_dir / "archive"
        self.sessions_dir = self.memory_dir / "sessions"
        self.index_path = self.root / "CODEX_MEMORY.md"

    def ensure_layout(self) -> None:
        for directory in (
            self.memory_dir,
            self.tasks_dir,
            self.tasks_active_dir,
            self.tasks_archive_dir,
            self.sessions_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def relpath(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def load_jsonl_records(self, path: Path) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not path.exists():
            return records
        for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError(f"{self.relpath(path)}:{lineno} is not a JSON object")
            records.append(data)
        return records

    def _latest_json_file(self, directory: Path) -> Optional[Path]:
        candidates = sorted(
            (path for path in directory.glob("*.json") if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return candidates[0] if candidates else None

    def _validate_long_record(
        self,
        record: Dict[str, Any],
        *,
        expected_scope: str,
        source_path: Path,
        index: int,
    ) -> List[str]:
        errors: List[str] = []
        prefix = f"{self.relpath(source_path)}:{index}"
        for field in LONG_RECORD_REQUIRED_FIELDS:
            value = record.get(field)
            if value in (None, "", []):
                errors.append(f"{prefix}: missing `{field}`")
        scope = record.get("scope")
        if scope != expected_scope:
            errors.append(f"{prefix}: scope must be `{expected_scope}`, got `{scope}`")
        if scope not in ALLOWED_LONG_RECORD_SCOPES:
            errors.append(f"{prefix}: invalid scope `{scope}`")
        source_type = record.get("source_type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{prefix}: invalid source_type `{source_type}`")
        return errors

    def _validate_json_record(
        self,
        path: Path,
        required_fields: Sequence[str],
        *,
        expected_schema: str,
    ) -> List[str]:
        errors: List[str] = []
        data = json.loads(path.read_text(encoding="utf-8"))
        prefix = self.relpath(path)
        if data.get("schema_version") != expected_schema:
            errors.append(
                f"{prefix}: schema_version must be `{expected_schema}`, got `{data.get('schema_version')}`"
            )
        for field in required_fields:
            value = data.get(field)
            if value in (None, "", []):
                errors.append(f"{prefix}: missing `{field}`")
            elif _is_placeholder(value):
                errors.append(f"{prefix}: `{field}` is still placeholder `{PLACEHOLDER_TOKEN}`")
        return errors

    def validate(self) -> List[str]:
        self.ensure_layout()
        errors: List[str] = []

        if not self.project_truth_path.exists():
            errors.append(f"missing {self.relpath(self.project_truth_path)}")
        else:
            for index, record in enumerate(self.load_jsonl_records(self.project_truth_path), start=1):
                errors.extend(
                    self._validate_long_record(
                        record,
                        expected_scope="project",
                        source_path=self.project_truth_path,
                        index=index,
                    )
                )

        if not self.user_preferences_path.exists():
            errors.append(f"missing {self.relpath(self.user_preferences_path)}")
        else:
            for index, record in enumerate(self.load_jsonl_records(self.user_preferences_path), start=1):
                errors.extend(
                    self._validate_long_record(
                        record,
                        expected_scope="preference",
                        source_path=self.user_preferences_path,
                        index=index,
                    )
                )

        for path in sorted(self.tasks_active_dir.glob("*.json")):
            errors.extend(
                self._validate_json_record(
                    path,
                    TASK_HANDOFF_REQUIRED_FIELDS,
                    expected_schema=TASK_HANDOFF_SCHEMA,
                )
            )

        for path in sorted(self.tasks_archive_dir.glob("*.json")):
            errors.extend(
                self._validate_json_record(
                    path,
                    TASK_CLOSURE_REQUIRED_FIELDS,
                    expected_schema=TASK_CLOSURE_SCHEMA,
                )
            )

        for path in sorted(self.sessions_dir.glob("*.json")):
            errors.extend(
                self._validate_json_record(
                    path,
                    SESSION_CAPSULE_REQUIRED_FIELDS,
                    expected_schema=SESSION_CAPSULE_SCHEMA,
                )
            )

        return errors

    def _render_table(self, records: List[Dict[str, Any]]) -> List[str]:
        def esc(text: Any) -> str:
            return str(text or "").replace("|", "\\|")

        lines = [
            "| ID | 标题 | 来源 | 复核规则 |",
            "|---|---|---|---|",
        ]
        for record in records:
            lines.append(
                f"| {esc(record.get('record_id'))} | {esc(record.get('title'))} | "
                f"{esc(record.get('source_ref'))} | {esc(record.get('expiry_or_revalidate_rule'))} |"
            )
        return lines

    def render_index(self) -> str:
        project_truths = self.load_jsonl_records(self.project_truth_path)
        preferences = self.load_jsonl_records(self.user_preferences_path)

        lines = [
            "# CODEX_MEMORY.md",
            "",
            "> Codex 开发助手稳定记忆索引",
            "> Source of truth: `.codex/memory/project_truth.jsonl` + `.codex/memory/user_preferences.jsonl`",
            "> 这是开发助手记忆索引，不是第二份项目总记忆；广义项目背景仍以 `PROJECT_MEMORY.md` 为主。",
            "",
            "## 记忆分层",
            "",
            "- `.codex/memory/project_truth.jsonl` + `.codex/memory/user_preferences.jsonl`：Codex 结构化记忆源。",
            "- `CODEX_MEMORY.md`：结构化记忆的渲染索引，服务新会话注入。",
            "- `PROJECT_MEMORY.md`：仓库级广义项目记忆，保存边界、流程、关键发现、里程碑与长期背景。",
            "",
            "## 使用边界",
            "",
            "- 这套记忆只服务开发助手会话衔接，不接入 EgoCore/OpenEmotion runtime。",
            "- 只保存结构化事实、长期偏好、任务 handoff/closure、session capsule。",
            "- 不保存长聊天原文、未验证结论、调试噪声和过期讨论。",
            "",
            "## 怎么读",
            "",
            "- 新会话恢复当前任务：先读任务 handoff，再读 `CODEX_MEMORY.md`。",
            "- 需要广义项目背景、系统边界、历史里程碑时：回读 `PROJECT_MEMORY.md`。",
            "- 需要追结构化源或做记忆维护时：直接看 `.codex/memory/*.jsonl` 与本目录说明。",
            "",
            "## 新会话注入顺序",
            "",
            "1. 当前任务 handoff",
            "2. `CODEX_MEMORY.md`",
            "3. 上一任务 closure",
            "4. 同任务 session capsule",
            "",
            "## 稳定项目真相",
            "",
        ]
        lines.extend(self._render_table(project_truths))
        lines.extend(
            [
                "",
                "## 长期用户偏好",
                "",
            ]
        )
        lines.extend(self._render_table(preferences))
        lines.extend(
            [
                "",
                "## 本地目录",
                "",
                f"- active task records: `{self.relpath(self.tasks_active_dir)}/`",
                f"- archived closures: `{self.relpath(self.tasks_archive_dir)}/`",
                f"- session capsules: `{self.relpath(self.sessions_dir)}/`",
                "",
                "## 维护命令",
                "",
                "```bash",
                "python3 scripts/codex_memory.py validate",
                "python3 scripts/codex_memory.py render",
                "python3 scripts/codex_memory.py bootstrap",
                "```",
                "",
            ]
        )
        return "\n".join(lines)

    def write_index(self) -> Path:
        self.ensure_layout()
        self.index_path.write_text(self.render_index(), encoding="utf-8")
        return self.index_path

    def _write_record(self, path: Path, payload: Dict[str, Any]) -> Path:
        if path.exists():
            raise FileExistsError(f"record already exists: {self.relpath(path)}")
        path.write_text(_json_dump(payload), encoding="utf-8")
        return path

    def create_task_handoff(
        self,
        *,
        task_id: str,
        title: str,
        owner: str = "codex",
        source_ref: str = PLACEHOLDER_TOKEN,
        output: Optional[Path] = None,
    ) -> Path:
        self.ensure_layout()
        path = output or (self.tasks_active_dir / f"{task_id}.json")
        payload = {
            "schema_version": TASK_HANDOFF_SCHEMA,
            "task_id": task_id,
            "title": title,
            "status": "active",
            "owner": owner,
            "source_ref": source_ref,
            "last_verified_at": _utc_now_iso(),
            "expiry_or_revalidate_rule": "until_task_closed",
            "real_goal": PLACEHOLDER_TOKEN,
            "success_criteria": [PLACEHOLDER_TOKEN],
            "current_layer": PLACEHOLDER_TOKEN,
            "main_chain_status": PLACEHOLDER_TOKEN,
            "authority_source": PLACEHOLDER_TOKEN,
            "confirmed": [],
            "unknowns": [],
            "blockers": [],
            "next_minimal_closure_action": PLACEHOLDER_TOKEN,
            "related_refs": [],
        }
        return self._write_record(path, payload)

    def create_task_closure(
        self,
        *,
        task_id: str,
        title: str,
        owner: str = "codex",
        source_ref: str = PLACEHOLDER_TOKEN,
        output: Optional[Path] = None,
    ) -> Path:
        self.ensure_layout()
        path = output or (self.tasks_archive_dir / f"{task_id}-closure.json")
        payload = {
            "schema_version": TASK_CLOSURE_SCHEMA,
            "task_id": task_id,
            "title": title,
            "status": "closed",
            "owner": owner,
            "source_ref": source_ref,
            "last_verified_at": _utc_now_iso(),
            "expiry_or_revalidate_rule": "archive_after_task_closed",
            "real_goal": PLACEHOLDER_TOKEN,
            "proved": [],
            "not_proved": [],
            "current_layer": PLACEHOLDER_TOKEN,
            "main_chain_status": PLACEHOLDER_TOKEN,
            "verification_level": PLACEHOLDER_TOKEN,
            "next_action": PLACEHOLDER_TOKEN,
            "related_refs": [],
        }
        return self._write_record(path, payload)

    def create_session_capsule(
        self,
        *,
        task_id: str,
        capsule_id: str,
        owner: str = "codex",
        source_ref: str = PLACEHOLDER_TOKEN,
        output: Optional[Path] = None,
    ) -> Path:
        self.ensure_layout()
        path = output or (self.sessions_dir / f"{task_id}-{capsule_id}.json")
        payload = {
            "schema_version": SESSION_CAPSULE_SCHEMA,
            "capsule_id": capsule_id,
            "task_id": task_id,
            "owner": owner,
            "source_ref": source_ref,
            "last_verified_at": _utc_now_iso(),
            "expiry_or_revalidate_rule": "expire_when_task_changes",
            "authority_source_unchanged": True,
            "summary": PLACEHOLDER_TOKEN,
            "confirmed": [],
            "raw_refs": [],
        }
        return self._write_record(path, payload)

    def build_bootstrap_bundle(
        self,
        *,
        task_record: Optional[Path] = None,
        previous_closure: Optional[Path] = None,
        session_capsule: Optional[Path] = None,
    ) -> str:
        task_record = task_record or self._latest_json_file(self.tasks_active_dir)
        previous_closure = previous_closure or self._latest_json_file(self.tasks_archive_dir)

        lines = [
            "# Codex Bootstrap Bundle",
            "",
            "按下面顺序启动新会话：",
            "",
        ]
        index = 1
        if task_record:
            lines.append(f"{index}. 当前任务 handoff: `{self.relpath(task_record)}`")
            index += 1
        lines.append(f"{index}. 稳定记忆索引: `{self.relpath(self.index_path)}`")
        index += 1
        if previous_closure:
            lines.append(f"{index}. 上一任务 closure: `{self.relpath(previous_closure)}`")
            index += 1
        if session_capsule:
            lines.append(f"{index}. 同任务 session capsule: `{self.relpath(session_capsule)}`")

        lines.extend(
            [
                "",
                "规则：",
                "",
                "- 切到下一个任务时仍然新开会话。",
                "- `session capsule` 只在同一任务继续推进时使用。",
                "- 没有 `source_ref` 的临时总结，不得晋升到长期记忆。",
                "",
            ]
        )
        return "\n".join(lines)


def _default_workspace() -> CodexMemoryWorkspace:
    return CodexMemoryWorkspace(Path(__file__).resolve().parents[1])


def _print_validation(errors: List[str]) -> int:
    if errors:
        print("Codex memory validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Codex memory validation passed.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Codex assistant memory helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Ensure memory layout exists and render CODEX_MEMORY.md")
    subparsers.add_parser("validate", help="Validate structured memory files")
    subparsers.add_parser("render", help="Render CODEX_MEMORY.md from structured records")

    handoff_parser = subparsers.add_parser("create-task-handoff", help="Create a task handoff skeleton")
    handoff_parser.add_argument("--task-id", required=True)
    handoff_parser.add_argument("--title", required=True)
    handoff_parser.add_argument("--owner", default="codex")
    handoff_parser.add_argument("--source-ref", default=PLACEHOLDER_TOKEN)
    handoff_parser.add_argument("--output")

    closure_parser = subparsers.add_parser("create-task-closure", help="Create a task closure skeleton")
    closure_parser.add_argument("--task-id", required=True)
    closure_parser.add_argument("--title", required=True)
    closure_parser.add_argument("--owner", default="codex")
    closure_parser.add_argument("--source-ref", default=PLACEHOLDER_TOKEN)
    closure_parser.add_argument("--output")

    capsule_parser = subparsers.add_parser("create-session-capsule", help="Create a session capsule skeleton")
    capsule_parser.add_argument("--task-id", required=True)
    capsule_parser.add_argument("--capsule-id", required=True)
    capsule_parser.add_argument("--owner", default="codex")
    capsule_parser.add_argument("--source-ref", default=PLACEHOLDER_TOKEN)
    capsule_parser.add_argument("--output")

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Print the recommended new-session bundle")
    bootstrap_parser.add_argument("--task-record")
    bootstrap_parser.add_argument("--previous-closure")
    bootstrap_parser.add_argument("--session-capsule")

    args = parser.parse_args(argv)
    workspace = _default_workspace()

    if args.command == "init":
        workspace.ensure_layout()
        workspace.write_index()
        return _print_validation(workspace.validate())

    if args.command == "validate":
        return _print_validation(workspace.validate())

    if args.command == "render":
        path = workspace.write_index()
        print(workspace.relpath(path))
        return 0

    if args.command == "create-task-handoff":
        output = Path(args.output) if args.output else None
        path = workspace.create_task_handoff(
            task_id=args.task_id,
            title=args.title,
            owner=args.owner,
            source_ref=args.source_ref,
            output=output,
        )
        print(workspace.relpath(path))
        return 0

    if args.command == "create-task-closure":
        output = Path(args.output) if args.output else None
        path = workspace.create_task_closure(
            task_id=args.task_id,
            title=args.title,
            owner=args.owner,
            source_ref=args.source_ref,
            output=output,
        )
        print(workspace.relpath(path))
        return 0

    if args.command == "create-session-capsule":
        output = Path(args.output) if args.output else None
        path = workspace.create_session_capsule(
            task_id=args.task_id,
            capsule_id=args.capsule_id,
            owner=args.owner,
            source_ref=args.source_ref,
            output=output,
        )
        print(workspace.relpath(path))
        return 0

    if args.command == "bootstrap":
        task_record = Path(args.task_record) if args.task_record else None
        previous_closure = Path(args.previous_closure) if args.previous_closure else None
        session_capsule = Path(args.session_capsule) if args.session_capsule else None
        print(
            workspace.build_bootstrap_bundle(
                task_record=task_record,
                previous_closure=previous_closure,
                session_capsule=session_capsule,
            )
        )
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
