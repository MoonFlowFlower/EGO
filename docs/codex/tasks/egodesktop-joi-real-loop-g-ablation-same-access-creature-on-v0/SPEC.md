# EgoDesktop Joi Real-Loop G-ABLATION Same-Access + CREATURE_ON v0 Spec

- task_id: `EGODESKTOP-GABLATION-010`
- status: `card_accepted__synthetic_preregistration_path_closed__real_capture_card_required`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / decisive comparison design`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_experiment_flags_only`
- real_trigger_evidence: `none_for_010_card`
- claim_ceiling: `egodesktop_real_loop_g_ablation_same_access_creature_on_task_card_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-009` replaced the synthetic calibration caveat for the `OFF_STATIC_REPLAY_HELDOUT` row with a
captured calibration reference, but it did not emit a `CREATURE_ON` row, run same-access reproducers, freeze scoring
thresholds, compare conditions, or produce a verdict. The next useful slice is a new bounded task card for a decisive
comparison package:

- one or more `CREATURE_ON` heldout rows captured through the same real EgoDesktop chat-turn seam and existing 006
  tap/writer;
- a same-access reproducer battery with independent callable controllers fit only on calibration data and evaluated on
  heldout rows;
- predeclared prompt packs, split protocol, thresholds, equivalence rules, and stop semantics before implementation;
- an expected honest route to `baseline_saturated_stop` if same-access controllers match or beat the candidate.

This card does not implement the comparison. It freezes the boundary for Claude review before any scoring, capture, or
runtime mutation.

## Claude Review Readback

Desktop Claude returned `BLOCKING_FINDINGS` source-limited for the first 010 card draft. The blockers were accepted as
technically valid for this repo:

1. `B1`: `baseline_saturated_stop` was treated as an equivalence conclusion without a predeclared equivalence boundary,
   power target, minimum sample size, or TOST/equivalent decision rule.
2. `B2`: the same-access battery capped the strongest baseline at short-context or low-capacity controllers, which
   could create false attribution against a stronger public-history learner.
3. `B3`: threshold, prompt-pack, baseline-battery, epsilon, and minimum-n freezing were pushed into a post-review
   implementation plan with no independent capture-before review checkpoint.

Advisories also accepted for repair: require a creature-to-D mechanism-presence positive control, add semantic
near-duplicate leakage checks, clarify that independent means independent callable code path rather than independent
author, and complete the outcome-blind verdict matrix for candidate-worse-than-static cases.

Desktop Claude then returned `NO_BLOCKING_FINDINGS (source-limited)` for the repaired card. The review accepted that
B1-B3 and A1-A4 are closed at the card layer, the mutation scope remains within the allowed card paths, and the card
does not authorize implementation. Claude's next minimal action is a separate preregistration-manifest slice that freezes
epsilon, power, MDE, minimum n, prompt packs, baseline battery, verdict matrix, and hashes, then receives independent
source-limited review. `CREATURE_ON` capture, scoring, verdicts, program-state updates, evidence-ledger updates, push,
tag, and remote anchor remain forbidden.

Post-012 route readback: that preregistration-manifest slice was attempted as `EGODESKTOP-GABLATION-011` and then
blocked because the repaired synthetic prompt packs still leaked split/meta identity, collapsed into repeated templates,
and stayed in a narrow calm affect band. `EGODESKTOP-GABLATION-012` closed or downgraded the synthetic prompt-pack
preregistration path only. This does not close the broader 010 card, does not prove baseline saturation, and does not
authorize capture or scoring.

## Current Stage / Layer

- current layer: `engineering implementation / evidence-chain design`
- mainline integration status: `not connected to default EgoDesktop runtime`
- enabled status: `explicit experiment flags only; default runtime remains off`
- real trigger evidence: `none for this docs-only card`
- current evidence carried in: 009 `d_field_replay_precondition_satisfied=true` and `scoring_run_authorized=false`
- claim ceiling: task-card authorization boundary only

## Bounded Audit

- real objective: define the smallest future comparison slice that can distinguish a `CREATURE_ON` effect from static
  replay and same-access classical controllers without granting runtime authority.
- possible wrong problem definition: if the current calibration/heldout protocol is too weak, prompt count is too low,
  or equivalence power is insufficient, the task must stay at card or preregistration repair instead of implementation.
- strongest baseline explanation: same-access public-input controllers can reproduce or beat the candidate because the
  visible output is a simple function of current turn, recent history, calibration schedule, or static presentation
  state.
- strongest invalidity risk: giving `CREATURE_ON` privileged creature state, prompt text, bot text, future target,
  renderer idle, or post-hoc prompt selection unavailable to baselines.
- falsifier for the current framing: the card cannot specify independent callable same-access implementations,
  pre-frozen fit/evaluation splits, and an outcome-blind threshold/equivalence rule before capture.
- evidence still insufficient: a single `CREATURE_ON` trace, a same-pack replay, an implementation-only pass, a report
  that names baselines without invoking them, or any result with thresholds tuned after seeing heldout outputs.
- mechanism vs resemblance: the future task tests bounded output-trace discriminability only; it does not test
  subjectivity, emotion, consciousness, or companion readiness.
- hard-coding check: prompt packs, controller families, thresholds, and metric definitions must be frozen before
  heldout `CREATURE_ON` capture; no literal expected labels or verdict dictionaries can decide the result.
- local optimum / Zeno check: if the first fair same-access battery saturates, bank `baseline_saturated_stop` rather
  than adding task complexity to chase a stronger story.
- leakage check: leakage scans must include positive controls and specifically cover privileged creature fields,
  future/target fields, LLM text leakage, prompt/user-text leakage in D, renderer idle, and duplicate source hashes.
- weak-baseline check: the baseline battery must include short-context controller families and a high-capacity
  full-public-history steelman learner. If the steelman is omitted, the preregistration manifest must prove a low-order
  Markov upper-bound for the candidate mechanism before capture.
- schema-split check: `CREATURE_ON`, `OFF_STATIC_REPLAY_HELDOUT`, and `SAME_ACCESS_REPRODUCER_BATTERY` rows must use one
  evaluator schema and one verdict helper; no second logic path can bypass replay/leakage gates.
- replay weakness check: all D fields must recompute from serialized_state + observation and callable controller
  functions, not stored hashes or stored labels.
- claim-inflation check: even an attribution pass would remain bounded local comparison evidence only; expected closure
  is baseline saturation.
- minimal validation: docs/card completeness, YAML parse, route-convergence generation, `git diff --check`, Claude
  source-limited card review.
- stop condition: any requirement to emit rows, score, compare, update program state/evidence ledger, push, tag, or
  remote-anchor before both the repaired card and the frozen preregistration manifest receive no blocking findings.
- rollback plan: delete this task directory, remove the task-board entry, regenerate derived views.
- acceptance signal: Claude returns `NO_BLOCKING_FINDINGS` on the repaired card text. This only permits the separate
  preregistration-manifest slice, not `CREATURE_ON` capture or scoring.

## Mainline Target

The future implementation target is explicit local artifact tooling plus the existing real EgoDesktop chat-turn seam:

- predeclared calibration and heldout prompt packs with content/provenance disjointness;
- `CREATURE_ON` heldout rows captured through `window.egoDesktop.sendChatTurn(...)` and the existing 006 tap/writer;
- same-access reproducer rows generated by independent callable controllers using only public inputs and calibration
  data available to the candidate;
- `OFF_STATIC_REPLAY_HELDOUT` retained as a decisive input-blind replay floor;
- one evaluator report that compares `CREATURE_ON`, `OFF_STATIC_REPLAY_HELDOUT`, and the best same-access reproducer;
- verdict rules inherited from the 002 harness contract, with baseline saturation treated as closure evidence.

No default EgoDesktop runtime path is enabled or changed by this card.

## Enabled-State Requirement

All future 010 behavior must be explicit-flag and artifact-only. The card permits no default runtime enablement.

Minimum future flags or equivalent CLI arguments must include:

- `JOI_REAL_LOOP_G_ABLATION=1`
- `JOI_REAL_LOOP_CONDITION=CREATURE_ON`
- `JOI_REAL_LOOP_TRACE_DIR=<artifact_dir>`
- `JOI_REAL_LOOP_LLM_MODE=replay_locked`
- `JOI_REAL_LOOP_PROMPT_PACK=<predeclared_pack_path_or_hash>`
- `JOI_REAL_LOOP_SPLIT=heldout`
- `JOI_REAL_LOOP_SCORING_THRESHOLDS=<predeclared_threshold_file>`
- `JOI_REAL_LOOP_BASELINE_BATTERY=<predeclared_battery_file>`

With the flags absent, default behavior must remain unchanged.

## Pre-Registration Review Gate

No `CREATURE_ON` heldout capture, same-access run, scoring, or verdict is authorized until a separate preregistration
manifest exists, is hash-frozen, and receives an independent source-limited review with no blocking findings.

The preregistration manifest must be produced before capture and must record:

- calibration and heldout prompt pack paths and hashes;
- split protocol id/hash and disjointness criteria;
- D-field whitelist and metric definitions;
- equivalence boundary `epsilon` for each scored D metric;
- alpha, power target, MDE, and minimum `n` per split/condition;
- TOST or equivalent statistical decision rule;
- baseline battery manifest path/hash, including controller families and hyperparameter spaces;
- high-capacity full-public-history steelman controller definition, or a low-order Markov upper-bound proof for why
  short-context controllers are sufficient;
- mechanism-presence positive-control plan;
- leakage, near-duplicate, renderer-idle, and replay positive controls;
- outcome-blind verdict matrix;
- producer function and code path hashes.

If this manifest is absent, mutable after capture, underpowered, or not independently reviewed, the next status is
`blocked_preregistration_not_accepted`, not `baseline_saturated_stop`.

## Real-Trigger Evidence Requirement

Future implementation acceptance requires real trigger evidence for `CREATURE_ON`:

- capture through visible/default EgoDesktop chat-turn entrypoint or equivalent real IPC seam;
- `window.egoDesktop.sendChatTurn(...)` or the existing default chat-turn result boundary must be the trigger;
- existing 006 tap/writer must produce `trace_rows.jsonl`;
- no second chat-turn implementation path;
- trace rows must record run id, condition id, prompt id, prompt-pack hash, split id, source hashes, row hash, public
  inputs, serialized state, adapter output, D-field provenance, and replay inputs.

This card itself has no 010 trigger evidence and must report that explicitly.

## Hypothesis

If `CREATURE_ON` has a real output-trace effect beyond static replay and public-input same-access controllers, then a
predeclared heldout comparison should show the candidate beating both `OFF_STATIC_REPLAY_HELDOUT` and the best
same-access reproducer under frozen metrics. If the best same-access reproducer matches or beats the candidate, the
correct outcome is baseline saturation / route closure evidence, not attribution pass.

## Strongest Baseline

The strongest baseline is a same-access reproducer battery fit on calibration data and evaluated on heldout rows with the
same public inputs, prompt splits, schedule metadata, and allowed D fields as the candidate. At minimum, the battery must
cover:

- `current_turn_reactive`
- `ema_history`
- `hysteresis_history`
- `logistic_short_context`
- `linear_short_context`
- `fixed_shim_template`
- `full_public_history_steelman`

`OFF_STATIC_REPLAY_HELDOUT` remains the decisive input-blind replay floor. Same-pack static replay remains diagnostic
only and cannot support positive evidence.

`full_public_history_steelman` must be a same-access learner over the full public calibration history and predeclared
public feature set. It may not consume privileged creature state, bot text unavailable to the candidate's D recompute,
future/target labels, heldout labels, expected verdicts, or post-capture threshold choices. If the implementation omits
this steelman, the preregistration manifest must provide a computed low-order Markov proof that the candidate's D path is
upper-bounded by the remaining short-context controllers. Otherwise the comparison is blocked for weak baseline.

`independent callable controller` means an independently invoked implementation path with its own producer function,
input artifact list, source hashes, and recompute tests. It does not imply independent authorship and must not be used as
a substitute for leakage, replay, or preregistration gates.

## Equivalence / Power Gate

`baseline_saturated_stop` is an equivalence conclusion and requires a predeclared equivalence protocol. The future
implementation must define:

- D metric vector and aggregation rule;
- equivalence boundary `epsilon` for each D metric or for the aggregate score;
- alpha and power target;
- minimum detectable effect with `MDE <= epsilon`;
- minimum sample size per split and condition;
- TOST or an equivalent predeclared equivalence test;
- rule for ties, confidence intervals, and missing/invalid rows.

If power is insufficient, sample size is below the frozen minimum, or `MDE > epsilon`, the outcome must be
`blocked_underpowered_equivalence_design` or card/preregistration repair. It must not be reported as
`baseline_saturated_stop`.

## Mechanism-Presence Positive Control

Before same-access equivalence can be interpreted, the future run must include a positive control showing that the
creature-to-D path is non-empty. At minimum, a predeclared `CREATURE_ON` versus `CREATURE_OFF` or `CREATURE_FROZEN`
contrast must move at least one allowed D field under the frozen D metric. If no allowed D field moves, the result is
`real_loop_g_ablation_fail_no_creature_effect` or `blocked_no_creature_to_d_path`, not baseline saturation and not
attribution.

## Semantic Near-Duplicate Leakage Gate

Content-disjoint prompt hashes are necessary but not sufficient. The preregistration manifest must define a callable
near-duplicate leakage scanner with a frozen distance threshold and at least one paraphrase positive-control case. The
scanner must cover calibration/heldout prompt text or text hashes available to the manifest without leaking heldout
answers into D. If near-duplicate controls are unavailable or fail to fire, heldout generalization claims are blocked.

## Outcome-Blind Verdict Matrix

The future verdict helper must cover at least these cells before any result is seen:

- candidate beats heldout static replay and beats best same-access by the frozen margin: bounded local attribution
  candidate only, still below product or mechanism success;
- candidate is equivalent to heldout static replay: `real_loop_g_ablation_baseline_saturated_stop`;
- candidate is equivalent to or worse than best same-access: `real_loop_g_ablation_baseline_saturated_stop`;
- candidate is worse than heldout static replay by more than the frozen margin: `real_loop_g_ablation_fail_no_creature_effect`;
- no allowed D field moves in the mechanism-presence positive control: `real_loop_g_ablation_fail_no_creature_effect` or
  `blocked_no_creature_to_d_path`;
- leakage, renderer-idle dominance, unlocked LLM, weak baseline, underpowered equivalence, replay failure, or
  preregistration mutation: blocked or invalid verdict only.

## Ablation Requirement

Future implementation must define and run only the ablations needed for this comparison:

- `CREATURE_ON`
- `OFF_STATIC_REPLAY_HELDOUT`
- `SAME_ACCESS_REPRODUCER_BATTERY`
- `CREATURE_OFF` or `CREATURE_FROZEN` mechanism-presence positive control
- leakage positive control
- semantic near-duplicate positive control
- renderer-idle dominance control
- shuffled or heldout-observation control if needed to prove D excludes public-input leakage

No broader tournament, product polish, route advancement, or new mechanism family is authorized by this card.

## Trace / Replay Requirement

Future trace rows and reports must prove:

- all scoring D fields are frozen before execution;
- `CREATURE_ON` rows serialize complete state and observation;
- same-access rows serialize controller id, producer function, fit split, evaluation split, hyperparameters, source
  hashes, and callable recompute path;
- offline replay recomputes candidate and baseline outputs from serialized_state + observation;
- LLM output is replay-locked or excluded from D;
- renderer idle is excluded from D and cannot drive the metric;
- prompt IDs, user-text hashes, row hashes, trace-record hashes, and capture run IDs are disjoint across calibration and
  heldout partitions where required;
- same-access controllers use no privileged creature state, bot text, future target, verdict, or heldout-only labels.
- the high-capacity full-public-history steelman or the low-order Markov upper-bound proof is serialized and
  recomputable.

## Computed-Evidence Provenance Gate

Every future score, baseline, ablation, leakage scan, replay metric, and verdict must record:

- producer function;
- input artifact paths;
- run id;
- seed, prompt ids, episode ids, and split ids;
- aggregation rule;
- code path hash;
- threshold file path/hash;
- baseline battery file path/hash;
- source row hashes;
- scoring D-field whitelist;
- verdict helper function id.
- equivalence protocol hash and preregistration manifest hash.

Static verdict dictionaries, hand-written scores, unconditional clean reports, or tests that only assert pass are
forbidden.

## Acceptance Gate

Card acceptance requires:

- task card and mutation scope exist before implementation;
- task-board entry records 010 as card/review-only;
- thresholds, prompt split, baseline battery, equivalence rule, expected saturation semantics, and stop conditions are
  specified before implementation;
- no capture or scoring can occur until a separate preregistration manifest freezes thresholds, prompt packs, baseline
  battery, epsilon, power, minimum n, and verdict matrix, then receives source-limited review;
- baseline saturation requires a TOST or equivalent equivalence protocol with `MDE <= epsilon`; insufficient power blocks
  saturation claims;
- same-access battery includes a high-capacity full-public-history steelman or a computed low-order Markov upper-bound
  proof;
- card requires same-access independent callable implementations, not labels only;
- card requires a creature-to-D mechanism-presence positive control;
- card requires semantic near-duplicate leakage scanning with a positive control;
- card blocks positive attribution under same-access equivalence, heldout static replay equivalence, leakage, renderer
  idle dominance, unlocked LLM, weak baseline, underpowered equivalence, preregistration mutation, or no creature effect;
- card forbids `PROGRAM_STATE_UNIFIED.yaml`, evidence ledger, default runtime, push, tag, and remote-anchor changes;
- Claude source-limited review returns `NO_BLOCKING_FINDINGS` before any preregistration-manifest slice; a second
  source-limited review of that manifest is required before implementation capture or scoring.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_same_access_creature_on_task_card_only`.

This can prove only that EGO has a bounded task-card boundary for a future same-access + `CREATURE_ON` comparison. It
does not prove real-loop effect, baseline saturation, candidate failure, attribution, route advancement, product benefit,
runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness,
alive status, or Bar-2 specialness.

## Stop Condition

Stop and do not implement if:

- Claude returns any blocking finding on the card;
- thresholds, prompt split, baseline battery, equivalence rules, epsilon, power, minimum n, or verdict matrix are not
  frozen in a preregistration manifest before capture;
- the preregistration manifest has not received independent source-limited review;
- equivalence design is underpowered or `MDE > epsilon`;
- the high-capacity full-public-history steelman or low-order Markov upper-bound proof is absent;
- semantic near-duplicate scanner or mechanism-presence positive control is absent;
- same-access controllers are not independent callable implementations;
- implementation would require default runtime enablement or a second chat-turn path;
- the next step would update program state/evidence ledger, push, tag, or remote-anchor.

## Rollback Plan

Delete this task directory, remove `EGODESKTOP-GABLATION-010` from `Tasks/TASK_BOARD.yaml`, regenerate
route-convergence views, and leave 009 artifacts unchanged.

## Expected Changed Files

Card/review slice:

- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-same-access-creature-on-v0/SPEC.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-same-access-creature-on-v0/PLAN.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-same-access-creature-on-v0/STATUS.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-same-access-creature-on-v0/MUTATION_SCOPE.yaml`
- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/TASK_LANE_INDEX.md`

Future implementation, not authorized until card review passes, may touch only a new 010 artifact namespace and minimal
explicit CLI/test modules named by a repaired implementation plan.

## Forbidden Changes

- No implementation before Claude card review.
- No `CREATURE_ON` capture or scoring before a frozen preregistration manifest and independent preregistration review.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No hidden target, future target, expected verdict, or privileged creature-state leak into baselines.
- No threshold tuning after capture.
- No equivalence, saturation, or closure claim when power is insufficient or `MDE > epsilon`.
- No omission of the high-capacity full-public-history steelman unless a computed low-order Markov upper-bound proof is
  accepted before capture.
- No semantic near-duplicate leakage blind spot.
- No same-pack replay as positive evidence.
- No positive attribution if same-access or heldout static replay matches or beats the candidate.
- No route advancement, product/readiness wording, push, tag, or remote anchor.

## Auto-Remote-Anchor Decision

`forbidden`. No push, tag, remote branch update, GitHub Project sync claim, or remote anchor is authorized by this card.

## Next Minimal Closed-Loop Action

No active implementation child is authorized. If future real evidence is wanted, open a separate real captured
desktop-chat-turn design card with explicit capture authority and independent source-limited review. Do not capture or
score `CREATURE_ON` until that future card and its frozen preregistration boundary are accepted.
