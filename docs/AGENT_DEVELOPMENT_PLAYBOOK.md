# Agent Development Playbook

This playbook is for current `EgoOperator`-first development.

Current authority:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/MAINLINE_QUICKSTART.md`
- `EgoOperator/`

Archived legacy reference:

- `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`
- `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`
- `artifacts/archive/legacy_pre_operator_mainline_manifest.json`
- git tag `legacy-pre-operator-mainline-before-purge`

## One-Sentence Rule

`EgoOperator` owns the current default operator runtime. Archived legacy code has no runtime authority, no default path, no fallback runtime, and no task-routing authority.

## First Files

1. `docs/PROGRAM_STATE_UNIFIED.yaml`
2. `docs/MAINLINE_QUICKSTART.md`
3. `README.md`
4. Current task docs under `Tasks/active/` or `docs/codex/tasks/<slug>/`
5. If editing `EgoOperator/`, also read `EgoOperator/docs/ALGORITHM_INVENTORY.md`

## Development Questions

Before implementation, answer:

1. What is the current authority source?
2. Does the change touch runtime, gate, memory, trace, approval, task routing, or evidence?
3. What is the smallest current-mainline surface that can prove the change?
4. What must remain reference-only?
5. What cannot be proven by this change?
6. What is the rollback path?

If these are unclear, write a Stage Card before coding.

For large deletion, migration, archive purge, program-state, project-contract, or evidence-ledger work, the Stage Card must also include `Expected Mutation Surface`. Add a task-local `MUTATION_SCOPE.yaml` beside the task docs and run closeout with:

```bash
python scripts/codex_session_guard.py --mutation-scope <task>/MUTATION_SCOPE.yaml closeout-check --format markdown
```

Do not permanently broaden `.codex/project_contract.yaml` for one-off mutation surfaces.

## Current Mainline Shape

Keep the default path:

```text
user text -> LLM understanding -> proposal/plan -> runtime gate -> trace
```

Do not restore:

- keyword-first semantic routing as the default entry
- template fallback as the default entry
- old proactive main-chain behavior
- old lab shell as a production runtime
- archived legacy code as a second runtime owner

## Where To Work

- Current operator runtime: `EgoOperator/`
- Current repo governance: `docs/PROGRAM_STATE_UNIFIED.yaml`, `docs/MAINLINE_QUICKSTART.md`, `docs/codex/tasks/TASK_LANE_INDEX.md`
- Evidence ledger: `artifacts/evidence_ledger/`
- Archive pointers: `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`, `docs/archive/`, `artifacts/archive/`
- PSPC lab: `labs/virtual_cat_pspc_v0/` and `artifacts/virtual_cat_pspc_v0/`; lab-only unless a separate Stage Card admits integration

## Legacy Reuse Boundary

Archived legacy ideas may be read only through the inventory and archive pointer. Any reuse must first define:

- Problem reframe.
- One hypothesis.
- One change surface.
- Authority source.
- What can change.
- What cannot be proven.
- Three-level verification.
- Rollback plan.
- Claim ceiling.

## Verification

Use task-matched checks. Common current-mainline checks:

```bash
python scripts/codex/verify_legacy_archival_purge.py
python scripts/codex/check_program_state_integrity.py --skip-diff-check
python scripts/codex/verify_route_convergence.py
python scripts/codex/verify_mainline_clarity.py
python scripts/codex/lint_repo.py
python scripts/codex/verify_repo.py --mode fast
python -m pytest -q EgoOperator/tests
git diff --check
```

If a check is unavailable, report `unavailable` with the exact reason. Do not report unavailable as pass.

## Claim Ceiling

Do not claim stable user benefit, live autonomy, durable memory efficacy, functional selfhood, consciousness, subjective experience, or alive status unless a future evidence gate explicitly supports that claim. Current local tests and archive hygiene prove only their stated local scope.
