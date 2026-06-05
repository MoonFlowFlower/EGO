from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex_session_guard.py"
spec = importlib.util.spec_from_file_location("codex_session_guard", MODULE_PATH)
codex_session_guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = codex_session_guard
spec.loader.exec_module(codex_session_guard)


class FakeRunner(codex_session_guard.GuardRunner):
    def __init__(
        self,
        *,
        git_status: str = "",
        origin: str = "git@github.com:MoonFlowFlower/EGO.git",
        branch: str = "main",
        head: str = "abc1234",
        upstream: str = "0\t0",
        gh_path: str | None = None,
        doctor_returncode: int = 0,
        doctor_stdout: str | None = None,
    ) -> None:
        self.git_status = git_status
        self.origin = origin
        self.branch = branch
        self.head = head
        self.upstream = upstream
        self.gh_path = gh_path
        self.doctor_returncode = doctor_returncode
        self.doctor_stdout = doctor_stdout or json.dumps({"status": "ok"})
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: list[str]):
        key = tuple(args)
        self.calls.append(key)
        if key == ("git", "remote", "get-url", "origin"):
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout=self.origin + "\n", stderr="")
        if key == ("git", "branch", "--show-current"):
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout=self.branch + "\n", stderr="")
        if key == ("git", "rev-parse", "--short", "HEAD"):
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout=self.head + "\n", stderr="")
        if key == ("git", "rev-list", "--left-right", "--count", "@{u}...HEAD"):
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout=self.upstream + "\n", stderr="")
        if key == ("git", "status", "--short", "--untracked-files=all"):
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout=self.git_status, stderr="")
        if args and args[-1] == "doctor":
            return codex_session_guard.CommandResult(
                args=args,
                returncode=self.doctor_returncode,
                stdout=self.doctor_stdout,
                stderr="" if self.doctor_returncode == 0 else "doctor failed",
            )
        raise AssertionError(f"unexpected command: {args}")

    def which(self, name: str) -> str | None:
        assert name == "gh"
        return self.gh_path


def write_contract(tmp_path: Path, *, repo: str = "MoonFlowFlower/EGO", owner: str = "MoonFlowFlower") -> Path:
    path = tmp_path / "project_contract.yaml"
    path.write_text(
        f"""
version: 1
project:
  name: EGO
  repo: {repo}
  default_branch: main
github_project:
  owner: {owner}
  number: 1
  status_field: Status
task_state:
  source: local_board
  board_path: TASK_BOARD.yaml
  github_project_role: mirror
  outbox_path: artifacts/task_board/outbox.jsonl
allowed_mutation_paths:
  - .codex/project_contract.yaml
  - AGENTS.md
  - CODEX_MEMORY.md
  - scripts/
  - scripts/tests/
  - docs/codex/tasks/codex-session-bootstrap-closeout-v1/
  - Tasks/TASK_BOARD.yaml
commit_policy:
  mode: direct-main
  push: true
  require_scoped_staging: true
session_bootstrap:
  required: true
closeout_gate:
  required: true
  require_task_board_github_sync: true
  local_only_path_prefixes:
    - data/live2d/
    - Test/
  verification_commands:
    - python -m py_compile scripts/codex_session_guard.py
observation_classes:
  deterministic_local:
    closeout_allowed: true
auto_closeout:
  default_observation_class: deterministic_local
""",
        encoding="utf-8",
    )
    return path


def write_program_state(tmp_path: Path) -> Path:
    path = tmp_path / "PROGRAM_STATE_UNIFIED.yaml"
    path.write_text(
        """
program:
  current_phase: ego_operator_human_operator_trial_v2_protocol_ready_real_provider_recheck_pending
  current_layer: transition / operator-first
  highest_evidence_level: E3
  verification_level: V3
  next_minimal_action: Run real-provider human operator trial.
  status_owner: EgoOperator
""",
        encoding="utf-8",
    )
    return path


def write_memory(tmp_path: Path) -> Path:
    path = tmp_path / "CODEX_MEMORY.md"
    path.write_text(
        """
# CODEX_MEMORY.md
> Source of truth: `.codex/memory/project_truth.jsonl` + `.codex/memory/user_preferences.jsonl`

| project-codex-memory-acceptance-v1 | Codex memory | source | rule |
| pref-auto-push-remote | 默认自动推送远端 | user_confirmation | until_user_overrides |
| pref-session-discipline | 保留任务边界新开会话纪律 | user_confirmation | until_user_overrides |

```bash
python3 scripts/codex_memory.py bootstrap
```
""",
        encoding="utf-8",
    )
    return path


def write_board(tmp_path: Path, *, status: str = "accepted") -> Path:
    path = tmp_path / "TASK_BOARD.yaml"
    path.write_text(
        f"""
version: 1
tasks:
  - id: T-1
    title: "Codex Toolkit: accepted workflow"
    kind: task
    parent: null
    status: {status}
    layer: codex_workflow
    owner: codex
    observation_class: deterministic_local
    evidence_level: E2
    claim_ceiling: Codex workflow local candidate pass
    next_action: "No ready work."
    acceptance:
      - "Accepted."
    rollback: "Remove task."
    canonical_sources:
      - "test"
    external_refs: {{}}
""",
        encoding="utf-8",
    )
    return path


def write_mutation_scope(tmp_path: Path, allowed_paths: list[str]) -> Path:
    path = tmp_path / "MUTATION_SCOPE.yaml"
    allowed = "\n".join(f"  - {item}" for item in allowed_paths)
    path.write_text(
        f"""
schema_version: codex.mutation_scope.v1
task: test-task
expected_mutation_surface:
  - test fixture mutation surface
allowed_mutation_paths:
{allowed}
claim_ceiling: test task-scoped mutation allowance only
""",
        encoding="utf-8",
    )
    return path


def build_snapshot(tmp_path: Path, runner: FakeRunner, *, repo: str = "MoonFlowFlower/EGO") -> dict:
    contract = write_contract(tmp_path, repo=repo)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path)
    return codex_session_guard.build_bootstrap_snapshot(
        contract_path=contract,
        program_state_path=program,
        codex_memory_path=memory,
        task_board_path=board,
        runner=runner,
    )


def test_bootstrap_snapshot_reads_program_memory_board_and_valid_no_ready_task(tmp_path: Path) -> None:
    payload = build_snapshot(tmp_path, FakeRunner())

    assert payload["status"] == "ok"
    assert payload["program_state"]["current_phase"] == "ego_operator_human_operator_trial_v2_protocol_ready_real_provider_recheck_pending"
    assert payload["codex_memory"]["has_auto_push_preference"] is True
    assert payload["remote_contract_check"]["status"] == "ok"
    assert payload["task_board"]["plan_next"]["stop_reason"] == "no_ready_task"
    assert payload["task_board"]["plan_next"]["valid_stop"] is True
    assert payload["github_sync"]["status"] == "unavailable"
    assert payload["github_sync"]["reason"] == "gh_not_found"


def test_remote_mismatch_is_reported_without_rewriting_old_refs(tmp_path: Path) -> None:
    payload = build_snapshot(tmp_path, FakeRunner(), repo="pen364692088/EGO")

    assert payload["remote_contract_check"] == {
        "status": "remote_contract_mismatch",
        "contract_repo": "pen364692088/EGO",
        "origin_repo": "MoonFlowFlower/EGO",
    }


def test_dirty_state_distinguishes_scoped_local_only_and_unsafe(tmp_path: Path) -> None:
    status = "\n".join(
        [
            " M scripts/codex_session_guard.py",
            "?? data/live2d/model.model3.json",
            "?? Test/AI.md",
            "?? random.tmp",
        ]
    )
    payload = build_snapshot(tmp_path, FakeRunner(git_status=status + "\n"))

    assert payload["dirty_state"]["counts"]["scoped"] == 1
    assert payload["dirty_state"]["counts"]["task_scoped"] == 0
    assert payload["dirty_state"]["counts"]["local_only"] == 2
    assert payload["dirty_state"]["counts"]["unsafe"] == 1


def test_closeout_check_allows_staged_deletion_under_task_scoped_allowance(tmp_path: Path) -> None:
    contract = write_contract(tmp_path)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path)
    scope = write_mutation_scope(tmp_path, ["legacy/old-runtime/"])

    payload = codex_session_guard.build_closeout_check(
        contract_path=contract,
        program_state_path=program,
        codex_memory_path=memory,
        task_board_path=board,
        mutation_scope_path=scope,
        runner=FakeRunner(git_status="D  legacy/old-runtime/app.py\n"),
    )

    assert payload["eligible"] is True
    assert payload["dirty_state"]["counts"]["task_scoped"] == 1
    assert payload["dirty_state"]["counts"]["unsafe"] == 0
    assert payload["task_mutation_scope"]["path"] == str(scope)
    assert "legacy/old-runtime/" not in codex_session_guard.codex_project_autopilot.load_contract(contract).allowed_mutation_paths


def test_closeout_check_blocks_same_deletion_without_task_scope_and_explains_group(tmp_path: Path) -> None:
    contract = write_contract(tmp_path)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path)

    payload = codex_session_guard.build_closeout_check(
        contract_path=contract,
        program_state_path=program,
        codex_memory_path=memory,
        task_board_path=board,
        runner=FakeRunner(git_status="D  legacy/old-runtime/app.py\n"),
    )

    assert payload["eligible"] is False
    blocker = next(reason for reason in payload["blocked_reasons"] if reason["reason"] == "unsafe_dirty_paths")
    assert blocker["groups"][0]["path_prefix"] == "legacy/old-runtime/"
    assert blocker["groups"][0]["staged_count"] == 1
    assert blocker["candidate_scoped_paths"] == ["legacy/old-runtime/"]


def test_closeout_check_blocks_staged_local_only_even_when_task_scope_allows_it(tmp_path: Path) -> None:
    contract = write_contract(tmp_path)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path)
    scope = write_mutation_scope(tmp_path, ["data/live2d/"])

    payload = codex_session_guard.build_closeout_check(
        contract_path=contract,
        program_state_path=program,
        codex_memory_path=memory,
        task_board_path=board,
        mutation_scope_path=scope,
        runner=FakeRunner(git_status="A  data/live2d/model.model3.json\n"),
    )

    assert payload["eligible"] is False
    assert payload["dirty_state"]["counts"]["local_only"] == 1
    assert payload["dirty_state"]["counts"]["task_scoped"] == 0
    assert any(reason["reason"] == "local_only_paths_staged" for reason in payload["blocked_reasons"])


def test_closeout_check_blocks_task_board_change_when_github_sync_unavailable(tmp_path: Path) -> None:
    contract = write_contract(tmp_path)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path, status="active")
    payload = codex_session_guard.build_closeout_check(
        contract_path=contract,
        program_state_path=program,
        codex_memory_path=memory,
        task_board_path=board,
        runner=FakeRunner(git_status="M  Tasks/TASK_BOARD.yaml\n"),
    )

    assert payload["eligible"] is False
    assert any(reason["reason"] == "remote_sync_unavailable" for reason in payload["blocked_reasons"])
    assert payload["github_sync"]["reason"] == "gh_not_found"


def test_cli_writes_markdown_out(tmp_path: Path) -> None:
    contract = write_contract(tmp_path)
    program = write_program_state(tmp_path)
    memory = write_memory(tmp_path)
    board = write_board(tmp_path)
    out_path = tmp_path / "boot.md"
    stream = io.StringIO()

    code = codex_session_guard.main(
        [
            "--contract",
            str(contract),
            "--program-state",
            str(program),
            "--codex-memory",
            str(memory),
            "--task-board",
            str(board),
            "bootstrap",
            "--format",
            "markdown",
            "--out",
            str(out_path),
        ],
        runner=FakeRunner(),
        stdout=stream,
    )

    assert code == 0
    assert "# Codex Boot Snapshot" in out_path.read_text(encoding="utf-8")
    assert "current_phase" in stream.getvalue()
