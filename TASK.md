# Task: MVP-6.2.1 (Step-by-step)

**GOAL:** Implement `/home/moonlight/Desktop/OpenEmotion/MVP-6.2.1.txt` with minimal changes (3 points), delivering one step at a time.

## DoD (Definition of Done)
- [x] Step 1: Bond differentiation made more visible in 10~30 turns
- [x] Step 2: Ledger diff gating (not_applicable when no ledger events)
- [ ] Step 3: Residual-conditioned gain promoted to production-tunable path
- [ ] Re-run eval suite and capture before/after evidence

## Status
- **Phase:** step-2-done
- **Last Update:** 2026-03-01 20:27:00
- **Blockers:** None

## Next Action
**next_action:** Implement Step 3 in production path, then run focused eval pack and compare before/after.

## Evidence
- Step2 eval pack: `reports/mvp621_step2_eval_pack.json`
- Ledger status examples:
  - `relationship_building`: `ledger_diff_status=not_applicable`, `event_count=0`
  - `promise_betrayal`: `ledger_diff_status=not_applicable`, `event_count=0`
  - `cross_target_isolation`: `ledger_diff_status=applicable`, `event_count=1`

## Notes
Step 2 implemented in `scripts/eval_suite_v2_3.py`:
- Single-target applicability gate for individualization diffs
- Explicit `ledger_diff_status` field (`applicable` | `not_applicable`)
