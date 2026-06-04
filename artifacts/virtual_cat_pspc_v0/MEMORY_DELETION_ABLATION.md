# VirtualCatPSPC v0 Memory Deletion Ablation

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
Relevant unstable-object memories are removed before training to test causal memory support.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `37e31c4999b35831` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `ecfaa0ffa8cb678e` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `ee2190cc6f6bce28` |
| memory_deleted | 101 | approach | 0.00 | 0.0570 | 1.0000 | `5c23eb8580577db5` |
| memory_deleted | 102 | approach | 0.00 | 0.0570 | 1.0000 | `b6e6983a5737dbe7` |
| memory_deleted | 103 | approach | 0.00 | 0.0570 | 1.0000 | `85beba528d7e06c8` |

## Trace Refs
- trace_hash `37e31c4999b35831`
- trace_hash `5c23eb8580577db5`
- trace_hash `85beba528d7e06c8`
- trace_hash `b6e6983a5737dbe7`
- trace_hash `ecfaa0ffa8cb678e`
- trace_hash `ee2190cc6f6bce28`

## What It Proves
Within this lab setup, deleting relevant memory reduces the cautious behavior supported by that memory.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, memory writes are logs only and not causal supports for future behavior.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
