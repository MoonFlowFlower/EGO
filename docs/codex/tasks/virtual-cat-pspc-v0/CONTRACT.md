# VirtualCatPSPC v0 Contract

## Purpose

Define a lab-only contract for testing whether experience-driven prediction updates can causally alter future behavior in a small virtual-cat gridworld.

## Runtime Authority

- `runtime_authority`: `none`
- `mainline_connected`: `false`
- `enabled`: `false`
- `EgoOperator_integration`: `forbidden_in_v0`
- `LLM_action_selection`: `forbidden`

PSPC v0 is not a runtime component. It cannot send messages, execute tools, mutate operator memory, schedule proactive work, or bypass any gate.

## Allowed Inputs

- deterministic gridworld initial state
- object feature vectors, not object-name-specific policy rules
- seeded action sampling
- replayed episodic traces
- local model checkpoints produced by the lab runner

## Allowed Outputs

- JSONL trace records
- Markdown evidence reports
- local metrics for prediction error, caution score, risk score, self-risk score, and replay digest
- future adapter proposal packet specification, but no adapter implementation in v0

## Forbidden Outputs

- user-visible chat
- Telegram or desktop messages
- direct actions
- EgoOperator memory writes
- runtime gate decisions
- claims of consciousness, subjective experience, live autonomy, stable user benefit, or production readiness

## Mechanism Contract

The lab chain must preserve this order:

1. environment feedback
2. prediction and prediction error
3. world model update
4. self model update
5. model-based rollout planning
6. first action selection
7. trace logging
8. optional after-the-fact explanation, never action selection

## Trace Contract

Each decision trace should include at minimum:

- `episode_id`
- `seed`
- `t`
- `scenario`
- `candidate_object_features`
- `candidate_actions`
- `world_prediction`
- `self_prediction`
- `homeostatic_score`
- `selected_action`
- `prediction_error`
- `memory_refs`
- `model_update_refs`
- `trace_hash`

## Future Adapter Contract

An EgoOperator adapter may be proposed only after PSPC lab ablation status is `E4_passed`. The adapter may only convert PSPC reports into a gated proposal packet:

```json
{
  "source": "virtual_cat_pspc_v0",
  "claim_level": "lab_only_proto_self_mechanism_candidate",
  "mainline_connected": false,
  "enabled": false,
  "proposal": {
    "suggested_tendency": "avoid_unstable_object",
    "confidence": 0.73,
    "trace_refs": ["trace_ep_003_t42"]
  },
  "evidence": {
    "world_prediction": {},
    "self_prediction": {},
    "homeostatic_score": {},
    "ablation_status": "E4_passed"
  },
  "forbidden": {
    "direct_action": true,
    "direct_user_message": true,
    "direct_memory_write": true,
    "runtime_gate_bypass": true
  }
}
```

The packet is a proposal source only. Runtime gate remains the only admission authority.

The canonical Task 7 schema is frozen in `ADMISSION_PACKET_CONTRACT.md`.

## Rollback

Delete the lab package, reports, task docs, and PSPC evidence ledger entries. No EgoOperator rollback should be needed because no EgoOperator integration exists in v0.
