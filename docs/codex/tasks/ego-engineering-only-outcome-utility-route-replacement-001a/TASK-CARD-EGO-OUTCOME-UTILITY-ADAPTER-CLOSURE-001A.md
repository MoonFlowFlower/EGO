# TASK CARD — EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A

Status: AUTHORIZED / CODEX-REPAIRED (Claude draft 2026-07-13; operator authorized route D; Codex repaired only execution-blocking evidence and publication defects before execution; Claude Yellow post-check remains required)
Tier: YELLOW (route closure / negative evidence banking; touches no threshold, no frozen spec, no positive claim)
Repo: Ego (package and admission-design route live there). ITL is NOT touched by this card.
Auto-Remote-Anchor: forbidden. One local scoped commit is authorized; push and tag are forbidden until the required Yellow post-check and a fresh operator publication decision.

## 1. Task id

EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A

## 2. Problem definition

The isolated outcome-utility package exists in the Ego repo, passes its own
functional tests, is not wired into EgoOperator, is disabled by default, has
no runtime callers of `observe_outcome()`, and has no grounded mapping from
runtime feedback to `outcome_micros`. Prior verdict (operator-reported,
2026-07-13 session):

    ADMISSION_DESIGN_BLOCKED__FEEDBACK_MAPPING_UNGROUNDED

This card decides the route, not the mapping: close the
"runtime feedback -> outcome_micros -> runtime utility learning" admission
route as a bounded analytic negative, with machine-readable evidence and
numeric reopen conditions.

### 2.1 Mainline and evidence boundary

- Mainline target: none; this is an additive route-closure bank only.
- Enabled-state requirement: the isolated package remains manually callable
  through its explicit CLI but has no EgoOperator runtime registration,
  enable flag, decision authority, or state owner.
- Real-trigger evidence requirement: none is claimed; the fact gate must
  confirm no EgoOperator import or runtime callsite.
- Acceptance signal: additive closure artifacts with callable analytic
  provenance, exact fact readback, a clean scoped local commit, and no prior
  artifact or runtime change.
- Anti-Zeno stop: one closure round only; no evaluator, label collection,
  adapter repair, mapping repair, or runtime experiment is authorized.

### 2.2 Collision record (pre-implementation)

1. Minimal implementation — map delivery/gate/tool statuses to integers.
   Evidence: state updates and deterministic traces. Strongest cheap baseline:
   the same hand-written status table. Leakage/hard-coding risk: decisive,
   because operational completion is not user value. Smallest falsifier: two
   outcomes with the same status but opposite explicit task outcome. Expected
   failure: fabricated utility semantics. Decision: reject.
2. Strongest baseline / shortcut — equal-access context-action count table or
   static lookup. Evidence: the same empirical means used by the isolated
   package. Strongest cheap baseline: the package's own context/action cell
   representation. Leakage risk: context/action identifiers can become a
   lookup key. Smallest falsifier: held-out context/action transfer that a
   frozen equal-access table cannot match. Expected failure: baseline identity
   or equivalence. Decision: blocking baseline.
3. Mechanism-faithful implementation — randomized epsilon-abstain with an
   independently scored actual/no-action comparison. Evidence: a causal C2
   estimate. Strongest cheap baseline: randomized no-action plus the same
   evaluator and an equal-access count table. Leakage risk: evaluator or
   post-hoc judge leakage. Smallest falsifier: failure to reach the frozen
   power contour before drift, or equality to the table control. Expected
   failure: insufficient traffic/product tolerance or baseline equivalence.
   Decision: reopen-only, not executable now.
4. Selected approach — bounded closure. It preserves the isolated package and
   negative evidence, adds no runtime path, and returns resources to the
   separately authorized capability work.

## 3. Current stage

Engineering implementation + mechanism-hypothesis governance (route closure).
No mechanism is being run. No learning claim is being made.

## 4. Hypothesis (closure grounds; both must be recorded)

- Ground A — counterfactual unidentifiable at current access.
  `score_no_action` is an interventional quantity (C2 on the causal-claim
  ladder). The three candidate sources are: (i) counterfactual simulator —
  does not exist for the live runtime; (ii) judge-imagined counterfactual —
  a post-hoc classifier; its amortization ("ask the judge at decision time")
  is itself the stronger baseline, so any utility learner distilling it dies
  by amortized-shadow; (iii) randomized epsilon-abstain — the only
  C2-valid source among these candidates. The power annex is a conditional
  reopen calculation, not measured traffic: the frozen contour is
  eps*(1-eps)*D >= 7.27 (e.g. D >= 81 eligible decisions/day at eps=0.10)
  for five equal-traffic strata, d=0.3 and a 60-day drift window. If current
  traffic is unknown, no empirical infeasibility claim is allowed. The route
  remains closed because the required intervention/evaluator evidence is
  absent, not because unknown traffic is asserted to be low.

- Ground B — the groundable variant is baseline-pre-empted.
  A subset is groundable without a judge only when a preregistered
  programmatic evaluator scores the executed result and explicitly defines
  no-action as zero; verifiability alone does not imply that zero point. On
  such a subset, the current package's learnable object is exactly a
  context/action outcome-sum and observation-count table, so an equal-access
  count_table / lookup implementation is an identity-class control rather
  than evidence for a distinct learning mechanism. Per
  LEARNING-SUCCESS-CRITERION-STANDARD-001A, this route cannot support a
  learning/mechanism claim without a predeclared held-out separator that
  defeats the equal-access control; no such separator or consumer exists.

Prior negative evidence to cite (Codex resolves exact repo paths/commits on
host; do not fabricate; mark chat-provenance where no repo record exists):

- UNCERTAINTY-VOI-001A -> 002A -> 003A lineage, terminal verdict
  STATIC_SUFFICIENT (tuned static matches learned VOI; ITL, commits around
  b05fbac0 / 8968b2e / e54e8e2b / 8d8944ce / 67edff12 — verify on host).
- EGO-PET-INTEGRATION-001A P0 STEP4 hostile audit:
  HIGH_SCORE_NO_ATTRIBUTION, observe=oracle (Ego, audit 6948427a, STEP4
  46d0daa2) — precedent that Ego runtime signals used as feedback leak.
- ITL contracts: LEARNING-SUCCESS-CRITERION-STANDARD-001A,
  BASELINE-IMMUNITY-ADMISSION-STANDARD-001A,
  MECHANISM-SIGNATURE-VERDICT-STANDARD-001A
  (docs/codex/contracts/ — existence confirmed 2026-07-13; cite as paths,
  read-only).
- Causal-claim ladder C0-C3 (counterfactual/interventional claims require
  intervention; amortized-shadow hole) — cite wherever recorded in repo
  standards; otherwise mark as operator-standard, chat provenance.

Parent-record rule: the blocked verdict is not banked in Ego. If the external
local admission contract exists, parse it, record its absolute path and
SHA-256 as `external_local_uncommitted`; otherwise use
`chat_provenance_2026-07-13`. Neither form is a remote or git anchor. A
conflicting banked Ego record remains S2.

## 5. Baseline

No comparison run is authorized because this card makes no mechanism claim.
The strongest baseline is the equal-access context/action count table, which
is the same representation class as the isolated package. The closure must
record this as structural baseline pre-emption, not as a computed superiority
or empirical equivalence result.

## 6. Ablation

Not applicable (no mechanism run). Narrowed by this card.

## 7. Trace / replay requirement

- `power_annex.py` is closed-form, RNG-free, no timestamps in artifacts.
- Before banking, the artifact copy receives a provenance repair
  (producer_function, input-artifact hash, run_id, N/A seed/context/episode
  IDs, aggregation rule, and code_path_hash) plus one wording-only correction
  in the explanatory comments and `key_reading`: context stratification can
  fund the current context/action count table and its equal-access control
  alike; it does not by itself create learner headroom. Constants, formula,
  grids, assertions, and numeric claims must not change.
- Run twice; `power_annex.json` sha256 must be byte-identical across runs.
- The following digest is for the un-repaired Claude attachment and is
  provenance-only, not an expected digest after the metadata repair:
  ca559207245b505a9871aa1f46622b0c50fc183c3a11752734edb3610c17d059
- Spot checks are asserted inside the script; any assertion failure is a
  STOP (see S3), not a number to adjust.

## 8. Acceptance gate

- G1 (facts at HEAD, recorded with raw grep output + HEAD sha):
  a. Python callsites of `observe_outcome(` outside the package and its
     focused tests = 0. Documentation signatures are recorded separately and
     are not callers; the exact source-only command and raw output are saved;
  b. runtime enable flag / registration is absent, the only executable entry
     is the explicit local CLI, and the frozen functional contract records
     `enabled=false`; do not invent a flag name;
  c. consumers of the package's utility output in EgoOperator = 0;
  d. rough current eligible-decision traffic: recorded from logs if any
     exist, else recorded explicitly as "no runtime logs; operator estimate
     <value or unknown>". No fabricated traffic numbers.
- G2: power annex runs twice, identical sha256, internal spot-check asserts
  pass (pooled 32.3d and stratified 161.5d at D=30/eps=0.10/d=0.3; contour
  7.27; min D 81 at eps=0.10), and contains the required computed-evidence
  provenance fields. The annex is a conditional analytic bound, not a
  measurement or a claim that current traffic is below the contour.
- G3: closure.md contains: both grounds; resolved prior-evidence citations
  (or explicit chat-provenance markers); the three reopen conditions with
  the numeric contour; the claim ceiling verbatim; and the parent record's
  exact provenance class (`repo`, `external_local_uncommitted`, or `chat`).
- G4: result.json complete (schema in Codex instruction), with
  `"positive_claim": false` and the claim-ceiling string verbatim.
- G5: git scope clean — only the authorized paths added; porcelain clean
  before and after; single scoped local commit; no prior artifact modified;
  no push or tag before Yellow post-check.

## 9. Claim ceiling (verbatim in result.json and closure.md)

Bounded negative admission-design evidence only: the runtime feedback ->
outcome_micros mapping for the isolated outcome-utility package is closed as
unidentifiable at current observational access and baseline-pre-empted for
the current count-table package. The power contour is conditional because
current eligible-decision traffic is unknown unless live logs prove it. This
does not prove the utility mechanism is impossible in other regimes, does
not prove the product never needs utility signals, and proves nothing about
runtime learning, decision improvement, user value, mainline effect,
subjectivity, or consciousness.

## 10. Reopen conditions (write verbatim into closure.md)

- R1: a sustained programmatically-verifiable task stream with a
  preregistered evaluator that explicitly defines the no-action zero point,
  satisfying
  eps*(1-eps)*D >= 7.27 under the frozen 60-day drift window, AND a new card
  that pre-declares count_table / lookup / no-update controls and beats them
  per MECHANISM-SIGNATURE-VERDICT-STANDARD-001A.
- R2: true randomization infrastructure with recorded operator consent to
  epsilon-abstain product degradation, satisfying the same contour.
- R3: multi-user deployment providing external A/B ground truth; power
  re-derived from measured traffic in a new card.

Reopen never edits this closure; it opens a successor card citing it.

## 11. Stop conditions

- S1: any G1 fact contradicts the premise (a real runtime caller, runtime
  registration/enablement, or mainline consumer exists) -> STOP, bank nothing, report
  premise failure to operator.
- S2: a prior banked repo record conflicts with the operator-reported
  blocked verdict -> STOP, report the conflict (ledger-vs-report rule);
  do not pick the convenient source.
- S3: power-annex assertion failure or hash mismatch across the two runs ->
  STOP, report numbers; do not tune constants.
- S4: any git anomaly (unexpected dirty files, no-delete violation,
  forbidden path in staging) -> STOP.

## 12. Rollback plan

Single scoped commit; rollback = `git revert <commit>`. No prior artifacts
are touched, so no other restoration is needed. If stopped before commit,
delete only the new unstaged files created by this card.

## 13. Scope

Expected changed files (Ego repo only; final root resolved by Codex to match
the existing pet/capability lineage layout — do NOT invent a new governance
tree):

- docs task card copy: TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md
- task-local closeout scope: CLOSURE_MUTATION_SCOPE.yaml
- artifacts/EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A/
    result.json
    closure.md
    build_closure_result.py
    power_annex.py
    power_annex.json
    power_annex.md
    fact_grep_evidence.txt
    failure_manifest.json (only if a stop condition fires)
- at most ONE line/state update in the EXISTING program-state / stage
  tracking doc if this route is already tracked there (no new tracking doc).

Resolved path for this execution:
`docs/codex/tasks/ego-engineering-only-outcome-utility-route-replacement-001a/TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md`.
The live program-state file contains no entry for this route, so STEP 4 is
not authorized and `docs/PROGRAM_STATE_UNIFIED.yaml` must remain unchanged.

Forbidden changes:

- the outcome-utility package source, its tests, its flags/defaults
- EgoOperator mainline code, config, schemas
- any prior artifact or audit record (no rewrite, no delete)
- ITL repo (this card does not touch it)
- any threshold, frozen spec, or governance contract

## 13.1 Computed-evidence provenance gate

Every numeric annex row must be produced by the callable `build()` path and
the annex must record: `producer_function`, `input_artifacts`, `run_id`,
seed/context/episode IDs (explicitly N/A), `aggregation_rule`, and
`code_path_hash`. The local double-run recomputes the artifact from the
script; no literal verdict or copied digest is accepted as evidence.
The closure verdict and `result.json` must be emitted by the callable
`build_closure_result.build_result` gate over live git facts, parent verdict,
frozen contract, source integrity, annex recomputation, and closure content;
a hand-written result or verdict is forbidden.
The task-local `CLOSURE_MUTATION_SCOPE.yaml` exists only to let the repo's
closeout guard classify these exact additive paths; it does not authorize
Program State, task-board, evidence-ledger, runtime, package, push, or tag
changes.

## 13.2 Publication decision

Local commit: authorized after all gates pass. Push/tag/remote anchor:
forbidden in this execution because Claude Yellow post-check is still
pending. A later explicit operator decision may publish the reviewed commit;
publication would not upgrade the claim ceiling.

## 14. What this does not prove

No statement about runtime learning, decision improvement, user value,
mechanism validity in other access regimes, product need for utility,
mainline effect, agency, subjectivity, or consciousness. The annex numbers
are analytic bounds over declared assumptions, not measurements.
