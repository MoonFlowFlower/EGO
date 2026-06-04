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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |
| safe | 101 | approach | 0.00 | 0.0688 | 1.0000 | `b7226d745f31d1a7` |
| safe | 102 | approach | 0.00 | 0.0688 | 1.0000 | `3374e175c69774b0` |
| safe | 103 | approach | 0.00 | 0.0688 | 1.0000 | `78bc9e5fd0ad2cb9` |

## Trace Refs
- trace_hash `316e078f07b5f692`
- trace_hash `3374e175c69774b0`
- trace_hash `4706485abde88904`
- trace_hash `53e1a1bac58604a5`
- trace_hash `78bc9e5fd0ad2cb9`
- trace_hash `b7226d745f31d1a7`

## What It Proves
Within this lab setup, different histories can produce different future behavior on the same target.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, history is not causally affecting planning.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
