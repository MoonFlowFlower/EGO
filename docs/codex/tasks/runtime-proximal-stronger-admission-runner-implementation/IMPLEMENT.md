# Runtime-Proximal Stronger Admission Runner Implementation - IMPLEMENT

## Scope

Allowed:

- `docs/codex/tasks/runtime-proximal-stronger-admission-runner-implementation/*`
- `scripts/codex/run_runtime_proximal_stronger_admission_runner.py`
- `EgoCore/tests/test_runtime_proximal_stronger_admission_runner.py`

Not allowed:

- runtime code changes
- authority expansion
- new public API
- new scorer ontology
- live / transport proof work

## Implementation rules

- Reuse the artifact-composition pattern from `run_runtime_proximal_basic_standard_admission_runner.py`
- Consume only bounded summaries / audits / aggregate verdicts from the two frozen inputs
- Treat missing, widened, stale, or overclaimed input state as `hold`, not as proof of a stronger conclusion
