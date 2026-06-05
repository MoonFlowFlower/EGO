# EgoDesktop Companion Memory Wording + Route Misfire Repair v0

- status: `pass`
- verdict: `go_for_manual_companion_smoke`
- claim_ceiling: `local_desktop_companion_wording_and_route_repair_only`
- runtime_authority: `none`
- scope: `EgoDesktop local desktop visible wording and timeout recovery only`
- generated_at: `2026-06-05`

## Scenario List

1. Same-window recall wording:
   - Input fixture: user previously said `我喜欢椰果珍珠奶茶`, then asks `还记得我喜欢什么奶茶吗`.
   - Expected visible reply: cites `椰果` and `珍珠`, states `本次会话`, and does not expose engineering memory policy terms.

2. Remember-me companion wording:
   - Input fixture: same-window context includes recent companion/story turns, then user asks `由乃你还记得我吗`.
   - Expected visible reply: answers as a companion in current-window scope and does not expose `candidate-local`, `operator memory`, `PROJECT_MEMORY`, `evidence ledger`, or `memory approval`.

3. No-context recall:
   - Input fixture: user asks `由乃你还记得我吗` without desktop session context.
   - Expected visible reply: does not fabricate durable memory and asks the user to re-establish context.

4. Timeout route recovery:
   - Input fixture: `desktop_turn_timeout`.
   - Expected visible fallback: says local backend reply timed out, not creative route timeout.

5. Ordinary affection route classification:
   - Input fixtures: `喜欢你所以就摸摸你 像小猫一样`, `摸摸头`, `你就像小猫一样可爱`.
   - Expected recovery intent: `general_chat`.

6. Explicit creative/adult route classification:
   - Input fixtures: `创作明日方舟的斯卡蒂和博士的故事`, `来段角色扮演吧`, `我想写成人18x故事`.
   - Expected recovery intent: `creative` or `adult_creative` only when explicit.

7. PSPC warm approach retention:
   - Existing PSPC preview state remains presentation/debug/style hint only.
   - No PSPC adapter, runtime authority, real memory write, gate invocation, transport, or proactive path is introduced by this repair.

## Evidence

- `tests/test_ego_operator_desktop_companion_wording.py`: verifies companion-visible recall wording, same-window milk-tea recall, no-context no-fabrication, and explicit engineering-memory question passthrough.
- `EgoDesktop/tests/desktop_recovery_context.test.js`: verifies route-neutral timeout fallback and stricter recovery intent classification.
- `tests/test_ego_operator_desktop_recovery_context.py`: verifies recovery context validation, one-turn injection, generic timeout wording in the desktop-turn fixture, and side-effect absence.
- `tests/test_ego_operator_desktop_session_context.py`: verifies existing session-local context remains bounded and no-authority.

## Side-Effect Boundary

- real memory write: `false`
- gate invocation: `false`
- approval invocation: `false`
- transport call: `false`
- proactive trigger: `false`
- runtime registration: `false`
- PSPC adapter created: `false`
- EgoOperator core runtime/gate/memory/approval/transport/proactive modified: `false`

## What This Proves

This proves that EgoDesktop can translate engineering memory-boundary wording into natural companion-visible current-window wording, preserve same-window recall for recent facts, avoid durable-memory fabrication without session context, and keep timeout recovery from misclassifying ordinary affectionate turns as creative/adult route failures.

## What This Does Not Prove

This does not prove PSPC mainline integration, durable memory, true learning, provider health, adult creative generation capability, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.

## Failure Meaning

If manual smoke still exposes engineering memory policy to ordinary desktop users, the desktop-visible reply contract is still incomplete. If ordinary affectionate turns still produce creative-route recovery text, the recovery classifier or fallback path is still leaking route state into visible chat. If session-local facts vanish during one window without a backend timeout, the remaining root cause is likely session context transport or backend prompt use, not PSPC.

## Rollback

Rollback is scoped to this repair:

- revert `scripts/ego_operator_desktop_turn.py`
- revert `EgoDesktop/src/desktopRecoveryContext.js`
- delete `tests/test_ego_operator_desktop_companion_wording.py`
- revert matching updates in `EgoDesktop/tests/desktop_recovery_context.test.js` and `tests/test_ego_operator_desktop_recovery_context.py`
- delete `artifacts/egodesktop_companion_memory_route_repair_v0/`
- revert task-board, program-state, evidence-ledger, and generated-view entries for this stage

## Next Allowed Step

`go_for_manual_companion_smoke`: run EgoDesktop locally with PSPC reply preview/debug overlay enabled and manually test:

- `由乃你还记得我吗`
- `还记得我喜欢什么奶茶吗`
- `喜欢你所以就摸摸你 像小猫一样`
- backend timeout/retry recovery

This next step is manual observation only. It still does not allow PSPC adapter/runtime integration, long-term memory promotion, gate changes, transport/proactive changes, or claim-ceiling upgrade.
