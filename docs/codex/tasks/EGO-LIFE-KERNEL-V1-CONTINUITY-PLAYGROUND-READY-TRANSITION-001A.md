# EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A

Status: `OPERATOR_AUTHORIZED_PHASE_A_PREREG_BANK__NO_READY_AUTHORITY_YET`

Auto-Remote-Anchor: `forbidden`

## 0. Operator authorization and phase boundary

The operator authorized this exact transition on 2026-07-15:

```text
授权起草并执行 EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A：
修复当前 V1 draft 的四项 contract blocker；建立双仓 machine-readable implementation
authorization 和 exact nonempty target allowlist；保持 enabled/default/mainline/runtime/
science/remote-anchor 全部关闭；通过 Claude Web staged-hash Red pre-check 和本地提交后，
再按子代理模式实施 V1。
```

This card does not self-grant implementation. The authorized sequence is
fail-closed and ordered:

```text
Phase A: bank the reviewed Ego V1 preregistration contract
Phase B: add an ITL machine-readable READY descendant route
Phase C: transcribe the committed ITL authority into Ego field by field
Phase D: implement only after both repos expose the exact target allowlist
```

Phase A changes no program state, route state, validator, runtime, product code,
or evidence result. A later phase may not cite Phase A as READY authority.

## 1. Problem definition

The V1 card exists only as an untracked worktree draft. ITL authority cannot pin
worktree bytes, and the draft contained four pre-code contract defects: cyclic
trace provenance, conflicting rollover order, an underdefined intervention
command, and live-V1 contamination risk in the immutable-V0 verifier tests. A
fifth conflict made Shuffle Provenance depend on opaque memory IDs while also
requiring ID-rename invariance.

The smallest safe action is to repair and bank the exact preregistration bytes
under an independent Claude staged-object review. It is invalid to skip directly
to READY or product code.

## 2. Current layer and lane

- Current layer: Layer 2, engineering evidence-governance and product contract.
- Lane: product/capability authorization control plane; no science execution.
- Mainline target: none / forbidden in Phase A.
- Enabled state: V1 remains `false`, default-off and non-mainline.
- Real trigger evidence: absent for V1. The separate V0 receipt remains
  `BANKED_RECOMPUTING_PRODUCT_TRIGGER` only.
- Claim ceiling: reviewed local preregistration card bank only.

## 3. Mandatory pins

Phase A is valid only at:

```text
Ego repo: D:\Project\AIProject\MyProject\Ego
branch: main
base HEAD: b852cedb1c1a31531a2f71e330e110539150c518
ITL reference HEAD: 619bff5fd9400bba00002af26f65ce73894a9dce
V0 immutable ancestor: 546e3639299d7b11b599df3d00645666a6953bac
route revision: EGO_VISIBLE_LIFE_PROXY_V0_CORE_ADOPTION_001A
route fingerprint: 2446c65920f96a9a49d9ae654a0f106e8fb0bcaf41e023d4405c46c083a0f005
```

Before mutation, the Ego worktree may contain only the task-owned untracked V1
draft. Any other dirty or staged path is a STOP.

## 4. First-principles bounded audit

- Real objective: establish a committed, falsifiable contract that can later
  authorize one V0-descendant continuity implementation without inventing a
  second core or evidence path.
- Strongest baseline explanation: a cue/clock FSM plus deficit/lookup/EMA tables
  can reproduce the visible behavior; product continuity is not mechanism
  evidence.
- Strongest invalidity reason: prose can claim authorization while machine state
  still forbids implementation, or a later implementation can exploit an
  underdefined hash/intervention contract.
- Framing falsifier: any Phase-A file claims READY/implementation authority,
  changes a route/runtime flag, or the staged bundle differs after review.
- Still insufficient: a banked card, clean review, or future green tests do not
  show memory causality, learning, initiative, agency, or subjectivity.
- Hard-coding/leakage: the card freezes an equal-access shortcut baseline, exact
  typed commands, noncyclic provenance and an ID-rename positive control.
- Zeno stop: after this single prereg bank, do not repair governance again unless
  Phase B produces the concrete executable authorization boundary.

## 5. Collision-before-collapse record

### Candidate A — begin code from the operator chat message

- Evidence: fast source diff.
- Cheap match: any unauthorized local edit.
- Leakage risk: total; machine targets remain empty.
- Smallest falsifier: session guard still reports implementation forbidden.
- Expected failure: unreviewed second authority path.

### Candidate B — edit only the draft header to authorized

- Evidence: an authorization string.
- Cheap match: prose-only promotion.
- Leakage risk: high; no committed pin or route transition.
- Smallest falsifier: ITL still reports `v1_implementation=false`.
- Expected failure: report self-consistency without control-plane effect.

### Candidate C — exact reviewed prereg bank, then additive route transition

- Evidence: committed Git-object card pin with nonrecursive review receipt.
- Cheap match: manual prose; blocked by staged blob/hash and direct-parent checks.
- Leakage risk: receipt or post-review byte drift; fail closed on either.
- Smallest falsifier: change one reviewed byte or add one path.
- Expected failure: review binding or exact-scope validation rejects the commit.

Selection: Candidate C. Phase A banks only the contract; Phase B/C own authority.

## 6. Hypothesis

If the repaired V1 contract, this transition card and its mutation scope are
bound to exact staged Git objects reviewed by an independent Claude session,
then a direct-child four-path commit can provide an immutable input for the ITL
READY transition without granting implementation prematurely.

Falsifier: any byte/path/parent mismatch, receipt recursion, missing review
binding, or READY/runtime/science field in Phase A.

## 7. Baseline, ablation, trace/replay and provenance requirements

- Baseline: a prose-only authorization with the same user-facing wording.
- Ablation/negative controls: missing receipt; extra staged path; changed reviewed
  blob; wrong base parent; `implementation_authorized=true` in the prereg card.
  Each must block the Phase-A claim.
- Trace/replay: recompute staged blob OIDs, raw blob-payload SHA-256, raw cached
  binary diff SHA-256 and the direct-parent changed-path set.
- Computed provenance: all hashes come from raw `git cat-file blob` and raw
  `git diff --cached --binary --no-ext-diff --full-index` bytes. PowerShell text
  normalization is not evidence.

## 8. Exact Phase-A mutation scope

The reviewed nonreceipt set is exactly:

1. `docs/codex/tasks/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A.md`
2. `docs/codex/tasks/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A.md`
3. `docs/codex/tasks/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A-MUTATION_SCOPE_PHASE_A.yaml`

After independent review, add exactly:

4. `docs/codex/tasks/EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-READY-TRANSITION-001A-PHASE_A_RED_REVIEW.json`

The receipt is excluded from its own review manifest. The Phase-A commit must be
the direct child of the pinned base and contain exactly these four paths.

## 9. Repaired preregistration contract

The V1 prereg must freeze before review:

- noncyclic `command_hash -> causal state -> trace_hash -> last_trace_hash` order;
- memory lineage by `source_command_hash`, with any resolved trace join report-only;
- pre-action episode rollover at ticks 9/17/... and no post-update rollover;
- exact command keys, trigger-source enum and intervention enum combinations;
- Shuffle Provenance ordering/seed independent of opaque memory IDs;
- exact future implementation target set of 20 paths, including
  `scripts/tests/test_verify_ego_life_core_v0_baseline.py` but not the V0
  validator itself.

The prereg card must remain:

```text
status = DRAFT_ONLY__IMPLEMENTATION_UNAUTHORIZED
execution_requested = false
implementation_authorized = false
authorized_implementation_targets = []
```

Phase B/C, not this prereg, will carry operator-authorized machine semantics.

## 10. Independent Claude Web Red pre-check

1. Stage only the three nonreceipt paths.
2. Build a bundle outside the repository containing the semantic manifest, raw
   staged diff and exact staged payloads.
3. Claude Web must return a distinct review/session ID, UTC time, exact bundle /
   manifest / diff hashes, `NO_BLOCKING_FINDINGS` or findings, and acknowledge
   the Phase-A claim ceiling.
4. Any blocking finding or post-review byte change stops the transition.
5. Add and stage `PHASE_A_RED_REVIEW.json` without changing reviewed objects.
6. Validate receipt, exact staged set and direct-parent contract before commit.

## 11. Acceptance gate

- all mandatory pins match;
- the repaired V1 card contains the exact contract fields and 20 target paths;
- receipt absent during independent review;
- Claude verdict is `NO_BLOCKING_FINDINGS` on the exact staged bundle;
- the final staged set is exactly four paths and passes `git diff --cached --check`;
- program-state integrity, route convergence and mainline clarity remain pass;
- no authority/runtime/product implementation file changes;
- local commit only; no push/tag/remote anchor.

## 12. Stop condition

STOP on pin/status drift, any non-task dirty path, any path expansion, card
ambiguity, Claude blocker, receipt mismatch, validator failure, need to edit a
route or product file in Phase A, or any requirement to push/tag/anchor.

## 13. Rollback plan

Before commit, remove only the three task-owned untracked nonreceipt files and
receipt if created; do not touch other user work. After commit, never reset,
amend or rewrite it. Any correction requires a separately reviewed additive
transition.

## 14. Forbidden changes

Every path outside Section 8; especially `docs/PROGRAM_STATE_UNIFIED.yaml`,
`docs/STATUS.md`, `TASK_LANE_INDEX.md`, validators, route artifacts, V0 product
code/tests, EgoOperator, EgoDesktop, LLM/network/runtime, science artifacts,
push, tag and remote anchor.

## 15. Local commit authorization

One exact four-path local Phase-A commit is operator-authorized only after every
gate above passes. Phase A does not authorize Phase-D code by itself.

## 16. Next minimal closed-loop action

After the clean Phase-A commit, create the separately reviewed ITL additive
READY descendant route pinned to the committed V1 card. Do not mutate or reopen
the adjudicated V0 adoption closure.

## 17. What this does not prove

This does not prove READY, implementation, product effect, continuity, learning,
memory causality, mechanism validity, initiative, agency, autonomy,
subjectivity, consciousness, electronic life, runtime/mainline effect, stable
user benefit or product value.
