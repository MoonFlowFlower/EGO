# EgoOperator Rename + Docs Reader Safety Pass v1 - SPEC

## Goal

Rename the current operator-first mainline from `Ego_handmade` to `EgoOperator`, then add a narrow reader-safety pass for old documents that can be mistaken for current entry points.

## Allowed Changes

- `EgoOperator/**`
- `AGENTS.md`, `README.md`, `docs/MAINLINE_QUICKSTART.md`
- `docs/PROGRAM_STATE_UNIFIED.yaml`, generated state/route views, and the evidence ledger transition entry
- route/mainline verifier scripts
- high-risk reader docs that need a top banner or cross-link only
- this task directory

## Forbidden Changes

- No legacy code edits under `legacy/ego-pre-handmade-mainline/**`.
- No rewrite of historical evidence or old task bodies beyond route-index/readability metadata.
- No runtime memory, trace, cache, `.team`, or local test-output staging.
- No compatibility alias preserving `Ego_handmade` as a tracked runtime path.

## Claim Boundary

This task can claim only `EgoOperator naming/docs safety transition recorded`. It does not prove stable real user benefit, runtime efficacy, durable long-term memory effectiveness, live autonomy, broader agent replacement success, or consciousness.

## Acceptance

- Tracked runtime files live under `EgoOperator/`.
- Current authority/docs/scripts point at `EgoOperator` and `ego_operator_first_transition`.
- Historical `ego-handmade-*` task directory names remain unchanged as history.
- Reader-safety banners are added only to high-risk old entry docs.
- Targeted runtime and governance checks pass or record precise limitations.
