# EgoDesktop PSPC Debug Signal Overlay v0 Acceptance

## Required Signals

- The hidden `审计` overlay shows `PSPC preview proxy`.
- The overlay shows `style`, `confidence`, `history_counts`, `recent_categories`, `reason_trace_refs`, `basis`, and `claim_ceiling`.
- The overlay shows `PSPC signal inactive / neutral` when no strong PSPC signal is present.
- The overlay shows seven proxy bars:
  - `trust proxy`
  - `stress proxy`
  - `approach tendency`
  - `avoidance tendency`
  - `care tendency`
  - `boundary tendency`
  - `low-interrupt tendency`

## Behavioral Checks

- Gentle history raises trust and approach proxy values.
- Frequent interruption history raises stress, avoidance, and boundary proxy values.
- Late-night history raises care and low-interrupt proxy values.
- The current fanfic/creative continuation log stays neutral/inactive rather than pretending PSPC strongly participated.
- Debug overlay output contains no executable authority fields.

## Forbidden Regression

- No reply-path mutation from toggling debug overlay.
- No real memory write.
- No gate, approval, transport, proactive, planner, training, or model-execution call.
- No adapter creation or runtime registration.
- No claim ceiling upgrade.

## Done Criteria

- Targeted tests pass.
- Existing EgoDesktop tests pass.
- Report exists under `artifacts/egodesktop_pspc_debug_signal_overlay_v0/`.
- State and evidence entries preserve repo-wide `highest_evidence_level=E3`.

## What This Proves

This proves local observability of the PSPC preview proxy inside EgoDesktop.

## What This Does Not Prove

It does not prove true PSPC learning, durable memory, EgoOperator runtime integration safety, stable user benefit, live autonomy, consciousness, subjective experience, or real emotion.
