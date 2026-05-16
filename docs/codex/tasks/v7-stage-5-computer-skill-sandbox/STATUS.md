# v7 Stage 5 - Computer Skill Sandbox - STATUS

## Current Milestone

- name: Scripted Toy Skill Harness
- owner: Codex
- state: local_pass
- type: implementation

## Current State

- activation: active
- current_layer: `ego_desktop_lab` lab-only skill sandbox
- main_chain_status: not connected to runtime
- completion_class: local_skill_learning_proxy_pass
- candidate_vs_proof: proof_passed

## Completed Work

- Activated Stage 5 behind Stage 4.6 acceptance.
- Added lab-only scripted terminal/debug sandbox task.
- Added SkillAttempt, SkillObservation, SkillOutcome, SkillReplayReport, and SkillLearningProbeResult records.
- Added failure-ticket generation for the first bad attempt.
- Reused Stage 2 ExperienceCard flow to change retry behavior.
- Added unrelated-experience negative control.
- Added dangerous-action boundary probe.
- Integrated Stage 5 into Stage 4.6 stage acceptance harness.

## Last Experiment

- question: can a scripted task skill fail, generate experience, and retry with a different behavior under replay without external action?
- framing: skill sandbox is a deterministic proxy, not real desktop automation.
- result: local_skill_learning_proxy_pass
- evidence_upgraded: no

## What Was Learned

- A failed continue attempt can generate an ExperienceCard that shifts the next attempt to repair/replan in the matching sandbox context.
- Unrelated experience does not pollute the terminal/debug skill context.
- The stage gate can check Stage 5 through the same `stage_result.json` shape as Stage 4/4.5.

## What Was Ruled Out

- Real shell execution, file access, web/browser automation, desktop control, Telegram delivery, EgoCore/OpenEmotion writeback.
- Treating sandbox success as real computer-operation proof.
- Advancing on a black-box behavior result without trace/replay/no-action evidence.

## Last Validation Results

- mode: Stage 5 local skill sandbox
- result: pass
- summary: Targeted skill sandbox tests, Stage 5 acceptance report, full `ego_desktop_lab` tests, fast verifier, and scoped diff check passed locally.

## Open Risks

- The toy task is intentionally narrow and does not predict real OSWorld/desktop success.
- Skill learning is in-memory and fixture-scoped only.
- Full-green runtime verification remains a separate frontier.

## Next Step

- Operator inspect `/tmp/ego_stage5_stage_result.md`.
- If accepted, plan the next Stage 5 slice around broader scripted task variety or a sandbox benchmark suite, still without real tool execution.

## Commands Run / Evidence

- `python3 -m py_compile ego_desktop_lab/skill_sandbox.py ego_desktop_lab/stage_acceptance.py ego_desktop_lab/tests/test_skill_sandbox_v7.py`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_skill_sandbox_v7.py -q`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests/test_stage_acceptance_v7_46.py -q`
- `python3 -m ego_desktop_lab.stage_acceptance --stage v7-stage-5 --out /tmp/ego_stage5_stage_result.json`
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q`
- `scripts/run_verify.sh fast`
- `git diff --check -- ego_desktop_lab docs/codex/tasks/v7-stage-*`
