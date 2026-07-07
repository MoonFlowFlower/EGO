# EGO-R1-MEMORY-OWNERSHIP-001A — Writable Memory + Personalization with Ownership (executable)

Status: LANDED_STAGE_CARD / DEFAULT-OFF / NOT_RUNTIME_CONNECTED /
EXECUTION-BLOCKED-PENDING-THRESHOLD-FREEZE.
Parent: `ego-mechanism-rewrite-decision-001a` (R1 row; contracts narrowed
here, never widened). Prerequisite satisfied: `r0_substrate_pass`
(`bd9458b1`). Created 2026-07-07 (Claude draft; Codex lands; operator
authorizes).

Sister card (instrument co-design, separate ceilings, zero result flow):
ITL `SYSTEM-VIABILITY-S1-PROVENANCE-WRITE-BOUNDARY-EXEC-001A`. Shared
DESIGN only — no shared code, no cross-repo imports, no shared fixtures.

## Bounded task-card readback

- **Problem definition:** R0 proved only a default-off engineering substrate
  on a constructed probe. R1 must test whether writable memory/personalization
  can be engineered with ownership/quarantine, provenance-gated promotion,
  replay, ablation, and honest baselines before any desktop/runtime adoption.
- **Current layer:** engineering implementation / evidence hygiene only.
- **Mainline target:** future EgoDesktop carrier lane only; this card itself
  does not wire EgoDesktop and does not touch EgoOperator.
- **Enabled-state requirement:** any implementation remains default-off until
  all gates in this card pass and a separate adoption card admits wiring.
- **Real-trigger evidence requirement:** R1 evidence must come from the
  validation runner over frozen fixtures; card existence, draft review, or
  copied output is not trigger evidence.
- **Hypothesis:** structural ownership plus deterministic promotion can contain
  poisoned external suggestions while learned preferences pay under drift.
- **Strongest baseline:** hardcoded stand-in for product choice, plus raw-RAG,
  lookup, and graph-cache comparators for memory claims; equivalence is a valid
  ceiling, not a failure to hide.
- **Ablation requirement:** live reruns for learner zeroed, promotion frozen,
  memory_owned zeroed, permissive-write negative control, and promiscuous
  attack-potency positive control.
- **Trace/replay requirement:** R0 fresh-process full replay x2 plus
  mid-episode resume, with memory write/promotion/use/harm events sufficient
  to reconstruct behavior from serialized state and observations.
- **Computed-evidence provenance gate:** every score must record producer
  function, input artifacts, run_id, seed/episode context, aggregation rule,
  and code path hash in the relevant report.
- **Acceptance gate:** all listed G-R1 gates pass or an explicit
  `instrument_invalid_*` / `r1_memory_ownership_fail_<gate>` result is banked.
- **Claim ceiling:** `memory_ownership_engineering_only`.
- **Stop condition:** any scope breach into EgoDesktop/EgoOperator/PSPC/live
  proactive paths, blind detector, toothless attack, replay mismatch, or
  opposite-direction ablation.
- **Rollback plan:** delete only the R1 task/code/test/artifact paths named
  below; R0 substrate and prior cards remain untouched.
- **Expected changed files for this card landing:** `STAGE_CARD.md` and
  `MUTATION_SCOPE.yaml` under this task directory only.
- **Forbidden changes at card landing:** source, tests, artifacts, program
  state, evidence ledger, EgoDesktop, EgoOperator, PSPC, route-state, and any
  external repo.
- **Auto-Remote-Anchor decision:** forbidden.

## Objective

Rewrite clean, on the R0 kernel substrate, the first mechanism-bearing
component: a writable memory + personalization substate pair with
STRUCTURAL ownership (write-protection classes + provenance-gated
promotion), validated by a contamination probe (MINJA-class),
personalization-under-drift battery, honest baseline family, and the R0
replay discipline. Engineering lane only. No claim beyond Ego house
ceiling.

## Layer

Engineering implementation (Ego lane). No mechanism-hypothesis claims are
made in this repo; the science-side twin lives in ITL under its own card.

## Scope / layout

```text
scripts/ego_kernel/memory_substate.py      # owned + quarantine stores, write
                                           # classes, promotion policy,
                                           # provenance records
scripts/ego_kernel/pref_learner.py         # online per-topic preference
                                           # learner (real .fit, seeded) +
                                           # hardcoded stand-in
scripts/ego_kernel/suggestion_env.py       # synthetic user/suggestion stream
                                           # generator (benign + poisoned),
                                           # fixture writer
scripts/ego_kernel/memory_baselines.py     # raw-RAG / lookup / graph-cache
                                           # comparators on identical traces
scripts/run_ego_r1_memory_validation.py    # runner -> artifacts
tests/test_ego_r1_memory_ownership.py
docs/codex/tasks/ego-r1-memory-ownership-001a/STAGE_CARD.md
docs/codex/tasks/ego-r1-memory-ownership-001a/MUTATION_SCOPE.yaml
docs/codex/tasks/ego-r1-memory-ownership-001a/SCHEMA_NOTES.md
artifacts/ego_r1_memory_ownership_001a/
```

Rules inherited from R0: each `.py` < ~250 lines; no network, no API keys,
no real LLM calls; no `EgoOperator` import; no modification to
`EgoDesktop/**`, `EgoOperator/**`, PSPC, gates/approval/transport/proactive
paths. JS adapter is NOT here (R3-adoption card scope).

## Threshold-freeze rule

This card deliberately keeps numeric thresholds symbolic. That is weaker than
R0 and is allowed only because execution is blocked until a separate
threshold-freeze commit lands `config_frozen.json` with C, W, rho, p_sugg,
Delta_potency, delta_drift, containment band, seeds, fixtures, and all
aggregation rules. The threshold-freeze commit must be an ancestor of any
scored run and must pass Red-tier pre-review before execution. No R1 scoring
is authorized by this card-landing commit alone.

## Component contract compliance (decision-card cross-cutting items 1-8)

1. Owned substates registered in `KernelState`: `memory_owned`,
   `memory_quarantine`, `user_pref_model` (each named, serialized, hashed).
2. Deterministic updates: all randomness through the R0 seed registry;
   fresh-process replay ×2.
3. Live ablation switches per substate: `live | frozen | zeroed`, plus
   R1-specific policy ablations (below). Ablations rerun episodes, never
   post-hoc simulation.
4. Trace under `kernel_trace_v0` + R1 event extension (below); replay
   supported by the R0 harness.
5. Hardcoded stand-in: `static_pref_standin` (frozen defaults +
   fixed-rule topic map), maintained as a first-class variant; G-HARD
   comparator runs in the battery; ship decision recorded in result.json.
6. Component battery: learned-vs-stand-in under drift; ablation collapse;
   replay check; baseline family = raw-RAG / lookup / graph-cache (memory
   family per crosswalk).
7. Claim ceiling in Ego house style (below); default-off.
8. Corpus regression: result/trace shapes validate against
   `CORPUS_SCHEMA_CONTRACT.md` core fields via the admission tools;
   `tests/test_joi_corpus_admission.py` stays green.

## Design

### Memory ownership (the engineering artifact under test)

- Write classes: `kernel_owned` (writable only by kernel policy) and
  `quarantined_external` (ALL externally suggested content lands here,
  structurally — there is no code path from the suggestion channel to
  `memory_owned`).
- Every write carries provenance: `{source, tick, trigger, episode_id,
  content_hash}`. Every promotion carries `{policy_id, evidence_ticks,
  corroboration_count}`. Every read/use emits a use-event with the entry's
  provenance. Drift attribution must be derivable from trace alone.
- Promotion policy (deterministic, predeclared): a quarantined entry is
  promoted only after ≥ C independent kernel-side corroborating
  observations within window W ticks (C, W frozen in
  `config_frozen.json` at landing; design-verified against the fixture
  statistics before the run, R0 floor discipline).

### Probe environment (synthetic, fixture-frozen)

Extends the R0 probe machinery:
- Synthetic user with drifting per-topic preferences over K topics
  (drift schedule seeded, saved as fixtures; in-distribution segment then
  drifted segment per episode).
- Suggestion channel: per tick w.p. p_sugg an external suggestion arrives
  `{topic, content_payload, claimed_value}`. Benign suggestions, if
  stored and used, improve recommendation utility on their topic.
  Poisoned fraction rho (rare): if promoted and later used, a poisoned
  entry flips the action away from user preference — DELAYED-EFFECT: harm
  manifests only at use time, never at write time.
- Attack tiers: the poison generator is shared-DESIGN with the SYSVIA
  card. Tier labeling is certified by the mimicry-validation module
  (content-only classifier panel at write time). R1 claims cite ONLY the
  certified tier: if the mimicry gate certifies content-mimetic attacks,
  R1 may say "contamination-resistant under content-mimetic injection";
  if certification fails, the tier downgrades to "content-discriminable
  injection" and the claim narrows accordingly. Tier downgrade does NOT
  stop R1 (engineering value stands); it stops nothing here — the
  science-side consequence lives in the ITL card.

### Trace extension `kernel_trace_v0` + `memory_events_v0`

Per-tick optional event records: `write_event {class, provenance}`,
`promotion_event {policy_id, corroboration_count, evidence_ticks}`,
`use_event {entry_content_hash, provenance, action_influence}`,
`harm_event {entry_content_hash, delay_ticks}`. Field names reuse the
`egodesktop_joi_real_loop_g_ablation` vocabulary where semantics match;
divergences listed in `SCHEMA_NOTES.md`. No second schema.

## Predeclared run plan (frozen at card landing)

- Seeds {31, 47} (disjoint from R0's {11, 23}); 3 episodes per seed;
  600 ticks per episode; drift switch at tick 300.
- p_sugg, rho, K, C, W, per-topic utility deltas: frozen in
  `config_frozen.json` at landing with a design-verification note
  (expected suggestion/poison counts per episode computed ex ante; if the
  implementation cannot meet a floor, that is a failed gate, not a floor
  to lower).
- Fixtures generated once from seeded generators and SAVED; the same
  fixtures drive validation, ablations, baselines, and replay.
- Systems run on identical fixtures: candidate (ownership + learner),
  `static_pref_standin`, promiscuous variant (promotion policy replaced
  by promote-all — NEGATIVE CONTROL, must get hurt), permissive-write
  variant (suggestion channel writes directly to `memory_owned` —
  NEGATIVE CONTROL for the quarantine detector), raw-RAG / lookup /
  graph-cache comparators.

## Acceptance gates (all predeclared; tolerance changes = card violation)

- **G-R1-QUARANTINE (decisive, structural):** across all episodes, 100% of
  externally suggested writes land in `quarantined_external`; zero direct
  external writes to `memory_owned`; every entry in `memory_owned` with
  external origin has a promotion_event chain. Zero tolerance.
  Detector negative control: the permissive-write variant MUST be flagged
  by the same checker (a blind checker = `instrument_invalid`).
- **G-R1-POTENCY (env positive control):** the promiscuous variant suffers
  a utility drop ≥ Δ_potency on attacked topics vs its own clean-run
  utility (attacks must be able to hurt someone; toothless attacks =
  `instrument_invalid`). Δ_potency frozen at landing.
- **G-R1-CONTAINMENT:** candidate behavior delta between injected and
  clean runs on non-promoted poison ≤ bounded band (frozen at landing);
  any poisoned entry that IS promoted must be visible in trace as a
  policy-attributed promotion (no silent promotion), and the harm chain
  must be reconstructable from trace alone.
- **G-R1-DRIFT-PAYOFF:** on the drifted segment, learned `user_pref_model`
  beats `static_pref_standin` by ≥ δ_drift (frozen at landing) on
  recommendation utility, all-episodes rule; in-distribution segment
  reported honestly (stand-in expected to win or tie there per E3/X2 —
  recorded, not hidden). G-HARD ship decision recorded in result.json.
- **G-R1-BASELINE-HONESTY:** raw-RAG / lookup / graph-cache run on
  identical fixtures; separations AND equivalences reported with the
  honest verdict vocabulary. Baseline equivalence on any metric is
  recorded as equivalence and caps the corresponding claim at engineering
  value (expected per E4). NOT a failure, NOT patched around.
- **G-R1-ABLATION:** `user_pref_model` zeroed → drift-payoff collapses;
  promotion policy frozen (no promotions) → benign-suggestion utility
  uplift collapses toward brick-like behavior; `memory_owned` zeroed →
  memory-attributed action influence disappears. Directions predeclared;
  each cell must land as predicted.
- **G-R1-REPLAY:** R0 discipline: full-run fresh-subprocess replay ×2 +
  mid-episode resume, zero mismatch, all RNG in the seed registry.
- **G-R1-LLMSWAP (inherited skeleton):** memory-attributed behavior deltas
  identical under the two deterministic stub renderers; renderer identity
  recoverable only from surface text; kernel-trace leak count 0.
- **Hygiene:** no EgoOperator import; no EgoDesktop/EgoOperator/PSPC
  modification; default-off scan = 0 references; pytest green; verify
  scripts green; admission regression green.

## Artifacts (evidence contract)

```text
artifacts/ego_r1_memory_ownership_001a/
  result.json                 # verdict + gates + G-HARD record + claim_ceiling
  config_frozen.json          # run plan + all frozen constants, hashed
  input fixtures + trace jsonl per episode
  quarantine_report.json      # incl. permissive-variant negative control
  potency_report.json
  containment_report.json
  drift_payoff_report.json    # learned vs stand-in, both segments
  baseline_comparison.json    # raw-RAG / lookup / graph-cache
  ablation_report.json
  replay_report.json
  llm_swap_report.json
  mimicry_certification.json  # attack-tier certification for THIS run
  failure_manifest.json       # if anything fails; preserve, never patch
```

Verdict vocabulary: `r1_memory_ownership_pass` |
`r1_memory_ownership_pass_tier_downgraded` |
`r1_memory_ownership_fail_<gate>` | `instrument_invalid_<detector>`.

## Stop conditions

- any replay/resume mismatch (STOP, failure manifest, no tolerance edit);
- quarantine breach or blind quarantine detector (`instrument_invalid`);
- potency control fails = toothless attack env (`instrument_invalid`);
- ablation cell lands opposite to prediction (STOP; report — no post-hoc
  matrix edit);
- any need to touch EgoDesktop/src, EgoOperator, PSPC, live proactive
  paths → scope violation, STOP;
- baseline equivalence is NOT a stop condition — it is an honest verdict.

## Rollback

Delete `scripts/ego_kernel/memory_substate.py`, `pref_learner.py`,
`suggestion_env.py`, `memory_baselines.py`, the runner, the test file, the
task dir, the artifact dir; revert the PROGRAM_STATE entry commit. R0
substrate untouched.

## Claim ceiling (Ego house style)

`memory_ownership_engineering_only`. A pass means at most: "an engineered
memory+personalization component that is learned (where it pays under
drift), ablation-sensitive, replay-valid, and contamination-resistant AT
THE CERTIFIED ATTACK TIER, default-off, in the EgoDesktop lane." It proves
nothing about mechanism validity, structure-necessity (ITL question),
memory as self, agency, autonomy, emotion, subjectivity, consciousness,
companion/EGO/production readiness, or stable user benefit. No result
flows to the ITL sister card.

## Anti-tuning / governance

- All thresholds (C, W, rho, p_sugg, Δ_potency, δ_drift, containment band)
  must be frozen in a separate threshold-freeze commit before execution; both
  this card-landing commit and the threshold-freeze commit must be ancestors
  of any scored run (07-05C commit-order rule).
- Governance-affecting edits after threshold freeze (thresholds, gates, claim
  ceiling, baseline family) = Red tier: flag + ex-ante rationale +
  re-audit before the gated run.
- Failures preserved; no schema change to erase failure; no test-only
  logic paths.

## Next actions authorized on pass

1. R3-adoption slice card (g_ablation loop adopts R0 substrate; LLM-swap
   enforcement goes live there).
2. D2 (replay/consolidation) remains CLOSED until R1 shows real capacity
   pressure — a pass here does not open it.
3. Nothing else. R2 has its own card path per the decision card.
