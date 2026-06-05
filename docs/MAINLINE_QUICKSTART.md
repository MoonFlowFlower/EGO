# Mainline Quickstart

## Current Mainline

The current active default lane is `ego_operator_first_transition`.

Default operator runtime: `EgoOperator/agent_base.py` (formerly `Ego_handmade/agent_base.py`).

Source of truth: `docs/PROGRAM_STATE_UNIFIED.yaml`.

Derived route view: `docs/codex/tasks/TASK_LANE_INDEX.md`.

## Runtime Ownership

- `EgoOperator` owns the current operator-first runtime candidate: natural language understanding, runtime modes, transaction approval, local operator memory, trace, and human-trial reports.
- `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md` is the working-tree tombstone for the archived pre-operator mainline.
- `docs/archive/LEGACY_ALGORITHM_INVENTORY.md` is the thin reusable-idea inventory. It is reference only, with no runtime authority and no default path.
- `artifacts/archive/legacy_pre_operator_mainline_manifest.json` records the removed paths, archive pointer, claim boundary, and rollback instructions.
- The archive pointer is `legacy-pre-operator-mainline-before-purge`. Restoring or reusing old `EgoCore / OpenEmotion / ego_desktop_lab` code requires a new Stage Card and evidence gate.
- New work should preserve the `user text -> LLM understanding -> proposal/plan -> gate -> trace` path. Do not reintroduce keyword-first semantic routing as the default entry.

## First 5 Files To Read

1. `docs/PROGRAM_STATE_UNIFIED.yaml`
2. `docs/MAINLINE_QUICKSTART.md`
3. `docs/codex/tasks/TASK_LANE_INDEX.md`
4. `docs/REPO_HYGIENE_POLICY.md`
5. `docs/codex/tasks/ego-operator-human-operator-trial-v2/STATUS.md`

## Do Not Reopen By Default

- `active_inference_mainline_activation` is closed evidence, not the active implementation lane.
- MVS-aligned compact work is closed evidence, not the active implementation lane.
- `subject_system_v1_governed_proactivity` is now legacy/pre-EgoOperator evidence, not the active default implementation lane.
- `repo_authority_cleanup` is closeout-complete; only explicit housekeeping slices should reopen cleanup.
- `thought_probe / weak-generic rebind / bare-continue repair / proactive timing / self-DM live gate` are regression evidence unless the active lane explicitly admits a new task.
- Archived pre-operator `EgoCore / OpenEmotion / ego_desktop_lab` code should not become a Telegram path, GUI path, desktop executor, subject kernel, fallback runtime, or third core without a new Stage Card and evidence gate.

## Claim Ceiling

The current trial can prove at most `EgoOperator human-operator trial local observation pass` after enough real-provider human observations. It does not prove consciousness, alive status, live autonomy, runtime efficacy, stable long-term memory, or stable real user benefit.

## Minimal Verification

```bash
python3 scripts/codex/verify_route_convergence.py
python3 scripts/codex/verify_mainline_clarity.py
python3 -m py_compile EgoOperator/agent_base.py EgoOperator/memory_system.py EgoOperator/real_use_gate.py EgoOperator/human_operator_trial.py
TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests
```
