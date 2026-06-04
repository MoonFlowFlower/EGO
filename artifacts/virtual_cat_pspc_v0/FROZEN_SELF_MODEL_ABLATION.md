# VirtualCatPSPC v0 Frozen Self Model Ablation

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
Self-model learning is disabled while world-risk prediction remains available.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| frozen_self | 101 | approach | 0.00 | 0.0474 | 0.0835 | `c4b85345a186e6b7` |
| frozen_self | 102 | approach | 0.00 | 0.0474 | 0.0835 | `175bed4a469239f8` |
| frozen_self | 103 | approach | 0.00 | 0.0474 | 0.0835 | `15c57674c187df81` |

## Trace Refs
- trace_hash `15c57674c187df81`
- trace_hash `175bed4a469239f8`
- trace_hash `36c042d4136fb343`
- trace_hash `98f315d03c1175b3`
- trace_hash `c4b85345a186e6b7`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, freezing self-model learning reduces self-risk judgment and changes action selection.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the self model is not causally involved in risk/ability judgment.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
