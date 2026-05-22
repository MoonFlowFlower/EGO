# EgoOperator Functional Subject Policy Replay Proof

## Goal

Add a scripted replay proof to the Functional Subject trial so the `policy_patch` sample shows a complete evidence path: repeated same-class failure, `PolicyPatchCandidate` emission, later comparable turn replay, and judge-visible trace evidence.

This is a proof/eval task over an already implemented candidate primitive. It strengthens the Functional Subject eval bundle without promoting policy patches into persistent memory or canonical state.

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-013`
- GPT-5.5 judge partial result from `EGO-FS-010`
- `docs/codex/tasks/ego-functional-subject-trial-v0/functional_subject_20_sample_trial_pack.json`

## Allowed Changes

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `docs/codex/tasks/ego-functional-subject-trial-v0/functional_subject_20_sample_trial_pack.json`
- `.codex/project_contract.yaml`
- `Tasks/TASK_BOARD.yaml`
- this task directory

## Non-Goals

- Do not make policy patches persistent.
- Do not mutate PROJECT_MEMORY, operator core memory, program state, or evidence ledger.
- Do not claim stable learning or autonomous selfhood.
- Do not modify legacy runtime.

## Acceptance Gate

- The fs_19 trial case has a scripted setup that emits a concrete `PolicyPatchCandidate`.
- The fs_19 user turn replays that candidate into trace/subject context.
- The GPT-5.5 judge packet includes setup evidence and replay count.
- Full Autopilot verification passes.

## Claim Ceiling

`Functional Subject policy replay proof local/scripted candidate pass`
