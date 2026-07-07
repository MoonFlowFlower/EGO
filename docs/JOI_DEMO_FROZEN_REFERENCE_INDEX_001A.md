# JOI_DEMO_FROZEN_REFERENCE_INDEX_001A — Frozen Corpus Index (sole citation source)

Created 2026-07-06. Corpus: `D:\Project\AIProject\MyProject\joi-demo`,
tag `frozen-reference-corpus-20260706` = `52714ed9f7ede8dfd14da7f4c310a9e9db28c834` on
`main` (evidence boundary 61909dd; branch ff-merged).
Cross-ref: ITL C-preflight bank `d5cc28805c43cda0e3d00d243ca55ee97e926526`.
Rule: any Ego doc citing joi-demo results MUST cite through this index at
exactly these ceilings. Append-only; corrections add rows.

## Banked positives (bounded, toy-scale, all "generic / no specialness")

| Result | Verdict | Ceiling — may NOT be cited as |
|---|---|---|
| P3 BAR1 + 004A battery (8/10) | learned-not-hardcoded; ablation collapses; replay-valid | product/EGO readiness; validated components at Ego scale |
| G4 USER-MODEL-001B (`86bdff2`, clean-clone reproduced) | `g4b_bar1_pass`: binary drifting user-latent inferred; beats POPULATION_BEST; below same-access Bayes (expected) | ToM/empathy/product user modeling; Bar-2 |
| G4→G0 coupling 001A | `coupling_bar1_pass_same_access_saturated` (+ predecoded-vote caveat: creature does NOT infer Z end-to-end from raw (a,r)) | end-to-end inference; headroom vs Bayes (none: CI ≤ 0) |
| Operation-learning gate 001A (`2cd1060`) | same_access_saturated_bar1_only; replay 88 rows 0 mismatch | anything beyond Bar-1 |
| G0 skill 001A/001B (`d0b1c82`/`6013998`) | acquisition/transfer + robustness pass, same-access saturated | Bar-2; mechanism superiority |
| Generality 001A (+min-energy RC) | `generality_present_separable`, scope generic; `explore` counterproductive for viability | architectural specialness |
| Capacity 001C | `capacity_is_binding_constraint`: C*(K) 3.25→8.00 monotone, saturates at skill count; 2-cell `saturates_early` = capacity starvation confirmed | open-ended growth |
| G1 replay spike (`ab7de52`) | thin positive headroom vs compute-matched replay only (0.183 CI>0); route-economics HOLD, full G1 not built | product memory; rich replay |
| Live2D Stage-2 adapter | pure-observer creature→悠小喵 param map verified; full-vs-frozen ablation (survives vs starves) | G-ABLATION (Stage 3); any runtime claim |
| CreatureState v0.2 freeze | interface contract pins: card `5f1afdb3…fae3bd`, schema `ddcce43f…988c9f` (v0.1 BLOCKED, preserved) | emitter conformance pass |

## Banked negatives / closures (evidence, not failure)

| Line | Terminal verdict |
|---|---|
| S2 load-bearing self-model | CLOSED: 001A `invalid_degenerate`; 002A `not_load_bearing` (candidate 0.21 < always-predict 0.27; generic ema_delta=0) |
| LP autotelic curiosity | CLOSED: 2× `LP_DEGENERATE` (naive rectified LP chases pure noise; SNR-gated collapses ≈uniform); stop-loss, no 003A |
| Raw prediction-error curiosity | `curiosity_harmful` at ALL capacities (noisy-TV; worsens with capacity); wrong-metric hypothesis FALSIFIED |
| Integrated "Joi-substrate" route | PAUSED as conjecture (operator 2026-06-29): premise UNPROVEN, not pursued; reopen only via non-saturable longitudinal D + paper well-posedness first |
| Bounded-attribution line | CLOSED after 4th saturation (P1 cue-EMA / P4 direct-optimizer / 001B static-replay / 001C controller) |
| Route-B costly-action D_CAC | REJECTED_NOT_WELLPOSED (optimum = same-access POMDP; cheap approx = hysteresis) |
| S1-P4 viability/homeostatic | bounded_mixed: loses to equal-access direct-objective optimizer V4; entropy probe self-sabotage; payoff variant exactly = V4 (no specialness) |
| Identifiability ceiling | ≥4 independent joi-side confirmations; acknowledged project frontier; only reopen condition recorded in HANDOFF 2026-06-29 block |

## Standing splits/rules inherited as knowledge

- competence = CAPACITY problem (solved, bounded); curiosity-usefulness =
  SIGNAL problem (unsolved; LP/RND unproven here).
- same-access saturation = ceiling marker, NOT a Bar-1 failure (operator
  framing 2026-06-28).
- instrument-repair discipline: fix instrument FORM predeclared, never tune a
  threshold to flip a verdict (capacity 001A→001C lesson).

## Backup & publication status (2026-07-06)

- GitHub publication: CLOSED_NOT_APPLICABLE — committed history contains
  >100MB blobs (e.g. trace_capacity_b.jsonl ~3.0GB); rewriting frozen
  history (LFS migrate / filter) is forbidden. Canonical corpus = local
  repo at tag `frozen-reference-corpus-20260706` =
  `52714ed9f7ede8dfd14da7f4c310a9e9db28c834`.
- Offline backup: git bundle `joi-demo-frozen-20260706.bundle`,
  sha256 = `1bd31e103497388a1adb0de0085c7cbe3673dc3f5101fc450890dcb47d94d6e9`,
  stored at: `D:\Project\AIProject\MyProject\joi-demo-frozen-20260706.bundle`
  (local same-device bundle; off-device copy waived by operator, no
  off-device redundancy claimed).
- Pin citation rule: per pin_verification_report.json = 231 match /
  43 mismatch / 0 missing; the 43 are EOL-era (capacity/generality lines
  predate .gitattributes LF coverage) — cite byte-level pins ONLY through
  that report; content-level golden checks (8/8) passed independently.
