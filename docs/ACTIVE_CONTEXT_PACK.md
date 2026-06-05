# Active Context Pack

Source of truth: `docs/PROGRAM_STATE_UNIFIED.yaml`.

This file is a derived reader pack for humans and AI agents. It is not a second program-state authority. If this file conflicts with `docs/PROGRAM_STATE_UNIFIED.yaml`, the unified program state wins.

## Current Runtime Owner

- Current default runtime owner: `EgoOperator/`
- Current phase: `legacy_pre_operator_mainline_archived_from_current_tree`
- Current layer: `transition / operator-first`
- Highest evidence level: `E3`
- Default runtime path to preserve:

```text
user text -> LLM understanding -> proposal/plan -> runtime gate -> trace
```

## Current Mainline Gate

The current next minimal action is human review import for EgoOperator Human Operator Trial v2:

```text
Have a human operator fill EgoOperator/artifacts/human_operator_trial/v2_latest/human_operator_trial_human_review_notes_template.jsonl, then import it with:

python EgoOperator/human_operator_trial.py --out EgoOperator/artifacts/human_operator_trial/v2_human_reviewed --notes EgoOperator/artifacts/human_operator_trial/v2_latest/human_operator_trial_human_review_notes_template.jsonl --provider-mode openrouter
```

Do not treat scripted provider scores as a human-observation pass.

## Legacy Status

Archived legacy reference surfaces:

- `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`
- `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`
- `artifacts/archive/legacy_pre_operator_mainline_manifest.json`
- git tag `legacy-pre-operator-mainline-before-purge`

Archived legacy code has no runtime authority, no default path, no fallback runtime, and no task-routing authority.

Removed current-tree code paths:

- `legacy/ego-pre-handmade-mainline/EgoCore/`
- `legacy/ego-pre-handmade-mainline/OpenEmotion/`
- `legacy/ego-pre-handmade-mainline/ego_desktop_lab/`

## PSPC Status

PSPC evidence is reference-only unless a future Stage Card explicitly admits a new review step.

Current allowed PSPC role:

- lab/shadow/product-preview evidence
- presentation/debug/style hints in EgoDesktop local preview work
- audit-only artifacts and reports

Current forbidden PSPC role:

- runtime authority
- direct action selection
- direct user-message authority
- direct memory write
- gate/approval bypass
- transport or proactive authority
- claim-ceiling upgrade

## Local Noise Policy

Local-only paths:

- `Test/`
- `data/live2d/`
- `EgoDesktop/tts_output/`
- `artifacts/desktop_tts/`
- `artifacts/task_board/outbox.jsonl`
- `artifacts/task_board/sync_log.jsonl`

These paths are not current source, tests, or evidence unless a future Stage Card explicitly admits them.

## What Not To Do

- Do not restore archived legacy code as an active runtime.
- Do not reintroduce keyword-first semantic routing or template fallback as the default entry.
- Do not let PSPC become runtime authority.
- Do not raise repo-wide claim ceiling from local/scripted evidence.
- Do not replace the human review import gate with scripted scores.
- Do not treat this reader pack as a source of truth over `docs/PROGRAM_STATE_UNIFIED.yaml`.

## Claim Boundary

This pack improves context readability only. It does not prove EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, functional selfhood, consciousness, subjective experience, or real emotion.
