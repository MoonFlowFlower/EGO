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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |
| frozen_world | 101 | approach | 0.00 | 0.3165 | 0.9002 | `c8f3e7762fec2af4` |
| frozen_world | 102 | approach | 0.00 | 0.3165 | 0.9002 | `4072c50f4c1ab6c8` |
| frozen_world | 103 | approach | 0.00 | 0.3165 | 0.9002 | `433c6aab0f45eeef` |

## Trace Refs
- trace_hash `316e078f07b5f692`
- trace_hash `4072c50f4c1ab6c8`
- trace_hash `433c6aab0f45eeef`
- trace_hash `4706485abde88904`
- trace_hash `53e1a1bac58604a5`
- trace_hash `c8f3e7762fec2af4`

## What It Proves
Within this lab setup, freezing world-model learning degrades prediction/planning quality.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the planner is not using the world model or prediction error is not updating it.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
