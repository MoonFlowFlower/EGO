# Task: MVP-6.2.1 (Step-by-step)

**GOAL:** Implement `/home/moonlight/Desktop/OpenEmotion/MVP-6.2.1.txt` with minimal changes (3 points), delivering one step at a time.

## DoD (Definition of Done)
- [x] Step 1: Bond differentiation made more visible in 10~30 turns
- [ ] Step 2: Ledger diff gating (not_applicable when no ledger events)
- [ ] Step 3: Residual-conditioned gain promoted to production-tunable path
- [ ] Re-run eval suite and capture before/after evidence

## Status
- **Phase:** step-1-done
- **Last Update:** 2026-03-01 20:17:00
- **Blockers:** None

## Next Action
**next_action:** Implement Step 2 (ledger diff gating), then run focused eval for cross_target_isolation + promise_betrayal.

## Evidence
- Target doc: `/home/moonlight/Desktop/OpenEmotion/MVP-6.2.1.txt`
- Edited file: `emotiond/core.py` (event-sensitive + target-conditioned bond gains)
- Focused eval: `reports/mvp621_step1_focused_eval.json`
- Key observed movement: `multi_target_isolation` bond_diff `0.7935` (pass)

## Notes
Step 1 scope retained in `emotiond/core.py`:
- event-sensitive bond gain knobs
- target-conditioned `target_gain` scaling
- world_event target resolution uses explicit `event.target` when present
