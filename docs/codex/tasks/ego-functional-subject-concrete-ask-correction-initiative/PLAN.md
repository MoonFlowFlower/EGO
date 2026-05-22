# Plan

1. Normalize the v4 GPT-5.5 partial verdict into `EGO-FS-027`.
2. Add deterministic regressions for concrete ASK, correction uptake, and bounded initiative selection.
3. Repair `EgoOperator` output/planner guards without adding a second memory/state authority.
4. Run targeted tests, Functional Subject trial smoke, and `autopilot_full`.
5. Rerun #94 real-provider smoke and GPT-5.5 judge if the local slice is stable.

## Non-Goals

- No memory authority promotion.
- No provider/model change.
- No GitHub Project mutation.
- No program-state or evidence-ledger update.
