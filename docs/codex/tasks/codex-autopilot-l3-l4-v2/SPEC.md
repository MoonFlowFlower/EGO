# Codex Autopilot L3/L4 v2 SPEC

## Goal

Add a bounded cross-project autopilot closeout and patrol layer:

- L3: only issues with sufficient local/scripted evidence may be auto-closed.
- L4: scheduled unattended patrol runs in dry-run mode only.

## Non-Goals

- Do not auto-implement code.
- Do not auto-close human smoke, Stage Card, permissions expansion, program state, evidence ledger, protected-path, mainline/demotion, or memory-promotion issues.
- Do not let LLM review override hard-stop gates.
- Do not modify `EgoOperator/**`, legacy code, `docs/PROGRAM_STATE_UNIFIED.yaml`, or `artifacts/evidence_ledger/**`.

## Claim Ceiling

`Codex autopilot L3/L4 bounded closeout/patrol local workflow candidate pass`.

This does not prove unattended autonomous development, stable productivity gain, EgoOperator runtime efficacy, live autonomy, durable memory efficacy, or consciousness.
