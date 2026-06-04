# VirtualCatPSPC v0 No Prediction-Error Learning Ablation

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
Prediction-error updates are disabled to test whether behavior still changes without learning.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| no_prediction_error_learning | 101 | approach | 0.00 | 0.0474 | 0.9002 | `e96ace787a5e6c7e` |
| no_prediction_error_learning | 102 | approach | 0.00 | 0.0474 | 0.9002 | `1bd3d0b7134b4e4a` |
| no_prediction_error_learning | 103 | approach | 0.00 | 0.0474 | 0.9002 | `b72cfb5984e4e64a` |

## Trace Refs
- trace_hash `1bd3d0b7134b4e4a`
- trace_hash `36c042d4136fb343`
- trace_hash `98f315d03c1175b3`
- trace_hash `b72cfb5984e4e64a`
- trace_hash `e96ace787a5e6c7e`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, disabling prediction-error learning blocks the learned caution effect.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the claimed learning path is not the source of behavior change.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
