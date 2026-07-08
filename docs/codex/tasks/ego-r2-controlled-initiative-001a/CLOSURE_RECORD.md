# CLOSURE RECORD — EGO-R2-CONTROLLED-INITIATIVE-001A — route I closed

record_type: route_closure_record (forward record; no banked artifact is rewritten)
task_id: ego-r2-controlled-initiative-001a
date: 2026-07-07
operator_approval: Zhouyu (Leo) / 2026-07-07
adjudication: Claude hostile post-check of P2 run1 + SC1 spec-conformance readback

## 1. Verdict and basis

Route I (learned gated initiative) is CLOSED on a valid decisive negative:
`r2_fail_win`, anchored solely on G-R2-WIN. The candidate, confirmed
conformant to the frozen card (act rule = frozen utility arithmetic with no
tunable threshold; probe budget enforced, 0 violations; feedback fusion
present and reachable), lost to the static baseline family with CI
separation on both seed blocks:

- pooled: candidate 0.6028814935 [0.5766352137, 0.6277073187] vs
  eval-oracle single_threshold_x1_0.80 0.7362689394 [0.7129312094, 0.7600125135]
- held-out {61,79} (first burn): candidate 0.5980790043 vs 0.7161796537

Closure basis: the pre-committed kill (decision card §R2) closes route I on
a CI-level TIE with a tuned threshold; a CI-separated LOSS is a fortiori
stronger evidence for the same conclusion. Retune, rescue, and
second-candidate attempts under this card remain forbidden.

Scope of closure: this closes route I's PRODUCT claim — that learned gating
earns net utility over the shippable static family in this env class. It
does NOT adjudicate the mechanism-capability question negatively; see §4a.
Score verdict and signature profile disagree in this run, and the two are
recorded separately by design.

## 4a. Score-vs-signature classification (recorded with the closure)

The run's score verdict (loses to the tuned-threshold RIVAL) and its
signature profile (separates from every live CONTROL) disagree.
Classification: low_score_signature_present, bounded to this env family.
Signature evidence: stateless obs_decoder control 0.1993 vs candidate
0.6029 (CI-separated); A1 no-learning ablation collapses the candidate to
0.0; replay bit-exact x2; the named capability observable — within-episode
latent-schedule inference — was realized (in-window utility ~96% of
analytic ideal, per-window decomposition banked). Rival-vs-control rule:
a task-specialist rival matching or beating the candidate is a product
verdict, not evidence that the function was unrealized; a control matching
the candidate would have been — and did not occur. Caveats: the signature
rests on the decoder control alone (A2 void per §3, distillate void, A1
collapse arithmetic-degenerate), so signature strength is graded weak-but-
present, engineering-observation ceiling, not a mechanism-validity claim.

## 2. Evidence anchors

Card landed frozen @ 84272490b6aa47e41e28d94aadcad6f0df6f7ac6; ADDENDUM-001
@ 4e966c09f205c6639fac01735e6348f516deef6a (gate change
d5f082ddcba6731d746ab614db92bc0d22a7adf5); P0R pass banked @
456dbe9b64e1e2195e9a62c74da7c3ce2a364080; certificate wiring W1 @ c8ea20c7
(short; full hash echoed in the landing report); P2 run1 banked+pushed @
7726d66cea537dde8bf55f610268c9047ba449fc (HEAD at closure drafting). All
failure artifacts preserved; grid-edge audit hook (x1_0.80 winner, rising
trend) recorded — it makes the negative conservative (a wider grid could
only raise the baseline).

## 3. Instrument-defect annotations (forward corrections; banked files untouched)

- A2 arm: harness breach — fusion was not actually disabled (factory
  wrapper kept feedback side-effects), so A2==candidate bit-identity is an
  arm defect. A2 numbers are VOID; the causal contribution of feedback
  fusion was NOT measured in either direction. An earlier auditor
  suspicion that fusion was epiphenomenal is RETRACTED on SC1 code
  readback.
- G-R2-ABLATION "fail" label: reporting artifact — the runner added an
  extra `candidate_advantage > 0` condition; the card inequality is true
  at the banked numbers. Correct taxonomy: not_evaluable (attribution
  gates presuppose a WIN). The run's failing gate set is effectively
  {G-R2-WIN}.
- A3 (probe-budget-zero, informational): never implemented; card §4
  required it reported. Defect recorded; no rerun on a closed route.
- amortized_distillate: 0.0 result strongly implies an always-silent mimic
  (no class-balance handling); faithful-mimic vs imbalance-artifact is
  ambiguous from banked artifacts. Distillate evidence carries no weight
  in this record.
- These defects live on the attribution side only; none touches the
  G-R2-WIN inputs (candidate arm, family arms, CRN, CI machinery).

## 4. What survives at engineering-observation ceiling (not mechanism claims, not reopen grounds)

- Within-episode phase inference worked: candidate in-window utility
  17.76625/ep on average vs analytic ideal 18.48 (~96% capture; per-window
  decomposition banked). The loss came from out-of-window spend
  (-6.625/ep; 37.04 out-of-window acts/ep) — a decision-calibration
  failure under asymmetric cost, plausibly aggravated by the frozen
  accept-boost tail extending past window ends.
- Utility-selected simple rules beat likelihood-trained models inside this
  very run (bare threshold 0.736 vs trained stateless decoder 0.199) — a
  calibration lesson, recorded as observation only.

## 5. Product note (operator decision, data point only)

The empirical static winner is the tuned single threshold (0.736); the
behavior tree scored 0.0764 (backoff starvation in this env family). The
decision card's tie-branch names the behavior tree as product solution;
under a loss, the product choice among static policies is the operator's,
made under product governance, outside this record.

## 6. Reopen bar

Two distinct future card shapes are allowed under new decision-card rows:
(a) capability cards — function-realization claims gated on control
separation + ablation destruction + replay + a NAMED unique-capability
observable, with rivals REPORTED but not verdict-gating (BAR1-shaped);
(b) product cards — rival gates with pre-committed kills, deciding what
ships. Controls, ablation, replay, anti-leak, pre-registration, and claim
ceilings are non-negotiable on BOTH tracks.

Any future drift/unseen-regime initiative claim (R2-prime) requires a NEW
decision-card row and must first pass a paper discriminability gate before
any implementation: state the shift family and show on paper that the
cheap-adaptive static rival family (running-quantile thresholds,
per-episode recalibration heuristics, cache/nearest-neighbor) cannot track
it while the learner can, with a pre-registered kill. Prior negative
evidence (this record; identifiability-ceiling lineage) must be cited.

## 7. Claim ceiling

This record certifies bounded offline-simulator engineering evidence only:
in env family r2_sim_v0, the frozen learned gated-initiative candidate did
not exceed the frozen static baseline family (G-R2-WIN fail), and route I
is closed per pre-commitment. It does NOT prove that learned initiative is
impossible in other environments, does NOT prove mechanism validity or
invalidity beyond this env family, and does NOT prove or disprove
initiative desire, motivation, autonomy, agency, self-awareness, user
benefit, live-product readiness, consciousness, subjective experience, or
real emotion. Live proactive / self-DM remain closed (do-not-reopen).
