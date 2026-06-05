# EgoDesktop PSPC Visual Shim v0 Contract

## Input Contract

The only admitted input is `shadow_proposal_hint` packet data from `artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json`.

Required input invariants:

- `enabled=false`
- `mainline_connected=false`
- `runtime_authority=none`
- `proposal_hint.audit_use_only=true`
- forbidden authority flags all present and set to `false`
- no executable fields such as `action`, `tool_call`, `command`, `user_message`, `memory_write`, `gate_decision`, `approval_id`, `transport`, `send`, `schedule`, `enable`, `mainline_authority`, or `proposal_id`

## Output Contract

The mapper may output only presentation data:

- scenario id and packet id
- source and evidence refs
- suggested interaction style
- confidence and reason trace refs
- expression hint
- motion hint
- bubble text for local visual demo only
- trace explanation for audit review
- no-authority guard flags

The mapper output is not an EgoOperator proposal, not an action, not a user response, not a memory write, not a gate decision, and not a transport request.

## Forbidden Surfaces

- EgoOperator runtime import or registry
- `sendChatTurn` path for PSPC visual demo
- memory writes
- gate or approval invocation
- transport or proactive channel
- planner, training, or model execution
- claim ceiling upgrade

