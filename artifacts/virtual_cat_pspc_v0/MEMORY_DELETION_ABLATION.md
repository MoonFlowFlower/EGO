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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| memory_deleted | 101 | approach | 0.00 | 0.0570 | 1.0000 | `beb659a2e91a219d` |
| memory_deleted | 102 | approach | 0.00 | 0.0570 | 1.0000 | `fb02593641ec0574` |
| memory_deleted | 103 | approach | 0.00 | 0.0570 | 1.0000 | `b95cc2c5d0215733` |

## Trace Refs
- trace_hash `36c042d4136fb343`
- trace_hash `98f315d03c1175b3`
- trace_hash `b95cc2c5d0215733`
- trace_hash `beb659a2e91a219d`
- trace_hash `fb02593641ec0574`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, deleting relevant memory reduces the cautious behavior supported by that memory.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, memory writes are logs only and not causal supports for future behavior.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
