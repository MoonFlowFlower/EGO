# STAGE CARD — EGO-R2-CONTROLLED-INITIATIVE-001A

task_id: ego-r2-controlled-initiative-001a
lane: R2 (decision card sequence, science flagship; design source = decision card §R2 — in-card restatement declared operative; the tracked docs/Joi-like_bounded_mechanism_proxy_roadmap_v1.md is the presumed citation referent, non-normative, identity unverified)
status_at_landing: LANDED_FROZEN — execution phases gated per §11
layer: engineering implementation + mechanism hypothesis (offline simulator only)
drafted_by: Claude (2026-07-07, operator-authorized R2 opening); landing_by: Codex (landing-only)

## 0. Problem definition

Test whether a learning-based gated-initiative controller (decides act vs
silent under uncertainty about user receptivity, with asymmetric
false-positive cost) yields net utility that a frozen family of non-learning
controls cannot match, in a fully offline user simulator with judge-side
ground truth o_t. Pre-committed kill: parity with a tuned single threshold or
with the behavior tree closes route I; the behavior tree becomes the product
solution; retune/rescue forbidden.

Hypothesis H-R2: cross-tick belief integration plus within-episode adaptation
(phase inference from noisy schedule carrier + feedback fusion) captures
receptive windows that stateless/static policies systematically mistime, by
margin >= delta with CI separation, and the advantage is attributable
(ablation destroys >= half the gain; interventions change trajectories).

Null / expected-failure mode: behavior tree with reject-triggered backoff ties
the candidate -> route_i_closed_baseline_equivalence (honorable close).

## 1. Environment spec — r2_sim_v0 (frozen)

Discrete episode, T=500 ticks. One simulated user per episode; user params
derived deterministically from episode seed.

Latent receptivity s_t in [0,1] (JUDGE-SIDE ONLY, never candidate-visible):
- phase offset a = grid_8[seed mod 8], grid_8 = {0,62,125,187,250,312,375,437}
- receptive windows (s=0.85): [a+90,a+130), [a+250,a+290), [a+410,a+450) mod 500
- averse dip (s=0.10): [a+170,a+230) mod 500
- baseline elsewhere (neutral): s=0.35
- ACTION-CONDITIONED DYNAMICS (the causal channel): an act while s<0.30
  applies s -= 0.20 for the next 40 ticks (non-stacking, timer refresh,
  floor 0.0); an act while s>=0.60 applies s += 0.10 for the next 20 ticks
  (non-stacking, cap 1.0). Note the designed cascade: annoyance can push
  post-dip neutral below 0.30, so ill-timed acting propagates.

Observations x_t (candidate-visible; equal access for ALL arms):
- x1 = clip(s_t + N(0, 0.30), 0, 1)            (noisy direct proxy)
- x2 = clip(0.5 + 0.5*cos(2*pi*(t-a)/500) + N(0, 0.40), 0, 1)
       (noisy schedule carrier; per-tick weakly informative, integrable)
- x3 = min(ticks_since_last_feedback_event, 100)/100
- x4 = U(0,1) decoy
- t (tick index) is visible to all arms.

Action space: {act, silent}; hard cooldown = 5 ticks forced silent after act
(applies to every arm including ideal).

Feedback r_t (only when acting): s>=0.6 -> accept p=0.9 else ignore;
s<=0.3 -> reject p=0.9 else ignore; else accept 0.1 / reject 0.1 / ignore 0.8.

Utility (frozen table): accept +1.0; reject -1.0; ignore -0.2; silent 0.
Derived expected utilities: E[u|act,hi]=+0.88, E[u|act,lo]=-0.92,
E[u|act,mid]=-0.16.

Normalization: U_norm = raw episode utility / U_IDEAL_ANALYTIC, where
U_IDEAL_ANALYTIC = 0.88 * 21 = 18.48 (ideal observer acts every 6th tick
inside 3x40 window ticks: 7 acts/window x 3; derivation in card, verified in
PART0 against realized ideal mean).

RNG: numpy PCG64, one Generator per episode, seed = master*100000 + i;
PYTHONHASHSEED=0 set by runner; python `random` unused; imports of
torch/tensorflow/jax FORBIDDEN in this task's code.

## 2. Candidate (frozen class) — gated_initiative_learner_v0

Interface: sees only (t, x1..x4, own feedback history); trains on train
episodes; NO o_t/s access anywhere, train or eval.

Learned components (cross-episode, fit on train split only):
- L1: phase-anchored accept-rate map h(tau), tau = (t - a_hat) mod 500,
  50 bins, Laplace +1, built from own act feedback with a_hat = argmax of
  W=50 smoothed x2 (per training episode)
- L2: x1 class-conditional histograms P(x1 | feedback-class) (10 bins,
  Laplace +1; feedback events as noisy labels)

Within-episode state (eval): running a_hat from smoothed observed x2 prefix;
receptivity estimate p_hi/p_mid/p_lo from h(tau) x L2(x1) x recent-feedback
fusion (accept -> local boost, reject -> local suppress + backoff).

Decision rule — theta-free act rule: argmax expected utility under the frozen
utility table: act iff 0.88*p_hi - 0.92*p_lo - 0.16*p_mid > 0. NO free act
threshold exists; any post-hoc constant tuning of the candidate = run void
(K-F).

Probes (active sensing, frozen budget): <= 3 probe acts per episode, only at
t<150, only while window-location uncertainty is high AND p_lo < 0.2.

Training protocol (frozen): 2 passes over train episodes, epsilon-greedy
exploration epsilon = 0.15 constant; after training, all learned tables
FROZEN for eval; eval-time adaptation = within-episode state updates only.

Implementation constants not fixed above (bin edges, smoothing window, fusion
weights, uncertainty rule) must land in the I1 commit with written ex-ante
rationale BEFORE any P0/P2 run (commit-order anti-tuning proof); changing any
of them after the first P0 run = run void (K-F).

## 3. Baseline family (frozen; equal observation access; CRN — same episode seeds across all arms)

Decision-card family (the max{} the candidate must beat):
1. always_silent
2. always_act (cooldown-respecting)
3. fixed_rate p, p in {0.02,0.05,0.10,0.20}, train-selected, frozen for eval
4. single_threshold: act iff channel >= theta; channel in {x1,x2}, theta in
   {0.30,0.35,...,0.80}; TWO variants both included in max{}: (a)
   train-selected; (b) EVAL-ORACLE-TUNED (hostile upper envelope; narrowing
   addition, allowed under only-narrow rule)
5. behavior_tree_v0 (product rival, frozen structure): act iff x1 >= th_a AND
   cooldown_elapsed >= c AND consecutive_rejects < 2; on reject -> c doubles
   (cap 80), on accept -> c resets; grid th_a in {0.55,0.60,0.65} x base c in
   {20,40}, train-selected, frozen for eval.

Controls (signature S1; not part of max{} but must be separated):
6. obs_decoder: stateless per-tick logistic on (x1,x2,x3,x4,t/500), trained
   on train WITH judge labels (control privilege), frozen; acts by the same
   theta-free expected-utility rule.
7. amortized_distillate: logistic mimic of the candidate's eval-policy on
   features (x1,x2,x3,x4,t/500,n_accept,n_reject,ticks_since_reject,
   probes_used), fit on candidate TRAIN rollouts, deployed static.
8. no_update control == ablation A1 arm (dual use).
Reference (not a rival): ideal_observer (sees s_t; acts iff s>=0.6).

## 4. Ablations (structural-identity check done at card time)

- A1 (THE decision-card ablation gate): all learned tables (L1,L2) replaced
  by uninformative priors; within-episode machinery intact.
- A2 (reported): feedback fusion disabled (r_t ignored by belief).
- A3 (reported, pre-declared possibly-inert): probe budget = 0.
Structural check: A1 and A2 provably change decisions unless the env is
per-tick decodable (excluded by G-P0-DECODER) or the candidate never acts
(excluded by probe rule); A3 may be inert if phase resolves early from x2 —
therefore A3 is informational, NOT a gate. No dominance identity found that
forces any gate leg equal by arithmetic (dominance-theorem audit done).

## 5. Frozen constants (threshold_source table)

| name | value | ex-ante rationale |
|---|---|---|
| delta (win margin) | 0.05 normalized | smallest product-meaningful margin; > MDE floor enforced by G-P0-POWER; set before any run |
| CI method | 95% bootstrap, 10k resamples, seeded, percentile | standard; frozen before runs |
| N_ep | 40/seed (160 pooled; 80 held-out block) | power target vs delta; doubling rule below |
| seeds | dev {31,47}, held-out {61,79} | R1 precedent; held-out first burned at P2 |
| T | 500 | matches R1-scale envs; 3 windows + dip fit |
| cooldown | 5 | rate-limits always_act; realistic initiative pacing |
| windows / dip / s-levels | 3x40 @ +90/+250/+410; 60 @ +170; 0.85/0.35/0.10 | headroom by design; verified in PART0, not assumed |
| annoyance / engagement | -0.20/40 ticks; +0.10/20 ticks (non-stacking) | intervention-changes-trajectory carrier |
| sigma_x1 / sigma_x2 | 0.30 / 0.40 | x1 informative-not-decodable; x2 integrable-not-per-tick-decodable; verified by G-P0-DECODER |
| feedback probs | 0.9/0.9/(0.1,0.1,0.8) | noisy-but-informative feedback channel |
| utility table | +1.0/-1.0/-0.2/0 | asymmetric false-positive cost per decision card |
| U_IDEAL_ANALYTIC | 18.48 | derived: 0.88 x 21 acts; PART0 cross-checks realized ideal |
| headroom gate | ideal - max(static family) >= 0.08 pooled | saturation check; below this the fight is meaningless |
| decoder gate | ideal - obs_decoder >= 0.05 pooled | K1 obs-decodability exclusion |
| degenerate gate | always_silent == 0; always_act <= -0.2 | env asymmetry sanity |
| power gate | MDE_80 = 2.8*sigma_pair/sqrt(N) <= 0.05, pooled AND held-out block | discovery-loop MDE lesson; sigma_pair from CRN paired diffs (behavior_tree vs always_silent) in PART0 |
| N doubling | 40 -> 80 per seed, at most once | pre-registered; then instrument_invalid_underpowered |
| ablation gate | (cand - A1) >= 0.5 x (cand - max_family) | decision card: ablation destroys >= half the gain |
| intervention ticks | forced branches at tau {120,260,400}; divergence on >= 80% episodes | pre-registered branch set |
| probe budget | <= 3, t<150, p_lo<0.2 | bounded active sensing; bounded worst-case probe cost |
| epsilon (train) | 0.15, constant, 2 passes | exploration for feedback labels; frozen |
| budget line | 4.0 CPU-h total; measured-first projection x1.8 after P0 | cost-projection lesson (1.7-1.8x underestimate) |
| runtime guard | 3600 s/phase; timeout >= measured x3 after first measurement; stdout tail; spawn_error != timeout | R3 executor lessons |
| env revision grid | sigma_x1 {0.25,0.30,0.35}; sigma_x2 {0.40,0.50,0.60}; window width {30,40,50}; ONE revision round | candidate-free instrument calibration only; then K-D |

## 6. Gates — PART0 (candidate-free environment certification; mechanical barrier)

PART0 runs BEFORE any candidate contact and writes part0_certificate.json;
the P2 runner MUST refuse to start without a valid certificate (mechanical
barrier, BATTERY-EXEC precedent). PART0 uses dev seeds {31,47} ONLY —
held-out {61,79} remain unburned until P2; sigma_pair is measured on the 80
dev episodes and the MDE requirement is evaluated for N=160 (pooled) and
N=80 (held-out block) using that dev estimate.

- G-P0-HEADROOM, G-P0-DECODER, G-P0-DEGEN, G-P0-POWER: per §5.
- G-P0-INTERVENTION-CARRIER: forced-act branches at frozen ticks on
  behavior_tree base trajectories diverge downstream (L1 distance of judge
  s-trajectory > 0 and utility delta != 0) on >= 80% of episodes.
- G-P0-LEAK: schema whitelist scan of every candidate-visible structure for
  o_t/s/receptivity-derived fields; scanner has a PLANTED-LEAK POSITIVE
  CONTROL that must fire (structurally failable detector).
- G-P0-REPLAY: PART0 fresh-process replay x2 bit-exact.
PART0 fail -> STOP; one pre-registered revision round (§5 grid), re-certify;
second fail -> K-D. Candidate code is never touched in revision.

## 7. Gates — P2 (battery; pooled AND held-out block both required)

- G-R2-WIN: mean U_norm(candidate) >= max(family §3.1-5) + 0.05 AND 95% CI
  non-overlap (candidate lower bound > family-max upper bound).
- G-R2-CONTROL-SEP (S1, non-negotiable): candidate separates from
  obs_decoder, amortized_distillate, and no_update/A1 with CI separation.
- G-R2-ABLATION (S2): per §5 ablation gate.
- G-R2-INTERVENTION (S4): suppress candidate's first act in each realized
  window (branch replay, same seeds) -> downstream divergence + utility delta
  on >= 80% episodes; report post-reject act-rate drop (annoyance-aware
  adaptation) as behavioral corroboration.
- G-R2-GEOGRAPHY (S3): predicted failure geography (§8) holds; uniform win
  across all cells = red flag -> leakage audit BEFORE any pass verdict.
- G-R2-REPLAY (S5): battery fresh-process replay x2 bit-exact; trace
  completeness per §9.
Verdict follows the signature standard: high score with S1/S2 failure =
HIGH_SCORE_NO_ATTRIBUTION (not a pass); low score with signature present =
LOW_SCORE_SIGNATURE_PRESENT (route decision, not a pass).

## 8. Predicted failure geography (frozen at card time)

- C1: on window-1 utility the candidate ties or barely beats behavior_tree
  (both discover late); candidate advantage concentrates on windows 2-3 via
  phase prediction. (geography_report.json decomposes per-window.)
- C2: candidate pays bounded probe costs; on some episodes it loses small
  amounts to always_silent in dip-adjacent probe ticks.
- C3 red flag: candidate winning uniformly, including window-1 clean-noise
  episodes, and never paying probe costs -> suspect leakage; audit before
  any pass.

## 9. Trace / replay / artifact contract

Per tick (candidate trace): t, x1..x4, belief summary (p_hi,p_mid,p_lo,
a_hat, uncertainty flag), action, probe_flag, expected_utility_act, feedback,
raw utility delta. Judge trace (separate file, judge-side only): s_t, window
phase, dynamics timers. The leak scanner verifies the candidate process
never loads the judge trace.

artifacts/ego-r2-controlled-initiative-001a/ (root resolved at landing, per
MUTATION_SCOPE): result.json (with claim_ceiling field + FULL gate_results
table + failing_gates = ALL non-pass gates), trace.jsonl, judge_trace.jsonl,
baseline_comparison.json, ablation_report.json, replay_report.json,
branch_replay_report.json, geography_report.json, distillate_report.json,
power_report.json, part0_certificate.json, failure_manifest.json (enumerated
independently; NOT a byte-copy of result.json).

Runner rules (R1/R3 lessons, binding): evaluate ALL gates and emit the full
gate_results table (no first-failure short-circuit labels); failure_manifest
enumerates every failed gate + captured exit codes; every gate boolean lands
WITH its underlying evidence text (CI tables, diffs, per-episode rows);
rerun outputs go to phase-suffixed subdirectories, never overwriting prior
phase files; failures are banked, never deleted, never patched into passes.

## 10. Kill conditions and verdict taxonomy (pre-committed)

- K-A: any single_threshold member (incl. eval-oracle-tuned) OR
  behavior_tree_v0 within CI overlap of candidate ->
  route_i_closed_baseline_equivalence. Route I CLOSED; behavior tree is the
  product solution; retune/rescue/second-candidate FORBIDDEN under this card.
- K-B (narrowing): amortized_distillate CI overlap -> same closure label
  (static-policy equivalence = attribution failure).
- K-C: o_t leakage at any stage -> instrument_invalid_leak (repair-only
  path; candidate untouched; no scoring salvage).
- K-D: PART0 fails after one revision round -> r2_instrument_infeasible_stop
  (operator decision; NOT mechanism-negative).
- K-E: measured-first projection exceeds 4.0 CPU-h line -> STOP for budget
  decision; no silent scope reduction.
- K-F: any candidate constant changed after first P0 run -> affected runs
  void.
Verdict labels: r2_initiative_pass | route_i_closed_baseline_equivalence |
r2_fail_<gate> (all failing gates enumerated) | instrument_invalid_<reason> |
r2_instrument_infeasible_stop. Signature subtypes per §7 attach to any
score/signature disagreement.

## 11. Phases, commits, gating

D1 landing (this card + mutation scope; landing commits must be ancestors of
every gated run) -> I1 implementation + TDD (unit tests incl. planted-leak
scanner control, A1 non-inertness on synthetic fixture, replay harness,
executor spawn/timeout rules) -> P0 PART0 certification -> P2 battery
(dev {31,47} + held-out {61,79} first burn; pooled + held-out gates) -> STOP
for Claude hostile post-check. One scoped commit per phase; failure
artifacts banked in place. Execution beyond D1 requires the operator's
execution instruction (drafted by Claude after the landing post-check).

## 12. Claim ceiling (frozen text; copy into result.json)

Maximum possible claim: "bounded offline-simulator engineering evidence
that, in env family r2_sim_v0, a learning-based gated-initiative
controller's timing behavior is a control-flow property whose measured net
utility exceeds the frozen static baseline family under the stated gates."
This is NOT evidence of initiative desire, motivation, wanting, autonomy,
agency, self-awareness, user benefit, or live-product readiness. Live
proactive / self-DM remain closed regardless of outcome. Causal wording is
capped at C2 with intervention-resolution qualifiers (branch-replay
resolution only).

## 13. Stop conditions and rollback

STOP on: any PART0 gate fail; budget line breach; leak detection; guard
timeout; any byte-mismatch between landed card and executing card; any
out-of-scope diff. Rollback: phases are additive (new files + scoped
commits); rollback = revert the phase commit; banked failure artifacts are
never deleted. No threshold, gate, baseline, or constant in this card may be
modified except by a superseding card explicitly authorized by the operator
(delta-supersede; this file is never rewritten).
