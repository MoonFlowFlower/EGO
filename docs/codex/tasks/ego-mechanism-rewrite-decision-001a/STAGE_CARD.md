# EGO-MECHANISM-REWRITE-DECISION-001A — Mechanism Rewrite Decision Card

Status: ACCEPTED_DOCS_ONLY / DECISION_RECORD / NO_CODE / NOT_RUNTIME_CONNECTED.
Created: 2026-07-06. Follows `JOI-DEMO-HISTORY-TO-EGO-REFERENCE-ADMISSION-001A`
(readback pass, `0a1bcaf5`) and `docs/RESEARCH_NEGATIVE_RESULTS_CROSSWALK_001A.md`.

## Purpose

Decide which mechanisms from the target component set are rewritten clean in
Ego, in what order, under what acceptance contracts — and which are
explicitly NOT rewritten. Target component set (operator's product goal, a
Joi-like functional electronic-life companion): kernel-owned internal state;
writable memory / personalization; prediction-error-driven update; controlled
initiative; self-boundary; social-emotion inference; replay/consolidation.

This card authorizes NOTHING to be implemented. Each admitted rewrite gets
its own bounded card later. This card fixes the decision so future cards
cannot silently reorder or re-scope.

## Lane ownership (anti-drift)

- Carrier lane for all rewrites: **EgoDesktop** (the desktop pet is the
  product carrier; its `joi_real_loop_g_ablation` lineage is the validation
  discipline these rewrites extend — no parallel gate system is created).
- **EgoOperator** operator-first runtime: untouched by this card and by all
  R-cards below.
- **PSPC** surfaces: remain shadow/default-off; not upgraded by this card.
- Per `docs/MAINLINE_QUICKSTART.md` do-not-reopen list: live proactive
  behavior / self-DM remain closed; R2 below is OFFLINE-SIMULATOR ONLY and
  its future card must restate this.

## Decision table

| # | Component | Decision | Evidence basis (crosswalk/corpus) |
|---|---|---|---|
| R0 | Kernel state substrate (serialized state, trace, replay harness) | REWRITE FIRST — engineering substrate, precondition for every gate | X1: non-replaceability must be engineered as access asymmetry; g_ablation replay discipline already proven in-lane |
| R1 | Writable memory + personalization, WITH ownership/write-protection (absorbs self-boundary engineering) | REWRITE SECOND — the only component where learning provably pays (drift exposure) | X2/E3: learning pays only under drift; E5: MINJA contamination real → quarantine from day 1; E6: self-boundary = access control engineering, zero grounding claims |
| R2 | Controlled initiative (route I) | REWRITE THIRD — offline user-simulator harness (roadmap v1 Part 8 T1 card), dual product+science value | Crosswalk §2: only first-tier route with zero negative evidence in either lab; T1 has built-in threshold-tuning kill |
| R3 | Prediction-error update loop | NO NEW REWRITE — the existing EgoDesktop g_ablation real-loop IS the carrier; it must ADOPT the R0 substrate when R0 lands | E2: window dominance — do not over-build; duplicating the in-flight lane = fork drift |
| D1 | Social-emotion inference (learned) | DEFERRED — keep the existing PSPC hardcoded/semantic-packet path; learned variant only if a future drift analysis shows hardcode failing | E7: self-report tautology trap; X2: in-distribution hardcode dominates |
| D2 | Replay/consolidation | DEFERRED — engineering-only concept (compaction, contamination defense, forgetting control); opens only after R1 shows real capacity pressure | E4: graph-cache absorbs mechanism claims; joi G1: thin headroom, route-economics hold |
| D3 | Self-boundary as standalone mechanism | NOT REWRITTEN — absorbed into R0 kernel API + R1 write-protection classes | E6/K1-K7: science line closed; engineering form only |

Order rationale: R0 unblocks all gates; R1 sits at maximum drift exposure
(the only place learned components can justify themselves per G-HARD logic);
R2 needs R0's harness and is the science flagship; R3 is already in flight —
this card forbids forking it.

## Cross-cutting component contract (binding on every R-card)

Every rewritten component ships AT CREATION (not retrofitted):

1. owned substate — named, serialized, hashed into the R0 state;
2. deterministic update rule given seed (all RNG frameworks seeded;
   fresh-process replay);
3. live ablation switch (reruns episodes; never post-hoc simulation);
4. trace fields + replay support under the R0 schema;
5. **hardcoded stand-in** — maintained fallback + G-HARD comparator: where
   the stand-in matches the learned version in-distribution, SHIP THE
   STAND-IN and record the choice (honest-headline enforcement, E3);
6. component battery: learned-vs-stand-in under drift, ablation collapse,
   replay check, relevant baseline family from the crosswalk (raw-RAG /
   lookup / graph-cache for memory; fixed-rule family for initiative);
7. claim ceiling in Ego house style; default-off until its own card's
   acceptance passes;
8. corpus regression where schemas overlap: result/trace shapes validate
   against `CORPUS_SCHEMA_CONTRACT.md` core fields via the admission tools.

## Acceptance contracts (frozen now; future R-cards may narrow, never widen)

### R0 — substrate
- Replay: behavior byte-reproducible from serialized state + input log in a
  fresh process ×2 (torch-lesson discipline, X3).
- State-causality smoke: same input stream, two different serialized states
  → behavior separates in the state-implied direction (extends g_ablation
  full-vs-frozen logic to the unified state).
- LLM-swap invariance harness EXISTS and runs (crosswalk §4): swapping LLM
  provider/prompt-style must not erase state-attributed behavior deltas;
  first enforced on R3's loop once it adopts R0.
- No mutation of EgoOperator runtime; EgoDesktop only.

### R1 — memory
- Contamination probe: MINJA-style poisoned external suggestion lands in
  quarantine; behavior unchanged unless kernel policy promotes it; promotion
  is traced and replayable.
- Personalization-under-drift: learned memory beats the hardcoded stand-in
  on drifted/user-shifted probes (pre-registered δ), while the stand-in may
  win in-distribution — both results recorded; G-HARD decides what ships.
- Baseline honesty: raw-RAG / lookup / graph-cache comparators run on the
  same traces; equivalence is recorded as equivalence (expected per E4;
  NOT a failure — it caps the claim at engineering value).
- Every write carries provenance (source, tick, trigger) sufficient for
  drift attribution from trace alone.

### R2 — initiative (offline simulator only)
- Environment: user-simulator with ground-truth opportunity labels o_t,
  receptivity, false-positive costs (roadmap v1 Part 3/8).
- Gate (pre-registered, CI non-overlap): learned gated-initiative net
  utility ≥ best of {always-silent, always-act, fixed-rate, best tuned
  single-threshold, behavior-tree} + δ; AND trigger-learning ablation
  destroys ≥ half the gain; AND logged trigger→downstream-transition shows
  interventions change trajectories.
- Pre-committed kill: tuned-threshold or behavior-tree tie within CI →
  route I closes as "no mechanism beyond threshold tuning"; behavior-tree
  ships as the cheap product solution; negative banked. No retune, no 002A
  rescue without a materially different, separately adjudicated design.
- Live wiring, notifications, self-initiated messages: NOT in scope of R2
  or its first card; requires a separate future card against the
  do-not-reopen list.

### R3 — adoption only
- The in-flight g_ablation lineage continues under its own cards; the only
  new obligation imposed here: adopt R0 serialized-state/replay substrate
  when R0 lands, and run the LLM-swap invariance test from then on.

## Claim ceiling

Decision-record only. Rewrites, once executed, can at most produce Ego-side
bounded engineering evidence: "learned, ablation-sensitive, replay-valid,
contamination-resistant components in a desktop companion." Nothing in this
card or its successors may claim mechanism validity, transfer of joi-demo
Bar-1 results to Ego scale, agency, autonomy, emotion, subjectivity,
consciousness, functional selfhood, EGO readiness beyond the recorded lane
scope, or stable user benefit. Route I positive at simulator scale claims a
control-flow property only (roadmap v1 L5-narrow wording), never initiative
"desire".

## Stop conditions (for this card's successors)

- any R-card attempts live proactive wiring → blocked by this card;
- any R-card ships a learned component without its hardcoded stand-in and
  G-HARD record → blocked;
- any attempt to port `stage1/*` / `battery/*` corpus code instead of clean
  rewrite → blocked (admission card boundary);
- R2 gate failure → execute the pre-committed kill, do not redesign the
  metric post hoc.

## What this does not prove

Nothing yet — it is a decision record. It does not prove the order is
optimal, that route I has headroom (it is merely untested), or that any
component will pass its battery.

## Next actions authorized by this card

1. Draft `EGO-R0-KERNEL-STATE-SUBSTRATE-001A` (first executable card).
2. Nothing else. R1 waits for R0 acceptance; R2 waits for R0 harness.
