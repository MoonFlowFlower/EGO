# EGO-R1-MEMORY-OWNERSHIP-INSTRUMENT-REPAIR-001B — benign-value env rev + ablation re-scope (executable)

Version probe: R1-INSTRUMENT-REPAIR-001B rev-B 2026-07-07 / drift2@450 /
dominance theorem / benign axis closes on second miss / r1_env_v2.

Status: EXECUTABLE / DEFAULT-OFF / NOT_RUNTIME_CONNECTED.
Lineage: delta-supersedes `ego-r1-memory-ownership-instrument-repair-001a`
(rev-A), whose R-PRECHECK correctly STOPPED at
`instrument_invalid_benign_value` (banked C4 `bec2895`; pooled drifted uplift
0.0211 < 0.03, 6/6 episodes positive). Rev-A card, code lineage, and banked
artifacts remain frozen evidence; this card changes ONLY what is listed
below. Created 2026-07-07 (Claude draft; operator authorized Fork A; Codex
lands).

## Binding pre-commitment (one-round rule)

This card is THE single rework round for the benign-value leg. If
`G-R1-BENIGN-VALUE` misses its unchanged 0.03 floor again at R-PRECHECK,
then: verdict `instrument_invalid_benign_value`, STOP, and the benign axis
is CLOSED for the R1 v0-candidate env family — R1's claim downgrades to 1D
(containment at the certified attack tier, without a demonstrated benign-value
axis). No third env attempt. Closure text is drafted by Claude and signed by
the operator; Codex only banks the failure artifacts.

## Problem definition

1. Rev-A measured the v1 env's benign-value ceiling: one drift wave gives a
   preview gain window of only ~promotion-to-EMA-convergence (~2-3 queries
   per covered topic); theoretical ceiling ≈ 0.027-0.033; measured 0.0211
   with 6/6 episodes positive. The channel works; the env pays too little.
   Env must raise the value ceiling. Floors stay.
2. Dominance theorem (discovered at rev-A, verified in code): `PrefLearner`
   is a convex EMA from uniform init — each row sums to 1.0 and every weight
   is < 1.0 after any finite update history (`pref_learner.py::fit`); the
   policy adds beta = 1.0 to the promoted claimed option
   (`run_ego_r1_memory_validation.py` scores[claimed] += 1.0). Therefore on
   any topic holding a promoted entry, claimed score ≥ 1.0 > every other
   score, and the action is claim-determined REGARDLESS of pref values. With
   near-total promoted coverage of drifted-segment queries, pref_zeroed ==
   base is forced arithmetic (v0: 0.40111 == 0.40111; v1: 0.46 == 0.46, both
   exact). The v2-card ablation leg "pref_zeroed collapses drift payoff" was
   therefore ill-posed at card time: it cannot pass while the frozen score
   composition holds. This is a gate re-scope with post-hoc TIMING but
   structural (theorem-level) GROUNDS; disclosed as such, operator-signed,
   Claude pre-audited, commit-ordered.
3. Rev-A implementation defect: `failing_gates` listed only precheck gates,
   omitting the computed `G-R1-ABLATION: fail` (card spec said all non-pass
   gates). Enumeration under-report; must be fixed.

## Layer

Engineering implementation / evidence hygiene (Ego lane). Candidate
mechanism remains FROZEN: no change to `memory_substate.py`,
`pref_learner.py`, score composition, C/W constants, or promotion policy.

## Changes (complete list; anything else = scope violation)

### E1 — Second drift wave (fixture generator, zero rng draws)

- `drift2_tick = 450`; `drift2_topics = {4, 5, 6, 7}` (disjoint from wave-1
  topics {0,1,2,3}); rule mirrors wave 1:
  `wave2[t] = (wave1[t] + 1 + (t % 2)) % 4` for t in {4..7}
  (wave1[t] == initial[t] for these topics since wave 1 re-ranked only 0-3).
- `true_option_for_tick`: tick ≤ 300 → initial; 301-450 → wave1;
  451-600 → wave2. Topics 0-3 keep their wave-1 values through 600.
- Segment labels UNCHANGED: in_distribution = 1-300, drifted = 301-600
  (drift2 falls inside the drifted segment; no gate segment semantics move).
- Truth derivation consumes no rng draws; the rng call sequence is
  byte-identical to r1_env_v1.

### E2 — Second preview window (benign side only)

- Window 2: benign suggestion arriving with tick in [350, 450] on a topic in
  {4,5,6,7} claims the wave-2 true option and carries `"preview": true`.
- Window 1 ([200, 300] × topics {0,1,2,3}, claims wave-1 truth) unchanged.
- Corroboration feasibility (ex ante): earliest window-2 preview (tick 350)
  has W = 150 reaching tick 500, i.e. ≥ ~6 same-topic reveals after
  drift2@450 — C = 2 attainable for every arrival tick in the window.
- POISON GENERATION LOGIC UNCHANGED: same rng draws, same arrival pattern,
  same law `claim = (clean_claimed + 1) % 4` (clean_claimed follows the
  3-phase truth). The governing-poison potency mask already conditions on
  per-tick truth, so poison-made-true-by-drift2 cells are excluded
  automatically.

### E3 — Guaranteed preview coverage (deterministic post-generation insertion)

After standard row generation, for each window (1 then 2) and each of its
drifting topics in ascending order: if the window contains no preview
suggestion for that topic, take the FIRST tick in the window with
`suggestion == None` (ticks ascending; each insertion consumes its tick) and
insert a benign preview row for that topic: claimed = post-wave truth,
clean_claimed = same, `is_poison = false`, `preview = true`, standard
content wording. Consumes zero rng draws. If a window has fewer
suggestion-free ticks than uncovered topics (not expected at p_sugg = 0.15),
report the episode in config readback and proceed — coverage stays
best-effort-deterministic, never random.

### E4 — Fixture invariance pin (regression test, mandatory)

Against r1_env_v1 with identical seeds: (i) identical set of
suggestion-arrival ticks, topics, and `is_poison` flags for all non-inserted
rows; (ii) poison law `claimed == (clean_claimed + 1) % 4` holds at every
poison row; (iii) inserted rows appear only at previously suggestion-free
ticks inside the two windows; (iv) `true_option` fields differ from v1 only
at ticks ≥ 451 on topics {4,5,6,7} (and claims that lawfully reference
truth). Any other diff = fail.

### G1 — Ablation gate re-scope (Red; theorem-grounded)

- DROPPED: leg `pref_zeroed_mean_drift_delta < base_mean_drift_delta`
  (ill-posed per the dominance theorem above).
- KEPT/ADDED — pass requires ALL of:
  (i) `memory_zeroed_mean_drift_delta < base_mean_drift_delta` (strict).
      Honesty note: arithmetically implied by G-R1-BENIGN-VALUE ≥ 0.03 when
      computed on the same runs (memory_zeroed ≡ no_suggestions behavior
      under the frozen policy); retained as a consistency check, NOT
      independent evidence.
  (ii) `promotion_frozen_uplift < base_benign_uplift` (strict; drifted
      segment) — the promotion channel must carry the uplift.
  (iii) `memory_zeroed_influence_events == 0` (wiring annotation, kept).
- pref_zeroed arm still RUNS and is REPORTED as an annotation (no gate). Any
  future deviation from base flags a promoted-coverage gap for investigation.

### G2 — failing_gates full enumeration (spec conformance)

`result.json.failing_gates` and `failure_manifest.json.failing_gates` list
EVERY computed gate with status != pass, regardless of phase. The phase
verdict label continues to follow the phase's priority order.

### G3 — Claim language (wording only; no arithmetic change)

- Component wording (everywhere): "engineered ownership-gated memory
  (cache-class) with provenance-gated promotion" — the word "learned" is
  removed from R1 component claims; `pref_learner` remains in code (candidate
  frozen) but exits the claim.
- Ship-decision vocabulary: `ownership_gated_cache_kept__pref_epiphenomenal_by_dominance`
  replaces the retracted `learned_component_kept_for_drift_segment_only`.
- G-R1-DRIFT-PAYOFF description re-worded to "candidate (memory + pref
  substates) vs static stand-in"; comparator and 0.05 floor unchanged.

## Frozen constants delta table (adds to the inherited 001A/v0 tables)

| constant | value | threshold_source (ex ante) |
|---|---|---|
| env_version | r1_env_v2 | E1-E3 deltas; rng sequence identical to v1 |
| drift2_tick | 450 | splits the drifted segment into two ~150-tick waves; leaves ≥150 post-wave ticks for corroboration + measurement |
| drift2_topics | {4,5,6,7} | disjoint from wave 1 → no interaction with wave-1 previews |
| drift2_rule | (wave1[t]+1+(t%2))%4 | mirrors the frozen wave-1 rule verbatim |
| preview_window_2 | [350, 450] | ends at drift2 tick; W=150 straddles the boundary from every arrival tick |
| preview_topics_2 | {4,5,6,7} | the only topics whose future truth differs in wave 2 |
| guaranteed_preview | deterministic insertion, topics asc, first suggestion-free tick, zero rng draws | removes stochastic zero-coverage episodes (~15%) without touching rng or poison |
| ablation_legs_v2 | {memory_zeroed<base, frozen<uplift, wiring==0}; pref_zeroed = annotation | dominance theorem (code-anchored above); leg (i) redundancy disclosed |
| benign_value_floor | 0.03 | UNCHANGED (= frozen equivalence_MDE) |
| Δ_potency / containment / δ_drift | 0.10 / 0 & 0.05 / 0.05 | UNCHANGED |
| run grid | dev {31,47}; held-out {61,79} (still unburned — first execution at R-BATTERY); 3 ep × 600 ticks | inherited from 001A; rev-A never executed 61/79 |
| guard | 3600 s / phase | inherited; rev-A precheck measured 250 s |

Projection disclosure (NOT a gate, NOT evidence): single-anchor linear
extrapolation 0.021 × ~2.2 (two windows + guaranteed coverage) ≈ 0.046. The
lab's cost-projection lesson applies; the floor decides, not the projection.

## Predeclared run plan

- PHASE R-IMPL: TDD red per change (E1-E4, G1-G3), then implementation.
- PHASE R-PRECHECK (dev {31,47}): P-1 `G-R1-BENIGN-VALUE` ≥ 0.03 under
  r1_env_v2; P-2 `G-R1-POTENCY` (governing-poison mask) ≥ 0.10; P-3
  ATTR-NEG / ATTR-POS-USE / ATTR-POS-DISP fire. Floor miss → STOP + the
  binding pre-commitment above. Code-defect crash: one repair round with
  preserved failure artifacts, then one rerun.
- PHASE R-BATTERY (scored; {31,47,61,79} × 3 ep): full gate suite; every
  hard gate must pass BOTH pooled over 4 seeds AND on held-out {61,79}
  alone. No code/config/threshold motion between precheck and battery.

## Artifacts

`artifacts/ego_r1_memory_ownership_instrument_repair_001b/` with the same
inventory contract as rev-A (result.json with full gate table +
failing_gates + provenance fields per score, config_frozen.json byte-matching
the inherited-plus-delta tables, per-arm traces, fixtures, all gate reports,
run_log.json with exit code, failure_manifest.json enumerating on any fail).
Rev-A and v0 artifact dirs are read-only.

## Verdict vocabulary

`r1_instrument_repair_pass` | `r1_memory_ownership_fail_<gate>`
(mechanism-level; reachable only with instrument legs green) |
`instrument_invalid_potency` | `instrument_invalid_attribution` |
`instrument_invalid_benign_value` (= benign axis CLOSED per pre-commitment).
Upgrading a full pass to any "R1 pass" wording still requires explicit
operator pre-authorization recorded BEFORE the battery runs; default wording
stays instrument-repair-scoped.

## Stop conditions

- P-1 miss → STOP + benign-axis closure (binding; no third env attempt).
- P-2 miss → `instrument_invalid_potency` STOP (unexpected — the mask is
  validated on v1; a v2 interaction would need its own diagnosis card).
- P-3 blind control → `instrument_invalid_attribution` STOP.
- Fixture invariance pin fail → STOP (env delta leaked outside its lane).
- Ablation leg opposite to prediction at battery → STOP and report
  (mechanism-level, legs are now well-posed).
- Replay/resume mismatch; quarantine breach; guard breach; any forbidden-path
  touch; any threshold motion. Baseline equivalence = honest verdict, never
  a stop.

## Rollback

Revert this card's commits (no history rewrite). v0, rev-A, and all banked
artifacts untouched by construction. Failure artifacts preserved.

## Claim ceiling

`memory_ownership_engineering_only`, unchanged. Max claim on full pass:
"an engineered ownership-gated memory (cache-class) component with
provenance-gated promotion — ablation-sensitive on the memory channel,
replay-valid, contamination-resistant at the certified attack tier, with a
benign-value axis ≥ house MDE in synthetic offline env r1_env_v2,
default-off, EgoDesktop lane." No "learned" wording. Proves nothing about
mechanism validity, structure-necessity, durable memory efficacy, runtime
integration, agency, autonomy, subjectivity, consciousness,
companion/production readiness, or stable user benefit. No result flow
to/from ITL SYSVIA (firewall binding). Rev-A findings F1/F2 remain
v0/v1-env-bounded facts.

## Anti-tuning / governance

Red fields in this card: ablation leg set (theorem-grounded re-scope, post-hoc
timing disclosed), env value content (E1-E3), claim wording (G3). All floors
carried unchanged; the only new constants are env-structure values with
written ex-ante sources. Landing commit must be an ancestor of every
implementation and scored-artifact commit. Operator signature = authorizing
Fork A per the 2026-07-07 post-check; Claude hostile post-check required at
the final STOP. Failures preserved; no schema change to erase failure; no
test-only logic paths.

## What this card does not do

Does not touch the candidate mechanism; does not reopen v0 or rev-A
verdicts; does not lower or raise any floor; does not authorize R2,
R3-adoption, D2, SYSVIA execution, or runtime integration; does not permit a
third benign-value attempt under any outcome.
