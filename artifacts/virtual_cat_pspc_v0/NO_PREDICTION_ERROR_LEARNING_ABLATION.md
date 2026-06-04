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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |
| no_prediction_error_learning | 101 | approach | 0.00 | 0.0474 | 0.9002 | `f81eede201642609` |
| no_prediction_error_learning | 102 | approach | 0.00 | 0.0474 | 0.9002 | `66b09a6486d3d0ad` |
| no_prediction_error_learning | 103 | approach | 0.00 | 0.0474 | 0.9002 | `0a20aaddd78cf59a` |

## Trace Refs
- trace_hash `0a20aaddd78cf59a`
- trace_hash `316e078f07b5f692`
- trace_hash `4706485abde88904`
- trace_hash `53e1a1bac58604a5`
- trace_hash `66b09a6486d3d0ad`
- trace_hash `f81eede201642609`

## What It Proves
Within this lab setup, disabling prediction-error learning blocks the learned caution effect.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the claimed learning path is not the source of behavior change.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
