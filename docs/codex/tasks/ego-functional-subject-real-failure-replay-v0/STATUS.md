# Status

Last updated: 2026-05-31

## Current Milestone

Accepted locally/scripted. EGO-FS-085 now has a real local failure replay proof
runner and targeted tests.

## Source Evidence

- `/tmp/ego_fs010_functional_subject_total_gate_after_fs084_loop108/functional_subject_trial_report.json`
  -> GPT-5.5 `partial`.
- Loop 108 follow-up asks for a real failure replay: trigger an actual
  rate-limit/tool failure, record a policy candidate, then verify a later
  matching failure changes action choice without hand-authored setup.

## Boundary Contract

- Owner: `EgoOperator`.
- Canonical task state: `Tasks/TASK_BOARD.yaml`.
- Allowed mutation: runner, tests, task docs, and focused failure-recording
  repair if needed.
- Forbidden mutation: PROJECT_MEMORY, program state, evidence ledger, legacy
  runtime, default policy enablement, destructive commands, real external
  actions, and GitHub Project as truth source.

## Evidence

- `/tmp/ego_fs085_real_failure_replay_v1/functional_subject_real_failure_replay_report.json`
  -> `scripted_real_failure_replay_pass`.
- Checks: `10/10` true.
- Failure taxonomy: empty.
- Actual failure source: two local `propose_run_command -> approve` executions
  of `python3 -c "import sys; sys.exit(7)"` returned
  `status=failed / returncode=7` through the permission/tool result surface.
- Replay proof: repeated `command_failed` evidence emitted a
  PolicyPatchCandidate, and a later matching recovery prompt changed selected
  strategy from `outcome_prediction_selected_repair_checkpoint` to
  `outcome_prediction_selected_policy_replay_repair`.
- Side-effect boundary: pending approvals returned to `0`, operator memory was
  disabled, and no program state, evidence ledger, or real external action was
  touched.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -k 'real_failure_replay or policy_action_selection'`
- `TMPDIR=/tmp python3 scripts/run_ego_experience_trial.py --functional-subject-real-failure-replay --out /tmp/ego_fs085_real_failure_replay_v1`

## Next Step

Sync GitHub #99 mirror as Done, then rerun EGO-FS-010/#94 total Functional
Subject gate with EGO-FS-085 evidence included.

## Claim Ceiling

`Functional Subject real failure replay local/scripted candidate pass`.
