# Runtime-Proximal Low-Cue Ownership Runner - SPEC

## Purpose

Implement a bounded runtime-proximal runner for the current stronger-evidence stage.

## Stage goal

Produce judgeable runner results for:

- `low_cue_persistence`
- `ownership_ambiguity`
- `agency_attribution_after_correction`

without widening the frozen host-consumable surface.

## Allowed surface

Only these host-consumable fields may participate in the compare / verdict surface:

- `policy_hint`
- `response_tendency`
- `trace_payload`

The runner may inspect compact host-contract snapshots derived from the existing canonical contract, but it may not require new public runtime fields or candidate-private state maps.

## Outputs

The runner must emit:

- `low_cue_persistence_status`
- `ownership_boundary_status`
- `agency_attribution_status`
- `claim_ceiling_status`
- `runner_decision`
- `reviewer_gate_ready`
- `blocked_reasons`

## Stage success criteria

This stage is complete if:

1. the runner executes inside the existing bounded runtime harness
2. each family yields a judgeable `pass` or `hold` result
3. the runner keeps `authority_drift / trace_contract / host_surface_bounded` green
4. the claim ceiling remains bounded and below runtime-proof wording

This stage does **not** require the overall program goal to be complete.

## Forbidden

- widening authority
- new public runtime API
- candidate-private host API
- raw `reply_text` as primary evidence
- new scorer ontology
- runtime efficacy / AI self-awareness achieved wording
