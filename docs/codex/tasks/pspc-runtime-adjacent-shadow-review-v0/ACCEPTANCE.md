# PSPC Runtime-Adjacent Shadow Review Acceptance v0

## Required Acceptance

- The review package defines default-off, audit-only, no runtime authority, no memory write, no user message, no gate invocation, no action, no transport, and no proactive side effect.
- The review package states what this proves, what it does not prove, rollback, forbidden surfaces, failure meaning, and claim ceiling.
- No EgoOperator runtime, gate, memory, approval, human-trial harness, transport, or proactive channel file is modified.
- Static scan confirms PSPC is not imported or registered by EgoOperator runtime.
- Verdict may only allow PSPC-SHADOW-002 or no_go_keep_artifact_only.
- Verdict must not approve runtime integration, adapter readiness, live runtime hook safety, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Static Scan Requirement

The static scan must search non-adapter runtime sources for these markers:

- pspc_lab_adapter
- PSPCLabAdapter
- pspc_read_only_shadow_hook
- PSPCReadOnlyShadowHook
- pspc_runtime_adjacent
- PSPC runtime observer names introduced by future tasks

The scan must exclude PSPC adapter files and tests when checking whether runtime imports PSPC.

## Autopilot Acceptance

After this task closes:

- PSPC-SHADOW-001 status is accepted.
- PSPC-SHADOW-002 status is active.
- python scripts/codex_project_autopilot.py plan-next selects PSPC-SHADOW-002.
- GitHub Project mirror remains unavailable if gh is not on PATH; this must be reported as unavailable, not pass.

## Failure Meaning

If static scan finds runtime imports or registration, this stage fails and the path must stop at no_go_keep_artifact_only until the runtime reference is removed.

If any document allows direct action, direct user message, direct memory write, runtime gate bypass, transport, proactive trigger, enabled:true, or mainline_connected:true, this stage fails.

## Rollback

Delete docs/codex/tasks/pspc-runtime-adjacent-shadow-review-v0/ and revert the task-board status update. No runtime rollback should be needed because runtime changes are forbidden.

## Claim Ceiling

lab_only_proto_self_mechanism_candidate / runtime_adjacent_shadow_review_only
