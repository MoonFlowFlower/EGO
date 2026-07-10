# EGO-K0 Foundation Route / Provenance Scope Repair Addendum

Addendum id: `ego_k0.foundation_route_provenance_scope_repair.v1`

Parent correction task:
`EGO-K0-FOUNDATION-EVIDENCE-ATOMICITY-CORRECTION-001A`

Repair task:
`EGO-K0-FOUNDATION-ROUTE-PROVENANCE-SCOPE-REPAIR-001A`

Status: AUTHORIZED ADDITIVE SCOPE REPAIR / OFFICIAL EVIDENCE BANK FORBIDDEN

Auto-Remote-Anchor: forbidden

## Problem definition

The already-banked correction task directory is a deterministic input to the
canonical route-view renderer, but its bank commit did not include the resulting
`TASK_LANE_INDEX.md` update. The existing Phase-B producer also treats raw
working bytes and a globally exact, globally clean ITL checkout as authority,
which is not portable across Git EOL materialization or unrelated ITL work.

This repair preserves the six-file atomic-persistence correction while making
the commit chain, generated route view, Git-content eligibility, and cross-repo
authority readback immutable and portable. It does not authorize an official
evidence-bank run.

## Current layer, mainline target, and enabled state

- Current layer: engineering implementation plus evidence/provenance integrity.
- Mainline target: none.
- Mainline integration: none; `mainline_connected=false`.
- Enabled-state requirement: remain disabled; `enabled=false` and
  `runtime_authority=none`.
- Real-trigger evidence requirement: the six preserved dirty Phase-B files, a
  focused callable test run, the deterministic route renderer, temporary-only
  producer trials, and mutation controls over Git/ITL object provenance.
- Official evidence bank: forbidden and `official_evidence_bank=false`.

## Bounded audit

- Real objective: retain the atomic event-plus-trace correction and produce an
  immutable commit chain that a future authorized evidence producer can verify.
- Strongest baseline: the only current route failure is an omitted generated
  dependency; this says nothing about whether K0 or persistence is effective.
- Strongest invalidity risk: another governance patch could form a Zeno chain
  without increasing discriminative evidence. This is the sole permitted scope
  repair. A further schema/scope repair stops the lane and requires route-level
  simplification.
- Falsifier: the canonical generator changes any file other than
  `docs/codex/tasks/TASK_LANE_INDEX.md`; the intermediate or final commit path set
  widens; clean-filter parity accepts a semantic mutation; or final route and
  provenance checks cannot both pass.
- Still insufficient: 27 focused tests, computed engineering gates, temporary
  producer output, or a local correction commit do not adjudicate Foundation
  final acceptance.
- Test classification: engineering/evidence integrity only; no mechanism test
  and no behavioral-resemblance test.
- Hard-coding/leakage check: verdicts remain derived from callable gate outcomes;
  object/blob/path pins are verified rather than self-reported.
- Local-optimum/Zeno check: no fourth repair card is permitted.
- Schema/second-path check: no second renderer, authority source, trace store,
  persistence path, replay path, or verdict resolver is authorized.
- Replay check: replay must continue to recompute from serialized state plus
  observation/source event; stored action or stored next state remains forbidden.
- Claim-inflation check: all results remain engineering-only and disabled.

## Hypothesis and strongest baseline

Hypothesis: if the generated route dependency is banked in one exact-scope
intermediate commit, Git eligibility is defined by attribute-aware blob parity,
and ITL authority is read from a frozen ancestor object whose route blob remains
unchanged at live HEAD, then the final six-file producer commit can verify an
immutable and portable chain without weakening semantic tamper detection.

Strongest baseline: exact raw-byte equality plus exact-live-HEAD/global-clean ITL
checks. That baseline is simpler, but rejects valid CRLF/LF materializations and
unrelated ITL descendants/files without adding authority evidence.

## Superseded topology only

This addendum supersedes only the original two-commit topology and related
source/ITL portability rules. The immutable linear chain is:

```text
1e25ddead74da9dad810622a657d82f03564091e
  -> fc2c9b1fa9bc3ef010592783d0a959b2aa4485a6
  -> 3404ff008e1920c4e3b6ee93408edaf308d6a975
  -> <route-provenance-scope-repair commit>
  -> <final six-file producer commit>
```

Each arrow means exactly one parent, not merely a matching first parent.

The intermediate route/provenance scope-repair commit is the direct child of
`3404ff008e1920c4e3b6ee93408edaf308d6a975` and changes exactly:

1. this addendum;
2. `ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_MUTATION_SCOPE.yaml`;
3. `docs/codex/tasks/TASK_LANE_INDEX.md`.

The final Phase-B commit is the direct child of that intermediate commit and
still changes exactly the original six Phase-B paths. No amend, merge commit,
history rewrite, push, tag, or remote anchor is allowed.

All atomicity, persistence, policy, probe, gate, threshold, seed, episode, step,
replay, verdict-resolution, and claim-ceiling semantics in the original task and
`ATOMIC_STEP_COMMIT_ADDENDUM.md` remain frozen.

## Mainline and authority sources

- Generated route-view authority: the existing callable renderer in
  `scripts/codex/route_convergence_common.py`, invoked by
  `scripts/codex/generate_route_convergence_views.py`.
- EGO committed-content authority: Git objects in the immutable chain above.
- ITL execution authority: the route JSON read from pinned commit
  `07c0f1f85a3c855511ff1610ec9629f8e94e89b1` at
  `artifacts/ROUTE-STATE-MACHINE-001A/routes/K0-DUAL-TRACK-SUPERSESSION-001A/state.json`.
- Frozen ITL route blob:
  `5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3`.
- Frozen route SHA-256:
  `ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37`.

No working copy, copied JSON, report, test fixture, or external trace sink becomes
a second authority.

## Portable source equality rule

1. Canonical committed bytes are the bytes of the verified Git blob.
2. Provenance records both raw working SHA-256 and canonical blob SHA-256.
3. Eligibility uses Git attribute-aware
   `git hash-object --path=<path> <path>` parity with the verified HEAD blob.
4. No ad-hoc newline normalization is permitted.
5. LF/CRLF representation differences are acceptable only when clean-filter
   parity holds; the raw mismatch and representation difference are recorded.
6. Any semantic content change must change clean-filter output and fail closed.
7. `code_path_hash` provenance records both a canonical Git-object aggregate
   hash and an executed-working aggregate hash without changing trace/replay
   schema or comparison fields.
8. EGO semantic cleanliness is computed from index/working Git diffs plus
   untracked-path checks. A representation-only porcelain status may be recorded
   but cannot override clean-filter and diff parity.

## ITL committed-object authority rule

1. The pinned authority commit must be an ancestor of live ITL HEAD.
2. The route blob at the pinned commit and live HEAD must both equal the frozen
   blob.
3. The producer reads and parses route authority from the pinned Git object, not
   the working file.
4. Any tracked, staged, semantic working, or untracked change at the authority
   path fails closed.
5. Unrelated ITL untracked paths and unrelated descendant commits are recorded
   as context but do not contaminate object-pinned authority.
6. The stable `execution_authority_hash` is derived from the frozen authority
   commit/blob/authorization plus verified ancestry and live-blob-equality facts;
   unrelated live-HEAD identity or unrelated status must not redefine authority.
7. If the pin is not inherited or the route blob/authorization changes, stop.

The known unrelated ITL path
`docs/codex/tasks/FORK-A-IIO-MCI-PREREG-001B.md` must be reported if present and
must not be described as clean or modified by this task.

## Ablation and mutation requirement

No mechanism ablation is authorized. Callable engineering mutations must cover:

- wrong intermediate commit, wrong/extra parent, and intermediate path-set drift;
- addendum, scope, or generated-index blob mismatch;
- canonical renderer/index tamper;
- `core.autocrlf=true` with LF blob and CRLF working materialization, proving
  clean-filter acceptance while recording raw-byte mismatch;
- semantic content mutation under the same Git configuration, proving failure;
- ITL pin not inherited, live route blob change, and authority-path dirtiness;
- unrelated ITL descendant/untracked context without authority contamination;
- every previously required gate-fail, blind-detector, producer-exception,
  rollback, throwing-sink, retry, and stored-action control.

## Trace and replay requirement

Trace and replay requirements are unchanged. Canonical trace rows come from the
SQLite outbox. Candidate behavior is recomputed from serialized state plus the
source observation/event. Stored actions and next states are comparison outputs,
not replay inputs. Original comparison fields and source sequence remain frozen.

## Computed-evidence provenance gate

The callable producer must verify and record:

- the full exact-parent chain and exact path sets above;
- pinned blobs and SHA-256 values for this addendum, its mutation scope, and the
  generated index at the intermediate commit;
- callable renderer equality with the pinned generated view at final HEAD;
- the original Foundation card, correction card, implementation commit, and ITL
  authority object pins;
- portable working/blob parity and both code-path hash forms;
- producer function, input artifacts, run/seed/context/episode IDs, aggregation
  rule, and code-path provenance;
- actual rerun gate outcomes and actual interventions for every mutation test.

Any unused frozen seed/context/counterfactual, unverified pin, or stored-result
replay blocks the evidence claim.

## Acceptance gate

Phase R is accepted only when the generator changes no path except the canonical
index; the staged set is exactly the three intermediate paths; the six Phase-B
files remain unstaged with their preflight SHA-256 values; route convergence,
fast verification, diff checks, and task-scoped closeout have no blocker other
than `push_pending` plus the declared dirty carryover; and committed-object
readback proves the exact parent/path/blob set.

Phase B is accepted only when the final exact-six-path commit is the sole child
of the intermediate commit, the full callable provenance and temporary producer
trial pass, the official artifact path remains absent, and post-commit checks
retain `foundation_task_final_acceptance=NOT_ADJUDICATED` and
`official_evidence_bank=false`.

## Claim ceiling

Additive generated-route-view synchronization, portable provenance enforcement,
Foundation atomic persistence, and evidence-producer engineering only.

## Stop condition

Stop without further repair if a new task directory is required; the generator
changes another file; program state, renderer/source, evidence ledger, runtime,
policy/probe/threshold/replay semantics, or ITL must change; the six preserved
files drift during Phase R; either commit path set cannot remain exact; semantic
tamper detection must be weakened; an official artifact is created; route and
formal provenance cannot both pass; or another schema/governance repair is
needed.

## Rollback plan

Before the intermediate commit, remove only the two newly authored repair files
and the generated index diff with an explicit manual patch while preserving the
six dirty files. After either commit, preserve history and use an additive
correction only; never amend or rewrite. No runtime rollback exists because no
runtime path is touched.

## Expected changed files

Intermediate route-scope commit only:

- `docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_ADDENDUM.md`
- `docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_MUTATION_SCOPE.yaml`
- `docs/codex/tasks/TASK_LANE_INDEX.md`

Final Phase-B commit only: the original six implementation-correction paths
enumerated in the adjacent mutation-scope file.

## Forbidden changes

Every path outside the exact phase path sets is forbidden, including
`docs/PROGRAM_STATE_UNIFIED.yaml`, route renderer/generator source,
`artifacts/evidence_ledger/**`, `Tasks/TASK_BOARD.yaml`,
`.codex/project_contract.yaml`, `EgoOperator/**`, `EgoDesktop/**`, all ITL files,
and `artifacts/ego_k0_foundation_001a/**`.

## What this does not prove

This repair does not prove Foundation final acceptance, mechanism validity,
learning, memory/replay contribution, transfer, initiative, mainline effect,
EGO readiness, agency, autonomy, subjectivity, consciousness, electronic life,
stable user benefit, or product readiness.
