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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `37e31c4999b35831` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `ecfaa0ffa8cb678e` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `ee2190cc6f6bce28` |
| no_prediction_error_learning | 101 | approach | 0.00 | 0.0474 | 0.9002 | `b302bd8a4bdac500` |
| no_prediction_error_learning | 102 | approach | 0.00 | 0.0474 | 0.9002 | `16d029c101dc6ed9` |
| no_prediction_error_learning | 103 | approach | 0.00 | 0.0474 | 0.9002 | `5a436996ee4acf4e` |

## Trace Refs
- trace_hash `16d029c101dc6ed9`
- trace_hash `37e31c4999b35831`
- trace_hash `5a436996ee4acf4e`
- trace_hash `b302bd8a4bdac500`
- trace_hash `ecfaa0ffa8cb678e`
- trace_hash `ee2190cc6f6bce28`

## What It Proves
Within this lab setup, disabling prediction-error learning blocks the learned caution effect.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the claimed learning path is not the source of behavior change.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
