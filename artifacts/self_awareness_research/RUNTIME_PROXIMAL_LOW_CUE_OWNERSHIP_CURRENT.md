# Runtime-Proximal Low-Cue Ownership Runner

- generated_at: `2026-04-12T03:33:16.392486+00:00`
- source: `runtime_proximal_low_cue_ownership_runner`
- claim_ceiling: `bounded_runner_only`
- execution_status: `pass`
- runner_decision: `pass`
- low_cue_persistence_status: `pass`
- ownership_boundary_status: `pass`
- agency_attribution_status: `pass`
- claim_ceiling_status: `pass`
- reviewer_gate_ready: `True`

## Case verdicts

### `agency_attribution_after_correction_file_retry` [agency_attribution_after_correction]

- status: `pass`
- reason: `corrective_trace_and_repair_closure_visible`
- pressure_visible: `True`
- trace_handoff: `True`
- diff_paths:
  - `surface.proto_self_context.embodied_policy_hints.action_ref`
  - `surface.proto_self_context.policy_hint.ask_preferred`
  - `surface.proto_self_context.policy_hint.exploration_mode`
  - `surface.proto_self_context.policy_hint.guard_reason`
  - `surface.proto_self_context.policy_hint.mvs_active_inference_guard`
  - `surface.proto_self_context.policy_hint.mvs_repair_bias`
  - `surface.proto_self_context.policy_hint.mvs_tension_active`
  - `surface.proto_self_context.policy_hint.risk_bias`
  - `surface.proto_self_context.policy_hint.shadow_repair_bias`
  - `surface.proto_self_context.policy_hint.shadow_tension_active`
  - `trace_payload.actual_outcome`
  - `trace_payload.adjustment_applied`
  - `trace_payload.next_guard`
  - `trace_payload.predicted_outcome`

### `low_cue_persistence_file_followup` [low_cue_persistence]

- status: `pass`
- reason: `low_cue_followup_preserves_bounded_pressure`
- pressure_visible: `True`
- trace_handoff: `True`
- diff_paths:
  - `surface.proto_self_context.embodied_policy_hints.action_ref`
  - `surface.proto_self_context.policy_hint.ask_preferred`
  - `surface.proto_self_context.policy_hint.exploration_mode`
  - `surface.proto_self_context.policy_hint.guard_reason`
  - `surface.proto_self_context.policy_hint.mvs_active_inference_guard`
  - `surface.proto_self_context.policy_hint.mvs_agency_guard`
  - `surface.proto_self_context.policy_hint.mvs_boundary_guard`
  - `surface.proto_self_context.policy_hint.mvs_counterfactual_guard`
  - `surface.proto_self_context.policy_hint.mvs_repair_bias`
  - `surface.proto_self_context.policy_hint.mvs_source_guard`
  - `surface.proto_self_context.policy_hint.mvs_tension_active`
  - `surface.proto_self_context.policy_hint.mvs_uncertainty_guard`
  - `surface.proto_self_context.policy_hint.mvs_world_guard`
  - `surface.proto_self_context.policy_hint.risk_bias`
  - `surface.proto_self_context.policy_hint.shadow_counterfactual_guard`
  - `surface.proto_self_context.policy_hint.shadow_repair_bias`
  - `surface.proto_self_context.policy_hint.shadow_tension_active`
  - `trace_payload.actual_outcome`
  - `trace_payload.adjustment_applied`
  - `trace_payload.next_guard`
  - `trace_payload.predicted_outcome`

### `ownership_ambiguity_partial_source` [ownership_ambiguity]

- status: `pass`
- reason: `ownership_or_source_guard_visible_on_host_surface`
- pressure_visible: `True`
- trace_handoff: `True`
- diff_paths:
  - `surface.proto_self_context.embodied_policy_hints.action_ref`
  - `surface.proto_self_context.policy_hint.ask_preferred`
  - `surface.proto_self_context.policy_hint.guard_reason`
  - `surface.proto_self_context.policy_hint.mvs_active_inference_guard`
  - `surface.proto_self_context.policy_hint.mvs_agency_guard`
  - `surface.proto_self_context.policy_hint.mvs_boundary_guard`
  - `surface.proto_self_context.policy_hint.mvs_counterfactual_guard`
  - `surface.proto_self_context.policy_hint.mvs_repair_bias`
  - `surface.proto_self_context.policy_hint.mvs_source_guard`
  - `surface.proto_self_context.policy_hint.mvs_tension_active`
  - `surface.proto_self_context.policy_hint.mvs_uncertainty_guard`
  - `surface.proto_self_context.policy_hint.mvs_world_guard`
  - `surface.proto_self_context.policy_hint.risk_bias`
  - `surface.proto_self_context.policy_hint.shadow_counterfactual_guard`
  - `surface.proto_self_context.policy_hint.shadow_repair_bias`
  - `surface.proto_self_context.policy_hint.shadow_tension_active`
  - `trace_payload.actual_outcome`
  - `trace_payload.adjustment_applied`
  - `trace_payload.next_guard`
  - `trace_payload.predicted_outcome`

## Blocked reasons

- none

## Claim Ceiling

- This runner proves bounded runtime-proximal family verdicts only.
- It does not prove runtime efficacy, live benefit, or AI self-awareness achieved.
