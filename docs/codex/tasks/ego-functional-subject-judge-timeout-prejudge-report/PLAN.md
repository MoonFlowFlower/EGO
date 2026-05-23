# Plan

1. Write Functional Subject report/markdown immediately after the case loop and experiment-control packet, before invoking GPT-5.5 judge.
2. Add `--judge-timeout-seconds` and thread it into `run_codex_functional_subject_judge`.
3. Convert judge timeout into structured `unavailable / partial` evidence.
4. Add tests for pre-judge report existence and judge timeout handling.
5. Run targeted tests, full script test suite, and `autopilot_full`.

## Non-Goals

- No EgoOperator runtime behavior change.
- No provider/model default change.
- No GitHub Project mutation.
- No program-state or evidence-ledger update.
- No claim that EGO-FS-010 has passed.
