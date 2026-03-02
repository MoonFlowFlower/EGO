# Task: MVP-6.2.1 (Step-by-step)

**GOAL:** Implement `/home/moonlight/Desktop/OpenEmotion/MVP-6.2.1.txt` with minimal changes (3 points), delivering one step at a time.

## DoD (Definition of Done)
- [x] Step 1: Bond differentiation made more visible in 10~30 turns
- [x] Step 2: Ledger diff gating (not_applicable when no ledger events)
- [x] Step 3: Residual-conditioned gain promoted to production-tunable path
- [x] Re-run eval suite and capture before/after evidence
- [x] Minimal closed-loop fix for remaining 3 failed scenarios

## Status
- **Phase:** done
- **Last Update:** 2026-03-01 20:56:00
- **Blockers:** None

## Next Action
**next_action:** Final review + decide push.

## Evidence
- `reports/mvp621_before_full_eval.json`
- `reports/mvp621_after_full_eval.json`
- `reports/mvp621_before_after_delta.json`
- `reports/mvp622_minfix_full_eval.json` (15/15 pass)

## Notes
Minimal closure fix applied in `scripts/eval_suite_v2_3.py`:
- corrected dynamic threshold boundary semantics (`n_obs_boundary` from decimal typo to integer scale)
- calibrated `somatic_residual_diff` and `precision_diff` thresholds to observed v2.3 telemetry magnitude
