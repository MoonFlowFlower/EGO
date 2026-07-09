# PREREG_ADDENDUM_001 — ego-pet-capability-conformance-001a (capability #1, feedback → subsequent behavior)

> Ex-ante pre-registration. All thresholds, seeds, intervention geography, metric definitions, and the verdict rule below are **frozen at the commit that banks this file**. This commit MUST be an ancestor of any implementation and any gated run it judges (commit order = the un-backdatable ex-ante proof). Changing any frozen value requires a NEW pre-reg addendum that is itself an ancestor of the re-run. No post-hoc tuning.

## Frozen inputs
- World: `docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json` (read-only). Episode 600 ticks; regimes R0[0,199] / R1[200,399] / R2[400,599]; drift boundaries 200, 400; W=50; 6 sites {bowl, mat, sun_patch, perch, corner_bowl, blanket}.
- Prior note (built-in should-lose): `zero_creature_state` seeds `model` with R0 site_yields. So at the R0 initial observe, real feedback ≈ prior ⇒ withhold makes ~no difference. This is a **predicted should-lose** region, not a failure.
- Regime designated best sites: R0 energy=bowl/comfort=mat; R1 energy=sun_patch/comfort=perch; R2 energy=corner_bowl/comfort=blanket.

## Seeds (frozen; disjoint asserted)
- Dev probe: `1101` (from S_dev). Run first (probe-first discipline).
- Scored: `M = 20`, seeds `3101 … 3120` (fresh block; disjoint from S_dev 1101–1105 and S_scored 2101–2120; the harness must assert disjointness and fail closed otherwise).

## Arms
`candidate` (updates_enabled=True), controls: `frozen_updates` (updates_enabled=False), `static` (needs-only). `candidate_ablated` = candidate with updates_enabled forced False (= the ablation arm for G-C). All reuse frozen `scripts/ego_pet/*` unchanged.

## Intervention protocol (matched pairs; harness supplies feedback variants; frozen pet code unchanged)
Interventions are applied by the harness at the point it calls `update_creature_after_feedback` — by passing a modified `feedback` dict. Frozen code is never edited.

Observe-interventions (channel C-observe) at the candidate's:
- R0 initial observe (tick 0) — **should-lose** (prior≈truth).
- first post-drift observe in R1 (first observe at tick ≥ 200) — should-win.
- first post-drift observe in R2 (first observe at tick ≥ 400) — should-win.
Variants: **A** = true `observed_site_yields`; **B (withhold)** = `observed_site_yields=None` (skip model update); **C (directional)** = inject another regime's site_yields per frozen map {R0←R1, R1←R2, R2←R0}.

Forage-interventions (channel C-forage) at the candidate's first `forage_energy` and first `seek_comfort` in each regime:
- **A** = true `action_yield`; **B** = prior-value (no change); **C** = altered `action_yield` for the visited site set to a frozen value that makes a pre-registered site the argmax for that need.

## Persistence window
For each intervention at tick t: metric window = [t+1, min(t+50, next_natural_update_tick−1)] where next_natural_update_tick is the trace-detected next tick the relevant site's model entry would be overwritten (next observe, or next forage of that site). Report the realized window length per intervention. Horizon k≥1 required; k=0 (same-tick) is excluded from the capability claim.

## Metrics (deterministic primary; RNG-free)
Primary compares `_best_site(model, need)` per need over the persistence window (function of model+needs only — no RNG).
- **G-A withhold-separation** (post-drift observe-interventions R1+R2, averaged over interventions×seeds×needs): candidate rate[ best_site(A) ≠ best_site(B) ] ≥ **0.60**; `frozen_updates` and `static` rate == **0.00**; R0-initial candidate rate ≤ **0.05** (should-lose).
- **G-B directional** (Pair C, post-drift): candidate rate[ best_site(C) == injected-regime designated best site, per need, over window ] ≥ **0.80**; controls reported, expected ≤ **0.20** (chance for 6-site argmax).
- **G-C ablation**: `candidate_ablated` → G-A ≤ **0.02** AND G-B ≤ **0.25** (≈ chance).
- **G-D replay**: 2 fresh-process replays, **0** mismatches, on all pairs (RNG only via `consume_registered_rng`; no unseeded RNG).
- **G-E channel**: **100%** of nonzero divergences attributed to C-observe or C-forage in trace; report the observe/forage split.

## Verdict rule (frozen)
- `CAPABILITY_PRESENT_CHANNEL_DISCLOSED` iff G-A ∧ G-B ∧ G-C ∧ G-D ∧ G-E all pass.
- `PERTURBATION_ONLY_NONDIRECTIONAL` iff G-A passes, G-B fails (behavior changes but does not track content).
- `CAPABILITY_ABSENT` iff G-A fails (no separation from feedback-blind control).
- `INSTRUMENT_INVALID` iff G-D fails, or G-E incomplete, or R0-should-lose candidate rate > 0.05 (leak), or any control shows nonzero G-A (control contamination), or seed-disjointness assertion fails.

## Failure geography (G3, predeclared)
Capability MUST be absent (rate 0 / chance) under: `frozen_updates`, `static`, `candidate_ablated`, Pair B, R0-initial observe, k=0. Presence only for `candidate` under A-vs-B / Pair-C at post-drift, k≥1. Any presence in the should-lose set ⇒ INSTRUMENT_INVALID.

## Claim ceiling
Bounded offline capability-conformance evidence for ONE capability under ONE world config + these seeds. Proves feedback is load-bearing + directional + ablation-sensitive + replay-valid + channel-disclosed. Does NOT prove learning, generalization, adaptation quality, understanding, world-modeling competence, self/agency/autonomy, subjectivity, or readiness. The C-observe channel is an oracle snapshot, disclosed as such — not experiential learning.

## Standards
Cites MECHANISM-SIGNATURE-VERDICT-STANDARD-001A (S1 control separation non-negotiable; G3 failure geography; verdict subtype + claim ceiling in result.json), LEARNING-SUCCESS-CRITERION-STANDARD-001A (control-vs-rival: beat controls; this card does NOT claim §2 flexible learning — conformance only), itl-torch-unseeded-init-nondeterminism (RNG seeding for replay).
