# Plan

1. Add a deterministic approval lifecycle helper using `propose_file_write` and explicit approval.
2. Attach the helper output to the Functional Subject report and GPT-5.5 judge packet.
3. Add regression tests for pending, approve execution, pending cleanup, summary, and probe cleanup.
4. Run targeted tests and `autopilot_full`.

## Non-Goals

- No approval model change.
- No command allowlist change.
- No provider/model change.
- No program-state or evidence-ledger update.
