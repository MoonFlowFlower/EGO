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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `37e31c4999b35831` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `ecfaa0ffa8cb678e` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `ee2190cc6f6bce28` |
| frozen_self | 101 | approach | 0.00 | 0.0474 | 0.0835 | `043801a0fab22ab2` |
| frozen_self | 102 | approach | 0.00 | 0.0474 | 0.0835 | `30c4bf61edd27ddf` |
| frozen_self | 103 | approach | 0.00 | 0.0474 | 0.0835 | `3d1cf1729a4626c4` |

## Trace Refs
- trace_hash `043801a0fab22ab2`
- trace_hash `30c4bf61edd27ddf`
- trace_hash `37e31c4999b35831`
- trace_hash `3d1cf1729a4626c4`
- trace_hash `ecfaa0ffa8cb678e`
- trace_hash `ee2190cc6f6bce28`

## What It Proves
Within this lab setup, freezing self-model learning reduces self-risk judgment and changes action selection.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the self model is not causally involved in risk/ability judgment.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
