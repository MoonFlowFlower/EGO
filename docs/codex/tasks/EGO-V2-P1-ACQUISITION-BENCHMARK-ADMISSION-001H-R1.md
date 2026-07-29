# EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1

## Bounded task card

- **Task ID:** EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1.
- **Layer:** engineering implementation plus bounded benchmark-admission preflight; science_weight=0.
- **Repository / base:** D:\Project\AIProject\MyProject\Ego, branch codex/ego-v2-bayesian-active-identification-001h, base commit 77a414c555d59486105a508277ebda0db9cdb204.
- **Current stage:** 001H closed before implementation with PREIMPLEMENTATION exact cheap-control equivalence. A broader privileged evidence-value draft was hostile-blocked before landing because its primary control, life envelope, and panel constructor were not comparable.
- **Problem definition:** before training or evaluating any new selector or predictor, determine whether this benchmark can supply (a) a balanced privileged training-row witness within the same finite action envelope as the banked fixed-quota control and (b) a deterministic, model-blind, sufficiently supported panel on disjoint life indices.
- **Hypothesis:** on each consumed world 52/54, a privileged evaluator can construct the frozen support/rank witness within 89 continuous action transitions without exceeding the corresponding control prefix's lifecycle envelope, and the frozen independent-reset panel constructor can satisfy its support/rank contract for rollout IDs 9..16.
- **Primary control:** exactly the first 89 transition_kind=action rows recovered from each banked 001F fixed-quota SQLite run. It is a comparison-envelope control only; no prediction effect is evaluated.
- **Ablation:** run the same privileged witness planner without private cause-aware survival priority. This discloses dependence on privileged survival information but is not an admission requirement.
- **Trace/replay requirement:** banked controls must recover through SQLiteEventStore.recover_run. Privileged reducer calls, navigation, lifecycle, support, panel checkpoints, and forced-action truths must be serialized and exactly recomputed in a fresh process and independent row reducer. This is evaluator replay, not canonical controller replay.
- **Acceptance gate:** only benchmark capacity and comparison-envelope validity. No model training, prediction headroom, acquisition competence, survival effect, or held-out effect is adjudicated.
- **Stop condition:** stop after one frozen run. A missing witness means WITNESS_NOT_FOUND under this planner/budget, not environmental impossibility. Do not implement a learned selector until admission passes.
- **Rollback:** revert only uncommitted R1 paths. Never modify runtime source, prior cards/artifacts, banked databases, or user data.
- **Auto-Remote-Anchor:** forbidden.

## Known facts used rather than re-tested

1. R4 training support was insufficient and its old balanced panel had only fourteen forced interact::interacted truths aggregate.
2. R5 established that raw feature rank 15 is impossible. A subsequent
   algebraic audit tightened the bound: the immediate front cell cannot be
   occluded, so `front_occluded` is constant zero; among the seven remaining
   reachable token indicators, bias equals their sum. A valid reference-coded
   quotient must therefore drop both `front_occluded` and one reachable dummy.
3. 001F banked 89 action rows for p0_cross_v1 and 115 for p2_vertical_v1; therefore 89 is the maximum equal action budget available in both banked runs.
4. 001H's Jeffreys predictive-entropy selector and count deficit have identical ordering on the frozen deterministic outcome cells.
5. Worlds 30..150 are contaminated. No 60..65, 721/722, or other fresh-effect execution is authorized.

## Authority pins

| Input | SHA-256 |
|---|---|
| docs/codex/tasks/EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H.md | bind after this card commit |
| artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/result.json | 39585cc1bc39b776f90978154cb08f4475fc38d66cff069304a68cf9f1d968c4 |
| artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p0_cross_v1.sqlite3 | bind in pre-run provenance |
| artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p2_vertical_v1.sqlite3 | bind in pre-run provenance |
| artifacts/EGO-V2-P1-ADDITIVE-PREDICTION-HEADROOM-DIAGNOSTIC-001C-R4/result.json | 918d07ef7535ea64072ea3eb870b1334e0a5e9efd89e767d713f3902b601d40e |
| labs/ego_life_playground_v0/microworld.py | d87ba9530d32d2b504c75a132ae1163dfe8e8cd0a8879e6cbdd09807a9daa923 |
| labs/ego_life_playground_v0/predictive_control.py | 1763ee3e2b755529559311fb99f247b8bc1034d0cc89708dafdd4b15e8529aae |

Pre-run provenance binds exact task/collision/plan, implementation/tests, all source/input hashes, dependency versions, float dtype, and an absent or empty canonical output directory.

## Frozen contexts, budget, and life firewall

Contexts:

- p0_cross_v1:world=52:policy=711
- p2_vertical_v1:world=54:policy=711

For every context:

- comparison control: first 89 recovered banked action rows;
- privileged witness: exactly 89 evaluator-selected action transitions starting from canonical life 1;
- no artificial reset;
- canonical terminal/death and respawn semantics;
- training-envelope validity requires the privileged witness's maximum life
  index and respawn count to be no greater than the values independently
  extracted from that context's first-89 control prefix;
- panel construction uses independent reset rollouts 9..16 and never trains a
  model. These are frozen initialization namespaces, not canonical progression
  from the training trajectory and not fresh worlds.

The oracle and control start from byte-equal canonical initial world/organism values for their context. Different subsequent lives or states are policy consequences, not extra experience. Any privileged artificial reset, skipped navigation action, or action outside the 89-row budget invalidates comparability.

## Comparison-control extraction

The verifier must:

1. open each 001F SQLite database read-only;
2. call SQLiteEventStore.recover_run and require exact banked replay;
3. retain the first 89 rows with non-null selected_action in sequence order;
4. retain respawn/non-action rows for lifecycle auditing but not action-budget counting;
5. record state/trace/schema/code hashes and life indices;
6. reject migrations, default-filled fields, compatibility shims, or a current-source recompute mismatch;
7. prove that the 89th action exists in both contexts;
8. derive per context the maximum life index and respawn count reached by the
   first-89 prefix; those computed values are the witness's hard upper bounds.

No model comparison is performed in R1.

## Privileged witness planner

The planner is an evaluator-only optimistic upper bound.

- It may inspect private full map, pose, and cause/token mapping for target and survival routing.
- It starts from engine.initial_state for the context and advances action effects only through unchanged transition_world, compute_actual_delta, and compute_metabolism_ledger callables plus canonical organism/lifecycle update semantics.
- Every navigation, rotation, rest, collision, and interaction consumes one action.
- It may not teleport, mutate layout/object/action/metabolism semantics, force a respawn, discard inconvenient rows, or call future panel truth.
- Target choice is deterministic:
  1. visit the frozen support strata in the exact listed order below and keep
     working on the first stratum whose count is below four; rows produced by
     navigation still count toward every stratum they actually satisfy, but a
     later stratum never preempts the first still-deficient stratum;
  2. for token-bearing strata choose the currently reachable target with the
     shortest exact private path; `interact::no_object` targets `empty` and
     `move_forward::blocked` targets `wall`;
  3. tie by full action-sequence lexicographic order under turn_left,
     turn_right, move_forward, interact, rest;
  4. after support, do not launch another target/path search. At the current
     public checkpoint, select among actions whose quotient rank is below 13
     and for which the current row increases rank; tie by current rank,
     current action count, then the frozen action order;
  5. if no current action gains rank, or after all ranks reach 13, select by
     least current action count then frozen action order until the budget ends.
- The admission path performs no cause-based target reorder because no exact
  cause ordering was frozen before implementation. The no-cause-priority
  disclosure is therefore intentionally inert; eligible equal-deficit/path
  object ties, reorder count zero, and trajectory-hash equality must still be
  reported. Adding a cause order or broader rank checkpoint search requires a
  successor card and cannot rescue this verdict.

Each learner-visible row projection contains only public observation, organism-before, selected action, visible pre-front token, public outcome type, actual organism delta, terminal receipt, and public quotient features. The admission task does not train a learner.

## Frozen training-witness support

Per context, within 89 action rows:

- each interact::{v0,v1,v2,v3,v4} has at least 4 direct rows;
- interact::no_object, move_forward::moved, move_forward::blocked, rest::rested, turn_left::turned, and turn_right::turned each have at least 4 rows;
- every navigation row remains in the evidence;
- every action appears;
- maximum life index and respawn count do not exceed that context's extracted
  first-89 control-prefix bounds.

The public quotient has exactly 13 columns. From the frozen 15-column order it
drops `front_occluded` because the adjacent front cell has no intermediate ray
and is never occluded, and drops `front_wall` as the reachable reference dummy.
It preserves all other features in their original order. For every
`context x action` separately, the training design matrix must have rank 13
under NumPy's documented matrix-rank tolerance. Report singular values and
condition number for every matrix. Raw rank 15 and the intermediate 14-column
rank upper bound 13 are structural disclosures.

A failed planner, support floor, life boundary, or rank gate produces WITNESS_NOT_FOUND, not an impossibility theorem.

## Frozen deterministic panel constructor

The constructor is fixed before any model evaluation and never reads model state, prediction, loss, or verdict.

For each context and each `panel_rollout_id=k` in 9..16:

1. construct an independent reset with
   `microworld.initial_world_state(seed=world_seed, layout_id=layout,
   life_index=k)` and an organism byte-equal to `engine.INITIAL_ORGANISM`;
   do not derive it by replaying deaths/respawns from training, and do not
   relabel a life-1 world;
2. visit target front tokens in exact order v0,v1,v2,v3,v4,empty,wall,empty,wall;
3. for each target, use shortest private BFS with the same action edge order;
4. record the first reached public pre-action checkpoint for that target;
5. on a deep copy, force each of the five primitive actions through transition_world, compute_actual_delta, and compute_metabolism_ledger to form evaluator truth;
6. advance the base panel world only by the frozen BFS navigation, never by a forced truth action;
7. stop the life after the ninth target or fail closed.

Panel checkpoints are deduplicated within context before forced-action truth
expansion. The checkpoint hash is exactly the canonical learner-visible public
observation, organism, public relative belief, and 13-column quotient features;
it excludes target, rollout, private path, truth, model, and verdict data.
Required both before and after dedupe, per context: eight checkpoints for each
v0..v4 and sixteen each for empty and wall. The five forced-action truths from
one retained checkpoint are distinct evaluator rows and may not deduplicate one
another. Every reachable `(context,action,front_token,outcome)` cell inherits
the corresponding post-dedupe token floor. For every `context x action`
separately, quotient rank across retained panel checkpoints must be 13;
singular values and condition numbers are disclosed.

Rollout IDs 9..16 are provenance- and constructor-disjoint from the training
trajectory only. They do not establish statistical independence or freshness.

The panel manifest and hash are outputs of R1 and become read-only inputs to a successor evidence-value card. Any future model-specific panel selection requires a new card and cannot inherit R1 admission.

## Leakage and provenance

Private oracle fields may exist only in evaluator receipts. A recursive learner-projection scanner must reject direct and encoded positive controls for:

- cause or cause identity;
- global/private position or map;
- objects_by_cause or token mapping;
- target reason or private path;
- world/policy/run IDs;
- future observation, panel truth, loss, verdict, file path, or hash.

All clean rows must pass. Positive controls must be detected.

The no-cause-priority ablation is disclosure-only and never changes admission
booleans or verdict routing. Because this frozen admission path performs no
cause-based reorder, it reports the number of eligible equal-deficit,
equal-path object ties, reorder count zero, and exact trajectory-hash equality.
This inert result is intentional and is not survival-priority evidence.

## Validity and verdict

Validity requires:

1. exact branch/commit/task/source/input/dependency/output provenance;
2. only consumed worlds, the control-derived witness lifecycle envelope, and
   frozen independent-reset panel rollout IDs;
3. exact read-only 001F recovery and first-89 control extraction;
4. actual invocation receipts for reducer, metabolism, and panel truth callables;
5. no artificial resets, skipped actions, or budget mismatch;
6. leakage scan clean with every positive control detected;
7. fresh-process deterministic recomputation exact;
8. independent row reducer recomputes support, ranks, panel capacity, check map, and verdict;
9. row, lifecycle, panel, producer, source-hash, and verdict tamper controls fail closed.

Verdict order:

1. BLOCKED_001H_R1_PROVENANCE_LEAKAGE_OR_RECOMPUTE;
2. BLOCKED_CONTROL_ENVELOPE_INCOMPARABLE;
3. PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND;
4. DETERMINISTIC_PANEL_CAPACITY_NOT_ADMITTED;
5. ACQUISITION_BENCHMARK_ADMISSION_READY_FOR_EVIDENCE_VALUE_PREFLIGHT.

The table is mutually exclusive and exhaustive. Admission authorizes only a new task card. It does not authorize model training or runtime implementation.

## TDD and provenance phases

- **Phase A:** commit card, collision record, and implementation plan before script/test changes.
- **Phase B RED:** add tests and observe failure for first-89 extraction, lifecycle envelope, quotient projection/rank, private BFS, action accounting, frozen target order, panel construction, leakage controls, verdict priority, recomputation, and tamper.
- **Phase C GREEN:** implement only the evaluator/verifier and tests; do not modify labs or prior artifacts.
- **Phase D provenance:** after tests pass and before formal output, commit PRE_RUN_PROVENANCE.json with finalized hashes and empty output binding.
- **Phase E formal:** execute once, independently recompute, and bank the verdict without tuning/rerun.

## Allowed paths

- this task card;
- docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/;
- scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py;
- scripts/codex/tests/test_verify_ego_v2_acquisition_benchmark_admission_001h_r1.py;
- artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/.

All other paths are forbidden, including runtime source, controller/store/world/metabolism/lifecycle semantics, source banks, transfer learners, neural candidates, held-out worlds, network/LLM, push, and tag.

## Required artifacts

- result.json
- control_rows.jsonl
- privileged_witness_rows.jsonl
- panel_rows.jsonl
- support_report.json
- panel_manifest.json
- ablation_report.json
- leakage_report.json
- recompute_report.json
- failure_manifest.json for every non-admitted verdict
- claim_ceiling.txt
- artifact_manifest.json

## Claim ceiling

The strongest possible claim is that a privileged evaluator found a balanced row witness and fixed a model-blind supported panel under the named old-context budget, making a separately governed evidence-value preflight testable. It is not evidence that a legal learner can collect the rows, that prediction improves, that runtime acquisition works, that the result generalizes, or that survival improves. It cannot establish AGI, agency, consciousness, subjectivity, emotion, companion readiness, or electronic life.
