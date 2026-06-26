# Minimal Surface for EGODESKTOP-GABLATION-006

This file attaches the minimal surface that the earlier Claude review asked to see in the next packet.

## Required Minimal Surface

1. Instrument, do not fork.
   - Tap only the default chat-turn result boundary already used by runtime.
   - Do not implement a parallel chat-turn path or runner-owned chat logic.
2. reuse 003/004 trace_rows.jsonl.
   - No second trace format, writer, or verdict surface.
3. Default-off remains no-op.
   - No `JOI_REAL_LOOP_G_ABLATION=1`, no G-ABLATION trace rows.
4. Row label is bounded.
   - Current 006 rows are `schema_valid_collect_only_snapshot`.
   - They do not satisfy 001C section 12 while replay is collect-only.
5. Rows-only acceptance.
   - 006 may show a real backend snapshot row and blocker reduction only.
   - No baseline, attribution, route-B, readiness, product benefit, agency, emotion, subjectivity, consciousness, alive
     status, or Bar-2 claim.
6. Tests-first and single condition.
   - CURRENT_SHIM smoke is enough for 006.
   - CREATURE_ON and condition battery are future slices and require replay preconditions first.
7. No state/ledger publication widening.
   - No `PROGRAM_STATE_UNIFIED.yaml` update.
   - No evidence-ledger update.
   - No push, tag, or remote anchor.

## Current 006 Readback

The implemented tap sits at the existing EgoDesktop chat-turn result boundary and passes the backend snapshot into the
existing trace runner. The row remains unreplayable and is intentionally blocked by `collect_only_replay_policy` and
`missing_llm_replay_id`.
