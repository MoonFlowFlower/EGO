# Plan

1. Add a Functional Subject trial progress report that is written after each completed case.
2. Add an optional per-case timeout for Unix/WSL runs using a bounded signal alarm.
3. Record timeout metadata in the case result, trace, JSON report, and markdown summary.
4. Add deterministic tests for progress writing and case timeout partial-report behavior.
5. Run targeted tests, `EgoOperator/tests`, `autopilot_full`, and a one-case progress smoke.

## Non-Goals

- No EgoOperator runtime behavior change.
- No provider/model default change.
- No GitHub Project mutation.
- No program-state or evidence-ledger update.
- No claim that EGO-FS-010 has passed.
