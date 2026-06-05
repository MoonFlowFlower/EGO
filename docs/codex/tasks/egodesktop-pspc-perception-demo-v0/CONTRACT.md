# EgoDesktop PSPC Perception Demo v0 Contract

## Input

- `artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json`
- Existing EgoDesktop PSPC visual shim output.

## Output

The perception demo may output only:

- `scenario_order`
- `trigger_text`
- `scenarios`
- `playback`
- `recording_mode`
- `debug_overlay`
- `no_authority`
- `side_effects_absent`
- report artifacts

## Required Scenarios

- `gentle_history` -> `warm_approach`
- `frequent_interruption` -> `cautious_boundary`
- `late_night_care` -> `low_interrupt_care`
- `mixed_history` -> `hesitation_low_confidence`

All scenarios use the same trigger: `我回来了。`

## Forbidden Fields And Effects

The perception demo must not output or invoke executable authority:

- action execution
- tool calls
- user message generation as EgoOperator reply
- memory writes
- gate decisions or gate invocation
- approval flow
- transport calls
- proactive messages
- runtime registration
- planner/model/training execution
- `enabled=true`
- `mainline_connected=true`

## Debug Overlay

The debug overlay is hidden by default and may show only:

- `packet_id`
- `style`
- `confidence`
- `basis`
- `reason_trace_refs`
- `claim_ceiling`

## Claim Ceiling

`product_only_local_perception_demo_from_shadow_proposal_hint`

This is local visual perception evidence only. It does not prove runtime integration safety, adapter readiness, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion.
