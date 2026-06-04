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
| danger | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| danger | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| danger | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |
| frozen_self | 101 | approach | 0.00 | 0.0474 | 0.0835 | `9a5e70b4127fa808` |
| frozen_self | 102 | approach | 0.00 | 0.0474 | 0.0835 | `839b35b2632b7eba` |
| frozen_self | 103 | approach | 0.00 | 0.0474 | 0.0835 | `a6128b0d899fe040` |

## Trace Refs
- trace_hash `316e078f07b5f692`
- trace_hash `4706485abde88904`
- trace_hash `53e1a1bac58604a5`
- trace_hash `839b35b2632b7eba`
- trace_hash `9a5e70b4127fa808`
- trace_hash `a6128b0d899fe040`

## What It Proves
Within this lab setup, freezing self-model learning reduces self-risk judgment and changes action selection.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the self model is not causally involved in risk/ability judgment.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
