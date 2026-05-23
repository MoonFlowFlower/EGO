# Plan

1. Add the thin Experiment Control Plane: phase gate, experiment ledger, failure taxonomy, repair router, and evidence-closeout inputs.
2. Reproduce the v7 partial blockers in a local fake-provider or scripted runner.
3. Add deterministic regressions for provider/empty-response transcript clarity, memory-gate language, and transcript-visible planner influence.
4. Repair `EgoOperator` and the trial packet without adding a second memory/state authority.
5. Run targeted tests, Functional Subject scripted trial, and `autopilot_full`.
6. Rerun #94 real-provider smoke and GPT-5.5 judge only after the local slice is stable.

## Non-Goals

- No memory authority promotion.
- No provider-model default change unless a separate provider task is created.
- No GitHub Project mutation.
- No program-state or evidence-ledger update.
