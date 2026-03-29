# OpenEmotion V6K2 Whitelist Alert Stabilization - PLAN

## Task summary

Bugfix slice for the v6k.2 whitelist alert engine. The failure is a contract
regression at the implementation/verification layer: BOOTSTRAP scenarios return
no alerts, while the tracked tests expect a structured governance-visible alert.

## Milestones

### Milestone 1: restore BOOTSTRAP alert generation

- scope: patch the whitelist alert engine so BOOTSTRAP scenarios emit a
  non-critical structured alert with valid fields
- files / areas likely touched:
  - `OpenEmotion/emotiond/memory/embedding/whitelist_alert_engine.py`
- acceptance:
  - targeted v6k.2 alert tests pass
  - generated alerts remain structured and warning-grade rather than critical
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/embedding/test_v6k2_whitelist_operations.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: revert the new BOOTSTRAP alert type if it proves incompatible with downstream governance assumptions

### Milestone 2: record slice status and rescan full-suite surface

- scope: update task records and confirm the v6k.2 failure surface leaves full verify summary
- files / areas likely touched:
  - `docs/codex/tasks/openemotion-v6k2-whitelist-alert-stabilization/*`
- acceptance:
  - task docs reflect the real root cause, fix, and verification strength
  - remaining failures are clearly outside this slice
- validation:
  - `git diff --check`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note: revert only documentation if it overstates completion strength

## Progress

- current_status: completed
- current_milestone: Milestone 2
- milestone_state: both milestones verified; slice ready to publish

## Decision log

- 2026-03-29: Keep this fix inside `whitelist_alert_engine.py`; the failure is local to BOOTSTRAP alert emission and does not justify widening into scheduler or governance refactors.
- 2026-03-29: Introduce an explicit `insufficient_observation_data` alert type instead of overloading unrelated alert categories.

## Surprises / discoveries

- The tracked tests treat “no observation data” as something that still requires a structured alert for governance visibility.
- Current BOOTSTRAP behavior silently returns `[]`, which hides the missing-evidence state from the alert summary layer.

## Outcomes / retrospective

- 本轮已证明：BOOTSTRAP scenarios now emit a structured warning alert and the v6k.2 failure surface has left the full-suite summary.
- 还没证明：global OpenEmotion suite stability; unrelated failures remain.
- 下一步最小闭环动作：publish this slice, then move to the next independent OpenEmotion failure surface.
