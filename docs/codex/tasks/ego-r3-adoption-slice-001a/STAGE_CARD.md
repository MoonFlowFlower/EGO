# EGO-R3-ADOPTION-SLICE-001A — g_ablation loop adopts the R0 state/trace/replay contract (executable)

Version probe: R3-ADOPTION-SLICE-001A rev-A 2026-07-07 / kernel_adoption_v0 /
parity-safe value domain / leaky-renderer positive control / no-fork.

Status: EXECUTABLE / DEFAULT-OFF / NOT_RUNTIME_CONNECTED.
Parent: `ego-mechanism-rewrite-decision-001a` R3 row (binding: "adoption only
— adopt R0 serialized-state/replay substrate when R0 lands, and run the
LLM-swap invariance test from then on"; forking the in-flight lineage is
forbidden). Preconditions satisfied: `r0_substrate_pass` (R0, `bd9458b1`
lineage) and the R1 lineage completion recorded in PROGRAM_STATE (v0
`instrument_invalid_potency` cb94184 → repair 001A precheck negative
bec2895 → 001B battery pass 9978f64). Authorized by the R1 v2 card's
"Next actions on pass" item 1. Created 2026-07-07 (Claude draft; operator
authorizes; Codex lands).

## Problem definition

The EgoDesktop `joi_real_loop_g_ablation` lineage (5 frozen-surface JS
modules + tests) has its own trace/replay discipline but does not emit the
R0 kernel contract: no named/serialized/hashed substate envelope, no
in-state seed registry, no `kernel_state_v0`-compatible per-turn state
hashes, and no LLM-swap invariance enforcement. The decision card obliges
adoption, not rewrite. This slice makes the loop's harness runs emit and
satisfy the R0 contract — with ZERO behavior change to the loop itself.

Prior-negative-evidence constraints honored (crosswalk): E2 window-dominance
→ do not over-build (adoption is representational only); E4 → no new
mechanism claims (cache/graph-cache absorption); X3 / torch lesson → all
randomness through a recorded seed registry, fresh-process replay ×2;
tautology/leak lessons → every detector ships a positive control that CAN
fire.

## Layer

Engineering implementation / evidence hygiene (EgoDesktop carrier lane,
harness context only). First R-card allowed to touch `EgoDesktop/src`, and
only on the paths listed below.

## Scope / layout

```text
docs/codex/tasks/ego-r3-adoption-slice-001a/STAGE_CARD.md
docs/codex/tasks/ego-r3-adoption-slice-001a/MUTATION_SCOPE.yaml
docs/codex/tasks/ego-r3-adoption-slice-001a/SCHEMA_NOTES.md          # additive trace block + parity-safe value domain
EgoDesktop/src/joiRealLoopGAblationKernelStateAdapter.js             # NEW, the slice
EgoDesktop/src/joiRealLoopGAblationTraceRunner.js                    # ADDITIVE HOOK ONLY (see No-fork rules)
EgoDesktop/scripts/run-joi-g-ablation-kernel-adoption.js             # NEW runner -> artifacts
EgoDesktop/tests/joi_real_loop_g_ablation_kernel_adoption.test.js    # NEW tests
tests/test_ego_r3_adoption_parity.py                                 # NEW cross-language parity gate
artifacts/ego_r3_adoption_slice_001a/
```

READ-ONLY: `scripts/ego_kernel/**` (import `canonical_sha256` for parity
verification only; no modification), all prior task/artifact dirs, the other
four g_ablation modules (`Harness`, `OfflineReplay`, `ReplayEvaluator`,
`CalibrationReference` — byte-frozen in this card).

## Design (frozen at landing)

### A1 — Kernel-state adapter (`kernel_adoption_v0`)

- Wraps the loop's condition-relevant harness state OPAQUELY as substate
  `joi_loop_state_v0` inside an R0-compatible envelope
  `{schema_version: kernel_state_v0, task_id, run_id, episode_id, step_id,
  substates, seed_registry, ablations}`. No semantic reinterpretation, no
  new state content.
- Canonical serialization/hash MUST byte-match Python
  `scripts/ego_kernel/state.canonical_json_dumps` semantics
  (`sort_keys, ensure_ascii=False, separators(",",":")`) over the declared
  parity-safe value domain: object/array/string/bool/null/int; floats are
  NOT hashed raw — any non-integer numeric state value must be encoded as a
  fixed-format decimal STRING at the adapter boundary (rule recorded in
  SCHEMA_NOTES). Ex-ante reason: Python repr vs JS `JSON.stringify` float
  formatting divergence is a known cross-language hash landmine; restricting
  the domain is the honest fix, forking the canonicalization is forbidden.
- Seed registry: every RNG draw available to the harness run is routed
  through / recorded in `seed_registry`; harness runs remain
  `LLM_REPLAY_LOCKED` (no live LLM anywhere in this card).

### A2 — Additive trace extension

Adapter attaches one additive block `kernel_adoption_v0 = {state_before_hash,
state_after_hash, step_id, seed_context}` to each existing trace row.
Existing row fields, schemas, consumers, conditions, and verdict vocabulary
are untouched (no second schema; the block is documented in SCHEMA_NOTES and
is ignorable by all existing readers).

### A3 — Fresh-process replay + resume

`run-joi-g-ablation-kernel-adoption.js` executes a frozen fixture-pack
harness run (existing g_ablation replay fixture family; no new distribution,
no new packs), serializes the envelope per turn, then: fresh **node**
process replay ×2 from (serialized initial envelope + input log), plus one
mid-episode resume from the serialized checkpoint at `floor(turns/2)`. Zero
mismatch required over `(state_before_hash, state_after_hash,
output-relevant row fields)`.

### A4 — LLM-swap invariance (first enforcement, per R0 contract)

Two deterministic stub renderers A/B present IDENTICAL locked semantic
outputs with different surface text. Gate: kernel-state-attributed fields
(all `kernel_adoption_v0` hashes and the loop's state trajectory) are
byte-identical across A/B; renderer identity is recoverable ONLY from
surface text; kernel-field leak count == 0.
Positive control (unfailable-detector rule): a third, deliberately leaky
renderer C (writes its identity into a state-adjacent field) MUST be flagged
by the same leak detector. Detector blind to C = `instrument_invalid_leak_detector_blind`.

### A5 — No-fork rules (hard)

- The four frozen g_ablation modules: zero diff.
- `joiRealLoopGAblationTraceRunner.js`: one additive, optional,
  default-off adapter hook only; `REQUIRED_CONDITIONS`, `ALLOWED_VERDICTS`,
  `DIAGNOSTIC_CONDITIONS`, claim-ceiling strings, and all existing fields
  byte-unchanged; hook inert unless the adoption runner explicitly injects
  the adapter.
- All existing EgoDesktop tests and the repo verify suite green before ==
  after. Loop behavior identical: adapter is observation/serialization only.

## Frozen constants (threshold_source)

| constant | value | threshold_source (ex ante) |
|---|---|---|
| parity_vectors | 16 frozen adversarial vectors (unicode, nesting, ints incl. negatives and 2^53-1, bool/null, empty containers, decimal-string floats, CJK keys, key-order traps) | must cover the declared value domain and the known cross-language traps; file sha-pinned in config_frozen |
| parity gate | 16/16 hash equality JS↔Python | contract is byte-parity; anything less is a second schema |
| replay | fresh-process ×2 + resume @ floor(turns/2) | R0 acceptance contract discipline (X3) |
| swap leak floor | 0 kernel-field leaks; positive control C must fire | R0 llm-swap contract + unfailable-detector rule |
| episodes | 2 episodes × existing fixture-pack turn count | smallest run exercising resume + swap; no new distribution claims |
| guard | 1800 s total | pure local JS/python harness; generous versus expected <120 s |
| regression | full existing EgoDesktop test suite + `tests/test_joi_corpus_admission.py` + verify_repo fast/full green | no-fork proof |

`config_frozen.json` must byte-match this table (plus the parity-vector file
sha256). Mismatch = card violation.

## Acceptance gates (all predeclared)

- **G-R3A-PARITY**: 16/16 canonical-hash parity. Fail →
  `instrument_invalid_parity` STOP. Single permitted remedy round: narrow
  the declared value domain in SCHEMA_NOTES (never touch canonicalization on
  either side), rerun once; second fail → STOP final.
- **G-R3A-STATE-HASH**: same envelope ⇒ same hash across processes; mutated
  substate ⇒ hash changes (both controls must fire).
- **G-R3A-REPLAY**: ×2 fresh-process + mid-episode resume, zero mismatch.
- **G-R3A-SWAP**: A/B kernel fields identical, leak count 0, AND leaky
  renderer C detected.
- **G-R3A-NO-FORK**: zero diff on the four frozen modules; trace-runner diff
  = the single additive hook; full regression green.
- **G-R3A-SCHEMA**: additive-only block documented; corpus admission
  regression green.
- Hygiene: lint, py_compile (python test), verify_repo fast + full,
  default-off scan (adapter and runner referenced from harness/test context
  only; no main.js/viewer/preload wiring).

## Artifacts (evidence contract)

```text
artifacts/ego_r3_adoption_slice_001a/
  result.json                # verdict + failing_gates + per-gate provenance
                             # (producer_function, input_artifacts, run_id,
                             # seed/episode context, aggregation_rule,
                             # code_path_hash)
  config_frozen.json
  parity_vectors.json + parity_report.json
  trace jsonl per episode (with kernel_adoption_v0 blocks)
  replay_report.json
  swap_report.json           # incl. positive-control C result
  regression_report.json
  run_log.json               # exit code + duration + guard
  failure_manifest.json      # enumerating, on any fail
```

## Verdict vocabulary

`r3_adoption_slice_pass` | `r3_adoption_fail_<gate>` |
`instrument_invalid_parity` | `instrument_invalid_leak_detector_blind`.
`failing_gates` always lists every non-pass gate.

## Stop conditions

- parity fail after the single value-domain round;
- leak detector blind to positive control C;
- any replay/resume mismatch;
- any diff on the four frozen modules, or any non-additive trace-runner
  change, or any need to touch main.js / viewer / preload / chatTurn / PSPC
  / EgoOperator / gate / approval / transport / proactive paths → scope
  violation STOP;
- guard breach; any threshold/constant motion.

## Rollback

Revert this card's commits. The loop, its modules, prior artifacts, and all
existing verdicts are untouched by construction.

## Claim ceiling

`r3_adoption_engineering_only`. A pass means at most: "the in-flight
EgoDesktop g_ablation loop, in harness context, emits the R0
kernel_state_v0-compatible state/trace envelope with byte-parity canonical
hashing, passes fresh-process replay ×2 with mid-episode resume, and passes
LLM-swap invariance with a fail-able leak detector — default-off, no runtime
wiring." It re-adjudicates NO g_ablation verdict, transfers no joi-demo
result, and proves nothing about mechanism validity, prediction-error-loop
scientific status, learning, durable memory efficacy, runtime integration
safety, stable user benefit, live autonomy, functional selfhood, agency,
consciousness, subjective experience, or real emotion. No result flow
to/from ITL (firewall binding).

## Anti-tuning / governance

All constants above are frozen before any run exists; the landing commit
must be an ancestor of every implementation and scored-artifact commit.
Red fields here: the parity value-domain rule and the swap-leak contract
(both new measurement definitions, ex-ante sourced). Failures preserved; no
schema change to erase failure; no test-only logic paths; PROGRAM_STATE
entry for this card is written only AFTER its battery, per its outcome.

## Next actions authorized on pass

1. Operator MAY authorize wiring the adapter into the g_ablation lineage's
   own next card as its default trace format (that card, not this one,
   decides).
2. Nothing else. R2 keeps its own card path; D2 stays closed; live wiring
   stays blocked by the decision card.
