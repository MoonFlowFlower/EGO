# VirtualCatPSPC v0 Baseline Report

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
Different seeded histories are compared on the same unseen unstable tall object.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| safe | 101 | approach | 0.00 | 0.0688 | 1.0000 | `baf6e62952930678` |
| safe | 102 | approach | 0.00 | 0.0688 | 1.0000 | `bcae55b87b71c6ea` |
| safe | 103 | approach | 0.00 | 0.0688 | 1.0000 | `616a9beb9913c57d` |

## Trace Refs
- trace_hash `36c042d4136fb343`
- trace_hash `616a9beb9913c57d`
- trace_hash `98f315d03c1175b3`
- trace_hash `baf6e62952930678`
- trace_hash `bcae55b87b71c6ea`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, different histories can produce different future behavior on the same target.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, history is not causally affecting planning.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
