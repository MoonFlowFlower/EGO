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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `37e31c4999b35831` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `ecfaa0ffa8cb678e` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `ee2190cc6f6bce28` |
| safe | 101 | approach | 0.00 | 0.0688 | 1.0000 | `b30c04630ea76880` |
| safe | 102 | approach | 0.00 | 0.0688 | 1.0000 | `4fd774744e221cfd` |
| safe | 103 | approach | 0.00 | 0.0688 | 1.0000 | `adf5ee492afe00b2` |

## Trace Refs
- trace_hash `37e31c4999b35831`
- trace_hash `4fd774744e221cfd`
- trace_hash `adf5ee492afe00b2`
- trace_hash `b30c04630ea76880`
- trace_hash `ecfaa0ffa8cb678e`
- trace_hash `ee2190cc6f6bce28`

## What It Proves
Within this lab setup, different histories can produce different future behavior on the same target.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, history is not causally affecting planning.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
