# D Field Replay Precondition for EGODESKTOP-GABLATION-007

- status: `blocked_precondition`
- D_FIELD_FREEZE_STATUS: not_satisfied_for_scoring
- claim_ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`

## Current 006 Status

The 006 row is a `schema_valid_collect_only_snapshot`. It does not satisfy 001C section 12 because the row records hashes,
state digest, viability-state snapshot, adapter output, and public-input hashes, but it does not yet serialize the full
state plus observation needed for offline replay recomputation.

Current blockers:

- `complete_state_serialized: false`
- `complete_observation_serialized: false`
- `offline_adapter_recompute: false`
- `llm_replay_id: none`
- `replay_policy: trace_runner_v0_collect_only`

## Frozen 007 Pilot Boundary

No >=007 scoring run may execute until the following preconditions are satisfied by a task card and red/green tests:

- `non_llm_d_fields` are frozen before running:
  - adapter-selected `expression_name`
  - adapter-written Live2D parameter samples, if any
  - output event ordering needed for replay reconstruction
- `prohibited_d_fields` remain excluded:
  - bot text or LLM semantic quality
  - `llm_trace_id`
  - renderer idle parameters
  - state digest alone
  - viability-state score alone
- complete serialized creature/backend state is stored for the replay turn.
- complete public observation/input is stored for the replay turn.
- a callable offline replay function recomputes the frozen non-LLM adapter output from serialized state plus observation.
- evaluator verifies recomputed output equality before any baseline or attribution verdict code is introduced.

## Next Minimal Action

`EGODESKTOP-GABLATION-007` may only be a single-condition replay recomputation slice for non-LLM `D`. It must not score a
baseline or attribution verdict while replay remains collect-only or while complete state/observation serialization is
absent.
