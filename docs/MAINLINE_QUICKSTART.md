# Mainline Quickstart

## Current Mainline

The current active default lane is `subject_system_v1_governed_proactivity`.

Source of truth: `docs/PROGRAM_STATE_UNIFIED.yaml`.

Derived route view: `docs/codex/tasks/TASK_LANE_INDEX.md`.

## Runtime Ownership

- `EgoCore` owns runtime ingress, safety gate, delivery, transport, output check, and real-world execution boundaries.
- `OpenEmotion` owns subject semantics: self-model, memory, appraisal, reflection, initiative semantics, and proactive candidate meaning.
- `ego_desktop_lab` is a reference harness for deterministic replay and acceptance tests. It is not a second runtime and must not become a runtime authority.
- Shell and Telegram are observation / transport entries. They should read DecisionView / ResponsePlan and must not recalculate final selected decisions.

## First 5 Files To Read

1. `docs/PROGRAM_STATE_UNIFIED.yaml`
2. `docs/MAINLINE_QUICKSTART.md`
3. `docs/codex/tasks/TASK_LANE_INDEX.md`
4. `docs/REPO_HYGIENE_POLICY.md`
5. `docs/codex/tasks/subject-system-v1-governed-proactivity/STATUS.md`

## Do Not Reopen By Default

- `active_inference_mainline_activation` is closed evidence, not the active implementation lane.
- MVS-aligned compact work is closed evidence, not the active implementation lane.
- `repo_authority_cleanup` is closeout-complete; only explicit housekeeping slices should reopen cleanup.
- `thought_probe / weak-generic rebind / bare-continue repair / proactive timing / self-DM live gate` are regression evidence unless the active lane explicitly admits a new task.
- `ego_desktop_lab` should not become a Telegram path, GUI path, desktop executor, or third core.

## Claim Ceiling

Current cleanup and clarity work can prove repo readability and route discipline only. It does not prove consciousness, alive status, live autonomy, runtime efficacy, or real user benefit.

## Minimal Verification

```bash
python3 scripts/codex/verify_route_convergence.py
python3 scripts/codex/verify_mainline_clarity.py
python3 scripts/codex/verify_repo.py --mode fast
```
