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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| frozen_world | 101 | approach | 0.00 | 0.3165 | 0.9002 | `a2596eed8a579476` |
| frozen_world | 102 | approach | 0.00 | 0.3165 | 0.9002 | `517323017c6207bb` |
| frozen_world | 103 | approach | 0.00 | 0.3165 | 0.9002 | `b1bc944d04e32641` |

## Trace Refs
- trace_hash `36c042d4136fb343`
- trace_hash `517323017c6207bb`
- trace_hash `98f315d03c1175b3`
- trace_hash `a2596eed8a579476`
- trace_hash `b1bc944d04e32641`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, freezing world-model learning degrades prediction/planning quality.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the planner is not using the world model or prediction error is not updating it.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
