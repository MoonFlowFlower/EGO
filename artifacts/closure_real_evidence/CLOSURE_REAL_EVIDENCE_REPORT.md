# Closure Real Evidence Report

## Scope

Task: `P3：真实 Telegram Closure 证据补采任务单`

Goal:
- verify upgraded closure-level identity on the real Telegram mainline
- verify real `execute_task / tool` evidence instead of local-only tests
- judge whether Q1-Q4 and the task completion gate are truly satisfied

This report uses real Telegram samples captured on March 26, 2026 and March 27, 2026 UTC.

## Executive Verdict

Status: `partial / not yet accepted`

What is now proven:
- real Telegram samples now contain closure-level fields in host ledger, OpenEmotion trace payload, and real evidence bundles
- the explicit-path root bug is fixed at the host/runtime layer: a direct path read request no longer collapses into stale `execute_task` step continuation
- post-fix real Telegram evidence bundles are complete enough to audit `normalized_event / openemotion_result / openemotion_trace / response_plan / outbox_record`
- the real `execute_task / tool` path is now evidenced with one blocked sample and two success samples

What is still not proven enough to claim full task completion:
- Q2 is only partially satisfied in reality: `tool:file blocked` and `tool:file success` split identity correctly, but their `closure_family_id` also splits on the real host chain
- Q3 is not satisfied formally: the retry path is real, but `repair_closure` did not become `true` in the real trace

## Acceptance Matrix

### Q1. Real closure-level fields landed

Status: `pass`

Confirmed real fields:
- `closure_signature`
- `closure_family_id`
- `action_signature`
- `outcome_signature`
- `closure_consistency_score`
- `order_invariance_candidate`

Direct real evidence:
- `sample_20260326_230059_8ded092c`
- `sample_20260326_230231_74277be4`
- `sample_20260326_230256_0fbd5ecc`
- `EgoCore/logs/proto_self_trace.jsonl`
- `EgoCore/artifacts/proto_self_store/agent_global/proto_self_state.v1.json`

State continuity evidence:
- agent-global store still contains pre-existing upgraded signatures such as:
  - `f92efd86648b35ec` for `tool:file -> success`
  - `6d2632f5abecd172` for `ingress:user_request -> unknown`
  - `3e728db79c906f48` for `tool:file -> blocked`

### Q2. Same bucket / different outcome split is real

Status: `partial`

Real blocked sample:
- `sample_20260326_230059_8ded092c`
- input: `读取 D:\Project\AIProject\MyProject\Test\missing_closure_probe.md 前 1 行`
- tool result:
  - `action_signature = tool:file`
  - `outcome_signature = blocked`
  - `closure_signature = 3e728db79c906f48`
  - `closure_family_id = 6824edaf39136534`

Real success samples:
- `sample_20260326_230231_74277be4`
- `sample_20260326_230256_0fbd5ecc`
- tool result:
  - `action_signature = tool:file`
  - `outcome_signature = success`
  - `closure_signature = f92efd86648b35ec`
  - `closure_family_id = 7a053f9ff7c61219`

What this proves:
- real host execution does split blocked vs success into different closure identities
- real host execution is no longer faking the path via stale task-step carry-over

Why Q2 is not a clean pass:
- the local design/tests expect success/failure of the same tool family to keep the same `closure_family_id` while splitting `closure_signature`
- on the real host chain, blocked samples pick up `runtime:tool_result:general:risk_high` while success samples stay in `runtime:tool_result:general`
- because `closure_family_id` is derived from `psi_bucket | action_signature`, the family splits too

Conclusion:
- `different-identity` is real
- `same-family` is not yet true on the real host chain
- this is a real-world drift from the intended closure-family contract

### Q3. Repair closure accumulates in reality

Status: `fail / not yet satisfied`

Real retry path observed:
1. blocked read of missing file
2. follow-up request: `如果刚才失败了，现在读取 ... CLAUDE.md 前 1 行`
3. repeated success: `再读取一次 ... CLAUDE.md 前 1 行`

What is real:
- the retry path is real Telegram traffic
- the retry path produced one blocked `tool:file` sample and two later success `tool:file` samples
- success consistency reached `1.0` for `tool:file -> success`

What is missing:
- `repair_closure` stayed `false`
- the success sample remained in `mode_signature = exploration`
- there is no formal real-trace proof that the retry was promoted as a repair closure

Conclusion:
- human-readable repair behavior happened
- formal repair-closure recognition did not happen
- Q3 cannot be counted as complete

### Q4. Compatibility loading without migration break

Status: `pass`

Evidence:
- `EgoCore/artifacts/proto_self_store/sessions/telegram_dm_8420019401/session.json`
  - `preserves_agent_global = true`
- `EgoCore/artifacts/proto_self_store/threads/telegram_dm_8420019401/thread.json`
  - thread/event chain continued after reset and restart
- `EgoCore/artifacts/proto_self_store/agent_global/proto_self_state.v1.json`
  - old upgraded signatures remained available and continued strengthening after new real samples

What this proves:
- `/new` and restart did not require any batch migration
- the live Telegram thread resumed on top of existing agent-global state
- the host-side compatibility path did not break the real session recovery chain

## Execute-Task Mainline Evidence

This task explicitly required more than chat/reply evidence.

Real `execute_task / tool` evidence now exists in complete bundles:
- `sample_20260326_230059_8ded092c`
- `sample_20260326_230231_74277be4`
- `sample_20260326_230256_0fbd5ecc`

These bundles contain:
- `raw_update`
- `normalized_event`
- `openemotion_result`
- `openemotion_trace`
- `response_plan`
- `outbox_record`

This was not true before the host-side evidence collector fix.

## Root Cause Findings Exposed By Real Evidence

### 1. Host-side stale target contamination was real

Before the fix, direct path reads could be contaminated by `last_uploaded_artifact` and old task state, causing replies like:
- `开始执行第 5 步：read_lines`

After the fix, the real Telegram path behaved correctly:
- missing file -> blocked reply
- explicit path success -> correct read reply

### 2. Evidence collector sample mixing was real

Before the fix, later real Telegram samples lost `normalized_event / openemotion / response_plan` because the collector used a single mutable current sample.

After the fix, the March 26, 2026 23:00 local samples are complete E4 bundles.

### 3. Real host chain still exposes a family-splitting drift

The real host path appends risk-level information into `psi_bucket`.
That causes:
- blocked `tool:file` to land in a different `closure_family_id` from success `tool:file`

This drift is the main reason Q2 is not a clean pass.

### 4. Real repair path is not yet formally recognized

The real retry sequence did not flip:
- `repair_closure = true`
- `mode_signature = repair`

This is the main reason Q3 is not yet a pass.

## Final Judgment

This round successfully completed the evidence supplement itself:
- real Telegram evidence was captured
- real host bugs in request binding and sample capture were exposed and fixed
- real complete bundles now exist

But the task's strict completion gate is still not fully met.

Current completion state:
- Q1: pass
- Q2: partial
- Q3: fail
- Q4: pass
- real execute-task evidence: pass

Therefore the task cannot honestly be reported as fully accepted yet.

## Next Required Task

The next task should not be "collect more of the same samples".
The next required task is algorithm/contract correction for the real host chain:
- keep blocked/success in the same closure family when they are the same action family
- make real retry paths recognizable as `repair_closure`

