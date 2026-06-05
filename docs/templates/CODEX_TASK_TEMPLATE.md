# Codex Task Template

Use this template when a repo-level task needs to touch status, evidence, or authority wording.

## 当前 phase

## 当前 layer

## 当前 evidence level

## Authority source

`docs/PROGRAM_STATE_UNIFIED.yaml`

## Expected Mutation Surface

- List every path group this task is expected to modify.
- For large deletions, directory migrations, `docs/PROGRAM_STATE_UNIFIED.yaml`, `.codex/project_contract.yaml`, `artifacts/evidence_ledger/`, or other authority/evidence changes, create a task-local `MUTATION_SCOPE.yaml` beside the task docs:

```yaml
schema_version: codex.mutation_scope.v1
task: example-task-id
expected_mutation_surface:
  - short behavior-level description
allowed_mutation_paths:
  - docs/codex/tasks/example-task-id/
  - scripts/example_verifier.py
claim_ceiling: "local workflow or task-specific claim only"
```

Use the scope only for the current closeout command, for example:

```bash
python scripts/codex_session_guard.py --mutation-scope docs/codex/tasks/example-task-id/MUTATION_SCOPE.yaml closeout-check --format markdown
```

Do not permanently broaden `.codex/project_contract.yaml` for one-off mutation surfaces.

## 本任务预期改变哪个状态字段

- Which fields in `docs/PROGRAM_STATE_UNIFIED.yaml` does this task expect to update?

## 本任务不能证明什么

- List the strongest conclusion this task does **not** justify.

## 是否涉及 boundary / authority source / shim

- Does this task touch boundary, authority source, shim, mirror, or adapter behavior?

## 是否需要更新 evidence ledger

- Does this task need to update `artifacts/evidence_ledger/index.yaml`?
- Which evidence entry ids will change or be added?

## Verification plan

- Syntax / import:
- Targeted test or script:
- Mainline or evidence proof:

## 下一步最小闭环动作

## Notes
