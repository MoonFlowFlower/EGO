# PSPC Disabled Runtime Shadow Hook Contract v0

## Contract Status

- status: `stage_card_only`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`
- allowed_use: `future_task_boundary_only`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / disabled_runtime_shadow_hook_stage_card_only`

## Future Hook Defaults

Any future hook must be inert by default:

```json
{
  "source": "virtual_cat_pspc_v0",
  "hook_mode": "shadow_audit_only",
  "enabled": false,
  "mainline_connected": false,
  "runtime_authority": "none",
  "allowed_use": "audit_artifact_only"
}
```

## Allowed Future Output

Only a shadow audit artifact may be produced:

```json
{
  "source": "pspc_disabled_runtime_shadow_hook_v0",
  "claim_level": "lab_only_proto_self_mechanism_candidate",
  "enabled": false,
  "mainline_connected": false,
  "runtime_authority": "none",
  "audit_candidate": {
    "evidence_refs": [],
    "proposal_hint": null,
    "non_executable": true
  },
  "side_effects": {
    "user_response_changed": false,
    "memory_written": false,
    "gate_invoked": false,
    "approval_changed": false,
    "transport_called": false,
    "proactive_triggered": false,
    "runtime_registered": false,
    "planner_called": false,
    "training_called": false,
    "model_executed": false
  }
}
```

## Forbidden Future Output

The future hook must reject or omit:

- `action`
- `tool_call`
- `command`
- `user_message`
- `memory_write`
- `gate_decision`
- `approval_id`
- `approval_decision`
- `transport`
- `send`
- `schedule`
- `enable`
- `mainline_authority`
- executable proposal fields
- runtime registration fields
- proactive trigger fields
- planner/training/model execution hooks

## Runtime Boundary

The hook may not own or modify:

- proposal selection
- plan selection
- approval state
- gate decision
- user response
- memory records
- transport calls
- proactive scheduling
- runtime registry
- EgoOperator claim ceiling

## Failure Meaning

If the future implementation needs any forbidden surface to work, it is not a shadow hook and must be rejected or reframed as a separate high-impact runtime task.
