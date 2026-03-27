## P4 Summary

P4 fixed the two real-mainline issues exposed by P3 without moving formal family or repair semantics into EgoCore.

- `same-family drift` is fixed in OpenEmotion.
- `repair_closure` now lights up on the real retry-success turn.
- Existing E4 evidence capture and replay compatibility stayed intact.

## Root Cause

Pre-fix evidence is captured in [FAMILY_REPAIR_DIFF_TABLE.md](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/closure_repair_fix/FAMILY_REPAIR_DIFF_TABLE.md).

- `closure_family_id` was computed from `psi_bucket|action_signature`.
- Real blocked `tool:file` samples used `psi_bucket=runtime:tool_result:general:risk_high`.
- Real success `tool:file` samples used `psi_bucket=runtime:tool_result:general`.
- That meant family split happened before closure identity logic could do its job.
- `repair_closure` depended on `mode_signature == repair`, but the real retry-success sample stayed at `mode_signature=exploration`, so the real retry chain never qualified.

## Minimal Fix

### OpenEmotion

- [cycles.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/cycles.py)
  - Added `family_bucket` so `closure_family_id` is computed from coarse closure family fields instead of risk-suffixed `psi_bucket`.
  - Kept `closure_signature` closure-sensitive by leaving full `psi_bucket`, `outcome_signature`, and `mode_signature` in the identity hash.
  - Reworked repair detection to recognize recent same-action `blocked/failure -> success` precursors from `episodic_trace`.
- [self_model.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/self_model.py)
  - `blocked` now enters repair semantics alongside `failure`, so blocked tool results can formally participate in repair closure formation.

### EgoCore

- No formal family/repair semantics were added to host normalization.
- [test_runtime_v2_proto_self_runtime.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/tests/test_runtime_v2_proto_self_runtime.py) now explicitly guards against host-side semantic theft.

## Validation

### Required tests

- T1 real-sample fixture regression:
  - [test_cycle_real_mainline_regression.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py)
- T2 same-family split test:
  - [test_cycle_real_mainline_regression.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py)
  - [test_cycle_closure_identity.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_closure_identity.py)
- T3 repair-closure activation test:
  - [test_cycle_real_mainline_regression.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py)
- T4 backward compatibility test:
  - [test_cycle_real_mainline_regression.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py)
  - [test_kernel_replay.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_kernel_replay.py)
- T5 no-host-semantic-theft test:
  - [test_runtime_v2_proto_self_runtime.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/tests/test_runtime_v2_proto_self_runtime.py)

### Local regression

- `pytest --capture=no openemotion/proto_self/tests -q`
  - Result: `42 passed`
- `PYTHONPATH=. pytest --capture=no tests/test_runtime_v2_telegram_bridge_actions.py tests/test_telegram_bot_native_switch.py tests/test_telegram_evidence_collector.py tests/test_runtime_v2_proto_self_runtime.py -q`
  - Result: `28 passed, 1 warning`

### Real Telegram proof

Post-fix real samples:

- [sample_20260326_232655_3f3f89cb](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_232655_3f3f89cb)
  - `tool:file`
  - `outcome_signature=blocked`
  - `closure_family_id=7a053f9ff7c61219`
  - `closure_signature=2581087c260a2524`
  - `mode_signature=repair`
  - `repair_closure=false`
- [sample_20260326_232715_271e229b](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_232715_271e229b)
  - `tool:file`
  - `outcome_signature=success`
  - `closure_family_id=7a053f9ff7c61219`
  - `closure_signature=f92efd86648b35ec`
  - `repair_closure=true`
- [sample_20260326_232738_49b65b2e](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/telegram_real_mainline_v1/real_telegram/sample_20260326_232738_49b65b2e)
  - `tool:file`
  - `outcome_signature=success`
  - `closure_family_id=7a053f9ff7c61219`
  - `closure_signature=f92efd86648b35ec`
  - `repair_closure=false`

This satisfies the intended real-mainline repair pattern:

- blocked/success remain split at `closure_signature`
- blocked/success align at `closure_family_id`
- the first retry-success lights `repair_closure=true`
- the repeated success stays in-family without repeatedly claiming repair

## Task Criteria Check

- S1 same-family alignment: passed
- S2 repair_closure activation: passed
- S3 no dual authority / no host semantic theft: passed
- S4 no regression of existing real E4 chain: passed

## Still Not Implemented

- No multi-step closure graph identity
- No closure archetype taxonomy
- No formal invariant proof over arbitrary retry chains
- No broader developmental-self expansion beyond the current minimal repair/family semantics
