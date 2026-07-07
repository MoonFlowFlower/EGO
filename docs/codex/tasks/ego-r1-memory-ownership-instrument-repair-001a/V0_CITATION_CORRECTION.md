# V0 Citation Correction — ego-r1-memory-ownership-001a battery (banked cb94184)

Version probe: R1-INSTRUMENT-REPAIR-001A rev-A 2026-07-07.
Status: FROZEN CITATION PIN. This file corrects how the banked v0 run may be
cited. It does NOT modify, reinterpret-upward, or replace any banked artifact;
`artifacts/ego_r1_memory_ownership_001a/**` remains byte-frozen evidence.

## Binding citation rules for the v0 run

1. The v0 verdict label `instrument_invalid_potency` is a priority-order
   single label (`run_ego_r1_memory_validation.py:233`, first failing gate
   wins). Correct citation reads the full gate table:
   POTENCY fail + CONTAINMENT fail + ABLATION fail;
   QUARANTINE / DRIFT-PAYOFF / BASELINE-HONESTY / REPLAY / LLMSWAP /
   MIMICRY pass.
2. The v0 run is INSTRUMENT-INVALID (three independent instrument defects:
   potency measurement window; containment attribution rule narrower than the
   card's own wording; benign-value leg not instantiated, base uplift −0.0267).
   It is NOT mechanism-negative. The R1 candidate's core claim
   (ownership value under contamination) is UNADJUDICATED by v0.
   Do not cite v0 as "R1 failed" or as evidence against memory ownership.
3. The v0 ship-decision string `learned_component_kept_for_drift_segment_only`
   (present in result.json) is RETRACTED as unsupported: the ablation shows
   pref_zeroed == base exactly (learned EMA causally inert for drift payoff
   in the v0 env) and promotion_frozen_uplift (0.0) > base_benign_uplift
   (−0.0267). No "learned component kept" decision may cite v0.
4. Real v0 findings that MAY be cited (at engineering ceiling, v0-env-bounded):
   - F1: the pref/EMA channel contributed nothing measurable to drift payoff
     in the v0 env (exact ablation equality).
   - F2: drift payoff was baseline-equivalent to raw_rag (mean_delta
     1.85e-17) and graph_cache (−0.013): equivalent_engineering_value; the
     payoff channel was carried by promoted-memory/cache retrieval.
   - F3: the structural write boundary behaved as designed (candidate direct
     external owned writes = 0; permissive negative control fired 546;
     replay ×2 + resume clean; llmswap clean; mimicry certified at
     content-mimetic tier). Anti-contamination VALUE remains unproven
     (potency instrument invalid).
5. seed_31_episode_1's 3 unattributed mismatches are an open attribution
   question pending PHASE R-DIAG of the repair card; they may not be cited as
   a containment breach nor as containment success.

## Claim ceiling

`memory_ownership_engineering_only`. This correction adds no new claim; it
narrows misuse. Nothing here proves mechanism validity, structure-necessity,
agency, autonomy, subjectivity, consciousness, readiness, or user benefit.
