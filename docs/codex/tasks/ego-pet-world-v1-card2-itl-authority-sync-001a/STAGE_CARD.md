# EGO-PET-WORLD-V1-CARD2-ITL-AUTHORITY-SYNC-001A

Status: `PHASE_A_TASK_CARD_BANK_AUTHORIZED__PHASE_B_REQUIRES_INDEPENDENT_RED_REVIEW`

Auto-Remote-Anchor: forbidden

## Problem definition

Ego currently exposes a self-authored generic Card 2 bank binding while the
committed ITL route object at
`cb6cd57b8405bbac378f2857766ddaf63e08e194` defines the controlling exact
action, four consumption dependencies, an action-specific path policy, a
zero-science firewall, and a committed Phase-B Red-review receipt. This task
banks and then performs one field-by-field authority sync so Ego consumes that
committed ITL route without creating a second control plane.

The task closes only these four consumption dependencies:

- `EGO_FIELD_BY_FIELD_AUTHORITY_SYNC_BANKED`
- `ACTION_SPECIFIC_PATH_POLICY_ENFORCED`
- `LINEAGE_OMISSION_POSITIVE_CONTROL_ENFORCED`
- `COMMITTED_RED_REVIEW_RECORD_BOUND_TO_DIFF`

It does not bank or execute Card 2.

## Current layer

Layer 2: engineering evidence-governance / cross-repo synchronization only.
This is not a runtime, product-program, experiment, mechanism, learning, or
subject-validation task.

## Mainline target

`none / forbidden`. This is a governance-consumer sync. Product/capability
mainline wiring and science/evidence-lane execution are forbidden.

## Enabled-state requirement

- Card 2 execution remains `false`.
- All implementation, runtime, mainline, experiment, scoring, mechanism,
  theory-pressure, and science-successor authorizations remain `false`.
- `authorized_implementation_targets` remains `[]`.
- No runtime or product path is enabled by this task.

## Real-trigger evidence requirement

No runtime trigger is permitted. The only admissible trigger evidence is
callable governance recomputation from committed Git objects, actual changed
paths, a frozen independently discovered lineage universe, mutation controls,
and committed diff-bound Red-review records.

## Hypothesis

If Ego stores only an exact, validator-checked transcription of the committed
ITL route and receipt, derives effective action availability from that source
plus locally recomputed dependency gates, and infers execution from actual
changed paths, then a later separate Card 2 banking task can be admitted only
to its task-document path while Card 2 execution and every science/runtime path
remain fail-closed.

## Strongest baseline

A docs-only statement or a validator that trusts self-declared booleans can look
consistent while still allowing a broad mutation scope, omitted lineage, or an
unbound review string. That baseline is insufficient because it does not bind
the consumed authority to committed ITL bytes or to the actual committed diff.

## Ablation requirement

Callable mutations must reject, at minimum:

1. an ITL source blob or field transcription drift;
2. an omitted crosswalk leaf;
3. a Card 2 bank scope that admits `EgoOperator/`, `EgoDesktop/`, runtime,
   kernel, experiment, tests, scripts, or evidence paths;
4. a missing mutation scope;
5. an execution attempt inferred from actual changed paths even when a declared
   boolean says `false`;
6. a Red-review receipt with only a non-empty reference, a wrong base, wrong
   path set, wrong diff SHA-256, or non-committed provenance;
7. a lineage universe with one independently discovered row omitted;
8. a nonzero science weight, old-S0X satisfaction, science-successor
   authorization, or non-empty implementation targets.

## Trace / replay requirement

Runtime and mechanism replay are forbidden. Governance replay must:

- reread the pinned ITL blobs with `git cat-file`;
- recompute the field crosswalk and compare every leaf;
- rediscover the frozen lineage universe independently of Program State rows;
- recompute actual changed paths and Red-review diff binding;
- regenerate existing route views and compare them byte-for-byte.

## Computed-evidence provenance gate

Every governance verdict must identify a callable producer, input artifacts,
run ID, aggregation rule, and code-path hash. The ITL source objects are:

- route state `8b2db13a023873775b80bfe4e8eab7e53a7bba62`;
- events `29e28c15bc3dd6d04b7dd5b892cb70f205540e2a`;
- admission report `f5c58e4d4cfb8b734e5e339845ddb4d0a3e3c5b5`;
- Phase-B review receipt `08b9d3ccef6418a7d4722bd62ad7130317f3b845`;
- Phase-A task card `9859765cd20044568f093c6c9579c37014f8ee21`
  from commit `f77187970786b27e85d93200a37ff427c2e3c243`.

Static PASS dictionaries, self-reported lineage rows, and self-declared
execution booleans are forbidden evidence.

## ITL field readback (verbatim values from the committed route object)

### allowed_next_actions

1. `sync_EGO_pet_world_v1_card2_bank_admission_under_separate_task`
2. `bank_EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A`
3. `run_route_state_machine_validation`

### forbidden_next_actions

1. `execute_EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A`
2. `start_capability_implementation`
3. `start_experiment_execution`
4. `start_scoring`
5. `enable_runtime_or_mainline`
6. `register_or_satisfy_science_successor`
7. `reopen_or_modify_old_k0`
8. `reuse_pilot_1_as_positive_control_or_regression_baseline`
9. `push_tag_or_remote_anchor`

### blocked_until for the Card 2 bank action

1. `EGO_FIELD_BY_FIELD_AUTHORITY_SYNC_BANKED`
2. `ACTION_SPECIFIC_PATH_POLICY_ENFORCED`
3. `LINEAGE_OMISSION_POSITIVE_CONTROL_ENFORCED`
4. `COMMITTED_RED_REVIEW_RECORD_BOUND_TO_DIFF`

### authorizations

- `capability_card_bank=true`
- `capability_implementation=false`
- `experiment_execution=false`
- `mainline=false`
- `mechanism_evidence=false`
- `remote_anchor=false`
- `runtime=false`
- `science_successor=false`
- `scoring=false`
- `authorized_implementation_targets=[]`

### science_firewall

- `card2_science_weight=0`
- `inherits_h0_h1_freeze_formal=false`
- `inherits_old_k0r=false`
- `may_reopen_old_k0=false`
- `may_satisfy_science_successor_boundary=false`
- `may_supply_mechanism_attribution=false`
- `satisfies_old_s0x=false`

### claim ceiling

`additive cross-repo capability-card bank-admission governance only`; the
committed source forbids claims of Card 2 bank/execution, headroom, learning,
mechanism validity, science-successor admission, runtime/mainline effect,
agency, autonomy, subjectivity, consciousness, electronic life, EGO readiness,
and product benefit.

## Acceptance gate

Acceptance requires all of the following:

1. Mandatory Step 0 branch, HEAD, clean-state, ahead/behind, and all five ITL
   object pins remain exact.
2. An explicit callable crosswalk covers every leaf in the committed ITL route
   and Phase-B receipt and proves byte/value equality with the Ego transcription.
3. The old Ego generic bank binding is removed or historical-only; effective
   Card 2 banking is derived from the exact ITL action and four computed gates.
4. The Card 2 path policy is action-specific and admits only
   `docs/codex/tasks/ego-pet-world-v1-capability-headroom-001a/`.
5. Missing mutation scope and actual-path execution attempts fail closed.
6. The lineage universe is produced by callable discovery independent of
   Program State rows, frozen with a code-path hash, and has an omission
   positive control.
7. Phase A and Phase B each have an independent Claude
   `NO_BLOCKING_FINDINGS` record bound to the exact reviewed diff; the Phase-B
   record is proven from committed objects before the Card 2 bank action becomes
   consumable.
8. Card 2 execution and every implementation/runtime/scoring/science authority
   remain false; targets remain empty and science weight remains zero.
9. Focused mutations, relevant broad tests, route/session guard, Program State
   integrity, route convergence, mainline clarity, fast verification, generated
   views, `git diff --check`, exact staged scope, and post-commit object readback
   pass.
10. Two local commits exist, the worktree is clean, and no push, tag, or remote
    anchor occurred.

## Claim ceiling

Field-by-field authority sync and guard enforcement only.

## Stop conditions

Stop on any branch/HEAD/worktree/pin drift; missing or blocking Claude review;
scope expansion; an ITL edit; any product/runtime/experiment/evidence change;
inability to fail closed; a third governance-repair cycle; an omitted source
field; a second route authority; Card 2 banking/execution; nonzero science
weight; non-empty implementation targets; failed required validation; or any
need for a third local commit.

## Rollback plan

Before commit, remove only this task's untracked files. After commit, use a later
operator-authorized revert of the exact Phase A and/or Phase B commit. Never
rewrite ITL, historical evidence, or unrelated user work.

## Exact expected changed files

### Phase A: transition-card bank

- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/STAGE_CARD.md`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/MUTATION_SCOPE.yaml`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/COLLISION_RECORD.md`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/PHASE_A_RED_REVIEW.json`

### Phase B: field sync and guard enforcement

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `scripts/codex_session_guard.py`
- `scripts/codex/verify_route_convergence.py`
- `scripts/tests/test_codex_session_guard.py`
- `scripts/tests/test_route_governance_supersession.py`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/MUTATION_SCOPE.yaml`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/FIELD_CROSSWALK.json`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/LINEAGE_UNIVERSE.json`
- `docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/PHASE_B_RED_REVIEW.json`
- `docs/STATUS.md` (existing generator output only)
- `docs/codex/tasks/TASK_LANE_INDEX.md` (existing generator output only)
- `docs/REPO_SURFACE_MAP.md` (existing generator output only)
- `artifacts/reports/program_state_summary.md` (existing generator output only)

No other file may change.

## Forbidden changes

- every file under `D:/Project/AIProject/MyProject/intelligence-theory-lab/`;
- `EgoOperator/**`, `EgoDesktop/**`, `packages/**`, `labs/**`, runtime/kernel/UI;
- experiment, scoring, product demo, and pet-world implementation paths;
- historical pet-world and pilot artifacts;
- `artifacts/evidence_ledger/**`, `Tasks/TASK_BOARD.yaml`;
- the Card 2 task directory itself;
- pushes, tags, remote anchors, branch creation, or remote publication.

## Phase and commit authorization

- Phase A local commit: authorized only after independent Claude review of the
  exact Phase-A diff returns `NO_BLOCKING_FINDINGS`.
- Phase B local commit: authorized only after independent Claude review of the
  exact Phase-B diff returns `NO_BLOCKING_FINDINGS` and all callable checks pass.
- Card 2 bank or execution: forbidden in this task.
- Auto-Remote-Anchor, push, and tag: forbidden.

## What this does not prove

This task cannot prove Card 2 is banked or executed, product headroom, learning,
mechanism validity, any science successor, runtime/mainline effect, stable user
benefit, agency, autonomy, subjectivity, consciousness, emotion, electronic
life, or EGO readiness.
