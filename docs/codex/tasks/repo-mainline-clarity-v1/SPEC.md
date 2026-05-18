# Repo Mainline Clarity v1 Spec

> Reader safety note (2026-05-18): This is pre-EgoOperator supporting task history. Current route authority is `docs/PROGRAM_STATE_UNIFIED.yaml`, `docs/MAINLINE_QUICKSTART.md`, and `EgoOperator/`; do not treat older `subject_system_v1_governed_proactivity` wording here as the current default route.

## Goal

Make the current EGO mainline easy to identify without moving files or changing runtime behavior.

The problem is not only directory shape. The real problem is that authority, experimental lanes, closed evidence, and operational exhaust are all visible at once. This task adds a single onboarding path and generated surface map so new agents can tell what is current, what is reference-only, and what must not be committed.

## Scope

- Add a human-facing mainline quickstart.
- Add a generated repo surface map.
- Keep `subject_system_v1_governed_proactivity` as the only active default lane.
- Keep `ego_desktop_lab` as a reference harness, not a runtime authority.
- Add staged operational-exhaust hygiene verification.

## Non-Goals

- No physical archive moves in Phase 1.
- No runtime behavior changes.
- No `PROGRAM_STATE_UNIFIED.yaml` update unless official authority changes.
- No formal evidence ledger update for docs/view cleanup.
- No split-repo migration.

## Acceptance

- A new agent can find the current mainline from `README.md` -> `docs/MAINLINE_QUICKSTART.md`.
- `docs/codex/tasks/TASK_LANE_INDEX.md` still has exactly one active default lane.
- `docs/REPO_SURFACE_MAP.md` classifies formal runtime, reference harness, governance, evidence, archive/reference, and operational exhaust.
- Staged new temp/log/cache/session exhaust is blocked by a verifier.
- Cleanup does not widen any consciousness, live autonomy, runtime efficacy, or user benefit claim.
