from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest


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


def historical_v4_route_state() -> dict:
    state = copy.deepcopy(live_route_state())
    route_guard = state["route_guard"]
    route_guard["schema_version"] = "ego.route_guard.v4"
    route_guard["route_revision_id"] = codex_session_guard.VISIBLE_LIFE_CORE_ROUTE_REVISION
    route_guard["authority_source"] = copy.deepcopy(route_guard["predecessor_authority_source"])
    route_guard.pop("predecessor_authority_source")
    transcribed = route_guard["transcribed_itl_product"]
    transcribed["product_axis_state"] = copy.deepcopy(transcribed["predecessor_product_axis_state"])
    route_guard["product_authority"] = copy.deepcopy(route_guard["predecessor_product_authority"])
    route_guard.pop("predecessor_product_authority")
    return state


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


def valid_visible_life_core_sync_scope() -> dict:
    return {
        "task_id": codex_session_guard.VISIBLE_LIFE_CORE_TASK_ID,
        "task_kind": "cross_repo_product_core_authority_sync",
        "requested_action_id": codex_session_guard.VISIBLE_LIFE_CORE_SYNC_ACTION_ID,
        "source_route_revision_id": codex_session_guard.VISIBLE_LIFE_ROUTE_REVISION,
        "source_route_fingerprint": "63a54cb04c634042e27b1af9500cbb1dd87d5d9941959a5abfeac28954f1f4de",
        "expected_target_route_revision_id": codex_session_guard.VISIBLE_LIFE_CORE_ROUTE_REVISION,
        "independent_red_review_required": True,
        "red_review_ref": codex_session_guard.VISIBLE_LIFE_CORE_RED_REVIEW_PATH,
        "allowed_mutation_paths": list(codex_session_guard.VISIBLE_LIFE_CORE_SYNC_PATHS),
        "migration_exception": {},
        "raw": {
            "execution_requested": True,
            "itl_product_axis_commit": codex_session_guard.VISIBLE_LIFE_CORE_ITL_COMMIT,
            "itl_product_axis_route_id": codex_session_guard.VISIBLE_LIFE_CORE_ITL_ROUTE_ID,
        },
    }


def valid_v1_ready_sync_scope() -> dict:
    raw = codex_session_guard._load_yaml(  # noqa: SLF001
        ROOT / codex_session_guard.V1_READY_SCOPE_PATH,
        code="missing_v1_ready_scope",
    )
    return {
        "task_id": codex_session_guard.V1_READY_TASK_ID,
        "task_kind": "cross_repo_v1_ready_authority_sync",
        "requested_action_id": codex_session_guard.V1_READY_SYNC_ACTION_ID,
        "source_route_revision_id": codex_session_guard.VISIBLE_LIFE_CORE_ROUTE_REVISION,
        "source_route_fingerprint": "2446c65920f96a9a49d9ae654a0f106e8fb0bcaf41e023d4405c46c083a0f005",
        "expected_target_route_revision_id": codex_session_guard.V1_READY_ROUTE_REVISION,
        "independent_red_review_required": True,
        "red_review_ref": codex_session_guard.V1_READY_RED_REVIEW_PATH,
        "allowed_mutation_paths": list(codex_session_guard.V1_READY_SYNC_PATHS),
        "migration_exception": {},
        "raw": raw,
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


def test_route_scope_rejects_wrong_visible_life_core_sync_task_kind(monkeypatch) -> None:
    state = historical_v4_route_state()
    scope = valid_visible_life_core_sync_scope()
    scope["task_kind"] = "governance_only_validator_repair"
    monkeypatch.setattr(
        codex_session_guard,
        "validate_visible_life_core_product_authority",
        lambda *_args, **_kwargs: {"status": "pass", "errors": []},
    )

    assert "visible_life_core_sync_task_kind_mismatch" in blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=[
                "docs/PROGRAM_STATE_UNIFIED.yaml",
                f"{codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md",
            ],
            added_task_dirs=[codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")],
        )
    )


def test_visible_life_core_sync_is_exactly_bound_to_v0_revision_and_fingerprint(monkeypatch) -> None:
    state = historical_v4_route_state()
    scope = valid_visible_life_core_sync_scope()
    changed = [
        "docs/PROGRAM_STATE_UNIFIED.yaml",
        f"{codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md",
    ]
    monkeypatch.setattr(
        codex_session_guard,
        "validate_visible_life_core_product_authority",
        lambda *_args, **_kwargs: {"status": "pass", "errors": []},
    )
    blockers = validate_scope(
        state,
        scope,
        changed_paths=changed,
        added_task_dirs=[codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")],
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
            added_task_dirs=[codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")],
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


def test_consumed_visible_life_phase_b_action_is_not_reusable() -> None:
    state = live_route_state()
    scope = valid_visible_life_phase_b_scope(state)

    assert "ROUTE_ACTION_NOT_BOUND" in blocker_reasons(validate_scope(state, scope))


def test_core_sync_execution_flag_cannot_be_self_declared_false(monkeypatch) -> None:
    state = historical_v4_route_state()
    scope = valid_visible_life_core_sync_scope()
    scope["raw"]["execution_requested"] = False
    monkeypatch.setattr(
        codex_session_guard,
        "validate_visible_life_core_product_authority",
        lambda *_args, **_kwargs: {"status": "pass", "errors": []},
    )

    reasons = blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=[
                "docs/PROGRAM_STATE_UNIFIED.yaml",
                f"{codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md",
            ],
            added_task_dirs=[codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")],
        )
    )
    assert "visible_life_core_sync_execution_flag_mismatch" in reasons


def test_stale_local_core_adopt_action_is_not_a_sync_authority(monkeypatch) -> None:
    state = historical_v4_route_state()
    scope = valid_visible_life_core_sync_scope()
    scope["requested_action_id"] = codex_session_guard.VISIBLE_LIFE_CORE_STALE_ADOPT_ACTION_ID
    monkeypatch.setattr(
        codex_session_guard,
        "validate_visible_life_core_product_authority",
        lambda *_args, **_kwargs: {"status": "pass", "errors": []},
    )

    reasons = blocker_reasons(
        validate_scope(
            state,
            scope,
            changed_paths=[
                "docs/PROGRAM_STATE_UNIFIED.yaml",
                f"{codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md",
            ],
            added_task_dirs=[codex_session_guard.VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")],
        )
    )
    assert "ROUTE_ACTION_NOT_BOUND" in reasons


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


def core_evidence_fixture(tmp_path: Path, monkeypatch):
    paths = {
        "manifest_path": tmp_path / "manifest.json",
        "trace_path": tmp_path / "trace.jsonl",
        "database_path": tmp_path / "trace.sqlite3",
        "validation_report_path": tmp_path / "report.json",
        "validator_path": tmp_path / "validator.py",
    }
    payloads = {
        "manifest_path": b'{"manifest":"computed"}\n',
        "trace_path": b'{"trace":"computed"}\n',
        "database_path": b"SQLite format 3\x00computed",
        "validator_path": b"# computed validator\n",
    }
    for key, payload in payloads.items():
        paths[key].write_bytes(payload)
    hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items() if key != "validation_report_path"}
    report = {
        "schema_version": "ego.life_core_v0_baseline_validation.v1",
        "task_id": codex_session_guard.VISIBLE_LIFE_CORE_TASK_ID,
        "baseline_id": "EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A",
        "computed_verdict": "PASS",
        "baseline_commit": codex_session_guard.VISIBLE_LIFE_CORE_BASELINE_COMMIT,
        "baseline_parent": codex_session_guard.VISIBLE_LIFE_CORE_BASELINE_PARENT,
        "baseline_tree": codex_session_guard.VISIBLE_LIFE_CORE_BASELINE_TREE,
        "exact_change_set_verified": True,
        "head_descends_from_baseline": True,
        "trace_payload_sha256": hashes["trace_path"],
        "trace_validation_status": "PASS",
        "trace_replay_status": "PASS",
        "trace_replay_input": "serialized_initial_state_and_typed_commands_from_sqlite_artifact",
        "database_path": str(paths["database_path"]),
        "database_payload_sha256": hashes["database_path"],
        "database_provenance_status": "PASS",
        "sqlite_recovery_status": "PASS",
        "sqlite_export_status": "PASS",
        "serialized_initial_state_status": "PASS",
        "direct_engine_replay_status": "PASS",
        "provenance": {
            "manifest_sha256": hashes["manifest_path"],
            "producer_code_path_hash": hashes["validator_path"],
        },
        "errors": [],
        "claim_ceiling": "bounded product engineering lineage only",
    }
    paths["validation_report_path"].write_text(json.dumps(report), encoding="utf-8")
    refs = {key: str(path) for key, path in paths.items()}
    monkeypatch.setattr(codex_session_guard, "VISIBLE_LIFE_CORE_BASELINE_REFS", refs)
    state = {"route_guard": {"product_authority": {"historical_baseline": dict(refs)}}}

    class EvidenceRunner:
        def __init__(self):
            self.report = dict(report)

        def run(self, args: list[str]):
            output = Path(args[args.index("--output") + 1])
            output.write_text(json.dumps(self.report), encoding="utf-8")
            return codex_session_guard.CommandResult(args=args, returncode=0, stdout="", stderr="")

    return state, paths, EvidenceRunner()


def test_core_evidence_gate_requires_callable_computed_pass(tmp_path: Path, monkeypatch) -> None:
    state, _paths, runner = core_evidence_fixture(tmp_path, monkeypatch)

    result = codex_session_guard.validate_visible_life_core_evidence(state, runner=runner)

    assert result["status"] == "pass"
    assert result["computed_critical"]["sqlite_recovery_status"] == "PASS"
    assert result["computed_critical"]["trace_replay_input"] == (
        "serialized_initial_state_and_typed_commands_from_sqlite_artifact"
    )


def test_core_evidence_gate_rejects_computed_sqlite_recovery_failure(tmp_path: Path, monkeypatch) -> None:
    state, _paths, runner = core_evidence_fixture(tmp_path, monkeypatch)
    runner.report["sqlite_recovery_status"] = "FAIL"

    result = codex_session_guard.validate_visible_life_core_evidence(state, runner=runner)

    assert result["status"] == "fail"
    assert "core_evidence_computed_sqlite_recovery_status_mismatch" in result["errors"]


@pytest.mark.parametrize(
    ("corrupt_key", "expected_error"),
    [
        ("manifest_path", "core_evidence_stored_manifest_sha256_mismatch"),
        ("validation_report_path", "core_evidence_stored_report_invalid"),
        ("trace_path", "core_evidence_stored_trace_sha256_mismatch"),
        ("database_path", "core_evidence_stored_database_sha256_mismatch"),
        ("validator_path", "core_evidence_stored_validator_sha256_mismatch"),
    ],
)
def test_core_evidence_gate_rejects_corrupted_banked_content(
    tmp_path: Path,
    monkeypatch,
    corrupt_key: str,
    expected_error: str,
) -> None:
    state, paths, runner = core_evidence_fixture(tmp_path, monkeypatch)
    paths[corrupt_key].write_bytes(paths[corrupt_key].read_bytes() + b"CORRUPTED")

    result = codex_session_guard.validate_visible_life_core_evidence(state, runner=runner)

    assert result["status"] == "fail"
    assert expected_error in result["errors"]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def _valid_phase_c_v2_receipt(manifest_sha: str, bundle_sha: str) -> dict:
    return {
        "schema_version": codex_session_guard.PHASE_C_V2_RECEIPT_SCHEMA_VERSION,
        "task_id": codex_session_guard.PHASE_C_V2_TASK_ID,
        "base_commit": codex_session_guard.PHASE_C_V2_EGO_BASE_COMMIT,
        "authority_manifest_sha256": manifest_sha,
        "review_bundle_sha256": bundle_sha,
        "review": {
            "spec_verdict": "SPEC_COMPLIANT",
            "code_quality_verdict": "CODE_QUALITY_APPROVED",
            "verdict": "NO_BLOCKING_FINDINGS",
            "blocking_findings": [],
        },
        "reviewer": {
            "reviewer": "Claude",
            "review_source": "Claude Web",
            "review_id": "review:phase-c-v2:001",
            "reviewer_session_id": "claude-web:independent",
            "executor_session_id": "codex:executor",
            "identity_assurance": "CONTROLLER_ATTESTED_LOCAL_ONLY",
            "cryptographic_identity_verified": False,
        },
    }


def _init_phase_c_v2_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Phase C Test")
    _git(repo, "config", "user.email", "phase-c@example.invalid")
    _git(repo, "fetch", "-q", str(ROOT), codex_session_guard.PHASE_C_V2_EGO_BASE_COMMIT)
    _git(repo, "reset", "-q", "--mixed", "FETCH_HEAD")


def _write_phase_c_v2_candidate(
    repo: Path,
    *,
    omit: str | None = None,
    extra: bool = False,
    mutate_authority=None,
) -> str:
    for relative in codex_session_guard.PHASE_C_V2_REVIEWED_PATHS:
        if relative == omit:
            continue
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == codex_session_guard.PHASE_C_V2_AUTHORITY_PATH:
            authority = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            if mutate_authority is not None:
                mutate_authority(authority)
            target.write_text(json.dumps(authority, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            target.write_text(f"phase-c-v2 fixture: {relative}\n", encoding="utf-8")
    if extra:
        (repo / "UNAUTHORIZED_PHASE_C_PATH.txt").write_text("extra\n", encoding="utf-8")
    _git(repo, "add", "--", *[p for p in codex_session_guard.PHASE_C_V2_REVIEWED_PATHS if p != omit])
    if extra:
        _git(repo, "add", "--", "UNAUTHORIZED_PHASE_C_PATH.txt")
    manifest = codex_session_guard.build_phase_c_v2_authority_manifest(repo=repo)
    authority_bytes = (repo / codex_session_guard.PHASE_C_V2_AUTHORITY_PATH).read_bytes()
    authority = codex_session_guard.validate_phase_c_v2_authority_bytes(authority_bytes)
    bundle = codex_session_guard.build_phase_c_v2_review_bundle(
        authority_manifest_sha256=manifest["authority_manifest_sha256"],
        authority_projection_sha256=authority.get("target_projection_sha256"),
    )
    receipt_path = repo / codex_session_guard.PHASE_C_V2_RECEIPT_PATH
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            _valid_phase_c_v2_receipt(
                manifest["authority_manifest_sha256"],
                bundle["review_bundle_sha256"],
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", codex_session_guard.PHASE_C_V2_RECEIPT_PATH)
    _git(repo, "commit", "-q", "-m", "phase-c-v2 candidate")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_phase_c_simplified_gate_strict_projection_and_typed_receipt_controls() -> None:
    authority = json.loads(
        (ROOT / codex_session_guard.PHASE_C_V2_AUTHORITY_PATH).read_text(encoding="utf-8")
    )
    assert codex_session_guard.validate_phase_c_v2_authority_payload(authority)["status"] == "pass"

    swapped = copy.deepcopy(authority)
    targets = swapped["v2"]["authorized_implementation_targets"]
    targets[0], targets[1] = targets[1], targets[0]
    assert "authority_projection_canonical_bytes_mismatch" in codex_session_guard.validate_phase_c_v2_authority_payload(swapped)["errors"]
    opened = copy.deepcopy(authority)
    opened["switches"]["enabled"] = True
    assert "authority_projection_canonical_bytes_mismatch" in codex_session_guard.validate_phase_c_v2_authority_payload(opened)["errors"]
    positive_float_zero = copy.deepcopy(authority)
    positive_float_zero["switches"]["science_weight"] = 0.0
    positive_zero_result = codex_session_guard.validate_phase_c_v2_authority_payload(
        positive_float_zero
    )
    assert "authority_projection_canonical_bytes_mismatch" in positive_zero_result["errors"]
    signed_zero = copy.deepcopy(authority)
    signed_zero["switches"]["science_weight"] = -0.0
    signed_zero_result = codex_session_guard.validate_phase_c_v2_authority_payload(signed_zero)
    assert "authority_projection_canonical_bytes_mismatch" in signed_zero_result["errors"]
    assert positive_zero_result["target_projection_sha256"] != signed_zero_result[
        "target_projection_sha256"
    ]

    assert codex_session_guard.parse_phase_c_v2_json(b'{"a":1,"a":2}')["errors"] == ["json_duplicate_key"]
    assert codex_session_guard.validate_phase_c_v2_authority_payload([])["status"] == "fail"

    receipt = _valid_phase_c_v2_receipt("a" * 64, "b" * 64)
    assert codex_session_guard.validate_phase_c_v2_receipt_payload(receipt)["status"] == "pass"
    contradictory = copy.deepcopy(receipt)
    contradictory["review"]["verdict"] = "BLOCKING_FINDINGS"
    assert "receipt_verdict_contradictory" in codex_session_guard.validate_phase_c_v2_receipt_payload(contradictory)["errors"]
    typed = copy.deepcopy(receipt)
    typed["reviewer"]["review_id"] = 7
    typed["reviewer"]["reviewer_session_id"] = ""
    typed["review"] = "NO_BLOCKING_FINDINGS"
    assert codex_session_guard.validate_phase_c_v2_receipt_payload(typed)["status"] == "fail"


def test_phase_c_simplified_gate_actual_git_union_and_validation_label(tmp_path: Path) -> None:
    repo = tmp_path / "paths"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Path Test")
    _git(repo, "config", "user.email", "paths@example.invalid")
    tracked = repo / codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[1]
    tracked.parent.mkdir(parents=True)
    tracked.write_text("base\n", encoding="utf-8")
    _git(repo, "add", "--", codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[1])
    _git(repo, "commit", "-q", "-m", "base")

    clean = codex_session_guard.validate_phase_c_v2_mutation_admission(
        {"requested_action_id": codex_session_guard.PHASE_C_V2_VALIDATION_ACTION_ID},
        repo=repo,
    )
    assert clean["status"] == "pass"

    tracked.write_text("unstaged\n", encoding="utf-8")
    staged = repo / codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[2]
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text("staged\n", encoding="utf-8")
    _git(repo, "add", "--", codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[2])
    untracked = repo / codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[3]
    untracked.parent.mkdir(parents=True, exist_ok=True)
    untracked.write_text("untracked\n", encoding="utf-8")

    actual = codex_session_guard.phase_c_v2_actual_changed_paths(repo=repo)
    assert actual["changed_paths"] == sorted(
        codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS[index] for index in (1, 2, 3)
    )
    validation = codex_session_guard.validate_phase_c_v2_mutation_admission(
        {"requested_action_id": codex_session_guard.PHASE_C_V2_VALIDATION_ACTION_ID},
        repo=repo,
    )
    assert "validation_action_product_mutation_forbidden" in validation["errors"]
    implementation = codex_session_guard.validate_phase_c_v2_mutation_admission(
        {
            "task_id": codex_session_guard.PHASE_C_V2_PRODUCT_TASK_ID,
            "task_kind": codex_session_guard.PHASE_C_V2_IMPLEMENT_TASK_KIND,
            "requested_action_id": codex_session_guard.PHASE_C_V2_IMPLEMENT_ACTION_ID,
            "authorized_implementation_targets": codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS,
            "authority_commit": None,
        },
        repo=repo,
    )
    assert "v2_committed_receipt_admission_required" in implementation["errors"]


def test_phase_c_simplified_gate_exact_direct_child_commit_and_hostile_paths(tmp_path: Path) -> None:
    repo = tmp_path / "phase-c"
    _init_phase_c_v2_repo(repo)
    valid_commit = _write_phase_c_v2_candidate(repo)
    result = codex_session_guard.validate_phase_c_v2_commit(valid_commit, repo=repo)
    assert result["status"] == "pass", result["errors"]
    assert result["changed_paths"] == sorted(codex_session_guard.PHASE_C_V2_COMMIT_PATHS)

    base_result = codex_session_guard.validate_phase_c_v2_commit(
        codex_session_guard.PHASE_C_V2_EGO_BASE_COMMIT,
        repo=repo,
    )
    assert "authority_commit_not_exact_direct_child" in base_result["errors"]

    intermediate_repo = tmp_path / "intermediate"
    _init_phase_c_v2_repo(intermediate_repo)
    _git(intermediate_repo, "commit", "-q", "--allow-empty", "-m", "intermediate")
    intermediate_candidate = _write_phase_c_v2_candidate(intermediate_repo)
    intermediate_result = codex_session_guard.validate_phase_c_v2_commit(
        intermediate_candidate,
        repo=intermediate_repo,
    )
    assert intermediate_result["changed_paths"] == sorted(
        codex_session_guard.PHASE_C_V2_COMMIT_PATHS
    )
    assert "authority_commit_not_exact_direct_child" in intermediate_result["errors"]

    missing_repo = tmp_path / "missing"
    _init_phase_c_v2_repo(missing_repo)
    missing_commit = _write_phase_c_v2_candidate(
        missing_repo,
        omit=codex_session_guard.PHASE_C_V2_REVIEWED_PATHS[0],
    )
    assert "authority_commit_exact_20_paths_required" in codex_session_guard.validate_phase_c_v2_commit(missing_commit, repo=missing_repo)["errors"]

    extra_repo = tmp_path / "extra"
    _init_phase_c_v2_repo(extra_repo)
    extra_commit = _write_phase_c_v2_candidate(extra_repo, extra=True)
    assert "authority_commit_exact_20_paths_required" in codex_session_guard.validate_phase_c_v2_commit(extra_commit, repo=extra_repo)["errors"]


def test_phase_c_simplified_gate_scope_contract_is_exact() -> None:
    payload = codex_session_guard._load_yaml(  # noqa: SLF001
        ROOT / codex_session_guard.PHASE_C_V2_SCOPE_PATH,
        code="missing_phase_c_v2_scope",
    )
    assert codex_session_guard.validate_phase_c_v2_scope_payload(payload) == []
    payload["implementation_allowlist"] = payload["implementation_allowlist"][::-1]
    assert "phase_c_v2_scope_implementation_allowlist_mismatch" in codex_session_guard.validate_phase_c_v2_scope_payload(payload)


def _r1_visual_source_fixture() -> dict:
    state = {
        "route_id": codex_session_guard.R1_VISUAL_ROUTE_ID,
        "task_id": codex_session_guard.R1_VISUAL_TRANSITION_TASK_ID,
        "phase": "V2_PRODUCT_MAIN_TAKEOVER_READY_TO_EXECUTE",
        "operator_decision": "AUTHORIZE_EXACT_DEFAULT_OFF_V2_PRODUCT_MAIN_TAKEOVER_AFTER_NEGATIVE_CHECKPOINT_PRESERVATION",
        "execution_state": "AUTHORIZED_CHECKPOINT_PRESERVATION_ONLY__FAST_FORWARD_AND_SYNC_CONDITIONAL",
        "conditional_actions": {
            codex_session_guard.R1_VISUAL_FAST_FORWARD_ACTION_ID: {
                "authorization": "GRANTED_EXACT_FAST_FORWARD_MANIFEST",
                "execution_precondition": "EXACT_19_PATH_CHECKPOINT_COMMIT_EXTERNAL_BUNDLE_VERIFY_AND_BYTE_RECONSTRUCTION",
                "state": "AUTHORIZED_BUT_BLOCKED_UNTIL_EXACT_NEGATIVE_CHECKPOINT_PRESERVATION",
            },
            codex_session_guard.R1_VISUAL_IMPLEMENT_ACTION_ID: {
                "authorization": "GRANTED_EXACT_26_PATH_TRANSCRIPTION",
                "execution_precondition": "EGO_MAIN_EXACTLY_AT_PINNED_V2_COMMIT_AND_TREE_WITH_CLEAN_INDEX_WORKTREE",
                "state": "AUTHORIZED_BUT_BLOCKED_UNTIL_EXACT_MAIN_FAST_FORWARD",
            }
        },
        "allowed_next_actions": [
            codex_session_guard.R1_VISUAL_PRESERVE_ACTION_ID,
            codex_session_guard.R1_VISUAL_FAST_FORWARD_ACTION_ID,
            codex_session_guard.R1_VISUAL_IMPLEMENT_ACTION_ID,
            codex_session_guard.R1_VISUAL_VALIDATION_ACTION_ID,
        ],
        "currently_executable_actions": [
            codex_session_guard.R1_VISUAL_PRESERVE_ACTION_ID,
            codex_session_guard.R1_VISUAL_VALIDATION_ACTION_ID,
        ],
        "implementation_authorized": True,
        "authorized_implementation_targets": list(codex_session_guard.R1_VISUAL_IMPLEMENTATION_TARGETS),
        "consumed_implementation": copy.deepcopy(codex_session_guard.R1_VISUAL_CONSUMED_IMPLEMENTATION),
        "product_development_core_lineage": copy.deepcopy(codex_session_guard.R1_VISUAL_LINEAGE),
        "real_trigger_evidence": "PINNED_ACTION_PERSEVERATION_REPAIR_RESULT_CONSUMED_WITHOUT_CLAIM_UPGRADE",
        "forbidden_next_actions": list(codex_session_guard.R1_VISUAL_FORBIDDEN_NEXT_ACTIONS),
        "claim_ceiling": copy.deepcopy(codex_session_guard.R1_VISUAL_CLAIM_CEILING),
        "repository_takeover_contract": copy.deepcopy(codex_session_guard.R1_VISUAL_TAKEOVER_CONTRACT),
        **copy.deepcopy(codex_session_guard.R1_VISUAL_CLOSED_SWITCHES),
    }
    product_axis = {
        "authority_semantics": "SOLE_MACHINE_READABLE_PRODUCT_DEVELOPMENT_AXIS_AUTHORITY",
        "product_development_axis": {
            "authority": "SOLE",
            "authority_route_id": codex_session_guard.R1_VISUAL_ROUTE_ID,
            "authorized_implementation_targets": list(codex_session_guard.R1_VISUAL_IMPLEMENTATION_TARGETS),
            "conditional_authorized_actions": [
                codex_session_guard.R1_VISUAL_FAST_FORWARD_ACTION_ID,
                codex_session_guard.R1_VISUAL_IMPLEMENT_ACTION_ID,
            ],
            "currently_executable_actions": [
                codex_session_guard.R1_VISUAL_PRESERVE_ACTION_ID,
                codex_session_guard.R1_VISUAL_VALIDATION_ACTION_ID,
            ],
            "effective_live_product_actions": [
                codex_session_guard.R1_VISUAL_PRESERVE_ACTION_ID,
                codex_session_guard.R1_VISUAL_VALIDATION_ACTION_ID,
            ],
            "source_commit": codex_session_guard.R1_VISUAL_V2_BASE_COMMIT,
            "state": "V2_PRODUCT_MAIN_TAKEOVER_AUTHORIZED_CHECKPOINT_PRESERVATION_REQUIRED",
            "enabled": False,
            "default_enabled": False,
            "mainline_connected": False,
            "runtime_mainline_connected": False,
            "runtime_authority": "none",
            "science_weight": 0,
            "remote_anchor": False,
            "repository_main_placement_complete": False,
            "repository_main_takeover_authorized": True,
        },
    }
    report = {"verdict": "pass", "route_id": codex_session_guard.R1_VISUAL_ROUTE_ID}
    return {"product_axis": product_axis, "v2_state": state, "v2_events": [{"event_id": "001"}, {"event_id": "002"}, {"event_id": "003"}, {"event_id": "004"}], "v2_report": report}


def test_r1_visual_authority_projection_is_exact_and_fail_closed() -> None:
    source = _r1_visual_source_fixture()
    authority = codex_session_guard.build_r1_visual_source_projection(source)
    result = codex_session_guard.validate_r1_visual_authority_payload(authority, source_objects=source)
    assert result["status"] == "pass", result["errors"]
    assert authority["main_takeover"]["effective_allowed_next_actions"] == [codex_session_guard.R1_VISUAL_VALIDATION_ACTION_ID]
    assert authority["main_takeover"]["authorized_implementation_targets"] == codex_session_guard.R1_VISUAL_IMPLEMENTATION_TARGETS

    reordered = copy.deepcopy(authority)
    reordered["main_takeover"]["authorized_implementation_targets"] = list(reversed(codex_session_guard.R1_VISUAL_IMPLEMENTATION_TARGETS))
    assert "r1_visual_authority_projection_mismatch" in codex_session_guard.validate_r1_visual_authority_payload(reordered, source_objects=source)["errors"]

    opened = copy.deepcopy(authority)
    opened["main_takeover"]["switches"]["background_dispatch"] = True
    assert "r1_visual_authority_projection_mismatch" in codex_session_guard.validate_r1_visual_authority_payload(opened, source_objects=source)["errors"]

    old_action = copy.deepcopy(authority)
    old_action["main_takeover"]["effective_allowed_next_actions"].insert(0, codex_session_guard.PHASE_C_V2_LEGACY_IMPLEMENT_ACTION_ID)
    assert "r1_visual_authority_projection_mismatch" in codex_session_guard.validate_r1_visual_authority_payload(old_action, source_objects=source)["errors"]


def test_r1_visual_source_object_pin_and_phase_a_scope_hostile_controls() -> None:
    source = _r1_visual_source_fixture()
    authority = codex_session_guard.build_r1_visual_source_projection(source)
    authority["itl_authority"]["objects"]["v2_state"]["git_blob_oid"] = "0" * 40
    assert "r1_visual_authority_projection_mismatch" in codex_session_guard.validate_r1_visual_authority_payload(authority, source_objects=source)["errors"]

    scope = codex_session_guard.build_r1_visual_phase_a_scope(authority_commit="a" * 40)
    assert codex_session_guard.validate_r1_visual_phase_a_scope_payload(scope) == []
    scope["authorized_implementation_targets"].append("labs/ego_life_playground_v0/app.py")
    assert "r1_visual_phase_a_targets_mismatch" in codex_session_guard.validate_r1_visual_phase_a_scope_payload(scope)
