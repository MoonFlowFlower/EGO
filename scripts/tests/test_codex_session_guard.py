from __future__ import annotations

import copy
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


def live_route_state() -> dict:
    return codex_session_guard._load_yaml(  # noqa: SLF001
        ROOT / "docs" / "PROGRAM_STATE_UNIFIED.yaml",
        code="missing_program_state",
    )


def valid_visible_life_phase_b_scope(state: dict) -> dict:
    fingerprint = codex_session_guard.compute_route_fingerprint(state)
    revision = state["route_guard"]["route_revision_id"]
    return {
        "task_id": codex_session_guard.VISIBLE_LIFE_TASK_ID,
        "task_kind": "local_product_clock_visible_playground",
        "requested_action_id": codex_session_guard.VISIBLE_LIFE_IMPLEMENT_ACTION_ID,
        "source_route_revision_id": revision,
        "source_route_fingerprint": fingerprint,
        "expected_target_route_revision_id": revision,
        "independent_red_review_required": False,
        "red_review_ref": None,
        "allowed_mutation_paths": list(codex_session_guard.VISIBLE_LIFE_TARGETS),
        "migration_exception": {},
        "raw": {"execution_requested": True},
    }


def valid_visible_life_transition_scope() -> dict:
    return {
        "task_id": codex_session_guard.VISIBLE_LIFE_TASK_ID,
        "task_kind": "operator_authorized_red_route_replacement",
        "requested_action_id": codex_session_guard.VISIBLE_LIFE_TRANSITION_ACTION_ID,
        "source_route_revision_id": codex_session_guard.CARD2_SYNC_ROUTE_REVISION,
        "source_route_fingerprint": "39775f663c17adf8dc0efb777d3ad49ee75181c43fea4546808e3dd48a697881",
        "expected_target_route_revision_id": codex_session_guard.VISIBLE_LIFE_ROUTE_REVISION,
        "independent_red_review_required": True,
        "red_review_ref": codex_session_guard.VISIBLE_LIFE_RED_REVIEW_PATH,
        "allowed_mutation_paths": [
            codex_session_guard.VISIBLE_LIFE_TASK_PREFIX,
            "docs/PROGRAM_STATE_UNIFIED.yaml",
            "docs/STATUS.md",
            "docs/codex/tasks/TASK_LANE_INDEX.md",
            "artifacts/reports/program_state_summary.md",
            "scripts/codex_session_guard.py",
            "scripts/codex/verify_route_convergence.py",
            "scripts/tests/test_codex_session_guard.py",
            "scripts/tests/test_route_governance_supersession.py",
        ],
        "raw": {"execution_requested": False},
    }


def blocker_reasons(blockers: list[dict]) -> set[str]:
    return {str(blocker.get("reason")) for blocker in blockers}


def validate_scope(state: dict, scope: dict, **overrides) -> list[dict]:
    params = {
        "scope": scope,
        "program_state": state,
        "changed_paths": list(codex_session_guard.VISIBLE_LIFE_TARGETS),
        "added_task_dirs": [],
        "red_triggers": [],
        "execution_requested": True,
    }
    params.update(overrides)
    return codex_session_guard.validate_route_mutation_scope(**params)


def test_route_scope_rejects_stale_fingerprint() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)
    scope["source_route_fingerprint"] = "0" * 64

    assert "stale_route_fingerprint" in blocker_reasons(validate_scope(state, scope))


def test_route_scope_rejects_wrong_requested_action() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)
    scope["requested_action_id"] = "bank_UNBOUND_ROUTE_CARD"

    assert "ROUTE_ACTION_NOT_BOUND" in blocker_reasons(validate_scope(state, scope))


def test_route_scope_rejects_second_task_directory() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)

    blockers = validate_scope(
        state,
        scope,
        added_task_dirs=[
            "docs/codex/tasks/one",
            "docs/codex/tasks/two",
        ],
    )
    assert "multiple_task_directories" in blocker_reasons(blockers)


def test_authority_change_requires_red_review_ref() -> None:
    state = live_route_state()
    scope = valid_visible_life_transition_scope()
    scope["red_review_ref"] = None

    blockers = validate_scope(
        state,
        scope,
        changed_paths=[
            "docs/PROGRAM_STATE_UNIFIED.yaml",
            f"{codex_session_guard.VISIBLE_LIFE_TASK_PREFIX}STAGE_CARD.md",
        ],
        added_task_dirs=[codex_session_guard.VISIBLE_LIFE_TASK_PREFIX.rstrip("/")],
        red_triggers=[{"type": "authority_path", "path": "docs/PROGRAM_STATE_UNIFIED.yaml"}],
    )
    assert "authority_change_without_red_review_ref" in blocker_reasons(blockers)


def test_route_scope_rejects_wrong_visible_life_task_kind() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)
    scope["task_kind"] = "governance_only_validator_repair"

    assert "visible_life_phase_b_task_kind_mismatch" in blocker_reasons(validate_scope(state, scope))


def test_visible_life_transition_is_exactly_bound_to_old_revision_and_fingerprint() -> None:
    state = live_route_state()
    scope = valid_visible_life_transition_scope()
    changed = [
        "docs/PROGRAM_STATE_UNIFIED.yaml",
        f"{codex_session_guard.VISIBLE_LIFE_TASK_PREFIX}STAGE_CARD.md",
    ]
    blockers = validate_scope(
        state,
        scope,
        changed_paths=changed,
        added_task_dirs=[codex_session_guard.VISIBLE_LIFE_TASK_PREFIX.rstrip("/")],
        execution_requested=False,
    )
    reasons = blocker_reasons(blockers)
    assert "stale_route_fingerprint" not in reasons
    assert "source_route_revision_mismatch" not in reasons
    assert "ROUTE_ACTION_NOT_BOUND" not in reasons

    scope["source_route_fingerprint"] = "0" * 64
    assert "stale_route_fingerprint" in blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=changed,
            added_task_dirs=[codex_session_guard.VISIBLE_LIFE_TASK_PREFIX.rstrip("/")],
            execution_requested=False,
        )
    )


def test_visible_life_transition_cannot_be_reused_after_task_directory_exists() -> None:
    state = live_route_state()
    scope = valid_visible_life_transition_scope()
    changed = [
        "docs/PROGRAM_STATE_UNIFIED.yaml",
        f"{codex_session_guard.VISIBLE_LIFE_TASK_PREFIX}STAGE_CARD.md",
    ]

    reasons = blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=changed,
            added_task_dirs=[],
            execution_requested=False,
        )
    )

    assert "visible_life_transition_reused_or_invalid" in reasons
    assert "stale_route_fingerprint" in reasons


def test_untouched_historical_mechanism_text_does_not_trigger_red_review() -> None:
    policy = {
        "authority_path_patterns": ["docs/PROGRAM_STATE_UNIFIED.yaml"],
        "diff_added_claim_terms": ["mechanism"],
        "generated_view_paths": [],
    }
    triggers = codex_session_guard.classify_red_review_triggers(
        changed_paths=["scripts/tests/test_codex_session_guard.py"],
        diff_added_lines={
            "scripts/tests/test_codex_session_guard.py": ["assert historical_artifact_is_untouched"],
            "artifacts/historical/report.md": ["mechanism"],
        },
        policy=policy,
    )

    assert triggers == []


def test_byte_equal_generated_view_only_does_not_trigger_red_review() -> None:
    path = "docs/STATUS.md"
    policy = {
        "authority_path_patterns": ["docs/*STATUS*.md"],
        "diff_added_claim_terms": ["enabled"],
        "generated_view_paths": [path],
    }
    triggers = codex_session_guard.classify_red_review_triggers(
        changed_paths=[path],
        diff_added_lines={path: ["enabled"]},
        policy=policy,
        generated_view_matches={path},
    )

    assert triggers == []


def test_valid_visible_life_phase_b_scope_admits_exact_six(monkeypatch) -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)
    monkeypatch.setattr(
        codex_session_guard,
        "compute_visible_life_phase_b_dependencies",
        lambda *_args, **_kwargs: {"all_satisfied": True, "dependencies": {"test": True}},
    )

    assert validate_scope(state, scope) == []


def test_self_declared_false_cannot_hide_execution_in_actual_changed_paths() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)
    scope["raw"]["execution_requested"] = False

    reasons = blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=[*codex_session_guard.VISIBLE_LIFE_TARGETS, "EgoOperator/agent_base.py"],
        )
    )
    assert "visible_life_phase_b_execution_flag_mismatch" in reasons
    assert "visible_life_changed_path_outside_exact_six" in reasons


def test_visible_life_scope_cannot_replace_exact_files_with_directory_prefix() -> None:
    result = codex_session_guard.validate_visible_life_action_paths(
        changed_paths=codex_session_guard.VISIBLE_LIFE_TARGETS,
        scope_allowed_paths=["labs/ego_life_playground_v0/"],
        require_complete_set=True,
    )

    assert result["status"] == "fail"
    assert "visible_life_scope_exact_six_mismatch" in result["errors"]


def test_nonempty_red_review_string_is_not_provenance() -> None:
    result = codex_session_guard.validate_red_review_record(
        f"{codex_session_guard.VISIBLE_LIFE_TASK_PREFIX}NOT_A_RECEIPT",
        require_committed=False,
    )

    assert result == {"status": "fail", "errors": ["candidate_red_review_record_unavailable"]}
