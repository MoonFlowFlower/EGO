# Runtime-Proximal Host-Consumption Runner Implementation - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/HOST_CONSUMPTION_CAUSAL_FREEZE.md`

## Scope control

- 允许改：
  - runner script
  - focused tests
  - task-local manifest
  - repo state/progress wording
  - evidence ledger
- 不允许改：
  - runtime public API
  - candidate-private host API
  - live Telegram acceptance logic
  - new scorer ontology

## Validation strategy

- `python3 -m py_compile scripts/codex/run_runtime_proximal_host_consumption_runner.py EgoCore/tests/test_runtime_proximal_host_consumption_runner.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_proximal_host_consumption_runner.py -q -s`
- `python3 scripts/codex/run_runtime_proximal_host_consumption_runner.py`
- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- <scoped files>`
