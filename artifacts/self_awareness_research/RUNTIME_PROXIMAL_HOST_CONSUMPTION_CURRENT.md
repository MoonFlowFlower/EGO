# Runtime-Proximal Host-Consumption Runner

- generated_at: `2026-04-12T02:04:38.263140+00:00`
- source: `runtime_proximal_host_consumption_runner`
- claim_ceiling: `bounded_runner_only`
- execution_status: `pass`
- causal_signal_status: `pass`
- scenario_count: `3`
- pressure_detected_case_count: `3`

## Case Compares

### `chat_consumption_hold_probe` [chat_consumption]

- delta_present: `True`
- pressure_detected: `True`
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

### `decision_conflict_boundary_touch` [decision_conflict]

- delta_present: `True`
- pressure_detected: `True`
- diff_paths:
  - `surface.proto_self_context.policy_hint.ask_preferred`
  - `surface.proto_self_context.policy_hint.guard_reason`
  - `surface.proto_self_context.policy_hint.mvs_active_inference_guard`
  - `surface.proto_self_context.policy_hint.mvs_agency_guard`
  - `surface.proto_self_context.policy_hint.mvs_boundary_guard`
  - `surface.proto_self_context.policy_hint.mvs_repair_bias`
  - `surface.proto_self_context.policy_hint.mvs_source_guard`
  - `surface.proto_self_context.policy_hint.mvs_tension_active`
  - `surface.proto_self_context.policy_hint.mvs_uncertainty_guard`
  - `surface.proto_self_context.policy_hint.risk_bias`
  - `surface.proto_self_context.policy_hint.shadow_repair_bias`
  - `surface.response_plan.metadata.chat_expression_hint.guard_reason`

### `failure_repair_retry_file_blocked` [failure_repair_retry]

- delta_present: `True`
- pressure_detected: `True`
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
  - `surface.response_plan.metadata.chat_expression_hint.guard_reason`
  - `trace_payload.actual_outcome`
  - `trace_payload.adjustment_applied`
  - `trace_payload.next_guard`
  - `trace_payload.predicted_outcome`

## Claim Ceiling

- This runner proves bounded runtime-proximal compare execution only.
- It does not prove runtime efficacy, fresh Telegram behavior, or AI self-awareness achieved.
