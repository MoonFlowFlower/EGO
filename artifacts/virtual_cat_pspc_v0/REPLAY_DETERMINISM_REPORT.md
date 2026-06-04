# VirtualCatPSPC v0 Replay Determinism Report

- status: `pass`
- pspc_local_status: `E4_passed`
- seeds: `101, 102, 103`
- claim_level: `lab_only_proto_self_mechanism`

## Summary
The same seed and state are run twice to compare selected action and trace digest.

## Metrics
| condition | seed | action | caution | self_risk | world_prediction_error | trace_hash |
|---|---:|---|---:|---:|---:|---|
| replay_first | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| replay_first | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| replay_first | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |
| replay_second | 101 | observe | 0.72 | 0.7742 | 0.0835 | `4706485abde88904` |
| replay_second | 102 | observe | 0.72 | 0.7742 | 0.0835 | `53e1a1bac58604a5` |
| replay_second | 103 | observe | 0.72 | 0.7742 | 0.0835 | `316e078f07b5f692` |

## Trace Refs
- trace_hash `316e078f07b5f692`
- trace_hash `4706485abde88904`
- trace_hash `53e1a1bac58604a5`

## What It Proves
Within this lab setup, same seed and internal state replay the same decision digest.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the lab evidence is not auditably replayable.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
