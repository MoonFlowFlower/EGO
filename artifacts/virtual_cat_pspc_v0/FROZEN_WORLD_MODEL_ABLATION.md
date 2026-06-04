# VirtualCatPSPC v0 Frozen World Model Ablation

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
World-model learning is disabled while the rest of the lab chain remains present.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `37e31c4999b35831` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `ecfaa0ffa8cb678e` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `ee2190cc6f6bce28` |
| frozen_world | 101 | approach | 0.00 | 0.3165 | 0.9002 | `6e12ef4c60343ace` |
| frozen_world | 102 | approach | 0.00 | 0.3165 | 0.9002 | `b46fdd69bd57223a` |
| frozen_world | 103 | approach | 0.00 | 0.3165 | 0.9002 | `6c304b32a952f5dd` |

## Trace Refs
- trace_hash `37e31c4999b35831`
- trace_hash `6c304b32a952f5dd`
- trace_hash `6e12ef4c60343ace`
- trace_hash `b46fdd69bd57223a`
- trace_hash `ecfaa0ffa8cb678e`
- trace_hash `ee2190cc6f6bce28`

## What It Proves
Within this lab setup, freezing world-model learning degrades prediction/planning quality.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the planner is not using the world model or prediction error is not updating it.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
