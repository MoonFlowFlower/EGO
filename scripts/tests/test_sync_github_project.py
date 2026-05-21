from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "sync_github_project.py"
spec = importlib.util.spec_from_file_location("sync_github_project", MODULE_PATH)
sync_github_project = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = sync_github_project
spec.loader.exec_module(sync_github_project)


class FakeGh(sync_github_project.github_project_task.GhClient):
    def __init__(self, responses: dict[tuple[str, ...], list[str] | str] | None = None) -> None:
        self.responses = {
            key: list(value) if isinstance(value, list) else [value]
            for key, value in (responses or {}).items()
        }
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: list[str]) -> str:
        key = tuple(args)
        self.calls.append(key)
        if key not in self.responses or not self.responses[key]:
            raise AssertionError(f"Unexpected gh call: {args}")
        value = self.responses[key].pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def run_cli(fake: FakeGh, argv: list[str]) -> tuple[int, dict]:
    out = io.StringIO()
    code = sync_github_project.main(argv, client=fake, stdout=out)
    return code, json.loads(out.getvalue())


def write_board(tmp_path: Path, *, status: str = "active") -> Path:
    path = tmp_path / "TASK_BOARD.yaml"
    path.write_text(
        f"""
version: 1
tasks:
  - id: T-1
    title: "EgoSubject: Local board test"
    kind: task
    parent: null
    status: {status}
    layer: test
    owner: codex
    observation_class: deterministic_local
    evidence_level: E2
    claim_ceiling: Local board sync candidate pass
    next_action: "Prove sync planning."
    acceptance:
      - "Plan is generated."
    rollback: "Remove the task."
    canonical_sources:
      - "test"
    external_refs:
      github_issue: "https://github.com/pen364692088/EGO/issues/1"
""",
        encoding="utf-8",
    )
    return path


def write_state(tmp_path: Path, *, body_hash: str | None = None, state: str = "open") -> Path:
    path = tmp_path / "sync_state.json"
    payload = {
        "version": 1,
        "repo": "pen364692088/EGO",
        "issues": {
            "T-1": {
                "number": 1,
                "url": "https://github.com/pen364692088/EGO/issues/1",
                "title_hash": "old",
                "body_hash": body_hash or "old",
                "state": state,
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_doctor_reads_local_board_without_github(tmp_path: Path) -> None:
    board = write_board(tmp_path)
    state = write_state(tmp_path)
    fake = FakeGh()

    code, payload = run_cli(fake, ["--board", str(board), "--state", str(state), "doctor"])

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["task_count"] == 1
    assert fake.calls == []


def test_sync_dry_run_generates_outbox_without_mutation(tmp_path: Path) -> None:
    board = write_board(tmp_path)
    state = write_state(tmp_path)
    outbox = tmp_path / "outbox.jsonl"
    log = tmp_path / "sync_log.jsonl"
    fake = FakeGh()

    code, payload = run_cli(
        fake,
        [
            "--board",
            str(board),
            "--state",
            str(state),
            "--outbox",
            str(outbox),
            "--sync-log",
            str(log),
            "sync",
            "--dry-run",
        ],
    )

    assert code == 0
    assert payload["operation_count"] == 1
    assert payload["operations"][0]["op"] == "update_issue"
    assert outbox.read_text(encoding="utf-8").strip()
    assert log.read_text(encoding="utf-8").strip()
    assert fake.calls == []


def test_noop_diff_produces_no_operations(tmp_path: Path) -> None:
    board = write_board(tmp_path)
    task = sync_github_project.load_yaml(board)["tasks"][0]
    state = write_state(tmp_path, body_hash=sync_github_project.sha256_text(sync_github_project.desired_issue_body(task)))
    payload = json.loads(state.read_text(encoding="utf-8"))
    payload["issues"]["T-1"]["title_hash"] = sync_github_project.sha256_text(task["title"])
    state.write_text(json.dumps(payload), encoding="utf-8")

    code, result = run_cli(FakeGh(), ["--board", str(board), "--state", str(state), "plan"])

    assert code == 0
    assert result["operation_count"] == 0


def test_execute_uses_cached_issue_id_and_updates_state(tmp_path: Path, monkeypatch) -> None:
    board = write_board(tmp_path, status="accepted")
    state = write_state(tmp_path, state="open")
    monkeypatch.setattr(sync_github_project.time, "sleep", lambda seconds: None)
    fake = FakeGh(
        {
            (
                "issue",
                "edit",
                "1",
                "--repo",
                "pen364692088/EGO",
                "--title",
                "EgoSubject: Local board test",
                "--body",
                sync_github_project.desired_issue_body(sync_github_project.load_yaml(board)["tasks"][0]),
            ): "",
            ("issue", "close", "1", "--repo", "pen364692088/EGO"): "",
        }
    )

    code, payload = run_cli(
        fake,
        [
            "--board",
            str(board),
            "--state",
            str(state),
            "--outbox",
            str(tmp_path / "outbox.jsonl"),
            "--sync-log",
            str(tmp_path / "sync_log.jsonl"),
            "sync",
            "--execute",
        ],
    )

    assert code == 0
    assert payload["operation_count"] == 2
    assert not any(call[:2] == ("project", "item-list") for call in fake.calls)
    updated = json.loads(state.read_text(encoding="utf-8"))
    assert updated["issues"]["T-1"]["state"] == "closed"


def test_rate_limit_error_is_structured(tmp_path: Path) -> None:
    board = write_board(tmp_path)
    state = write_state(tmp_path)
    task = sync_github_project.load_yaml(board)["tasks"][0]
    error = sync_github_project.github_project_task.GhCommandError(
        ["issue", "edit", "1"],
        1,
        "",
        "GraphQL: API rate limit exceeded",
    )
    fake = FakeGh(
        {
            (
                "issue",
                "edit",
                "1",
                "--repo",
                "pen364692088/EGO",
                "--title",
                task["title"],
                "--body",
                sync_github_project.desired_issue_body(task),
            ): error,
            ("api", "rate_limit"): json.dumps(
                {"resources": {"graphql": {"limit": 5000, "remaining": 0, "used": 5000, "reset": 9999999999}}}
            ),
        }
    )

    code, payload = run_cli(
        fake,
        [
            "--board",
            str(board),
            "--state",
            str(state),
            "--outbox",
            str(tmp_path / "outbox.jsonl"),
            "--sync-log",
            str(tmp_path / "sync_log.jsonl"),
            "--rate-limit-max-wait-seconds",
            "1",
            "sync",
            "--execute",
        ],
    )

    assert code == 1
    assert payload["error"] == "github_rate_limited"
