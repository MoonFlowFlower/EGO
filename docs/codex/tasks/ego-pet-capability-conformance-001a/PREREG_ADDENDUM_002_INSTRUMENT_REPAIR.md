# PREREG_ADDENDUM_002 — ego-pet-capability-conformance-001a — directional-instrument repair (r2)

> Ex-ante pre-registration of a REPAIRED directional instrument for capability #1, after `PREREG_ADDENDUM_001` produced `INSTRUMENT_INVALID` (G-C fail; the directional-injection map had a degenerate leg). All thresholds, seeds, the injection map, the metric definitions, and the verdict rule below are **frozen at the commit that banks this file**. This commit MUST be an ancestor of the repaired harness and of any gated re-run it judges (commit order = the un-backdatable ex-ante proof). Changing any frozen value requires a NEW addendum that is itself an ancestor of the re-run. **No post-hoc tuning.**
>
> **This addendum does NOT edit or reinterpret `PREREG_ADDENDUM_001` or the banked `INSTRUMENT_INVALID` bundle.** Those remain the historical negative record (no-delete, no-rewrite). This is a new instrument, scored on fresh disjoint seeds, writing to a new artifact subdirectory.

## 1. What failed in 001 and why (defect statement, from the banked evidence)
The 001 directional gate (G-B) used an **absolute match rate** — `rate[ best_site(C) == injected-regime designated best site ]` — with control expectation ≤0.20 and ablation threshold (G-C) ≤0.25. The injection map `{R0←R1, R1←R2, R2←R1... }` actually banked as `{R0←R1, R1←R2, R2←R0}` contained a **degenerate leg `R2←R0`: it injects R0's site_yields, whose designated best sites (energy=bowl, comfort=mat) equal the R0 prior that seeds every creature.** Every feedback-blind arm (`frozen_updates`, `static`, `candidate_ablated`) keeps `model` at that prior, so it matches the R2-leg target 100% by coincidence and the R1-leg target 0% → a hard **0.50 structural chance floor** (banked: all three feedback-blind arms = 2000/4000; per-leg R1=0/2000, R2=2000/2000). 0.50 exceeds the 0.20/0.25 thresholds → G-C correctly failed → `INSTRUMENT_INVALID`. The ablation control did its job. The withhold gate (G-A) and the R1 leg of the directional gate were clean and discriminative (candidate ≫ controls), so a genuine feedback-conditioning signal is present; only the directional instrument, as specified, could not certify directionality.

## 2. Two independent repairs (belt-and-suspenders; either alone removes the false floor, both give a robust, well-powered instrument)

### 2a. Injection map de-degeneracy (config-derived + asserted, fail-closed)
For every SCORED (post-drift) Pair-C intervention, the injected regime's designated best site must differ, **for each need**, from BOTH:
- (a) the feedback-blind / R0-prior best site, AND
- (b) the true current-regime best site.

The harness derives designations from `world_config_v0.json` via `_best_site` (as in 001) and **asserts (a)∧(b) for every scored leg before running; fail-closed → `INSTRUMENT_INVALID` if any scored leg is degenerate.** Verified (config-derived): the UNIQUE post-drift map satisfying this for the 3 regimes is:

```
frozen injection map (scored, post-drift):  { R1 <- R2 ,  R2 <- R1 }
```

(At R1, injecting R2 → target {corner_bowl, blanket} ≠ prior {bowl, mat} and ≠ R1-true {sun_patch, perch}. At R2, injecting R1 → target {sun_patch, perch} ≠ prior {bowl, mat} and ≠ R2-true {corner_bowl, blanket}. Injecting R0 is degenerate at both and is FORBIDDEN.) R0-initial observe remains **should-lose** (excluded from directional scoring). Matching the injected (not the true) regime's designation continues to prove content-tracking rather than a `regime_id` leak.

### 2b. Directional metric = discriminative delta, scored per leg (not an absolute rate, not an aggregate)
Primary directional score, per scored leg L ∈ {R1←R2, R2←R1}, per need:
```
D_dir(arm, L) = rate_match(arm, L) − rate_match(frozen_updates, L)
```
where `rate_match` = fraction of the persistence window where `best_site(model, need) == injected designation`, and `frozen_updates` is the feedback-blind reference floor. The delta cancels ANY residual coincidence between the injected target and the feedback-blind floor by construction. Report per-leg and aggregate, per need and pooled, plus the raw rates for both candidate and the floor.

## 3. Frozen inputs (unchanged from 001 except seeds + map + metric + verdict)
- World: `docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json` (read-only). 600 ticks; R0[0,199]/R1[200,399]/R2[400,599]; drift 200,400; 6 sites; designations R0 bowl/mat, R1 sun_patch/perch, R2 corner_bowl/blanket (harness derives + asserts).
- Prior: `zero_creature_state` seeds `model` with R0 yields (feedback-blind floor = R0 designation).
- Arms: `candidate` (updates_enabled=True), `frozen_updates` (False, = floor reference), `static` (needs-only), `candidate_ablated` (candidate forced updates_enabled=False, = ablation arm). All reuse frozen `scripts/ego_pet/*` unchanged; interventions applied only by passing modified `feedback` dicts.

## 4. Seeds (fresh, disjoint; assert fail-closed)
- Dev probe: `1106` (fresh; run first, probe-first discipline).
- Scored: `M = 20`, seeds `4101 … 4120` (fresh block; **assert disjoint from all prior: S_dev 1101–1105, S_scored 2101–2120, and the 001 scored block 3101–3120**; fail closed otherwise).

## 5. Intervention protocol (matched pairs; harness supplies feedback variants; frozen pet code unchanged)
Observe-interventions (channel C-observe), variants at the candidate's first post-drift observe in R1 (tick≥200) and R2 (tick≥400):
- **A** = true `observed_site_yields`; **B (withhold)** = `observed_site_yields=None` (skip model update); **C (directional)** = inject the mapped regime's site_yields per the frozen map §2a `{R1←R2, R2←R1}`.
- R0-initial observe (tick 0) is included ONLY as the should-lose control (A-vs-B), never in directional scoring.

Forage-interventions (channel C-forage) remain **diagnostic** (reported as deltas for transparency, not gate-scoring) unless a future addendum promotes them; the same de-degeneracy + delta rules apply if promoted.

Persistence window per intervention at tick t: `[t+1, min(t+50, next_natural_update_tick−1)]` (trace-detected). k≥1 required; k=0 excluded.

## 6. Metrics (deterministic primary; RNG-free) and thresholds (frozen; inherited from the sound 001 G-A family — NOT derived from the 001 G-B magnitudes)
Primary uses `_best_site(model, need)` over the window (deterministic; no RNG).
- **G-A withhold-separation** (post-drift observe, candidate): `rate[best_site(A) ≠ best_site(B)] ≥ 0.60`; `frozen_updates`, `static`, `candidate_ablated` == `0.00`; R0-initial candidate ≤ `0.05` (should-lose). *(unchanged; 001 G-A passed cleanly.)*
- **G-B directional-delta** (post-drift, **per leg**): candidate `D_dir(candidate, L) ≥ 0.60` for **each** scored leg L (both R1←R2 and R2←R1); feedback-blind floor raw rate `rate_match(frozen_updates, L) ≤ 0.05` for each leg; `static` and `candidate_ablated` raw `≤ 0.05` each leg. *(Per-leg gating directly prevents a degenerate leg being hidden by aggregation — the 001 failure mode.)*
- **G-C ablation (delta form)**: `D_dir(candidate_ablated, L) ≤ 0.05` for each leg AND G-A(candidate_ablated) ≤ `0.02`. *(Delta form cannot be tripped by a structural floor, because the floor cancels.)*
- **G-D replay**: 2 fresh-process replays, **0** mismatches, all pairs (RNG only via `consume_registered_rng`; no unseeded RNG; fail-able positive-control RNG audit retained).
- **G-E channel**: **100%** of nonzero divergence/directional records attributed to C-observe or C-forage; report the split.

Threshold rationale (ex-ante): 0.60 = "a majority of interventions show a discriminative signal"; 0.05 = "near-zero feedback-blind floor / ablation collapse" (allows tiny slack for exploration-ε and window edges). These are the SAME family used by the 001 G-A gate, which was never the defect. They are NOT read off the 001 G-B numbers. The direction of change vs 001 (0.20→0.05 floor, 0.25→0.05 ablation) is a **tightening** (harder to pass), which cannot be post-hoc tuning to force a pass.

## 7. Verdict rule (frozen — closes the 001 "G-C fail" gap)
Evaluate on the delta family above.
- `CAPABILITY_PRESENT_CHANNEL_DISCLOSED` iff G-A ∧ G-B (both legs) ∧ G-C ∧ G-D ∧ G-E all pass.
- `PERTURBATION_ONLY_NONDIRECTIONAL` iff G-A passes but G-B fails on ≥1 leg (behavior changes but does not track injected content on some leg).
- `CAPABILITY_ABSENT` iff G-A fails.
- `INSTRUMENT_INVALID` iff **any of**: the §2a de-degeneracy assertion fails on a scored leg; G-C fails (ablation does not collapse the directional delta, i.e., `D_dir(candidate_ablated, L) > 0.05` on any leg); G-D fails; G-E incomplete; R0-should-lose candidate rate > 0.05 (leak); any control shows nonzero G-A; or seed-disjointness assertion fails. *(G-C fail now maps explicitly to INSTRUMENT_INVALID — the 001 gap is closed.)*

## 8. Predeclared failure geography (G3)
Directional signal MUST be absent (delta ≈ 0 / raw ≤ 0.05) under: `frozen_updates`, `static`, `candidate_ablated`, and any degenerate leg (which cannot occur under the asserted map). Present only for `candidate` under Pair-C at post-drift, both legs, k≥1. Any directional presence in the feedback-blind set, OR ablation not collapsing the delta, ⇒ INSTRUMENT_INVALID (not a downgrade-to-pass).

## 9. Artifacts + preservation
New artifacts under `artifacts/ego-pet-capability-conformance-001a/repair_001/` (result.json with verdict_subtype + signature_manifest + per-leg delta table + claim_ceiling; trace.jsonl gate-scoped; baseline_comparison.json; ablation_report.json; replay_report.json; channel_report.json; failure_manifest.json if any fail). **The 001 bundle at `artifacts/ego-pet-capability-conformance-001a/*.json` is preserved unchanged.**

## 10. Claim ceiling (unchanged, binding)
Bounded offline capability-conformance evidence for ONE capability under ONE world config + these seeds. Proves (only, if it passes) feedback is load-bearing + directional + ablation-sensitive + replay-valid + channel-disclosed. Proves NO learning, generalization, adaptation quality, understanding, world-modeling, self/agency/autonomy, subjectivity, emotion, consciousness, or EGO/companion readiness. C-observe is an oracle snapshot, disclosed as such — not experiential learning.
