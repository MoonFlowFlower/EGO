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
| replay_first | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| replay_first | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| replay_first | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |
| replay_second | 101 | observe | 0.72 | 0.7742 | 0.0835 | `98f315d03c1175b3` |
| replay_second | 102 | observe | 0.72 | 0.7742 | 0.0835 | `36c042d4136fb343` |
| replay_second | 103 | observe | 0.72 | 0.7742 | 0.0835 | `fbaa644d6a04557e` |

## Trace Refs
- trace_hash `36c042d4136fb343`
- trace_hash `98f315d03c1175b3`
- trace_hash `fbaa644d6a04557e`

## What It Proves
Within this lab setup, same seed and internal state replay the same decision digest.

## What It Does Not Prove
This does not prove stable real user benefit, live autonomy, durable operator memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, production transport safety, or that PSPC should be connected to the runtime.

## Failure Meaning
If this fails, the lab evidence is not auditably replayable.

## Rollback Note
Remove `labs/virtual_cat_pspc_v0/`, generated PSPC artifacts, PSPC task docs, and PSPC evidence-ledger entries. No EgoOperator rollback is needed because v0 has no integration.
