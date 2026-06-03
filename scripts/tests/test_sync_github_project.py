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


def write_two_task_board(tmp_path: Path) -> Path:
    path = tmp_path / "TASK_BOARD.yaml"
    path.write_text(
        """
version: 1
tasks:
  - id: T-1
    title: "EgoSubject: Existing mirror task"
    kind: task
    parent: null
    status: accepted
    layer: test
    owner: codex
    observation_class: deterministic_local
    evidence_level: E2
    claim_ceiling: Existing mirror sync candidate pass
    next_action: "Update cached mirror."
    acceptance:
      - "Cached mirror is updated."
    rollback: "Remove the mirror update."
    canonical_sources:
      - "test"
    external_refs:
      github_issue: "https://github.com/pen364692088/EGO/issues/1"
  - id: T-2
    title: "EgoSubject: Historical accepted task"
    kind: task
    parent: null
    status: accepted
    layer: test
    owner: codex
    observation_class: deterministic_local
    evidence_level: E2
    claim_ceiling: Historical local task pass
    next_action: "Do not create noisy historical mirror in existing scope."
    acceptance:
      - "No create_issue in existing scope."
    rollback: "No remote mutation."
    canonical_sources:
      - "test"
    external_refs: {}
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


def test_existing_scope_suppresses_uncached_issue_creation(tmp_path: Path) -> None:
    board = write_two_task_board(tmp_path)
    state = write_state(tmp_path)

    code, result = run_cli(FakeGh(), ["--board", str(board), "--state", str(state), "plan", "--scope", "existing"])

    assert code == 0
    assert result["scope"] == "existing"
    assert result["task_count"] == 1
    assert result["skipped_task_count"] == 1
    assert all(operation["op"] != "create_issue" for operation in result["operations"])


def test_all_scope_still_plans_missing_issue_creation(tmp_path: Path) -> None:
    board = write_two_task_board(tmp_path)
    state = write_state(tmp_path)

    code, result = run_cli(FakeGh(), ["--board", str(board), "--state", str(state), "plan"])

    assert code == 0
    assert result["scope"] == "all"
    assert any(operation["op"] == "create_issue" and operation["task_id"] == "T-2" for operation in result["operations"])


def test_task_id_filter_allows_one_uncached_current_task_creation(tmp_path: Path) -> None:
    board = write_two_task_board(tmp_path)
    state = write_state(tmp_path)

    code, result = run_cli(
        FakeGh(),
        ["--board", str(board), "--state", str(state), "plan", "--task-id", "T-2", "--project-status"],
    )

    assert code == 0
    assert result["task_ids"] == ["T-2"]
    assert result["task_count"] == 1
    assert result["operation_count"] == 1
    assert result["operations"] == [
        {
            "op": "create_issue",
            "task_id": "T-2",
            "title": "EgoSubject: Historical accepted task",
            "body_hash": result["operations"][0]["body_hash"],
            "desired_state": "closed",
            "project_status": "Done",
        }
    ]


def test_all_scope_project_status_marks_new_issue_creation(tmp_path: Path) -> None:
    board = write_two_task_board(tmp_path)
    state = write_state(tmp_path)

    code, result = run_cli(FakeGh(), ["--board", str(board), "--state", str(state), "plan", "--project-status"])

    assert code == 0
    create_ops = [operation for operation in result["operations"] if operation["op"] == "create_issue"]
    assert any(operation["task_id"] == "T-2" and operation["project_status"] == "Done" for operation in create_ops)


def test_project_status_mapping_is_available_for_existing_scope(tmp_path: Path) -> None:
    board = write_board(tmp_path, status="accepted")
    state = write_state(tmp_path)

    code, result = run_cli(
        FakeGh(),
        ["--board", str(board), "--state", str(state), "plan", "--scope", "existing", "--project-status"],
    )

    assert code == 0
    assert result["project_status"] is True
    assert {
        "op": "set_project_status",
        "task_id": "T-1",
        "issue": 1,
        "project_status": "Done",
    } in result["operations"]


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
    assert len(payload["results"]) == 2
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
