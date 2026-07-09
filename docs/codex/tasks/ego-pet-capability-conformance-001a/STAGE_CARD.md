# Bounded Task Card — CAPABILITY-CONFORMANCE-PET-001A (v1 pilot: capability #1, feedback → subsequent behavior)


## task_id
`ego-pet-capability-conformance-001a` (pilot slice: `#1-feedback-to-behavior`)

## research_layer
Layer 2 — engineering implementation + capability-conformance verification. **NOT** mechanism-attribution, learning/generalization, subjectivity, or agency. Inherits the P0 audit ceiling (the pet's observe channel is an omniscient oracle snapshot, not experiential learning — see `ego-pet-integration-001a` P0 FULL hostile audit / HIGH_SCORE_NO_ATTRIBUTION).

## real_objective
Show, with discriminative + ablation + replay evidence, that the pet's **subsequent** action selection is **causally conditioned on the content of feedback it received at earlier ticks** — and disclose the exact channel by which it is. This is *functional conformance* ("capability behavior is present, load-bearing, and honestly attributed to a named channel"), explicitly **not** a claim that the pet *learns*, *adapts well*, or *understands*.

Do NOT reduce this to "behavior appears" (P0 lesson: appearance ≠ mechanism, and "adapts" was really oracle-observe). Every claimed effect must be (a) discriminative against a feedback-blind control, (b) directional (tracks the *content* of altered feedback, not just any perturbation), (c) ablation-sensitive, (d) replay-reproducible, (e) channel-disclosed.

## current_stage
Pre-implementation. Precondition met: Route-A #3/#1/#2 landed (HEAD `d9b89a1c`); repo-wide suite 0-failed in clean env (3 host failures were provider-env only); PSPC/pet/lab evidence surface clean.

## capability_statement (#1)
"Altering or withholding the feedback delivered to the pet at tick *t* changes the pet's action choices at ticks *t+1 … t+k* (with no further intervention in between), and the later choices track the *content* of the altered feedback."

## bounded formal object
- **S (state)**: `creature` substate — `model: {site: {energy, comfort}}`, `model_counts`, `last_prediction_error`, `last_observe_tick`, `updates_enabled`; plus `world` needs/tick.
- **O (observation)**: `{tick_index, regime_id, needs, viability, user_event}` (`world.build_observation`). Note: observation does **not** carry site yields; site knowledge reaches the policy only through `model`, which is fed by past feedback.
- **A (action)**: `observe` | `forage_energy@site` | `seek_comfort@site` (+ exploration).
- **M (memory / latent)**: `creature["model"]` — the persistence substrate; carries feedback across ticks until overwritten.
- **U (update)**: `creature.update_creature_after_feedback` (creature.py:153) — `observe` → `model = observed_site_yields` (oracle snapshot, C-observe); `forage/seek` → `model[site] = action_yield` (single-site real yield, C-forage); gated by `updates_enabled`.
- **J (what "capability present" means)**: intervention on feedback at *t* produces a divergence in the policy-preference / realized actions at *t+1…t+k* that (i) exceeds the feedback-blind control, (ii) is directional to the altered content, (iii) vanishes under ablation.
- **agent-controlled vs not**: agent controls action + (via feedback) `model`. Harness controls the injected feedback (intervention variable). World regimes / yields are not agent-controlled.

## hypothesis
H1: `candidate` (arm with `updates_enabled=True`) shows a directional, ablation-sensitive, replay-stable divergence in subsequent behavior under matched-pair feedback intervention; the feedback-blind control (`frozen_updates`) and needs-only `static` do not.

## channels (must be disclosed per divergence — G2)
- **C-observe**: `model` overwritten by full-truth `observed_site_yields` after an `observe` action (oracle snapshot; **not** learning — disclose as such).
- **C-forage**: `model[site]` overwritten by that site's true `action_yield` after a forage/seek (single-sample experiential write; still oracle-truthful for the visited site).
Trace must tag which channel produced each model change and therefore each downstream divergence. Report the split (how much of the capability rides on C-observe vs C-forage).

## baselines (CONTROL, not rival — per LEARNING-SUCCESS-CRITERION-STANDARD-001A)
Candidate must **separate from every control**; a task-specialist rival is irrelevant here.
1. `frozen_updates` (`updates_enabled=False`): feedback-blind. Under intervention → **no divergence** expected. Primary control.
2. `static` (needs-only `static_policy_action`): ignores `model`. Feedback-insensitive on the model channel → no divergence.
3. **directional control** (should-win/should-lose, S3): inject a *specific wrong regime's* yields as altered feedback; candidate's later `_best_site` must move **toward the injected regime's best site** at rate ≥ threshold — separates "conditioned on feedback content" from "perturbed by any change."
4. (optional) **random-feedback control**: replace feedback with random yields → expect incoherent change; candidate should track structured injection (#3) more than noise.

## ablation (S2 directional)
`updates_enabled=False` on the candidate → the intervention divergence must drop to ≈0. This is the "ablation destroys it" signature. (Reuses existing `frozen_updates` arm semantics; no frozen-code change.)

## G1 discriminative counterfactual (MANDATORY falsifier)
Matched-pair design sharing world + seed + history up to intervention tick *t*:
- **Pair A (real feedback)**: apply true feedback F at *t*; run forward to *t+k* with no further intervention.
- **Pair B (withheld)**: skip the model update at *t* (deliver null-effect feedback); run forward identically.
- **Pair C (altered/directional)**: replace F's `observed_site_yields`/`action_yield` with a different regime R′'s values; run forward.
- **Primary metric (deterministic, RNG-free)**: at each tick *t+1…t+k*, compare `_best_site(model, need)` (a deterministic function of model+needs) across pairs. Divergence here isolates the feedback→policy-preference effect with **no RNG confound**.
- **Secondary metric (realized action)**: compare sampled actions with RNG **held identical** across pairs; report and control for any RNG-draw desync (integrity check — do not count desync as capability).
- **FAIL (capability absent)**: Pair A ≡ Pair B in policy-preference at all *t+1…t+k* → feedback not load-bearing.
- **DOWNGRADE (perturbation-only)**: A≠B but C does not track R′'s best site → "feedback-perturbation-sensitive," weaker than "feedback-content-conditioned."

## trace / replay (reuse `battery.py` pattern; integrity S4)
Per-tick trace rows: `tick_index, needs, observation, action, feedback{action_yield, observed_site_yields}, model_before, model_after, channel∈{observe,forage,none}, best_site_energy, best_site_comfort, pair_id, intervention_tick`. Paired-run divergence records. Replay: fresh-process ×2, bit-exact. RNG only via `consume_registered_rng` (seeded); **no unseeded RNG** — grep the harness for `random./np.random/secrets/torch.rand` (per `itl-torch-unseeded-init-nondeterminism`; the AST rng_audit from P0 may be reused).

## acceptance_gate (pre-register all thresholds BEFORE running; no post-hoc tuning)
- G-A separation: candidate policy-preference divergence (A vs B) on ≥ **N** decisions across **M** seeds, while `frozen_updates` and `static` show 0 divergence. (Pre-register N, M, seed list, k-horizon, divergence metric.)
- G-B directional: under Pair C, candidate later best-site matches R′'s best site ≥ **p** of interventions.
- G-C ablation: candidate with `updates_enabled=False` → divergence ≈ 0 (≤ ε).
- G-D replay: fresh-process ×2 bit-exact on all pairs.
- G-E channel: 100% of divergences attributed to C-observe or C-forage in trace; report the split.
All five required. Thresholds pre-registered in the card addendum before STEP "run."

## predeclared_failure_geography (G3)
Capability MUST be **absent** under: `frozen_updates`, `static`, withheld feedback (Pair B), and horizon k=0 (same-tick only = no persistence claim). If divergence appears there → leak/bug → STOP. Capability MUST be **present** only for the update-enabled candidate under real/altered feedback with k≥1.

## claim_ceiling
Allowed (only): "Under `world_config_v0` + the pre-registered seeds, the pet's subsequent action selection is causally conditioned on the content of feedback it received at earlier ticks, via disclosed model-persistence channels (C-observe oracle snapshot and/or C-forage single-site real yield); the effect is discriminative vs feedback-blind/static controls, directional to altered feedback content, ablation-sensitive, and replay-reproducible."
Forbidden: learning, generalization, adaptation quality, understanding, prediction/world-modeling competence, self/agency/autonomy, subjective experience, companion/EGO readiness, or any claim that C-observe is experiential rather than oracle. No product/UI "learns/adapts" language.

## stop_conditions
- No separation from `frozen_updates` → report **CAPABILITY_ABSENT** (bounded negative; do not tune to force divergence).
- Separation but non-directional → **PERTURBATION_ONLY_NONDIRECTIONAL** (downgrade).
- If the only separating channel is C-observe AND k-persistence cannot be shown (model doesn't carry across ticks) → **INDISTINGUISHABLE_FROM_INSTANTANEOUS_OBSERVE** → STOP (P0 trap). (Code shows persistence, so not expected — still pre-registered.)
- Cost: run a 1-seed probe first; harness is pure-Python, no torch, deterministic → cost trivial, but honor probe-first discipline (`itl-cost-projection-precision-not-accuracy`).

## rollback_plan
New isolated files only. Rollback = delete `scripts/ego_pet_capability/`, its tests, and `artifacts/ego-pet-capability-conformance-001a/`. No EgoOperator/runtime rollback (none touched).

## expected_changed_files
- `scripts/ego_pet_capability/__init__.py`, `.../feedback_to_behavior.py` (protocol/evaluator; imports frozen `scripts.ego_pet.*` read-only), `.../trace.py`
- `scripts/ego_pet_capability/tests/test_feedback_to_behavior.py`
- `artifacts/ego-pet-capability-conformance-001a/` (result.json, trace.jsonl, baseline_comparison.json, ablation_report.json, replay_report.json, channel_report.json, claim_ceiling.txt; failure_manifest.json if anything fails)
- `docs/codex/tasks/ego-pet-capability-conformance-001a/` (this card + PREREG addendum with thresholds)

## forbidden_changes
`scripts/ego_pet/*` (P0 frozen — import read-only, do NOT edit), the 5 g_ablation modules, EgoOperator runtime, pet `suite_baseline.json`, `world_config_v0.json` / `static_gate_config` (frozen), any config/threshold in frozen modules. No LLM, no UI, no proactive, no runtime wiring, no new EgoOperator refs, no global schema change.

## evidence_contract
Machine-readable artifacts under `artifacts/ego-pet-capability-conformance-001a/`; natural-language summaries are not evidence. Preserve any failure artifacts (no patching failures into passes).

## anti_hardcoding_audit (before + after)
No if-else that fakes the divergence; no label/regime leakage through observation/filename/fixture names; thresholds pre-registered (not tuned to result); no test-only logic path; capability replayable from trace; not passing only because the intervention is weak (directional control #3 guards this).

## standards_cited
`MECHANISM-SIGNATURE-VERDICT-STANDARD-001A` (S1 control separation non-negotiable; G3 failure geography; verdict carries subtype + claim ceiling; capability-conformance verdict vocabulary: CAPABILITY_PRESENT_CHANNEL_DISCLOSED / PERTURBATION_ONLY / CAPABILITY_ABSENT); `LEARNING-SUCCESS-CRITERION-STANDARD-001A` (control-vs-rival: must beat controls; NOTE this card does **not** claim §2 flexible-learning — conformance only, scoped out explicitly); `BASELINE-IMMUNITY-ADMISSION-STANDARD-001A` (obs-decodability / saturation checks); `itl-torch-unseeded-init-nondeterminism` (RNG seeding for replay).

## claim ceiling (repeat, binding)
This card can at most produce bounded offline capability-conformance evidence for one pet capability under one world config. It cannot prove learning, mechanism, subjectivity, agency, autonomy, or readiness of anything.
