# Claude Full Hostile Audit 001 ? PET P0 Scored Battery

One-line verdict: `HIGH_SCORE_NO_ATTRIBUTION`; positive mechanism claim `BLOCKED`.

Machine field caveat: `verdict=pet_integration_p0_pass` and `positive_claim_flag=true` are quoted only as banked gate-conjunction fields from `result.json`; they are not a mechanism-validity claim and must be read with this audit verdict.

## Blocking findings

- B1 observe oracle: `world.py:153` returns the full true current-regime `site_yields` for all 6 sites; `creature.py:166` overwrites the entire model from that map. Trace evidence: candidate uses exactly three observe actions per episode at ticks `[0,201,401]`, each carrying a six-site full-truth map.
- B2 schedule-derived trigger: `creature.py:66-75` computes `_derived_prediction_error_trigger` from true `drift_schedule` magnitudes in config, so the re-sense timing uses ground-truth drift knowledge.
- B3 no isolating control: the arm set has candidate / standin / random / static / frozen_updates / schedule_aware_reference, but no local or partial-observe arm and no recency/count/lookup baseline. The frozen-updates ablation disables both oracle-observe refresh and per-site updates, so attribution remains unfalsified.
- B4 card mechanism mismatch: `DERIVATION_NOTES.md` says the reachability argument ignores observe benefit and assumes experiential identification of changed best-site pairs; the implementation instead relies on oracle refresh as the primary recovery channel. The intended experiential mechanism was not tested.

## Defensible engineering-only ceiling

`pet_integration_engineering_only`: an end-to-end, default-off, offline desktop-pet P0 loop that is deterministic and fresh-process replay-valid, with an honestly labeled static user-facing gate, an online-update path that is load-bearing versus frozen updates, and resistance to one MINJA-class poison fixture. This is not a world-model result, not experiential drift-adaptation, and not a mechanism-validity result.

## Required controls before any future attribution claim

1. Add a local/partial-observe control arm where observe returns only the visited site yield, not the full map.
2. Add a trivial adaptive baseline such as recency/count go-to-best-recently-experienced-site, with no world model.
3. Replace the drift-schedule-derived observe trigger with a purely observed error threshold.
4. Remove `regime_id` from candidate-visible observation.
5. Pre-register the next comparison; any future attribution claim requires the candidate to still beat stand-in and the recency baseline under local-observe.

## What this record does not prove

No mechanism validity, no experiential adaptation, no consciousness, subjective experience, real emotion, agency, autonomy, functional selfhood, companion readiness, stable user benefit, or EGO-mainline readiness.
