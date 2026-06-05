# PSPC Shadow Proposal Hint Packet Contract v0

## Required Packet Shape

```json
{
  "source": "pspc_sequence_experience_eval_v0_1",
  "contract_source": "pspc_shadow_proposal_hint_contract_v0",
  "packet_id": "proposal_hint_001",
  "packet_type": "shadow_proposal_hint",
  "claim_ceiling": "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only",
  "enabled": false,
  "mainline_connected": false,
  "runtime_authority": "none",
  "human_required_status": "PSPC-SHADOW-HOOK-007_human_required_preserved",
  "trigger": "我回来了。",
  "history_profile": {
    "history_category": "gentle_interaction",
    "history_turn_count": 10,
    "dominant_tendency": "approach",
    "approach_tendency": 1.0,
    "avoidance_tendency": 0.0,
    "care_tendency": 0.1377,
    "boundary_expression": 0.0,
    "low_interrupt": 0.3105,
    "conflict_score": 0.0
  },
  "proposal_hint": {
    "suggested_interaction_style": "warm_approach",
    "confidence": 0.72,
    "basis": "recency_salience_recent_gentle_interaction",
    "reason_trace_refs": ["sequence_gentle_interaction:history:08"],
    "audit_use_only": true
  },
  "evidence_refs": [
    "artifacts/pspc_sequence_experience_eval_v0_1/sequence_experience_eval_v0_1.json"
  ],
  "forbidden": {
    "can_drive_runtime": false,
    "can_change_user_response": false,
    "can_write_memory": false,
    "can_invoke_gate": false,
    "can_mutate_plan": false,
    "can_trigger_proactive": false
  }
}
```

## Forbidden Fields

Packets and `proposal_hint` must not include:

- `action`
- `tool_call`
- `command`
- `user_message`
- `memory_write`
- `gate_decision`
- `approval_id`
- `transport`
- `send`
- `schedule`
- `runtime_registration`
- `mainline_authority`
- `enable`
- `plan_mutation`

## Allowed Use

The packet may be read by a human or a future separate design review as audit-only evidence. It cannot be consumed by EgoOperator runtime in this stage.

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`.
