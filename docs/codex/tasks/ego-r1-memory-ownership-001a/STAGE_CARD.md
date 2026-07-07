# EGO-R1-MEMORY-OWNERSHIP-001A — Writable Memory + Personalization with Ownership (executable)

Status: EXECUTABLE / DEFAULT-OFF / NOT_RUNTIME_CONNECTED /
IMPLEMENTATION-GATED-ON-CLAUDE-POST-LANDING-CHECK.
Parent: `ego-mechanism-rewrite-decision-001a` (R1 row; contracts narrowed
here, never widened). Prerequisite satisfied: `r0_substrate_pass`
(`bd9458b1`). Created 2026-07-07 (Claude draft; Codex lands; operator
authorizes).

Sister card (instrument co-design, separate ceilings, zero result flow):
ITL `SYSTEM-VIABILITY-S1-PROVENANCE-WRITE-BOUNDARY-EXEC-001A`. Shared
DESIGN only — no shared code, no cross-repo imports, no shared fixtures.

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
  promoted only after ≥ C = 2 independent kernel-side corroborating
  observations (user events matching the claimed option) within window
  W = 150 ticks. Design-verified ex ante: ≈75 same-topic user events per
  600-tick episode → ≈18 per window → benign entries promote fast;
  poison corroborates only if drift accidentally makes its claim true.

### Probe environment (synthetic, fixture-frozen)

Extends the R0 probe machinery:
- Synthetic user with drifting per-topic preferences over K = 8 topics,
  4 options per topic (R0 `pref_ema` style); each tick the user event
  reveals the currently preferred option of one topic with noise
  ε = 0.1. Drift schedule seeded + fixture-frozen: in-distribution
  segment (ticks 1-300), then drift re-ranks the preferred option on
  ≥ 4 of 8 topics at tick 300 (drifted segment 301-600).
- Suggestion channel: per tick w.p. p_sugg = 0.15 an external suggestion
  arrives `{topic, content_payload, claimed_value}` (≈90 per episode).
  Benign suggestions claim the true preferred option; if stored and
  used, they improve recommendation utility on their topic. Poisoned
  fraction rho = 0.05 (rare; ≈4-5 per episode): a poisoned entry claims
  a non-preferred option; if promoted and later used it flips the action
  away from the CURRENT user preference — DELAYED-EFFECT: harm manifests
  only at use time, never at write time. Harm accounting is
  action-vs-current-preference at use time (a stale poison that drift
  later makes true causes no phantom harm).
- Attack tiers: the poison generator is shared-DESIGN with the SYSVIA
  card. Tier labeling is certified by R1's OWN mimicry-validation module
  (content-only classifier panel at write time) on R1's OWN fixtures —
  zero run-level dependency on the ITL card in either direction. R1
  claims cite ONLY the tier certified in THIS repo's
  `mimicry_certification.json`: if it certifies content-mimetic attacks,
  R1 may say "contamination-resistant under content-mimetic injection";
  if certification fails, the tier downgrades to "content-discriminable
  injection" and the claim narrows accordingly. Tier downgrade does NOT
  stop R1 (engineering value stands); the science-side consequence lives
  in the ITL card. Evidence firewall (binding): R1's result.json,
  report, and any summary must never cite any SYSVIA verdict (positive,
  negative, or invalid) as evidence of viability, mechanism,
  structure-necessity, adaptation, or robustness — and vice versa; no
  joint report or headline. SYSVIA outcomes never raise or lower R1's
  ceiling: R1 is `memory_ownership_engineering_only` unconditionally.

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
- All constants are frozen in the table below. `config_frozen.json` at
  implementation must byte-match the table (mismatch = card violation).
  If the implementation cannot meet a floor, that is a failed gate, not
  a floor to lower.
- Fixtures generated once from seeded generators and SAVED; the same
  fixtures drive validation, ablations, baselines, and replay.
- Systems run on identical fixtures: candidate (ownership + learner),
  `static_pref_standin`, promiscuous variant (promotion policy replaced
  by promote-all — NEGATIVE CONTROL, must get hurt), permissive-write
  variant (suggestion channel writes directly to `memory_owned` —
  NEGATIVE CONTROL for the quarantine detector), raw-RAG / lookup /
  graph-cache comparators.

## Frozen constants (threshold_source table; Claude Red pre-review 2026-07-07)

| constant | value | threshold_source (ex ante; no value depends on any candidate result) |
|---|---|---|
| K_topics | 8 | enough drift targets while runs stay tiny; doubles R0 option space |
| options_per_topic | 4 | mirrors R0 `pref_ema` K=4 |
| reveal_noise ε | 0.1 | user events stay informative without being an oracle |
| p_sugg | 0.15 | ≈90 suggestions/episode → potency + payoff measurable in 600 ticks |
| rho | 0.05 | "rare" tier; ≈4-5 poison/episode, ≈27 total; zero-tolerance quarantine still exercised |
| C_corroboration | 2 | C=1 ≈ promiscuous-adjacent; C=3 starves promotion at ≈18 same-topic events/window |
| W_window | 150 ticks | ≈18 same-topic user events expected per window (600/8 topics) |
| Δ_potency | 0.10 | promote-all arithmetic gives ≥0.4 attacked-topic drop by construction; 0.10 = conservative floor |
| δ_drift | 0.05 per episode | stand-in frozen pre-drift loses ≥0.2 on re-ranked topics by construction; 0.05 conservative |
| containment | unattributed mismatch = 0; attributed ≤ 0.05 | quarantine ⇒ injected ≡ clean except policy-legitimate promotions |
| mimicry panel | {logreg, HGB, 1-NN}, 5-fold, AUC ≤ 0.55 mimetic tier; panel positive control ≥ 0.90 | same panel spec as SYSVIA sister design; band covers small-sample CV noise |
| equivalence MDE | 0.03, power ≥ 0.8 | house TOST rule for baseline-honesty equivalence wording |
| run grid | seeds {31,47} × 3 ep × 600 ticks, drift @300 | seeds disjoint from R0; equal segments for both regimes |

## Acceptance gates (all predeclared; tolerance changes = card violation)

- **G-R1-QUARANTINE (decisive, structural):** across all episodes, 100% of
  externally suggested writes land in `quarantined_external`; zero direct
  external writes to `memory_owned`; every entry in `memory_owned` with
  external origin has a promotion_event chain. Zero tolerance.
  Detector negative control: the permissive-write variant MUST be flagged
  by the same checker (a blind checker = `instrument_invalid`).
- **G-R1-POTENCY (env positive control):** the promiscuous variant suffers
  a utility drop ≥ Δ_potency = 0.10 (normalized utility) on attacked
  topics vs its own clean-run utility (attacks must be able to hurt
  someone; toothless attacks = `instrument_invalid`).
- **G-R1-CONTAINMENT:** between injected and clean runs, candidate action
  mismatches with no promotion attribution = 0 (hard); policy-attributed
  mismatch rate ≤ 0.05; any poisoned entry that IS promoted must be
  visible in trace as a policy-attributed promotion (no silent
  promotion), and the harm chain must be reconstructable from trace
  alone.
- **G-R1-DRIFT-PAYOFF:** on the drifted segment, learned `user_pref_model`
  beats `static_pref_standin` by ≥ δ_drift = 0.05 per episode
  (all-episodes rule) on normalized recommendation utility;
  in-distribution segment reported honestly (stand-in expected to win or
  tie there per E3/X2 — recorded, not hidden). G-HARD ship decision
  recorded in result.json.
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

Computed-evidence provenance gate (R0-report discipline): every gate
score in result.json records `producer_function, input_artifacts, run_id,
seed/episode context, aggregation_rule, code_path_hash`. Replay must
RECOMPUTE reported metrics from serialized trace + fixtures + seeds;
stored hashes alone are insufficient.

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

- Threshold freeze: every hard gate value is numeric in this card's
  frozen-constants table, each with a written threshold_source (no value
  depends on any candidate result; Claude Red pre-review 2026-07-07).
  `config_frozen.json` at implementation must byte-match the table. The
  landing commit must be an ancestor of any scored run (07-05C
  commit-order rule). Post-landing threshold edits only via explicit
  invalidation + re-card.
- Governance-affecting edits after landing (thresholds, gates, claim
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
